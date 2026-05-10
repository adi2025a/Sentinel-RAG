import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.utils.logger import get_logger

load_dotenv()

logger = get_logger(name=__name__)

def get_embedder() -> GoogleGenerativeAIEmbeddings:
    """
    Initialize and return a Gemini embedder via Google Generative AI.

    Returns:
        GoogleGenerativeAIEmbeddings: Configured embedder instance.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
        RuntimeError: If the embedder fails to initialize.
    """
    logger.info("Initializing Gemini embedder...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

    logger.info("GOOGLE_API_KEY found.")
    try:
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key,
            task_type="retrieval_document"
        )
    except Exception as e:
        logger.error(f"Error initializing embedder: {e}")
        raise RuntimeError(f"Failed to initialize embedder: {e}") from e
