import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="HCAI Diagnostic Lab")

# --- INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # For the chat history
if "document_content" not in st.session_state:
    st.session_state.document_content = "The AI will generate the audit here..." # For the editor

# --- UI LAYOUT ---
col_chat, col_editor = st.columns([1, 1.2], gap="large")

with col_chat:
    st.subheader("💬 AI Research Assistant")
    
    # Chat Container
    chat_container = st.container(height=500, border=True)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask the AI about the document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
        
        # We will plug the actual model response logic here later
        with chat_container.chat_message("assistant"):
            st.write("Thinking...")

with col_editor:
    st.subheader("📝 Diagnostic Editor")
    
    # The Editor Interface
    # Using a text_area as a simple editor for participants to 'correct' the AI
    st.session_state.document_content = st.text_area(
        label="Edit the report to fix errors:",
        value=st.session_state.document_content,
        height=550,
        key="editor_area"
    )
    
    # Action Buttons for the Experiment
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🚨 Log Diagnostic Error", use_container_width=True, type="primary"):
            st.toast("Error timestamp logged!", icon="✅")
            # We will add timestamp logging logic here
    with btn_col2:
        if st.button("💾 Finalize & Submit", use_container_width=True):
            st.success("Document Submitted for Review.")