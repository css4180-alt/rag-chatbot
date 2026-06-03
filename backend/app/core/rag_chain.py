from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
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


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def _owner_filter(session_id: int | None) -> dict:
    """검색 대상 범위 필터를 만든다.

    - session_id 가 None: 전역 문서만 검색.
    - session_id 가 있음: 전역 문서 + 해당 대화 전용 문서를 함께 검색.
    """
    if session_id is None:
        return {"owner": "global"}
    return {"owner": {"$in": ["global", str(session_id)]}}


def retrieve_relevant(
    question: str,
    session_id: int | None = None,
    k: int | None = None,
    score_threshold: float | None = None,
) -> list[Document]:
    """질문과 *충분히 관련 있는* 청크만 반환한다.

    상위 k개를 코사인 관련도 점수와 함께 가져온 뒤, 임계값 미만인 청크는
    버린다. 이렇게 하면 빈자리를 채우려고 끌려온 무관한 문서가 컨텍스트와
    출처에서 제외된다. 관련 청크가 하나도 없으면 빈 리스트를 반환한다
    (이 경우 LLM은 "문서에서 찾을 수 없다"고 답한다).
    """
    k = k or settings.retrieval_k
    threshold = settings.retrieval_score_threshold if score_threshold is None else score_threshold

    results = get_vectorstore().similarity_search_with_relevance_scores(
        question, k=k, filter=_owner_filter(session_id)
    )
    # results: [(Document, relevance_score)], 관련도 높은 순. 점수는 0~1.
    return [doc for doc, score in results if score >= threshold]


def build_answer_chain():
    """프롬프트 → LLM 체인. 컨텍스트는 호출 시 주입한다(검색은 외부에서 1회 수행).

    스트리밍 시 ``AIMessageChunk`` 를 그대로 받아 텍스트와 함께 ``usage_metadata``
    (입력/출력 토큰 수)를 추출하기 위해 StrOutputParser 는 붙이지 않는다.
    """
    prompt = ChatPromptTemplate.from_template(_PROMPT_TEMPLATE)
    return prompt | get_llm()
