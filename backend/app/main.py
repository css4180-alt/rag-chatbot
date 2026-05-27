from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, chat

app = FastAPI(
    title="RAG Chatbot",
    description="Upload documents, ask in natural language.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers will be included in step 2
# app.include_router(documents.router)
# app.include_router(chat.router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
