import os
import chromadb
import subprocess
import json
from PyPDF2 import PdfReader

DB_PATH = "./rag_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"

DATA_FOLDER = "./data"


# ---------- CHROMA SETUP ----------
client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
# ----------------------------------


def embed(text: str):
    """Generate embeddings using Ollama (nomic-embed-text returns a raw list)."""
    result = subprocess.run(
        ["ollama", "run", EMBED_MODEL],
        input=text,
        text=True,
        capture_output=True,
    )

    raw = result.stdout.strip()

    try:
        emb = json.loads(raw)
        return emb
    except Exception as e:
        print("❌ Embedding error while indexing:", e)
        print("RAW OUTPUT (first 200 chars):", raw[:200])
        return None


def load_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    text_content = ""

    for page in reader.pages:
        try:
            text_content += (page.extract_text() or "") + "\n"
        except Exception:
            pass

    return text_content


def chunk_text(text: str, chunk_size: int = 500):
    """Split text into chunks by word count."""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks


def process_documents():
    print("🔍 Loading documents from:", DATA_FOLDER)

    for filename in os.listdir(DATA_FOLDER):
        filepath = os.path.join(DATA_FOLDER, filename)

        if filename.lower().endswith(".pdf"):
            print("📄 Processing PDF:", filename)
            text = load_pdf(filepath)
        elif filename.lower().endswith(".txt"):
            print("📝 Processing TXT:", filename)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            print("⏩ Skipped (not PDF/TXT):", filename)
            continue

        chunks = chunk_text(text, chunk_size=500)
        print(f"📦 Splitting into {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            emb = embed(chunk)
            if emb is None:
                print(f"⚠️ Skipping chunk {i} due to embedding failure.")
                continue

            collection.add(
                documents=[chunk],
                embeddings=[emb],
                ids=[f"{filename}_chunk_{i}"],
            )

        print("✔ Finished:", filename)

    print("🎉 All documents processed!")


if __name__ == "__main__":
    process_documents()
