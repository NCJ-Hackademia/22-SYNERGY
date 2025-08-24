# spotify_data_fetcher.py

def get_user_market(sp_client):
    """
    Fetches the user's country code (market) from their profile.
    """
    if not sp_client:
        return None
    try:
        return sp_client.current_user().get('country')
    except Exception as e:
        print(f"Could not fetch user's market: {e}")
        return None

def get_playlist_uri(sp_client, playlist_name):
    """
    Searches for a playlist by name and returns the URI of the top result.
    """
    if not sp_client:
        return None
    try:
        print(f"Searching for playlist: {playlist_name}")
        # Try with quoted search term for exact match
        results = sp_client.search(q=f'playlist:"{playlist_name}"', type='playlist', limit=1)
        if results is None:
            print(f"API returned no response for {playlist_name}, trying unquoted search")
            # Fallback to unquoted search if quoted fails
            results = sp_client.search(q=f'playlist:{playlist_name}', type='playlist', limit=1)
        if results is None or not isinstance(results, dict):
            print(f"API returned invalid response for {playlist_name}: {results}")
            return None
        playlists = results.get('playlists', {}).get('items', [])
        if playlists:
            print(f"Found playlist: {playlists[0]['name']} with URI: {playlists[0]['uri']}")
            return playlists[0]['uri']
        else:
            print(f"No playlist found for: {playlist_name}")
            return None
    except Exception as e:
        print(f"Error searching for playlist {playlist_name}: {e}")
        return None