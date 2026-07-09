"""Central configuration, loaded from environment / .env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Values come from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Datastores
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "horus_sentinel"
    postgres_user: str = "horus"
    postgres_password: str = "horus_dev_pw"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "horus_dev_pw"

    redis_url: str = "redis://localhost:6379/0"

    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # HORUS Brain
    ollama_endpoint: str = "http://localhost:11434"
    horus_model_name: str = "horus-osint"
    llm_provider: str = "horus-selfhosted"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
