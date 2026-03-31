import streamlit as st
import pandas as pd
from datetime import date

# --- CONFIGURATION DATA ---
ALL_STATES = sorted(['Assam', 'Maharashtra', 'Haryana', 'Jammu and Kashmir', 'Sikkim', 'Kerala', 
              'Gujarat', 'Manipur', 'Andaman and Nicobar Islands', 'Jharkhand', 'Goa', 
              'Madhya Pradesh', 'Bihar', 'Karnataka', 'Tamil Nadu', 'Mizoram', 'Uttarakhand', 
              'Meghalaya', 'Punjab', 'Telangana', 'Andhra Pradesh', 'Delhi', 'Himachal Pradesh', 
              'West Bengal', 'Arunachal Pradesh', 'Uttar Pradesh', 'Odisha', 'Rajasthan', 
              'Nagaland', 'Tripura', 'Chhattisgarh'])

ALL_LANGS = sorted(['Kannada', 'Marathi', 'Telugu', 'Bengali', 'English', 'Mandarin', 
             'Chattisgarhi', 'Hindi', 'Garhwali', 'Spanish', 'Punjabi', 'Assamese', 
             'Bhojpuri', 'Malayalam', 'Hinglish', 'Tamil', 'Gujarati', 'Korean', 
             'Japanese', 'Odia', 'French'])

# Page Config
st.set_page_config(page_title="Box Office Input Portal", layout="wide")

st.title("🎬 Box Office Prediction: Input Module")
st.markdown("Enter details to generate market-specific show inputs.")

# --- SECTION 1: MOVIE IDENTITY ---
with st.container():
    st.subheader("1. General Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        movie_name = st.text_input("Movie Name", placeholder="e.g. Pushpa 2")
    with col2:
        primary_lang = st.selectbox("Original/Primary Language", ALL_LANGS)
    with col3:
        release_date = st.date_input("Release Date", min_value=date.today())

st.divider()

# --- SECTION 2: DISTRIBUTION STRATEGY (The lang_state Logic) ---
st.subheader("2. Market Distribution")

# 1. Ask for States and Languages first
col_a, col_b = st.columns(2)
with col_a:
    selected_states = st.multiselect("Select States for Release", ALL_STATES, help="Which states will the movie be screened in?")
with col_b:
    selected_langs = st.multiselect("Select Dubbed/Release Languages", ALL_LANGS, help="Which languages will be available in these states?")

if selected_states and selected_langs:
    st.info("💡 Enter the number of **Expected Shows** for Day 1 for each active pairing below:")
    
    # Create a dictionary to store the results
    # This will eventually map to your log_shows_{language}_{state} columns
    show_inputs = {}
    
    # 2. Iterate through pairs and ask for show counts
    for state in selected_states:
        with st.expander(f"📍 Distribution in {state}", expanded=True):
            # Create columns for the languages to save vertical space
            cols = st.columns(len(selected_langs))
            for i, lang in enumerate(selected_langs):
                # Unique key for Streamlit state management
                input_key = f"{lang}_{state}"
                
                # Each number input matches a Market Bucket
                show_count = cols[i].number_input(
                    f"{lang} shows", 
                    min_value=0, 
                    step=1, 
                    key=input_key
                )
                show_inputs[input_key] = show_count

    # --- SUMMARY FOR VERIFICATION ---
    if st.button("Finalize Inputs"):
        # Convert dictionary to a DataFrame to show the user what we captured
        summary_data = []
        for key, val in show_inputs.items():
            if val > 0:
                l, s = key.split("_", 1)
                summary_data.append({"Language": l, "State": s, "Shows": val})
        
        if summary_data:
            st.success("Inputs Captured Successfully!")
            st.table(pd.DataFrame(summary_data))
        else:
            st.warning("Please enter at least one show count.")
else:
    st.write("Please select at least one State and one Language to begin mapping shows.")
