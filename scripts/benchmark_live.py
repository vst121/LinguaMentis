#!/usr/bin/env python3
"""Live & Simulated Speed Benchmark for LinguaMentis in the Dev Container."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from uuid import uuid4

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR / "src"))
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from linguamentis.agents.registry import AgentRegistry  # noqa: E402
from linguamentis.ai.gateway import AIGateway  # noqa: E402
from linguamentis.ai.gemini import GeminiClient  # noqa: E402
from linguamentis.application.evaluation.service import EvaluationService  # noqa: E402
from linguamentis.application.learning.service import LearningService  # noqa: E402
from linguamentis.application.mindquests.prefetch import (  # noqa: E402
    ChallengePrefetchCache,
)
from linguamentis.application.mindquests.service import MindQuestService  # noqa: E402
from linguamentis.application.turns.service import TurnService  # noqa: E402
from linguamentis.domain.hats.types import HatType  # noqa: E402
from linguamentis.domain.mindquests.enums import LanguageLevel  # noqa: E402
from linguamentis.domain.users.entities import User  # noqa: E402
from linguamentis.infrastructure.configuration import get_settings  # noqa: E402
from linguamentis.infrastructure.database.models import Base  # noqa: E402
from linguamentis.infrastructure.database.repositories import (  # noqa: E402
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserActivityRepository,
    SQLAlchemyUserRepository,
)
from tests.conftest import FakeLLMClient  # noqa: E402


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000


async def run_benchmark() -> None:
    settings = get_settings()
    print("=" * 68)
    print("LinguaMentis Speed & Latency Benchmark")
    print("=" * 68)

    engine = create_async_engine(settings.database_url)
    try:
        t0 = time.perf_counter()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
        print(f"  [DB] PostgreSQL (postgres:5432) ping:         {_ms(t0):7.1f} ms")
    except Exception:
        await engine.dispose()
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        t0 = time.perf_counter()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(f"  [DB] SQLite (in-memory) init:                 {_ms(t0):7.1f} ms")

    has_key = bool(
        settings.gemini_api_key
        and settings.gemini_api_key != "your-gemini-api-key"
        and not settings.gemini_api_key.startswith("fake")
    )
    if has_key and "--live-ai" in sys.argv:
        llm = GeminiClient(settings)
        t_w = time.perf_counter()
        await llm.warmup()
        print(f"  [AI] Live Gemini TLS warmup:                  {_ms(t_w):7.1f} ms")
    else:
        llm = FakeLLMClient(simulated_delay_seconds=0.25)  # type: ignore[assignment]
        print("  [AI] Mode: Simulated LLM (250.0 ms per AI call)")

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        mq_repo = SQLAlchemyMindQuestRepository(session)
        eval_repo = SQLAlchemyEvaluationRepository(session)
        act_repo = SQLAlchemyUserActivityRepository(session)
        prefetch = ChallengePrefetchCache()
        gateway = AIGateway(client=llm, settings=settings)  # type: ignore[arg-type]
        registry = AgentRegistry(gateway=gateway)
        eval_srv = EvaluationService(gateway, eval_repo, act_repo)
        turn_srv = TurnService(mq_repo, eval_srv, registry, act_repo, prefetch)
        mq_srv = MindQuestService(
            mq_repo, eval_repo, turn_srv, registry, act_repo, prefetch
        )
        learning_srv = LearningService(mq_repo, eval_repo, act_repo)

        uid = uuid4()
        await user_repo.save(User(id=uid, display_name="Benchmark User"))

        t0 = time.perf_counter()
        mq = await mq_srv.create_mindquest(
            user_id=uid,
            topic="KI in der öffentlichen Verwaltung",
            target_level=LanguageLevel.B2,
        )
        mq.planned_hats = (HatType.WHITE,)
        await mq_repo.save(mq)
        print(f"  [1] create_mindquest (schedules prefetch):    {_ms(t0):7.1f} ms")

        await asyncio.sleep(0.28)
        t0 = time.perf_counter()
        await mq_srv.start_mindquest(mq.id)
        print(f"  [2] start_mindquest (warm prefetch hit):      {_ms(t0):7.1f} ms")

        t0 = time.perf_counter()
        await mq_srv.submit_response(mq.id, "Ein Risiko ist Kontrollverlust.")
        print(f"  [3] submit_response (parallel eval+feedback): {_ms(t0):7.1f} ms")

        await asyncio.sleep(0.28)
        t0 = time.perf_counter()
        await mq_srv.advance_mindquest(mq.id)
        print(f"  [4] advance_mindquest (warm reflection hit):  {_ms(t0):7.1f} ms")

        t0 = time.perf_counter()
        await learning_srv.get_user_learning_profile(uid)
        print(f"  [5] get_user_learning_profile (DB query):     {_ms(t0):7.1f} ms")

    if hasattr(llm, "aclose"):
        await llm.aclose()
    await engine.dispose()
    print("=" * 68)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
