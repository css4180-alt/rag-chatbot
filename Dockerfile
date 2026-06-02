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

COPY --from=py-builder /install /usr/local
COPY backend/app/ ./app/
COPY --from=frontend-builder /frontend/dist ./static/

# 임베딩/LLM은 AWS Bedrock API로 호출하므로 로컬 모델 적재가 없다.
# → 이미지가 가볍고(torch 미포함) 콜드 스타트가 없다.
RUN mkdir -p data/chroma data/sqlite && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
