import streamlit as st
import os 
from dotenv import load_dotenv
from utils import init_models

load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="HCAI Diagnostic Lab")
init_models()

st.title("Welcome to the LLM Study")

p_id = st.number_input("Enter Participant ID", min_value=1)

if st.button("Begin Study"):
    st.session_state.p_id = p_id
    st.switch_page("pages/1_Diagnostic_Lab.py")

