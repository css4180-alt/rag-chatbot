from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from app.core.vectorstore import get_vectorstore

ALLOWED_SUFFIXES = {".pdf", ".md", ".txt"}
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def ingest_document(file_path: str, filename: str, document_id: int) -> int:
    """Parse, chunk, embed and store a document. Returns the number of chunks."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {suffix}")

    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    raw_docs = loader.load()
    chunks = _splitter.split_documents(raw_docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_index": str(i),
            }
        )

    get_vectorstore().add_documents(chunks)
    return len(chunks)


def delete_document_chunks(document_id: int) -> None:
    """Remove all vectors associated with a document from ChromaDB."""
    vs = get_vectorstore()
    results = vs._collection.get(where={"document_id": str(document_id)})
    ids = results.get("ids", [])
    if ids:
        vs.delete(ids)
