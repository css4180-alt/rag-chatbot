import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.ingestion import delete_document_chunks
from app.core.rag_chain import build_rag_chain, retrieve_sources
from app.db.database import SessionLocal, get_db
from app.db.models import ChatMessage, ChatSession, Document
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatSessionResponse,
    SourceReference,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _make_title(question: str, limit: int = 60) -> str:
    """첫 질문을 대화 제목으로 사용한다(길면 잘라서)."""
    title = " ".join(question.strip().split())
    return title[:limit] + ("…" if len(title) > limit else "")


@router.post("")
def ask(request: ChatRequest, db: Session = Depends(get_db)):
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

    # Retrieve sources and build chain outside the generator (blocking, but fast).
    # 전역 문서 + 이 대화 전용 문서를 검색 대상으로 삼는다.
    source_docs = retrieve_sources(question, session_id=session_id)
    sources = [
        SourceReference(
            document_id=int(doc.metadata.get("document_id", 0)),
            filename=doc.metadata.get("filename", ""),
            chunk_content=doc.page_content[:300],
        )
        for doc in source_docs
    ]
    chain = build_rag_chain(session_id=session_id)

    def event_stream():
        full_answer = ""

        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"

        for token in chain.stream(question):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'sources', 'sources': [s.model_dump() for s in sources]})}\n\n"

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

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    return db.query(ChatSession).order_by(ChatSession.last_message_at.desc()).all()


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
