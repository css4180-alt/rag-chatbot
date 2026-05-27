from langchain_core.documents import Document


def build_rag_chain():
    """Build and return a LangChain RAG chain.

    Combines the vectorstore retriever and LLM with a prompt template
    to answer questions based on retrieved document chunks.
    Implementation in step 2.
    """
    raise NotImplementedError("RAG chain will be implemented in step 2")


def answer_question(question: str, session_id: int | None = None) -> dict:
    """Answer a question using RAG.

    Args:
        question: The user's natural language question.
        session_id: Optional existing session to continue.

    Returns:
        Dict with keys: answer (str), sources (list[Document]), session_id (int).

    Implementation in step 2.
    """
    raise NotImplementedError("RAG query will be implemented in step 2")
