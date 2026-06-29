from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Cortex API"
    app_env: Literal["local", "test", "staging", "production"] = "local"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = Field(
        default="postgresql+asyncpg://cortex:cortex@postgres:5432/cortex",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias="REDIS_URL")
    qdrant_url: str = Field(default="http://qdrant:6333", validation_alias="QDRANT_URL")
    ollama_url: str = Field(
        default="http://host.docker.internal:11434",
        validation_alias="OLLAMA_URL",
    )

    embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = 768
    qdrant_collection: str = "cortex_chunks"
    llm_model: str = "qwen2.5-coder:7b"
    worker_concurrency: int = 2
    github_token: str | None = None
    github_api_url: str = "https://api.github.com"
    github_raw_url: str = "https://raw.githubusercontent.com"
    github_fetch_timeout_seconds: float = 15.0
    github_max_files_per_repo: int = 500

    readiness_timeout_seconds: float = 2.0

    @property
    def asyncpg_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
