from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    chunk_count: int
    status: str
    session_id: int | None = None  # None이면 전역 문서
    has_file: bool = False  # 원본이 보관되어 다운로드·미리보기가 가능한지

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str
