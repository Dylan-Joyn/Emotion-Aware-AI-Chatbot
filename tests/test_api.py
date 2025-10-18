from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

# Test the key directly
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me a thumbs up'
)
print(response.text)

print(response.model_dump_json(
    exclude_none=True, indent=4))