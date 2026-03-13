import streamlit as st
import time
from utils import run_mercury_diffusion, get_assistant_response, load_scenario_text

# --- 0. PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Study Session", initial_sidebar_state="collapsed")

# --- 1. SESSION STATE INITIALIZATION ---
# We check for 'main_editor' because it's the direct link to the UI widget
if "main_editor" not in st.session_state:
    initial_text = load_scenario_text(1)
    # The 'truth' for the UI widget
    st.session_state.main_editor = initial_text 
    # The background variable for AI/Sync logic
    st.session_state.doc_content = initial_text 
    # Used to track if the user has changed anything
    st.session_state.last_synced_content = initial_text 

# Initialize these if they don't exist yet
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False
        
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
    chat_container = st.container(height=600, border=True)
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
            # 1. SHOW THE LOADING STATUS (Only for the initial "thinking" phase)
            status_box = st.status("Assistant Analyzing...", expanded=False)
            
            # 2. PLACEHOLDER FOR TEXT (Must be outside the status update for smooth streaming)
            placeholder = st.empty()
            
            res_gen = get_assistant_response(
                st.session_state.model_mode, 
                user_query, 
                st.session_state.doc_content, 
                st.session_state.mercury_client, 
                st.session_state.mistral_client
            )
            
            full_res = ""
            ttft_captured = False

            for update in res_gen:
                if not st.session_state.get("is_running", True): 
                    break
                
                # --- METRIC: TTFT ---
                if not ttft_captured:
                    ttft = time.time() - st.session_state.start_time
                    st.session_state.messages.append({
                        "role": "system", 
                        "content": f"METRIC: TTFT: {ttft:.2f}s"
                    })
                    # Update status and collapse it to clear the way for text
                    status_box.update(label="Generating Audit...", state="running")
                    ttft_captured = True

                # --- DISPLAY LOGIC (Exactly like your Warmup) ---
                if "Mistral" in st.session_state.model_mode:
                    full_res = update 
                    placeholder.markdown(full_res)
                else:
                    full_res = update["content"]
                    # For Mercury, we keep the info box inside the placeholder
                    placeholder.markdown(f"**Refining:** {update['effort'].upper()}\n\n{full_res}")
            
            # 3. FINALIZE UI
            status_box.update(label="Analysis Complete", state="complete", expanded=False)
            
            st.session_state.ai_finish_time = time.time() 
            gen_duration = st.session_state.ai_finish_time - st.session_state.start_time
            st.session_state.messages.append({"role": "system", "content": f"METRIC: Gen_Time: {gen_duration:.2f}s"})
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.session_state.is_running = False
            st.rerun()

with col_editor:
    st.subheader("📝 Diagnostic Editor")
    
    # The Editor - Key handles the state, no 'value' needed
    st.text_area(
        label="Analyze and fix the report below:",
        height=600, 
        key="main_editor"
    )
    
    # Sync internal variable with widget state
    st.session_state.doc_content = st.session_state.main_editor
    
    # Check if they've made any changes
    has_changed = st.session_state.doc_content.strip() != st.session_state.last_synced_content.strip()

    # Action Buttons
    c1, c2 = st.columns(2)
    with c1:
        # LOG ERROR: Only active if they've edited something
        if st.button("✅ Log Error Found", use_container_width=True, disabled=not has_changed, key="btn_fix"):
            st.session_state.errors_found += 1
            st.session_state.last_synced_content = st.session_state.doc_content
            st.session_state.messages.append({"role": "system", "content": f"PROGRESS: Error {st.session_state.errors_found} logged."})
            st.rerun()
    
    with c2:
        # LOG STOP: Red button for when they get frustrated/stuck
        if st.button("🚨 Log Diagnostic Stop", use_container_width=True, type="primary"):
            st.session_state.is_running = False 
            st.session_state.temp_elapsed = time.time() - st.session_state.get("start_time", time.time())
            st.session_state.show_stop_reason = True
            st.rerun()

    # SAFE RESET: Inside an expander to prevent accidental clicks
    with st.expander("⚠️ Danger Zone"):
        if st.button("♻️ Reset to Original Scenario Text", use_container_width=True):
            # Figure out which task we are on based on the 'SWAPPED' system message
            has_swapped = "SWAPPED" in [m['content'] for m in st.session_state.messages if m.get('role') == 'system']
            task_num = 2 if has_swapped else 1
            
            # Reload original
            original_text = load_scenario_text(task_num)
            st.session_state.main_editor = original_text # Update widget key
            st.session_state.doc_content = original_text
            st.session_state.last_synced_content = original_text
            
            st.toast("Document reset to original state.", icon="♻️")
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