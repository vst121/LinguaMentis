"""FastAPI dependency injection wiring.

Per Architecture.md #7: API layer delegates HTTP concerns and injects application services.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.gemini import GeminiClient
from linguamentis.ai.jev import DisabledDecisionVerifier, JevClient
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.learning.service import LearningService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.application.turns.service import TurnService
from linguamentis.infrastructure.configuration import Settings, get_settings
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserActivityRepository,
    SQLAlchemyUserRepository,
)
from linguamentis.infrastructure.database.session import get_db_session

# Singleton AI Gateway, Gemini client, and prefetch cache reuse
_gemini_client: GeminiClient | None = None
_ai_gateway: AIGateway | None = None
_agent_registry: AgentRegistry | None = None
_prefetch_cache: ChallengePrefetchCache | None = None


def get_gemini_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient(settings)
    return _gemini_client


def get_ai_gateway(
    settings: Annotated[Settings, Depends(get_settings)]
) -> AIGateway:
    global _ai_gateway
    if _ai_gateway is None:
        client = get_gemini_client(settings)
        _ai_gateway = AIGateway(client=client, settings=settings)
    return _ai_gateway


def get_prefetch_cache() -> ChallengePrefetchCache:
    global _prefetch_cache
    if _prefetch_cache is None:
        _prefetch_cache = ChallengePrefetchCache()
    return _prefetch_cache


async def shutdown_ai_resources() -> None:
    global _gemini_client, _ai_gateway, _agent_registry, _prefetch_cache
    if _prefetch_cache is not None:
        _prefetch_cache.clear()
        _prefetch_cache = None
    if _gemini_client is not None:
        await _gemini_client.aclose()
        _gemini_client = None
    _ai_gateway = None
    _agent_registry = None


def get_agent_registry(
    gateway: Annotated[AIGateway, Depends(get_ai_gateway)]
) -> AgentRegistry:
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry(gateway=gateway)
    return _agent_registry


def get_user_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


def get_mindquest_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SQLAlchemyMindQuestRepository:
    return SQLAlchemyMindQuestRepository(session)


def get_evaluation_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SQLAlchemyEvaluationRepository:
    return SQLAlchemyEvaluationRepository(session)


def get_activity_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SQLAlchemyUserActivityRepository:
    return SQLAlchemyUserActivityRepository(session)


def get_evaluation_service(
    settings: Annotated[Settings, Depends(get_settings)],
    gateway: Annotated[AIGateway, Depends(get_ai_gateway)],
    evaluation_repo: Annotated[SQLAlchemyEvaluationRepository, Depends(get_evaluation_repo)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
) -> EvaluationService:
    if settings.jev_enabled and (not settings.jev_api_key or not settings.jev_base_url):
        raise ValueError("JEV_API_KEY and JEV_BASE_URL are required when JEV_ENABLED=true.")
    verifier = (
        JevClient(
            api_key=settings.jev_api_key,
            base_url=settings.jev_base_url,
            timeout=settings.jev_timeout_seconds,
        )
        if settings.jev_enabled
        else DisabledDecisionVerifier()
    )
    return EvaluationService(
        gateway=gateway,
        evaluation_repo=evaluation_repo,
        activity_repo=activity_repo,
        decision_verifier=verifier,
    )


def get_turn_service(
    mindquest_repo: Annotated[SQLAlchemyMindQuestRepository, Depends(get_mindquest_repo)],
    evaluation_service: Annotated[EvaluationService, Depends(get_evaluation_service)],
    agent_registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
    prefetch_cache: Annotated[ChallengePrefetchCache, Depends(get_prefetch_cache)],
) -> TurnService:
    return TurnService(
        mindquest_repo=mindquest_repo,
        evaluation_service=evaluation_service,
        agent_registry=agent_registry,
        activity_repo=activity_repo,
        prefetch_cache=prefetch_cache,
    )


def get_mindquest_service(
    mindquest_repo: Annotated[SQLAlchemyMindQuestRepository, Depends(get_mindquest_repo)],
    evaluation_repo: Annotated[SQLAlchemyEvaluationRepository, Depends(get_evaluation_repo)],
    turn_service: Annotated[TurnService, Depends(get_turn_service)],
    agent_registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
    prefetch_cache: Annotated[ChallengePrefetchCache, Depends(get_prefetch_cache)],
) -> MindQuestService:
    return MindQuestService(
        mindquest_repo=mindquest_repo,
        evaluation_repo=evaluation_repo,
        turn_service=turn_service,
        agent_registry=agent_registry,
        activity_repo=activity_repo,
        prefetch_cache=prefetch_cache,
    )


def get_learning_service(
    mindquest_repo: Annotated[SQLAlchemyMindQuestRepository, Depends(get_mindquest_repo)],
    evaluation_repo: Annotated[SQLAlchemyEvaluationRepository, Depends(get_evaluation_repo)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
) -> LearningService:
    return LearningService(
        mindquest_repo=mindquest_repo,
        evaluation_repo=evaluation_repo,
        activity_repo=activity_repo,
    )
