"""Isolated E2E test backend server using SQLite and deterministic FakeLLMClient."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import UUID

DB_FILE = Path("/tmp/linguamentis_e2e_test.db")
if DB_FILE.exists():
    DB_FILE.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_FILE}"
os.environ["GEMINI_API_KEY"] = "fake-e2e-key"

import uvicorn  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from linguamentis.ai.gateway import AIGateway  # noqa: E402
from linguamentis.api.dependencies import get_ai_gateway  # noqa: E402
from linguamentis.infrastructure.configuration import (  # noqa: E402
    Settings,
    get_settings,
)
from linguamentis.infrastructure.database.models import Base  # noqa: E402
from linguamentis.infrastructure.database.repositories import (  # noqa: E402
    SQLAlchemyUserRepository,
)
from linguamentis.infrastructure.database.session import get_db_session  # noqa: E402
from linguamentis.main import app  # noqa: E402
from tests.conftest import FakeLLMClient  # noqa: E402

e2e_settings = Settings(
    database_url=f"sqlite+aiosqlite:///{DB_FILE}",
    gemini_api_key="fake-e2e-key",
    default_user_id=UUID("00000000-0000-0000-0000-000000000001"),
)

engine = create_async_engine(
    e2e_settings.database_url, connect_args={"check_same_thread": False}
)
session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
fake_gateway = AIGateway(client=FakeLLMClient(), settings=e2e_settings)  # type: ignore[arg-type]


async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db_session] = _override_get_db_session
app.dependency_overrides[get_settings] = lambda: e2e_settings
app.dependency_overrides[get_ai_gateway] = lambda: fake_gateway


async def _init_e2e_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        await user_repo.ensure_default_user(e2e_settings.default_user_id, "E2E Learner")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(_init_e2e_db())
    port = int(os.getenv("E2E_BACKEND_PORT", "8001"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

