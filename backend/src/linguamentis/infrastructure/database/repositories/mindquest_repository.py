"""MindQuest repository implementation and interface.

Per Architecture.md #26/#27: Translates between plain domain entities
(MindQuest, HatRound, Turn) and SQLAlchemy ORM models (MindQuestModel, ...).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import HatRound, MindQuest, Turn
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestStatus
from linguamentis.infrastructure.database.models import HatRoundModel, MindQuestModel, TurnModel


class MindQuestRepository(Protocol):
    async def get_by_id(self, mindquest_id: UUID) -> MindQuest | None:
        ...

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[MindQuest]:
        ...

    async def save(self, mindquest: MindQuest) -> MindQuest:
        ...


class SQLAlchemyMindQuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, mindquest_id: UUID) -> MindQuest | None:
        stmt = (
            select(MindQuestModel)
            .where(MindQuestModel.id == mindquest_id)
            .options(
                selectinload(MindQuestModel.hat_rounds).selectinload(HatRoundModel.turns)
            )
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain_mindquest(model)

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[MindQuest]:
        stmt = (
            select(MindQuestModel)
            .where(MindQuestModel.user_id == user_id)
            .order_by(MindQuestModel.created_at.desc())
            .options(
                selectinload(MindQuestModel.hat_rounds).selectinload(HatRoundModel.turns)
            )
            .limit(limit)
            .offset(offset)
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [_to_domain_mindquest(m) for m in models]

    async def save(self, mindquest: MindQuest) -> MindQuest:
        stmt = (
            select(MindQuestModel)
            .where(MindQuestModel.id == mindquest.id)
            .options(
                selectinload(MindQuestModel.hat_rounds).selectinload(HatRoundModel.turns)
            )
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()

        planned_json = [h.value for h in mindquest.planned_hats]
        current_hat_val = mindquest.current_hat.value if mindquest.current_hat else None

        if model is None:
            model = MindQuestModel(
                id=mindquest.id,
                user_id=mindquest.user_id,
                topic=mindquest.topic,
                target_level=mindquest.target_level.value,
                status=mindquest.status.value,
                current_hat=current_hat_val,
                planned_hats=planned_json,
                created_at=mindquest.created_at,
                updated_at=mindquest.updated_at,
                completed_at=mindquest.completed_at,
            )
            self._session.add(model)
        else:
            model.topic = mindquest.topic
            model.target_level = mindquest.target_level.value
            model.status = mindquest.status.value
            model.current_hat = current_hat_val
            model.planned_hats = planned_json
            model.updated_at = mindquest.updated_at
            model.completed_at = mindquest.completed_at

        # Sync HatRounds & Turns
        existing_rounds_by_id = {r.id: r for r in model.hat_rounds}
        for domain_round in mindquest.hat_rounds:
            round_model = existing_rounds_by_id.get(domain_round.id)
            if round_model is None:
                round_model = HatRoundModel(
                    id=domain_round.id,
                    mindquest_id=domain_round.mindquest_id,
                    hat=domain_round.hat.value,
                    sequence_index=domain_round.sequence_index,
                    started_at=domain_round.started_at,
                    completed_at=domain_round.completed_at,
                )
                model.hat_rounds.append(round_model)
            else:
                round_model.hat = domain_round.hat.value
                round_model.sequence_index = domain_round.sequence_index
                round_model.started_at = domain_round.started_at
                round_model.completed_at = domain_round.completed_at

            # Sync Turns
            existing_turns_by_id = {t.id: t for t in round_model.turns}
            for domain_turn in domain_round.turns:
                turn_model = existing_turns_by_id.get(domain_turn.id)
                if turn_model is None:
                    turn_model = TurnModel(
                        id=domain_turn.id,
                        hat_round_id=domain_turn.hat_round_id,
                        turn_number=domain_turn.turn_number,
                        hat=domain_turn.hat.value,
                        challenge_question=domain_turn.challenge_question,
                        challenge_instruction=domain_turn.challenge_instruction,
                        difficulty=domain_turn.difficulty,
                        user_response=domain_turn.user_response,
                        responded_at=domain_turn.responded_at,
                        created_at=domain_turn.created_at,
                    )
                    round_model.turns.append(turn_model)
                else:
                    turn_model.turn_number = domain_turn.turn_number
                    turn_model.hat = domain_turn.hat.value
                    turn_model.challenge_question = domain_turn.challenge_question
                    turn_model.challenge_instruction = domain_turn.challenge_instruction
                    turn_model.difficulty = domain_turn.difficulty
                    turn_model.user_response = domain_turn.user_response
                    turn_model.responded_at = domain_turn.responded_at

        await self._session.flush()
        return mindquest


def _to_domain_mindquest(model: MindQuestModel) -> MindQuest:
    rounds: list[HatRound] = []
    sorted_rounds = sorted(model.hat_rounds, key=lambda r: r.sequence_index)
    for r in sorted_rounds:
        sorted_turns = sorted(r.turns, key=lambda t: t.turn_number)
        turns = [
            Turn(
                id=t.id,
                hat_round_id=t.hat_round_id,
                turn_number=t.turn_number,
                hat=HatType(t.hat),
                challenge_question=t.challenge_question,
                challenge_instruction=t.challenge_instruction,
                difficulty=t.difficulty,
                user_response=t.user_response,
                responded_at=t.responded_at,
                created_at=t.created_at,
            )
            for t in sorted_turns
        ]
        rounds.append(
            HatRound(
                id=r.id,
                mindquest_id=r.mindquest_id,
                hat=HatType(r.hat),
                sequence_index=r.sequence_index,
                turns=turns,
                started_at=r.started_at,
                completed_at=r.completed_at,
            )
        )

    planned_hats = tuple(HatType(h) for h in (model.planned_hats or []))
    current_hat = HatType(model.current_hat) if model.current_hat else None

    return MindQuest(
        id=model.id,
        user_id=model.user_id,
        topic=model.topic,
        target_level=LanguageLevel(model.target_level),
        status=MindQuestStatus(model.status),
        current_hat=current_hat,
        hat_rounds=rounds,
        planned_hats=planned_hats,
        created_at=model.created_at,
        updated_at=model.updated_at,
        completed_at=model.completed_at,
    )
