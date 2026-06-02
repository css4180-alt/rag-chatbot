# CLAUDE.md — rag-chatbot

## Project Overview

Portfolio project for backend developer job applications. A RAG-based chatbot that lets users upload PDF/Markdown documents and ask questions in natural language.

This is a **public open-source project** and will be shared on GitHub. It has no relationship to any employer or proprietary codebase.

---

## Hard Rules (never violate)

1. **Do not reference company code.** `/Users/seokhyun/projects/` is completely off-limits. No variable names, function names, file conventions, or business logic from that directory may appear here.

2. **This is a generic RAG chatbot.** It has no domain affiliation (no translation, copyright, content-matching, or other employer-specific logic).

3. **No secrets in commits.** `.env` is gitignored. API keys, tokens, and passwords must never appear in tracked files. Use `.env.example` for documentation.

---

## Directory Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── config.py        # pydantic-settings env loader
│   │   ├── api/             # Route handlers (documents, chat)
│   │   ├── core/            # Business logic (embedder, vectorstore, llm, rag_chain)
│   │   ├── db/              # SQLAlchemy setup and ORM models
│   │   └── schemas/         # Pydantic request/response schemas
│   ├── tests/
│   ├── data/                # gitignored — runtime data only
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/                # Vue 3 + Vite (step 3)
├── docs/
├── docker-compose.yml
└── README.md
```

---

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.11 |
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0 (sync) |
| Validation | Pydantic v2 + pydantic-settings |
| LLM | AWS Bedrock — Claude 3.5 Haiku (`langchain-aws` `ChatBedrockConverse`) |
| Embedding | AWS Bedrock — Amazon Titan Text Embeddings V2 (`langchain-aws` `BedrockEmbeddings`) |
| Vector DB | ChromaDB (local file, `langchain-chroma`) |
| Metadata DB | SQLite |
| Frontend | Vue 3 + Vite |
| Container | Docker (single container) |
| Deployment | AWS EC2 (Docker + Caddy 자동 HTTPS) |
| CI/CD | GitHub Actions |
| Testing | pytest + httpx |

---

## Code Style

- Follow PEP 8.
- Type hints are **required** on all function signatures.
- Docstrings are recommended for public functions and classes.
- Keep modules focused — one responsibility per file.
- No wildcard imports.
- Line length: 100 characters (ruff configured in pyproject.toml).
