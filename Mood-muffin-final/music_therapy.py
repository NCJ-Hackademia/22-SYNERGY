# music_therapy.py

def get_stage_for_emotion(emotion_analysis):
    """
    The "GPS Navigator": Determines the CURRENT stage name based on emotion and intensity.
    """
    emotion, intensity = emotion_analysis.split('-')

    stage_index = 0  # Default to stage 1 for Low intensity
    if intensity == 'Medium':
        stage_index = 1  # Stage 2
    elif intensity == 'High':
        stage_index = 2  # Stage 3

    journeys = {
        'Sadness': ['Acknowledge & Validate', 'Process & Reflect', 'Empower & Uplift'],
        'Anger': ['Match the Intensity', 'Channel & Process', 'Cool Down & Calm'],
        'Distress': ['Safe Space', 'Gentle Reflection', 'Finding Hope'],
        'Joy': ['Embrace the Joy', 'Amplify the Feeling', 'Sustained Happiness'],
        'Default': ['Acknowledgment', 'Reflection', 'Empowerment']
    }
    
    stage_names = journeys.get(emotion, journeys['Default'])
    
    # Ensure we don't go out of bounds
    if stage_index >= len(stage_names):
        stage_index = len(stage_names) - 1
        
    return stage_names[stage_index]

def create_emotional_journey_plan(emotion_analysis):
    """
    Creates the FULL three-stage plan with playlist URIs for each stage.
    """
    emotion, _ = emotion_analysis.split('-')  # We only need the emotion type

    # Map each stage to the corresponding playlist URI
    journeys = {
        'Sadness': [
            {'label': 'Acknowledge & Validate', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX7qK8ma5wgG1'},
            {'label': 'Process & Reflect', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'},
            {'label': 'Empower & Uplift', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX0XUsuxWHRQd'}
        ],
        'Anger': [
            {'label': 'Match the Intensity', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'},
            {'label': 'Channel & Process', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX0XUsuxWHRQd'},
            {'label': 'Cool Down & Calm', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'}
        ],
        'Distress': [
            {'label': 'Safe Space', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'},
            {'label': 'Gentle Reflection', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'},
            {'label': 'Finding Hope', 'playlist_uri': 'spotify:playlist:37i9dQZF1DX4sWSpwq3LiO'}
        ],
        'Joy': [
            {'label': 'Embrace the Joy', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'},
            {'label': 'Amplify the Feeling', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'},
            {'label': 'Sustained Happiness', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'}
        ],
        'Default': [
            {'label': 'Acknowledgment', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'},
            {'label': 'Reflection', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'},
            {'label': 'Empowerment', 'playlist_uri': 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'}
        ]
    }

    return journeys.get(emotion, journeys['Default'])