from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    google_api_key: str = ""
    database_url: str = "sqlite:///./data/sqlite/app.db"
    chroma_persist_dir: str = "./data/chroma"
    embedding_model_name: str = "intfloat/multilingual-e5-small"


settings = Settings()
