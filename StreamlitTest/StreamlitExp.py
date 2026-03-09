import streamlit as st
import time
import pandas as pd
from datetime import datetime

# --- SETTINGS & DATA ---
TASK_A_CONTENT = "SERVER REPORT: DB_MIGRATION_V2. Error: Snapshot scheduled for 10/12, but Wipe set for 10/11."
# (Replace with your full dashboard snapshots later)

# --- SESSION STATE INITIALIZATION ---
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'task_active' not in st.session_state:
    st.session_state.task_active = False

def log_data(model_type, event, duration):
    st.session_state.logs.append({
        "timestamp": datetime.now(),
        "model": model_type,
        "event": event,
        "duration_seconds": duration
    })

# --- UI LAYOUT ---
st.title("HCAI Diagnostic Bench 2026")
st.sidebar.header("Experiment Control")
model_choice = st.sidebar.radio("Select Architecture", ["Autoregressive (AR)", "Diffusion (dLLM)"])

if st.button("Start Diagnostic Task"):
    st.session_state.task_active = True
    st.session_state.start_time = time.time()

# --- THE TESTING CANVAS ---
if st.session_state.task_active:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        placeholder = st.empty()
        
        if model_choice == "Autoregressive (AR)":
            # Simulation: Word-by-word typing
            full_text = ""
            for word in TASK_A_CONTENT.split():
                full_text += word + " "
                placeholder.markdown(f"### AI Output:\n{full_text}")
                time.sleep(0.2) # Adjust for 'reading speed'
        
        else:
            # Simulation: Diffusion Fade-in
            for i in range(1, 11):
                opacity = i / 10
                # We use a simple blur/gray-out effect for the 'sketch' phase
                placeholder.markdown(
                    f'<div style="filter: blur({(10-i)*1}px); opacity: {opacity};">'
                    f'### AI Output (Refining Step {i}/10):\n{TASK_A_CONTENT}</div>', 
                    unsafe_allow_html=True
                )
                time.sleep(0.6) # Total 6 seconds to clarify
    
    with col2:
        if st.button("🚨 I FOUND THE ERROR"):
            end_time = time.time()
            duration = end_time - st.session_state.start_time
            log_data(model_choice, "Error Detected", duration)
            st.success(f"Detection logged: {duration:.2f}s")
            st.session_state.task_active = False

# --- EXPORT DATA ---
if st.sidebar.button("Download Session Data"):
    df = pd.DataFrame(st.session_state.logs)
    st.sidebar.download_button("Download CSV", df.to_csv(index=False), "experiment_results.csv")