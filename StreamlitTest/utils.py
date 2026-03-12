import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

# Load global .env from the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def init_models():
    """Initializes and returns Mercury and Mistral clients."""
    # 1. Initialize Mercury 2 (Diffusion)
    mercury_client = OpenAI(
        api_key=os.getenv("MERCURY_API_KEY"),
        base_url="https://api.inceptionlabs.ai/v1"
    )
    
    # 2. Initialize Mistral (Autoregressive)
    mistral_client = OpenAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url="https://api.mistral.ai/v1"
    )
    
    return mercury_client, mistral_client

def get_assistant_response(model_mode, user_query, current_doc, mercury_client, mistral_client):
    """Routes request to either Mistral or Mercury."""
    full_context = f"DOCUMENT TO AUDIT:\n{current_doc}\n\nUSER QUESTION: {user_query}"
    
    # Speed Slicing: Last 2 chat messages for context
    recent_history = st.session_state.messages[-2:] if len(st.session_state.get("messages", [])) > 2 else []
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in recent_history])
    final_prompt = f"{full_context}\n\nRECENT HISTORY:\n{history_str}"

    if "Mistral" in model_mode:
        return stream_mistral(final_prompt, mistral_client)
    else:
        return run_mercury_diffusion(final_prompt, mercury_client)
WORDS_PER_SECOND = 4
MAX_RESPONSE_WORDS = 150
def stream_mistral(prompt, client):
    """Yields text with a 4 words-per-second governor and a word limit."""
    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    
    full_text = ""
    word_count = 0
    
    for chunk in response:
        if not st.session_state.get("is_running", True):
            return
        
        content = chunk.choices[0].delta.content
        if content:
            # Add content to buffer
            full_text += content
            
            # Simple governor: pause briefly after each 'chunk' 
            # to simulate human-like reading/typing speed
            yield full_text
            time.sleep(1 / WORDS_PER_SECOND) 
            
            # Basic word limit check
            word_count = len(full_text.split())
            if word_count >= MAX_RESPONSE_WORDS:
                yield full_text + "\n\n[Word limit reached for study audit]"
                return

def run_mercury_diffusion(prompt, client):
    """Runs diffusion efforts for Mercury with a word limit."""
    efforts = ["instant", "low", "medium", "high"]
    for effort in efforts:
        if not st.session_state.get("is_running", True):
            break
        response = client.chat.completions.create(
            model="mercury-2",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": effort}
        )
        content = response.choices[0].message.content
        
        # --- NEW: Word limit check for Mercury ---
        words = content.split()
        if len(words) > MAX_RESPONSE_WORDS:
            content = " ".join(words[:MAX_RESPONSE_WORDS]) + "... [Word limit reached]"
        
        yield {"effort": effort, "content": content}
        time.sleep(1.5) # Delay between refinement steps

# StreamlitTest/utils.py

def load_scenario_text(task_num):
    """Loads the audit text using an absolute path relative to this file."""
    # 1. Determine the filename based on the task
    filename = "The_Aurora_7_Deep_Sea.txt" if task_num == 1 else "The_Emerald_Canopy_Urban.txt"
    
    # 2. Get the directory where THIS utils.py file is located (StreamlitTest/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 3. Build the absolute path to the file inside StreamlitTest/data/scenarios/
    file_path = os.path.join(current_dir, "data", "scenarios", filename)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # This will now show the full path it tried to use, making debugging easier
        return f"Error: Scenario file not found at {file_path}"