from google.generativeai.types import GenerateContentResponse

def detect_unsafe_content(model: 'GenerativeModel', message: str) -> bool:
    """
    Detects unsafe content using Gemini AI.
    Returns True if unsafe, False if safe.
    """
    prompt = f"""
    Analyze the following message for:
    - Abuse (verbal, emotional, etc.)
    - Suicidal behavior or thoughts
    - Self-harm
    - Encouraging self-harm or suicide
    Respond only with 'safe' or 'unsafe'.
    Message: {message}
    """
    try:
        response: GenerateContentResponse = model.generate_content(prompt)
        result = response.text.strip().lower()
        return result == 'unsafe'
    except Exception as e:
        print(f"Error in AI detection: {e}")
        return False
