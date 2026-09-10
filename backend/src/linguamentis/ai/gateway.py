"""AI Gateway.

Per Architecture.md #3/#22: all LLM communication is isolated behind this
capability-oriented facade. Agents and evaluators call ``AIGateway``
methods; they never see ``LLMClient`` or model name configuration
directly. This is also where per-capability model selection happens
(Architecture.md #23 — models must be independently configurable).
"""

from __future__ import annotations

from linguamentis.ai import prompts
from linguamentis.ai.client import LLMClient
from linguamentis.ai.models import (
    FinalReflectionOutput,
    GermanEvaluationOutput,
    HatChallenge,
    HatFeedback,
    ThinkingEvaluationOutput,
)
from linguamentis.domain.hats.contracts import HatContract
from linguamentis.domain.mindquests.value_objects import MindQuestContext
from linguamentis.infrastructure.configuration import Settings
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)


class AIGateway:
    """Facade exposing one method per AI capability used in the product."""

    def __init__(self, client: LLMClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    # -- Hat challenge generation ------------------------------------------

    async def generate_hat_challenge(
        self, *, contract: HatContract, context: MindQuestContext
    ) -> HatChallenge:
        model = self._settings.ai_model_hat
        result = await self._client.generate_structured(
            system_prompt=prompts.hat_challenge_system_prompt(contract),
            user_prompt=prompts.hat_challenge_user_prompt(context),
            response_model=HatChallenge,
            model=model,
            temperature=0.6,
        )
        logger.info(
            "ai.hat_challenge.generated",
            hat=contract.hat.value,
            mindquest_id=str(context.mindquest_id),
            model=model,
            difficulty=result.difficulty,
        )
        return result

    # -- Evaluation ----------------------------------------------------

    async def evaluate_thinking(
        self,
        *,
        contract: HatContract,
        context: MindQuestContext,
        challenge_question: str,
        user_response: str,
    ) -> ThinkingEvaluationOutput:
        model = self._settings.ai_model_thinking_evaluator
        result = await self._client.generate_structured(
            system_prompt=prompts.thinking_evaluation_system_prompt(contract),
            user_prompt=prompts.thinking_evaluation_user_prompt(
                context=context,
                challenge_question=challenge_question,
                user_response=user_response,
            ),
            response_model=ThinkingEvaluationOutput,
            model=model,
            temperature=0.2,
        )
        logger.info(
            "ai.thinking_evaluation.generated",
            hat=contract.hat.value,
            mindquest_id=str(context.mindquest_id),
            model=model,
        )
        return result

    async def evaluate_german(
        self, *, target_level: str, topic: str, user_response: str
    ) -> GermanEvaluationOutput:
        model = self._settings.ai_model_german_evaluator
        result = await self._client.generate_structured(
            system_prompt=prompts.german_evaluation_system_prompt(),
            user_prompt=prompts.german_evaluation_user_prompt(
                target_level=target_level, topic=topic, user_response=user_response
            ),
            response_model=GermanEvaluationOutput,
            model=model,
            temperature=0.2,
        )
        logger.info("ai.german_evaluation.generated", model=model)
        return result

    # -- Feedback ---------------------------------------------------------

    async def generate_feedback(
        self,
        *,
        challenge_question: str,
        user_response: str,
        thinking_summary: str,
        german_summary: str,
    ) -> HatFeedback:
        model = self._settings.ai_model_hat
        return await self._client.generate_structured(
            system_prompt=prompts.hat_feedback_system_prompt(),
            user_prompt=prompts.hat_feedback_user_prompt(
                challenge_question=challenge_question,
                user_response=user_response,
                thinking_summary=thinking_summary,
                german_summary=german_summary,
            ),
            response_model=HatFeedback,
            model=model,
            temperature=0.5,
        )

    # -- Final reflection (Blue Agent) -------------------------------------

    async def generate_final_reflection(
        self,
        *,
        topic: str,
        target_level: str,
        hat_summaries: str,
        previous_mindquest_summary: str = "(no previous MindQuests)",
    ) -> FinalReflectionOutput:
        model = self._settings.ai_model_reflection
        result = await self._client.generate_structured(
            system_prompt=prompts.final_reflection_system_prompt(),
            user_prompt=prompts.final_reflection_user_prompt(
                topic=topic,
                target_level=target_level,
                hat_summaries=hat_summaries,
                previous_mindquest_summary=previous_mindquest_summary,
            ),
            response_model=FinalReflectionOutput,
            model=model,
            temperature=0.5,
        )
        logger.info("ai.final_reflection.generated", model=model)
        return result
