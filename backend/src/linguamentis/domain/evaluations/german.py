"""German Evaluation domain entity.

Per EvaluationRubric.md #13-#19: German Quality evaluates the learner's
German independently from the intellectual quality of the response.

Score formula (EvaluationRubric.md #14):

    German Score =
          Grammar                * 0.25
        + Vocabulary              * 0.20
        + Sentence Structure      * 0.20
        + Naturalness             * 0.20
        + Level Appropriateness   * 0.15
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from linguamentis.domain.evaluations.evidence import Correction, Evidence

GRAMMAR_WEIGHT = 0.25
VOCABULARY_WEIGHT = 0.20
SENTENCE_STRUCTURE_WEIGHT = 0.20
NATURALNESS_WEIGHT = 0.20
LEVEL_APPROPRIATENESS_WEIGHT = 0.15


def compute_german_score(
    *,
    grammar: int,
    vocabulary: int,
    sentence_structure: int,
    naturalness: int,
    level_appropriateness: int,
) -> int:
    """Deterministic, application-owned scoring formula (see thinking.py docstring)."""

    for name, value in (
        ("grammar", grammar),
        ("vocabulary", vocabulary),
        ("sentence_structure", sentence_structure),
        ("naturalness", naturalness),
        ("level_appropriateness", level_appropriateness),
    ):
        if not (0 <= value <= 100):
            raise ValueError(f"{name} must be within 0-100, got {value}.")

    total = (
        grammar * GRAMMAR_WEIGHT
        + vocabulary * VOCABULARY_WEIGHT
        + sentence_structure * SENTENCE_STRUCTURE_WEIGHT
        + naturalness * NATURALNESS_WEIGHT
        + level_appropriateness * LEVEL_APPROPRIATENESS_WEIGHT
    )
    return round(total)


@dataclass(slots=True)
class GermanEvaluation:
    """Per EvaluationRubric.md #4 — evaluator output shape."""

    id: UUID
    turn_id: UUID

    grammar: int
    vocabulary: int
    sentence_structure: int
    naturalness: int
    level_appropriateness: int

    evidence: list[Evidence] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def score(self) -> int:
        return compute_german_score(
            grammar=self.grammar,
            vocabulary=self.vocabulary,
            sentence_structure=self.sentence_structure,
            naturalness=self.naturalness,
            level_appropriateness=self.level_appropriateness,
        )

    def score_anchor(self) -> str:
        """Per EvaluationRubric.md #24."""

        s = self.score
        if s >= 90:
            return "Excellent command for the target level"
        if s >= 80:
            return "Strong"
        if s >= 70:
            return "Good"
        if s >= 60:
            return "Adequate"
        if s >= 50:
            return "Weak"
        if s >= 30:
            return "Very weak"
        return "Insufficient"
