// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
  const journalInterface = document.getElementById('journal-interface');
  if (!journalInterface) return;

  // --- Element Selectors ---
  const journalText = document.getElementById('journal-entry');
  const resultsContainer = document.getElementById('results-container');
  const sentimentResult = document.getElementById('sentiment-result');
  const stageResult = document.getElementById('stage-result');
  const musicContainer = document.getElementById('music-container');
  const tracksContainer = document.getElementById('tracks-container');
  const errorMessage = document.getElementById('error-message');

  // --- State ---
  let spotifyPlayer = null;
  let deviceId = null;
  let spotifyAccessToken = null;
  let lastAnalyzedText = '';
  let currentSentiment = null;
  let isAnalyzing = false;

  // Playback cycle management
  let playLock = false;
  let playTimer = null;
  let playbackCooldown = false; // prevents rapid retries

  // --- Spotify Player Initialization ---
  window.onSpotifyWebPlaybackSDKReady = () => {
    console.log("Spotify SDK is ready.");
    fetch('/get_token')
      .then(res => res.json())
      .then(data => {
        if (data.access_token) {
          spotifyAccessToken = data.access_token;

          spotifyPlayer = new Spotify.Player({
            name: 'Sentiment Journal Web Player',
            getOAuthToken: cb => { cb(spotifyAccessToken); }
          });

          spotifyPlayer.addListener('ready', ({ device_id }) => {
            console.log('Spotify Player ready. Device ID:', device_id);
            deviceId = device_id;
          });

          spotifyPlayer.addListener('player_state_changed', (state) => {
            if (!state) return;
            const track = state.track_window.current_track;
            if (track) {
              displayNowPlaying({
                name: track.name,
                artist: track.artists.map(a => a.name).join(', '),
                uri: track.uri,
                album_art: track.album.images[0]?.url || 'https://placehold.co/64x64/png?text=No+Art'
              });
            }
          });

          spotifyPlayer.addListener('initialization_error', ({ message }) => console.error('Init Error:', message));
          spotifyPlayer.addListener('authentication_error', ({ message }) => console.error('Auth Error:', message));
          spotifyPlayer.addListener('account_error', ({ message }) => {
            console.error('Account Error:', message);
            alert("The Web Player requires a Spotify Premium subscription.");
          });
          spotifyPlayer.addListener('playback_error', ({ message }) => {
            console.error('Playback Error:', message);
            displayError("Playback failed. Please retry or check your Spotify app.");
            resetPlaybackCycle();
            playbackCooldown = true;
            setTimeout(() => { playbackCooldown = false; }, 10000); // wait 10s
          });

          spotifyPlayer.connect();
        } else {
          displayError('Could not get Spotify access token.');
        }
      })
      .catch(err => {
        console.error('Token fetch error:', err);
        displayError('Failed to initialize Spotify.');
      });
  };

  // --- Auto-analysis loop (every 60s) ---
  setInterval(async () => {
    const currentText = journalText.value.trim();
    if (currentText && currentText !== lastAnalyzedText && !isAnalyzing) {
      await analyzeAndReact(currentText);
    }
  }, 60000);

  async function analyzeAndReact(textToAnalyze) {
    isAnalyzing = true;
    lastAnalyzedText = textToAnalyze;

    try {
      const sentimentResponse = await fetch('/analyze_sentiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textToAnalyze }),
      });

      const sentimentData = await sentimentResponse.json();
      if (!sentimentResponse.ok) throw new Error(sentimentData.error || 'Analysis failed.');

      const newSentiment = sentimentData.sentiment;
      displayResults(newSentiment, sentimentData.stage);

      if (newSentiment !== currentSentiment) {
        resetPlaybackCycle();   // stop old cycle
        currentSentiment = newSentiment;
        await fetchAndPlayNewJourney(currentSentiment);
      }
    } catch (error) {
      displayError(error.message);
    } finally {
      isAnalyzing = false;
    }
  }

  async function fetchAndPlayNewJourney(sentiment) {
    if (!deviceId) {
      displayError("Spotify player is not ready yet. Please wait a moment.");
      return;
    }
    if (playbackCooldown) {
      console.warn("Playback is in cooldown, skipping new journey request.");
      return;
    }

    try {
      const journeyResponse = await fetch('/create_journey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sentiment }),
      });
      const journeyData = await journeyResponse.json();
      if (!journeyResponse.ok) throw new Error(journeyData.error || 'Failed to create journey.');

      const firstStage = journeyData.journey?.[0];
      if (!firstStage || !firstStage.playlist_uri) throw new Error("No playlist found in the journey.");

      await playPlaylistOnDevice(firstStage.playlist_uri);

      // Start cycle management
      startPlaybackCycle();
    } catch (error) {
      displayError(error.message);
    }
  }

  async function playPlaylistOnDevice(playlistUri) {
    const res = await fetch('/play', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        playlist_uri: playlistUri,
        device_id: deviceId
      }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error || 'Could not start playback.');
    }
  }

  // --- Playback Cycle ---
  function startPlaybackCycle() {
    if (playLock || playbackCooldown) return; 
    playLock = true;

    console.log("🔒 Playback locked for 60s");

    playTimer = setTimeout(async () => {
      playLock = false;
      console.log("🔓 Unlock - attempting skip...");

      if (spotifyAccessToken && currentSentiment) {
        try {
          await fetch(`https://api.spotify.com/v1/me/player/next?device_id=${deviceId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${spotifyAccessToken}` }
          });
          console.log("⏭️ Skipped to next track");

          // throttle next play command for 5s
          playbackCooldown = true;
          setTimeout(() => { playbackCooldown = false; }, 5000);

          startPlaybackCycle();  // re-lock for next 60s
        } catch (e) {
          console.error("Error skipping track:", e);
          resetPlaybackCycle();
        }
      }
    }, 60000);
  }

  function resetPlaybackCycle() {
    if (playTimer) {
      clearTimeout(playTimer);
      playTimer = null;
    }
    playLock = false;
    console.log("⏹️ Playback cycle reset");
  }

  // --- UI Helpers ---
  function displayResults(sentiment, stage) {
    resultsContainer.classList.remove('hidden');
    sentimentResult.textContent = formatSentiment(sentiment);
    sentimentResult.className = getSentimentColorClass(sentiment.split('-')[0]);
    stageResult.textContent = stage || '';
    stageResult.className = "font-bold";
  }

  function displayNowPlaying(track) {
    musicContainer.classList.remove('hidden');
    tracksContainer.innerHTML = createTrackHtml(track);
  }

  function formatSentiment(s) { return `${s.split('-')[1]} ${s.split('-')[0]}`; }
  function createTrackHtml(p) {
    return `
      <div class="flex items-center p-3 bg-white rounded-lg shadow-sm">
        <img src="${p.album_art}" alt="${p.name}" class="w-14 h-14 rounded-md mr-4 object-cover">
        <div class="flex-grow min-w-0">
          <p class="font-semibold text-gray-900 truncate">${p.name}</p>
          <p class="text-sm text-gray-500 truncate">${p.artist}</p>
        </div>
      </div>
    `;
  }
  function displayError(m) {
    errorMessage.innerHTML = `<p class="text-red-600 bg-red-100 p-4 rounded-lg font-medium">${m}</p>`;
    errorMessage.classList.remove('hidden');
  }
  function getSentimentColorClass(e) {
    const base = 'font-bold';
    switch (e.toLowerCase()) {
      case 'joy': case 'hopeful': case 'love': case 'surprise': return `text-green-600 ${base}`;
      case 'sadness': case 'anxious': case 'fear': return `text-blue-600 ${base}`;
      case 'anger': return `text-red-600 ${base}`;
      case 'calm': return `text-purple-600 ${base}`;
      case 'distress': return `text-orange-600 ${base}`;
      default: return `text-gray-600 ${base}`;
    }
  }
});
