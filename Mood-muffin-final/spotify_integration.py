# spotify_integration.py
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session, url_for

SCOPE = "user-top-read user-read-private user-modify-playback-state user-read-playback-state user-library-read user-library-modify playlist-modify-public playlist-modify-private streaming user-read-email"

def get_spotify_oauth():
    """
    Creates and returns a SpotifyOAuth object.
    """
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=url_for('main.callback', _external=True),
        scope=SCOPE,
        cache_path=None
    )

def get_current_device_id():
    """
    Returns the device ID of the current login session (if available).
    """
    token_info = session.get('spotify_token_info', None)
    device_id = None
    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        devices = sp.devices().get('devices', [])
        if devices:
            device_id = devices[0].get('id')
    return device_id

def get_spotify_client():
    """
    Checks for a token in the session, refreshes it if necessary,
    and returns an authenticated Spotipy client.
    """
    token_info = session.get('spotify_token_info', None)
    if not token_info:
        return None

    sp_oauth = get_spotify_oauth()
    try:
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['spotify_token_info'] = token_info
    except Exception as e:
        print(f"Error refreshing Spotify token: {e}")
        session.clear()
        return None

    return spotipy.Spotify(auth=token_info['access_token'])

