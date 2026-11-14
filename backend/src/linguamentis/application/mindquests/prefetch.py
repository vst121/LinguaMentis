"""In-memory speculative prefetch cache for MindQuest AI calls.

Prefetch tasks invoke only the stateless AIGateway (never DB sessions) so
next-hat challenges and final reflections can be prepared in the background
while the learner reads their evaluation feedback.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any
from uuid import UUID

from linguamentis.ai.models import FinalReflectionOutput, HatChallenge
from linguamentis.domain.hats.types import HatType
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)


def _consume_task_exception(task: asyncio.Task[Any]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.debug("prefetch.task_failed", error=str(exc))


class ChallengePrefetchCache:
    """Tracks in-flight background AI generation tasks keyed by MindQuest and Hat."""

    def __init__(self) -> None:
        self._hat_tasks: dict[tuple[UUID, HatType], asyncio.Task[HatChallenge]] = {}
        self._reflection_tasks: dict[UUID, asyncio.Task[FinalReflectionOutput]] = {}

    def schedule_hat_challenge(
        self,
        mindquest_id: UUID,
        hat: HatType,
        coro: Coroutine[Any, Any, HatChallenge],
    ) -> None:
        key = (mindquest_id, hat)
        existing = self._hat_tasks.get(key)
        if existing is not None and not existing.done():
            coro.close()
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            coro.close()
            return
        task = loop.create_task(coro)
        task.add_done_callback(_consume_task_exception)
        self._hat_tasks[key] = task

    async def consume_hat_challenge(
        self, mindquest_id: UUID, hat: HatType
    ) -> HatChallenge | None:
        task = self._hat_tasks.pop((mindquest_id, hat), None)
        if task is None:
            return None
        try:
            return await task
        except Exception as exc:
            logger.warning(
                "prefetch.hat_challenge_fallback",
                mindquest_id=str(mindquest_id),
                hat=hat.value,
                error=str(exc),
            )
            return None

    def schedule_final_reflection(
        self,
        mindquest_id: UUID,
        coro: Coroutine[Any, Any, FinalReflectionOutput],
    ) -> None:
        existing = self._reflection_tasks.get(mindquest_id)
        if existing is not None and not existing.done():
            coro.close()
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            coro.close()
            return
        task = loop.create_task(coro)
        task.add_done_callback(_consume_task_exception)
        self._reflection_tasks[mindquest_id] = task

    async def consume_final_reflection(
        self, mindquest_id: UUID
    ) -> FinalReflectionOutput | None:
        task = self._reflection_tasks.pop(mindquest_id, None)
        if task is None:
            return None
        try:
            return await task
        except Exception as exc:
            logger.warning(
                "prefetch.final_reflection_fallback",
                mindquest_id=str(mindquest_id),
                error=str(exc),
            )
            return None

    def clear(self) -> None:
        for hat_task in self._hat_tasks.values():
            if not hat_task.done():
                hat_task.cancel()
        for reflection_task in self._reflection_tasks.values():
            if not reflection_task.done():
                reflection_task.cancel()
        self._hat_tasks.clear()
        self._reflection_tasks.clear()
