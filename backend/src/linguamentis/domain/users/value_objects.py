"""Value objects for the users domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DimensionScore:
    """A single named 0-100 score, used within a UserLearningProfile."""

    name: str
    score: float
    sample_size: int
