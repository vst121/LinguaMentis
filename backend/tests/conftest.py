"""Pytest fixtures for unit and integration testing.

Per Architecture.md #42:
- Unit tests use in-memory SQLite / fake LLM client and do not make real LLM calls.
- Integration tests test FastAPI endpoints and repositories.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.models import (
    Correction,
    Evidence,
    FinalReflectionOutput,
    GermanEvaluationOutput,
    GermanReflectionSection,
    HatChallenge,
    HatFeedback,
    SpeechTranscriptionOutput,
    ThinkingEvaluationOutput,
    ThinkingReflectionSection,
)
from linguamentis.api.dependencies import get_ai_gateway
from linguamentis.domain.hats.types import HatType
from linguamentis.infrastructure.configuration import Settings, get_settings
from linguamentis.infrastructure.database.models import Base
from linguamentis.infrastructure.database.repositories import (
    SQLAlchemyUserRepository,
)
from linguamentis.infrastructure.database.session import get_db_session
from linguamentis.main import app


class FakeLLMClient:
    """Mock LLM client returning deterministic structured objects for testing."""

    def __init__(self, *, simulated_delay_seconds: float = 0.0) -> None:
        self.queued_responses: dict[type, list[object]] = {}
        self.error_to_raise: Exception | None = None
        self.calls: list[dict[str, object]] = []
        self.simulated_delay_seconds = simulated_delay_seconds

    def queue_response(self, response_model: type, *items: object) -> None:
        self.queued_responses.setdefault(response_model, []).extend(items)

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type,
        model: str,
        temperature: float = 0.4,
    ):
        import asyncio

        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_model": response_model,
                "model": model,
                "temperature": temperature,
            }
        )
        if self.simulated_delay_seconds > 0:
            await asyncio.sleep(self.simulated_delay_seconds)
        if self.error_to_raise is not None:
            raise self.error_to_raise

        queued = self.queued_responses.get(response_model)
        if queued:
            return queued.pop(0)

        if response_model is HatChallenge:
            return HatChallenge(
                question="Welche Risiken siehst du bei diesem Vorhaben?",
                instruction="Bleib beim Black Hat: Konzentriere dich nur auf Risiken.",
                expected_thinking_mode=HatType.BLACK,
                difficulty=3,
                rationale="Testing rationale",
            )

        if response_model is ThinkingEvaluationOutput:
            return ThinkingEvaluationOutput(
                hat_adherence=85,
                relevance=80,
                reasoning=90,
                depth=75,
                specificity=80,
                evidence=[
                    Evidence(
                        dimension="hat_adherence",
                        observation="Learner identified a genuine risk.",
                        impact="Stuck to Black Hat.",
                    )
                ],
                strengths=["Good critical reasoning"],
                weaknesses=["Could be more specific"],
                recommendations=["Provide concrete numbers"],
            )

        if response_model is GermanEvaluationOutput:
            return GermanEvaluationOutput(
                grammar=85,
                vocabulary=80,
                sentence_structure=85,
                naturalness=75,
                level_appropriateness=85,
                evidence=[
                    Evidence(
                        dimension="grammar",
                        observation="Correct Nebensatz word order.",
                        impact="Shows B2 control.",
                    )
                ],
                corrections=[
                    Correction(
                        original="das ist gut idea",
                        corrected="das ist eine gute Idee",
                        explanation="Gender and article missing.",
                        category="grammar",
                    )
                ],
                strengths=["Clear sentence structure"],
                weaknesses=["Minor article mistakes"],
                recommendations=["Focus on noun gender"],
            )

        if response_model is HatFeedback:
            return HatFeedback(
                thinking_feedback="Good analysis of risks.",
                german_feedback="Clear German expression with minor grammar errors.",
                encouragement="Keep going!",
            )

        if response_model is FinalReflectionOutput:
            return FinalReflectionOutput(
                thinking=ThinkingReflectionSection(
                    overall_summary="Strong critical thinking demonstrated across all hats.",
                    strongest_thinking_modes=["BLACK"],
                    weakest_thinking_modes=["GREEN"],
                    key_reasoning_patterns=["Causal risk analysis"],
                    recommendations=["Explore more unconventional ideas"],
                ),
                german=GermanReflectionSection(
                    overall_summary="Solid B2 control throughout the debate.",
                    grammar_strengths=["Subordinate clauses"],
                    vocabulary_notes=["Good topic vocabulary"],
                    naturalness_notes=["Slightly formal"],
                    important_corrections=[],
                    recommended_expressions=["Meiner Ansicht nach"],
                    level_recommendations=["Practice C1 passive voice"],
                ),
                closing_message="Ausgezeichnete Leistung!",
            )

        if response_model is SpeechTranscriptionOutput:
            return SpeechTranscriptionOutput(
                text="Meiner Ansicht nach überwiegen hier die langfristigen Risiken."
            )

        raise ValueError(f"Unsupported response_model in FakeLLMClient: {response_model}")

    async def transcribe_audio(
        self,
        *,
        audio_base64: str,
        mime_type: str,
        model: str,
    ) -> SpeechTranscriptionOutput:
        return await self.generate_structured(
            system_prompt="transcribe",
            user_prompt=f"{mime_type}:{len(audio_base64)}",
            response_model=SpeechTranscriptionOutput,
            model=model,
            temperature=0.1,
        )


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        gemini_api_key="fake-key",
        default_user_id=UUID("00000000-0000-0000-0000-000000000001"),
    )


@pytest_asyncio.fixture
async def db_engine(test_settings: Settings):
    engine = create_async_engine(
        test_settings.database_url, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def fake_llm_client() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
def fake_gateway(test_settings: Settings, fake_llm_client: FakeLLMClient) -> AIGateway:
    return AIGateway(client=fake_llm_client, settings=test_settings)  # type: ignore[arg-type]


@pytest.fixture
def agent_registry(fake_gateway: AIGateway) -> AgentRegistry:
    return AgentRegistry(gateway=fake_gateway)


@pytest_asyncio.fixture
async def async_client(
    test_settings: Settings, fake_gateway: AIGateway, db_engine
) -> AsyncGenerator[AsyncClient, None]:
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def _override_get_settings() -> Settings:
        return test_settings

    def _override_get_ai_gateway() -> AIGateway:
        return fake_gateway

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_settings] = _override_get_settings
    app.dependency_overrides[get_ai_gateway] = _override_get_ai_gateway

    # Ensure default user is seeded in test DB
    async with factory() as session:
        user_repo = SQLAlchemyUserRepository(session)
        await user_repo.ensure_default_user(test_settings.default_user_id)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
