import streamlit as st
import google.generativeai as genai
import mercury_api
from dotenv import load_dotenv
import os
import time
from openai import OpenAI

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
    """Initializes and returns both model clients."""
    # 1. Initialize Gemini with the correct preview ID
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # FIX: Add '-preview' to the model name
    gemini_model = genai.GenerativeModel('gemini-3-flash-preview') 
    
    # 2. Initialize Mercury 2
    mercury_client = OpenAI(
        api_key=os.getenv("MERCURY_API_KEY"),
        base_url="https://api.inceptionlabs.ai/v1"
    )
    
    return gemini_model, mercury_client

def stream_gemini(prompt, model):
    """Yields text chunks for the AR 'Typewriter' effect."""
    response = model.generate_content(prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text


def run_mercury_diffusion(prompt, client):
    """
    Simulates the 'Diffusion' process by requesting 3 distinct 
    levels of reasoning effort from Mercury 2.
    """
    # 2026 Mercury 2 supports: "instant", "low", "medium", "high"
    efforts = ["instant", "low", "medium", "high"]
    
    for effort in efforts:
        # Each call here is a 'refinement pass'
        response = client.chat.completions.create(
            model="mercury-2",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": effort}
        )
        
        # Yield the current 'state' of the thought
        content = response.choices[0].message.content
        yield {"effort": effort, "content": content}
        
        # Artificial delay so the participant has time to 'audit'
        # Adjust this time (e.g., 2.0) to make it even slower
        time.sleep(1.5)

def check_api_configs():
    """Verify that secrets are loaded before starting the task."""
    keys_found = "GEMINI_API_KEY" in st.secrets and "MERCURY_API_KEY" in st.secrets
    if not keys_found:
        st.error("⚠️ API Keys missing! Check your .streamlit/secrets.toml file.")
    return keys_found


def get_assistant_response(model_mode, user_query, current_doc, gemini_model, mercury_client):
    """
    Routes the request to the correct model logic.
    """
    full_context = f"CURRENT DOCUMENT CONTENT:\n{current_doc}\n\nUSER REQUEST: {user_query}"
    
    if model_mode == "Autoregressive (Gemini)":
        # Returns a generator yielding text chunks
        return stream_gemini(full_context, gemini_model)
    else:
        # Returns a generator yielding effort-level dictionaries
        return run_mercury_diffusion(full_context, mercury_client)