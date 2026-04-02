# LLM_rag.py
import chromadb
import subprocess
import json
import time
import re
import os

# ---------- CONFIG ----------
DB_PATH = "./rag_db"
COLLECTION_NAME = "documents"

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "phi3"
MAX_TOKENS = "60"
MAX_CONTEXT_CHARS = 400
N_RESULTS = 1
LLM_TIMEOUT = 40
# -----------------------------

# Initialize Chroma DB client / collection
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

# ---------- Utilities ----------
_ansi_re = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
_ctrl_re = re.compile(r'[\x00-\x08\x0B-\x1F\x7F-\x9F]')
_meaningful_re = re.compile(r'[\w\u00C0-\u017F]')

def _clean_text(text: str) -> str:
    """
    Lightweight cleaning for model output: remove ANSI/control chars and normalize whitespace.
    Returns cleaned string or empty string if nothing meaningful remains.
    """
    if not text:
        return ""

    s = text
    s = _ansi_re.sub("", s)       # remove ANSI escapes
    s = _ctrl_re.sub("", s)       # remove control chars
    s = re.sub(r'\r', '', s)      # remove carriage returns
    s = re.sub(r'\n{2,}', '\n', s)  # collapse multiple newlines
    s = s.strip()
    if not _meaningful_re.search(s):
        return ""
    return s

def _ollama_supports_num_predict():
    if hasattr(_ollama_supports_num_predict, "cached"):
        return _ollama_supports_num_predict.cached
    try:
        proc = subprocess.run(["ollama", "run", "--help"],
                              capture_output=True, text=True, timeout=3)
        help_text = (proc.stdout or "") + (proc.stderr or "")
        supported = ("--num-predict" in help_text) or ("--num_predict" in help_text)
        _ollama_supports_num_predict.cached = supported
        return supported
    except Exception:
        _ollama_supports_num_predict.cached = False
        return False

NUM_PREDICT_SUPPORTED = _ollama_supports_num_predict()

def embed(text: str):
    """Generate embedding using Ollama-based embed model (expects JSON list)."""
    t0 = time.perf_counter()
    try:
        result = subprocess.run(
            ["ollama", "run", EMBED_MODEL],
            input=text,
            text=True,
            capture_output=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        print("❌ Embedding subprocess timed out.")
        return None
    except Exception as e:
        print("❌ Embedding subprocess error:", e)
        return None

    raw = (result.stdout or "").strip()
    try:
        emb = json.loads(raw)
    except Exception as e:
        print("❌ Embedding JSON parse error:", e)
        print("RAW OUTPUT (first 400 chars):", raw[:400])
        return None

    t1 = time.perf_counter()
    print(f"🔢 Embedding took {t1 - t0:.2f}s")
    return emb

def _build_ollama_cmd(model: str, token_limit: str = None, hidethinking: bool = True):
    cmd = ["ollama", "run", model]
    if token_limit and NUM_PREDICT_SUPPORTED:
        cmd += ["--num-predict", token_limit]
    if hidethinking:
        cmd += ["--hidethinking"]
    return cmd

def run_llm(prompt: str) -> str:
    """Call Ollama (non-streaming) and return cleaned output or an error message."""
    t0 = time.perf_counter()
    cmd = _build_ollama_cmd(LLM_MODEL, MAX_TOKENS, hidethinking=True)

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=LLM_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"⛔ LLM call exceeded {LLM_TIMEOUT}s, aborting.")
        return "⚠️ The local model timed out. Try again with a simpler question."
    except Exception as e:
        print("❌ LLM call error:", e)
        return f"⚠️ LLM call failed: {e}"

    out = (result.stdout or "").strip()
    t1 = time.perf_counter()
    print(f"🤖 LLM generation took {t1 - t0:.2f}s")
    if not out:
        return "⚠️ Model returned no output."

    cleaned = _clean_text(out)
    return cleaned or out

# ---------- RAG (non-streaming) ----------
def rag_answer(query: str) -> str:
    """
    Embed the query, retrieve top document chunk(s), form a concise prompt,
    call the model once, and return a cleaned answer string.
    """
    print("\n🔍 QUERY:", query)

    # 1) Embed
    q_emb = embed(query)
    if q_emb is None:
        return "⚠️ Embedding failed."

    # 2) Retrieve
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=N_RESULTS,
    )
    docs = results.get("documents", [])
    if not docs or not docs[0]:
        print("⚠️ No documents found for query.")
        # fall back to a direct model answer without context
        prompt_fb = f"You are a concise assistant. Answer briefly.\n\nQuestion: {query}\n\nAnswer in 2-3 short sentences."
        return run_llm(prompt_fb)

    # 3) Build small context
    context = "\n\n".join(docs[0])
    context = context[:MAX_CONTEXT_CHARS]
    print("📝 Context length:", len(context))

    # 4) Prompt
    prompt = (
        "You are a concise assistant for the LLM Chatbot HR product.\n\n"
        "Use ONLY the following context to answer the question.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer in 2-3 short sentences"
    )
    print("💬 Prompt length:", len(prompt))

    # 5) Call LLM
    response = run_llm(prompt)
    if not response:
        return "⚠️ Could not produce an answer."
    return response
