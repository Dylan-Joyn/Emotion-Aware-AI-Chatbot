from dotenv import load_dotenv
from google import genai
import os
import pytest

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

#test API Keys
@pytest.fixture(scope="module")
def gemini_client():
    # Check for API Key
    if not api_key:
        raise ValueError("GOOGLE_API_KEY env variable is missing. Check secrets")
    
    # Check for valid API Key
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        raise RuntimeError("Failed to initialize Gemini Client. Check if the provided key is valid.")
    
# Test Connection
def test_gemini_api_connection(gemini_client):
    model_name = 'gemini-2.5-flash'
    prompt = 'Give me a simple response to confirm connection'

    try:
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt
        )
    except Exception as e:
        # connection fails on server end
        pytest.fail(f"API call failed during content generation: {e}")

    assert response.text is not None, "Response text was empty."
    assert len(response.text.strip()) > 0, "Response was only whitespace"
