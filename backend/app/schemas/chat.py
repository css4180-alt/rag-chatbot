from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: int | None = None


class SourceReference(BaseModel):
    document_id: int
    filename: str
    chunk_content: str


class ChatResponse(BaseModel):
    answer: str
    session_id: int
    sources: list[SourceReference] = []


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    sources: list[SourceReference] | None = None

    model_config = {"from_attributes": True}


class ChatSessionUpdate(BaseModel):
    title: str


class ChatSessionResponse(BaseModel):
    id: int
    title: str | None = None
    created_at: datetime
    last_message_at: datetime

    model_config = {"from_attributes": True}
