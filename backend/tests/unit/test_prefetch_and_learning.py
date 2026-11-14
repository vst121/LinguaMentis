"""Focused tests for speculative prefetch cache and bulk learning profile queries."""

from __future__ import annotations

from uuid import uuid4

import pytest

from linguamentis.ai.models import HatChallenge
from linguamentis.application.learning.service import LearningService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest
from linguamentis.domain.mindquests.enums import LanguageLevel
from linguamentis.domain.users.entities import User
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserActivityRepository,
    SQLAlchemyUserRepository,
)


@pytest.mark.asyncio
async def test_prefetch_cache_consumes_and_handles_failure():
    cache = ChallengePrefetchCache()
    mq_id = uuid4()

    async def _ok_challenge() -> HatChallenge:
        return HatChallenge(
            question="Welche Risiken gibt es?",
            instruction="Bleib beim Black Hat.",
            expected_thinking_mode=HatType.BLACK,
            difficulty=2,
        )

    async def _failing_challenge() -> HatChallenge:
        raise RuntimeError("transient upstream failure")

    cache.schedule_hat_challenge(mq_id, HatType.BLACK, _ok_challenge())
    result = await cache.consume_hat_challenge(mq_id, HatType.BLACK)
    assert result is not None
    assert result.question == "Welche Risiken gibt es?"
    # Consumed once -> second consume returns None
    assert await cache.consume_hat_challenge(mq_id, HatType.BLACK) is None

    cache.schedule_hat_challenge(mq_id, HatType.WHITE, _failing_challenge())
    assert await cache.consume_hat_challenge(mq_id, HatType.WHITE) is None
    cache.clear()


@pytest.mark.asyncio
async def test_learning_service_bulk_profile_aggregation(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)

    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Learner"))

    mq = MindQuest(
        id=uuid4(),
        user_id=user_id,
        topic="Test Topic",
        target_level=LanguageLevel.B2,
    )
    mq.select_topic(mq.topic, (HatType.BLACK,))
    mq.begin()
    mq.activate_hat(HatType.BLACK)
    mq.complete_current_hat()
    mq.finish_all_hats()
    mq.start_final_evaluation()
    mq.complete()
    await mq_repo.save(mq)

    service = LearningService(
        mindquest_repo=mq_repo,
        evaluation_repo=eval_repo,
        activity_repo=act_repo,
    )
    profile = await service.get_user_learning_profile(user_id)
    assert profile.mindquests_completed == 1
    assert profile.thinking_overall is None


@pytest.mark.asyncio
async def test_learning_service_profile_with_populated_evaluations_and_activities(db_session):
    from linguamentis.domain.evaluations.evidence import Correction, Evidence
    from linguamentis.domain.evaluations.german import GermanEvaluation
    from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
    from linguamentis.domain.mindquests.enums import ActivityType

    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)

    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Learner"))

    mq = MindQuest(
        id=uuid4(),
        user_id=user_id,
        topic="Digitalisierung",
        target_level=LanguageLevel.C1,
    )
    mq.select_topic(mq.topic, (HatType.BLACK,))
    mq.begin()
    round_ = mq.activate_hat(HatType.BLACK)
    turn = round_.add_turn(
        challenge_question="Risiken?",
        challenge_instruction="Black Hat",
        difficulty=3,
    )
    turn.record_response("Ein großes Risiko ist der Datenschutz.")
    mq.complete_current_hat()
    mq.finish_all_hats()
    mq.start_final_evaluation()
    mq.complete()
    await mq_repo.save(mq)

    await eval_repo.save_thinking(
        ThinkingEvaluation(
            id=uuid4(),
            turn_id=turn.id,
            hat_adherence=95,
            relevance=85,
            reasoning=80,
            depth=60,
            specificity=75,
            evidence=[Evidence("hat_adherence", "Focused on risk", "Good")],
        )
    )
    await eval_repo.save_german(
        GermanEvaluation(
            id=uuid4(),
            turn_id=turn.id,
            grammar=92,
            vocabulary=84,
            sentence_structure=80,
            naturalness=68,
            level_appropriateness=78,
            corrections=[Correction("ist der", "besteht im", "Style", "vocabulary")],
        )
    )
    await act_repo.log_activity(user_id, ActivityType.MINDQUEST_COMPLETED, mq.id, {"ok": True})

    service = LearningService(
        mindquest_repo=mq_repo,
        evaluation_repo=eval_repo,
        activity_repo=act_repo,
    )
    profile = await service.get_user_learning_profile(user_id)
    assert profile.mindquests_completed == 1
    assert profile.thinking_overall is not None
    assert profile.german_overall is not None
    assert profile.strongest_thinking_dimension == "hat_adherence"
    assert profile.weakest_thinking_dimension == "depth"
    assert profile.strongest_german_dimension == "grammar"
    assert profile.weakest_german_dimension == "naturalness"

    activities = await service.list_user_activities(user_id, limit=10, offset=0)
    assert len(activities) == 1
    assert activities[0].activity_type == ActivityType.MINDQUEST_COMPLETED

