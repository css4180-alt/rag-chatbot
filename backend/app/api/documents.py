import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth import get_account
from app.core.ingestion import ALLOWED_SUFFIXES, delete_document_chunks, ingest_document
from app.db.database import get_db
from app.db.models import ChatSession, Document
from app.schemas.document import DocumentResponse, DocumentUploadResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])

# 미리보기 시 브라우저가 인라인으로 렌더하도록 붙이는 media type.
INLINE_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


@router.post("", response_model=DocumentUploadResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    session_id: int | None = Form(None),
    db: Session = Depends(get_db),
    account: str = Depends(get_account),
):
    """문서를 업로드한다.

    ``session_id`` 가 없으면 전역 문서(모든 대화에서 참조), 있으면 해당 대화 전용
    문서로 저장한다. 원본 파일은 다운로드·미리보기를 위해 ``upload_dir`` 에
    ``{document_id}{확장자}`` 이름으로 영구 보관한다.
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

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = upload_dir / f"{doc.id}{suffix}"

    try:
        with open(storage_path, "wb") as out:
            out.write(file.file.read())

        chunk_count = ingest_document(str(storage_path), file.filename, doc.id, session_id=session_id)

        doc.chunk_count = chunk_count
        doc.status = "ready"
        doc.storage_path = str(storage_path)
        db.commit()
        db.refresh(doc)
    except Exception as exc:
        doc.status = "error"
        db.commit()
        # 색인 실패 시 보관 파일을 남기지 않는다.
        if storage_path.exists():
            storage_path.unlink()
        raise HTTPException(status_code=500, detail=str(exc))

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


def _get_doc_file(document_id: int, db: Session) -> tuple[Document, str]:
    """문서와 보관된 원본 파일 경로를 함께 반환한다(없으면 404)."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.storage_path or not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="원본 파일이 보관되어 있지 않습니다.")
    return doc, doc.storage_path


@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    """원본 파일을 첨부(다운로드)로 내려준다. 한글 파일명도 안전하게 처리된다."""
    doc, path = _get_doc_file(document_id, db)
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=doc.filename,  # Starlette가 RFC 6266(filename*) 으로 UTF-8 인코딩
    )


@router.get("/{document_id}/raw")
def raw_document(document_id: int, db: Session = Depends(get_db)):
    """원본 파일을 인라인으로 내려준다(브라우저 미리보기용)."""
    doc, path = _get_doc_file(document_id, db)
    suffix = os.path.splitext(path)[1].lower()
    media_type = INLINE_MEDIA_TYPES.get(suffix, "application/octet-stream")
    return FileResponse(path, media_type=media_type, content_disposition_type="inline")


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document_id)
    # 보관된 원본 파일도 함께 정리한다.
    if doc.storage_path and os.path.exists(doc.storage_path):
        os.remove(doc.storage_path)
    db.delete(doc)
    db.commit()
