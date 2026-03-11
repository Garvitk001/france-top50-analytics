import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# ==========================================
# 1. PAGE SETUP & EXECUTIVE CSS
# ==========================================
st.set_page_config(page_title="Atlantic Records | France Intel", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; }
    [data-testid="stMetricValue"] { color: #ff4b4b !important; font-weight: 800; font-size: 32px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 2px solid #30363d; padding-bottom: 5px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; color: #8b949e; font-size: 16px; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #ff4b4b !important; border-bottom: 3px solid #ff4b4b; background-color: transparent; }
    .executive-card { background-color: #161b22; border-left: 5px solid #ff4b4b; padding: 20px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BULLETPROOF DATA PIPELINE
# ==========================================
@st.cache_data
def load_and_clean_data():
    file_path = os.path.join('data', 'france_music_kpi_dataset.csv')
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    
    # Safely handle dates to prevent sidebar crashes
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'track_name'])
    
    # Force numeric conversion to stop overlapping Plotly bugs
    numeric_cols = ['popularity', 'duration_ms', 'rank', 'streams', 'days_on_chart', 'previous_rank']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Standardize column names (handles 'artist' vs 'artist_names')
    artist_col = 'artist_names' if 'artist_names' in df.columns else 'artist'
    if artist_col in df.columns:
        df['artist_target'] = df[artist_col]
    else:
        df['artist_target'] = "Unknown Artist"

    # Feature Engineering
    df['is_explicit'] = df['explicit'].astype(bool) if 'explicit' in df.columns else False
    if 'duration_ms' in df.columns:
        df['duration_min'] = df['duration_ms'] / 60000
    else:
        df['duration_min'] = 0

    # Categorize Duration for clean bucket charts
    def categorize_dur(m):
        if m < 2.5: return "Short (< 2.5m)"
        elif m <= 3.5: return "Medium (2.5 - 3.5m)"
        else: return "Long (> 3.5m)"
    df['duration_bucket'] = df['duration_min'].apply(categorize_dur)
    
    # Rank Tier fallback
    if 'rank_tier' not in df.columns:
        df['rank_tier'] = pd.cut(df['rank'], bins=[0, 10, 25, 50], labels=['Top 10', 'Top 25', 'Top 50'])

    return df

df_master = load_and_clean_data()

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/d/d4/Atlantic_Records_logo.svg", width=140)
st.sidebar.markdown("### 🎛️ Data Controls")

if not df_master.empty:
    # 1. Date Range Selector (Safe Mode)
    min_date = df_master['date'].min().date()
    max_date = df_master['date'].max().date()
    
    if min_date == max_date:
        st.sidebar.info(f"Showing data for: {min_date}")
        start_date, end_date = min_date, max_date
    else:
        date_range = st.sidebar.date_input("Analysis Period", [min_date, max_date], min_value=min_date, max_value=max_date)
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = date_range[0], date_range[0]

    # 2. Rank Tier Filter
    tier_filter = st.sidebar.multiselect("Chart Rank Tier", ['Top 10', 'Top 25', 'Top 50'], default=['Top 10', 'Top 25', 'Top 50'])

    # 3. Explicit Content Toggle
    content_filter = st.sidebar.radio("Content Compliance", ["All", "Explicit Only", "Clean Only"])

    # 4. Album Type Filter
    available_formats = df_master['album_type'].unique() if 'album_type' in df_master.columns else []
    format_filter = st.sidebar.multiselect("Release Format", available_formats, default=available_formats)

    # --- APPLY FILTERS ---
    df = df_master[(df_master['date'].dt.date >= start_date) & (df_master['date'].dt.date <= end_date)]
    df = df[df['rank_tier'].isin(tier_filter)]
    if len(available_formats) > 0:
        df = df[df['album_type'].isin(format_filter)]
    
    if content_filter == "Explicit Only": df = df[df['is_explicit'] == True]
    elif content_filter == "Clean Only": df = df[df['is_explicit'] == False]

# ==========================================
# 4. TOP DASHBOARD HEADER & KPIs
# ==========================================
    st.title("🇫🇷 France Top 50 Intelligence")
    st.caption("Atlantic Recording Corporation | Audience Sensitivity & Content Compliance Analysis")

    if df.empty:
        st.warning("⚠️ No data matches the selected filters. Please adjust the sidebar controls.")
    else:
        # KPI PANEL
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tracks Analyzed", len(df))
        k2.metric("Avg Popularity Score", round(df['popularity'].mean(), 1))
        
        exp_share = (df['is_explicit'].sum() / len(df)) * 100
        k3.metric("Explicit Share", f"{round(exp_share, 1)}%")
        k4.metric("Avg Duration", f"{round(df['duration_min'].mean(), 1)}m")
        st.divider()

# ==========================================
# 5. MULTI-TAB ANALYTICAL VIEWS
# ==========================================
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Market Overview", "⚖️ Compliance", "💿 Format & Structure", "📋 Executive Summary"])

        # TAB 1: MARKET OVERVIEW
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Top 5 Artists by Popularity")
                # Clean horizontal bar chart, limited to Top 5
                top_5 = df.groupby('artist_target')['popularity'].mean().reset_index().nlargest(5, 'popularity')
                fig_bar = px.bar(top_5, x='popularity', y='artist_target', orientation='h', 
                                 range_x=[0, 100], color='popularity', color_continuous_scale='Reds', template='plotly_dark')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                st.subheader("Daily Popularity Trend")
                trend = df.groupby('date')['popularity'].mean().reset_index()
                fig_line = px.line(trend, x='date', y='popularity', markers=True, template='plotly_dark')
                st.plotly_chart(fig_line, use_container_width=True)

        # TAB 2: CONTENT COMPLIANCE
        with tab2:
            cl1, cl2 = st.columns([1, 1.5])
            with cl1:
                st.subheader("Explicit vs Clean")
                fig_pie = px.pie(df, names='is_explicit', hole=0.6, color='is_explicit', 
                                 color_discrete_map={True: '#ff4b4b', False: '#1f77b4'}, template='plotly_dark')
                st.plotly_chart(fig_pie, use_container_width=True)
            with cl2:
                st.subheader("Content Compliance Summary Panel")
                # Speedometer Gauge Chart for Explicit Content
                
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = exp_share,
                    title = {'text': "Explicit Sensitivity Risk (%)", 'font': {'size': 20}},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#ff4b4b"},
                        'steps': [
                            {'range': [0, 20], 'color': "#00cc96"}, # Green (Low Risk)
                            {'range': [20, 50], 'color': "#F4D03F"}, # Yellow (Med)
                            {'range': [50, 100], 'color': "#E74C3C"} # Red (High)
                        ]}
                ))
                fig_gauge.update_layout(template='plotly_dark', height=350)
                st.plotly_chart(fig_gauge, use_container_width=True)

        # TAB 3: FORMAT AND STRUCTURE
        with tab3:
            s1, s2 = st.columns(2)
            with s1:
                st.subheader("Album Format Distribution")
                if 'album_type' in df.columns:
                    fmt_counts = df['album_type'].value_counts().reset_index()
                    fig_fmt = px.bar(fmt_counts, x='album_type', y='count', color='album_type', template='plotly_dark')
                    st.plotly_chart(fig_fmt, use_container_width=True)
            with s2:
                st.subheader("Song Duration Preference")
                dur_counts = df['duration_bucket'].value_counts().reset_index()
                fig_dur = px.bar(dur_counts, x='duration_bucket', y='count', template='plotly_dark', color_discrete_sequence=['#ff4b4b'])
                st.plotly_chart(fig_dur, use_container_width=True)
            
            st.divider()
            st.subheader("Rank-Tier Content Attribute Comparison")
            # Grouped bar chart comparing metrics across tiers
            tier_comp = df.groupby('rank_tier').agg({'popularity':'mean', 'duration_min':'mean'}).reset_index()
            fig_tier = px.bar(tier_comp, x='rank_tier', y='popularity', color='rank_tier', template='plotly_dark', title="Avg Popularity by Rank Tier")
            st.plotly_chart(fig_tier, use_container_width=True)

        # TAB 4: EXECUTIVE SUMMARY
        with tab4:
            st.subheader("Market Strategy Summary")
            
            # The "Hit Formula" Generator
            best_format = df['album_type'].mode()[0].capitalize() if 'album_type' in df.columns else "Singles"
            best_length = df['duration_bucket'].mode()[0]
            safety = "Clean" if exp_share < 50 else "Explicit"
            
            st.markdown(f"""
            <div class="executive-card">
            <h4>🎯 The Current "Hit Formula" for France:</h4>
            To maximize playlist placement based on current filtered data, Atlantic Records should prioritize releases that fit this profile:<br><br>
            • <b>Format:</b> {best_format} <br>
            • <b>Length:</b> {best_length} <br>
            • <b>Content:</b> {safety} Lyrics
            </div>
            """, unsafe_allow_html=True)

            c_mov1, c_mov2 = st.columns([1.5, 2])
            with c_mov1:
                st.markdown("#### 🚀 Top Movers (Momentum)")
                if 'previous_rank' in df.columns:
                    df['jump'] = df['previous_rank'] - df['rank']
                    movers = df[df['jump'] > 0].nlargest(3, 'jump')[['track_name', 'artist_target', 'jump']]
                    if not movers.empty:
                        st.table(movers.rename(columns={'track_name': 'Track', 'artist_target': 'Artist', 'jump': 'Places Climbed'}))
                    else:
                        st.info("No tracks climbed today.")
                else:
                    st.info("Momentum data currently unavailable.")

            with c_mov2:
                st.markdown("#### 📥 Filtered Dataset Export")
                st.dataframe(df[['rank', 'track_name', 'artist_target', 'popularity', 'is_explicit', 'duration_min']].head(5), use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Full CSV Report", data=csv, file_name=f"atlantic_intel_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')

else:
    st.error("SYSTEM OFFLINE: Dataset missing. Please ensure 'data/france_music_kpi_dataset.csv' exists.")