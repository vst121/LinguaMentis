"""User repository implementation and interface.

Per Architecture.md #27/#28: Repository interfaces belong to the
application/domain boundary; SQLAlchemy implementations belong to infrastructure.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from linguamentis.domain.mindquests.enums import LanguageLevel
from linguamentis.domain.users.entities import User
from linguamentis.infrastructure.database.models import UserModel


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None:
        ...

    async def save(self, user: User) -> User:
        ...

    async def ensure_default_user(self, default_id: UUID, display_name: str = "Learner") -> User:
        ...


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            return None
        return User(
            id=model.id,
            display_name=model.display_name,
            target_level=LanguageLevel(model.target_level),
            created_at=model.created_at,
        )

    async def save(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            model = UserModel(
                id=user.id,
                display_name=user.display_name,
                target_level=user.target_level.value,
                created_at=user.created_at,
            )
            self._session.add(model)
        else:
            model.display_name = user.display_name
            model.target_level = user.target_level.value
        await self._session.flush()
        return user

    async def ensure_default_user(self, default_id: UUID, display_name: str = "Learner") -> User:
        user = await self.get_by_id(default_id)
        if user is None:
            user = User(id=default_id, display_name=display_name, target_level=LanguageLevel.B2)
            await self.save(user)
        return user
