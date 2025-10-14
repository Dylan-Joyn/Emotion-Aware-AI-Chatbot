from google.ai.generativelanguage_v1 import ModelServiceClient
from google.ai.generativelanguage_v1.types import ListModelsRequest
from google.api_core.client_options import ClientOptions
from google.auth.credentials import Credentials
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise EnvironmentError("GOOGLE_API_KEY not found in .env file!")

# ✅ Custom credentials class for API key auth
class APIKeyCredentials(Credentials):
    def __init__(self, key):
        super().__init__()
        self._key = key

    def apply(self, headers, token=None):
        headers["x-goog-api-key"] = self._key
        return headers

    def refresh(self, request):
        """Required abstract method (no-op)."""
        return None

# Create the API client with explicit API key authentication
client = ModelServiceClient(
    credentials=APIKeyCredentials(api_key),
    client_options=ClientOptions(api_endpoint="generativelanguage.googleapis.com"),
)

# List models
response = client.list_models(ListModelsRequest())

print("\nAvailable Gemini Models:")
print("=" * 40)
for model in response.models:
    print(model.name)
