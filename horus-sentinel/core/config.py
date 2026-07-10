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

    # Job queue + workers (Phase 5.2). "memory" (default, in-process) or "redis" (full stack).
    queue_backend: str = "memory"
    queue_name: str = "horus:jobs"
    worker_enabled: bool = False  # start an in-process worker on API startup
    worker_poll_timeout: float = 5.0  # seconds a worker blocks waiting for a job

    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # Relational DB. Defaults to a local SQLite file so the platform runs with zero
    # infrastructure; set DATABASE_URL (e.g. the postgres_dsn) on the full stack.
    database_url: str = "sqlite:///./horus_sentinel.db"

    # HORUS Brain
    ollama_endpoint: str = "http://localhost:11434"
    horus_model_name: str = "horus-osint"
    llm_provider: str = "horus-selfhosted"

    # Passive threat-intel / OSINT API keys (all optional — tools degrade gracefully).
    shodan_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    virustotal_api_key: str = ""
    otx_api_key: str = ""
    abuseipdb_api_key: str = ""
    hibp_api_key: str = ""

    # Reasoning knobs
    ollama_timeout_s: float = 120.0
    ollama_temperature: float = 0.2

    # Deterministic risk-scoring weights (master plan Part 4.4). Must sum to 1.0.
    w_exposure: float = 0.30
    w_threat_context: float = 0.30
    w_reputation: float = 0.20
    w_criticality: float = 0.20

    # Geo-event corpus (GTD/GDELT-derived). Points at the real dataset on the full stack;
    # falls back to the bundled sample so the Geo-Event agent runs out of the box.
    geo_corpus_path: str = "data/geo_corpus.json"

    # RAG store (ATT&CK + geo corpus + findings). Persist dir for ChromaDB.
    chroma_persist_dir: str = "data/chroma"
    rag_top_k: int = 4
    # Retrieval backend: "keyword" (deterministic, zero-dep, default) or "chroma"
    # (semantic vector search — opt in on the full stack where ChromaDB is available).
    rag_backend: str = "keyword"

    # Reporting output directory.
    report_output_dir: str = "data/reports"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sqlalchemy_url(self) -> str:
        """The URL SQLAlchemy connects to. Honors DATABASE_URL; falls back to SQLite."""
        return self.database_url


settings = Settings()
