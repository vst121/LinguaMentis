"""Speed tests verifying concurrent AI execution (asyncio.gather)."""

from __future__ import annotations

import asyncio
import time
from uuid import uuid4

import pytest

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.jev import JevDecision
from linguamentis.ai.models import Evidence, ThinkingEvaluationOutput
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.turns.service import TurnService
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest, Turn
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestMode
from linguamentis.domain.mindquests.value_objects import MindQuestContext
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
async def test_evaluate_dimensions_executes_thinking_german_and_jev_in_parallel(
    test_settings, db_session
):
    delay = 0.12
    slow_client = FakeLLMClient(simulated_delay_seconds=delay)
    gateway = AIGateway(client=slow_client, settings=test_settings)  # type: ignore[arg-type]

    class SlowJevVerifier:
        async def evaluate_hat_adherence(
            self, *, hat: str, challenge: str, response: str
        ) -> JevDecision:
            await asyncio.sleep(delay)
            return JevDecision("adherent", 0.96, {"adherent": 0.96})

    service = EvaluationService(
        gateway=gateway,
        evaluation_repo=SQLAlchemyEvaluationRepository(db_session),
        activity_repo=SQLAlchemyUserActivityRepository(db_session),
        decision_verifier=SlowJevVerifier(),
    )

    turn = Turn(
        id=uuid4(),
        hat_round_id=uuid4(),
        turn_number=1,
        hat=HatType.BLACK,
        challenge_question="Welche Risiken?",
        challenge_instruction="Black Hat",
        difficulty=3,
    )
    context = MindQuestContext(
        mindquest_id=uuid4(),
        topic="KI im Gesundheitswesen",
        target_level=LanguageLevel.B2.value,
        current_hat=HatType.BLACK,
        current_turn_number=1,
    )

    t0 = time.perf_counter()
    await service.evaluate_dimensions(
        turn=turn, context=context, user_response="Ein Risiko ist Datenmissbrauch."
    )
    elapsed = time.perf_counter() - t0

    # Sequential execution would take >= 3 * 0.12s = 0.36s.
    # Parallel asyncio.gather must complete in roughly 1 * delay (< 0.23s).
    assert elapsed < delay * 1.9, (
        f"Expected parallel execution (< {delay * 1.9:.2f}s), took {elapsed:.3f}s"
    )


@pytest.mark.speed
@pytest.mark.asyncio
async def test_turn_service_runs_feedback_and_follow_up_challenge_in_parallel(
    test_settings, db_session
):
    delay = 0.12
    slow_client = FakeLLMClient(simulated_delay_seconds=delay)
    slow_client.queue_response(
        ThinkingEvaluationOutput,
        ThinkingEvaluationOutput(
            hat_adherence=50,
            relevance=55,
            reasoning=50,
            depth=50,
            specificity=50,
            evidence=[Evidence(dimension="depth", observation="Brief", impact="Low")],
            strengths=[],
            weaknesses=["Too brief"],
            recommendations=["Expand"],
        ),
    )
    gateway = AIGateway(client=slow_client, settings=test_settings)  # type: ignore[arg-type]
    registry = AgentRegistry(gateway=gateway)

    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)

    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Speed Learner"))

    mq = MindQuest(
        id=uuid4(),
        user_id=user_id,
        topic="Speed Test",
        target_level=LanguageLevel.C1,
        mode=MindQuestMode.ARGUE,
    )
    mq.select_topic("Speed Test", (HatType.BLACK,))
    mq.begin()
    r = mq.activate_hat(HatType.BLACK)
    r.add_turn(challenge_question="Risiken?", challenge_instruction="Black Hat", difficulty=2)
    await mq_repo.save(mq)

    eval_service = EvaluationService(
        gateway=gateway, evaluation_repo=eval_repo, activity_repo=act_repo
    )
    turn_service = TurnService(
        mindquest_repo=mq_repo,
        evaluation_service=eval_service,
        agent_registry=registry,
        activity_repo=act_repo,
    )

    # 4 AI calls happen inside submit_response:
    # Phase 1: (evaluate_thinking || evaluate_german) -> ~1 * delay
    # Phase 2: (generate_feedback || create_challenge) -> ~1 * delay
    # Total parallel time ~ 2 * delay (0.24s) vs sequential 4 * delay (0.48s)
    t0 = time.perf_counter()
    res = await turn_service.submit_response(mindquest=mq, user_response="Kurze Antwort.")
    elapsed = time.perf_counter() - t0

    assert res.round_should_complete is False
    assert res.next_challenge is not None
    assert elapsed < delay * 3.1, (
        f"Expected 2-stage parallel execution (< {delay * 3.1:.2f}s), took {elapsed:.3f}s"
    )
