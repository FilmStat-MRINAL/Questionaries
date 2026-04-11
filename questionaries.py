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

# Helper function to resolve IDs from strings
def extract_id(entry):
    if entry and "(" in entry:
        return entry.split("(")[-1].strip(")")
    return np.nan

# --- SECTION 1: MOVIE IDENTITY ---
with st.expander("1. General Information", expanded=True):
    col1, col2, col3 = st.columns(3)
    movie_name = col1.text_input("Movie Name", placeholder="e.g. Pushpa 2")
    primary_lang = col2.selectbox("Primary Language (Original)", ALL_LANGS)
    release_date = col3.date_input("Target Release Date", min_value=date.today())
    st.divider()
    
    # New Questions Block
    q_col1, q_col2, q_col3 = st.columns(3)
    is_rerelease = q_col1.radio("Is it a re-release of an old movie?", ["No", "Yes"], horizontal=True)
    proposed_budget = q_col2.number_input("Proposed Budget (in Crores)", min_value=0.0, step=1.0)
    is_remake = q_col3.checkbox("Is it a Remake from another language?")
    
    original_remake_lang = ""
    if is_remake:
        original_remake_lang = q_col3.selectbox("Original Language of the movie:", [""] + ALL_LANGS)

    st.divider()    
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
        dir_id_input = st.text_input("Enter IMDb ID (if possible)", placeholder="nm...", key="main_dir_id")
        if dir_id_input.startswith("nm"):
            st.markdown(f"🔗 [View Profile on IMDb](https://www.imdb.com/name/{dir_id_input}/)")
    else:
        director_input = st.selectbox("Search Resolved Directors", [""] + DIR_OPTIONS, key="main_dir_select")
        if director_input and "(" in director_input:
            extracted_id = extract_id(director_input)
            st.markdown(f"✅ **Verify Talent:** [View IMDb Page](https://www.imdb.com/name/{extracted_id}/)")

    st.divider()

    st.markdown("#### Top 5 Cast Members (In order of importance)")
    selected_cast_entries = []
    for i in range(1, 6):
        c1, c2 = st.columns([3, 1])
        is_new_c = c2.checkbox(f"Actor {i} not in list", key=f"new_c_{i}")
        if is_new_c:
            c_name = c1.text_input(f"Enter Name for Cast {i}", key=f"name_c_{i}")
            c_id = c1.text_input(f"ID for Cast {i}", placeholder="nm...", key=f"id_c_{i}")
            if c_id and c_id.startswith("nm"):
                st.markdown(f"🔗 [Verify Cast {i} on IMDb](https://www.imdb.com/name/{c_id}/)")
        else:
            c_name = c1.selectbox(f"Search Resolved Cast {i}", [""] + CAST_OPTIONS, key=f"select_c_{i}")
            if c_name and "(" in c_name:
                extracted_c_id = extract_id(c_name)
                st.markdown(f"✅ **Verify Cast {i}:** [View Profile](https://www.imdb.com/name/{extracted_c_id}/)")
        
        if c_name:
            selected_cast_entries.append({"name": c_name, "is_new": is_new_c, "manual_id": c_id if is_new_c else None})

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
st.caption("Optional: Providing details for competitors helps the model calculate 'Competition Quality'.")

num_competitors = st.number_input("Number of major competitor movies:", min_value=0, max_value=5, step=1)

competitor_list = []
for i in range(int(num_competitors)):
    with st.expander(f"🎬 Competitor Movie {i+1}", expanded=False):
        comp_info = {}
        c_col1, c_col2, c_col3 = st.columns(3)
        comp_info['name'] = c_col1.text_input(f"Name", key=f"cn_{i}")
        comp_info['lang'] = c_col2.selectbox(f"Language", [""] + ALL_LANGS, key=f"cl_{i}")
        comp_info['rel_date'] = c_col3.date_input(f"Release Date", value=None, key=f"cd_{i}")
        
        comp_info['genres'] = st.multiselect(f"Genres (Max 3)", ALL_GENRES, max_selections=3, key=f"cg_{i}")
        
        # Competitor Director
        st.markdown("**Competitor Talent**")
        d_col1, d_col2 = st.columns([3, 1])
        c_is_new_dir = d_col2.checkbox("Director not in list", key=f"c_new_dir_{i}")
        if c_is_new_dir:
            comp_info['director'] = d_col1.text_input("Director Name", key=f"c_dir_name_{i}")
            c_dir_id = d_col1.text_input("IMDb ID", placeholder="nm...", key=f"c_dir_id_{i}")
            if c_dir_id.startswith("nm"):
                st.markdown(f"🔗 [Verify Director on IMDb](https://www.imdb.com/name/{c_dir_id}/)")
        else:
            comp_info['director'] = d_col1.selectbox("Director", [""] + DIR_OPTIONS, key=f"c_dir_sel_{i}")
            if comp_info['director'] and "(" in comp_info['director']:
                st.markdown(f"🔗 [Verify IMDb Profile](https://www.imdb.com/name/{extract_id(comp_info['director'])}/)")

        # Competitor Cast (5 members)
        comp_info['cast_ids'] = []
        for j in range(1, 6):
            cast_col1, cast_col2 = st.columns([3, 1])
            c_is_new_cast = cast_col2.checkbox(f"Actor {j} not in list", key=f"c_new_cast_{i}_{j}")
            if c_is_new_cast:
                c_c_name = cast_col1.text_input(f"Actor {j} Name", key=f"c_cast_name_{i}_{j}")
                c_c_id = cast_col1.text_input(f"Actor {j} ID", placeholder="nm...", key=f"c_cast_id_{i}_{j}")
                comp_info['cast_ids'].append(c_c_id if c_c_id else np.nan)
            else:
                c_c_sel = cast_col1.selectbox(f"Actor {j}", [""] + CAST_OPTIONS, key=f"c_cast_sel_{i}_{j}")
                comp_info['cast_ids'].append(extract_id(c_c_sel))

        st.markdown("**Estimated Shows in selected states:**")
        c_shows = {}
        if selected_states:
            c_show_cols = st.columns(3)
            for idx, state in enumerate(selected_states):
                c_shows[state] = c_show_cols[idx % 3].number_input(f"{state} shows", min_value=0, key=f"cs_{i}_{state}")
        comp_info['shows'] = c_shows
        competitor_list.append(comp_info)

# --- SUBMISSION ---
if st.button("Finalize Inputs for Model"):
    st.success("Processing inputs...")
    
    # 1. Resolve Main Director ID
    main_dir_id = dir_id_input if is_new_dir else extract_id(director_input)
    
    # 2. Resolve Main Cast IDs
    main_cast_ids = []
    for entry in selected_cast_entries:
        cid = entry['manual_id'] if entry['is_new'] else extract_id(entry['name'])
        main_cast_ids.append(cid)
    while len(main_cast_ids) < 5: main_cast_ids.append(np.nan)

    # Build the final DataFrame
    data_dict = {
        "movie_name": movie_name,
        "primary_lang": primary_lang,
        "release_date": release_date,
        "genres": [selected_genres],
        "plot": movie_plot,
        "director_id": main_dir_id,
        **{f"cast_{i+1}_id": main_cast_ids[i] for i in range(5)},
        "user_show_distribution": [show_data],
        "competition_details": [competitor_list]
    }
    final_df = pd.DataFrame(data_dict)
    
    st.session_state['final_df'] = final_df
    st.markdown("### 📋 Final Data Payload Prepared")
    st.dataframe(final_df)
