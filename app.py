from flask import Flask, request, jsonify, render_template
from rag_pipeline import rag_answer
from query_classifier import classify_query
from greeting_handler import greeting_response

app = Flask(__name__, template_folder="templates")


# -------------------------------
# FRONTEND ROUTE
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# API ROUTE
# -------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    query = data.get("query", "")

    if not isinstance(query, str) or not query.strip():
        return jsonify({"response": "Please enter a valid query."}), 400

    query = query.strip()
    print("\n🔍 USER QUERY:", query)

    # Classify the query (local + instant)
    category = classify_query(query)
    print("📌 Category:", category)

    # Fast local greeting — no LLM, no RAG
    if category == "GREETING":
        return jsonify({"response": greeting_response(query)})

    # Everything else → RAG over local docs + local LLM
    response = rag_answer(query)
    return jsonify({"response": response})


if __name__ == "__main__":
    print("🚀 Local LLM Chatbot running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
