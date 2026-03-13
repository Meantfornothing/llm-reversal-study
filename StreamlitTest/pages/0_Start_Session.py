import streamlit as st
import time
from utils import get_assistant_response

# --- 1. PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Introduction & Warmup", initial_sidebar_state="collapsed")

# --- 2. PRACTICE TEXT DEFINITION ---
PRACTICE_TEXT = """TECHNICAL REPORT: SENSOR CALIBRATION (PRACTICE)

The oxygen sensors in Sector 7 are performing within normal parameters. 
However, the data logs show a temperature of 500 degrees Celcius.

This temperature is physically impossible for this environment. 
Please check the thermal shield for potential cracks or leaks."""

# --- 3. SESSION STATE INITIALIZATION ---
# FORCE-CHECK: If the key exists but is empty/wrong, we override it.
if "warmup_editor" not in st.session_state or st.session_state.warmup_editor == "":
    st.session_state.warmup_editor = PRACTICE_TEXT
    st.session_state.warmup_doc = PRACTICE_TEXT

if "warmup_messages" not in st.session_state:
    st.session_state.warmup_messages = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "model_mode" not in st.session_state:
    st.session_state.model_mode = "Mistral (Autoregressive)"

st.title("Welcome to the AI Collaboration Study")

# --- 4. CONSENT & INSTITUTIONAL INFO ---
with st.expander("📝 Participant Consent & Information", expanded=True):
    st.markdown("""
    ### Research Study: Human-AI Collaboration Patterns
    **University of Gothenburg | Department of Applied IT**
    
    We are conducting a research study to understand how different AI architectures influence human diagnostic workflows. 
    """)
    st.info("- Data is anonymized. You may withdraw at any point.")
    agreed = st.checkbox("I have read the info and agree to participate.")

# --- 5. API WARMUP / PING ---
if agreed and "apis_warmed" not in st.session_state:
    with st.status("📡 Checking Satellite Uplink...", expanded=True) as status:
        try:
            # Check Mistral
            t0 = time.time()
            st.session_state.mistral_client.chat.completions.create(
                model="mistral-small-latest", messages=[{"role": "user", "content": "ping"}], max_tokens=1
            )
            st.write(f"✅ Mistral: {time.time() - t0:.2f}s")
            # Check Mercury
            t1 = time.time()
            st.session_state.mercury_client.chat.completions.create(
                model="mercury-2", messages=[{"role": "user", "content": "ping"}], max_tokens=1
            )
            st.write(f"✅ Mercury: {time.time() - t1:.2f}s")
            st.session_state.apis_warmed = True
            status.update(label="System Ready", state="complete", expanded=False)
        except:
            st.warning("Skipping ping check for offline testing.")
            st.session_state.apis_warmed = True

if agreed:
    # --- 6. DEMOGRAPHICS ---
    with st.container(border=True):
        st.subheader("📊 Participant Profile")
        c_dem1, c_dem2 = st.columns(2)
        with c_dem1:
            st.session_state.age = st.number_input("Age", 18, 100, 25)
            st.session_state.gender = st.selectbox("Gender", ["Female", "Male", "Other", "Prefer not to say"])
        with c_dem2:
            st.session_state.field_study = st.text_input("Field of Study")
            st.session_state.ai_familiarity = st.select_slider("AI Familiarity", ["Novice", "Occasional", "Frequent", "Expert"])

    st.divider()
    
    # --- 7. WARMUP SECTION ---
    st.subheader("🛠️ Interface Warmup (Practice Mode)")
    
    col_chat, col_editor = st.columns([1, 1.2], gap="large")

    with col_editor:
        # THE FIX: No 'value' parameter. Let the session_state handle it.
        st.text_area(
            "Practice Editor", 
            height=300, 
            key="warmup_editor" # Linked directly to the logic at the top
        )
        # Sync immediately
        st.session_state.warmup_doc = st.session_state.warmup_editor
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Sync Practice"):
                if st.session_state.warmup_messages:
                    st.session_state.warmup_editor = st.session_state.warmup_messages[-1]["content"]
                    st.rerun()
        with c2:
            if st.button("🚨 Practice Stop", type="primary"):
                st.toast("Practice interrupt captured!")

    with col_chat:
        warmup_container = st.container(height=350, border=True)
        for msg in st.session_state.warmup_messages:
            with warmup_container.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_query := st.chat_input("Ask: 'Is there a temperature error?'"):
            st.session_state.is_running = True
            st.session_state.warmup_messages.append({"role": "user", "content": user_query})
            
            with warmup_container.chat_message("assistant"):
                res_gen = get_assistant_response(
                    st.session_state.model_mode, 
                    user_query, 
                    st.session_state.warmup_doc,
                    st.session_state.mercury_client,
                    st.session_state.mistral_client
                )
                
                placeholder = st.empty()
                full_res = ""
                for update in res_gen:
                    if not st.session_state.is_running: break
                    if "Mistral" in st.session_state.model_mode:
                        full_res = update
                        placeholder.markdown(full_res)
                    else:
                        full_res = update["content"]
                        placeholder.markdown(f"**Refining:** {update['effort'].upper()}\n\n{full_res}")
                
                st.session_state.warmup_messages.append({"role": "assistant", "content": full_res})
                st.session_state.is_running = False
                st.rerun()

    if st.session_state.get('field_study'):
        st.markdown("---")
        if st.button("🚀 I'm Ready - Start Real Experiment", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Diagnostic_Lab.py")