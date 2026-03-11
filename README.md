# france-top50-analytics
Automated ETL pipeline and Streamlit analytics dashboard for the Spotify France Top 50 dataset. Built for Atlantic Recording Corporation to analyze market trends and content sensitivity.
# 🇫🇷 France Top 50: Data Pipeline & Analytics

An automated data science project analyzing the Spotify France Top 50 charts. This project tracks market trends, content sensitivity (Explicit vs. Clean), and release formats for Atlantic Recording Corporation.

## 🚀 Features
- **Daily Automation:** Uses GitHub Actions and Spotipy (Spotify Web API) to fetch new data every 24 hours.
- **KPI Dashboard:** Interactive Streamlit interface with real-time analytics.
- **Trend Analysis:** Tracks popularity and track movement (Momentum) over time.
- **Cloud Hosted:** Fully automated ETL pipeline running in the cloud.

## 🛠️ Tech Stack
- **Language:** Python 3.x
- **Libraries:** Pandas, Plotly, Streamlit, Spotipy
- **Automation:** GitHub Actions
- **Data Source:** Spotify Web API

## 📁 Project Structure
- `data/`: Contains the daily updated CSV.
- `scripts/`: Python ETL scripts for data fetching.
- `app.py`: Streamlit dashboard code.

## ⚙️ Setup
1. Clone the repo.
2. Install requirements: `pip install -r requirements.txt`.
3. Set your Spotify API Credentials as environment variables.
4. Run the dashboard: `streamlit run app.py`.
