from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text_into_chunks(raw_text: str, chunk_size: int = 100, chunk_overlap: int = 20) -> list[str]:
    """
    Splits raw text into chunks using LangChain's RecursiveCharacterTextSplitter.

    Args:
        raw_text (str): The full text to split.
        chunk_size (int): Maximum size of each chunk (default 100 characters).
        chunk_overlap (int): Overlap between chunks to preserve context (default 20 characters).

    Returns:
        list[str]: A list of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(raw_text)
    return chunks
