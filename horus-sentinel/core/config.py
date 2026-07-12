"""Central configuration, loaded from environment / .env."""

from __future__ import annotations

from pathlib import Path

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

    # Brain backend selection (Part 4.3 — the provider bridge, now pluggable).
    #   "hybrid"        → try HF online first, fall back to local Ollama (recommended).
    #   "hf_serverless" → HF Inference router (serverless) only.
    #   "hf_endpoint"   → a dedicated HF Inference Endpoint URL only.
    #   "ollama"        → self-hosted Ollama only (data never leaves the box).
    brain_backend: str = "hybrid"

    # Hugging Face online inference. The token is prompted on first run and saved to .env.
    hf_token: str = ""
    hf_model_id: str = "mahmoudalyosify/Horus-OSINT"
    # A dedicated Inference Endpoint URL (used when brain_backend includes hf_endpoint).
    hf_endpoint_url: str = ""
    hf_timeout_s: float = 120.0
    hf_max_new_tokens: int = 512

    # Report / narrative language. "ar" = Arabic (RTL), "en" = English.
    report_language: str = "ar"

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

    # ---- Active reconnaissance (authorized targets only) ----
    # These tools send traffic to the target and only ever run against in-scope, explicitly
    # authorized assets (enforced by the Authorization Engine). The knobs keep them polite.
    active_scan_ports: str = (  # comma-separated common ports for the TCP connect scan
        "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3306,3389,5432,5900,"
        "6379,8080,8443,8000,8888,9200,27017"
    )
    active_scan_timeout_s: float = 1.5  # per-port connect timeout
    active_scan_concurrency: int = 100  # max simultaneous connect attempts
    active_banner_bytes: int = 256  # bytes to read for a service banner
    active_dns_wordlist: str = (  # subdomain brute-force candidates (small, polite default)
        "www,mail,ftp,webmail,smtp,pop,ns1,ns2,dns,admin,portal,vpn,remote,api,dev,test,"
        "staging,stage,uat,git,gitlab,jenkins,jira,confluence,intranet,internal,app,apps,"
        "cloud,cdn,static,assets,img,files,download,shop,store,blog,news,support,help,docs,"
        "status,monitor,grafana,kibana,prometheus,db,database,sql,mysql,phpmyadmin,cpanel,"
        "webdisk,autodiscover,mx,mx1,mx2,smtp2,relay,gw,gateway,proxy,fw,firewall,router"
    )
    active_crawl_max_pages: int = 40  # crawler page budget
    active_crawl_max_depth: int = 2  # crawler link depth
    active_crawl_timeout_s: float = 10.0  # per-request timeout

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


_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def update_env(values: dict[str, str]) -> None:
    """Persist config values to the .env file AND the live ``settings`` object.

    Used by the first-run setup wizard so a token the user enters survives a restart.
    Keys are the UPPER_SNAKE env names (e.g. ``HF_TOKEN``); the matching lowercase
    attribute on ``settings`` is updated in place so the change takes effect immediately.
    """
    updates = {k: str(v) for k, v in values.items()}
    remaining = dict(updates)

    # Update existing keys in place, preserving comments/blank lines/order.
    lines: list[str] = []
    if _ENV_PATH.exists():
        for raw in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.partition("=")[0].strip()
                if key in remaining:
                    lines.append(f"{key}={remaining.pop(key)}")
                    continue
            lines.append(raw)
    # Append any brand-new keys at the end.
    lines.extend(f"{k}={v}" for k, v in remaining.items())
    _ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    for k, v in values.items():
        attr = k.lower()
        if hasattr(settings, attr):
            field = settings.model_fields.get(attr)
            annotation = field.annotation if field else str
            try:
                if annotation is bool:
                    coerced: object = str(v).lower() in {"1", "true", "yes", "on"}
                elif annotation in (int, float):
                    coerced = annotation(v)
                else:
                    coerced = v
                setattr(settings, attr, coerced)
            except (ValueError, TypeError):
                setattr(settings, attr, v)
