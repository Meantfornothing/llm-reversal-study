import streamlit as st
import time
from utils import stream_gemini, run_mercury_diffusion, get_assistant_response,load_scenario_text

# --- 0. PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(
    layout="wide", 
    page_title="Study Session", 
    initial_sidebar_state="collapsed"
)

# --- 1. SESSION STATE INITIALIZATION ---
if "doc_content" not in st.session_state:
    st.session_state.doc_content = ""
if "last_synced_content" not in st.session_state:
    st.session_state.last_synced_content = ""
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0

# --- 2. LOAD INITIAL TEXT IF EMPTY ---
if st.session_state.doc_content == "":
    loaded_text = load_scenario_text(1)
    if "Error:" in loaded_text:
        st.error(loaded_text)
        # Provide a fallback so the app doesn't crash on line 159
        st.session_state.doc_content = "FILE MISSING"
        st.session_state.last_synced_content = "FILE MISSING"
    else:
        st.session_state.doc_content = loaded_text
        st.session_state.last_synced_content = loaded_text
# --- SIDEBAR CONTROLS ---
# Inside StreamlitTest/pages/1_Diagnostic_Lab.py

# Replace the sidebar radio button with this logic:
# StreamlitTest/pages/1_Diagnostic_Lab.py

# Initialize error counts if not present
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0

with st.sidebar:
    st.header("Task Progress")
    st.write(f"Errors Corrected: {st.session_state.errors_found} / 3")
    st.progress(min(st.session_state.errors_found / 3, 1.0))
    
    st.divider()
    
    # Transition Logic: Triggers after 3 errors are logged
    if st.session_state.errors_found >= 3:
        st.success("Target Reached: 3 Errors Found & Fixed!")
        
        # Check if we have already performed the swap
        has_swapped = "SWAPPED" in [m['content'] for m in st.session_state.messages if m['role'] == 'system']
        
        if not has_swapped:
            if st.button("➡️ Start Next Task (Second Assistant)", use_container_width=True):
                # 1. Swap the model mode
                if "Autoregressive" in st.session_state.model_mode:
                    st.session_state.model_mode = "Diffusion (Mercury 2)"
                else:
                    st.session_state.model_mode = "Autoregressive (Gemini)"
                
                # 2. Load Task 2 text 
                # Source: The Emerald Canopy Urban initiative 
                new_text = load_scenario_text(2) 
                st.session_state.doc_content = new_text
                
                # 3. CRITICAL: Reset the comparison baseline so 'Fixed an error' button disables
                st.session_state.last_synced_content = new_text 
                
                # 4. Reset counter and log the swap
                st.session_state.errors_found = 0
                st.session_state.messages.append({"role": "system", "content": "SWAPPED"})
                
                st.rerun()
        else:
            # If already swapped, the only option left is to finish
            if st.button("🏁 Finish & Go to Survey", use_container_width=True, type="primary"):
                st.switch_page("pages/2_Debrief_Survey.py")

# --- DUAL-PANE LAYOUT ---
col_chat, col_editor = st.columns([1, 1.2], gap="large")

with col_chat:
    st.subheader("💬 AI Research Assistant")
    
    # 2. CHAT CONTAINER
    chat_container = st.container(height=500, border=True)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

# 3. CHAT INPUT & INTERRUPTIBLE LOOP
if user_query := st.chat_input("Ask the AI to analyze the document..."):
    st.session_state.is_running = True
    st.session_state.start_time = time.time() # This is the start of the whole process
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    with chat_container.chat_message("user"):
        st.markdown(user_query)

    with chat_container.chat_message("assistant"):
        # UI Bridge: Immediate visual feedback while the API prepares
        with st.status("Initializing model...", expanded=False) as status:
            placeholder = st.empty()
            
            # When the user submits a query
            response_generator = get_assistant_response(
                st.session_state.model_mode, 
                user_query, 
                st.session_state.doc_content, # This passes the text to the LLM
                st.session_state.gemini_model,
                st.session_state.mercury_client
            )
            
            full_response = ""
            first_token_received = False

            for update in response_generator:
                if not st.session_state.is_running:
                    break 
                
                # Capture TTFT (Time to First Token)
                if not first_token_received:
                    ttft = time.time() - st.session_state.start_time
                    st.session_state.messages.append({
                        "role": "system", 
                        "content": f"METRIC: TTFT {ttft:.2f}s"
                    })
                    status.update(label="Assistant Generating...", state="running")
                    first_token_received = True

                if st.session_state.model_mode == "Autoregressive (Gemini)":
                    full_response = update 
                    placeholder.markdown(full_response)
                else:
                    full_response = update["content"]
                    with placeholder.container():
                        st.info(f"🧬 Assistant Beta Refinement: **{update['effort'].upper()}**")
                        st.markdown(full_response)
            
            status.update(label="Response Complete", state="complete")
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.is_running = False
with col_editor:
    st.subheader("📝 Diagnostic Editor")
    
    # Ensure the 'value' is pulled from session_state where load_scenario_text saved it
    st.session_state.doc_content = st.text_area(
        label="Analyze and fix the report below:",
        value=st.session_state.get("doc_content", "Loading text..."), 
        height=600,
        key="main_editor" # Unique key for this widget
    )
    
    # RE-EVALUATE: has_changed based on the new input
    has_changed = st.session_state.doc_content.strip() != st.session_state.last_synced_content.strip()

    c1, c2 = st.columns(2)
    with c1:
        # SYNC BUTTON: Pulls the AI's last message INTO the editor
        if st.button("🔄 Sync Assistant to Editor", use_container_width=True):
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                st.session_state.doc_content = st.session_state.messages[-1]["content"]
                st.rerun()

    if st.button("✅ I have fixed an error", use_container_width=True, disabled=not has_changed):
        st.session_state.errors_found += 1
        st.session_state.last_synced_content = st.session_state.doc_content # Update baseline
        st.session_state.messages.append({
            "role": "system", 
            "content": f"PROGRESS: Error {st.session_state.errors_found} logged."
        })
        st.rerun()
    
# Logic to check if they've actually changed anything since the last AI sync
    has_changed = st.session_state.doc_content.strip() != st.session_state.last_synced_content.strip()

# This is the ONLY button that should increment the count
    if st.button("✅ I have fixed an error", use_container_width=True, disabled=not has_changed):
        st.session_state.errors_found += 1
        st.session_state.last_synced_content = st.session_state.doc_content
        
        # Log the progress for your final data analysis
        st.session_state.messages.append({
            "role": "system", 
            "content": f"PROGRESS: Error {st.session_state.errors_found} logged."
        })
        st.rerun()

    if not has_changed:
        st.caption("⚠️ Edit the text in the editor above to enable error logging.")

with c2:
    if st.button("🚨 Log Diagnostic Error", use_container_width=True, type="primary"):
        # 1. Immediate Kill Switch
        st.session_state.is_running = False 
        
        # 2. Capture timing
        start = st.session_state.get("start_time", time.time())
        elapsed = time.time() - start
        
        # 3. Store temporary data for the 'Reason' popup
        st.session_state.temp_elapsed = elapsed
        st.session_state.show_stop_reason = True
        st.rerun()

# Display the reason selection only after a stop
if st.session_state.get("show_stop_reason", False):
    st.divider()
    with st.container(border=True):
        st.warning(f"Interrupt captured at **{st.session_state.temp_elapsed:.2f}s**. Why did you stop?")
        reason = st.radio(
            "Select Reason:",
            ["Early Success (Found the error)", "Wrong Direction/Hallucination", "Output was too slow", "Other"],
            horizontal=True
        )
        if st.button("Confirm Log"):
            # Finalize logging
            st.session_state.messages.append({
                "role": "system", 
                "content": f"INTERRUPT: {reason} at {st.session_state.temp_elapsed:.2f}s"
            })
            st.session_state.show_stop_reason = False
            st.toast("Data points logged for study!", icon="📊")
            st.rerun()