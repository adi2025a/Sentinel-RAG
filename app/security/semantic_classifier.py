"""
app/security/semantic_classifier.py
===================================
Module 2 — Semantic Attack Similarity Classifier via FAISS.
Compares input queries against an indexed vector database of known attack vectors.
"""

from __future__ import annotations
from pathlib import Path
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(name=__name__)

# Cached singletons
_model: SentenceTransformer | None = None
_index: faiss.Index | None = None
_metadata: list[dict] | None = None


def _get_resources():
    """Lazily loads and caches the SentenceTransformer model, FAISS index, and metadata."""
    global _model, _index, _metadata

    if _model is None:
        logger.info(f"Loading semantic attack classifier model: {settings.SEMANTIC_MODEL_NAME}...")
        _model = SentenceTransformer(settings.SEMANTIC_MODEL_NAME)

    if _index is None or _metadata is None:
        index_path = str(settings.ATTACK_INDEX_PATH)
        metadata_path = str(settings.ATTACK_METADATA_PATH)

        logger.info(f"Loading FAISS attack index from: {index_path}")
        _index = faiss.read_index(index_path)

        logger.info(f"Loading attack metadata from: {metadata_path}")
        with open(metadata_path, "rb") as f:
            _metadata = pickle.load(f)

        logger.info(f"Semantic classifier ready. Indexed vectors: {_index.ntotal}")

    return _model, _index, _metadata


def score(query: str, top_k: int = 5) -> float:
    """
    Embed `query`, search the attack vector store, and return a
    similarity score in [0.0, 1.0].

    The score is the mean cosine similarity of the top-k nearest
    attack vectors, weighted by their cluster severity.

    Args:
        query: The user input string to evaluate.
        top_k: How many neighbours to retrieve (default 5).

    Returns:
        float: Normalized threat score between 0.0 (benign) and 1.0 (highly malicious).
    """
    severity_weights = {
        "critical": 1.0,
        "high":     0.75,
        "medium":   0.50,
        "low":      0.25,
    }

    model, index, metadata = _get_resources()

    # Embed and normalise (cosine similarity via inner product)
    query_emb = model.encode([query], normalize_embeddings=True).astype("float32")

    # Search
    similarities, ids = index.search(query_emb, top_k)
    similarities = similarities[0]   # shape (top_k,)
    ids          = ids[0]

    if len(similarities) == 0:
        return 0.0

    # Weight each neighbour by its severity
    weights = np.array([
        severity_weights.get(metadata[i]["severity"], 0.5)
        for i in ids if i < len(metadata)
    ])

    raw_score = float(np.mean(similarities[:len(weights)] * weights))

    # Clamp to [0.0, 1.0]
    return round(min(max(raw_score, 0.0), 1.0), 4)


# Backward-compatible alias
attack_classifier = score

if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter query: ")
    print(f"Threat Score: {score(q)}")
