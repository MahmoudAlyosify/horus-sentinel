"""Centralized app configuration, loaded from environment / .env."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ARGUS_",
        extra="ignore",
    )

    app_env: str = "development"

    # Postgres (jobs, RoE records, audit log, normalized findings — section 4.2)
    database_url: str = "postgresql+asyncpg://argus:argus@localhost:5432/argus"

    # Redis (tool-result cache, rate budgets, task queue — wired from week 3)
    redis_url: str = "redis://localhost:6379/0"

    # HMAC key used to sign/verify RoE records (core/authorization.py).
    # MUST be overridden via ARGUS_ROE_SIGNING_KEY in any non-dev environment.
    roe_signing_key: str = "dev-only-insecure-signing-key-change-me"


settings = Settings()
