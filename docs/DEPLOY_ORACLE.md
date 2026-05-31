# Oracle Cloud (Always Free ARM) 배포 가이드

Fly.io의 콜드 스타트(절전 후 첫 응답 ~3분)를 없애기 위해, **Oracle Cloud
Always Free** ARM 인스턴스에 상시 가동으로 배포한다. ARM Ampere 인스턴스는
**4 vCPU / 24GB RAM 까지 영구 무료**라 이 앱을 항상 띄워둬도 비용이 0이다.

도메인/HTTPS는 **DuckDNS 무료 서브도메인 + Caddy 자동 인증서**로 처리한다.

---

## 0. 준비물

- Oracle Cloud 계정 (가입 시 해외결제 가능 신용카드 필요 — 과금되진 않음)
- GitHub에 푸시된 이 저장소
- Google AI(Gemini) API 키

---

## 1. Oracle VM 인스턴스 생성 (콘솔에서 직접)

1. https://cloud.oracle.com 로그인 → **Compute → Instances → Create instance**
2. **Image and shape** 변경:
   - Image: **Canonical Ubuntu 22.04** (또는 24.04)
   - Shape: **Ampere → VM.Standard.A1.Flex**, OCPU **2**, Memory **12GB**
     (4 OCPU / 24GB 까지 무료지만 2/12 면 충분하고 용량 확보가 더 쉽다)
   - > "Out of capacity" 가 뜨면 가용성 도메인(AD-1/2/3)을 바꿔가며 재시도하거나
     > 다른 리전을 선택한다. ARM 무료 용량은 인기가 많아 시간대를 바꿔 재시도하면 잘 잡힌다.
3. **SSH keys**: "Generate a key pair for me" → **private key 다운로드** (예: `oracle.key`).
   로컬에서 `chmod 600 oracle.key`.
4. **Create** → 인스턴스의 **Public IP** 를 메모한다 (예: `132.x.x.x`).

### 1-1. 방화벽(포트 개방) — 두 군데 모두 열어야 함

**(a) Oracle 보안 목록(Security List / NSG)**
- 인스턴스 → 서브넷 → Default Security List → **Add Ingress Rules**
- 다음 두 규칙 추가 (Source CIDR `0.0.0.0/0`):
  - TCP **80**
  - TCP **443**

**(b) Ubuntu 내부 방화벽** — SSH 접속 후(2단계) 실행:
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```
> Oracle Ubuntu 이미지는 기본 iptables 가 80/443 을 막아둔다. 위 두 줄을 빼먹으면
> 도메인 인증서 발급이 실패하니 반드시 실행한다.

---

## 2. DuckDNS 도메인 만들기

1. https://www.duckdns.org 접속 → GitHub/Google 등으로 로그인
2. 원하는 서브도메인 입력 (예: `myrag`) → **add domain** → `myrag.duckdns.org` 생성
3. 그 도메인의 **current ip** 칸에 1단계의 **VM Public IP** 입력 → **update ip**
4. 토큰(페이지 상단)은 따로 보관(나중에 IP가 바뀌면 갱신용, 고정 IP면 거의 불필요)

확인: 로컬에서 `nslookup myrag.duckdns.org` → VM IP가 나오면 OK.

---

## 3. VM 접속 & Docker 설치

```bash
ssh -i oracle.key ubuntu@<VM_PUBLIC_IP>

# Docker + compose 플러그인 설치
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
# 그룹 반영을 위해 일단 로그아웃 후 재접속
exit
ssh -i oracle.key ubuntu@<VM_PUBLIC_IP>
docker --version && docker compose version   # 확인
```

---

## 4. 코드 받기 & 환경변수 설정

```bash
git clone https://github.com/css4180-alt/rag-chatbot.git
cd rag-chatbot

# 백엔드 .env 작성 (.env.example 복사 후 키 입력)
cp backend/.env.example backend/.env
nano backend/.env     # GOOGLE_API_KEY=... 채우기 (나머지는 기본값 그대로)
```

`.env` 예시:
```
GOOGLE_API_KEY=실제-Gemini-키
DATABASE_URL=sqlite:///./data/sqlite/app.db
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
```

---

## 5. 빌드 & 기동

```bash
cd deploy
SITE_ADDRESS=myrag.duckdns.org docker compose -f docker-compose.prod.yml up -d --build
```

- 최초 빌드는 ARM에서 torch/임베딩 모델 다운로드까지 포함해 **5~15분** 걸린다(24GB RAM이라 여유).
- 진행/로그 확인:
  ```bash
  docker compose -f docker-compose.prod.yml logs -f
  ```
- Caddy 가 자동으로 Let's Encrypt 인증서를 발급한다(80포트가 열려 있어야 함).

확인:
```bash
curl -s https://myrag.duckdns.org/health    # {"status":"ok"} 류 응답
```
브라우저에서 `https://myrag.duckdns.org` 접속 → 콜드 스타트 없이 즉시 동작.

---

## 6. 운영 명령어

```bash
cd ~/rag-chatbot/deploy
# 상태
docker compose -f docker-compose.prod.yml ps
# 재시작
docker compose -f docker-compose.prod.yml restart
# 코드 업데이트 후 재배포
cd ~/rag-chatbot && git pull && cd deploy \
  && SITE_ADDRESS=myrag.duckdns.org docker compose -f docker-compose.prod.yml up -d --build
# 중지
docker compose -f docker-compose.prod.yml down
```

데이터(SQLite/Chroma)는 `app_data` 도커 볼륨에 보존되므로 재빌드해도 유지된다.

---

## 7. (선택) IP가 바뀔 때 DuckDNS 자동 갱신

Oracle 무료 VM은 보통 고정 공인 IP라 불필요하지만, 갱신을 자동화하려면:
```bash
# crontab -e 에 추가 (TOKEN/도메인 교체)
*/5 * * * * curl -s "https://www.duckdns.org/update?domains=myrag&token=<TOKEN>&ip=" >/dev/null 2>&1
```

---

## 트러블슈팅

| 증상 | 원인/해결 |
|---|---|
| 인증서 발급 실패 / 443 접속 불가 | Oracle 보안목록 **또는** Ubuntu iptables 에서 80/443 미개방. 1-1 단계 재확인 |
| `SITE_ADDRESS ... 를 지정하세요` 에러 | compose 실행 시 `SITE_ADDRESS=...` 를 앞에 붙였는지 확인 |
| 빌드 중 OOM | OCPU/메모리를 2/12 이상으로. (1GB짜리 마이크로 인스턴스에선 불가) |
| 도메인이 VM IP로 안 풀림 | DuckDNS current ip 갱신 확인, 전파까지 1~2분 대기 |
