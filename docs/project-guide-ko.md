# 프로젝트 구조 가이드 (한국어)

이 문서는 rag-chatbot 프로젝트의 전체 구조와 동작 방식을 처음 보는 사람도
이해할 수 있게 설명합니다.

---

## 1. 한 문장 요약

> 사용자가 **문서를 올리면**, 그 문서 내용을 근거로 **AI가 질문에 답하는** 챗봇.

핵심 개념은 **RAG (Retrieval-Augmented Generation)**입니다.
AI가 아무거나 지어내는 게 아니라, 내가 올린 문서에서 찾은 내용으로만 답합니다.

---

## 2. 가장 큰 그림

```
[프론트엔드]  ←→  [백엔드]  ←→  [저장소 2개]
   Vue 3          FastAPI       SQLite + ChromaDB
   화면           두뇌·로직      데이터 보관
                     ↕
               [Google Gemini]  ← 실제 답변 생성하는 외부 AI
```

| 덩어리 | 폴더 | 역할 | 비유 |
|---|---|---|---|
| 프론트엔드 | `frontend/` | 사용자가 보는 화면 | 식당 홀 |
| 백엔드 | `backend/` | 요청 처리, 비즈니스 로직 | 주방 |
| 저장소 | `backend/data/` | 데이터 보관 | 창고 |

---

## 3. 전체 파일 구조

```
rag-chatbot/
│
├── frontend/                   ← Vue 3 화면 (빌드하면 backend/static/에 들어감)
│   ├── src/
│   │   ├── App.vue             앱 루트
│   │   ├── components/
│   │   │   ├── DocumentPanel.vue   문서 업로드·목록·삭제 화면
│   │   │   └── ChatPanel.vue       채팅 화면 (스트리밍 응답)
│   │   └── api/client.js       백엔드 API 호출 함수 모음
│   ├── vite.config.js          개발 서버 설정 (백엔드로 프록시)
│   └── package.json            npm 의존성
│
├── backend/
│   ├── app/
│   │   ├── main.py             ← 서버 시작점 (FastAPI 앱 생성, 라우터 연결)
│   │   ├── config.py           ← 환경변수 설정 (API키, DB 경로)
│   │   │
│   │   ├── api/                ← 접수처: HTTP 요청을 받아서 core에 넘김
│   │   │   ├── documents.py    POST/GET/DELETE /api/documents
│   │   │   └── chat.py         POST /api/chat (SSE 스트리밍)
│   │   │
│   │   ├── core/               ← 실제 일하는 곳 (비즈니스 로직)
│   │   │   ├── ingestion.py    문서 파싱 → 청킹 → 임베딩 → ChromaDB 저장
│   │   │   ├── embedder.py     글자를 숫자(벡터)로 바꾸는 AI 모델 (e5-small)
│   │   │   ├── vectorstore.py  ChromaDB 연결 및 싱글톤 관리
│   │   │   ├── llm.py          Gemini 모델 연결 및 싱글톤 관리
│   │   │   └── rag_chain.py    검색 → 프롬프트 조립 → AI 답변 파이프라인
│   │   │
│   │   ├── db/                 ← DB 담당
│   │   │   ├── database.py     SQLAlchemy 엔진·세션 설정
│   │   │   └── models.py       ORM 테이블 정의 (Document, ChatSession, ChatMessage)
│   │   │
│   │   └── schemas/            ← 요청·응답 데이터 형식 검사 (Pydantic)
│   │       ├── document.py
│   │       └── chat.py
│   │
│   ├── tests/
│   │   └── test_health.py      헬스체크 엔드포인트 테스트
│   │
│   ├── data/                   ← 런타임 데이터 (gitignore됨)
│   │   ├── sqlite/app.db       SQLite DB 파일
│   │   └── chroma/             ChromaDB 벡터 파일들
│   │
│   ├── requirements.txt        파이썬 의존성 목록
│   └── .env                    비밀키 (gitignore됨, .env.example 참고)
│
├── .github/workflows/
│   ├── ci.yml                  ← main 푸시 시 자동 테스트 (pytest)
│   └── fly-deploy.yml          ← main 푸시 시 자동 배포 (Fly.io)
│
├── Dockerfile                  ← 컨테이너 빌드 레시피 (프론트+백엔드 하나로)
├── docker-compose.yml          ← 로컬 도커 실행 설정
├── fly.toml                    ← Fly.io 배포 설정 (메모리, 볼륨 등)
└── README.md
```

---

## 4. 백엔드 레이어 구조 (핵심)

코드는 **역할별로 4개 층**으로 나뉩니다. 식당에 비유하면:

```
api/        →  웨이터    : 손님 주문 받아서 주방에 전달
core/       →  요리사    : 실제 요리 (검색, AI 호출, 답변 생성)
db/         →  창고 관리 : 재료(데이터) 꺼내고 저장
schemas/    →  주문서 양식: "주문은 이 형식으로만" 검사
```

**규칙**: 각 층은 바로 아래 층하고만 대화합니다. 웨이터가 직접 창고에 가거나
요리하지 않는 것처럼, `api/`는 비즈니스 로직을 직접 짜지 않고 `core/`에 넘깁니다.
이렇게 나눠야 코드를 고치기 쉽고, 테스트하기 쉽습니다.

---

## 5. 데이터가 흐르는 두 가지 시나리오

### 시나리오 A: 문서를 올릴 때

```
사용자 → PDF 업로드
    ↓
api/documents.py  : 파일 형식 검사 (PDF/MD/TXT만 허용)
    ↓               SQLite에 "처리 중" 상태로 Document 행 생성
core/ingestion.py : PDF에서 텍스트 추출
    ↓               500자씩 잘게 쪼갬 (chunk), 50자 겹침 (overlap)
core/embedder.py  : 각 조각을 384차원 숫자 배열(벡터)로 변환
    ↓               (모델: intfloat/multilingual-e5-small, 로컬 실행)
core/vectorstore  : ChromaDB에 벡터 + 메타데이터(파일명, document_id) 저장
    ↓
SQLite            : Document 상태를 "ready"로, chunk_count 기록
```

> **왜 쪼개나?** 문서 전체(수백 페이지)를 AI에게 주면 너무 길고 비쌉니다.
> 질문과 관련 있는 조각만 골라서 주려고 미리 작게 잘라둡니다.

> **벡터란?** "안녕하세요"라는 문장을 `[0.12, -0.88, 0.34, ...]` 같은 숫자 배열로
> 변환한 것입니다. 의미가 비슷한 문장은 숫자도 비슷하게 나옵니다.
> 그래서 "질문과 가장 비슷한 조각"을 빠르게 찾을 수 있습니다.

---

### 시나리오 B: 질문할 때

```
사용자 → 질문 입력
    ↓
api/chat.py       : 세션 생성 또는 기존 세션 연결
    ↓               SQLite에 사용자 메시지 저장
core/rag_chain.py :
    │
    ├── [R] Retrieval  질문을 벡터로 변환 → ChromaDB에서 가장 비슷한 조각 4개 검색
    │
    ├── [A] Augmented  "다음 문서를 참고해서 답하세요:\n{조각4개}\n\n질문: {질문}" 조립
    │
    └── [G] Generation Gemini에게 프롬프트 전달 → 답변 생성 (한 글자씩 스트리밍)
    ↓
SSE 이벤트 순서:
    1. session_id  → 세션 ID 전달
    2. token       → 답변 글자씩 전달 (여러 번 반복)
    3. sources     → 참고한 문서 조각 출처 전달
    4. done        → 완료 신호
    ↓
SQLite            : 어시스턴트 메시지 + 출처 저장
```

---

## 6. 저장소 2개 — 왜 나뉘어 있나

| | SQLite | ChromaDB |
|---|---|---|
| **저장하는 것** | 문서 목록, 대화 기록, 세션 | 문서 조각의 벡터(숫자 배열) |
| **잘하는 것** | 정형 데이터 조회, 관계형 쿼리 | 유사도 검색 ("이것과 비슷한 것 찾아줘") |
| **실체** | `data/sqlite/app.db` 파일 1개 | `data/chroma/` 폴더 |
| **설치 필요** | 없음 (Python 내장) | 없음 (`pip install chromadb`) |

---

## 7. 배포 구조

```
GitHub main 브랜치에 푸시
    ↓
GitHub Actions ci.yml      → pytest 자동 실행 (실패 시 배포 안 됨)
    ↓ (테스트 통과)
GitHub Actions fly-deploy  → Fly.io에 Docker 이미지 빌드 + 배포
    ↓
Fly.io 컨테이너 (도쿄 리전, 2GB RAM)
    ├── FastAPI 서버 (포트 8000)
    ├── /static/           Vue 빌드 결과물 (정적 파일)
    └── /app/data/ 볼륨    SQLite + ChromaDB (재시작해도 유지)
```

**단일 컨테이너 배포**: Vue 프론트엔드를 빌드해서 FastAPI가 정적 파일로 서빙합니다.
서버 하나만 띄우면 되니 배포·관리가 단순합니다.

---

## 8. 환경변수 설정 (`backend/.env`)

```
GOOGLE_API_KEY=...     ← Gemini AI 사용을 위한 Google API 키 (필수)
DATABASE_URL=...       ← SQLite 경로 (기본값 있음, 보통 안 건드림)
CHROMA_PERSIST_DIR=... ← ChromaDB 저장 경로 (기본값 있음, 보통 안 건드림)
```

`.env` 파일은 gitignore돼 있어서 GitHub에 올라가지 않습니다.
`.env.example`을 복사해서 사용합니다.

---

## 9. 로컬 개발 빠른 시작

```bash
# 가상환경 활성화 (backend/ 에서)
cd backend
source .venv/bin/activate   # Mac/Linux

# 서버 실행
uvicorn app.main:app --reload

# 테스트 실행
python3 -m pytest

# 프론트엔드 개발 서버 (별도 터미널, frontend/ 에서)
cd frontend
npm run dev
```

---

## 10. 핵심 용어 정리

| 용어 | 설명 |
|---|---|
| **RAG** | Retrieval-Augmented Generation. 문서 검색 결과를 AI에 넘겨 답변 생성 |
| **청킹(Chunking)** | 긴 문서를 일정 크기 조각으로 자르는 것 |
| **임베딩(Embedding)** | 텍스트를 숫자 벡터로 변환하는 것. 의미가 비슷하면 벡터도 비슷 |
| **벡터 DB** | 벡터끼리 유사도 검색이 빠른 DB. 여기선 ChromaDB |
| **SSE** | Server-Sent Events. 서버에서 클라이언트로 실시간 데이터를 흘려보내는 방식 |
| **LCEL** | LangChain Expression Language. `retriever \| prompt \| llm` 처럼 파이프라인을 연결하는 문법 |
| **싱글톤** | 인스턴스를 딱 하나만 만들고 재사용. `lru_cache`로 구현. 임베딩 모델·LLM처럼 무거운 것에 씀 |
| **ORM** | Object Relational Mapper. 파이썬 클래스로 DB 테이블을 다루는 방식. 여기선 SQLAlchemy |
