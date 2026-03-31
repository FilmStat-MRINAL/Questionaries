# Questionaries
A Streamlit-based input portal for predicting movie footfalls
# 🎬 Box Office Prediction: Input Module

This repository contains the web-based interface for capturing movie release data. The inputs collected here are designed to feed directly into a high-performance **Prediction Pipeline**.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Python-based)
* **Backend:** Regression
* **Data Processing:** Pandas, NumPy

## 📝 Features
- **Primary Language Mapping:** Primary Release Language
- **Release Date:** Expected Release Date
- **States:** In which states it would be released
- **Show Count:** How many shows in which state are planned
- **Talent Context:** Who are the top 10 cast and Crew. If possible, use IMDb for finding exact spelling of the individuals
- **Competition Scaling:** Are you aware of any other movie that would be released on the same period? If yes, do you have any guess of their planned show numbers?

## 🏃 How to Run Locally
1. Clone the repo
2. Install requirements: `pip install -r requirements.txt`
3. Run app: `streamlit run app.py`
