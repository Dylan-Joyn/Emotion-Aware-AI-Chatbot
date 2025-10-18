from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key}")

# Test the key directly
client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me a thumbs up'
)
print(response.text)

print(response.model_dump_json(
    exclude_none=True, indent=4))