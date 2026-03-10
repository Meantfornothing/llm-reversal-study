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
    Routes the request to the correct model logic based on the selected architecture.
    """
    # Combine the document context with the user's specific request
    full_context = f"CURRENT DOCUMENT CONTENT:\n{current_doc}\n\nUSER REQUEST: {user_query}"
    
    if model_mode == "Autoregressive (Gemini)":
        # Returns the generator from stream_gemini which yields text chunks
        return stream_gemini(full_context, gemini_model)
    else:
        # Returns the generator from run_mercury_diffusion which yields effort levels
        return run_mercury_diffusion(full_context, mercury_client)

# StreamlitTest/utils.py

# --- THE GOVERNOR CONFIG ---
WORDS_PER_SECOND = 4  # Standardized speed for ARLLM

def stream_gemini(prompt, model):
    """Yields text chunks with an artificial delay (The Governor)."""
    response = model.generate_content(prompt, stream=True)
    full_text = ""
    for chunk in response:
        if chunk.text:
            # We split by space to simulate a 'word-by-word' typewriter
            words = chunk.text.split()
            for word in words:
                full_text += word + " "
                yield full_text
                # Force the human-readable pace
                time.sleep(1 / WORDS_PER_SECOND)

def run_mercury_diffusion(prompt, client):
    """
    Standardized Diffusion stages. 
    Each 'effort' is a global refinement pass.
    """
    efforts = ["instant", "low", "medium", "high"]
    
    # Total expected time should roughly match ARLLM for fairness
    # We'll use 2.5 seconds per 'global' update
    for effort in efforts:
        response = client.chat.completions.create(
            model="mercury-2",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": effort}
        )
        content = response.choices[0].message.content
        yield {"effort": effort, "content": content}
        
        # This pause allows the user to 'audit' the global draft
        time.sleep(2.5)