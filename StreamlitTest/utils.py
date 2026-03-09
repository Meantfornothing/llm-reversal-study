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

# StreamlitTest/utils.py

def run_mercury_diffusion(prompt):
    """
    Actual Mercury 2 Diffusion Call.
    We iterate through a few 'samples' to show the user the refinement.
    """
    # Initialize the client (OpenAI-compatible)
    client = init_models()[1] 
    
    # Define the steps you want to show the participant
    # This simulates the 'clearing up' of the text
    display_steps = ["Initial Noise Reduction...", "Structural Alignment...", "Logic Synthesis...", "Final Polish"]
    
    # 1. Yield the visual status updates first
    for step_msg in display_steps:
        yield step_msg

    # 2. Perform the actual high-fidelity diffusion call
    # Mercury 2 handles the complex 'refinement' in one high-speed parallel pass
    response = client.chat.completions.create(
        model="mercury-2",
        messages=[{"role": "user", "content": prompt}],
        extra_body={"reasoning_effort": "high"} # Triggers the deep diffusion process
    )
    
    # 3. Yield the final result to replace the 'analyzing' text
    yield response.choices[0].message.content

def check_api_configs():
    """Verify that secrets are loaded before starting the task."""
    keys_found = "GEMINI_API_KEY" in st.secrets and "MERCURY_API_KEY" in st.secrets
    if not keys_found:
        st.error("⚠️ API Keys missing! Check your .streamlit/secrets.toml file.")
    return keys_found

def get_assistant_response(model_mode, user_query, current_doc):
    """
    Logic to route the prompt to the correct model.
    Passes the 'current_doc' as the system context.
    """
    full_context = f"CURRENT DOCUMENT CONTENT:\n{current_doc}\n\nUSER REQUEST: {user_query}"
    
    if model_mode == "Autoregressive (Gemini)":
        return stream_gemini(full_context)
    else:
        return run_mercury_diffusion(full_context)