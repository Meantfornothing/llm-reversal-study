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
with st.expander("📝 Participant Consent & Information", expanded=True):
    st.write("Please read the following information carefully:")
    st.info("- Data is anonymized. You may withdraw at the end.")
    agreed = st.checkbox("I have read the info and agree to participate.")

# --- SILENT DUAL WARMUP ---
if agreed and "apis_warmed" not in st.session_state:
    with st.spinner("Initializing Assistant Connections..."):
        try:
            # Warm up Gemini (AR)
            st.session_state.gemini_model.generate_content("Ping", generation_config={"max_output_tokens": 1})
            
            # Warm up Mercury (Diffusion)
            st.session_state.mercury_client.chat.completions.create(
                model="mercury-2",
                messages=[{"role": "user", "content": "Ping"}],
                extra_body={"reasoning_effort": "instant"},
                max_tokens=1
            )
            st.session_state.apis_warmed = True
            st.toast("Systems Online", icon="🛰️")
        except Exception as e:
            st.error(f"Connection Lag Detected: {e}")

if agreed:
# --- 2. DEMOGRAPHICS SECTION ---
    with st.container(border=True):
        st.subheader("📊 Participant Profile")
        st.write("Please provide some basic information before we begin.")
        
        col_dem_1, col_dem_2 = st.columns(2)
        with col_dem_1:
            # We assign these directly to session_state keys
            st.session_state.age = st.number_input("Age", min_value=18, max_value=100, value=20)
            st.session_state.gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Other", "Prefer not to say"])
        
        with col_dem_2:
            st.session_state.field_study = st.text_input("Field of Study", placeholder="e.g., Biology, Engineering")
            st.session_state.ai_familiarity = st.select_slider(
                "AI Familiarity",
                options=["Novice", "Occasional", "Frequent", "Expert"]
            )

    st.divider()
    st.subheader("🛠️ Interface Warmup (Practice Mode)")
    st.write("Use this space to get comfortable with the tools. This data is **NOT** recorded.")
    
    # Guidance for the participant
    st.markdown("""
    **Try these three steps now:**
    1. **Ask the AI** to "Find typos" in the text below.
    2. **Stop the AI** early by clicking the red 'Log Error' button if you see it working.
    3. **Sync the result** to the editor using the blue button.
    """)

    # --- MINI LAB LAYOUT (Mirroring 1_Diagnostic_Lab.py) ---
    col_chat, col_editor = st.columns([1, 1.2], gap="large")

    with col_chat:
        # Simple Chat
        warmup_container = st.container(height=300, border=True)
        for msg in st.session_state.warmup_messages:
            with warmup_container.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_query := st.chat_input("Practice: Type 'Hello' or 'Find errors'..."):
            st.session_state.is_running = True
            st.session_state.warmup_messages.append({"role": "user", "content": user_query})
            
            with warmup_container.chat_message("assistant"):
                # Using the real models so they see the actual visual style (AR vs Diffusion)
                res_gen = get_assistant_response(
                    st.session_state.model_mode, 
                    user_query, 
                    st.session_state.warmup_doc,
                    st.session_state.gemini_model,
                    st.session_state.mercury_client
                )
                
                placeholder = st.empty()
                full_res = ""
                for update in res_gen:
                    if not st.session_state.is_running: break
                    
                    if "Autoregressive" in st.session_state.model_mode:
                        full_res = update
                        placeholder.markdown(full_res)
                    else:
                        full_res = update["content"]
                        placeholder.info(f"Refining: {update['effort']}")
                        placeholder.markdown(full_res)
                
                st.session_state.warmup_messages.append({"role": "assistant", "content": full_res})

    with col_editor:
        # Mini Editor
        st.session_state.warmup_doc = st.text_area("Practice Editor", value=st.session_state.warmup_doc, height=200)
        
        c1, c2 = st.columns(2)
        if c1.button("🔄 Sync Practice"):
            if st.session_state.warmup_messages:
                st.session_state.warmup_doc = st.session_state.warmup_messages[-1]["content"]
                st.rerun()
        
        if c2.button("🚨 Practice Stop", type="primary"):
            st.session_state.is_running = False
            st.toast("Practice interrupt captured!")

    st.divider()
    
    if st.session_state.get('field_study'):
        if st.button("🚀 I'm Ready - Start Real Experiment"):
            # Clean up warmup state so it doesn't bleed into the real experiment
            st.session_state.messages = [] 
            st.switch_page("pages/1_Diagnostic_Lab.py")
    else:
        st.caption("⚠️ Please fill in your Field of Study to enable the start button.")