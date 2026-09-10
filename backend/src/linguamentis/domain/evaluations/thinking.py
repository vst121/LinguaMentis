"""Thinking Evaluation domain entity.

Per EvaluationRubric.md #5-#11:
  Thinking Quality measures how effectively the learner performs the
  assigned cognitive task. It does NOT measure German proficiency.

Score formula (EvaluationRubric.md #6):

    Thinking Score =
          Hat Adherence   * 0.25
        + Relevance       * 0.15
        + Reasoning       * 0.25
        + Depth           * 0.20
        + Specificity     * 0.15
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from linguamentis.domain.evaluations.evidence import Evidence

# Weights per EvaluationRubric.md #6.
HAT_ADHERENCE_WEIGHT = 0.25
RELEVANCE_WEIGHT = 0.15
REASONING_WEIGHT = 0.25
DEPTH_WEIGHT = 0.20
SPECIFICITY_WEIGHT = 0.15


def compute_thinking_score(
    *,
    hat_adherence: int,
    relevance: int,
    reasoning: int,
    depth: int,
    specificity: int,
) -> int:
    """Deterministic, application-owned scoring formula.

    The LLM proposes per-dimension scores; the *aggregate* score is always
    computed here so the arithmetic cannot drift between calls or providers
    (Principle 1 — the application owns state, including derived scores).
    """

    for name, value in (
        ("hat_adherence", hat_adherence),
        ("relevance", relevance),
        ("reasoning", reasoning),
        ("depth", depth),
        ("specificity", specificity),
    ):
        if not (0 <= value <= 100):
            raise ValueError(f"{name} must be within 0-100, got {value}.")

    total = (
        hat_adherence * HAT_ADHERENCE_WEIGHT
        + relevance * RELEVANCE_WEIGHT
        + reasoning * REASONING_WEIGHT
        + depth * DEPTH_WEIGHT
        + specificity * SPECIFICITY_WEIGHT
    )
    return round(total)


@dataclass(slots=True)
class ThinkingEvaluation:
    """Per EvaluationRubric.md #4 — evaluator output shape."""

    id: UUID
    turn_id: UUID

    hat_adherence: int
    relevance: int
    reasoning: int
    depth: int
    specificity: int

    evidence: list[Evidence] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def score(self) -> int:
        return compute_thinking_score(
            hat_adherence=self.hat_adherence,
            relevance=self.relevance,
            reasoning=self.reasoning,
            depth=self.depth,
            specificity=self.specificity,
        )

    def score_anchor(self) -> str:
        """Human-readable interpretation, per EvaluationRubric.md #24."""

        s = self.score
        if s >= 90:
            return "Exceptional thinking for the task"
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
