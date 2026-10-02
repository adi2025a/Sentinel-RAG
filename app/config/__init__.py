"""
app/config/__init__.py
======================
Centralized configuration for SentinelRAG.
Loads environment variables and sets path defaults.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if present
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    # ── Base Directories ───────────────────────────────────────────────────
    ROOT_DIR: Path = _ROOT_DIR
    APP_DIR: Path = _ROOT_DIR / "app"
    DATA_DIR: Path = _ROOT_DIR / "data"
    MODELS_DIR: Path = _ROOT_DIR / "data" / "models"
    VECTOR_STORE_DIR: Path = _ROOT_DIR / "data" / "vector_store"
    EVALS_DIR: Path = _ROOT_DIR / "evals"

    # ── Security (PID) Paths & Fallbacks ──────────────────────────────────
    ATTACK_INDEX_PATH: Path = field(
        default_factory=lambda: (
            _ROOT_DIR / "data" / "models" / "attack_index.faiss"
            if (_ROOT_DIR / "data" / "models" / "attack_index.faiss").exists()
            else _ROOT_DIR / "app" / "security" / "PID" / "attack_index.faiss"
        )
    )
    ATTACK_METADATA_PATH: Path = field(
        default_factory=lambda: (
            _ROOT_DIR / "data" / "models" / "attack_metadata.pkl"
            if (_ROOT_DIR / "data" / "models" / "attack_metadata.pkl").exists()
            else _ROOT_DIR / "app" / "security" / "PID" / "attack_metadata.pkl"
        )
    )

    # ── Thresholds & Hyperparameters ──────────────────────────────────────
    PID_BLOCK_THRESHOLD: float = float(os.getenv("PID_BLOCK_THRESHOLD", "0.65"))
    PID_REVIEW_THRESHOLD: float = float(os.getenv("PID_REVIEW_THRESHOLD", "0.40"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    SEMANTIC_TOP_K: int = int(os.getenv("SEMANTIC_TOP_K", "5"))

    # ── Models & Keys ─────────────────────────────────────────────────────
    SEMANTIC_MODEL_NAME: str = os.getenv("SEMANTIC_MODEL_NAME", "BAAI/bge-base-en-v1.5")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.1-flash-lite-preview")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "default-admin-token")


settings = Settings()
