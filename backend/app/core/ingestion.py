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


def ingest_document(
    file_path: str,
    filename: str,
    document_id: int,
    session_id: int | None = None,
) -> int:
    """Parse, chunk, embed and store a document. Returns the number of chunks.

    ``session_id`` 가 None 이면 전역 문서(모든 대화에서 검색됨), 값이 있으면 해당
    대화 전용 문서다. 검색 시 필터링할 수 있도록 각 청크 메타데이터에 ``owner``
    필드("global" 또는 세션 id 문자열)를 기록한다.
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError(f"Unsupported file type: {suffix}")

    if suffix == ".pdf":
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    raw_docs = loader.load()
    chunks = _splitter.split_documents(raw_docs)

    owner = "global" if session_id is None else str(session_id)
    for i, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_index": str(i),
                "owner": owner,
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
