from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    chunk_count: int
    status: str
    session_id: int | None = None  # None이면 전역 문서

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
