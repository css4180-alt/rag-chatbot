from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Endpoints will be implemented in step 2:
# POST /api/chat             — ask a question (RAG), returns SSE stream
# GET  /api/chat/sessions    — list chat sessions
# GET  /api/chat/sessions/{id}/messages — get messages in a session
