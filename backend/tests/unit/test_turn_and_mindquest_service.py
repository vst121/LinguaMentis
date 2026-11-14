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
async def test_full_six_hat_default_sequence_and_activity_logging(
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


@pytest.mark.asyncio
async def test_argue_mode_hat_switching_thresholds_and_read_only_solved_hats(
    db_session, fake_llm_client, fake_gateway, agent_registry
):
    user_repo, mq_service = _build_services(db_session, fake_gateway, agent_registry)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Debater"))

    # --- Part A: C1 requires > 80%, allows hat switching with preserved state ---
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

    # Select BLACK hat first and submit a weak answer (<= 80% -> rejected, Turn 2 created)
    sel_black_1 = await mq_service.select_hat(mq.id, HatType.BLACK)
    assert sel_black_1.active_hat == HatType.BLACK

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

    # Switch to WHITE hat mid-debate, then switch back to BLACK -> BLACK's Turn 2 state is preserved
    sel_white = await mq_service.select_hat(mq.id, HatType.WHITE)
    assert sel_white.active_hat == HatType.WHITE
    assert sel_white.initial_turn.turn_number == 1

    sel_black_2 = await mq_service.select_hat(mq.id, HatType.BLACK)
    assert sel_black_2.active_hat == HatType.BLACK
    assert sel_black_2.is_read_only is False
    assert sel_black_2.initial_turn.turn_number == 2
    assert sel_black_2.last_answered_turn is not None
    assert sel_black_2.last_answered_turn.user_response == "Es gibt Staus."
    assert sel_black_2.last_average_score is not None

    # Submit stronger response (> 80% average with default FakeLLMClient 82.0) -> BLACK solved!
    sub_pass = await mq_service.submit_response(
        mindquest_id=mq.id,
        user_response="Ein zentrales Risiko liegt in längeren Lieferzeiten im Güterverkehr.",
    )
    assert sub_pass.average_score > 80.0
    assert sub_pass.round_should_complete is True
    assert sub_pass.next_challenge is None

    # Selecting solved BLACK hat returns read-only state & scores, and blocks modifications
    inspect_black = await mq_service.select_hat(mq.id, HatType.BLACK)
    assert inspect_black.is_read_only is True
    assert inspect_black.last_thinking_evaluation is not None
    assert inspect_black.last_german_evaluation is not None
    assert inspect_black.last_average_score is not None and inspect_black.last_average_score > 80.0

    with pytest.raises(DomainError, match="No active hat round"):
        await mq_service.submit_response(
            mindquest_id=mq.id, user_response="Darf nicht mehr geändert werden."
        )

    # Complete the remaining 4 selectable hats (WHITE, YELLOW, GREEN, RED) -> auto-completes on 5th
    for idx, remaining_hat in enumerate(
        (HatType.WHITE, HatType.YELLOW, HatType.GREEN, HatType.RED)
    ):
        await mq_service.select_hat(mq.id, remaining_hat)
        sub = await mq_service.submit_response(
            mindquest_id=mq.id,
            user_response="Differenzierte Argumentation mit präziser C1-Ausdrucksweise.",
        )
        assert sub.round_should_complete is True
        if idx == 3:
            assert sub.final_reflection is not None

    finished = await mq_service.get_mindquest(mq.id)
    assert finished.status == MindQuestStatus.COMPLETED

    # --- Part B: B2 requires only >= 10% average ---
    mq_b2 = await mq_service.create_mindquest(
        user_id=user_id,
        topic="ÖPNV kostenlos machen",
        target_level=LanguageLevel.B2,
        mode=MindQuestMode.ARGUE,
    )
    await mq_service.select_hat(mq_b2.id, HatType.YELLOW)
    fake_llm_client.queue_response(
        ThinkingEvaluationOutput,
        ThinkingEvaluationOutput(
            hat_adherence=10,
            relevance=10,
            reasoning=10,
            depth=10,
            specificity=10,
        ),
    )
    fake_llm_client.queue_response(
        GermanEvaluationOutput,
        GermanEvaluationOutput(
            grammar=10,
            vocabulary=10,
            sentence_structure=10,
            naturalness=10,
            level_appropriateness=10,
        ),
    )
    sub_b2_pass = await mq_service.submit_response(
        mindquest_id=mq_b2.id, user_response="Busse wären für alle zugänglich."
    )
    assert sub_b2_pass.average_score == 10.0
    assert sub_b2_pass.round_should_complete is True

    await mq_service.select_hat(mq_b2.id, HatType.RED)
    fake_llm_client.queue_response(
        ThinkingEvaluationOutput,
        ThinkingEvaluationOutput(
            hat_adherence=5, relevance=5, reasoning=5, depth=5, specificity=5
        ),
    )
    fake_llm_client.queue_response(
        GermanEvaluationOutput,
        GermanEvaluationOutput(
            grammar=5,
            vocabulary=5,
            sentence_structure=5,
            naturalness=5,
            level_appropriateness=5,
        ),
    )
    sub_b2_fail = await mq_service.submit_response(
        mindquest_id=mq_b2.id, user_response="Hm."
    )
    assert sub_b2_fail.average_score == 5.0
    assert sub_b2_fail.round_should_complete is False
