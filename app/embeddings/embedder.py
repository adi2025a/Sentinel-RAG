from langchain.embeddings import HuggingFaceEmbeddings

def get_embeddings_from_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Convert text chunks into embeddings using Hugging Face models.
    
    Args:
        chunks (list[str]): List of text chunks.
    
    Returns:
        list[list[float]]: Embedding vectors for each chunk.
    """
    # Initialize Hugging Face embeddings (default model: sentence-transformers/all-MiniLM-L6-v2)
    embedder = HuggingFaceEmbeddings()
    
    # Generate embeddings for all chunks
    embeddings = embedder.embed_documents(chunks)
    return embeddings , embedder
