import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import chat, documents
from app.db.database import Base, engine, run_lightweight_migrations

logger = logging.getLogger("uvicorn.error")


def _warm_embedder() -> None:
    """임베딩 모델을 백그라운드에서 미리 메모리에 적재한다.

    머신이 자동 중지(min_machines_running=0)되는 환경이라 매번 콜드 스타트가
    발생한다. 첫 질문 때 모델을 적재하면 그 요청이 수십 초간 지연되므로,
    서버 기동 직후 별도 스레드에서 미리 워밍업해 첫 응답 지연을 없앤다.
    포트 바인딩을 막지 않도록 스레드로 분리한다.
    """
    try:
        from app.core.embedder import get_embedder

        get_embedder()
        logger.info("Embedding model warmed up.")
    except Exception as exc:  # noqa: BLE001 - 워밍업 실패가 기동을 막으면 안 됨
        logger.warning("Embedder warm-up failed (lazy load on first use): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data/sqlite", exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()
    threading.Thread(target=_warm_embedder, daemon=True).start()
    yield


app = FastAPI(
    title="RAG Chatbot",
    description="Upload documents, ask in natural language.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


# 프론트엔드 정적 파일 서빙 (빌드 결과물이 있을 때만)
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
