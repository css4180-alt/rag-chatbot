from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from app.core.llm import get_llm
from app.core.vectorstore import get_vectorstore

_PROMPT_TEMPLATE = """\
You are a helpful assistant that answers questions based on the provided documents.
Use only the information from the context below to answer the question.
If the answer cannot be found in the context, say so clearly.
Respond in the same language as the question.

Context:
{context}

Question: {question}

Answer:"""


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def _owner_filter(session_id: int | None) -> dict:
    """검색 대상 범위 필터를 만든다.

    - session_id 가 None: 전역 문서만 검색.
    - session_id 가 있음: 전역 문서 + 해당 대화 전용 문서를 함께 검색.
    """
    if session_id is None:
        return {"owner": "global"}
    return {"owner": {"$in": ["global", str(session_id)]}}


def get_retriever(k: int = 4, session_id: int | None = None):
    return get_vectorstore().as_retriever(
        search_kwargs={"k": k, "filter": _owner_filter(session_id)}
    )


def build_rag_chain(session_id: int | None = None):
    """Build a LangChain LCEL RAG chain (retriever → prompt → LLM → parser)."""
    prompt = ChatPromptTemplate.from_template(_PROMPT_TEMPLATE)
    retriever = get_retriever(session_id=session_id)
    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain


def retrieve_sources(question: str, session_id: int | None = None, k: int = 4) -> list[Document]:
    """Return the top-k relevant document chunks for a question."""
    return get_retriever(k=k, session_id=session_id).invoke(question)
