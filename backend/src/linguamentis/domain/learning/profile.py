"""UserLearningProfile — derived, never manually maintained as source of truth.

Per Architecture.md #29:

    MindQuest History -> Evaluations -> Evidence -> Learning Profile Service
        -> UserLearningProfile

The profile is *derived* from accumulated ThinkingEvaluation/GermanEvaluation
rows; it is recomputed by ``application/learning/service.py`` rather than
stored as authoritative state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from linguamentis.domain.users.value_objects import DimensionScore

# Per Architecture.md #29 — possible dimensions.
THINKING_DIMENSIONS = (
    "critical_thinking",
    "creativity",
    "reasoning",
    "perspective_shifting",
    "depth",
)

GERMAN_DIMENSIONS = (
    "grammar",
    "vocabulary",
    "naturalness",
    "sentence_structure",
    "advanced_expression",
)


@dataclass(frozen=True, slots=True)
class UserLearningProfile:
    user_id: UUID
    mindquests_completed: int
    thinking_overall: float | None
    german_overall: float | None
    thinking_dimensions: tuple[DimensionScore, ...] = field(default_factory=tuple)
    german_dimensions: tuple[DimensionScore, ...] = field(default_factory=tuple)
    strongest_thinking_dimension: str | None = None
    weakest_thinking_dimension: str | None = None
    strongest_german_dimension: str | None = None
    weakest_german_dimension: str | None = None
