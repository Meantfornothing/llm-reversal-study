import streamlit as st
import google.generativeai as genai
import mercury_api
from dotenv import load_dotenv
import os

# Load global .env from the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# StreamlitTest/utils.py

# --- GEMINI CONFIG (AR) ---
# Limit output to prevent 'rambling' and keep audits concise
gemini_config = {
    "temperature": 0.7,
    "max_output_tokens": 500,  # Limits the length of each response
    "top_p": 0.95,
}

# --- MERCURY 2 CONFIG (Diffusion) ---
# Control the number of steps and complexity
mercury_config = {
    "max_tokens": 500,
    "diffusion_steps": [20, 100, 300], # Only run 3 refinement passes instead of 10+
}

def init_models():
    """Initialize API configurations using Streamlit secrets or .env."""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # Mercury 2 Client setup
    return mercury_api.Client(api_key=os.getenv("MERCURY_API_KEY"))

def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-3-flash')
    return model.generate_content(prompt, stream=True)

def get_mercury_steps(prompt):
    client = init_models()
    # Returns the iterative denoising steps for the diffusion model
    return client.generate(prompt, return_steps=True)
def check_api_configs():
    """Verify that secrets are loaded before starting the task."""
    keys_found = "GEMINI_API_KEY" in st.secrets and "MERCURY_API_KEY" in st.secrets
    if not keys_found:
        st.error("⚠️ API Keys missing! Check your .streamlit/secrets.toml file.")
    return keys_found