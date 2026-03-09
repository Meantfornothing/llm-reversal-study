import streamlit as st
import time
from utils import get_assistant_response

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Step 1: Diagnostic Lab")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_content" not in st.session_state:
    st.session_state.doc_content = "The AI will generate the diagnostic report here..."
if "model_mode" not in st.session_state:
    st.session_state.model_mode = "Autoregressive (Gemini)"

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
    
    # Display chat history
    chat_container = st.container(height=500, border=True)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input Logic
    if user_query := st.chat_input("Ask the AI to analyze the document..."):
        # 1. Add user message to state and UI
        st.session_state.messages.append({"role": "user", "content": user_query})
        with chat_container.chat_message("user"):
            st.markdown(user_query)

        # 2. Get response from utils
        with chat_container.chat_message("assistant"):
            if st.session_state.model_mode == "Autoregressive (Gemini)":
                # Handle streaming response
                response_generator = get_assistant_response(
                    st.session_state.model_mode, 
                    user_query, 
                    st.session_state.doc_content
                )
                # st.write_stream automatically iterates and displays the text
                full_response = st.write_stream(response_generator)
        
            # Save the clean text to history, not the object
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            else:
                # Handle Mercury 2 diffusion steps
                steps_generator = get_assistant_response(
                    st.session_state.model_mode, 
                    user_query, 
                    st.session_state.doc_content
                )
                status_placeholder = st.empty()
                final_text = ""
                
                for step_content in steps_generator:
                    # Check if it's a status message or the final long report
                    if len(step_content) < 50: 
                        status_placeholder.info(f"🧬 Mercury Diffusion: {step_content}")
                        time.sleep(0.5) 
                    else:
                        final_text = step_content
                        status_placeholder.markdown(final_text)
                
                st.session_state.messages.append({"role": "assistant", "content": final_text})

with col_editor:
    st.subheader("📝 Diagnostic Editor")
    
    # The Editor Interface
    st.session_state.doc_content = st.text_area(
        label="Edit the report to fix errors:",
        value=st.session_state.doc_content,
        height=550,
        key="editor_area"
    )
    
    # Action Buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Sync Assistant to Editor", use_container_width=True):
            # Takes the last message from the AI and puts it in the editor
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
                st.session_state.doc_content = st.session_state.messages[-1]["content"]
                st.rerun()
    
    with c2:
        if st.button("🚨 Log Diagnostic Error", use_container_width=True, type="primary"):
            st.toast("Error timestamp logged!", icon="✅")