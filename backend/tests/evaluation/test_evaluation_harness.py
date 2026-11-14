"""AI Evaluation Harness (Architecture.md #42-#44).

- Default run (`uv run pytest`): validates dataset schema, independent Thinking vs. German
  scoring invariants, and HatContract alignment without making external LLM calls.
- Live evaluation mode (`RUN_AI_EVALUATION=1 uv run pytest -m evaluation`): executes the
  benchmark cases against the live configured Gemini model via AIGateway.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest

from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.gemini import GeminiClient
from linguamentis.domain.evaluations.german import compute_german_score
from linguamentis.domain.evaluations.thinking import compute_thinking_score
from linguamentis.domain.hats.contracts import get_hat_contract
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.value_objects import MindQuestContext
from linguamentis.infrastructure.configuration import get_settings

DATASET_PATH = Path(__file__).parent / "datasets" / "regression_cases.json"


def _load_cases() -> list[dict]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_evaluation_dataset_schema_and_independence_invariants():
    cases = _load_cases()
    assert len(cases) >= 2

    for case in cases:
        hat = HatType(case["hat"])
        contract = get_hat_contract(hat)
        assert contract.hat == hat

        t_score = compute_thinking_score(**case["reference_thinking"])
        g_score = compute_german_score(**case["reference_german"])

        if "expected_thinking_min" in case:
            assert t_score >= case["expected_thinking_min"]
        if "expected_thinking_max" in case:
            assert t_score <= case["expected_thinking_max"]
        if "expected_german_min" in case:
            assert g_score >= case["expected_german_min"]
        if "expected_german_max" in case:
            assert g_score <= case["expected_german_max"]

        # Principle check: Thinking score and German score are independent
        assert t_score != g_score


@pytest.mark.evaluation
@pytest.mark.asyncio
async def test_live_gemini_evaluation_regression_harness():
    if os.getenv("RUN_AI_EVALUATION") != "1":
        pytest.skip("Set RUN_AI_EVALUATION=1 to run live Gemini evaluation harness.")

    settings = get_settings()
    client = GeminiClient(settings)
    gateway = AIGateway(client=client, settings=settings)

    try:
        for case in _load_cases():
            hat = HatType(case["hat"])
            contract = get_hat_contract(hat)
            context = MindQuestContext(
                mindquest_id=uuid4(),
                topic=case["topic"],
                target_level=case["target_level"],
                current_hat=hat,
                current_turn_number=1,
            )
            t_out = await gateway.evaluate_thinking(
                contract=contract,
                context=context,
                challenge_question=case["challenge_question"],
                user_response=case["user_response"],
            )
            g_out = await gateway.evaluate_german(
                target_level=case["target_level"],
                topic=case["topic"],
                user_response=case["user_response"],
            )

            t_score = compute_thinking_score(
                hat_adherence=t_out.hat_adherence,
                relevance=t_out.relevance,
                reasoning=t_out.reasoning,
                depth=t_out.depth,
                specificity=t_out.specificity,
            )
            g_score = compute_german_score(
                grammar=g_out.grammar,
                vocabulary=g_out.vocabulary,
                sentence_structure=g_out.sentence_structure,
                naturalness=g_out.naturalness,
                level_appropriateness=g_out.level_appropriateness,
            )
            assert len(t_out.evidence) > 0
            assert len(g_out.evidence) > 0
            if "expected_thinking_min" in case:
                assert t_score >= case["expected_thinking_min"]
            if "expected_thinking_max" in case:
                assert t_score <= case["expected_thinking_max"]
            if "expected_german_min" in case:
                assert g_score >= case["expected_german_min"]
            if "expected_german_max" in case:
                assert g_score <= case["expected_german_max"]
    finally:
        await client.aclose()
