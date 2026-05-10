from app.ingestion.pdf_text_extractor import extract_text_from_pdf
from app.ingestion.chunking import split_text_into_chunks
from app.embeddings.embedder import get_embedder
from app.embeddings.vector_store import build_vector_store    
from app.llm.output import answer_query_with_context
from app.utils.logger import get_logger


logger = get_logger(name=__name__)

def ingestion_test(contents):
    logger.info("Starting ingestion test...")
    text = extract_text_from_pdf(contents)
    logger.info("Text extraction completed.")
    logger.info("Starting text chunking...")
    chunks = split_text_into_chunks(text)
    logger.info(f"Text chunking completed. Number of chunks: {len(chunks)}")
    embedder = get_embedder()
    logger.info("Embedder granted.")
    vector_store = build_vector_store(chunks,embedder)
    logger.info("Vector store built.")

def query_test(query):
    logger.info("Starting query test...")
    from app.retrieval.retriever import search_query
    results = search_query(query)
    logger.info(f"Search completed. Number of results: {len(results)}")
    for i, res in enumerate(results):
        logger.info(f"--- Result {i+1} ---")
        logger.info(res.page_content)

    answer = answer_query_with_context([res.page_content for res in results], query)
    return answer
    