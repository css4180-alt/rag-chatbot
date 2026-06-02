from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AWS Bedrock
    # 자격증명(AWS_ACCESS_KEY_ID/SECRET)은 boto3가 환경변수·IAM 역할에서 자동으로 읽는다.
    # EC2에 IAM 역할을 부여하면 키를 환경변수로 둘 필요가 없다.
    # us-east-1 은 Bedrock 모델 가용성이 가장 넓다. Claude 3 Haiku 는 추론
    # 프로파일 없이 온디맨드 호출이 가능해 설정이 가장 단순하다.
    aws_region: str = "us-east-1"
    bedrock_llm_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # 저장소
    database_url: str = "sqlite:///./data/sqlite/app.db"
    chroma_persist_dir: str = "./data/chroma"


settings = Settings()
