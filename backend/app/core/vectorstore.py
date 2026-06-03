from functools import lru_cache

from langchain_chroma import Chroma

from app.config import settings
from app.core.embedder import get_embedder


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    # 코사인 거리를 쓰면 관련도 점수가 0~1로 잘 정규화되어 임계값 필터링이
    # 안정적이다(L2 기본값은 Titan 임베딩에서 점수 범위가 들쭉날쭉하다).
    # 주의: 이 메타데이터는 컬렉션 "생성 시"에만 적용된다. 기존 컬렉션이
    # 이미 L2로 만들어졌다면 chroma 디렉터리를 비우고 다시 색인해야 한다.
    return Chroma(
        persist_directory=settings.chroma_persist_dir,
        embedding_function=get_embedder(),
        collection_name="documents",
        collection_metadata={"hnsw:space": "cosine"},
    )
