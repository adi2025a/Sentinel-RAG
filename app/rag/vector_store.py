"""
app/rag/vector_store.py
=======================
Embedding generation and FAISS vector store build/load management.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Union
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(name=__name__)


def get_embedder() -> GoogleGenerativeAIEmbeddings:
    """
    Initialize and return a Gemini embedder via Google Generative AI.
    """
    logger.info("Initializing Gemini embedder...")
    api_key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

    try:
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=api_key,
            task_type="retrieval_document"
        )
    except Exception as e:
        logger.error(f"Error initializing embedder: {e}")
        raise RuntimeError(f"Failed to initialize embedder: {e}") from e


def build_vector_store(
    chunks: list[str],
    embedder: GoogleGenerativeAIEmbeddings,
    save_path: Union[str, Path] | None = None
) -> str:
    """
    Build and persist a FAISS vector store from text chunks.
    """
    target_path = Path(save_path) if save_path else settings.VECTOR_STORE_DIR
    target_path.parent.mkdir(parents=True, exist_ok=True)
    str_path = str(target_path)

    logger.info(f"Building vector store at: {str_path} with {len(chunks)} chunks")
    vector_store = FAISS.from_texts(chunks, embedder)
    vector_store.save_local(str_path)
    logger.info("Vector store successfully saved.")
    return str_path


def load_vector_store(save_path: Union[str, Path] | None = None) -> FAISS:
    """
    Load a saved FAISS vector store.
    """
    target_path = Path(save_path) if save_path else settings.VECTOR_STORE_DIR
    
    # Fallback to repo-root 'vector_store' if data/vector_store doesn't exist
    if not target_path.exists():
        legacy_path = settings.ROOT_DIR / "vector_store"
        if legacy_path.exists():
            target_path = legacy_path

    str_path = str(target_path)
    embedder = get_embedder()
    logger.info(f"Loading vector store from {str_path}...")
    vector_store = FAISS.load_local(str_path, embedder, allow_dangerous_deserialization=True)
    return vector_store
