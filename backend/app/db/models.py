import json
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    # NULL이면 전역 문서(모든 대화에서 참조), 값이 있으면 해당 대화 전용 문서.
    session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("chat_sessions.id"), nullable=True, index=True
    )
    # 업로드된 원본 파일의 디스크 경로. 다운로드·미리보기에 사용한다.
    # NULL이면 이 기능 도입 이전에 올라온 문서(원본 미보관).
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    @property
    def has_file(self) -> bool:
        """다운로드·미리보기가 가능한(원본이 보관된) 문서인지 여부."""
        return bool(self.storage_path)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_message_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def get_sources(self) -> list | None:
        if self.sources is None:
            return None
        return json.loads(self.sources)

    def set_sources(self, sources: list) -> None:
        self.sources = json.dumps(sources)


class TokenUsage(Base):
    """일자별·범위별 LLM 토큰 누적 사용량.

    ``scope`` 는 계정 라벨이거나 사이트 전체를 뜻하는 특수값(``__site__``)이다.
    ``usage_date`` 는 UTC 기준 ``YYYY-MM-DD`` 문자열로, 매일 새 행이 만들어져
    자정마다 자연스럽게 리셋되는 효과를 낸다.
    """

    __tablename__ = "token_usage"
    __table_args__ = (UniqueConstraint("scope", "usage_date", name="uq_scope_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scope: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    usage_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
