from langchain_core.vectorstores import FAISS
from embeddings.embedder import get_embedder

def load_vector_store(save_path: str = "faiss_index"):
    """
    Load a saved FAISS vector store.
    
    Args:
        save_path (str): Path where FAISS index was saved.
    
    Returns:
        FAISS: Loaded vector store.
    """
    embedder = get_embedder()
    vector_store = FAISS.load_local(save_path, embedder, allow_dangerous_deserialization=True)
    return vector_store

def search_query(query: str, save_path: str = "faiss_index", k: int = 3):
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
    results = vector_store.similarity_search(query, k=k)
    return results
