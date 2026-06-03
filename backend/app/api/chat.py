import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core import usage
from app.core.auth import get_account
from app.core.ingestion import delete_document_chunks
from app.core.rag_chain import build_answer_chain, format_docs, retrieve_relevant
from app.db.database import SessionLocal, get_db
from app.db.models import ChatMessage, ChatSession, Document
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatSessionResponse,
    ChatSessionUpdate,
    SourceReference,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _make_title(question: str, limit: int = 60) -> str:
    """첫 질문을 대화 제목으로 사용한다(길면 잘라서)."""
    title = " ".join(question.strip().split())
    return title[:limit] + ("…" if len(title) > limit else "")


def _chunk_text(content) -> str:
    """``AIMessageChunk.content`` 에서 표시용 텍스트만 뽑아낸다.

    Bedrock Converse 는 청크 content 가 문자열이거나, ``{"type": "text", ...}``
    형태의 블록 리스트일 수 있어 양쪽을 모두 처리한다.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return ""


@router.post("")
def ask(
    request: ChatRequest,
    db: Session = Depends(get_db),
    account: str = Depends(get_account),
):
    # 호출 전 토큰 쿼터 검사(계정별 + 사이트 전체). 초과 시 429.
    ok, reason = usage.check_quota(db, account)
    if not ok:
        raise HTTPException(status_code=429, detail=reason)

    # Resolve or create session
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession()
        db.add(session)
        db.commit()
        db.refresh(session)

    # 첫 질문이면 대화 제목을 지정
    if not session.title:
        session.title = _make_title(request.question)
        db.commit()

    # Persist user message before streaming
    user_msg = ChatMessage(session_id=session.id, role="user", content=request.question)
    db.add(user_msg)
    db.commit()

    session_id = session.id
    question = request.question

    # 검색은 1회만 수행하고, 그 결과로 컨텍스트와 출처를 함께 만든다(둘이 항상 일치).
    # 전역 문서 + 이 대화 전용 문서를 대상으로, 관련도 임계값을 넘는 청크만 남긴다.
    relevant_docs = retrieve_relevant(question, session_id=session_id)
    context = format_docs(relevant_docs)

    # 출처는 문서 단위로 중복 제거(같은 문서의 여러 청크는 한 번만 표시).
    sources: list[SourceReference] = []
    seen_docs: set[int] = set()
    for doc in relevant_docs:
        doc_id = int(doc.metadata.get("document_id", 0))
        if doc_id in seen_docs:
            continue
        seen_docs.add(doc_id)
        sources.append(
            SourceReference(
                document_id=doc_id,
                filename=doc.metadata.get("filename", ""),
                chunk_content=doc.page_content[:300],
            )
        )

    chain = build_answer_chain()

    def event_stream():
        full_answer = ""
        gathered = None  # 청크를 합산해 마지막에 usage_metadata 를 추출

        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

        for chunk in chain.stream({"context": context, "question": question}):
            gathered = chunk if gathered is None else gathered + chunk
            token = _chunk_text(chunk.content)
            if not token:
                continue
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"

        # 실제 토큰 사용량 집계(입력+출력). 메타데이터가 없으면 대략 추정.
        meta = getattr(gathered, "usage_metadata", None) or {}
        total_tokens = int(meta.get("total_tokens") or 0)
        if total_tokens == 0:
            total_tokens = (len(question) + len(full_answer)) // 4  # 대략적 fallback

        # Persist assistant message with a fresh DB session (generator runs in a thread)
        with SessionLocal() as write_db:
            assistant_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_answer,
            )
            assistant_msg.set_sources([s.model_dump() for s in sources])
            write_db.add(assistant_msg)
            write_db.query(ChatSession).filter(ChatSession.id == session_id).update(
                {"last_message_at": datetime.utcnow()}
            )
            write_db.commit()
            usage.record_usage(write_db, account, total_tokens)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
def create_session(
    db: Session = Depends(get_db),
    account: str = Depends(get_account),
):
    """빈 대화를 미리 만든다.

    첫 메시지를 보내기 전에도 이 대화 전용 문서를 업로드할 수 있도록,
    프런트의 "새 대화" 진입 시점에 세션을 선발급한다. 제목은 첫 질문 때 채워진다.
    """
    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.last_message_at.desc()).all()


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
def rename_session(
    session_id: int,
    payload: ChatSessionUpdate,
    db: Session = Depends(get_db),
    account: str = Depends(get_account),
):
    """대화 제목을 수정한다. 빈 문자열은 허용하지 않는다."""
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="제목을 입력해 주세요.")

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = title[:200]
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(session_id: int, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    # sources 는 DB에 JSON 문자열로 저장되므로 응답 스키마에 맞게 파싱한다.
    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            sources=m.get_sources(),
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """대화와 그 대화 전용 문서·메시지를 함께 삭제한다(전역 문서는 보존)."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 이 대화 전용 문서의 벡터 청크 + 메타데이터 삭제
    docs = db.query(Document).filter(Document.session_id == session_id).all()
    for doc in docs:
        delete_document_chunks(doc.id)
        db.delete(doc)

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
