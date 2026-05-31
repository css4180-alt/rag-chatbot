# ---- 프론트엔드 빌드 ----
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Python 의존성 설치 ----
FROM python:3.11-slim AS py-builder
WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- 런타임 ----
FROM python:3.11-slim AS runtime
WORKDIR /app

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# HuggingFace 모델 캐시 경로를 쓰기 가능한 위치로 고정.
# (appuser는 홈 디렉터리가 없어 기본 캐시 경로 /home/appuser/.cache 에 쓸 수 없음)
ENV HF_HOME=/app/hf_cache

COPY --from=py-builder /install /usr/local
COPY backend/app/ ./app/
COPY --from=frontend-builder /frontend/dist ./static/

# 임베딩 모델을 빌드 시점에 이미지로 미리 내려받는다.
# → 런타임 권한 에러 제거 + 콜드 스타트 단축(첫 질문 시 다운로드 안 함).
RUN python -c "from langchain_community.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='intfloat/multilingual-e5-small', model_kwargs={'device': 'cpu'})"

RUN mkdir -p data/chroma data/sqlite && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
