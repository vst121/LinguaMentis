"""UserActivity repository implementation and interface.

Per Architecture.md #30: Provides a chronological view of the learning journey.
UserActivity is NOT the authoritative source of domain state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from linguamentis.domain.mindquests.enums import ActivityType
from linguamentis.infrastructure.database.models import UserActivityModel


@dataclass(slots=True)
class UserActivity:
    id: UUID
    user_id: UUID
    activity_type: ActivityType
    mindquest_id: UUID | None = None
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class UserActivityRepository(Protocol):
    async def log_activity(
        self,
        user_id: UUID,
        activity_type: ActivityType,
        mindquest_id: UUID | None = None,
        payload: dict | None = None,
    ) -> UserActivity:
        ...

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[UserActivity]:
        ...


class SQLAlchemyUserActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_activity(
        self,
        user_id: UUID,
        activity_type: ActivityType,
        mindquest_id: UUID | None = None,
        payload: dict | None = None,
    ) -> UserActivity:
        activity = UserActivity(
            id=uuid.uuid4(),
            user_id=user_id,
            activity_type=activity_type,
            mindquest_id=mindquest_id,
            payload=payload or {},
        )
        model = UserActivityModel(
            id=activity.id,
            user_id=activity.user_id,
            mindquest_id=activity.mindquest_id,
            activity_type=activity.activity_type.value,
            payload=activity.payload,
            created_at=activity.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        return activity

    async def list_by_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[UserActivity]:
        stmt = (
            select(UserActivityModel)
            .where(UserActivityModel.user_id == user_id)
            .order_by(UserActivityModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self._session.execute(stmt)
        models = res.scalars().all()
        return [
            UserActivity(
                id=m.id,
                user_id=m.user_id,
                activity_type=ActivityType(m.activity_type),
                mindquest_id=m.mindquest_id,
                payload=m.payload or {},
                created_at=m.created_at,
            )
            for m in models
        ]
