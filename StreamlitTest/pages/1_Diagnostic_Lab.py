import streamlit as st
import time
from utils import run_mercury_diffusion, get_assistant_response, load_scenario_text

# --- 0. PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Study Session", initial_sidebar_state="collapsed")

# --- 1. SESSION STATE ---
if "doc_content" not in st.session_state:
    st.session_state.doc_content = ""
if "last_synced_content" not in st.session_state:
    st.session_state.last_synced_content = ""
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. LOAD TEXT ---
if st.session_state.doc_content == "":
    loaded_text = load_scenario_text(1)
    st.session_state.doc_content = loaded_text
    st.session_state.last_synced_content = loaded_text
        
# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Task Progress")
    st.write(f"Errors Corrected: {st.session_state.errors_found} / 3")
    st.progress(min(st.session_state.errors_found / 3, 1.0))
    
    if st.session_state.errors_found >= 3:
        st.success("Target Reached!")
        has_swapped = "SWAPPED" in [m['content'] for m in st.session_state.messages if m.get('role') == 'system']
        
        if not has_swapped:
            if st.button("➡️ Start Next Task"):
                st.session_state.messages = [] 
                st.session_state.model_mode = "Mercury 2 (Diffusion)" if "Mistral" in st.session_state.model_mode else "Mistral (Autoregressive)"
                new_text = load_scenario_text(2) 
                st.session_state.doc_content = new_text
                st.session_state.last_synced_content = new_text 
                if "main_editor" in st.session_state:
                    st.session_state["main_editor"] = new_text
                st.session_state.errors_found = 0
                st.session_state.messages.append({"role": "system", "content": "SWAPPED"})
                st.rerun()
        else:
            if st.button("🏁 Finish to Survey", type="primary"):
                st.switch_page("pages/2_Debrief_Survey.py")

# --- 4. LAYOUT ---
col_chat, col_editor = st.columns([1, 1.2], gap="large")

with col_chat:
    st.subheader("💬 AI Research Assistant")
    chat_container = st.container(height=500, border=True)
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with chat_container.chat_message(msg["role"]):
                st.markdown(msg["content"])

# 3. CHAT INPUT & INTERRUPTIBLE LOOP
if user_query := st.chat_input("Ask the AI to analyze the document..."):
    # --- METRIC: REACTION LATENCY ---
    # Captures time between the LAST AI message and this new prompt
    if "ai_finish_time" in st.session_state:
        reaction_latency = time.time() - st.session_state.ai_finish_time
        st.session_state.messages.append({
            "role": "system", 
            "content": f"METRIC: User_Reaction_Latency: {reaction_latency:.2f}s"
        })
    
    # Initialize state for the new turn
    st.session_state.is_running = True
    st.session_state.start_time = time.time() # Start of the generation process
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with chat_container.chat_message("user"):
        st.markdown(user_query)

    with chat_container.chat_message("assistant"):
        # UI Bridge: Show activity while waiting for the first token
        with st.status("Assistant Analyzing...", expanded=False) as status:
            placeholder = st.empty()
            
            # Call assistant (Ensure utils.py uses mercury_client, mistral_client)
            response_generator = get_assistant_response(
                st.session_state.model_mode, 
                user_query, 
                st.session_state.doc_content, 
                st.session_state.mercury_client, 
                st.session_state.mistral_client
            )
            
            full_res = ""
            ttft_captured = False

            for update in response_generator:
                if not st.session_state.get("is_running", True):
                    break 
                
                # --- METRIC: TTFT ---
                if not ttft_captured:
                    ttft = time.time() - st.session_state.start_time
                    # Use a specialized key to avoid logging this system message multiple times 
                    # if the loop runs fast.
                    st.session_state.messages.append({
                        "role": "system", 
                        "content": f"METRIC: TTFT: {ttft:.2f}s"
                    })
                    status.update(label="Generating Audit...", state="running")
                    ttft_captured = True

                # --- DISPLAY LOGIC ---
                if "Mistral" in st.session_state.model_mode:
                    full_res = update # This will now come in word-by-word from utils.py
                    placeholder.markdown(full_res)
                else:
                    # Mercury Logic (Steps)
                    full_res = update["content"]
                    with placeholder.container():
                        st.info(f"🧬 Diffusion Refinement: **{update['effort'].upper()}**")
                        st.markdown(full_res)
            
            status.update(label="Analysis Complete", state="complete")
        
        # --- FINALIZE TURN & LOG METRICS ---
        # 1. Capture exact end time for the 'Reaction' clock
        st.session_state.ai_finish_time = time.time() 
        
        # 2. Capture Generation Duration
        gen_duration = st.session_state.ai_finish_time - st.session_state.start_time
        st.session_state.messages.append({
            "role": "system", 
            "content": f"METRIC: Total_Generation_Time: {gen_duration:.2f}s"
        })
        
        # 3. Log content and reset state
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        st.session_state.is_running = False
        
        # 4. Final Rerun to update chat history UI
        st.rerun()

with col_editor:
    st.subheader("📝 Diagnostic Editor")
    # This now only updates via typing or the manual Sync button
    st.session_state.doc_content = st.text_area(label="Analyze and fix:", value=st.session_state.doc_content, height=600, key="main_editor")
    
    has_changed = st.session_state.doc_content.strip() != st.session_state.last_synced_content.strip()

    c1, c2 = st.columns(2)
    with c1:
        # MANUAL SYNC: This is the only way the AI text gets into the editor
        if st.button("🔄 Sync AI to Editor", use_container_width=True):
            assistant_msgs = [m for m in st.session_state.messages if m["role"] == "assistant"]
            if assistant_msgs:
                new_val = assistant_msgs[-1]["content"]
                st.session_state.doc_content = new_val
                st.session_state["main_editor"] = new_val
                st.rerun()

        if st.button("✅ Log Error", use_container_width=True, disabled=not has_changed, key="btn_fix"):
            st.session_state.errors_found += 1
            st.session_state.last_synced_content = st.session_state.doc_content
            st.session_state.messages.append({"role": "system", "content": f"PROGRESS: Error {st.session_state.errors_found}"})
            st.rerun()
    
    with c2:
        if st.button("🚨 Log Stop", use_container_width=True, type="primary"):
            st.session_state.is_running = False 
            st.session_state.temp_elapsed = time.time() - st.session_state.get("start_time", time.time())
            st.session_state.show_stop_reason = True
            st.rerun()

# --- 5. INTERRUPT LOGGING ---
if st.session_state.get("show_stop_reason", False):
    st.divider()
    with st.container(border=True):
        st.warning(f"Interrupt at {st.session_state.temp_elapsed:.2f}s")
        reason = st.radio("Reason:", ["Early Success", "Wrong Direction", "Too Slow", "Other"], horizontal=True)
        if st.button("Confirm Log"):
            st.session_state.messages.append({"role": "system", "content": f"INTERRUPT: {reason} at {st.session_state.temp_elapsed:.2f}s"})
            st.session_state.show_stop_reason = False
            st.rerun()