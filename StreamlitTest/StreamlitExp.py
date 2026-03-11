# StreamlitTest/StreamlitExp.py
import streamlit as st
from utils import init_models

st.set_page_config(layout="wide", page_title="Researcher Dashboard")

if "gemini_model" not in st.session_state:
    gemini, mercury = init_models()
    st.session_state.gemini_model = gemini
    st.session_state.mercury_client = mercury

st.title("🛡️ Researcher Setup")

# Set these once per machine
st.session_state.laptop_id = st.selectbox("Laptop ID", ["Laptop_A", "Laptop_B"])

p_id = st.text_input("Enter Participant ID")
first_mode = st.selectbox("First Architecture (Counterbalancing)", ["Mode A", "Mode B"])

if st.button("Initialize for Participant"):
    if p_id:
        st.session_state.p_id = p_id
        # Internally map the names so the participant never sees 'Diffusion' or 'AR'
        mapping = {"Mode A": "Autoregressive (Gemini)", "Mode B": "Diffusion (Mercury 2)"}
        st.session_state.model_mode = mapping[first_mode]
        st.session_state.initial_model_choice = mapping[first_mode]
        
        # Switch to the new Intro/Consent page
        st.switch_page("pages/0_Start_Session.py")