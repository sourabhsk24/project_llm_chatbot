# greeting_handler.py
# Pure local greeting logic – no API calls, instant response.

import random

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good afternoon",
    "good evening", "good night", "hola", "namaste"
]

THANKS_KEYWORDS = [
    "thanks", "thank you", "thankyou", "tnx", "thx"
]

GREETING_RESPONSES = [
    "Hi! 👋 I'm your LLM Chatbot assistant. How can I help you today?",
    "Hello! 😊 Ask me anything about LLM Chatbot modules or features.",
    "Hey there! 👋 What would you like to know about LLM Chatbot?",
    "Hi! I'm ready to help you with LLM Chatbot documentation and features."
]

THANKS_RESPONSES = [
    "You're welcome! 😊",
    "Glad I could help! 🙌",
    "Anytime! If you have more questions, just ask. 🙂",
    "You're welcome! Happy to assist. 🤝"
]


def greeting_response(user_query: str) -> str:
    """
    Very fast, offline greeting handler.
    No network calls, no LLM calls.
    """
    q = user_query.lower().strip()

    # Thanks-type messages
    if any(word in q for word in THANKS_KEYWORDS):
        return random.choice(THANKS_RESPONSES)

    # Greetings
    if any(word in q for word in GREETING_KEYWORDS):
        return random.choice(GREETING_RESPONSES)

    # Fallback – if classifier sent here by mistake
    return "Hi! 👋 How can I help you with LLM Chatbot?"
