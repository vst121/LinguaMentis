"""Application configuration, loaded from environment variables / .env.

Per Architecture.md #23: models must be independently configurable per
capability so no code assumes a particular model is permanently responsible
for a task.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use absolute path to the .env file in the backend root
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    database_url: str = "postgresql+asyncpg://linguamentis:linguamentis@postgres:5432/linguamentis"

    # Gemini
    gemini_api_key: str
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    # Per-capability model configuration (Architecture.md #23)
    ai_model_blue: str = "gemini-2.5-flash"
    ai_model_hat: str = "gemini-2.5-flash"
    ai_model_thinking_evaluator: str = "gemini-2.5-flash"
    ai_model_german_evaluator: str = "gemini-2.5-flash"
    ai_model_reflection: str = "gemini-2.5-flash"
    ai_model_transcription: str = ""
    ai_model_structured_fallback: str = "gemini-2.5-flash"

    ai_request_timeout_seconds: float = 120.0
    ai_max_retries: int = 2
    jev_enabled: bool = False
    jev_api_key: str = ""
    jev_base_url: str = ""
    jev_model: str = "typesafe/jev-1.13"
    jev_timeout_seconds: float = 10.0
    jev_auto_accept_confidence: float = 0.90
    jev_review_confidence: float = 0.70

    # App
    app_env: str = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # V1 has no authentication (Architecture.md #28).
    default_user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
