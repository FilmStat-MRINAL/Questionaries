import streamlit as st
import pandas as pd
from datetime import date
import numpy as np
import requests
import io

# --- CONFIGURATION ---
ALL_STATES = sorted(['Assam', 'Maharashtra', 'Haryana', 'West Bengal', 'Tamil Nadu', 'Andhra Pradesh', 'Karnataka', 'Kerala', 'Delhi', 'Uttar Pradesh', 'Gujarat', 'Punjab', 'Rajasthan', 'Madhya Pradesh', 'Bihar', 'Jharkhand', 'Odisha', 'Chhattisgarh', 'Uttarakhand', 'Himachal Pradesh', 'Jammu and Kashmir', 'Goa', 'Telangana'])
ALL_LANGS = sorted(['Telugu', 'Tamil', 'Malayalam', 'Hindi', 'English', 'Kannada', 'Bengali', 'Marathi'])
ALL_GENRES = sorted(['Action', 'Adult', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy', 'Film Noir', 'Game Show', 'History', 'Horror', 'Musical', 'Music', 'Mystery', 'News', 'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Talk-Show', 'Thriller', 'War', 'Western'])

st.set_page_config(page_title="Box Office Input Portal", layout="wide")

st.title("🎬 Pre-Release Data Capture Portal")
st.markdown("Enter Day 1 release plans.")

# --- DATA LOADING & TALENT RESOLUTION ---
@st.cache_data
def load_and_resolve_talent():
    if "DIR_ID" not in st.secrets or "CAST_ID" not in st.secrets:
        st.error("Secrets missing! Add DIR_ID and CAST_ID in Streamlit Settings.")
        return ["Secrets Missing"], ["Secrets Missing"]

    def download_file_from_google_drive(id):
        URL = "https://docs.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(URL, params={'id': id}, stream=True)
        token = None
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                token = value
                break
        if token:
            response = session.get(URL, params={'id': id, 'confirm': token}, stream=True)
        return response.content

    try:
        dir_content = download_file_from_google_drive(st.secrets["DIR_ID"])
        cast_content = download_file_from_google_drive(st.secrets["CAST_ID"])
        df_dir = pd.read_pickle(io.BytesIO(dir_content))
        df_cast = pd.read_pickle(io.BytesIO(cast_content))

        def get_final_id(df):
            return df.apply(lambda row: (
                row["Same_as_person"] if pd.notna(row.get("Same_as_person"))
                else (row["Same_as_person_from_Fuzzy"] if pd.notna(row.get("Same_as_person_from_Fuzzy"))
                else row["person_id"])
            ), axis=1)

        df_dir["final_person_id"] = get_final_id(df_dir)
        dir_unique = df_dir.groupby("final_person_id")["Director_name"].first().reset_index()
        dir_options = (dir_unique["Director_name"] + " (" + dir_unique["final_person_id"] + ")").tolist()

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
    
    st.markdown("**Genre Selection (Maximum 3)**")
    selected_genres = st.multiselect("Select genres:", ALL_GENRES, max_selections=3)
    
    st.markdown("**Brief Movie Plot**")
    movie_plot = st.text_area("Enter a short summary of the movie storyline:", placeholder="Brief plot...")

# --- SECTION 2: TALENT PROFILES ---
with st.expander("2. Talent Profiles", expanded=True):
    st.info("💡 Verify identity via the IMDb link below your selection.")
    
    st.markdown("#### Director(s)")
    is_new_dir = st.checkbox("Director not in the drop-down?")
    if is_new_dir:
        director_input = st.text_input("Enter Director Name")
        dir_id = st.text_input("Enter IMDb ID (if possible)", placeholder="nm...")
        if dir_id.startswith("nm"):
            st.markdown(f"🔗 [View Profile on IMDb](https://www.imdb.com/name/{dir_id}/)")
    else:
        director_input = st.selectbox("Search Resolved Directors", [""] + DIR_OPTIONS)
        if director_input and "(" in director_input:
            extracted_id = director_input.split("(")[-1].strip(")")
            st.markdown(f"✅ **Verify Talent:** [View {director_input.split(' (')[0]}'s IMDb Page](https://www.imdb.com/name/{extracted_id}/)")

    st.divider()

    st.markdown("#### Top 5 Cast Members (In order of importance)")
    selected_cast_entries = []
    for i in range(1, 6): # Increased to 5
        c1, c2 = st.columns([3, 1])
        is_new_c = c2.checkbox(f"Actor {i} not in list", key=f"new_c_{i}")
        if is_new_c:
            c_name = c1.text_input(f"Enter Name for Cast {i}", key=f"name_c_{i}")
            c_id = st.text_input(f"ID for Cast {i}", placeholder="nm...", key=f"id_c_{i}")
            if c_id.startswith("nm"):
                st.markdown(f"🔗 [Verify Cast {i} on IMDb](https://www.imdb.com/name/{c_id}/)")
        else:
            c_name = c1.selectbox(f"Search Resolved Cast {i}", [""] + CAST_OPTIONS, key=f"select_c_{i}")
            if c_name and "(" in c_name:
                extracted_c_id = c_name.split("(")[-1].strip(")")
                st.markdown(f"✅ **Verify Cast {i}:** [View Profile](https://www.imdb.com/name/{extracted_c_id}/)")
        if c_name:
            selected_cast_entries.append(c_name)

# --- SECTION 3: STATE-ONLY SHOW COUNTS ---
st.subheader("3. Expected Day 1 Show Counts")
selected_states = st.multiselect("Select States for Release", ALL_STATES)

show_data = {}
if selected_states:
    cols = st.columns(3)
    for i, state in enumerate(selected_states):
        show_data[state] = cols[i % 3].number_input(f"Total Shows in {state}", min_value=0, step=1, key=f"our_{state}")

# --- SECTION 4: COMPETITOR LANDSCAPE ---
st.divider()
st.subheader("4. Competitor Landscape")
num_competitors = st.number_input("Number of major competitor movies you are aware of:", min_value=0, max_value=5, step=1)

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
                c_shows[state] = c_show_cols[idx].number_input(f"{state}", min_value=0, key=f"cs_{i}_{state}", label_visibility="collapsed")
        competitor_list.append({"name": c_name, "lang": c_lang, "shows": c_shows})

# --- SUBMISSION ---
if st.button("Finalize Inputs for Model"):
    st.success("Processing inputs...")
    
    # Resolve IDs for Director and Cast
    final_dir_id = director_input.split("(")[-1].strip(")") if not is_new_dir and "(" in director_input else (dir_id if is_new_dir else np.nan)
    
    resolved_cast = []
    for entry in selected_cast_entries:
        cid = entry.split("(")[-1].strip(")") if "(" in entry else np.nan
        resolved_cast.append(cid)
    # Ensure list has 5 entries (pad with NaN if fewer provided)
    while len(resolved_cast) < 5:
        resolved_cast.append(np.nan)

    # Build the final DataFrame
    data_dict = {
        "movie_name": movie_name,
        "primary_lang": primary_lang,
        "release_date": release_date,
        "genres": [selected_genres],
        "plot": movie_plot,
        "director_id": final_dir_id,
        **{f"cast_{i+1}_id": resolved_cast[i] for i in range(5)},
        "user_show_distribution": [show_data],
        "competition_data": [competitor_list]
    }
    final_df = pd.DataFrame(data_dict)
    
    st.session_state['final_df'] = final_df
    st.markdown("### 📋 Final Data Payload Prepared")
    st.dataframe(final_df)

# --- HOW TO GET THE DATA AUTOMATICALLY ---
# Option: Add a hidden section or a direct trigger to write to a cloud CSV/Google Sheet.
