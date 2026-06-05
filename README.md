# RAG Chatbot

![CI](https://github.com/css4180-alt/rag-chatbot/actions/workflows/ci.yml/badge.svg)

PDF·Markdown 문서를 업로드하고, 자연어로 질문하면 문서 기반으로 답변하는 RAG 챗봇입니다.

**라이브 데모**: https://css4180-rag.duckdns.org

---

## 주요 기능

- PDF·Markdown 문서 업로드 및 자동 벡터 색인
- 자연어 질의응답 (한국어·영어 지원)
- 출처 문서 표시 (답변 근거 추적 가능)
- 대화 세션 관리 (생성·제목 수정·삭제)
- 스트리밍 응답 (SSE — 타이핑 효과)
- 패스코드 인증 및 계정별 일일 토큰 쿼터 (비용 보호)

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| LLM | AWS Bedrock — Claude Haiku 4.5 |
| 임베딩 | AWS Bedrock — Amazon Titan Text Embeddings V2 |
| 벡터 DB | ChromaDB (로컬 파일) |
| 메타데이터 DB | SQLite |
| RAG 프레임워크 | LangChain |
| 프론트엔드 | Vue 3 + Vite |
| 컨테이너 | Docker (멀티스테이지 단일 이미지) |
| 배포 | AWS EC2 + Caddy (자동 HTTPS) |
| CI/CD | GitHub Actions |

---

## 아키텍처

```
사용자 브라우저
     │ HTTPS
     ▼
 [Caddy]          — 리버스 프록시, Let's Encrypt 인증서 자동 발급
     │
     ▼
 [FastAPI]         — REST API + SSE 스트리밍
     ├── SQLite    — 대화 세션·메시지 메타데이터
     └── ChromaDB  — 문서 청크 벡터 저장소
           │
           ▼
     AWS Bedrock   — 임베딩(Titan) + 답변 생성(Claude Haiku 4.5)
```

문서 업로드 흐름:
1. PDF·Markdown 파싱 → 청크 분할
2. Titan Embeddings로 벡터화 → ChromaDB 저장

질의 흐름:
1. 질문 벡터화 → ChromaDB에서 유사 청크 검색 (코사인 유사도)
2. 관련 청크 + 대화 이력을 컨텍스트로 Claude에 전달
3. 스트리밍 응답 생성 → SSE로 프론트엔드에 전달

---

## 로컬 실행

### 사전 요구사항

- Python 3.11+
- Node.js 20+
- AWS 계정 및 Bedrock 모델 접근 권한

### 환경 설정

```bash
git clone https://github.com/css4180-alt/rag-chatbot.git
cd rag-chatbot

cp backend/.env.example backend/.env
# backend/.env 열어서 AWS 자격증명 및 설정 입력
```

### 백엔드 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 운영 배포 (Docker)

```bash
# 환경변수 설정
cp backend/.env.example backend/.env
# backend/.env 편집

# 빌드 및 실행 (프론트+백+Caddy 한 번에)
SITE_ADDRESS=your-domain.duckdns.org docker compose up -d --build
```

`docker-compose.yml`이 아래를 자동으로 처리합니다:
- 프론트엔드 빌드 (Vue → 정적 파일)
- FastAPI 서버 실행
- Caddy로 HTTPS 인증서 자동 발급 및 리버스 프록시 설정

---

## 테스트

```bash
cd backend
pytest
```

---

## 완료 항목

- [x] 프로젝트 구조 설계
- [x] 문서 업로드·청킹·벡터 색인
- [x] RAG 체인 (검색 + LLM 답변 생성)
- [x] SSE 스트리밍 응답
- [x] Vue 3 프론트엔드
- [x] 대화 세션 관리 (생성·제목 수정·삭제)
- [x] 패스코드 인증 + 일일 토큰 쿼터
- [x] AWS Bedrock LLM·임베딩 연동
- [x] Docker 단일 이미지 멀티스테이지 빌드
- [x] AWS EC2 + Caddy 배포
- [x] GitHub Actions CI/CD

---

## 라이선스

MIT — [LICENSE](LICENSE) 참고
