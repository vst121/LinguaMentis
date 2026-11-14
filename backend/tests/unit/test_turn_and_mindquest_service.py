"""Unit tests for TurnService and MindQuestService multi-turn & multi-hat logic."""

from __future__ import annotations

from uuid import uuid4

import pytest

from linguamentis.ai.models import Evidence, GermanEvaluationOutput, ThinkingEvaluationOutput
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.application.turns.service import TurnService
from linguamentis.domain.hats.types import ARGUE_SELECTABLE_HATS, HatType
from linguamentis.domain.mindquests.enums import (
    LanguageLevel,
    MindQuestMode,
    MindQuestStatus,
)
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

    # Even with a low thinking score (< 75), each hat has strictly one turn/round
    fake_llm_client.queue_response(ThinkingEvaluationOutput, _low_thinking_output())
    sub1 = await mq_service.submit_response(
        mindquest_id=mq.id, user_response="Es gibt viele Studien zur Nutzung."
    )
    assert sub1.thinking_evaluation.score < 75
    assert sub1.round_should_complete is True
    assert sub1.next_challenge is None

    updated_mq = await mq_service.get_mindquest(mq.id)
    assert len(updated_mq.hat_rounds[0].turns) == 1

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
async def test_argue_mode_flow_locks_hat_until_above_80_and_forbids_blue_or_reuse(
    db_session, fake_llm_client, fake_gateway, agent_registry
):
    user_repo, mq_service = _build_services(db_session, fake_gateway, agent_registry)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Debater"))

    mq = await mq_service.create_mindquest(
        user_id=user_id,
        topic="Tempolimit auf Autobahnen",
        target_level=LanguageLevel.C1,
        mode=MindQuestMode.ARGUE,
    )
    assert mq.mode == MindQuestMode.ARGUE
    assert mq.planned_hats == ARGUE_SELECTABLE_HATS
    assert HatType.BLUE not in mq.planned_hats

    # Blue hat can never be selected in Argue Mode
    with pytest.raises(DomainError, match="Blue Hat"):
        await mq_service.select_hat(mq.id, HatType.BLUE)

    # Select BLACK hat first
    sel = await mq_service.select_hat(mq.id, HatType.BLACK)
    assert sel.active_hat == HatType.BLACK

    # Cannot switch hat while current hat is active and below >80% average
    with pytest.raises(DomainError, match="Cannot change hat"):
        await mq_service.select_hat(mq.id, HatType.WHITE)

    # Submit response with average <= 80% -> Devil's Advocate rejection, round stays open
    fake_llm_client.queue_response(ThinkingEvaluationOutput, _low_thinking_output())
    fake_llm_client.queue_response(
        GermanEvaluationOutput,
        GermanEvaluationOutput(
            grammar=78,
            vocabulary=78,
            sentence_structure=78,
            naturalness=78,
            level_appropriateness=78,
        ),
    )
    sub_reject = await mq_service.submit_response(
        mindquest_id=mq.id, user_response="Es gibt Staus."
    )
    assert sub_reject.average_score <= 80.0
    assert sub_reject.round_should_complete is False
    assert sub_reject.next_challenge is not None

    # Still cannot switch hats while rejected
    with pytest.raises(DomainError, match="Cannot change hat"):
        await mq_service.select_hat(mq.id, HatType.YELLOW)

    # Submit stronger response (>80% average with default FakeLLMClient 82.0)
    sub_pass = await mq_service.submit_response(
        mindquest_id=mq.id,
        user_response="Ein zentrales Risiko liegt in längeren Lieferzeiten im Güterverkehr.",
    )
    assert sub_pass.average_score > 80.0
    assert sub_pass.round_should_complete is True
    assert sub_pass.next_challenge is None

    # Advance completes BLACK and waits for next user selection
    adv1 = await mq_service.advance_mindquest(mq.id)
    assert adv1.is_completed is False
    assert adv1.next_hat is None
    assert adv1.mindquest.status == MindQuestStatus.HAT_COMPLETED

    # Already-completed BLACK hat cannot be selected again
    with pytest.raises(DomainError, match="already been completed"):
        await mq_service.select_hat(mq.id, HatType.BLACK)

    # Complete the remaining 4 selectable hats (WHITE, YELLOW, GREEN, RED)
    for remaining_hat in (HatType.WHITE, HatType.YELLOW, HatType.GREEN, HatType.RED):
        await mq_service.select_hat(mq.id, remaining_hat)
        sub = await mq_service.submit_response(
            mindquest_id=mq.id,
            user_response="Differenzierte Argumentation mit präziser C1-Ausdrucksweise.",
        )
        assert sub.round_should_complete is True
        adv = await mq_service.advance_mindquest(mq.id)

    assert adv.is_completed is True
    assert adv.final_reflection is not None
    assert adv.mindquest.status == MindQuestStatus.COMPLETED
