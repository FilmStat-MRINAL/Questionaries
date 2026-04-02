import streamlit as st
import pandas as pd
from datetime import date
import numpy as np

# --- CONFIGURATION ---
ALL_STATES = sorted(['Assam', 'Maharashtra', 'Haryana', 'West Bengal', 'Tamil Nadu', 'Andhra Pradesh', 'Karnataka', 'Kerala', 'Delhi', 'Uttar Pradesh', 'Gujarat', 'Punjab', 'Rajasthan', 'Madhya Pradesh', 'Bihar', 'Jharkhand', 'Odisha', 'Chhattisgarh', 'Uttarakhand', 'Himachal Pradesh', 'Jammu and Kashmir', 'Goa', 'Telangana'])
ALL_LANGS = sorted(['Telugu', 'Tamil', 'Malayalam', 'Hindi', 'English', 'Kannada', 'Bengali', 'Marathi'])
ALL_GENRES = sorted(['Action', 'Adult', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Film Noir', 'Game Show', 'History', 'Horror', 'Musical', 'Music', 'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Talk-Show', 'Thriller', 'War', 'Western'])

st.set_page_config(page_title="Box Office Input Portal", layout="wide")

st.title("🎬 Movie Release: Data Capture Portal")
st.markdown("Enter Day 1 release plans using the State-Only logic.")

# --- DATA LOADING & TALENT RESOLUTION ---
import requests
import io

@st.cache_data
def load_and_resolve_talent():
    # Direct download format for Google Drive
    # confirm=t helps bypass potential virus scan confirmation pages for small files
    # Fetch IDs from Streamlit's private "Secrets" manager
    DIR_ID = st.secrets["DIR_ID"]
    CAST_ID = st.secrets["CAST_ID"]
    
    DIR_URL = f"https://drive.google.com/uc?export=download&id={DIR_ID}&confirm=t"
    CAST_URL = f"https://drive.google.com/uc?export=download&id={CAST_ID}&confirm=t"

    try:
        # Stream from Drive into RAM
        dir_res = requests.get(DIR_URL)
        cast_res = requests.get(CAST_URL)
        
        # Verify if the download was successful
        if dir_res.status_code != 200 or cast_res.status_code != 200:
            st.error("Failed to fetch data from Drive. Check if permissions are set to 'Anyone with link'.")
            return ["Data Not Found"], ["Data Not Found"]

        df_dir = pd.read_pickle(io.BytesIO(dir_res.content))
        df_cast = pd.read_pickle(io.BytesIO(cast_res.content))

        # --- Your existing logic ---
        def get_final_id(df):
            return df.apply(
                lambda row: (
                    row["Same_as_person"] if pd.notna(row.get("Same_as_person"))
                    else (row["Same_as_person_from_Fuzzy"] if pd.notna(row.get("Same_as_person_from_Fuzzy"))
                    else row["person_id"])
                ), axis=1
            )

        # Process Directors
        df_dir["final_person_id"] = get_final_id(df_dir)
        # Create "Name (ID)" string. We group by ID to ensure uniqueness.
        # We take the first name encountered for that ID.
        dir_unique = df_dir.groupby("final_person_id")["Director_name"].first().reset_index()
        dir_options = (dir_unique["Director_name"] + " (" + dir_unique["final_person_id"] + ")").tolist()

        # Process Cast
        df_cast["final_person_id"] = get_final_id(df_cast)
        cast_unique = df_cast.groupby("final_person_id")["Cast_name"].first().reset_index()
        cast_options = (cast_unique["Cast_name"] + " (" + cast_unique["final_person_id"] + ")").tolist()

        return sorted(dir_options), sorted(cast_options)
    
    except Exception as e:
        st.error(f"Error loading talent data: {e}")
        return ["Error Loading Data"], ["Error Loading Data"]

DIR_OPTIONS, CAST_OPTIONS = load_and_resolve_talent()

# --- SECTION 1: MOVIE IDENTITY ---
with st.expander("1. General Information", expanded=True):
    col1, col2, col3 = st.columns(3)
    movie_name = col1.text_input("Movie Name", placeholder="e.g. Pushpa 2")
    primary_lang = col2.selectbox("Primary Language (Original)", ALL_LANGS)
    release_date = col3.date_input("Target Release Date", min_value=date.today())
    
    st.markdown("**Genre Selection**")
    selected_genres = st.multiselect("Select all applicable genres:", ALL_GENRES)

# --- SECTION 2: TALENT PROFILES ---
with st.expander("2. Talent Profiles (Mapped to Unique IDs)", expanded=True):
    st.info("💡 Names are grouped by Final ID. Verify identity via the IMDb link below your selection.")
    
    # --- DIRECTOR LOGIC ---
    st.markdown("#### Director(s)")
    is_new_dir = st.checkbox("New Director? (Not in list)")
    
    if is_new_dir:
        director_input = st.text_input("Enter Director Name")
        dir_id = st.text_input("Enter IMDb ID (optional)", placeholder="nm...")
        if dir_id.startswith("nm"):
            st.markdown(f"🔗 [View Profile on IMDb](https://www.imdb.com/name/{dir_id}/)")
    else:
        director_input = st.selectbox("Search Resolved Directors", [""] + DIR_OPTIONS)
        # DYNAMIC LINK GENERATION
        if director_input and "(" in director_input:
            extracted_id = director_input.split("(")[-1].strip(")")
            st.markdown(f"✅ **Verify Talent:** [View {director_input.split(' (')[0]}'s IMDb Page](https://www.imdb.com/name/{extracted_id}/)")

    st.divider()

    # --- CAST LOGIC ---
    st.markdown("#### Top Cast Members")
    selected_cast_entries = []
    
    for i in range(1, 4):
        c1, c2 = st.columns([3, 1])
        is_new_c = c2.checkbox(f"New Actor {i}", key=f"new_c_{i}")
        
        if is_new_c:
            c_name = c1.text_input(f"Enter Name for Cast {i}", key=f"name_c_{i}")
            c_id = st.text_input(f"ID for Cast {i}", placeholder="nm...", key=f"id_c_{i}")
            if c_id.startswith("nm"):
                st.markdown(f"🔗 [Verify Cast {i} on IMDb](https://www.imdb.com/name/{c_id}/)")
        else:
            c_name = c1.selectbox(f"Search Resolved Cast {i}", [""] + CAST_OPTIONS, key=f"select_c_{i}")
            # DYNAMIC LINK FOR CAST
            if c_name and "(" in c_name:
                extracted_c_id = c_name.split("(")[-1].strip(")")
                st.markdown(f"✅ **Verify Cast {i}:** [View Profile](https://www.imdb.com/name/{extracted_c_id}/)")
        
        if c_name:
            selected_cast_entries.append(c_name)

# --- SECTION 3: STATE-ONLY SHOW COUNTS ---
st.subheader("3. Expected Day 1 Show Counts (Our Movie)")
selected_states = st.multiselect("Select States for Release", ALL_STATES)

show_data = {}
if selected_states:
    cols = st.columns(3)
    for i, state in enumerate(selected_states):
        show_data[state] = cols[i % 3].number_input(f"Total Shows in {state}", min_value=0, step=1, key=f"our_{state}")

# --- SECTION 4: COMPETITOR LANDSCAPE ---
st.divider()
st.subheader("4. Competitor Landscape (For Competition Logic)")
num_competitors = st.number_input("Number of major competitor movies:", min_value=0, max_value=5, step=1)

competitor_list = []
for i in range(int(num_competitors)):
    with st.container(border=True):
        c_col1, c_col2 = st.columns(2)
        c_name = c_col1.text_input(f"Competitor {i+1} Name", key=f"cn_{i}")
        c_lang = c_col2.selectbox(f"Competitor {i+1} Language", ALL_LANGS, key=f"cl_{i}")
        
        st.markdown(f"Shows for {c_name} in your selected states:")
        c_shows = {}
        if selected_states:
            c_show_cols = st.columns(len(selected_states))
            for idx, state in enumerate(selected_states):
                c_shows[state] = c_show_cols[idx].number_input(f"{state}", min_value=0, key=f"cs_{i}_{state}")
        competitor_list.append({"name": c_name, "shows": c_shows})

# --- SUBMISSION & VECTOR PREP ---
if st.button("Finalize Inputs for Model"):
    st.success("Processing inputs...")
    
    # --- 1. RESOLVE DIRECTOR ID ---
    final_director_name = ""
    final_director_id = np.nan
    
    if is_new_dir:
        final_director_name = director_input
        # Use provided ID or default to NaN
        final_director_id = dir_id if dir_id.strip() != "" else np.nan
    elif director_input:
        # Extract ID from "Name (nm12345)"
        final_director_name = director_input.split(" (")[0]
        final_director_id = director_input.split("(")[-1].strip(")")

    # --- 2. RESOLVE CAST IDs ---
    resolved_cast_list = []
    for entry in selected_cast_entries:
        # Check if it was a manual text input (New Actor) or a Selectbox choice
        if "(" in entry and "nm" in entry:
            # Existing Talent
            c_name = entry.split(" (")[0]
            c_id = entry.split("(")[-1].strip(")")
        else:
            # New Talent (either from text_input or name only)
            c_name = entry
            c_id = np.nan # Default to NaN for your team to research
            
        resolved_cast_list.append({"name": c_name, "id": c_id})

    # --- 3. DISPLAY SUMMARY FOR USER ---
    st.markdown("### 📋 Final Data Payload")
    
    col_a, col_b = st.columns(2)
    with col_a:-
        st.write("**Director Mapping:**")
        st.write(f"Name: {final_director_name}")
        st.write(f"ID: {final_director_id}")
        if pd.isna(final_director_id):
            st.warning("⚠️ ID marked as NaN. Our team will verify this creator.")

    with col_b:
        st.write("**Cast Mapping:**")
        cast_summary_df = pd.DataFrame(resolved_cast_list)
        st.table(cast_summary_df)

    # Store for Step 2 (The Model Run)
    st.session_state['processed_talent'] = {
        "director": {"name": final_director_name, "id": final_director_id},
        "cast": resolved_cast_list
    }
