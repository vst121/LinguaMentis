"""Spoken Conversation REST API endpoints for MindQuests."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from linguamentis.api.dependencies import get_conversation_service
from linguamentis.api.v1.mindquests import _map_mindquest, _map_turn
from linguamentis.api.v1.schemas import (
    CorrectionDTO,
    EvidenceDTO,
    GermanEvaluationDTO,
    MindQuestResponse,
    ThinkingEvaluationDTO,
    TurnResponse,
)
from linguamentis.application.conversation.service import ConversationService
from linguamentis.domain.hats.types import HatType

router = APIRouter(prefix="/mindquests", tags=["Conversation"])


class ConversationOpeningResponse(BaseModel):
    mindquest: MindQuestResponse
    active_hat: HatType | None = None
    active_turn: TurnResponse | None = None
    spoken_text: str
    audio_base64: str
    audio_mime_type: str = "audio/wav"
    is_completed: bool


class ConversationTurnRequest(BaseModel):
    transcript: str | None = None
    audio_base64: str | None = None
    mime_type: str = "audio/webm"
    include_audio: bool = True


class ConversationTurnResponse(BaseModel):
    mindquest: MindQuestResponse
    user_transcript: str
    spoken_reply: str
    audio_base64: str
    audio_mime_type: str = "audio/wav"
    thinking_evaluation: ThinkingEvaluationDTO
    german_evaluation: GermanEvaluationDTO
    active_hat: HatType | None = None
    active_turn: TurnResponse | None = None
    transitioned_hat: HatType | None = None
    is_completed: bool
    average_score: float = 0.0
    round_should_complete: bool = True


@router.post("/{id}/conversation/opening", response_model=ConversationOpeningResponse)
async def open_conversation(
    id: UUID,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationOpeningResponse:
    res = await service.open_conversation(id)
    return ConversationOpeningResponse(
        mindquest=_map_mindquest(res.mindquest),
        active_hat=res.active_hat,
        active_turn=_map_turn(res.active_turn) if res.active_turn else None,
        spoken_text=res.spoken_text,
        audio_base64=res.audio_base64,
        audio_mime_type=res.audio_mime_type,
        is_completed=res.is_completed,
    )


@router.post("/{id}/conversation/turn", response_model=ConversationTurnResponse)
async def submit_conversation_turn(
    id: UUID,
    body: ConversationTurnRequest,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationTurnResponse:
    res = await service.process_turn(
        id,
        transcript=body.transcript,
        audio_base64=body.audio_base64,
        mime_type=body.mime_type,
        include_audio=body.include_audio,
    )
    t = res.thinking_evaluation
    g = res.german_evaluation

    t_dto = ThinkingEvaluationDTO(
        id=t.id,
        score=t.score,
        score_anchor=t.score_anchor(),
        hat_adherence=t.hat_adherence,
        relevance=t.relevance,
        reasoning=t.reasoning,
        depth=t.depth,
        specificity=t.specificity,
        evidence=[
            EvidenceDTO(dimension=e.dimension, observation=e.observation, impact=e.impact)
            for e in t.evidence
        ],
        strengths=t.strengths,
        weaknesses=t.weaknesses,
        recommendations=t.recommendations,
    )
    g_dto = GermanEvaluationDTO(
        id=g.id,
        score=g.score,
        score_anchor=g.score_anchor(),
        grammar=g.grammar,
        vocabulary=g.vocabulary,
        sentence_structure=g.sentence_structure,
        naturalness=g.naturalness,
        level_appropriateness=g.level_appropriateness,
        evidence=[
            EvidenceDTO(dimension=e.dimension, observation=e.observation, impact=e.impact)
            for e in g.evidence
        ],
        corrections=[
            CorrectionDTO(
                original=c.original,
                corrected=c.corrected,
                explanation=c.explanation,
                category=c.category,
            )
            for c in g.corrections
        ],
        strengths=g.strengths,
        weaknesses=g.weaknesses,
        recommendations=g.recommendations,
    )

    return ConversationTurnResponse(
        mindquest=_map_mindquest(res.mindquest),
        user_transcript=res.user_transcript,
        spoken_reply=res.spoken_reply,
        audio_base64=res.audio_base64,
        audio_mime_type=res.audio_mime_type,
        thinking_evaluation=t_dto,
        german_evaluation=g_dto,
        active_hat=res.active_hat,
        active_turn=_map_turn(res.active_turn) if res.active_turn else None,
        transitioned_hat=res.transitioned_hat,
        is_completed=res.is_completed,
        average_score=res.average_score,
        round_should_complete=res.round_should_complete,
    )
