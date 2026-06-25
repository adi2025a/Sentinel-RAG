import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pathlib import Path

_HERE = Path(__file__).parent 

# ── Paths (place these files next to this script) ──────────────────────────
INDEX_PATH    = str(_HERE / "attack_index.faiss")
METADATA_PATH = str(_HERE / "attack_metadata.pkl")
MODEL_NAME    = "BAAI/bge-base-en-v1.5"

# ── Load once at module level ───────────────────────────────────────────────
print("Loading embedding model...")
_model = SentenceTransformer(MODEL_NAME)

print("Loading FAISS index...")
_index = faiss.read_index(INDEX_PATH)

print("Loading metadata...")
with open(METADATA_PATH, "rb") as f:
    _metadata = pickle.load(f)

print(f"Ready. Index has {_index.ntotal} vectors.\n")


def score(query: str, top_k: int = 5) -> float:
    """
    Embed `query`, search the attack vector store, and return a
    similarity score in [0.0, 1.0].

    The score is the mean cosine similarity of the top-k nearest
    attack vectors, weighted by their cluster severity.

    Args:
        query:  The user input string to evaluate.
        top_k:  How many neighbours to retrieve (default 5).

    Returns:
        A float between 0.0 (benign) and 1.0 (highly malicious).
    """
    SEVERITY_WEIGHTS = {
        "critical": 1.0,
        "high":     0.75,
        "medium":   0.50,
        "low":      0.25,
    }

    # Embed and normalise (cosine similarity via inner product)
    query_emb = _model.encode([query], normalize_embeddings=True).astype("float32")

    # Search
    similarities, ids = _index.search(query_emb, top_k)
    similarities = similarities[0]   # shape (top_k,)
    ids          = ids[0]

    if len(similarities) == 0:
        return 0.0

    # Weight each neighbour by its severity
    weights = np.array([
        SEVERITY_WEIGHTS.get(_metadata[i]["severity"], 0.5)
        for i in ids if i < len(_metadata)
    ])

    raw_score = float(np.mean(similarities[:len(weights)] * weights))

    # Clamp to [0, 1]
    return round(min(max(raw_score, 0.0), 1.0), 4)


# ── CLI usage ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter query: ")

    result = score(query)
    print(f"Score: {result}")