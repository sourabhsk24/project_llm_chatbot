# query_classifier.py
# Lightweight, fully local query classifier.

GREETING_WORDS = [
    "hi", "hello", "hey",
    "good morning", "good afternoon", "good evening",
    "good night",
    "hola", "namaste",
    "thanks", "thank you", "thankyou", "thx", "tnx"
]


def classify_query(user_query: str) -> str:
    """
    Very simple classifier:
    - If it's basically a greeting / thanks → GREETING
    - Everything else → RAG (send to RAG pipeline)
    """
    if not isinstance(user_query, str):
        return "RAG"

    q = user_query.lower().strip()

    # If the whole message is very short and looks like greeting/thanks
    if any(word in q for word in GREETING_WORDS):
        # If it's just like "hi", "hello", "thanks"
        if len(q.split()) <= 4:
            return "GREETING"

    return "RAG"
