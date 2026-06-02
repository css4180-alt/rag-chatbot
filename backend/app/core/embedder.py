from functools import lru_cache

from langchain_aws import BedrockEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embedder() -> BedrockEmbeddings:
    """AWS Bedrock 기반 임베딩(Amazon Titan).

    로컬에서 모델을 적재하지 않으므로 메모리 사용량이 작고 콜드 스타트가 없다.
    자격증명은 boto3가 환경변수 또는 EC2 IAM 역할에서 자동으로 가져온다.
    """
    return BedrockEmbeddings(
        model_id=settings.bedrock_embedding_model_id,
        region_name=settings.aws_region,
    )
