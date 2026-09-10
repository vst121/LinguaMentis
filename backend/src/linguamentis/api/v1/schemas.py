"""Pydantic API DTOs (Data Transfer Objects) for v1 endpoints.

Per Architecture.md #32: Exposes application use cases concisely.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.enums import LanguageLevel, MindQuestStatus


class CreateMindQuestRequest(BaseModel):
    topic: str = Field(min_length=3, description="The topic for intellectual debate.")
    target_level: LanguageLevel = Field(default=LanguageLevel.B2)
    planned_hats: list[HatType] = Field(
        default_factory=lambda: [
            HatType.BLACK, 
            HatType.WHITE, 
            HatType.YELLOW, 
            HatType.RED, 
            HatType.GREEN]
    )


class TurnResponse(BaseModel):
    id: UUID
    turn_number: int
    hat: HatType
    challenge_question: str
    challenge_instruction: str
    difficulty: int
    user_response: str | None = None
    responded_at: datetime | None = None
    created_at: datetime


class HatRoundResponse(BaseModel):
    id: UUID
    hat: HatType
    sequence_index: int
    turns: list[TurnResponse]
    started_at: datetime
    completed_at: datetime | None = None


class MindQuestResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic: str
    target_level: LanguageLevel
    status: MindQuestStatus
    current_hat: HatType | None
    planned_hats: list[HatType]
    completed_hats: list[HatType]
    hat_rounds: list[HatRoundResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class StartMindQuestResponse(BaseModel):
    mindquest: MindQuestResponse
    active_hat: HatType
    initial_turn: TurnResponse
    challenge_question: str
    challenge_instruction: str
    difficulty: int


class SubmitResponseRequest(BaseModel):
    response: str = Field(min_length=1, description="Learner response in German.")


class EvidenceDTO(BaseModel):
    dimension: str
    observation: str
    impact: str


class CorrectionDTO(BaseModel):
    original: str
    corrected: str
    explanation: str
    category: str


class ThinkingEvaluationDTO(BaseModel):
    id: UUID
    score: int
    score_anchor: str
    hat_adherence: int
    relevance: int
    reasoning: int
    depth: int
    specificity: int
    evidence: list[EvidenceDTO]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class GermanEvaluationDTO(BaseModel):
    id: UUID
    score: int
    score_anchor: str
    grammar: int
    vocabulary: int
    sentence_structure: int
    naturalness: int
    level_appropriateness: int
    evidence: list[EvidenceDTO]
    corrections: list[CorrectionDTO]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class HatFeedbackDTO(BaseModel):
    thinking_feedback: str
    german_feedback: str
    encouragement: str = ""


class SubmitResponseResponse(BaseModel):
    turn: TurnResponse
    thinking_evaluation: ThinkingEvaluationDTO
    german_evaluation: GermanEvaluationDTO
    feedback: HatFeedbackDTO
    next_challenge_question: str | None = None
    next_challenge_instruction: str | None = None
    round_should_complete: bool


class AdvanceMindQuestResponse(BaseModel):
    mindquest: MindQuestResponse
    next_hat: HatType | None
    is_completed: bool
    initial_turn: TurnResponse | None = None
    final_reflection: dict | None = None


class DimensionScoreDTO(BaseModel):
    name: str
    score: float


class UserLearningProfileResponse(BaseModel):
    user_id: UUID
    mindquests_completed: int
    thinking_overall: float | None
    german_overall: float | None
    thinking_dimensions: list[DimensionScoreDTO]
    german_dimensions: list[DimensionScoreDTO]
    strongest_thinking_dimension: str | None
    weakest_thinking_dimension: str | None
    strongest_german_dimension: str | None
    weakest_german_dimension: str | None


class UserActivityResponse(BaseModel):
    id: UUID
    user_id: UUID
    activity_type: str
    mindquest_id: UUID | None
    payload: dict
    created_at: datetime
