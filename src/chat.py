#CLI for setimental routing bot
"""
Interactive command-line chat interface for the sentiment chatbot.
Run with: python chat.py
"""

from sentiment_bot import route_by_sentiment
from dotenv import load_dotenv

load_dotenv()

def main():
    """Main chat loop"""
    print("\n" + "="*60)
    print("    Sentiment-Aware Chatbot")
    print("="*60)
    print("Type your message and press Enter.")
    print("Type 'quit', 'exit', or 'bye' to end the chat.")
    print("="*60 + "\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ")

            # Check for exit commands
            if user_input.lower().strip() in ["quit", "exit", "bye", "goodbye"]:
                print("\nGoodbye! Take care!\n")
                break

            # Skip empty messages
            if not user_input.strip():
                continue

            # Get bot response
            response = route_by_sentiment(user_input)
            
            # Display response
            print(f"\nKnight Bot: {response}\n")

        except KeyboardInterrupt:
            print("\n\nChat interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    main()