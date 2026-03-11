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
# StreamlitTest/utils.py

def get_assistant_response(model_mode, user_query, current_doc, gemini_model, mercury_client):
    """
    Routes the request to the correct model logic and provides 
    the generator needed for the interruptible UI loop.
    """
    # Contextualize the prompt with the current state of the diagnostic editor
    full_context = f"CURRENT DOCUMENT CONTENT:\n{current_doc}\n\nUSER REQUEST: {user_query}"
    
    if model_mode == "Autoregressive (Gemini)":
        # Returns the word-by-word governed generator
        return stream_gemini(full_context, gemini_model)
    else:
        # Returns the step-by-step refinement generator
        return run_mercury_diffusion(full_context, mercury_client)

# --- THE GOVERNOR CONFIG ---
WORDS_PER_SECOND = 4  # Standardized speed for ARLLM

# StreamlitTest/utils.py

def stream_gemini(prompt, model):
    """Yields text chunks while checking for a stop signal."""
    response = model.generate_content(prompt, stream=True)
    full_text = ""
    for chunk in response:
        # Check if the user clicked stop (managed via session_state in the UI loop)
        if not st.session_state.get("is_running", True):
            return # Exit the generator immediately
        
        if chunk.text:
            full_text += chunk.text
            yield full_text
            time.sleep(0.1) # Governor delay

def run_mercury_diffusion(prompt, client):
    """Runs diffusion efforts but aborts if is_running becomes False."""
    efforts = ["instant", "low", "medium", "high"]
    
    for effort in efforts:
        # Check stop signal BEFORE making the next expensive API call
        if not st.session_state.get("is_running", True):
            break
            
        response = client.chat.completions.create(
            model="mercury-2",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": effort}
        )
        
        content = response.choices[0].message.content
        yield {"effort": effort, "content": content}
        time.sleep(1.5) # Governor delay