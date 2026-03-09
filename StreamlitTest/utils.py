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

def stream_gemini(prompt):
    # Ensure you are using the correct model ID we found earlier
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    # This returns an iterable of GenerateContentResponse objects
    response = model.generate_content(prompt, stream=True)
    
    # We yield just the text chunks so Streamlit can render them directly
    for chunk in response:
        if chunk.text:
            yield chunk.text


def run_mercury_diffusion(prompt, client):
    """
    Calls Mercury 2 and yields intermediate 'denoising' steps.
    Each step represents the model's current global understanding of the audit.
    """
    # 1. We perform a 'Low Effort' pass to get the 'Sketch'
    sketch_res = client.chat.completions.create(
        model="mercury-2",
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "instant"} # Fastest, lowest fidelity
    )
    sketch_text = sketch_res.choices[0].message.content
    yield sketch_text

    # 2. We perform the 'Refinement' pass
    # This simulates the parallel 'diffusion' process where text is corrected globally
    final_res = client.chat.completions.create(
        model="mercury-2",
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "high"} # Deepest diffusion reasoning
    )
    yield final_res.choices[0].message.content

def check_api_configs():
    """Verify that secrets are loaded before starting the task."""
    keys_found = "GEMINI_API_KEY" in st.secrets and "MERCURY_API_KEY" in st.secrets
    if not keys_found:
        st.error("⚠️ API Keys missing! Check your .streamlit/secrets.toml file.")
    return keys_found


def get_assistant_response(model_mode, user_query, current_doc, gemini_model, mercury_client):
    """
    Updated to accept model objects from the session state.
    """
    full_context = f"CURRENT DOCUMENT CONTENT:\n{current_doc}\n\nUSER REQUEST: {user_query}"
    
    if model_mode == "Autoregressive (Gemini)":
        # Pass the model to the stream function
        return stream_gemini(full_context, gemini_model)
    else:
        # Pass the client to the diffusion function
        return run_mercury_diffusion(full_context, mercury_client)