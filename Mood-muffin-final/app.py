# app.py (ALL ROUTES IN ONE FILE, NO BLUEPRINTS)

from flask import Flask, render_template, redirect, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room
import os, time, uuid
from threading import Lock
from dotenv import load_dotenv

# Gemini imports
from google.generativeai import configure, GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerateContentResponse

# Spotify imports
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = "http://localhost:5000/callback"   # you can change this if needed

if not GEMINI_API_KEY:
    raise ValueError("🚨 GEMINI_API_KEY environment variable not set")

# -----------------------
# Initialize Flask + SocketIO
# -----------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# -----------------------
# Gemini Config
# -----------------------
configure(api_key=GEMINI_API_KEY)
gemini_model = GenerativeModel('gemini-1.5-flash')

# -----------------------
# Spotify Helpers
# -----------------------
def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-email user-read-playback-state user-modify-playback-state streaming"
    )

def get_spotify_client():
    token_info = session.get("spotify_token_info", None)
    if not token_info:
        return None
    return spotipy.Spotify(auth=token_info.get("access_token"))

# -----------------------
# Dashboard Routes
# -----------------------
@app.route('/')
def home():
    return render_template("dashboard.html", user="User")

@app.route('/chat')
def chat():
    return redirect('/aichat')

@app.route('/game')
def game():
    return redirect('/whack-a-mole')

@app.route('/add')
def add():
    return redirect('/journalling')

# -----------------------
# AI Chat Routes
# -----------------------
@app.route('/aichat')
def aichat():
    return render_template("aichat.html")

waiting_queue = []
pairs = {}
lock = Lock()

def detect_unsafe_content(model: GenerativeModel, message: str) -> bool:
    try:
        keywords = [
            "kill myself", "end my life", "hurt myself", "self harm", "suicide",
            "cut myself", "want to die", "no reason to live", "take my life"
        ]
        message_lower = message.lower()
        if any(kw in message_lower for kw in keywords):
            response: GenerateContentResponse = model.generate_content(
                message,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
                }
            )
            if not response.candidates:
                return True
            for rating in response.prompt_feedback.safety_ratings:
                if rating.category == HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT and rating.probability >= 0.8:
                    return True
        return False
    except Exception as e:
        print(f"Error in content safety check: {e}")
        return True

@socketio.on('connect')
def handle_connect():
    print(f"User connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"User disconnected: {request.sid}")
    with lock:
        if request.sid in waiting_queue:
            waiting_queue.remove(request.sid)
        for room_id, users in list(pairs.items()):
            if request.sid in users:
                other_sid = [u for u in users if u != request.sid][0]
                socketio.emit('stranger_disconnected', to=other_sid)
                leave_room(room_id, request.sid)
                leave_room(room_id, other_sid)
                del pairs[room_id]
                break

@socketio.on('start_chat')
def start_chat():
    sid = request.sid
    with lock:
        waiting_queue.append(sid)
        if len(waiting_queue) >= 2:
            sid1 = waiting_queue.pop(0)
            sid2 = waiting_queue.pop(0)
            room_id = str(uuid.uuid4())
            pairs[room_id] = [sid1, sid2]
            join_room(room_id, sid=sid1)
            join_room(room_id, sid=sid2)
            socketio.emit('chat_started', {'room_id': room_id}, to=sid1)
            socketio.emit('chat_started', {'room_id': room_id}, to=sid2)
            socketio.emit('message', {'text': 'You are now connected to a stranger!'}, room=room_id)

@socketio.on('send_message')
def handle_message(data):
    room_id = data['room_id']
    message = data['message']
    sid = request.sid
    if detect_unsafe_content(gemini_model, message):
        socketio.emit('message', {'text': '⚠️ Your message was flagged as unsafe and not sent.'}, to=sid)
        return
    with lock:
        if room_id in pairs and sid in pairs[room_id]:
            other_sid = [u for u in pairs[room_id] if u != sid][0]
            socketio.emit('message', {'text': message, 'from': 'stranger'}, to=other_sid)
            socketio.emit('message', {'text': message, 'from': 'you'}, to=sid)

@socketio.on('end_chat')
def end_chat(data):
    room_id = data['room_id']
    sid = request.sid
    with lock:
        if room_id in pairs and sid in pairs[room_id]:
            other_sid = [u for u in pairs[room_id] if u != sid][0]
            socketio.emit('stranger_disconnected', to=other_sid)
            leave_room(room_id, sid)
            leave_room(room_id, other_sid)
            del pairs[room_id]

# -----------------------
# Journalling Routes
# -----------------------
@app.route('/journalling')
def journalling():
    sp = get_spotify_client()
    user_profile = None
    if sp:
        try:
            user_profile = sp.current_user()
        except Exception:
            session.clear()
    return render_template('journal.html', user_profile=user_profile)

@app.route('/login')
def login():
    auth_url = get_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    token_info = get_spotify_oauth().get_access_token(request.args.get('code'))
    session['spotify_token_info'] = token_info
    return redirect('/journalling')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/journalling')

@app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    try:
        data = request.get_json()
        journal_text = data.get('text', '')
        if not journal_text:
            return jsonify({'error': 'No text provided'}), 400
        # Just a placeholder sentiment
        sentiment = "calm" if "happy" in journal_text.lower() else "stressed"
        stage_name = "relaxation" if sentiment == "calm" else "uplifting"
        return jsonify({'sentiment': sentiment, 'stage': stage_name})
    except Exception as e:
        print(f"A critical error occurred in /analyze_sentiment: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@app.route('/create_journey', methods=['POST'])
def create_journey():
    sp_client = get_spotify_client()
    if not sp_client:
        return jsonify({'error': 'Spotify login required.'}), 401
    try:
        data = request.get_json()
        sentiment = data.get('sentiment', '')
        if not sentiment:
            return jsonify({'error': 'No sentiment provided'}), 400
        journey_playlists = [
            {"label": "Stage 1", "playlist_uri": "spotify:playlist:example1"},
            {"label": "Stage 2", "playlist_uri": "spotify:playlist:example2"},
            {"label": "Stage 3", "playlist_uri": "spotify:playlist:example3"}
        ]
        return jsonify({'journey': journey_playlists})
    except Exception as e:
        print(f"A critical error occurred in /create_journey: {e}")
        return jsonify({'error': f'Failed to create music journey: {str(e)}'}), 500

@app.route('/get_token')
def get_token():
    token_info = session.get('spotify_token_info', None)
    if not token_info:
        return jsonify({'error': 'User not logged in'}), 401
    return jsonify({'access_token': token_info.get('access_token')})

@app.route('/play', methods=['POST'])
def play_song():
    sp_client = get_spotify_client()
    if not sp_client:
        return jsonify({'error': 'Spotify login required.'}), 401
    try:
        data = request.get_json()
        playlist_uri = data.get('playlist_uri')
        device_id = data.get('device_id')
        if not playlist_uri or not device_id:
            return jsonify({'error': 'Playlist URI and Device ID are required.'}), 400
        sp_client.transfer_playback(device_id=device_id, force_play=True)
        sp_client.start_playback(device_id=device_id, context_uri=playlist_uri)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"A critical error occurred in /play: {e}")
        return jsonify({'error': f'Could not start playback: {str(e)}'}), 500

# -----------------------
# Whack-a-Mole Game Routes
# -----------------------
game_state = {
    'score': 0,
    'game_over': False,
    'start_time': None,
    'game_duration': 30
}

@app.route('/whack-a-mole')
def mole_index():
    return render_template('mole.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    global game_state
    game_state = {
        'score': 0,
        'game_over': False,
        'start_time': time.time(),
        'game_duration': 30
    }
    return jsonify({'status': 'started', 'score': game_state['score']})

@app.route('/hit_mole', methods=['POST'])
def hit_mole():
    global game_state
    if not game_state['game_over']:
        game_state['score'] += 1
        return jsonify({'status': 'hit', 'score': game_state['score']})
    return jsonify({'status': 'game_over', 'score': game_state['score']})

@app.route('/game_status', methods=['GET'])
def game_status():
    global game_state
    if game_state['start_time']:
        elapsed_time = time.time() - game_state['start_time']
        time_left = max(0, game_state['game_duration'] - elapsed_time)
        if time_left <= 0:
            game_state['game_over'] = True
        return jsonify({
            'score': game_state['score'],
            'time_left': round(time_left),
            'game_over': game_state['game_over']
        })
    return jsonify({'score': 0, 'time_left': game_state['game_duration'], 'game_over': True})

# -----------------------
# Run Unified App
# -----------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
