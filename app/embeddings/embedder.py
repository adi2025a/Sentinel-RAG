from langchain.embeddings import HuggingFaceEmbeddings

def get_embedder():
    """
    Initialize and return a Hugging Face embedder.
    
    Returns:
        HuggingFaceEmbeddings: An instance of the Hugging Face embedder.
    """
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return embedder


def get_embeddings_from_chunks(chunks: list[str]) -> list[list[float]]:
    """
    Convert text chunks into embeddings using Hugging Face models.
    
    Args:
        chunks (list[str]): List of text chunks.
    
    Returns:
        list[list[float]]: Embedding vectors for each chunk.
    """
    embedder = get_embedder()
    
    # Generate embeddings for all chunks
    embeddings = embedder.embed_documents(chunks)
    return embeddings , embedder
