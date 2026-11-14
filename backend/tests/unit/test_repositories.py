"""Unit tests for SQLAlchemy repositories using in-memory SQLite."""

from uuid import uuid4

import pytest

from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestStatus
from linguamentis.domain.users.entities import User
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserRepository,
)


@pytest.mark.asyncio
async def test_user_repository_save_and_get(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    user_id = uuid4()
    user = User(id=user_id, display_name="Test User", target_level=LanguageLevel.C1)

    saved = await user_repo.save(user)
    assert saved.id == user_id

    fetched = await user_repo.get_by_id(user_id)
    assert fetched is not None
    assert fetched.display_name == "Test User"
    assert fetched.target_level == LanguageLevel.C1


@pytest.mark.asyncio
async def test_mindquest_repository_save_and_get(db_session):
    user_repo = SQLAlchemyUserRepository(db_session)
    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Test User"))

    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    mq_id = uuid4()
    mq = MindQuest(
        id=mq_id,
        user_id=user_id,
        topic="Künstliche Intelligenz am Arbeitsplatz",
        target_level=LanguageLevel.B2,
    )
    mq.select_topic(mq.topic, (HatType.BLACK, HatType.WHITE))
    mq.begin()
    round_ = mq.activate_hat(HatType.BLACK)
    round_.add_turn(
        challenge_question="Welche Risiken gibt es?",
        challenge_instruction="Bleib beim Black Hat.",
        difficulty=3,
    )

    await mq_repo.save(mq)

    fetched = await mq_repo.get_by_id(mq_id)
    assert fetched is not None
    assert fetched.topic == "Künstliche Intelligenz am Arbeitsplatz"
    assert fetched.status == MindQuestStatus.HAT_ACTIVE
    assert len(fetched.hat_rounds) == 1
    assert fetched.hat_rounds[0].hat == HatType.BLACK
    assert len(fetched.hat_rounds[0].turns) == 1

    # Ensure default user idempotency
    def_user1 = await user_repo.ensure_default_user(user_id, "Default")
    def_user2 = await user_repo.ensure_default_user(user_id, "Default")
    assert def_user1.id == def_user2.id

    # Test list_by_user and count_completed_by_user
    listed = await mq_repo.list_by_user(user_id, limit=10, offset=0)
    assert len(listed) == 1
    assert await mq_repo.count_completed_by_user(user_id) == 0


@pytest.mark.asyncio
async def test_evaluation_repository_evidence_lists_and_final_reflection_upsert(db_session):
    from linguamentis.domain.evaluations.evidence import Correction, Evidence
    from linguamentis.domain.evaluations.german import GermanEvaluation
    from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
    from linguamentis.infrastructure.database.repositories import (
        FinalReflection,
        SQLAlchemyEvaluationRepository,
    )

    user_repo = SQLAlchemyUserRepository(db_session)
    mq_repo = SQLAlchemyMindQuestRepository(db_session)
    eval_repo = SQLAlchemyEvaluationRepository(db_session)

    user_id = uuid4()
    await user_repo.save(User(id=user_id, display_name="Repo Tester"))

    mq_id = uuid4()
    mq = MindQuest(id=mq_id, user_id=user_id, topic="Bildung", target_level=LanguageLevel.B2)
    mq.select_topic("Bildung", (HatType.BLACK,))
    mq.begin()
    r = mq.activate_hat(HatType.BLACK)
    turn = r.add_turn(
        challenge_question="Risiken?", challenge_instruction="Black Hat", difficulty=2
    )
    turn.record_response("Ein Risiko ist soziale Ungleichheit.")
    await mq_repo.save(mq)

    await eval_repo.save_thinking(
        ThinkingEvaluation(
            id=uuid4(),
            turn_id=turn.id,
            hat_adherence=88,
            relevance=82,
            reasoning=85,
            depth=79,
            specificity=80,
            evidence=[Evidence("reasoning", "Clear link", "Strong")],
        )
    )
    await eval_repo.save_german(
        GermanEvaluation(
            id=uuid4(),
            turn_id=turn.id,
            grammar=84,
            vocabulary=80,
            sentence_structure=82,
            naturalness=78,
            level_appropriateness=80,
            evidence=[Evidence("grammar", "Good syntax", "Solid")],
            corrections=[Correction("a", "b", "expl", "grammar")],
        )
    )

    t_list = await eval_repo.list_thinking_evaluations_by_mindquest(mq_id)
    g_list = await eval_repo.list_german_evaluations_by_mindquest(mq_id)
    ev_list = await eval_repo.list_evidence_by_user(user_id)
    assert len(t_list) == 1 and t_list[0].evidence[0].dimension == "reasoning"
    assert len(g_list) == 1 and len(g_list[0].corrections) == 1
    assert len(ev_list) == 2

    # Save and update FinalReflection for the same MindQuest
    refl1 = FinalReflection(
        id=uuid4(),
        mindquest_id=mq_id,
        thinking_summary="Initial thinking",
        german_summary="Initial german",
        thinking_section={"overall_summary": "Initial"},
        german_section={"overall_summary": "Initial"},
        closing_message="Good",
    )
    await eval_repo.save_final_reflection(refl1)

    refl2 = FinalReflection(
        id=uuid4(),
        mindquest_id=mq_id,
        thinking_summary="Updated thinking",
        german_summary="Updated german",
        thinking_section={"overall_summary": "Updated"},
        german_section={"overall_summary": "Updated"},
        closing_message="Great!",
    )
    await eval_repo.save_final_reflection(refl2)

    fetched_refl = await eval_repo.get_final_reflection(mq_id)
    assert fetched_refl is not None
    assert fetched_refl.thinking_summary == "Updated thinking"
    assert fetched_refl.closing_message == "Great!"


