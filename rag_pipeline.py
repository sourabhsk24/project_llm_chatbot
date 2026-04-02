import chromadb
import subprocess
import json
import time

# ---------- CONFIG ----------
DB_PATH = "./rag_db"
COLLECTION_NAME = "documents"

EMBED_MODEL = "nomic-embed-text"  # embedding model in Ollama
LLM_MODEL = "phi3"                # small, faster model in Ollama

MAX_TOKENS = "60"                 # hard cap on output tokens
MAX_CONTEXT_CHARS = 400           # keep context tiny
N_RESULTS = 1                     # only the best chunk
LLM_TIMEOUT = 600                  # seconds – safety timeout
# -----------------------------


# ---------- CHROMA SETUP ----------
client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
# ----------------------------------

from functools import lru_cache

# In rag_pipeline.py
@lru_cache(maxsize=256)
def rag_answer_cached(query: str) -> str:
    return _rag_answer_impl(query)  # move your existing rag logic into _rag_answer_impl()

# Then in app.py use rag_answer_cached instead of rag_answer


def embed(text: str):
    """Generate embeddings using Ollama (nomic-embed-text returns a raw list)."""
    t0 = time.perf_counter()

    result = subprocess.run(
        ["ollama", "run", EMBED_MODEL],
        input=text,
        text=True,
        capture_output=True,
    )

    raw = result.stdout.strip()

    try:
        emb = json.loads(raw)
    except Exception as e:
        print("❌ Embedding error:", e)
        print("RAW OUTPUT (first 200 chars):", raw[:200])
        return None

    t1 = time.perf_counter()
    print(f"🔢 Embedding took {t1 - t0:.2f}s")
    return emb

def run_llm(prompt: str) -> str:
    """Call local LLM (no unsupported flags). Prompt asks model to be short."""
    import subprocess, time
    t0 = time.perf_counter()

    try:
        proc = subprocess.run(
            ["ollama", "run", LLM_MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=LLM_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"⛔ LLM call exceeded {LLM_TIMEOUT}s, aborting.")
        return f"⚠️ The local model timed out after {LLM_TIMEOUT}s."

    t1 = time.perf_counter()
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    print("🤖 LLM returncode:", proc.returncode)
    print("🤖 LLM took: %.2fs" % (t1 - t0))
    print("🤖 stdout (first 500 chars):", stdout[:500])
    print("🤖 stderr (first 500 chars):", stderr[:500])

    if proc.returncode != 0:
        return f"⚠️ LLM exited with code {proc.returncode}. See server logs."

    if not stdout:
        return "⚠️ Model returned no output. See server logs."

    return stdout


def rag_answer(query: str) -> str:
    """RAG: embed query -> search Chroma -> short answer from LLM."""
    print("\n🔍 QUERY:", query)

    # 1) Embed query
    q_emb = embed(query)
    if q_emb is None:
        return "Embedding failed."

    # 2) Retrieve similar chunks
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=N_RESULTS,
    )

    docs = results.get("documents", [])
    if not docs or not docs[0]:
        print("⚠️ No documents found for query.")
        return "No relevant information found."

    # 3) Build *small* context
    context = "\n\n".join(docs[0])
    context = context[:MAX_CONTEXT_CHARS]
    print("📝 Context length:", len(context))

    # 4) Build *short* prompt
    prompt = f"""You are a concise assistant for the LLM Chatbot HR product.

Use ONLY the following context to answer the question.
If the answer is not in the context, say you don't have enough information.

Context:
{context}

Question: {query}

Please answer in 2–3 short sentences (brief, factual, ~40–60 words)."""


    # 5) Get answer from LLM
    answer = run_llm(prompt)
    return answer
