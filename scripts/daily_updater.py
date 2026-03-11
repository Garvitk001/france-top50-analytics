import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
from datetime import datetime

# 1. SETUP SPOTIFY API
client_id = os.getenv("911af7db8c9e4a59aed82c58f014ef81")
client_secret = os.getenv("f82885bf343a436094db338302253b5d")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id, client_secret=client_secret
))

def fetch_france_top_50():
    # Playlist ID for France Top 50 (Global/National Charts)
    playlist_id = '37i9dQZEVXbIPWwYss6Pwt' 
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    new_data = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for i, item in enumerate(tracks):
        track = item['track']
        
        # Metadata Extraction (Creating the "Missing" Columns)
        track_info = {
            'rank': i + 1,
            'uri': track['uri'],
            'artist_names': ", ".join([artist['name'] for artist in track['artists']]),
            'track_name': track['name'],
            'source': 'Spotify API',
            'peak_rank': i + 1, # Placeholder for logic
            'previous_rank': i + 1,
            'days_on_chart': 1,
            'streams': 0, # Note: API doesn't provide stream counts
            'date': today,
            'track_id': track['id'],
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'album_type': track['album']['album_type'],
            'total_tracks': track['album']['total_tracks'],
            'duration_min': round(track['duration_ms'] / 60000, 2)
        }
        
        # Assign Rank Tier
        if track_info['rank'] <= 10:
            track_info['rank_tier'] = 'Top 10'
        elif track_info['rank'] <= 25:
            track_info['rank_tier'] = 'Top 25'
        else:
            track_info['rank_tier'] = 'Top 50'
            
        new_data.append(track_info)
    
    return pd.DataFrame(new_data)

# 2. LOAD, APPEND, AND SAVE
csv_path = 'france_music_kpi_dataset.csv' # Adjust if in data/ folder

new_df = fetch_france_top_50()

if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path)
    # Check if we already added today's data to prevent duplicates
    if new_df['date'].iloc[0] not in existing_df['date'].values:
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
        final_df.to_csv(csv_path, index=False)
        print(f"Successfully added 50 rows for {new_df['date'].iloc[0]}")
    else:
        print("Data for today already exists in CSV.")
else:
    new_df.to_csv(csv_path, index=False)
    print("Created new CSV file with 50 rows.")