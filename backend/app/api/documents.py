from fastapi import APIRouter

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Endpoints will be implemented in step 2:
# POST /api/documents        — upload a PDF or Markdown file
# GET  /api/documents        — list all documents
# DELETE /api/documents/{id} — delete a document and its vectors
