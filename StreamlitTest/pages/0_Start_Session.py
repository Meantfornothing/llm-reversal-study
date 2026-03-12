import streamlit as st
import time
from utils import get_assistant_response

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Introduction & Warmup", initial_sidebar_state="collapsed")

# --- SESSION STATE FOR WARMUP ---
if "warmup_messages" not in st.session_state:
    st.session_state.warmup_messages = []
if "warmup_doc" not in st.session_state:
    st.session_state.warmup_doc = "This is a PRACTICE document. Try editing this text!"
if "is_running" not in st.session_state:
    st.session_state.is_running = False

st.title("Welcome to the AI Collaboration Study")

# 1. CONSENT SECTION
# StreamlitTest/pages/0_Start_Session.py

st.title("Welcome to the AI Collaboration Study")

# 1. CONSENT & INSTITUTIONAL INFO
with st.expander("📝 Participant Consent & Information", expanded=True):
    st.markdown("""
    ### Research Study: Human-AI Collaboration Patterns
    **University of Gothenburg | Department of Applied IT**
    
    We are conducting a research study to understand how different AI architectures 
    (Autoregressive vs. Diffusion) influence human diagnostic workflows. 
    Your participation helps us map the future of collaborative error-detection.
    """)
    st.info("- Data is anonymized. You may withdraw at any point before submission.")
    agreed = st.checkbox("I have read the info and agree to participate.")


# Add this to the 'Initialization' section of 0_Start_Session.py

if agreed and "apis_warmed" not in st.session_state:
    with st.status("📡 Checking Satellite Uplink (API Ping)...") as status:
        # Check Mistral
        t0 = time.time()
        st.session_state.mistral_client.chat.completions.create(
            model="mistral-small-latest", messages=[{"role": "user", "content": "ping"}], max_tokens=1
        )
        mistral_ping = time.time() - t0
        st.write(f"✅ Mistral Latency: {mistral_ping:.2f}s")
        
        # Check Mercury
        t1 = time.time()
        st.session_state.mercury_client.chat.completions.create(
            model="mercury-2", messages=[{"role": "user", "content": "ping"}], max_tokens=1
        )
        mercury_ping = time.time() - t1
        st.write(f"✅ Mercury Latency: {mercury_ping:.2f}s")
        
        st.session_state.apis_warmed = True
        status.update(label="System Ready", state="complete")

if agreed:
    # --- 2. DEMOGRAPHICS SECTION ---
    with st.container(border=True):
        st.subheader("📊 Participant Profile")
        col_dem_1, col_dem_2 = st.columns(2)
        with col_dem_1:
            st.session_state.age = st.number_input("Age", min_value=18, max_value=100, value=20)
            st.session_state.gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Other", "Prefer not to say"])
        with col_dem_2:
            st.session_state.field_study = st.text_input("Field of Study", placeholder="e.g., Biology")
            st.session_state.ai_familiarity = st.select_slider("AI Familiarity", options=["Novice", "Occasional", "Frequent", "Expert"])

    st.divider()
    st.subheader("🛠️ Interface Warmup (Practice Mode)")
    
    col_chat, col_editor = st.columns([1, 1.2], gap="large")

    with col_chat:
        warmup_container = st.container(height=300, border=True)
        for msg in st.session_state.warmup_messages:
            with warmup_container.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_query := st.chat_input("Practice: Type 'Find errors'..."):
            st.session_state.is_running = True
            st.session_state.warmup_messages.append({"role": "user", "content": user_query})
            
            with warmup_container.chat_message("assistant"):
                # Pass the two correct clients to get_assistant_response
                res_gen = get_assistant_response(
                    st.session_state.model_mode, 
                    user_query, 
                    st.session_state.warmup_doc,
                    st.session_state.mercury_client, # Updated param order
                    st.session_state.mistral_client  # Updated param order
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

    with col_editor:
        # Use a key to ensure manual syncing works in warmup too
        st.session_state.warmup_doc = st.text_area("Practice Editor", value=st.session_state.warmup_doc, height=200, key="warmup_editor")
        
        c1, c2 = st.columns(2)
        if c1.button("🔄 Sync Practice"):
            if st.session_state.warmup_messages:
                last_ai_msg = st.session_state.warmup_messages[-1]["content"]
                st.session_state.warmup_doc = last_ai_msg
                st.session_state["warmup_editor"] = last_ai_msg
                st.rerun()
        
        if c2.button("🚨 Practice Stop", type="primary"):
            st.session_state.is_running = False
            st.toast("Practice interrupt captured!")

    if st.session_state.get('field_study'):
        if st.button("🚀 I'm Ready - Start Real Experiment"):
            st.session_state.messages = [] 
            st.switch_page("pages/1_Diagnostic_Lab.py")