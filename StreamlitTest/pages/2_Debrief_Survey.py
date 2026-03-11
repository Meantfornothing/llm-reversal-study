import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="Step 2: LLM Evaluation")

st.header("Step 2: Architectural Evaluation")
st.info("Please evaluate your experience with the two different AI generation styles you just tested.")

# Wrap everything in a single form
with st.form("unified_study_form"):
    
    # Create two tabs for the specific models
    tab_ar, tab_dllm = st.tabs(["⚡ Model 1 (Sequential/Gemini)", "🌊 Model 2 (Diffusion/Mercury)"])

    # --- TAB 1: ARLLM ---
    with tab_ar:
        st.subheader("Model 1 Experience (Token-by-Token)")
        
        ar_natural = st.select_slider(
            "How natural did the 'Typewriter' style feel for problem identification in text?",
            options=["Very Unnatural", "Unnatural", "Neutral", "Natural", "Very Natural"],
            value="Very Unnatural",
            key="ar_nat"
        )
        
        ar_wait = st.select_slider(
            "Did you feel you had to 'wait' for the AI to finish a sentence before you could think?",
            options=["Always Waiting", "Often", "Neutral", "Rarely", "Never (Read while typing)"],
            value="Always Waiting",
            key="ar_wait"
        )

        st.markdown("** Cognitive Workload (NASA-TLX)**")
        col1, col2 = st.columns(2)
        with col1:
            ar_mental = st.slider("Mental Demand (Tracking the sequence)", 1, 10, 1, key="ar_m")
            ar_temp = st.slider("Temporal Demand (Speed of the output)", 1, 10, 1, key="ar_t")
        with col2:
            ar_frust = st.slider("Frustration (Waiting for output)", 1, 10, 1, key="ar_f")
            ar_perf = st.slider("Success in finding traps with AR", 1, 10, 1, key="ar_p")
            ar_effort = st.slider("Effort (How much mental effort was required?)", 1, 10, 1, key="ar_e")

        st.subheader("Qualitative Load (Model 1)")
        ar_qual_notes = st.text_area(
            "Describe specific moments where the Model 1 felt 'heavy' or confusing:",
            placeholder="e.g. The typewriter pace was too slow/fast...",
            key="ar_qual_text",
            height=100
        )

    # --- TAB 2: DLLM ---
    with tab_dllm:
        st.subheader("Model 2 Experience (Iterative Refinement)")
        
        dllm_natural = st.select_slider(
            "How natural did the 'Denoising' (Global-to-Local) style feel?",
            options=["Very Unnatural", "Unnatural", "Neutral", "Natural", "Very Natural"],
            value="Very Unnatural",
            key="dl_nat"
        )
        
        dllm_stability = st.select_slider(
            "Did the text 'changing globally' make you feel disoriented?",
            options=["Very Disoriented", "Somewhat", "Neutral", "Stable enough", "Very Stable"],
            value="Very Disoriented",
            key="dl_stab"
        )

        st.markdown("**Model 2 Cognitive Workload (NASA-TLX)**")
        col3, col4 = st.columns(2)
        with col3:
            dllm_mental = st.slider("Mental Demand (Interpreting the blur/refinement)", 1, 10, 1, key="dl_m")
            dllm_temp = st.slider("Temporal Demand (Speed of the 'clearing up')", 1, 10, 1, key="dl_t")
        with col4:
            dllm_frust = st.slider("Frustration (Text changing under your eyes)", 1, 10, 1, key="dl_f")
            dllm_perf = st.slider("Success in finding traps with DLLM", 1, 10, 1, key="dl_p")
            # FIX: Changed key from 'ar_e' to 'dl_e'
            dllm_effort = st.slider("Effort (How much mental effort was required?)", 1, 10, 1, key="dl_e")

        st.subheader("Qualitative Load (Model 2)")
        dl_qual_notes = st.text_area(
            "Describe specific moments where the Model 2 felt 'heavy' or confusing:",
            placeholder="e.g. The global changes made me lose my place...",
            key="dl_qual_text",
            height=100
        )

    st.divider()

    # --- FINAL COMPARISON & AGENCY ---
    st.subheader("3. Comparative Analysis & Agency")
    
    col_pref, col_agency = st.columns(2)
    with col_pref:
        preference = st.radio(
            "Which LLM felt more like a 'Collaborative Partner'?",
            ["Model 1 (Sequential)", "Model 2 (Diffusion)", "No Difference"],
            key="pref_radio"
        )
    with col_agency:
        agency_score = st.radio(
            "In which model did you feel MORE in control of the document?",
            ["Model 1", "Model 2", "Both equal"],
            key="agency_radio"
        )

    why_text = st.text_area("Describe the 'Why' behind your preference:", height=100, key="why_notes")

    # THE ONLY SUBMIT BUTTON
    submit = st.form_submit_button("Submit Final Study Data")

# --- DATA LOGGING ---
if submit:
    # Calculate Raw TLX for both
    ar_tlx = (ar_mental + ar_temp + ar_frust + ar_perf + ar_effort) / 5
    dl_tlx = (dllm_mental + dllm_temp + dllm_frust + dllm_perf + dllm_effort) / 5
    
    # Unified results dictionary
    data = {
        "p_id": st.session_state.get("p_id", "N/A"),
        "pref_choice": preference,
        "agency_choice": agency_score,
        "ar_total_tlx": ar_tlx,
        "dl_total_tlx": dl_tlx,
        "ar_mental": ar_mental,
        "ar_temp": ar_temp,
        "ar_frust": ar_frust,
        "ar_perf": ar_perf,
        "ar_effort": ar_effort,
        "ar_natural": ar_natural,
        "ar_wait": ar_wait,
        "ar_qual_notes": ar_qual_notes,
        "dl_mental": dllm_mental,
        "dl_temp": dllm_temp,
        "dl_frust": dllm_frust,
        "dl_perf": dllm_perf,
        "dl_effort": dllm_effort, 
        "dl_natural": dllm_natural,
        "dl_stability": dllm_stability,
        "dl_qual_notes": dl_qual_notes,
        "overall_why": why_text
    }
    
    try:
        # Create a directory if it doesn't exist
        os.makedirs("quantitative/results", exist_ok=True)
        csv_path = "quantitative/results/survey_data.csv"
        
        df = pd.DataFrame([data])
        
        # Append to CSV
        df.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)
        
        st.success(f"Success! Workloads Logged -> AR: {ar_tlx:.2f} | DLLM: {dl_tlx:.2f}")
        st.balloons()
    except Exception as e:
        st.error(f"Error saving data: {e}")
