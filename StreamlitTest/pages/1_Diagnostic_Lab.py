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
st.set_page_config(layout="wide", page_title="Step 1: Diagnostic Lab")

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("Experiment Settings")
    st.session_state.model_mode = st.radio(
        "Current AI Architecture:",
        ["Autoregressive (Gemini)", "Diffusion (Mercury 2)"]
    )
    st.divider()
    if st.button("Clear Chat"):
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
    
    with c2:
        # This button serves as the main 'Interrupt' measurement
        if st.button("🚨 Log Diagnostic Error", use_container_width=True, type="primary"):
            st.session_state.is_running = False # Stops the loop in col_chat
            elapsed = time.time() - (st.session_state.start_time or time.time())
            st.toast(f"Error caught at {elapsed:.2f}s!", icon="✅")