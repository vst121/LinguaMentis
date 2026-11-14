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

from fastapi import APIRouter, Depends, HTTPException, Response, status

from linguamentis.api.dependencies import get_mindquest_service
from linguamentis.api.v1.schemas import (
    AdvanceMindQuestResponse,
    CorrectionDTO,
    CreateMindQuestRequest,
    EvidenceDTO,
    GermanEvaluationDTO,
    HatFeedbackDTO,
    HatRoundResponse,
    LastEvaluationDTO,
    MindQuestResponse,
    PropositionHighlightDTO,
    ResponsePropositionDTO,
    SelectHatRequest,
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
        mode=mq.mode,
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
        mode=body.mode,
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


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mindquest(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> Response:
    await service.delete_mindquest(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


def _map_thinking_dto(t_eval) -> ThinkingEvaluationDTO:
    return ThinkingEvaluationDTO(
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


def _map_german_dto(g_eval) -> GermanEvaluationDTO:
    return GermanEvaluationDTO(
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


def _map_proposition_dto(prop) -> ResponsePropositionDTO | None:
    if prop is None:
        return None
    return ResponsePropositionDTO(
        id=prop.id,
        improved_response=prop.improved_response,
        highlights=[
            PropositionHighlightDTO(
                upgraded_phrase=h.upgraded_phrase,
                original_phrase=h.original_phrase,
                explanation=h.explanation,
                category=h.category,
            )
            for h in prop.highlights
        ],
    )


@router.post("/{id}/select-hat", response_model=StartMindQuestResponse)
async def select_hat(
    id: UUID,
    body: SelectHatRequest,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> StartMindQuestResponse:
    result = await service.select_hat(id, body.hat)
    last_eval = None
    if result.last_answered_turn is not None:
        last_eval = LastEvaluationDTO(
            turn=_map_turn(result.last_answered_turn),
            thinking_evaluation=(
                _map_thinking_dto(result.last_thinking_evaluation)
                if result.last_thinking_evaluation is not None
                else None
            ),
            german_evaluation=(
                _map_german_dto(result.last_german_evaluation)
                if result.last_german_evaluation is not None
                else None
            ),
            proposition=_map_proposition_dto(result.last_proposition),
            average_score=result.last_average_score,
        )
    return StartMindQuestResponse(
        mindquest=_map_mindquest(result.mindquest),
        active_hat=result.active_hat,
        initial_turn=_map_turn(result.initial_turn),
        challenge_question=result.challenge.question,
        challenge_instruction=result.challenge.instruction,
        difficulty=result.challenge.difficulty,
        is_read_only=result.is_read_only,
        last_evaluation=last_eval,
    )


@router.post("/{id}/responses", response_model=SubmitResponseResponse)
async def submit_response(
    id: UUID,
    body: SubmitResponseRequest,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> SubmitResponseResponse:
    res = await service.submit_response(mindquest_id=id, user_response=body.response)

    t_dto = _map_thinking_dto(res.thinking_evaluation)
    g_dto = _map_german_dto(res.german_evaluation)

    f_dto = HatFeedbackDTO(
        thinking_feedback=res.feedback.thinking_feedback,
        german_feedback=res.feedback.german_feedback,
        encouragement=res.feedback.encouragement,
    )

    p_dto = _map_proposition_dto(res.proposition)

    reflection_dict = None
    if res.final_reflection is not None:
        mq = await service.get_mindquest(id)
        metrics = await service.get_mindquest_evaluation_metrics(id)
        reflection_dict = _map_reflection_payload(res.final_reflection, mq, metrics)

    return SubmitResponseResponse(
        turn=_map_turn(res.turn),
        thinking_evaluation=t_dto,
        german_evaluation=g_dto,
        feedback=f_dto,
        proposition=p_dto,
        average_score=res.average_score,
        next_challenge_question=res.next_challenge.question if res.next_challenge else None,
        next_challenge_instruction=res.next_challenge.instruction if res.next_challenge else None,
        round_should_complete=res.round_should_complete,
        final_reflection=reflection_dict,
    )


def _map_reflection_payload(
    reflection,
    mq: MindQuest,
    metrics,
) -> dict:
    return {
        "id": str(reflection.id),
        "mindquest_id": str(reflection.mindquest_id),
        "topic": mq.topic,
        "target_level": mq.target_level.value,
        "mode": mq.mode.value,
        "hats_completed": len(mq.completed_hats),
        "hats_total": len(mq.planned_hats),
        "thinking_overall": metrics.thinking_overall,
        "german_overall": metrics.german_overall,
        "thinking_dimensions": [
            {"name": d.name, "score": d.score} for d in metrics.thinking_dimensions
        ],
        "german_dimensions": [
            {"name": d.name, "score": d.score} for d in metrics.german_dimensions
        ],
        "strongest_thinking_dimension": metrics.strongest_thinking_dimension,
        "weakest_thinking_dimension": metrics.weakest_thinking_dimension,
        "strongest_german_dimension": metrics.strongest_german_dimension,
        "weakest_german_dimension": metrics.weakest_german_dimension,
        "thinking_summary": reflection.thinking_summary,
        "german_summary": reflection.german_summary,
        "thinking_section": reflection.thinking_section,
        "german_section": reflection.german_section,
        "closing_message": reflection.closing_message,
        "created_at": reflection.created_at.isoformat(),
    }


@router.post("/{id}/advance", response_model=AdvanceMindQuestResponse)
async def advance_mindquest(
    id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
) -> AdvanceMindQuestResponse:
    res = await service.advance_mindquest(id)

    reflection_dict = None
    if res.final_reflection:
        metrics = await service.get_mindquest_evaluation_metrics(id)
        reflection_dict = _map_reflection_payload(
            res.final_reflection, res.mindquest, metrics
        )

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
    mq = await service.get_mindquest(id)
    metrics = await service.get_mindquest_evaluation_metrics(id)
    return _map_reflection_payload(reflection, mq, metrics)
