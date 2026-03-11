import pandas as pd
import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

# 1. LOAD SECURE KEYS
load_dotenv() # This looks for a file named .env
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

def get_spotify_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ ERROR: Keys not found in .env file!")
        return None
        
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_str.encode()).decode()
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    res = requests.post(url, headers=headers, data=data)
    return res.json().get('access_token') if res.status_code == 200 else None

# ... (rest of your fetch_top_50_full_columns and file saving logic remains the same)
def fetch_top_50_full_columns(token):
    all_tracks = []
    today = datetime.now().strftime('%Y-%m-%d')
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    
    for i in range(5): # Fetching 50 tracks in batches of 10
        params = {'q': 'Top 50 France', 'type': 'track', 'limit': 10, 'offset': i * 10}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            items = response.json().get('tracks', {}).get('items', [])
            for rank_idx, t in enumerate(items):
                current_rank = (i * 10) + rank_idx + 1
                
                # Mapping all requested columns
                track_data = {
                    'rank': current_rank,
                    'uri': t.get('uri'),
                    'artist_names': ", ".join([a['name'] for a in t['artists']]),
                    'track_name': t['name'],
                    'source': 'Spotify API Automation',
                    'peak_rank': current_rank, # Placeholder: updated via logic below
                    'previous_rank': 0,        # Placeholder
                    'days_on_chart': 1,        # Placeholder
                    'streams': 0,              # Spotify Search API doesn't provide daily stream counts
                    'date': today,
                    'track_id': t.get('id'),
                    'rank_tier': 'Top 10' if current_rank <= 10 else ('Top 25' if current_rank <= 25 else 'Top 50'),
                    'popularity': t.get('popularity', 0),
                    'duration_ms': t.get('duration_ms', 0),
                    'explicit': t.get('explicit', False),
                    'album_type': t['album']['album_type'],
                    'total_tracks': t['album']['total_tracks'],
                    'duration_min': round(t['duration_ms'] / 60000, 2)
                }
                all_tracks.append(track_data)
        else:
            print(f"⚠️ Error on batch {i}: {response.status_code}")
            
    return pd.DataFrame(all_tracks)

# 2. RUN AND APPEND
token = get_spotify_token()
if token:
    new_data = fetch_top_50_full_columns(token)
    full_path = os.path.join('data', 'france_music_kpi_dataset.csv')

    if not new_data.empty:
        if os.path.exists(full_path):
            old_df = pd.read_csv(full_path)
            
            # --- ADVANCED LOGIC FOR SMART COLUMNS ---
            # We look at old_df to calculate actual peak_rank and days_on_chart
            for index, row in new_data.iterrows():
                history = old_df[old_df['track_id'] == row['track_id']]
                if not history.empty:
                    new_data.at[index, 'peak_rank'] = min(history['rank'].min(), row['rank'])
                    new_data.at[index, 'days_on_chart'] = len(history) + 1
                    new_data.at[index, 'previous_rank'] = history.sort_values('date').iloc[-1]['rank']
            
            # Combine and save
            final_df = pd.concat([old_df, new_data]).drop_duplicates(subset=['date', 'track_id'], keep='last')
            final_df.to_csv(full_path, index=False)
            print(f"🚀 SUCCESS! {len(new_data)} tracks added to {full_path}. Total rows now: {len(final_df)}")
        else:
            # First time setup
            if not os.path.exists('data'): os.makedirs('data')
            new_data.to_csv(full_path, index=False)
            print(f"🆕 Initialized new dataset with all columns in {full_path}")