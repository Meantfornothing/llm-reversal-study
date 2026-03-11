import streamlit as st
import time
from utils import stream_gemini, run_mercury_diffusion, get_assistant_response

# --- 1. SESSION STATE INITIALIZATION (Top of File) ---
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = "The AI will generate the diagnostic report here..."
if "model_mode" not in st.session_state:
    st.session_state.model_mode = "Autoregressive (Gemini)"
if "last_synced_content" not in st.session_state:
    st.session_state.last_synced_content = ""

# --- PAGE CONFIG ---
# Add this to the top of 1_Diagnostic_Lab.py and 2_Debrief_Survey.py
st.set_page_config(
    layout="wide", 
    page_title="Study Session", 
    initial_sidebar_state="collapsed" # Hides the page list
)

# --- SIDEBAR CONTROLS ---
# Inside StreamlitTest/pages/1_Diagnostic_Lab.py

# Replace the sidebar radio button with this logic:
# StreamlitTest/pages/1_Diagnostic_Lab.py

# Initialize error counts if not present
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0

with st.sidebar:
    st.header("Task Progress")
    # Just a visual display now - no button here!
    st.write(f"Errors Corrected: {st.session_state.errors_found} / 3")
    st.progress(st.session_state.errors_found / 3)
    
    st.divider()
    
    # Transition Logic: Only pops up when they've used the Editor button 3 times
    if st.session_state.errors_found >= 3:
        st.success("Target Reached: 3 Errors Found & Fixed!")
        
        # Check if we need to swap to the second model or go to the survey
        if "SWAPPED" not in [m['content'] for m in st.session_state.messages if m['role'] == 'system']:
            if st.button("➡️ Start Next Task (Second Assistant)", use_container_width=True):
                # Swap logic...
                st.rerun()
        else:
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
            
            response_generator = get_assistant_response(
                st.session_state.model_mode, 
                user_query, 
                st.session_state.doc_content,
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
    st.session_state.doc_content = st.text_area(
        label="Edit the report to fix errors:",
        value=st.session_state.doc_content,
        height=550,
        key="editor_area"
    )
    
    # ACTION & INTERRUPT BUTTONS
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Sync Assistant to Editor", use_container_width=True):
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                st.session_state.doc_content = st.session_state.messages[-1]["content"]
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