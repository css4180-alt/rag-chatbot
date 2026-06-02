# AWS 배포 가이드 (EC2 + Bedrock)

LLM·임베딩을 **AWS Bedrock**(Claude + Titan)으로 호출하고, 앱은 **EC2 t3.micro**
(프리티어, 12개월 무료)에 Docker로 상시 가동한다. 로컬 ML 모델이 없어 메모리가
가볍고 콜드 스타트가 없다.

도메인/HTTPS는 **DuckDNS 무료 서브도메인 + Caddy 자동 인증서**로 처리한다.

> 비용 요약: EC2 t3.micro 12개월 무료(이후 ~$8/mo), Bedrock는 사용량 과금이지만
> 데모 수준이면 월 ~$1 수준. EBS 30GB·트래픽도 프리티어 한도 내.

---

## 1. Bedrock 모델 사용 가능 상태 확인 (먼저!)

> **변경 사항**: 예전의 **Model access**(모델 액세스) 페이지는 폐지되었다.
> 이제 서버리스 파운데이션 모델은 **해당 리전에서 첫 호출 시 자동으로 활성화**된다.
> 따라서 모델을 미리 일일이 켤 필요가 없다. 단, Anthropic(Claude)은 **처음 쓰는
> 계정**일 경우 한 번 **사용 사례(use case) 정보 제출**을 요구할 수 있다.

1. AWS 콘솔 우상단 리전을 **N. Virginia (us-east-1)** 로 변경
2. **Bedrock** 검색 → 좌측 **Chat / Text Playground**(또는 **Model catalog**) 이동
3. **Claude 3 Haiku** 선택:
   - 처음이라면 **사용 사례 정보 제출** 폼이 뜰 수 있다 → 회사명/용도 등 간단히 입력
     (예: 개인 RAG 데모) 후 제출. 보통 즉시 승인된다.
   - Playground에서 짧은 문장을 한 번 보내 응답이 오면 호출 가능 상태다.
4. **Titan Text Embeddings V2** 도 Playground/카탈로그에서 한 번 호출되는지 확인
   (임베딩은 보통 사용 사례 제출 없이 바로 호출된다).

> 다른 리전을 쓰려면 `.env`의 `AWS_REGION`을 그 리전으로 맞추고, 그 리전에서
> 같은 방식으로 첫 호출만 확인하면 된다.
> Claude 3.5 Haiku 를 쓰려면 추론 프로파일 ID(`us.anthropic.claude-3-5-haiku-...`)가
> 필요할 수 있다. 가장 단순한 조합은 위의 Claude 3 Haiku(온디맨드)다.

---

## 2. EC2 인스턴스 생성

1. **EC2 → Launch instance**
2. **Name**: `rag-chatbot`
3. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance type**: **t3.micro** (또는 t2.micro) — *Free tier eligible* 확인
5. **Key pair**: 새로 생성 → `.pem` 다운로드 → `chmod 400 rag-key.pem`
6. **Network settings → Edit → Security group** 인바운드 규칙:
   - SSH (22) — My IP
   - HTTP (80) — Anywhere `0.0.0.0/0`
   - HTTPS (443) — Anywhere `0.0.0.0/0`
7. **Storage**: 8~30GB (프리티어 30GB 한도 내)
8. **Launch instance** → 인스턴스의 **Public IPv4 address** 메모

---

## 3. EC2에 Bedrock 호출 권한 부여 (IAM 역할 — 키 없이)

키를 서버에 두지 않는 안전한 방법:

1. **IAM → Roles → Create role**
2. Trusted entity: **AWS service → EC2**
3. 권한: 인라인 정책으로 아래 추가 (또는 `AmazonBedrockFullAccess`)
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
       "Resource": "*"
     }]
   }
   ```
4. Role 이름: `rag-bedrock-role` → 생성
5. **EC2 → 인스턴스 선택 → Actions → Security → Modify IAM role** → `rag-bedrock-role` 연결

> 이렇게 하면 `.env`에 AWS 키를 넣을 필요가 없다(boto3가 인스턴스 역할을 자동 사용).
> 로컬 개발에서만 `.env`에 IAM 사용자 액세스 키를 넣는다.

---

## 4. DuckDNS 도메인

1. https://www.duckdns.org 로그인 → 서브도메인 추가 (예: `myrag`)
2. **current ip** 칸에 EC2 Public IP 입력 → **update ip**
3. 확인: `nslookup myrag.duckdns.org` → EC2 IP

---

## 5. EC2 접속 & Docker 설치

```bash
ssh -i rag-key.pem ubuntu@<EC2_PUBLIC_IP>

sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# t3.micro 는 RAM 1GB 라 빌드 중 OOM 방지를 위해 swap 2GB 추가(권장)
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile \
  && sudo mkswap /swapfile && sudo swapon /swapfile \
  && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

exit
ssh -i rag-key.pem ubuntu@<EC2_PUBLIC_IP>   # 그룹 반영 위해 재접속
docker --version && docker compose version
```

---

## 6. 코드 받기 & 환경변수

```bash
git clone https://github.com/css4180-alt/rag-chatbot.git
cd rag-chatbot
cp backend/.env.example backend/.env
nano backend/.env
```

IAM 역할(3단계)을 연결했다면 `.env`는 아래만 있으면 된다 (키 줄은 지운다):
```
AWS_REGION=us-east-1
BEDROCK_LLM_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
DATABASE_URL=sqlite:///./data/sqlite/app.db
CHROMA_PERSIST_DIR=./data/chroma
```

---

## 7. 빌드 & 기동

```bash
cd deploy
SITE_ADDRESS=myrag.duckdns.org docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f
```

- torch가 빠져 이미지 빌드가 이전보다 빠르고 가볍다.
- Caddy가 Let's Encrypt 인증서를 자동 발급(80포트 개방 필요).

확인:
```bash
curl -s https://myrag.duckdns.org/health      # {"status":"ok"}
```
브라우저에서 `https://myrag.duckdns.org` → 즉시 응답.

---

## 8. 문서 업로드

임베딩 모델이 바뀌어(차원 변경) 기존 벡터는 호환되지 않는다. **새 서버라
데이터가 비어 있으니** 화면에서 문서를 새로 업로드하면 Titan 임베딩으로 색인된다.

---

## 운영 / 업데이트

```bash
cd ~/rag-chatbot && git pull && cd deploy \
  && SITE_ADDRESS=myrag.duckdns.org docker compose -f docker-compose.prod.yml up -d --build
```

---

## 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| `AccessDeniedException` / `not authorized to perform bedrock:InvokeModel` | IAM 역할 미연결 또는 정책 누락. 3단계 확인 |
| `Could not load credentials` | 로컬이면 `.env`에 키, EC2면 IAM 역할 연결 확인 |
| `model ... on-demand throughput isn't supported` | 그 모델은 추론 프로파일 필요. Claude 3 Haiku(온디맨드)로 쓰거나 `us.` 프로파일 ID 사용 |
| `ValidationException ... model identifier is invalid` | 리전에 해당 모델 미제공. 1단계 리전/모델 액세스 확인 |
| 인증서 발급 실패 | 보안그룹 80/443 인바운드 개방 확인, DNS 전파 대기 |
| 빌드 중 메모리 부족 | t3.micro 1GB라면 swap 1~2GB 추가 후 재시도 |
