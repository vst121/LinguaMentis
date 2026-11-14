"""Speed tests verifying speculative prefetching hides LLM latency on /start and /advance."""

from __future__ import annotations

import asyncio
import time
from uuid import uuid4

import pytest

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.application.turns.service import TurnService
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.enums import LanguageLevel
from linguamentis.domain.users.entities import User
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserActivityRepository,
    SQLAlchemyUserRepository,
)
from tests.conftest import FakeLLMClient


@pytest.mark.speed
@pytest.mark.asyncio
async def test_speculative_prefetch_eliminates_llm_wait_on_start_and_advance(
    test_settings, db_session
):
    llm_delay = 0.16
    slow_client = FakeLLMClient(simulated_delay_seconds=llm_delay)
    gateway = AIGateway(client=slow_client, settings=test_settings)  # type: ignore[arg-type]
    registry = AgentRegistry(gateway=gateway)
    prefetch_cache = ChallengePrefetchCache()

    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)

    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Prefetch Speed Tester"))

    eval_service = EvaluationService(
        gateway=gateway, evaluation_repo=eval_repo, activity_repo=act_repo
    )
    turn_service = TurnService(
        mindquest_repo=mq_repo,
        evaluation_service=eval_service,
        agent_registry=registry,
        activity_repo=act_repo,
        prefetch_cache=prefetch_cache,
    )
    mq_service = MindQuestService(
        mindquest_repo=mq_repo,
        evaluation_repo=eval_repo,
        turn_service=turn_service,
        agent_registry=registry,
        activity_repo=act_repo,
        prefetch_cache=prefetch_cache,
    )

    # 1. Create MindQuest -> schedules background prefetch for Hat 1 (WHITE)
    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="Kernfusion als Energiequelle",
        target_level=LanguageLevel.C1,
    )
    mq.planned_hats = (HatType.WHITE, HatType.YELLOW)
    await mq_repo.save(mq)

    # Simulate user navigation / reading time (180ms > 160ms LLM delay)
    await asyncio.sleep(llm_delay + 0.03)

    # 2. start_mindquest must consume prefetched challenge in < 40ms (instead of >= 160ms)
    t_start = time.perf_counter()
    await mq_service.start_mindquest(mq.id)
    start_elapsed = time.perf_counter() - t_start
    assert start_elapsed < 0.05, (
        f"start_mindquest did not use prefetch cache: took {start_elapsed:.3f}s"
    )

    # 3. Submit response on Hat 1 -> schedules prefetch for Hat 2 (YELLOW) while feedback runs
    await mq_service.submit_response(
        mq.id, "Die enormen Investitionskosten binden Kapital über Jahrzehnte."
    )
    # Wait brief moment for background prefetch if not already done during generate_feedback
    await asyncio.sleep(0.04)

    # 4. advance_mindquest to Hat 2 (YELLOW) must consume prefetched challenge in < 40ms
    t_adv1 = time.perf_counter()
    adv1 = await mq_service.advance_mindquest(mq.id)
    adv1_elapsed = time.perf_counter() - t_adv1
    assert adv1.next_hat == HatType.YELLOW
    assert adv1_elapsed < 0.05, (
        f"advance_mindquest (next hat) did not use prefetch: took {adv1_elapsed:.3f}s"
    )

    # 5. Submit response on final Hat 2 (YELLOW) -> schedules prefetch for FinalReflection
    await mq_service.submit_response(
        mq.id, "Nahezu unbegrenzte grundlastfähige Energie ohne CO2-Ausstoß."
    )
    await asyncio.sleep(0.04)

    # 6. advance_mindquest to FinalReflection must consume prefetched reflection in < 50ms
    t_adv2 = time.perf_counter()
    adv2 = await mq_service.advance_mindquest(mq.id)
    adv2_elapsed = time.perf_counter() - t_adv2
    assert adv2.is_completed is True
    assert adv2.final_reflection is not None
    assert adv2_elapsed < 0.05, (
        f"advance_mindquest (reflection) did not use prefetch: took {adv2_elapsed:.3f}s"
    )
