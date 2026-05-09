import io
from PyPDF2 import PdfReader

def extract_text_from_pdf(contents: bytes) -> str:
    """
    Extract text from PDF bytes using PyPDF2.
    
    Args:
        contents (bytes): Raw PDF file content.
    
    Returns:
        str: Extracted text from all pages.
    """
    text = ""
    # Wrap bytes in a BytesIO buffer so PdfReader can handle it
    pdf_buffer = io.BytesIO(contents)
    reader = PdfReader(pdf_buffer)

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text
