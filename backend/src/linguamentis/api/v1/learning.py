"""User learning history and profile REST API endpoints.

Per Architecture.md #32:
    GET /api/v1/users/{user_id}/learning-profile
    GET /api/v1/users/{user_id}/activities
    GET /api/v1/users/{user_id}/mindquests
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from linguamentis.api.dependencies import get_learning_service, get_mindquest_service
from linguamentis.api.v1.mindquests import _map_mindquest
from linguamentis.api.v1.schemas import (
    DimensionScoreDTO,
    MindQuestResponse,
    UserActivityResponse,
    UserLearningProfileResponse,
)
from linguamentis.application.learning.service import LearningService
from linguamentis.application.mindquests.service import MindQuestService

router = APIRouter(prefix="/users", tags=["Learning & Users"])


@router.get("/{user_id}/learning-profile", response_model=UserLearningProfileResponse)
async def get_learning_profile(
    user_id: UUID,
    service: Annotated[LearningService, Depends(get_learning_service)],
) -> UserLearningProfileResponse:
    profile = await service.get_user_learning_profile(user_id)
    return UserLearningProfileResponse(
        user_id=profile.user_id,
        mindquests_completed=profile.mindquests_completed,
        thinking_overall=profile.thinking_overall,
        german_overall=profile.german_overall,
        thinking_dimensions=[
            DimensionScoreDTO(name=d.name, score=d.score)
            for d in profile.thinking_dimensions
        ],
        german_dimensions=[
            DimensionScoreDTO(name=d.name, score=d.score)
            for d in profile.german_dimensions
        ],
        strongest_thinking_dimension=profile.strongest_thinking_dimension,
        weakest_thinking_dimension=profile.weakest_thinking_dimension,
        strongest_german_dimension=profile.strongest_german_dimension,
        weakest_german_dimension=profile.weakest_german_dimension,
    )


@router.get("/{user_id}/activities", response_model=list[UserActivityResponse])
async def list_user_activities(
    user_id: UUID,
    service: Annotated[LearningService, Depends(get_learning_service)],
    limit: int = 50,
    offset: int = 0,
) -> list[UserActivityResponse]:
    activities = await service.list_user_activities(user_id, limit=limit, offset=offset)
    return [
        UserActivityResponse(
            id=a.id,
            user_id=a.user_id,
            activity_type=a.activity_type.value,
            mindquest_id=a.mindquest_id,
            payload=a.payload,
            created_at=a.created_at,
        )
        for a in activities
    ]


@router.get("/{user_id}/mindquests", response_model=list[MindQuestResponse])
async def list_user_mindquests(
    user_id: UUID,
    service: Annotated[MindQuestService, Depends(get_mindquest_service)],
    limit: int = 50,
    offset: int = 0,
) -> list[MindQuestResponse]:
    quests = await service.list_user_mindquests(user_id, limit=limit, offset=offset)
    return [_map_mindquest(q) for q in quests]
