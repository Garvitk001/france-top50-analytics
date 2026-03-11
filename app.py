import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="France Top 50 Advanced Analytics",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/france_music_kpi_dataset.csv")
    # Clean up duration
    df['duration_min'] = df['duration_ms'] / 60000
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Data file not found. Ensure 'france_music_kpi_dataset.csv' is in the 'data' folder.")
    st.stop()

# --- SIDEBAR CONTROL PANEL ---
with st.sidebar:
    st.title("🎛️ Atlantic Records Control Panel")
    
    # Select specific days or a range
    min_day = int(df['date'].min())
    max_day = int(df['date'].max())
    selected_days = st.slider("Select Day Range (History):", min_day, max_day, (min_day, max_day))
    
    # Filters
    rank_tier_filter = st.multiselect("Rank Tier:", df["rank_tier"].unique(), default=df["rank_tier"].unique())
    format_filter = st.multiselect("Release Format:", df["album_type"].unique(), default=df["album_type"].unique())

# Apply Filters
filtered_df = df[
    (df['date'] >= selected_days[0]) & 
    (df['date'] <= selected_days[1]) &
    (df['rank_tier'].isin(rank_tier_filter)) &
    (df['album_type'].isin(format_filter))
]

# --- MAIN DASHBOARD HEADER ---
st.title("🇫🇷 France Top 50: Advanced Cultural & Structural Analysis")
st.markdown("Evaluating explicit content sensitivity, structural norms, and catalog velocity for the French market.")

# --- ADVANCED KPIS (Based on the latest day in selection) ---
latest_day_df = filtered_df[filtered_df['date'] == selected_days[1]]
total_tracks = len(latest_day_df)
explicit_count = latest_day_df[latest_day_df['explicit'] == True].shape[0]
clean_dominance = ((total_tracks - explicit_count) / total_tracks * 100) if total_tracks > 0 else 0
avg_duration = latest_day_df['duration_min'].mean()

st.subheader(f"Key Metrics (Snapshot for Day {selected_days[1]})")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tracks", total_tracks)
col2.metric("Explicit Tracks", explicit_count)
col3.metric("Clean Dominance Ratio", f"{clean_dominance:.1f}%", delta="Cultural Sensitivity KPI")
col4.metric("Optimal Duration Avg", f"{avg_duration:.2f} m", delta="Structural KPI")
st.divider()

# --- ADVANCED TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Time-Series Trends", 
    "🎯 Album Impact & Structure", 
    "⏱️ Duration Sweet-Spot", 
    "🚀 Momentum Tracker"
])

with tab1:
    st.subheader("Popularity Trends: Explicit vs. Clean Over Time")
    # Calculate daily average popularity for explicit vs clean
    trend_df = filtered_df.groupby(['date', 'explicit'])['popularity'].mean().reset_index()
    trend_df['explicit'] = trend_df['explicit'].map({True: 'Explicit', False: 'Clean'})
    
    fig_trend = px.line(
        trend_df, x='date', y='popularity', color='explicit',
        markers=True,
        color_discrete_map={'Explicit': '#EF553B', 'Clean': '#00CC96'},
        labels={'date': 'Day', 'popularity': 'Average Popularity Score', 'explicit': 'Content Type'}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.subheader("Album Size Impact Index (Dilution vs. Concentration)")
    st.markdown("Does releasing a massive 20+ track album dilute individual track popularity?")
    
    # Scatter plot of Total Tracks vs Popularity
    fig_album = px.scatter(
        filtered_df, x='total_tracks', y='popularity', color='album_type',
        size='streams', hover_data=['track_name', 'artist_names'],
        labels={'total_tracks': 'Total Tracks in Album', 'popularity': 'Track Popularity', 'streams': 'Streams'},
        title="Album Size vs. Track Popularity"
    )
    st.plotly_chart(fig_album, use_container_width=True)

with tab3:
    st.subheader("Format Preference: The Duration Sweet-Spot")
    # Histogram of duration
    fig_duration = px.histogram(
        filtered_df, x='duration_min', color='rank_tier',
        nbins=20, marginal="box",
        labels={'duration_min': 'Song Duration (Minutes)', 'rank_tier': 'Rank Tier'},
        title="Distribution of Song Durations by Rank Tier"
    )
    st.plotly_chart(fig_duration, use_container_width=True)

with tab4:
    st.subheader("Top Momentum Tracks (Rising Stars)")
    st.markdown("Tracks with the highest positive movement between their previous rank and peak rank.")
    
    momentum_df = latest_day_df.copy()
    momentum_df['rank_jump'] = momentum_df['previous_rank'] - momentum_df['rank']
    # Filter only tracks that are actually moving up (positive jump)
    rising_stars = momentum_df[momentum_df['rank_jump'] > 0].sort_values(by='rank_jump', ascending=False)
    
    st.dataframe(
        rising_stars[['rank', 'track_name', 'artist_names', 'rank_jump', 'days_on_chart', 'explicit']],
        use_container_width=True,
        hide_index=True
    )