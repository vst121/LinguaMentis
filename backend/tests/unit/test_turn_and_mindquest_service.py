"""Unit tests for TurnService and MindQuestService multi-turn & multi-hat logic."""

from __future__ import annotations

from uuid import uuid4

import pytest

from linguamentis.ai.models import Evidence, ThinkingEvaluationOutput
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.application.turns.service import TurnService
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestStatus
from linguamentis.domain.users.entities import User
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserActivityRepository,
    SQLAlchemyUserRepository,
)
from linguamentis.shared.exceptions import DomainError, NotFoundError


def _low_thinking_output() -> ThinkingEvaluationOutput:
    return ThinkingEvaluationOutput(
        hat_adherence=55,
        relevance=60,
        reasoning=50,
        depth=50,
        specificity=55,
        evidence=[
            Evidence(
                dimension="depth",
                observation="Very brief statement.",
                impact="Needs deeper risk exploration.",
            )
        ],
        strengths=["On topic"],
        weaknesses=["Too shallow"],
        recommendations=["Give a concrete example"],
    )


def _build_services(db_session, fake_gateway, agent_registry, prefetch_cache=None):
    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)
    eval_service = EvaluationService(
        gateway=fake_gateway, evaluation_repo=eval_repo, activity_repo=act_repo
    )
    turn_service = TurnService(
        mindquest_repo=mq_repo,
        evaluation_service=eval_service,
        agent_registry=agent_registry,
        activity_repo=act_repo,
        prefetch_cache=prefetch_cache,
    )
    mq_service = MindQuestService(
        mindquest_repo=mq_repo,
        evaluation_repo=eval_repo,
        turn_service=turn_service,
        agent_registry=agent_registry,
        activity_repo=act_repo,
        prefetch_cache=prefetch_cache,
    )
    return user_repo, mq_service


@pytest.mark.asyncio
async def test_multi_turn_hat_round_and_multi_hat_progression(
    db_session, fake_llm_client, fake_gateway, agent_registry
):
    prefetch_cache = ChallengePrefetchCache()
    user_repo, mq_service = _build_services(
        db_session, fake_gateway, agent_registry, prefetch_cache
    )
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Learner"))

    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="KI in der Medizin",
        target_level=LanguageLevel.B2,
        planned_hats=(HatType.BLACK, HatType.YELLOW),
    )
    assert mq.planned_hats == (
        HatType.WHITE,
        HatType.YELLOW,
        HatType.GREEN,
        HatType.RED,
        HatType.BLACK,
        HatType.BLUE,
    )
    start_res = await mq_service.start_mindquest(mq.id)
    assert start_res.active_hat == HatType.WHITE
    assert start_res.initial_turn.turn_number == 1

    # Turn 1 gets a low thinking score (< 75) -> follow-up Turn 2 is created
    fake_llm_client.queue_response(ThinkingEvaluationOutput, _low_thinking_output())
    sub1 = await mq_service.submit_response(
        mindquest_id=mq.id, user_response="Es gibt viele Studien zur Nutzung."
    )
    assert sub1.thinking_evaluation.score < 75
    assert sub1.round_should_complete is False
    assert sub1.next_challenge is not None

    updated_mq = await mq_service.get_mindquest(mq.id)
    assert len(updated_mq.hat_rounds[0].turns) == 2

    # Turn 2 gets default score (>= 75) -> round completes
    sub2 = await mq_service.submit_response(
        mindquest_id=mq.id,
        user_response="Krankenhäuser berichten von 20 Prozent schnellerer Auswertung.",
    )
    assert sub2.round_should_complete is True
    assert sub2.next_challenge is None

    # Advance through remaining mandatory hats: YELLOW -> GREEN -> RED -> BLACK -> BLUE
    remaining_hats = (
        HatType.YELLOW,
        HatType.GREEN,
        HatType.RED,
        HatType.BLACK,
        HatType.BLUE,
    )
    for expected_hat in remaining_hats:
        adv = await mq_service.advance_mindquest(mq.id)
        assert adv.is_completed is False
        assert adv.next_hat == expected_hat
        assert adv.initial_turn is not None
        await mq_service.submit_response(
            mindquest_id=mq.id,
            user_response="Eine differenzierte Perspektive auf KI in der Medizin ist wichtig.",
        )

    adv_final = await mq_service.advance_mindquest(mq.id)
    assert adv_final.is_completed is True
    assert adv_final.final_reflection is not None
    assert adv_final.mindquest.status == MindQuestStatus.COMPLETED


@pytest.mark.asyncio
async def test_mindquest_and_turn_service_error_branches(
    db_session, fake_gateway, agent_registry
):
    user_repo, mq_service = _build_services(db_session, fake_gateway, agent_registry)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Learner"))

    with pytest.raises(NotFoundError):
        await mq_service.get_mindquest(uuid4())

    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="Test Thema",
        target_level=LanguageLevel.B2,
        planned_hats=(HatType.BLACK,),
    )

    with pytest.raises(DomainError, match="Expected HAT_ACTIVE"):
        await mq_service.submit_response(
            mindquest_id=mq.id, user_response="Antwort vor dem Start"
        )

    with pytest.raises(DomainError):
        await mq_service.advance_mindquest(mq.id)


@pytest.mark.asyncio
async def test_max_three_turns_per_hat_round_forces_completion_even_with_low_scores(
    db_session, fake_llm_client, fake_gateway, agent_registry
):
    user_repo, mq_service = _build_services(db_session, fake_gateway, agent_registry)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Learner"))

    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="Künstliche Intelligenz im Journalismus",
        target_level=LanguageLevel.B2,
        planned_hats=(HatType.BLACK,),
    )
    await mq_service.start_mindquest(mq.id)

    # Queue 3 consecutive low-scoring thinking evaluations (< 75)
    fake_llm_client.queue_response(
        ThinkingEvaluationOutput,
        _low_thinking_output(),
        _low_thinking_output(),
        _low_thinking_output(),
    )

    sub1 = await mq_service.submit_response(mq.id, "Turn 1 zu kurz.")
    assert sub1.round_should_complete is False
    assert sub1.next_challenge is not None

    sub2 = await mq_service.submit_response(mq.id, "Turn 2 immer noch oberflächlich.")
    assert sub2.round_should_complete is False
    assert sub2.next_challenge is not None

    # Turn 3 reaches MAX_TURNS_PER_HAT_ROUND = 3 -> must complete round despite low score
    sub3 = await mq_service.submit_response(mq.id, "Turn 3 erreicht das Limit.")
    assert sub3.thinking_evaluation.score < 75
    assert sub3.round_should_complete is True
    assert sub3.next_challenge is None


@pytest.mark.asyncio
async def test_full_five_hat_default_sequence_and_activity_logging(
    db_session, fake_gateway, agent_registry
):
    from linguamentis.domain.hats.types import DEFAULT_HAT_SEQUENCE

    user_repo, mq_service = _build_services(db_session, fake_gateway, agent_registry)
    act_repo = SQLAlchemyUserActivityRepository(db_session)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Full Journey Learner"))

    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="Vier-Tage-Woche in Deutschland",
        target_level=LanguageLevel.C1,
        planned_hats=DEFAULT_HAT_SEQUENCE,
    )
    assert len(mq.planned_hats) == len(DEFAULT_HAT_SEQUENCE)

    start_res = await mq_service.start_mindquest(mq.id)
    assert start_res.active_hat == DEFAULT_HAT_SEQUENCE[0]

    for idx, expected_hat in enumerate(DEFAULT_HAT_SEQUENCE):
        current = await mq_service.get_mindquest(mq.id)
        assert current.current_hat == expected_hat
        sub = await mq_service.submit_response(
            mq.id, f"Fundierte C1-Antwort für Perspektive {expected_hat.value}."
        )
        assert sub.round_should_complete is True
        adv = await mq_service.advance_mindquest(mq.id)
        if idx < len(DEFAULT_HAT_SEQUENCE) - 1:
            assert adv.is_completed is False
            assert adv.next_hat == DEFAULT_HAT_SEQUENCE[idx + 1]
        else:
            assert adv.is_completed is True
            assert adv.final_reflection is not None

    from linguamentis.domain.mindquests.enums import ActivityType

    activities = await act_repo.list_by_user(user_id, limit=100)
    activity_types = {a.activity_type for a in activities}
    assert {
        ActivityType.MINDQUEST_STARTED,
        ActivityType.HAT_SELECTED,
        ActivityType.RESPONSE_SUBMITTED,
        ActivityType.THINKING_EVALUATED,
        ActivityType.GERMAN_EVALUATED,
        ActivityType.HAT_COMPLETED,
        ActivityType.MINDQUEST_COMPLETED,
    }.issubset(activity_types)

