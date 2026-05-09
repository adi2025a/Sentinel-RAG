from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.chains import LLMChain

def answer_query_with_context(chunks: list[str], query: str) -> str:
    """
    Use Google Gemini model via LangChain to answer a query based on context chunks.
    
    Args:
        chunks (list[str]): List of text chunks (retrieved from vector store).
        query (str): User query string.
    
    Returns:
        str: Model-generated answer.
    """
    # Initialize Gemini model (make sure GOOGLE_API_KEY is set in your environment)
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.2)

    # Combine chunks into a single context string
    context = "\n\n".join(chunks)

    # Define a prompt template
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

    # Create chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run chain
    response = chain.run({"context": context, "question": query})
    return response
