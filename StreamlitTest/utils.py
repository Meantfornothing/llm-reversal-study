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

# StreamlitTest/utils.py

def get_assistant_response(model_mode, user_query, current_doc, mercury_client, mistral_client):
    """
    Refined prompt with strict structural constraints and word limits.
    """
    # 1. High-priority System Instructions
    system_instruction = (
        "ACT AS A TECHNICAL AUDITOR. Your sole task is to analyze the DOCUMENT provided below. "
        "CONSTRAINTS:\n"
        "- OUTPUT ONLY the audited text. Do not include introductions, 'Sure!', or explanations.\n"
        "- MAXIMUM LENGTH: 150 words. Be extremely concise.\n"
        "- Focus strictly on resolving contradictions or errors in the provided document.\n"
    )
    
    # 2. Document Markers
    document_block = f"--- DOCUMENT TO AUDIT ---\n{current_doc}\n--- END DOCUMENT ---"
    
    # 3. Handle History as secondary context
    recent_history = st.session_state.messages[-2:] if len(st.session_state.get("messages", [])) > 2 else []
    history_str = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_history])
    
    # 4. Final prompt assembly
    final_prompt = (
        f"{system_instruction}\n"
        f"{document_block}\n\n"
        f"USER QUESTION: {user_query}\n\n"
        f"CONTEXT (PAST MESSAGES):\n{history_str}\n\n"
        f"FINAL COMMAND: Provide the audited text now (Max 150 words)."
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
        time.sleep(0.8) 



def stream_mistral(prompt, client):
    response = client.chat.completions.create(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        stream=True 
    )
    
    full_text = ""
    words_yielded = 0
    WORDS_PER_SECOND = 4
    # Use a small 'tick' delay to prevent the loop from eating CPU
    # but keep it fast enough to feel responsive.

    for chunk in response:
        if not st.session_state.get("is_running", True):
            break
            
        content = chunk.choices[0].delta.content
        if content:
            full_text += content
            current_words = full_text.split()
            
            # Only trigger the timing logic if a NEW word has actually appeared
            if len(current_words) > words_yielded:
                # How many new words did we just get?
                new_words_count = len(current_words) - words_yielded
                
                # Sleep for the duration of those new words
                # e.g., if 1 new word, sleep 0.25s.
                time.sleep(new_words_count / WORDS_PER_SECOND)
                
                words_yielded = len(current_words)
                yield full_text
    
    # Final yield to make sure any trailing punctuation/characters are shown
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
        