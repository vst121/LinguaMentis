"""Speed tests for SQL query count budgets (N+1 prevention), schema caching, and API throughput."""

from __future__ import annotations

import asyncio
import time
from contextlib import contextmanager
from uuid import uuid4

import pytest
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy import event

from linguamentis.ai.gemini import _get_cached_schema
from linguamentis.domain.evaluations.evidence import Evidence
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest
from linguamentis.domain.mindquests.enums import LanguageLevel
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
)


@contextmanager
def count_sql_queries(db_engine):
    queries: list[str] = []

    def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.strip().upper().startswith("SELECT"):
            queries.append(statement)

    event.listen(db_engine.sync_engine, "before_cursor_execute", _before_cursor_execute)
    try:
        yield queries
    finally:
        event.remove(db_engine.sync_engine, "before_cursor_execute", _before_cursor_execute)


@pytest.mark.speed
@pytest.mark.asyncio
async def test_no_n_plus_one_queries_on_mindquest_list_and_learning_profile(
    async_client: AsyncClient, db_engine, db_session, test_settings
):
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    user_id = test_settings.default_user_id

    # Seed 20 completed MindQuests, each with 2 hats and 2 turns (= 40 turns, 80 evaluations)
    for i in range(20):
        mq = MindQuest(
            id=uuid4(),
            user_id=user_id,
            topic=f"Debattenthema Nummer {i}",
            target_level=LanguageLevel.B2,
        )
        mq.select_topic(mq.topic, (HatType.BLACK, HatType.WHITE))
        mq.begin()
        for hat in (HatType.BLACK, HatType.WHITE):
            r = mq.activate_hat(hat)
            t = r.add_turn(
                challenge_question="Frage?",
                challenge_instruction="Instruktion",
                difficulty=3,
            )
            t.record_response("Eine ausführliche Antwort auf Deutsch.")
            mq.complete_current_hat()
        mq.finish_all_hats()
        mq.start_final_evaluation()
        mq.complete()
        await mq_repo.save(mq)

        for r in mq.hat_rounds:
            for t in r.turns:
                await eval_repo.save_thinking(
                    ThinkingEvaluation(
                        id=uuid4(),
                        turn_id=t.id,
                        hat_adherence=85,
                        relevance=80,
                        reasoning=82,
                        depth=78,
                        specificity=80,
                        evidence=[Evidence("reasoning", "Obs", "Impact")],
                    )
                )
                await eval_repo.save_german(
                    GermanEvaluation(
                        id=uuid4(),
                        turn_id=t.id,
                        grammar=84,
                        vocabulary=80,
                        sentence_structure=82,
                        naturalness=79,
                        level_appropriateness=81,
                    )
                )
    await db_session.commit()

    # 1. GET /api/v1/mindquests must use selectinload (<= 3 SELECT queries total, NOT 20+ queries)
    with count_sql_queries(db_engine) as list_queries:
        t0 = time.perf_counter()
        resp_list = await async_client.get("/api/v1/mindquests?limit=25")
        list_elapsed = time.perf_counter() - t0

    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 20
    assert len(list_queries) <= 3, f"N+1 detected on /mindquests: {len(list_queries)} SELECTs"
    assert list_elapsed < 0.08, f"GET /mindquests too slow: {list_elapsed:.3f}s"

    # 2. GET /api/v1/users/{id}/learning-profile must use bulk queries (<= 4 SELECTs total)
    with count_sql_queries(db_engine) as profile_queries:
        t0 = time.perf_counter()
        resp_prof = await async_client.get(f"/api/v1/users/{user_id}/learning-profile")
        prof_elapsed = time.perf_counter() - t0

    assert resp_prof.status_code == 200
    assert resp_prof.json()["mindquests_completed"] == 20
    assert len(profile_queries) <= 4, (
        f"N+1 detected on /learning-profile: {len(profile_queries)} SELECTs"
    )
    assert prof_elapsed < 0.08, f"GET /learning-profile too slow: {prof_elapsed:.3f}s"


@pytest.mark.speed
@pytest.mark.asyncio
async def test_concurrent_api_requests_and_schema_cache_speed(async_client: AsyncClient):
    class ComplexSchema(BaseModel):
        a: str
        b: int
        c: list[str]
        d: dict[str, int]

    # 1,000 schema lookups must take < 10ms thanks to _SCHEMA_CACHE
    t0 = time.perf_counter()
    for _ in range(1000):
        _get_cached_schema(ComplexSchema)
    schema_elapsed = time.perf_counter() - t0
    assert schema_elapsed < 0.015, f"Schema cache lookup too slow: {schema_elapsed:.4f}s"

    # 20 concurrent HTTP GET requests must complete within 150ms
    t1 = time.perf_counter()
    responses = await asyncio.gather(
        *[async_client.get("/api/v1/mindquests") for _ in range(10)],
        *[async_client.get("/health") for _ in range(10)],
    )
    burst_elapsed = time.perf_counter() - t1
    assert all(r.status_code == 200 for r in responses)
    assert burst_elapsed < 0.20, f"Concurrent burst of 20 requests took {burst_elapsed:.3f}s"
