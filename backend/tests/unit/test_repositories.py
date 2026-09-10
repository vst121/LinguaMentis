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
