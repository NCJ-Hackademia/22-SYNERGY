# sentiment_analysis.py
import os
import json
import requests

def analyze_sentiment_with_gemini(text):
    """
    Analyzes the text for a specific emotion, prioritizing the detection of distress.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not available.")
        return {"error": "The sentiment analysis service is not configured."}

    # Advanced prompt with a safety check (Chain of Thought)
    prompt = f"""
    Analyze the following journal entry by following these steps:
    1. First, read the text carefully to identify any language related to self-harm, severe depression, hopelessness, or immediate distress.
    2. If any such language is present, you MUST classify the emotion as "Distress".
    3. If and only if there is NO language of distress, then determine the primary emotion from the list below.
    4. Finally, determine the intensity of the emotion on a scale of low, medium, or high.

    Respond with only the emotion and its intensity, separated by a hyphen.
    For example: "Distress-High", "Joy-Low", "Sadness-Medium".

    Emotion List (only use if no distress is found):
    - Joy
    - Sadness
    - Anger
    - Fear
    - Surprise
    - Calm
    - Hopeful
    - Anxious
    - Love

    Journal Entry:
    "{text}"

    Analysis:
    """
    
    model_name = "gemini-1.5-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 20}
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        result = response.json()
        
        analysis_result = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Calm-Medium').strip()
        
        if '-' in analysis_result and len(analysis_result.split('-')) == 2:
            return analysis_result
        else:
            print(f"Warning: Gemini returned an unexpected format: '{analysis_result}'. Defaulting.")
            return 'Calm-Medium'

    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return {"error": "Could not connect to the sentiment analysis service."}
    except (KeyError, IndexError) as e:
        print(f"Error parsing Gemini API response: {e}")
        return {"error": "Invalid response from the sentiment analysis service."}