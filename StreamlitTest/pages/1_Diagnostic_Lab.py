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
with st.sidebar:
    st.header("Session Info")
    st.write(f"Participant: **{st.session_state.get('p_id', 'N/A')}**")
    
    # Generic labeling for the participant
    display_name = "Assistant Alpha" if "Autoregressive" in st.session_state.model_mode else "Assistant Beta"
    st.success(f"Connected to: **{display_name}**")
    
    # Hide the 'Clear Chat' and other technical buttons behind an expander if needed
    with st.expander("Researcher Tools"):
        if st.button("Force Clear"):
            st.session_state.messages = []
            st.rerun()
            
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
        st.session_state.start_time = time.time()
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        with chat_container.chat_message("user"):
            st.markdown(user_query)

        with chat_container.chat_message("assistant"):
            placeholder = st.empty()
            
            # Fetch the generator (Governed in utils.py)
            response_generator = get_assistant_response(
                st.session_state.model_mode, 
                user_query, 
                st.session_state.doc_content,
                st.session_state.gemini_model,   # Initialized in StreamlitExp.py
                st.session_state.mercury_client  # Initialized in StreamlitExp.py
            )
            
            full_response = ""
            for update in response_generator:
                # BREAK CONDITION: Check if is_running was flipped by an interrupt button
                if not st.session_state.is_running:
                    break 
                
                if st.session_state.model_mode == "Autoregressive (Gemini)":
                    full_response = update # Accumulated text from stream_gemini
                    placeholder.markdown(full_response)
                else:
                    # update is a dict: {"effort": ..., "content": ...}
                    full_response = update["content"]
                    with placeholder.container():
                        st.info(f"🧬 Mercury 2 Refinement: **{update['effort'].upper()}**")
                        st.markdown(full_response)
            
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
    
    # StreamlitTest/pages/1_Diagnostic_Lab.py

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