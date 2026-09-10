"""MindQuest domain entities.

Per Architecture.md #9, the domain layer must not depend on FastAPI,
SQLAlchemy, OpenRouter, HTTP, Next.js, or any specific LLM provider.
These are plain dataclasses with small amounts of behavior; persistence
mapping happens in ``infrastructure/database``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.enums import (
    LanguageLevel,
    MindQuestEvent,
    MindQuestStatus,
)
from linguamentis.domain.mindquests.state_machine import MindQuestStateMachine


@dataclass(slots=True)
class Turn:
    """One exchange within a HatRound: an agent challenge + the user's response.

    Evaluations are attached once the application layer produces them; a
    Turn may exist briefly with ``user_response is None`` between the
    challenge being issued and the learner answering it.
    """

    id: UUID
    hat_round_id: UUID
    turn_number: int
    hat: HatType
    challenge_question: str
    challenge_instruction: str
    difficulty: int
    user_response: str | None = None
    responded_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def record_response(self, response: str, *, at: datetime | None = None) -> None:
        if not response or not response.strip():
            raise ValueError("A turn response must not be empty.")
        self.user_response = response
        self.responded_at = at or datetime.utcnow()

    @property
    def is_answered(self) -> bool:
        return self.user_response is not None


@dataclass(slots=True)
class HatRound:
    """One hat's complete exploration within a MindQuest (one or more Turns)."""

    id: UUID
    mindquest_id: UUID
    hat: HatType
    sequence_index: int
    turns: list[Turn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    def complete(self, *, at: datetime | None = None) -> None:
        self.completed_at = at or datetime.utcnow()

    def add_turn(
        self,
        *,
        challenge_question: str,
        challenge_instruction: str,
        difficulty: int,
    ) -> Turn:
        turn = Turn(
            id=uuid4(),
            hat_round_id=self.id,
            turn_number=len(self.turns) + 1,
            hat=self.hat,
            challenge_question=challenge_question,
            challenge_instruction=challenge_instruction,
            difficulty=difficulty,
        )
        self.turns.append(turn)
        return turn

    @property
    def latest_turn(self) -> Turn | None:
        return self.turns[-1] if self.turns else None


@dataclass(slots=True)
class MindQuest:
    """A complete intellectual exploration (Architecture.md #10)."""

    id: UUID
    user_id: UUID
    topic: str
    target_level: LanguageLevel
    status: MindQuestStatus = MindQuestStatus.CREATED
    current_hat: HatType | None = None
    hat_rounds: list[HatRound] = field(default_factory=list)
    planned_hats: tuple[HatType, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # -- state machine plumbing -------------------------------------------

    def _apply(self, event: MindQuestEvent) -> None:
        self.status = MindQuestStateMachine.apply(self.status, event)
        self.updated_at = datetime.utcnow()

    def select_topic(self, topic: str, planned_hats: tuple[HatType, ...]) -> None:
        self.topic = topic
        self.planned_hats = planned_hats
        self._apply(MindQuestEvent.SELECT_TOPIC)

    def begin(self) -> None:
        self._apply(MindQuestEvent.BEGIN_PROGRESS)

    def activate_hat(self, hat: HatType) -> HatRound:
        self._apply(MindQuestEvent.ACTIVATE_HAT)
        self.current_hat = hat
        round_ = HatRound(
            id=uuid4(),
            mindquest_id=self.id,
            hat=hat,
            sequence_index=len(self.hat_rounds),
        )
        self.hat_rounds.append(round_)
        return round_

    def complete_current_hat(self) -> None:
        current = self.current_hat_round
        if current is None:
            raise ValueError("No active hat round to complete.")
        current.complete()
        self._apply(MindQuestEvent.COMPLETE_HAT)

    def finish_all_hats(self) -> None:
        self._apply(MindQuestEvent.ALL_HATS_DONE)
        self.current_hat = None

    def start_final_evaluation(self) -> None:
        self._apply(MindQuestEvent.START_FINAL_EVALUATION)

    def complete(self) -> None:
        self._apply(MindQuestEvent.COMPLETE)
        self.completed_at = datetime.utcnow()

    def abandon(self) -> None:
        self._apply(MindQuestEvent.ABANDON)

    # -- queries -------------------------------------------------------

    @property
    def current_hat_round(self) -> HatRound | None:
        if not self.hat_rounds:
            return None
        return self.hat_rounds[-1]

    @property
    def completed_hats(self) -> tuple[HatType, ...]:
        return tuple(r.hat for r in self.hat_rounds if r.is_completed)

    @property
    def remaining_planned_hats(self) -> tuple[HatType, ...]:
        done = set(self.completed_hats)
        return tuple(h for h in self.planned_hats if h not in done)

    def all_planned_hats_completed(self) -> bool:
        return len(self.remaining_planned_hats) == 0
