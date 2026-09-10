"""Value objects for the MindQuest domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from linguamentis.domain.hats.types import HatType


@dataclass(frozen=True, slots=True)
class Topic:
    """The intellectual topic a MindQuest explores. Kept small and immutable."""

    text: str

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("Topic text must not be empty.")
        if len(self.text) > 500:
            raise ValueError("Topic text must not exceed 500 characters.")


@dataclass(frozen=True, slots=True)
class TurnContext:
    """A compact, read-only summary of a previous turn, safe to hand to an
    agent's prompt (per HatContracts.md #15 — Agent Context)."""

    hat: HatType
    challenge_question: str
    user_response: str
    thinking_score: int | None = None
    german_score: int | None = None


@dataclass(frozen=True, slots=True)
class MindQuestContext:
    """The controlled context object handed to Hat Agents and the Blue Agent.

    Per HatContracts.md #15 and Architecture.md #25: agents receive this
    value object, never a database session or repository.
    """

    mindquest_id: UUID
    topic: str
    target_level: str  # LanguageLevel value, kept as str to avoid domain<->ai coupling
    current_hat: HatType
    current_turn_number: int = 1
    previous_responses: tuple[TurnContext, ...] = field(default_factory=tuple)
    completed_hats: tuple[HatType, ...] = field(default_factory=tuple)
    learner_strengths: tuple[str, ...] = field(default_factory=tuple)
    learner_weaknesses: tuple[str, ...] = field(default_factory=tuple)
