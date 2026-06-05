from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)


class Base(DeclarativeBase):
    pass


def run_lightweight_migrations() -> None:
    """초기 배포 이후 추가된 컬럼을 기존 SQLite DB에 반영한다.

    Alembic 없이 운영하는 소규모 프로젝트라, 누락된 컬럼만 ADD COLUMN 으로
    채워 넣는다. ``create_all`` 은 새 테이블만 만들 뿐 기존 테이블의 컬럼은
    추가하지 못하므로 이 보강 단계가 필요하다.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    pending: list[str] = []

    if "chat_sessions" in tables:
        cols = {c["name"] for c in inspector.get_columns("chat_sessions")}
        if "title" not in cols:
            pending.append("ALTER TABLE chat_sessions ADD COLUMN title VARCHAR(200)")

    if "documents" in tables:
        cols = {c["name"] for c in inspector.get_columns("documents")}
        if "session_id" not in cols:
            pending.append("ALTER TABLE documents ADD COLUMN session_id INTEGER")
        if "storage_path" not in cols:
            pending.append("ALTER TABLE documents ADD COLUMN storage_path VARCHAR(500)")

    if pending:
        with engine.begin() as conn:
            for stmt in pending:
                conn.execute(text(stmt))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
