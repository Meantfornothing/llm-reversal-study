# StreamlitTest/StreamlitExp.py
import streamlit as st
from utils import init_models

st.set_page_config(layout="wide", page_title="HCAI Study Home")

# Initialize models once at startup
if "gemini_model" not in st.session_state:
    gemini, mercury = init_models()
    st.session_state.gemini_model = gemini
    st.session_state.mercury_client = mercury

st.title("Welcome to the LLM Reversal Study")
p_id = st.text_input("Enter Participant ID")

if st.button("Begin Study"):
    if p_id:
        st.session_state.p_id = p_id
        st.switch_page("pages/1_Diagnostic_Lab.py")
    else:
        st.error("Please enter an ID to continue.")