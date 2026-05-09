from langchain_core.vectorstores import FAISS
from .embedder import get_embeddings_from_chunks as embed_chunks

def build_vector_store(chunks: list[str]):
    save_path = "vector_store"
    embedder, chunks = embed_chunks(chunks)
    vector_store = FAISS.from_texts(chunks, embedder)
    vector_store.save_local(save_path)
    return save_path


