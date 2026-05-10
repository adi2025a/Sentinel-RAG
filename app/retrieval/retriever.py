from langchain_community.vectorstores import FAISS
from app.embeddings.embedder import get_embedder

from app.utils.logger import get_logger
logger = get_logger(__name__)

def load_vector_store(save_path: str = "vector_store"):
    """
    Load a saved FAISS vector store.
    
    Args:
        save_path (str): Path where FAISS index was saved.
    
    Returns:
        FAISS: Loaded vector store.
    """

    embedder = get_embedder()
    logger.info(f"Loading vector store from {save_path}...")
    vector_store = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
    return vector_store

def search_query(query: str, save_path: str = "vector_store", k: int = 3):
    """
    Perform semantic similarity search on a saved FAISS vector store.
    
    Args:
        query (str): The search query.
        save_path (str): Path to saved FAISS index.
        k (int): Number of top results to return.
    
    Returns:
        list: Top matching chunks.
    """
    vector_store = load_vector_store(save_path)
    logger.info(f"Searching for query: {query}")
    results = vector_store.similarity_search(query, k=k)
    logger.info(f"Search completed. Number of results: {len(results)}")
    return results
