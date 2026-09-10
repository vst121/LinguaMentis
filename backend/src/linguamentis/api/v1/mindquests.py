"""MindQuest REST API endpoints.

Per Architecture.md #32:
    POST   /api/v1/mindquests
    GET    /api/v1/mindquests
    GET    /api/v1/mindquests/{id}
    POST   /api/v1/mindquests/{id}/start
    POST   /api/v1/mindquests/{id}/responses
    POST   /api/v1/mindquests/{id}/advance
    GET    /api/v1/mindquests/{id}/reflection
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from linguamentis.api.dependencies import get_mindquest_service
from linguamentis.api.v1.schemas import (
    AdvanceMindQuestResponse,
    CorrectionDTO,
    CreateMindQuestRequest,
    EvidenceDTO,
    GermanEvaluationDTO,
    HatFeedbackDTO,
    HatRoundResponse,
    MindQuestResponse,
    StartMindQuestResponse,
    SubmitResponseRequest,
    SubmitResponseResponse,
    ThinkingEvaluationDTO,
    TurnResponse,
)
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.domain.mindquests.entities import HatRound, MindQuest, Turn
from linguamentis.infrastructure.configuration import Settings, get_settings

router = APIRouter(prefix="/mindquests", tags=["MindQuests"])


def _map_turn(t: Turn) -> TurnResponse:
    return TurnResponse(
        id=t.id,
        turn_number=t.turn_number,
        hat=t.hat,
        challenge_question=t.challenge_question,
        challenge_instruction=t.challenge_instruction,
        difficulty=t.difficulty,
        user_response=t.user_response,
        responded_at=t.responded_at,
        created_at=t.created_at,
    )


def _map_round(r: HatRound) -> HatRoundResponse:
    return HatRoundResponse(
        id=r.id,
        hat=r.hat,
        sequence_index=r.sequence_index,
        turns=[_map_turn(t) for t in r.turns],
        started_at=r.started_at,
        completed_at=r.completed_at,
    )


def _map_mindquest(mq: MindQuest) -> MindQuestResponse:
    return MindQuestResponse(
        id=mq.id,
        user_id=mq.user_id,
        topic=mq.topic,
        target_level=mq.target_level,
        status=mq.status,
        current_hat=mq.current_hat,
        planned_hats=list(mq.planned_hats),
        completed_hats=list(mq.completed_hats),
        hat_rounds=[_map_round(r) for r in mq.hat_rounds],
        created_at=mq.created_at,
        updated_at=mq.updated_at,
        completed_at=mq.completed_at,
    )


@router.post("", response_model=MindQuestResponse, status_code=status.HTTP_201_CREATED)
async def create_mindquest(
    body: CreateMindQuestRequest,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> MindQuestResponse:
    mq = await service.create_mindquest(
        user_id=settings.default_user_id,
        topic=body.topic,
        target_level=body.target_level,
        planned_hats=tuple(body.planned_hats),
    )
    return _map_mindquest(mq)


@router.get("", response_model=list[MindQuestResponse])
async def list_mindquests(
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    limit: int = 50,
    offset: int = 0,
) -> list[MindQuestResponse]:
    quests = await service.list_user_mindquests(
        user_id=settings.default_user_id, limit=limit, offset=offset
    )
    return [_map_mindquest(mq) for mq in quests]


@router.get("/{id}", response_model=MindQuestResponse)
async def get_mindquest(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> MindQuestResponse:
    mq = await service.get_mindquest(id)
    return _map_mindquest(mq)


@router.post("/{id}/start", response_model=StartMindQuestResponse)
async def start_mindquest(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> StartMindQuestResponse:
    result = await service.start_mindquest(id)
    return StartMindQuestResponse(
        mindquest=_map_mindquest(result.mindquest),
        active_hat=result.active_hat,
        initial_turn=_map_turn(result.initial_turn),
        challenge_question=result.challenge.question,
        challenge_instruction=result.challenge.instruction,
        difficulty=result.challenge.difficulty,
    )


@router.post("/{id}/responses", response_model=SubmitResponseResponse)
async def submit_response(
    id: UUID,
    body: SubmitResponseRequest,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> SubmitResponseResponse:
    res = await service.submit_response(mindquest_id=id, user_response=body.response)

    t_eval = res.thinking_evaluation
    g_eval = res.german_evaluation

    t_dto = ThinkingEvaluationDTO(
        id=t_eval.id,
        score=t_eval.score,
        score_anchor=t_eval.score_anchor(),
        hat_adherence=t_eval.hat_adherence,
        relevance=t_eval.relevance,
        reasoning=t_eval.reasoning,
        depth=t_eval.depth,
        specificity=t_eval.specificity,
        evidence=[
            EvidenceDTO(dimension=e.dimension, observation=e.observation, impact=e.impact)
            for e in t_eval.evidence
        ],
        strengths=t_eval.strengths,
        weaknesses=t_eval.weaknesses,
        recommendations=t_eval.recommendations,
    )

    g_dto = GermanEvaluationDTO(
        id=g_eval.id,
        score=g_eval.score,
        score_anchor=g_eval.score_anchor(),
        grammar=g_eval.grammar,
        vocabulary=g_eval.vocabulary,
        sentence_structure=g_eval.sentence_structure,
        naturalness=g_eval.naturalness,
        level_appropriateness=g_eval.level_appropriateness,
        evidence=[
            EvidenceDTO(dimension=e.dimension, observation=e.observation, impact=e.impact)
            for e in g_eval.evidence
        ],
        corrections=[
            CorrectionDTO(
                original=c.original,
                corrected=c.corrected,
                explanation=c.explanation,
                category=c.category,
            )
            for c in g_eval.corrections
        ],
        strengths=g_eval.strengths,
        weaknesses=g_eval.weaknesses,
        recommendations=g_eval.recommendations,
    )

    f_dto = HatFeedbackDTO(
        thinking_feedback=res.feedback.thinking_feedback,
        german_feedback=res.feedback.german_feedback,
        encouragement=res.feedback.encouragement,
    )

    return SubmitResponseResponse(
        turn=_map_turn(res.turn),
        thinking_evaluation=t_dto,
        german_evaluation=g_dto,
        feedback=f_dto,
        next_challenge_question=res.next_challenge.question if res.next_challenge else None,
        next_challenge_instruction=res.next_challenge.instruction if res.next_challenge else None,
        round_should_complete=res.round_should_complete,
    )


@router.post("/{id}/advance", response_model=AdvanceMindQuestResponse)
async def advance_mindquest(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> AdvanceMindQuestResponse:
    res = await service.advance_mindquest(id)

    reflection_dict = None
    if res.final_reflection:
        reflection_dict = {
            "id": str(res.final_reflection.id),
            "mindquest_id": str(res.final_reflection.mindquest_id),
            "thinking_summary": res.final_reflection.thinking_summary,
            "german_summary": res.final_reflection.german_summary,
            "thinking_section": res.final_reflection.thinking_section,
            "german_section": res.final_reflection.german_section,
            "closing_message": res.final_reflection.closing_message,
        }

    return AdvanceMindQuestResponse(
        mindquest=_map_mindquest(res.mindquest),
        next_hat=res.next_hat,
        is_completed=res.is_completed,
        initial_turn=_map_turn(res.initial_turn) if res.initial_turn else None,
        final_reflection=reflection_dict,
    )


@router.get("/{id}/reflection")
async def get_reflection(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> dict:
    reflection = await service.get_final_reflection(id)
    if reflection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Final reflection for MindQuest '{id}' was not found.",
        )
    return {
        "id": str(reflection.id),
        "mindquest_id": str(reflection.mindquest_id),
        "thinking_summary": reflection.thinking_summary,
        "german_summary": reflection.german_summary,
        "thinking_section": reflection.thinking_section,
        "german_section": reflection.german_section,
        "closing_message": reflection.closing_message,
        "created_at": reflection.created_at.isoformat(),
    }
