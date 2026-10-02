"""
app/rag/retriever.py
====================
Semantic similarity search over the FAISS vector store.
"""

from __future__ import annotations
from pathlib import Path
from typing import Union
from app.rag.vector_store import load_vector_store
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def search_query(
    query: str,
    save_path: Union[str, Path] | None = None,
    k: int | None = None
) -> list:
    """
    Perform semantic similarity search on a saved FAISS vector store.

    Args:
        query: The search query string.
        save_path: Path to the saved FAISS index (defaults to settings.VECTOR_STORE_DIR).
        k: Number of top results to return (defaults to settings.RETRIEVAL_TOP_K).

    Returns:
        list: Matching LangChain Document objects.
    """
    top_k = k if k is not None else settings.RETRIEVAL_TOP_K
    vector_store = load_vector_store(save_path)
    logger.info(f"Searching for query: {query!r} (top_k={top_k})")
    results = vector_store.similarity_search(query, k=top_k)
    logger.info(f"Search completed. Found {len(results)} matching chunks.")
    return results
