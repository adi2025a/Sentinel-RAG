"""
app/rag/generator.py
====================
LLM answer generation using retrieved context chunks via Google Gemini.
"""

from __future__ import annotations
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(name=__name__)

PROMPT_TEMPLATE = """
You are a helpful assistant. Use the provided context to answer the question.

Context:
{context}

Question:
{question}

Answer:
"""


def answer_query_with_context(
    chunks: list[str],
    query: str,
    model_name: str | None = None,
    temperature: float = 0.2
) -> str:
    """
    Use Google Gemini model via LangChain to answer a query based on context chunks.

    Args:
        chunks: List of text chunks (retrieved from vector store).
        query: User query string.
        model_name: Optional Gemini model name override.
        temperature: Sampling temperature (default 0.2).

    Returns:
        str: Model-generated answer.
    """
    chosen_model = model_name or settings.GEMINI_CHAT_MODEL
    logger.info(f"Generating answer using {chosen_model} for query: {query!r}")

    llm = ChatGoogleGenerativeAI(model=chosen_model, temperature=temperature)
    context = "\n\n".join(chunks)

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=PROMPT_TEMPLATE
    )

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": query})
