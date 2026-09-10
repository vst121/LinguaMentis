"""Structured AI output contracts.

Per Architecture.md #24 / PRD.md #27, important AI interactions must use
typed structured outputs rather than free-form prose:

    HatChallenge, ThinkingEvaluation, GermanEvaluation, HatFeedback,
    FinalReflection

These Pydantic models are the *wire contract* between the LLM and the AI
Gateway. The application/domain layers never see these directly — the
agents and evaluators (below) convert them into domain dataclasses
(``domain/mindquests/entities.py``, ``domain/evaluations/*.py``) so the
domain stays free of any AI-library dependency (Architecture.md #9).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from linguamentis.domain.hats.types import HatType


class Evidence(BaseModel):
    """Mirrors ``domain.evaluations.evidence.Evidence``."""

    dimension: str = Field(description="The evaluation dimension this evidence supports.")
    observation: str = Field(description="A specific, concrete observation from the response.")
    impact: str = Field(description="Why this observation matters for the score.")


class Correction(BaseModel):
    """Mirrors ``domain.evaluations.evidence.Correction``."""

    original: str = Field(description="The exact original phrase/sentence from the learner.")
    corrected: str = Field(description="A corrected or more natural version.")
    explanation: str = Field(description="Why the correction improves the German.")
    category: str = Field(
        description="grammar | vocabulary | sentence_structure "
        "| naturalness | level_appropriateness"
    )


class HatChallenge(BaseModel):
    """Output of a Hat Agent — the next question posed to the learner.

    Per HatContracts.md #14.
    """

    question: str = Field(description="The challenge question, in German unless clarification "
        "in English is explicitly required.")
    instruction: str = Field(
        description="A short instruction keeping the learner within the active Hat's thinking mode."
    )
    expected_thinking_mode: HatType
    difficulty: int = Field(ge=1, le=5, description="1 (easiest) - 5 (hardest).")
    rationale: str = Field(
        default="",
        description="Internal, not shown to the learner: why this challenge follows from context.",
    )


class ThinkingEvaluationOutput(BaseModel):
    """Raw LLM output for Thinking Quality. Per-dimension scores only —
    the aggregate score is always computed deterministically by the domain
    layer (``domain.evaluations.thinking.compute_thinking_score``), never
    trusted from the model directly.
    """

    hat_adherence: int = Field(ge=0, le=100)
    relevance: int = Field(ge=0, le=100)
    reasoning: int = Field(ge=0, le=100)
    depth: int = Field(ge=0, le=100)
    specificity: int = Field(ge=0, le=100)

    evidence: list[Evidence] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class GermanEvaluationOutput(BaseModel):
    """Raw LLM output for German Quality. See ``ThinkingEvaluationOutput`` docstring
    re: deterministic aggregation."""

    grammar: int = Field(ge=0, le=100)
    vocabulary: int = Field(ge=0, le=100)
    sentence_structure: int = Field(ge=0, le=100)
    naturalness: int = Field(ge=0, le=100)
    level_appropriateness: int = Field(ge=0, le=100)

    evidence: list[Evidence] = Field(default_factory=list)
    corrections: list[Correction] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class HatFeedback(BaseModel):
    """Per HatContracts.md #19 — Feedback Contract: Thinking, then German,
    then the next challenge. Assembled by the application layer from the
    two independent evaluations plus a short synthesis; kept as its own
    contract because the *presentation* order/framing is itself a
    structured, testable artifact.
    """

    thinking_feedback: str = Field(
        description="Feedback about the learner's thinking, given first."
    )
    german_feedback: str = Field(description="Feedback about the learner's German, given second.")
    encouragement: str = Field(default="", description="Optional short encouraging remark.")


class ThinkingReflectionSection(BaseModel):
    overall_summary: str
    strongest_thinking_modes: list[str] = Field(default_factory=list)
    weakest_thinking_modes: list[str] = Field(default_factory=list)
    key_reasoning_patterns: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    progress_note: str = Field(
        default="", description="Comparison with previous MindQuests, if any history exists."
    )


class GermanReflectionSection(BaseModel):
    overall_summary: str
    grammar_strengths: list[str] = Field(default_factory=list)
    vocabulary_notes: list[str] = Field(default_factory=list)
    naturalness_notes: list[str] = Field(default_factory=list)
    important_corrections: list[Correction] = Field(default_factory=list)
    recommended_expressions: list[str] = Field(default_factory=list)
    level_recommendations: list[str] = Field(default_factory=list)
    progress_note: str = Field(default="")


class FinalReflectionOutput(BaseModel):
    """Per PRD.md #24 — Final Reflection has two independent sections.

    The two sections are never merged into a single narrative score; each
    keeps its own summary/evidence, consistent with the "never combine"
    rule applied throughout the product.
    """

    thinking: ThinkingReflectionSection
    german: GermanReflectionSection
    closing_message: str = Field(
        description="A short, motivating closing message from the Blue Agent."
    )
