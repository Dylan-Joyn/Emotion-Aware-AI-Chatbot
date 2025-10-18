from dotenv import load_dotenv
from groq import Groq
import os
import pytest

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Test API Keys
@pytest.fixture(scope="module")
def groq_client():
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing. Check secrets.")
    
    try:
        return Groq(api_key=api_key)
    except Exception:
        raise RuntimeError("Failed to initialize Groq Client. Check if the provided key is valid.")
    
# Test API Connection
def test_groq_api_connectivity(groq_client):    
    model_name = 'llama-3.3-70b-versatile' 
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Say 'Groq connected'"},
            ],
            model=model_name,
            temperature=0,
            max_tokens=10,
        )
    except Exception as e:
        # connection fails on server end
        pytest.fail(f"Groq API call failed during chat completion: {e}")

    response_text = chat_completion.choices[0].message.content
    
    # Assertions
    assert response_text is not None, "Groq response text was empty."
    assert 'Groq connected' in response_text, "Groq model did not return expected confirmation text."