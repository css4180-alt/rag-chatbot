# rag-chatbot

Upload your documents, ask in natural language. RAG-based document Q&A chatbot built with FastAPI, LangChain, and Gemini.

**Live demo**: Coming soon

---

## Features

- Upload PDF and Markdown documents
- Ask questions in natural language (Korean & English)
- Grounded answers with source references
- Conversation history per session
- Streaming responses (SSE)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| LLM | Google Gemini 2.0 Flash |
| Embedding | `intfloat/multilingual-e5-small` (local, no API cost) |
| Vector DB | ChromaDB (file-based) |
| Metadata DB | SQLite |
| RAG Framework | LangChain |
| Frontend | Vue 3 + Vite |
| Container | Docker |
| Deployment | Fly.io |

## Architecture

See [docs/architecture.md](docs/architecture.md) for a detailed diagram and explanation.

## Quickstart

```bash
# 1. Clone
git clone https://github.com/css4180-alt/rag-chatbot.git
cd rag-chatbot

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and fill in your GOOGLE_API_KEY

# 3. Run with Docker Compose
docker compose up --build

# 4. Open API docs
open http://localhost:8000/docs
```

## Development (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Running Tests

```bash
cd backend
pytest
```

## Roadmap

- [x] Project setup & directory structure
- [ ] Document upload + chunking + embedding
- [ ] RAG chain (retriever + LLM)
- [ ] Chat API with SSE streaming
- [ ] Vue 3 frontend
- [ ] Docker single-container build
- [ ] Fly.io deployment
- [ ] GitHub Actions CI/CD

## License

MIT — see [LICENSE](LICENSE)
