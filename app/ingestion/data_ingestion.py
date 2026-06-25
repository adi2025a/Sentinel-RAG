import fitz  # PyMuPDF
import re
import unicodedata
from typing import Union


# --------------------------------------------------
# 1. Extract visible text only
# --------------------------------------------------
def extract_visible_text(pdf_bytes: bytes) -> str:
    """
    Extract only visible text from PDF bytes.
    Ignores metadata, attachments, forms, etc.
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

                    # Ignore invisible or near-invisible text
                    if span["size"] < 1:
                        continue

                    extracted_text.append(text)

    doc.close()

    return "\n".join(extracted_text)


# --------------------------------------------------
# 2. PDF Sanitization
# --------------------------------------------------

ZERO_WIDTH_PATTERN = re.compile(
    r'[\u200B\u200C\u200D\u2060\uFEFF]'
)


def sanitize_text(text: str) -> str:
    """
    Remove hidden unicode characters,
    control characters and suspicious text.
    """

    # Remove zero-width chars
    text = ZERO_WIDTH_PATTERN.sub("", text)

    # Remove control chars except newline/tab
    text = ''.join(
        ch for ch in text
        if ch == '\n'
        or ch == '\t'
        or ord(ch) >= 32
    )

    return text


def sanitize_pdf(pdf_bytes: bytes) -> bytes:
    """
    Create a sanitized PDF from PDF bytes.

    Removes:
      - metadata
      - annotations
      - embedded files (where possible via garbage collection)
      - forms (if removed during save cleanup)
      - javascript (if removed during save cleanup)

    Returns:
        Sanitized PDF bytes.
    """

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Remove metadata
    doc.set_metadata({})

    for page in doc:

        # Remove annotations
        annot = page.first_annot
        while annot:
            next_annot = annot.next
            page.delete_annot(annot)
            annot = next_annot

    sanitized_pdf = doc.tobytes(
        garbage=4,
        clean=True,
        deflate=True
    )

    doc.close()

    return sanitized_pdf


# --------------------------------------------------
# 3. Normalization
# --------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize text for RAG indexing.
    """

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Lowercase
    text = text.lower()

    # Remove hidden chars
    text = sanitize_text(text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove repeated punctuation
    text = re.sub(r'([.!?]){2,}', r'\1', text)

    # Remove excessive separators
    text = re.sub(r'[-_=]{3,}', ' ', text)

    return text.strip()


def secure_pdf_to_text(pdf_bytes: bytes) -> str:
    """
    Full extraction pipeline from PDF bytes.
    """

    text = extract_visible_text(pdf_bytes)

    text = sanitize_text(text)

    text = normalize_text(text)

    return text