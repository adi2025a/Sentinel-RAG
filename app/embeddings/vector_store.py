from langchain_community.vectorstores import FAISS

def build_vector_store(chunks: list[str],embedder) -> str:
    save_path: str = "vector_store"
    vector_store = FAISS.from_texts(chunks, embedder)
    vector_store.save_local(save_path)
    return save_path