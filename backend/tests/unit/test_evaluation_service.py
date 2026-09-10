"""Unit tests for EvaluationService."""

from uuid import uuid4

import pytest

from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import Turn
from linguamentis.domain.mindquests.enums import LanguageLevel
from linguamentis.domain.mindquests.value_objects import MindQuestContext
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyUserActivityRepository,
)


@pytest.mark.asyncio
async def test_evaluate_turn_response_parallel_execution(fake_gateway, db_session):
    eval_repo = SQLAlchemyEvaluationRepository(db_session)
    act_repo = SQLAlchemyUserActivityRepository(db_session)
    service = EvaluationService(
        gateway=fake_gateway, evaluation_repo=eval_repo, activity_repo=act_repo
    )

    user_id = uuid4()
    mq_id = uuid4()
    turn_id = uuid4()

    turn = Turn(
        id=turn_id,
        hat_round_id=uuid4(),
        turn_number=1,
        hat=HatType.BLACK,
        challenge_question="Welche Risiken gibt es?",
        challenge_instruction="Bleib beim Black Hat.",
        difficulty=3,
    )

    context = MindQuestContext(
        mindquest_id=mq_id,
        topic="KI im Alltag",
        target_level=LanguageLevel.B2.value,
        current_hat=HatType.BLACK,
        current_turn_number=1,
    )

    user_response = "Ein großes Risiko ist Datenschutz und Kontrollverlust."

    res = await service.evaluate_turn_response(
        user_id=user_id,
        turn=turn,
        context=context,
        user_response=user_response,
    )

    assert res.thinking.turn_id == turn_id
    assert res.thinking.score >= 0
    assert res.german.turn_id == turn_id
    assert res.german.score >= 0
    assert res.feedback.thinking_feedback != ""
    assert res.feedback.german_feedback != ""

    # Verify persisted in database
    persisted_thinking = await eval_repo.get_thinking_by_turn(turn_id)
    assert persisted_thinking is not None
    assert persisted_thinking.score == res.thinking.score

    persisted_german = await eval_repo.get_german_by_turn(turn_id)
    assert persisted_german is not None
    assert persisted_german.score == res.german.score
