"""Unit tests for AIGateway, prompt builders, and Jev decision verifier."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest

from linguamentis.ai import prompts
from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.jev import DisabledDecisionVerifier, JevClient
from linguamentis.domain.hats.contracts import get_hat_contract
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.value_objects import MindQuestContext, TurnContext
from linguamentis.infrastructure.configuration import Settings


@pytest.mark.asyncio
async def test_ai_gateway_uses_configured_capability_models(fake_llm_client):
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        gemini_api_key="test-key",
        ai_model_hat="model-hat-v1",
        ai_model_thinking_evaluator="model-thinking-v1",
        ai_model_german_evaluator="model-german-v1",
        ai_model_reflection="model-reflection-v1",
    )
    gateway = AIGateway(client=fake_llm_client, settings=settings)  # type: ignore[arg-type]
    contract = get_hat_contract(HatType.BLACK)
    context = MindQuestContext(
        mindquest_id=uuid4(),
        topic="Atomkraft in Europa",
        target_level="C1",
        current_hat=HatType.BLACK,
        current_turn_number=1,
    )

    await gateway.generate_hat_challenge(contract=contract, context=context)
    assert fake_llm_client.calls[-1]["model"] == "model-hat-v1"
    assert fake_llm_client.calls[-1]["temperature"] == 0.6

    await gateway.evaluate_thinking(
        contract=contract,
        context=context,
        challenge_question="Welche Risiken?",
        user_response="Atommüll ist schwer zu lagern.",
    )
    assert fake_llm_client.calls[-1]["model"] == "model-thinking-v1"
    assert fake_llm_client.calls[-1]["temperature"] == 0.2

    await gateway.evaluate_german(
        target_level="C1",
        topic="Atomkraft in Europa",
        user_response="Atommüll ist schwer zu lagern.",
    )
    assert fake_llm_client.calls[-1]["model"] == "model-german-v1"
    assert fake_llm_client.calls[-1]["temperature"] == 0.2

    await gateway.generate_feedback(
        challenge_question="Welche Risiken?",
        user_response="Atommüll ist schwer zu lagern.",
        thinking_summary="Strong risk focus",
        german_summary="Good C1 structure",
    )
    assert fake_llm_client.calls[-1]["model"] == "model-hat-v1"
    assert fake_llm_client.calls[-1]["temperature"] == 0.5

    await gateway.generate_final_reflection(
        topic="Atomkraft in Europa",
        target_level="C1",
        hat_summaries="Hat BLACK: ...",
    )
    assert fake_llm_client.calls[-1]["model"] == "model-reflection-v1"
    assert fake_llm_client.calls[-1]["temperature"] == 0.5


def test_prompts_include_contract_context_and_previous_turns():
    from linguamentis.domain.mindquests.value_objects import Topic

    with pytest.raises(ValueError, match="must not be empty"):
        Topic("   ")
    with pytest.raises(ValueError, match="must not exceed 500"):
        Topic("x" * 501)
    assert Topic("Mobilität der Zukunft").text == "Mobilität der Zukunft"

    contract = get_hat_contract(HatType.GREEN)
    prev = (
        TurnContext(
            hat=HatType.GREEN,
            challenge_question="Welche neuen Ansätze gibt es?",
            user_response="Wir könnten autofreie Sonntage einführen.",
            thinking_score=78,
            german_score=84,
        ),
    )
    context = MindQuestContext(
        mindquest_id=uuid4(),
        topic="Mobilität der Zukunft",
        target_level="B2",
        current_hat=HatType.GREEN,
        current_turn_number=2,
        completed_hats=(HatType.BLACK,),
        previous_responses=prev,
    )

    sys_prompt = prompts.hat_challenge_system_prompt(contract)
    user_prompt = prompts.hat_challenge_user_prompt(context)
    assert "Green Hat" in sys_prompt
    assert "Mobilität der Zukunft" in user_prompt
    assert "autofreie Sonntage" in user_prompt
    assert "Thinking score: 78" in user_prompt
    assert "BLACK" in user_prompt


@pytest.mark.asyncio
async def test_disabled_decision_verifier_returns_review():
    verifier = DisabledDecisionVerifier()
    decision = await verifier.evaluate_hat_adherence(
        hat="BLACK",
        challenge="Welche Risiken?",
        response="Alles wird super!",
    )
    assert decision.choice == "review"
    assert decision.confidence == 0.0
    assert decision.probabilities == {}


@pytest.mark.asyncio
async def test_jev_client_parses_decision_response(monkeypatch):
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "answers": [
                    {
                        "choice": "adherent",
                        "confidence": 0.94,
                        "probabilities": {"adherent": 0.94, "not_adherent": 0.04, "review": 0.02},
                    }
                ]
            },
        )

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(handler), timeout=kwargs.get("timeout")
        ),
    )

    client = JevClient(api_key="jev-secret", base_url="https://jev.example.com/")
    decision = await client.evaluate_hat_adherence(
        hat="BLACK",
        challenge="Welche Risiken siehst du?",
        response="Die Kosten könnten explodieren.",
    )
    assert captured["url"] == "https://jev.example.com/alpha/decisions"
    assert captured["auth"] == "Bearer jev-secret"
    assert captured["body"]["state"]["hat"] == "BLACK"
    assert decision.choice == "adherent"
    assert decision.confidence == pytest.approx(0.94)
    assert decision.probabilities["adherent"] == pytest.approx(0.94)
