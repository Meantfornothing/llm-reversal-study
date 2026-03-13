import streamlit as st
import time
from utils import run_mercury_diffusion, get_assistant_response, load_scenario_text

# --- 0. PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Study Session", initial_sidebar_state="collapsed")

# --- 1. SESSION STATE INITIALIZATION ---
if "main_editor" not in st.session_state:
    text = load_scenario_text(1)
    st.session_state.main_editor = text
    st.session_state.editor_widget = text
    st.session_state.last_synced_content = text

if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# Track the start time of the current task
if "task_start_time" not in st.session_state:
    st.session_state.task_start_time = time.time()

# --- THE BLACK BOX RECORDER ---
if "study_logs" not in st.session_state:
    st.session_state.study_logs = {
        "task_1": {"time": "N/A", "interrupts": 0, "reasons": [], "text": "N/A"},
        "task_2": {"time": "N/A", "interrupts": 0, "reasons": [], "text": "N/A"}
    }
else:
    # SAFETY: Ensure "reasons" exists in both tasks if the session was already active
    for task in ["task_1", "task_2"]:
        if "reasons" not in st.session_state.study_logs[task]:
            st.session_state.study_logs[task]["reasons"] = []

if "interrupt_count" not in st.session_state:
    st.session_state.interrupt_count = 0
# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Task Progress")
    st.write(f"Errors Corrected: {st.session_state.errors_found} / 3")
    st.progress(min(st.session_state.errors_found / 3, 1.0))
    
    if st.session_state.errors_found >= 3:
        # Check if we've already moved to Task 2
        has_swapped = "SWAPPED" in [m['content'] for m in st.session_state.messages if m.get('role') == 'system']
        
        if not has_swapped:
            st.success("Target Reached! Ready for the next scenario.")
            if st.button("➡️ Start Next Task", use_container_width=True):
                # --- NEW: LOG TASK 1 DATA ---
                t1_duration = time.time() - st.session_state.task_start_time
                
                # We store this in a "Persistent Data" key so it doesn't get cleared with messages
                if "task_1_data" not in st.session_state:
                    st.session_state.task_1_data = {
                        "time": f"{t1_duration:.2f}s",
                        "interrupts": st.session_state.interrupt_count,
                        "final_text": st.session_state.main_editor
                    }

                # 1. Clear chat history for Task 2
                st.session_state.messages = [] 
                
                # 2. Swap the AI Model
                current_mode = st.session_state.get("model_mode", "Mistral (Autoregressive)")
                st.session_state.model_mode = "Mercury 2 (Diffusion)" if "Mistral" in current_mode else "Mistral (Autoregressive)"
                
                # 3. Load Scenario 2
                new_text = load_scenario_text(2) 
                
                # 4. Update keys for sync logic
                st.session_state.main_editor = new_text
                st.session_state.editor_widget = new_text 
                
                # 5. RESET TRACKERS FOR TASK 2
                st.session_state.last_synced_content = new_text 
                st.session_state.errors_found = 0
                st.session_state.interrupt_count = 0 # Reset count
                st.session_state.task_start_time = time.time() # Reset clock
                
                # 6. Mark the swap and refresh
                st.session_state.messages.append({"role": "system", "content": "SWAPPED"})
                st.rerun()
        else:
            st.info("Task 2 Complete!")
            if st.button("🏁 Finish to Survey", type="primary", use_container_width=True):
                # SAVE TASK 2 TO BLACK BOX
                t2_duration = time.time() - st.session_state.task_start_time
                st.session_state.study_logs["task_2"] = {
                    "time": f"{t2_duration:.2f}s",
                    "interrupts": st.session_state.interrupt_count,
                    "text": st.session_state.main_editor
                }
                st.switch_page("pages/2_Debrief_Survey.py")

# --- 3. LAYOUT ---
col_chat, col_editor = st.columns([1, 1.2], gap="large")

with col_chat:
    st.subheader("💬 AI Research Assistant")
    
    # --- A. SOFT-STOP BUTTON ---
    # This button does NOT stop the loop; it just opens the "Reason" window.
    # This prevents the UI from locking up.
    # --- A. SOFT-STOP BUTTON ---
    if st.session_state.is_running and not st.session_state.get("show_stop_reason"):
        # This button just toggles the 'show_stop_reason' state. 
        # Streamlit will naturally refresh the UI to show the overlay without killing the LLM loop.
        if st.button("🚨 LOG INTERRUPT REASON", use_container_width=True, type="primary"):
            st.session_state.show_stop_reason = True
            st.session_state.temp_elapsed = time.time() - st.session_state.get("start_time", time.time())
        
    # --- B. CHAT HISTORY ---
    chat_container = st.container(height=500, border=True)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] in ["user", "assistant"]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # --- C. THE REASON OVERLAY ---
    if st.session_state.get("show_stop_reason", False):
        with st.container(border=True):
            st.warning(f"⚠️ Capturing Interrupt at {st.session_state.temp_elapsed:.2f}s")
            reason = st.radio("Why are you interrupting?", ["Found error", "AI is wrong", "Too slow", "Other"], horizontal=True)
            
            if st.button("Confirm Log & Continue"):
                # 1. Increment count
                st.session_state.interrupt_count += 1
                
                # 2. Determine Current Task
                has_swapped = "SWAPPED" in [m['content'] for m in st.session_state.get("messages", []) if m.get('role') == 'system']
                current_task = "task_2" if has_swapped else "task_1"
                
                # 3. SAVE THE REASON to the Black Box list
                st.session_state.study_logs[current_task]["reasons"].append(reason)
                st.session_state.study_logs[current_task]["interrupts"] = st.session_state.interrupt_count
                
                # 4. UI Feedback
                st.session_state.show_stop_reason = False
                st.toast(f"Logged: {reason}", icon="📝")
                # No st.rerun() so the LLM keeps streaming!

    # --- D. CHAT INPUT ---
    if not st.session_state.is_running and not st.session_state.get("show_stop_reason"):
        if user_query := st.chat_input("Ask the AI auditor..."):

            # Force capture latest editor value
            st.session_state.main_editor = st.session_state.get("main_editor", "")

            st.session_state.is_running = True
            st.session_state.start_time = time.time()
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.rerun()

    # --- E. NON-BLOCKING GENERATION ENGINE ---
    if st.session_state.is_running and st.session_state.messages:
        if st.session_state.messages[-1]["role"] == "user":
            with chat_container.chat_message("assistant"):
                placeholder = st.empty()
                full_res = ""
                
                # Pulls live from 'main_editor' key automatically
                res_gen = get_assistant_response(
                    st.session_state.model_mode, 
                    st.session_state.messages[-1]["content"], 
                    st.session_state.main_editor, 
                    st.session_state.mercury_client, 
                    st.session_state.mistral_client
                )
                
                for update in res_gen:
                    if "Mistral" in st.session_state.model_mode:
                        full_res = update
                    else:
                        full_res = update["content"]
                    
                    # Update the UI while keeping everything else live
                    placeholder.markdown(full_res)
                
                # Turn ends naturally
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.session_state.is_running = False
                st.rerun()

with col_editor:
    st.subheader("📝 Diagnostic Editor")
    
    st.text_area(
        label="Analyze and fix the report below:",
        height=600,
        key="editor_widget",
    )

    # Sync widget -> state
    st.session_state.main_editor = st.session_state.editor_widget
    
    # Local variable for the "Log Error" button state
    has_changed = st.session_state.main_editor.strip() != st.session_state.last_synced_content.strip()

    if st.button("✅ Log Error Found", use_container_width=True, disabled=not has_changed):
        st.session_state.errors_found += 1
        # Update the baseline so the button disables again until the next edit
        st.session_state.last_synced_content = st.session_state.main_editor
        
        # Optional: Small toast to let the participant know it saved
        st.toast(f"Error {st.session_state.errors_found}/3 logged!", icon="📍")
        st.rerun()