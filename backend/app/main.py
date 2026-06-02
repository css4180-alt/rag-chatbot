import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import chat, documents
from app.db.database import Base, engine, run_lightweight_migrations

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 임베딩/LLM을 Bedrock API로 호출하므로 로컬 모델 워밍업이 필요 없다.
    os.makedirs("data/sqlite", exist_ok=True)
    os.makedirs("data/chroma", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    run_lightweight_migrations()
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
