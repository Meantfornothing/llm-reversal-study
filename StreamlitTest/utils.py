import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

# Load global .env from the root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def init_models():
    mercury_client = OpenAI(
        api_key=os.getenv("MERCURY_API_KEY"),
        base_url="https://api.inceptionlabs.ai/v1"
    )
    mistral_client = OpenAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url="https://api.mistral.ai/v1"
    )
    return mercury_client, mistral_client

def get_assistant_response(model_mode, user_query, current_doc, mercury_client, mistral_client):
    system_instruction = (
        "ACT AS A TECHNICAL AUDIT ADVISOR. Your goal is to ASSIST the user, not do the work for them.\n"
        "STRICT RESEARCH CONSTRAINTS:\n"
        "- NEVER provide the full corrected document at once.\n"
        "- If asked to audit, point out the GENERAL areas where errors might exist.\n"
        "- Provide hints and guidance rather than direct solutions.\n"
        "- MAXIMUM LENGTH: 80 words.\n"
        "- Maintain a professional, slightly critical tone."
        "- Focus on one error/fix at the time"
    )
    
    document_block = f"--- DOCUMENT TO AUDIT ---\n{current_doc}\n--- END DOCUMENT ---"
    
    # Simple history retrieval
    recent_history = st.session_state.get("messages", [])[-2:]
    history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_history])
    
    final_prompt = (
        f"{system_instruction}\n"
        f"{document_block}\n\n"
        f"USER REQUEST: {user_query}\n\n"
        f"RECENT CHAT HISTORY:\n{history_str}\n\n"
        f"ASSISTANT RESPONSE:"
    )

    if "Mistral" in model_mode:
        return stream_mistral(final_prompt, mistral_client)
    else:
        return run_mercury_diffusion(final_prompt, mercury_client)
# StreamlitTest/utils.py

def run_mercury_diffusion(prompt, client):
    """Simulates/Triggers Mercury diffusion steps for the UI."""
    # Effort levels to show the 'refinement' process
    efforts = ["low", "medium", "high"]
    
    full_content = ""
    for effort in efforts:
        if not st.session_state.get("is_running", True):
            break
            
        response = client.chat.completions.create(
            model="mercury-2",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"reasoning_effort": effort} # This triggers different refinement depths
        )
        full_content = response.choices[0].message.content
        
        # We yield each 'effort' level so the UI shows the "Refining" info box
        yield {"effort": effort, "content": full_content}
        
        # A tiny sleep so the participant can actually see the "Refining" status change
        time.sleep(1) 



import time
import streamlit as st

def stream_mistral(prompt, client):
    # 1. Immediate API Call
    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        stream=True 
    )
    
    full_text = ""
    words_yielded = 0
    WORDS_PER_SECOND = 6 # Bumped to 6 for better UX (4 can feel like a crawl)
    start_time = None

    for chunk in response:
        if not st.session_state.get("is_running", True):
            break
            
        content = chunk.choices[0].delta.content
        if content:
            if start_time is None:
                start_time = time.time() # Capture TTFT here
                
            full_text += content
            current_words = full_text.split()
            
            # If a new word has arrived, show it, THEN wait if we are too fast
            if len(current_words) > words_yielded:
                yield full_text # PUSH TO UI IMMEDIATELY
                
                # Math: How long should it take to show this many words?
                target_time = len(current_words) / WORDS_PER_SECOND
                actual_elapsed = time.time() - start_time
                
                delay = target_time - actual_elapsed
                if delay > 0:
                    time.sleep(delay)
                
                words_yielded = len(current_words)

    # Final safety yield
    yield full_text

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
        