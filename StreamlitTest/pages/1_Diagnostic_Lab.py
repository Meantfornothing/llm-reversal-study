import streamlit as st
from utils import get_gemini_response, get_mercury_steps

st.set_page_config(layout="wide", page_title="Step 1: Diagnostic Lab")

# Ensure participant ID is carried over from the main page
if "p_id" not in st.session_state:
    st.warning("Please enter a Participant ID on the Home page first.")
    st.stop()

col_chat, col_editor = st.columns([1, 1.2], gap="large")

with col_chat:
    st.subheader(f"💬 Assistant (ID: {st.session_state.p_id})")
    # ... (Chat logic here)

with col_editor:
    st.subheader("📝 Audit Document")
    st.session_state.doc_content = st.text_area(
        "Current Report State", 
        value=st.session_state.get("doc_content", ""), 
        height=500
    )
    
    if st.button("Complete Task"):
        st.switch_page("pages/2_Debrief_Survey.py")