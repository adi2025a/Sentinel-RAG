"""
app/rag/ingestion.py
====================
Secure PDF text extraction, sanitization, and chunking.
"""

from __future__ import annotations
import re
import unicodedata
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.logger import get_logger

logger = get_logger(name=__name__)

ZERO_WIDTH_PATTERN = re.compile(r'[\u200B\u200C\u200D\u2060\uFEFF]')


def extract_visible_text(pdf_bytes: bytes) -> str:
    """
    Extract only visible text from PDF bytes.
    Ignores invisible text spans, metadata, attachments, forms.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    extracted_text = []

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    if span["size"] < 1:  # Ignore invisible or near-invisible text
                        continue
                    extracted_text.append(text)

    doc.close()
    return "\n".join(extracted_text)


def sanitize_text(text: str) -> str:
    """Remove zero-width chars and control chars except newline/tab."""
    text = ZERO_WIDTH_PATTERN.sub("", text)
    return ''.join(
        ch for ch in text
        if ch == '\n' or ch == '\t' or ord(ch) >= 32
    )


def sanitize_pdf(pdf_bytes: bytes) -> bytes:
    """Remove annotations, metadata, and scripts from PDF bytes."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    doc.set_metadata({})

    for page in doc:
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot

    sanitized_pdf = doc.tobytes(garbage=4, clean=True, deflate=True)
    doc.close()
    return sanitized_pdf


def normalize_text(text: str) -> str:
    """Normalize text for RAG indexing (Unicode NFKC, lowercase, whitespace)."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = sanitize_text(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.!?]){2,}', r'\1', text)
    text = re.sub(r'[-_=]{3,}', ' ', text)
    return text.strip()


def secure_pdf_to_text(pdf_bytes: bytes) -> str:
    """Full extraction & sanitization pipeline from raw PDF bytes."""
    text = extract_visible_text(pdf_bytes)
    text = sanitize_text(text)
    text = normalize_text(text)
    return text


def split_text_into_chunks(
    raw_text: str,
    chunk_size: int = 100,
    chunk_overlap: int = 20
) -> list[str]:
    """Splits raw text into chunks using LangChain's RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(raw_text)
