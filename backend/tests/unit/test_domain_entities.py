"""Unit tests for MindQuest, HatRound, and Turn domain entities."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest

from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import HatRound, MindQuest, Turn
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestStatus
from linguamentis.shared.exceptions import InvalidStateTransitionError


def test_turn_record_response_and_validation():
    turn = Turn(
        id=uuid4(),
        hat_round_id=uuid4(),
        turn_number=1,
        hat=HatType.BLACK,
        challenge_question="Welche Risiken gibt es?",
        challenge_instruction="Fokus auf Risiken.",
        difficulty=3,
    )
    assert turn.is_answered is False

    with pytest.raises(ValueError, match="must not be empty"):
        turn.record_response("")

    with pytest.raises(ValueError, match="must not be empty"):
        turn.record_response("   ")

    fixed_time = datetime(2026, 11, 14, 12, 0, 0)
    turn.record_response("Ein zentrales Risiko ist die Abhängigkeit.", at=fixed_time)
    assert turn.is_answered is True
    assert turn.user_response == "Ein zentrales Risiko ist die Abhängigkeit."
    assert turn.responded_at == fixed_time


def test_hat_round_turns_and_completion():
    round_ = HatRound(
        id=uuid4(),
        mindquest_id=uuid4(),
        hat=HatType.WHITE,
        sequence_index=0,
    )
    assert round_.is_completed is False
    assert round_.latest_turn is None

    t1 = round_.add_turn(
        challenge_question="Was wissen wir?",
        challenge_instruction="Nur Fakten.",
        difficulty=2,
    )
    t2 = round_.add_turn(
        challenge_question="Welche Daten fehlen?",
        challenge_instruction="Datenlücken benennen.",
        difficulty=3,
    )
    assert t1.turn_number == 1
    assert t2.turn_number == 2
    assert round_.latest_turn == t2

    round_.complete()
    assert round_.is_completed is True
    assert round_.completed_at is not None


def test_mindquest_multi_hat_progression_and_abandon():
    mq = MindQuest(
        id=uuid4(),
        user_id=uuid4(),
        topic="Erneuerbare Energien",
        target_level=LanguageLevel.C1,
    )
    assert mq.status == MindQuestStatus.CREATED
    assert mq.current_hat_round is None

    with pytest.raises(ValueError, match="No active hat round to complete"):
        mq.complete_current_hat()

    mq.select_topic("Erneuerbare Energien", (HatType.BLACK, HatType.YELLOW))
    assert mq.status == MindQuestStatus.TOPIC_SELECTED
    assert mq.remaining_planned_hats == (HatType.BLACK, HatType.YELLOW)
    assert mq.all_planned_hats_completed() is False

    mq.begin()
    r1 = mq.activate_hat(HatType.BLACK)
    assert mq.current_hat == HatType.BLACK
    assert mq.current_hat_round == r1
    assert mq.status == MindQuestStatus.HAT_ACTIVE

    mq.complete_current_hat()
    assert mq.status == MindQuestStatus.HAT_COMPLETED
    assert mq.completed_hats == (HatType.BLACK,)
    assert mq.remaining_planned_hats == (HatType.YELLOW,)
    assert mq.all_planned_hats_completed() is False

    # Activate second hat from HAT_COMPLETED
    r2 = mq.activate_hat(HatType.YELLOW)
    assert r2.sequence_index == 1
    assert mq.current_hat == HatType.YELLOW
    mq.complete_current_hat()
    assert mq.all_planned_hats_completed() is True

    mq.finish_all_hats()
    assert mq.current_hat is None
    assert mq.status == MindQuestStatus.ALL_HATS_COMPLETED

    mq.start_final_evaluation()
    assert mq.status == MindQuestStatus.FINAL_EVALUATION

    mq.complete()
    assert mq.status == MindQuestStatus.COMPLETED
    assert mq.completed_at is not None

    # Completed is terminal -> cannot abandon after completion
    with pytest.raises(InvalidStateTransitionError):
        mq.abandon()


def test_mindquest_abandon_from_active_state():
    mq = MindQuest(
        id=uuid4(),
        user_id=uuid4(),
        topic="Test",
        target_level=LanguageLevel.B2,
    )
    mq.select_topic("Test", (HatType.BLACK,))
    mq.begin()
    mq.abandon()
    assert mq.status == MindQuestStatus.ABANDONED
