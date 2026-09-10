"""FastAPI dependency injection wiring.

Per Architecture.md #7: API layer delegates HTTP concerns and injects application services.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.openrouter import OpenRouterClient
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.learning.service import LearningService
from linguamentis.application.mindquests.service import MindQuestService
from linguamentis.application.turns.service import TurnService
from linguamentis.infrastructure.configuration import Settings, get_settings
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyUserActivityRepository,
    SQLAlchemyEvaluationRepository,
    SQLAlchemyMindQuestRepository,
    SQLAlchemyUserRepository,
)
from linguamentis.infrastructure.database.session import get_db_session

# Singleton AI Gateway reuse
_ai_gateway: AIGateway | None = None
_agent_registry: AgentRegistry | None = None


def get_ai_gateway(
    settings: Annotated[Settings, Depends(get_settings)]
) -> AIGateway:
    global _ai_gateway
    if _ai_gateway is None:
        client = OpenRouterClient(settings)
        _ai_gateway = AIGateway(client=client, settings=settings)
    return _ai_gateway


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
    gateway: Annotated[AIGateway, Depends(get_ai_gateway)],
    evaluation_repo: Annotated[SQLAlchemyEvaluationRepository, Depends(get_evaluation_repo)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
) -> EvaluationService:
    return EvaluationService(
        gateway=gateway,
        evaluation_repo=evaluation_repo,
        activity_repo=activity_repo,
    )


def get_turn_service(
    mindquest_repo: Annotated[SQLAlchemyMindQuestRepository, Depends(get_mindquest_repo)],
    evaluation_service: Annotated[EvaluationService, Depends(get_evaluation_service)],
    agent_registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
) -> TurnService:
    return TurnService(
        mindquest_repo=mindquest_repo,
        evaluation_service=evaluation_service,
        agent_registry=agent_registry,
        activity_repo=activity_repo,
    )


def get_mindquest_service(
    mindquest_repo: Annotated[SQLAlchemyMindQuestRepository, Depends(get_mindquest_repo)],
    evaluation_repo: Annotated[SQLAlchemyEvaluationRepository, Depends(get_evaluation_repo)],
    turn_service: Annotated[TurnService, Depends(get_turn_service)],
    agent_registry: Annotated[AgentRegistry, Depends(get_agent_registry)],
    activity_repo: Annotated[SQLAlchemyUserActivityRepository, Depends(get_activity_repo)],
) -> MindQuestService:
    return MindQuestService(
        mindquest_repo=mindquest_repo,
        evaluation_repo=evaluation_repo,
        turn_service=turn_service,
        agent_registry=agent_registry,
        activity_repo=activity_repo,
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
