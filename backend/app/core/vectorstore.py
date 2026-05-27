from functools import lru_cache

from langchain_chroma import Chroma

from app.config import settings
from app.core.embedder import get_embedder


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    return Chroma(
        persist_directory=settings.chroma_persist_dir,
        embedding_function=get_embedder(),
        collection_name="documents",
    )
