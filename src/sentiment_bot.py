from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import BaseOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableSequence
from dotenv import load_dotenv
import os

# 1. Load environment variables (keep your keys in .env, never hardcode!)
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Check for required keys
if not GOOGLE_API_KEY or not GROQ_API_KEY or not CLAUDE_API_KEY:
    raise EnvironmentError("Missing one or more required API keys (GOOGLE_API_KEY, GROQ_API_KEY, or CLAUDE_API_KEY) in .env file.")

# Set environment variables for LangChain/underlying libraries to auto-detect
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY
# We pass the CLAUDE key directly to the constructor for reliability.

# 2. Custom parser: detects sentiment + severity
class SentimentParser(BaseOutputParser):
    """Parses the LLM's raw text response into structured sentiment and severity."""
    def parse(self, text: str) -> dict:
        text = text.strip().lower()
        
        # Determine Sentiment
        if "positive" in text:
            sentiment = "positive"
        elif "negative" in text:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Determine Severity (only relevant if negative, but parsed universally)
        severity = "normal"
        if any(word in text for word in ["severe", "crisis", "urgent", "hopeless"]):
            severity = "severe"
        elif any(word in text for word in ["moderate", "concerning", "significant"]):
            severity = "moderate"

        return {"sentiment": sentiment, "severity": severity}


# 3. Mental-health keyword detector (Pre-screening for immediate crisis)
def check_mental_health_concerns(user_input: str) -> str:
    """Checks input for high-priority crisis keywords."""
    crisis_keywords = [
        "suicide", "suicidal", "kill myself", "end my life", "want to die",
        "self harm", "self-harm", "cut myself", "hurt myself",
        "no reason to live", "better off dead", "can't go on"
    ]

    serious_keywords = [
        "depressed", "depression", "anxious", "anxiety", "panic attack",
        "can't cope", "overwhelmed", "hopeless", "worthless",
        "hate myself", "severe anxiety", "mental breakdown"
    ]

    user_lower = user_input.lower()
    if any(k in user_lower for k in crisis_keywords):
        return "crisis"
    if any(k in user_lower for k in serious_keywords):
        return "serious"
    return "none"


# 4. Sentiment analysis chain (Using a strong model for reliable classification)
sentiment_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
sentiment_prompt = PromptTemplate(
    input_variables=["user_input"],
    template=(
        "Analyze the sentiment and severity of the following text.\n\n"
        "First, determine sentiment: positive, negative, or neutral.\n"
        "Then, if negative, assess severity: normal, moderate, or severe.\n\n"
        "Severity guidelines:\n"
        "- severe: Mentions of self-harm, suicide, crisis, extreme distress, hopelessness.\n"
        "- moderate: Strong negative emotions, significant problems, sustained distress.\n"
        "- normal: Typical complaints or frustrations, mild annoyance.\n\n"
        "Respond ONLY in this format: '[sentiment] - [severity]'\n"
        "Example: 'negative - severe' or 'positive - normal'\n\n"
        "Text: {user_input}\n\n"
        "Analysis:"
    ),
)
sentiment_chain = sentiment_prompt | sentiment_llm | SentimentParser()


# 5. Models for routed responses
positive_model = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)

# --- CLAUDE INTEGRATION FIX: Use the specific, current model name ---
# FIX: Using the full, stable model name 'claude-3-5-sonnet-20240620'
claude_negative_llm = ChatAnthropic(
    # Changed model name from 'claude-3-sonnet' to the specific version
    model="claude-3-5-sonnet-20240620", 
    temperature=0.5,
    anthropic_api_key=CLAUDE_API_KEY 
)
negative_model = claude_negative_llm
# ------------------------------------------------------------------

neutral_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)


# 6. Response templates
positive_prompt = PromptTemplate(
    input_variables=["user_input"],
    template=(
        "The user seems happy! Respond enthusiastically, congratulatory, and build on their positive energy.\n\n"
        "User: {user_input}\n\nResponse:"
    ),
)

negative_prompt = PromptTemplate(
    input_variables=["user_input"],
    template=(
        "The user seems upset/frustrated. Respond with deep empathy, acknowledging their feelings first.\n"
        "Then, offer supportive and practical steps to address the core problem.\n\n"
        "User: {user_input}\n\nResponse:"
    ),
)

neutral_prompt = PromptTemplate(
    input_variables=["user_input"],
    template=(
        "Respond to the user's query in a helpful, informative, and concise way.\n\n"
        "User: {user_input}\n\nResponse:"
    ),
)

# 7. Mental-health response template
MENTAL_HEALTH_RESPONSE = """I hear that you're going through a difficult time, and I want you to know that your feelings are valid. However, I'm an AI assistant and not a certified mental health professional. 
If you're struggling with your emotional or mental health, I strongly encourage you to reach out to a qualified human specialist who can provide the proper support you deserve.

Here are some options that can help:

Immediate Crisis Support:
- 988 Suicide & Crisis Lifeline: Call or text 988 (available 24/7 in the US)
- Crisis Text Line: Text HOME to 741741
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/

Professional Help:
- Talk to your doctor or healthcare provider
- Contact a licensed therapist or counselor
- Reach out to a trusted friend or family member

You don't have to go through this alone. Professional support can make a real difference, and reaching out is a sign of strength, not weakness."""

# 8. Routing logic

def route_by_sentiment(user_input: str) -> str:
    # Step 1: Crisis detection (highest priority)
    mental_health_level = check_mental_health_concerns(user_input)
    if mental_health_level in ["crisis", "serious"]:
        print(f"--- MENTAL HEALTH TRIGGERED: {mental_health_level.upper()} LEVEL ---")
        return MENTAL_HEALTH_RESPONSE

    # Step 2: Sentiment analysis
    try:
        analysis = sentiment_chain.invoke({"user_input": user_input})
    except Exception as e:
        print(f"Error during sentiment analysis: {e}. Falling back to neutral.")
        # Fallback to a neutral response if the sentiment analysis fails
        response_content = neutral_model.invoke(neutral_prompt.invoke({"user_input": user_input})).content
        return response_content

    sentiment = analysis["sentiment"]
    severity = analysis["severity"]

    print(f"--- ROUTING ANALYSIS: Sentiment: {sentiment}, Severity: {severity} ---")

    # Step 3: Escalate severe negative cases (LLM-detected severe)
    if severity == "severe":
        print("Severe emotional distress detected by LLM - providing mental health resources")
        return MENTAL_HEALTH_RESPONSE

    # Step 4: Route to proper model
    if sentiment == "positive":
        print("Routing to Groq (Llama) for enthusiastic response.")
        chain = positive_prompt | positive_model
    elif sentiment == "negative":
        print("Routing to Anthropic (Claude 3.5 Sonnet) for empathetic response.")
        chain = negative_prompt | negative_model
    else:
        print("Routing to Gemini Flash for informative/neutral response.")
        chain = neutral_prompt | neutral_model

    # Step 5: Generate response
    response = chain.invoke({"user_input": user_input})
    # LangChain returns a Response object, extract the content
    return response.content if hasattr(response, 'content') else str(response)