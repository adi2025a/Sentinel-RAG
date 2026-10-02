"""
app/rag/__init__.py
===================
Unified RAG package re-exporting ingestion, vector store, retrieval, and generation.
"""

from app.rag.ingestion import (
    extract_visible_text,
    sanitize_text,
    sanitize_pdf,
    normalize_text,
    secure_pdf_to_text,
    split_text_into_chunks,
)
from app.rag.vector_store import (
    get_embedder,
    build_vector_store,
    load_vector_store,
)
from app.rag.retriever import search_query
from app.rag.generator import answer_query_with_context

__all__ = [
    "extract_visible_text",
    "sanitize_text",
    "sanitize_pdf",
    "normalize_text",
    "secure_pdf_to_text",
    "split_text_into_chunks",
    "get_embedder",
    "build_vector_store",
    "load_vector_store",
    "search_query",
    "answer_query_with_context",
]
