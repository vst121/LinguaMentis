"""Evaluation application service.

Per Architecture.md #18/#34: Executes Thinking and German evaluations in
parallel using ``asyncio.gather``, applies deterministic domain score
formulas, generates structured feedback, persists evaluations and evidence,
and logs user activities.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from uuid import UUID

from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.models import HatFeedback
from linguamentis.domain.evaluations.evidence import Correction, Evidence
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.hats.contracts import get_hat_contract
from linguamentis.domain.mindquests.entities import Turn
from linguamentis.domain.mindquests.enums import ActivityType
from linguamentis.domain.mindquests.value_objects import MindQuestContext
from linguamentis.infrastructure.database.repositories.activity_repository import (
    UserActivityRepository,
)
from linguamentis.infrastructure.database.repositories.evaluation_repository import (
    EvaluationRepository,
)
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class EvaluationResult:
    thinking: ThinkingEvaluation
    german: GermanEvaluation
    feedback: HatFeedback


class EvaluationService:
    def __init__(
        self,
        gateway: AIGateway,
        evaluation_repo: EvaluationRepository,
        activity_repo: UserActivityRepository,
    ) -> None:
        self._gateway = gateway
        self._evaluation_repo = evaluation_repo
        self._activity_repo = activity_repo

    async def evaluate_turn_response(
        self,
        *,
        user_id: UUID,
        turn: Turn,
        context: MindQuestContext,
        user_response: str,
    ) -> EvaluationResult:
        """Run parallel evaluations for Thinking Quality and German Quality."""
        contract = get_hat_contract(context.current_hat)

        # Execute Thinking & German evaluation in parallel (Architecture.md #34)
        thinking_task = self._gateway.evaluate_thinking(
            contract=contract,
            context=context,
            challenge_question=turn.challenge_question,
            user_response=user_response,
        )
        german_task = self._gateway.evaluate_german(
            target_level=str(context.target_level),
            topic=context.topic,
            user_response=user_response,
        )

        thinking_out, german_out = await asyncio.gather(thinking_task, german_task)

        # Map Thinking output -> domain ThinkingEvaluation
        thinking_eval = ThinkingEvaluation(
            id=uuid.uuid4(),
            turn_id=turn.id,
            hat_adherence=thinking_out.hat_adherence,
            relevance=thinking_out.relevance,
            reasoning=thinking_out.reasoning,
            depth=thinking_out.depth,
            specificity=thinking_out.specificity,
            evidence=[
                Evidence(dimension=e.dimension, observation=e.observation, impact=e.impact)
                for e in thinking_out.evidence
            ],
            strengths=thinking_out.strengths,
            weaknesses=thinking_out.weaknesses,
            recommendations=thinking_out.recommendations,
        )

        # Map German output -> domain GermanEvaluation
        german_eval = GermanEvaluation(
            id=uuid.uuid4(),
            turn_id=turn.id,
            grammar=german_out.grammar,
            vocabulary=german_out.vocabulary,
            sentence_structure=german_out.sentence_structure,
            naturalness=german_out.naturalness,
            level_appropriateness=german_out.level_appropriateness,
            evidence=[
                Evidence(dimension=e.dimension, observation=e.observation, impact=e.impact)
                for e in german_out.evidence
            ],
            corrections=[
                Correction(
                    original=c.original,
                    corrected=c.corrected,
                    explanation=c.explanation,
                    category=c.category,
                )
                for c in german_out.corrections
            ],
            strengths=german_out.strengths,
            weaknesses=german_out.weaknesses,
            recommendations=german_out.recommendations,
        )

        # Generate structured HatFeedback (Thinking feedback first, then German)
        thinking_summary = f"Score: {thinking_eval.score}/100 ({thinking_eval.score_anchor()}). " \
                    f"Strengths: {', '.join(thinking_eval.strengths)}"
        
        german_summary = f"Score: {german_eval.score}/100 ({german_eval.score_anchor()}). " \
                    f"Strengths: {', '.join(german_eval.strengths)}"

        feedback = await self._gateway.generate_feedback(
            challenge_question=turn.challenge_question,
            user_response=user_response,
            thinking_summary=thinking_summary,
            german_summary=german_summary,
        )

        # Persist evaluations & log activities
        await self._evaluation_repo.save_thinking(thinking_eval)
        await self._evaluation_repo.save_german(german_eval)

        await self._activity_repo.log_activity(
            user_id=user_id,
            activity_type=ActivityType.THINKING_EVALUATED,
            mindquest_id=context.mindquest_id,
            payload={"turn_id": str(turn.id), "score": thinking_eval.score},
        )
        await self._activity_repo.log_activity(
            user_id=user_id,
            activity_type=ActivityType.GERMAN_EVALUATED,
            mindquest_id=context.mindquest_id,
            payload={"turn_id": str(turn.id), "score": german_eval.score},
        )

        logger.info(
            "application.evaluation.completed",
            turn_id=str(turn.id),
            thinking_score=thinking_eval.score,
            german_score=german_eval.score,
        )

        return EvaluationResult(
            thinking=thinking_eval,
            german=german_eval,
            feedback=feedback,
        )
