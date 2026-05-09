from langchain_core.vectorstores import FAISS
from .embedder import get_embeddings_from_chunks as embed_chunks

def build_vector_store(chunks: list[str]):
    embedder, chunks = embed_chunks(chunks)
    vector_store = FAISS.from_texts(chunks, embedder)
    return vector_store

# Step 4: Perform semantic similarity search
def semantic_search(vector_store: FAISS, query: str, k: int = 3):
    results = vector_store.similarity_search(query, k=k)
    return results

