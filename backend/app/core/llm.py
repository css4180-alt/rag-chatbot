from functools import lru_cache

from langchain_aws import ChatBedrockConverse

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatBedrockConverse:
    """AWS Bedrock 기반 LLM(Claude).

    자격증명은 boto3가 환경변수 또는 EC2 IAM 역할에서 자동으로 가져온다.
    Converse API를 사용해 모델 종류에 상관없이 일관된 인터페이스로 호출한다.
    """
    return ChatBedrockConverse(
        model=settings.bedrock_llm_model_id,
        region_name=settings.aws_region,
        temperature=0.3,
        max_tokens=2048,
    )
