from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def answer_query_with_context(chunks: list[str], query: str) -> str:
    """
    Use Google Gemini model via LangChain to answer a query based on context chunks.

    Args:
        chunks (list[str]): List of text chunks (retrieved from vector store).
        query (str): User query string.

    Returns:
        str: Model-generated answer.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0.2)

    context = "\n\n".join(chunks)

    template = """
    You are a helpful assistant. Use the provided context to answer the question.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )

    # Modern LCEL chain: prompt | llm | parser
    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"context": context, "question": query})