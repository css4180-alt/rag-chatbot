import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.ingestion import ALLOWED_SUFFIXES, delete_document_chunks, ingest_document
from app.db.database import get_db
from app.db.models import ChatSession, Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    session_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """문서를 업로드한다.

    ``session_id`` 가 없으면 전역 문서(모든 대화에서 참조), 있으면 해당 대화 전용
    문서로 저장한다.
    """
    suffix = os.path.splitext(file.filename or "")[1].lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(ALLOWED_SUFFIXES)}",
        )

    if session_id is not None:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

    doc = Document(filename=file.filename, status="processing", session_id=session_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        chunk_count = ingest_document(tmp_path, file.filename, doc.id, session_id=session_id)

        doc.chunk_count = chunk_count
        doc.status = "ready"
        db.commit()
        db.refresh(doc)
    except Exception as exc:
        doc.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return DocumentUploadResponse(
        document=DocumentResponse.model_validate(doc),
        message=f"Ingested {chunk_count} chunks from '{file.filename}'.",
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    scope: str | None = None,
    session_id: int | None = None,
    db: Session = Depends(get_db),
):
    """문서 목록을 조회한다.

    - ``session_id`` 지정: 해당 대화 전용 문서만.
    - ``scope=global``: 전역 문서(session_id IS NULL)만.
    - 둘 다 없으면: 전체 문서.
    """
    query = db.query(Document)
    if session_id is not None:
        query = query.filter(Document.session_id == session_id)
    elif scope == "global":
        query = query.filter(Document.session_id.is_(None))
    return query.order_by(Document.uploaded_at.desc()).all()


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document_id)
    db.delete(doc)
    db.commit()
