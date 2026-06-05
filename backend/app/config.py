from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS Bedrock
    # 자격증명(AWS_ACCESS_KEY_ID/SECRET)은 boto3가 환경변수·IAM 역할에서 자동으로 읽는다.
    # EC2에 IAM 역할을 부여하면 키를 환경변수로 둘 필요가 없다.
    # us-east-1 은 Bedrock 모델 가용성이 가장 넓다. Claude Haiku 4.5 는 최신·저비용
    # 모델로, 크로스리전 추론 프로파일(us. 접두사)로 온디맨드 호출이 가능하다.
    aws_region: str = "us-east-1"
    bedrock_llm_model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # 저장소
    database_url: str = "sqlite:///./data/sqlite/app.db"
    chroma_persist_dir: str = "./data/chroma"
    # 업로드 원본 파일 보관 디렉터리. 다운로드·미리보기를 위해 원본을 유지한다.
    upload_dir: str = "./data/uploads"

    # --- 검색(retrieval) ---
    # retrieval_k: 후보로 가져올 최대 청크 수.
    # retrieval_score_threshold: 코사인 관련도 점수(0~1)가 이 값 미만인 청크는
    #   버린다. 질문과 무관한 문서가 출처/컨텍스트에 섞이는 것을 막는다.
    #   값이 높을수록 엄격(관련도 높은 것만), 낮을수록 관대.
    #   주의: 한 질문에 여러 주제를 섞으면 임베딩이 희석돼 관련도가 낮아진다.
    #   0.3 은 단일 주제엔 좋지만 복합 질문은 통째로 걸러버려, 0.2 로 완화한다.
    #   (실측: 무관 문서 ~0.05~0.10, 단일 주제 관련 ~0.7, 복합 질문 ~0.25~0.35)
    retrieval_k: int = 4
    retrieval_score_threshold: float = 0.2

    # --- 접근 제어 / 토큰 쿼터 (공개 데모 비용 보호) ---
    # ACCESS_CODES: "패스코드:계정,패스코드:계정" 형식. 비워두면 인증/쿼터가
    #   전부 비활성화되어(로컬 개발·테스트) 누구나 무제한으로 호출할 수 있다.
    # AUTH_SECRET: 로그인 토큰 서명용 비밀키. 운영에서는 반드시 임의 값으로 교체.
    # DAILY_TOKEN_LIMIT_PER_ACCOUNT: 계정 1개가 하루에 쓸 수 있는 LLM 토큰 상한.
    # SITE_DAILY_TOKEN_LIMIT: 모든 계정 합산 하루 토큰 상한(전체 비용 캡).
    # (날짜 경계는 UTC 자정 기준으로 매일 리셋된다.)
    access_codes: str = ""
    auth_secret: str = "dev-insecure-secret-change-me"
    daily_token_limit_per_account: int = 50_000
    site_daily_token_limit: int = 300_000
    token_ttl_hours: int = 24

    def parse_access_codes(self) -> dict[str, str]:
        """``access_codes`` 문자열을 {패스코드: 계정라벨} 사전으로 변환한다."""
        mapping: dict[str, str] = {}
        for pair in self.access_codes.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            code, label = pair.split(":", 1)
            code, label = code.strip(), label.strip()
            if code and label:
                mapping[code] = label
        return mapping

    @property
    def auth_enabled(self) -> bool:
        """접근 코드가 하나라도 설정돼 있으면 인증/쿼터를 적용한다."""
        return bool(self.parse_access_codes())


settings = Settings()
