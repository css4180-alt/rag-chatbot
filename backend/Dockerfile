# ---- builder ----
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime ----
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

COPY --from=builder /install /usr/local
COPY app/ ./app/

# Data directories (will be volume-mounted in production)
RUN mkdir -p data/chroma data/sqlite && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
