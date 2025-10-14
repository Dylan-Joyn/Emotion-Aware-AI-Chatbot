from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key: {api_key}")

# Test the key directly
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say hello")
print(response.text)