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


def get_retriever(k: int = 4):
    return get_vectorstore().as_retriever(search_kwargs={"k": k})


def build_rag_chain():
    """Build a LangChain LCEL RAG chain (retriever → prompt → LLM → parser)."""
    prompt = ChatPromptTemplate.from_template(_PROMPT_TEMPLATE)
    chain = (
        {"context": get_retriever() | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )
    return chain


def retrieve_sources(question: str, k: int = 4) -> list[Document]:
    """Return the top-k relevant document chunks for a question."""
    return get_retriever(k=k).invoke(question)
