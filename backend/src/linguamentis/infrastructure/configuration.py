"""Application configuration, loaded from environment variables / .env.

Per Architecture.md #23: models must be independently configurable per
capability so no code assumes a particular model is permanently responsible
for a task.
"""

from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://linguamentis:linguamentis@localhost:5438/linguamentis"

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str = ""
    openrouter_app_title: str = "LinguaMentis"

    # Per-capability model configuration (Architecture.md #23)
    ai_model_blue: str = "google/gemma-4-26b-a4b-it:free"
    ai_model_hat: str = "google/gemma-4-26b-a4b-it:free"
    ai_model_thinking_evaluator: str = "google/gemma-4-26b-a4b-it:free"
    ai_model_german_evaluator: str = "google/gemma-4-26b-a4b-it:free"
    ai_model_reflection: str = "google/gemma-4-26b-a4b-it:free"

    ai_request_timeout_seconds: float = 60.0
    ai_max_retries: int = 2

    # App
    app_env: str = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # V1 has no authentication (Architecture.md #28).
    default_user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")


@lru_cache
def get_settings() -> Settings:
    return Settings()
