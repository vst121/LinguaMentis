"""Turn application service.

Coordinates submitting responses, triggering evaluation, generating feedback,
and determining next turn challenge within a hat round.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.models import HatChallenge, HatFeedback
from linguamentis.application.evaluation.service import EvaluationService
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.entities import MindQuest, Turn
from linguamentis.domain.mindquests.enums import ActivityType, MindQuestStatus
from linguamentis.domain.mindquests.value_objects import MindQuestContext, TurnContext
from linguamentis.infrastructure.database.repositories.activity_repository import (
    UserActivityRepository,
)
from linguamentis.infrastructure.database.repositories.mindquest_repository import (
    MindQuestRepository,
)
from linguamentis.shared.exceptions import DomainError
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)

COMPLETION_SCORE_THRESHOLD = 75
MAX_TURNS_PER_HAT_ROUND = 3


@dataclass(slots=True)
class TurnSubmissionResult:
    turn: Turn
    thinking_evaluation: ThinkingEvaluation
    german_evaluation: GermanEvaluation
    feedback: HatFeedback
    next_challenge: HatChallenge | None
    round_should_complete: bool


class TurnService:
    def __init__(
        self,
        mindquest_repo: MindQuestRepository,
        evaluation_service: EvaluationService,
        agent_registry: AgentRegistry,
        activity_repo: UserActivityRepository,
        prefetch_cache: ChallengePrefetchCache | None = None,
    ) -> None:
        self._mindquest_repo = mindquest_repo
        self._evaluation_service = evaluation_service
        self._agent_registry = agent_registry
        self._activity_repo = activity_repo
        self._prefetch_cache = prefetch_cache

    async def submit_response(
        self,
        *,
        mindquest: MindQuest,
        user_response: str,
    ) -> TurnSubmissionResult:
        """Submit learner response to the current active turn in the current hat round."""
        if mindquest.status != MindQuestStatus.HAT_ACTIVE:
            raise DomainError(
                f"Cannot submit response when MindQuest status is '{mindquest.status.value}'. "
                "Expected HAT_ACTIVE."
            )

        active_round = mindquest.current_hat_round
        if active_round is None or active_round.is_completed:
            raise DomainError("No active hat round found to accept a response.")

        latest_turn = active_round.latest_turn
        if latest_turn is None or latest_turn.is_answered:
            raise DomainError("No active unanswered turn in current hat round.")

        # Record learner response
        latest_turn.record_response(user_response)
        await self._activity_repo.log_activity(
            user_id=mindquest.user_id,
            activity_type=ActivityType.RESPONSE_SUBMITTED,
            mindquest_id=mindquest.id,
            payload={"turn_id": str(latest_turn.id), "hat": active_round.hat.value},
        )

        # Build MindQuestContext for evaluation and next challenge
        previous_turn_contexts: list[TurnContext] = []
        for t in active_round.turns[:-1]:
            previous_turn_contexts.append(
                TurnContext(
                    hat=t.hat,
                    challenge_question=t.challenge_question,
                    user_response=t.user_response or "",
                )
            )

        context = MindQuestContext(
            mindquest_id=mindquest.id,
            topic=mindquest.topic,
            target_level=mindquest.target_level.value,
            current_hat=active_round.hat,
            current_turn_number=len(active_round.turns),
            completed_hats=mindquest.completed_hats,
            previous_responses=tuple(previous_turn_contexts),
        )

        # Evaluate dimensions first so we immediately know whether another turn is needed
        thinking_eval, german_eval = await self._evaluation_service.evaluate_dimensions(
            turn=latest_turn,
            context=context,
            user_response=user_response,
        )

        # Check if the hat round has reached completion threshold
        thinking_score = thinking_eval.score
        turn_count = len(active_round.turns)

        round_should_complete = (
            thinking_score >= COMPLETION_SCORE_THRESHOLD
            or turn_count >= MAX_TURNS_PER_HAT_ROUND
        )

        feedback_task = self._evaluation_service.generate_feedback(
            challenge_question=latest_turn.challenge_question,
            user_response=user_response,
            thinking_eval=thinking_eval,
            german_eval=german_eval,
        )

        next_challenge: HatChallenge | None = None
        if not round_should_complete:
            # Run feedback generation and next-turn challenge generation in parallel
            agent = self._agent_registry.get(active_round.hat)
            updated_previous = list(previous_turn_contexts) + [
                TurnContext(
                    hat=latest_turn.hat,
                    challenge_question=latest_turn.challenge_question,
                    user_response=user_response,
                    thinking_score=thinking_eval.score,
                    german_score=german_eval.score,
                )
            ]
            updated_context = MindQuestContext(
                mindquest_id=mindquest.id,
                topic=mindquest.topic,
                target_level=mindquest.target_level.value,
                current_hat=active_round.hat,
                current_turn_number=len(active_round.turns) + 1,
                completed_hats=mindquest.completed_hats,
                previous_responses=tuple(updated_previous),
            )
            feedback, follow_up_challenge = await asyncio.gather(
                feedback_task,
                agent.create_challenge(updated_context),
            )
            next_challenge = follow_up_challenge

            # Create new Turn on active round
            active_round.add_turn(
                challenge_question=follow_up_challenge.question,
                challenge_instruction=follow_up_challenge.instruction,
                difficulty=follow_up_challenge.difficulty,
            )
        else:
            # Prefetch the next hat challenge (or final reflection) while feedback is generated/read
            self._schedule_post_round_prefetch(mindquest, active_round.hat)
            feedback = await feedback_task

        await self._evaluation_service.persist_evaluations(
            user_id=mindquest.user_id,
            turn=latest_turn,
            mindquest_id=mindquest.id,
            thinking_eval=thinking_eval,
            german_eval=german_eval,
        )

        await self._mindquest_repo.save(mindquest)

        return TurnSubmissionResult(
            turn=latest_turn,
            thinking_evaluation=thinking_eval,
            german_evaluation=german_eval,
            feedback=feedback,
            next_challenge=next_challenge,
            round_should_complete=round_should_complete,
        )

    def _schedule_post_round_prefetch(
        self, mindquest: MindQuest, completed_hat: HatType
    ) -> None:
        if self._prefetch_cache is None:
            return
        done_after_round = set(mindquest.completed_hats) | {completed_hat}
        remaining = tuple(h for h in mindquest.planned_hats if h not in done_after_round)
        if remaining:
            next_hat = remaining[0]
            next_context = MindQuestContext(
                mindquest_id=mindquest.id,
                topic=mindquest.topic,
                target_level=mindquest.target_level.value,
                current_hat=next_hat,
                current_turn_number=1,
                completed_hats=tuple(
                    [*mindquest.completed_hats, completed_hat]
                ),
            )
            agent = self._agent_registry.get(next_hat)
            self._prefetch_cache.schedule_hat_challenge(
                mindquest.id, next_hat, agent.create_challenge(next_context)
            )
            return

        hat_summaries_list = []
        for r in mindquest.hat_rounds:
            turns_text = "\n".join(
                f"  Turn {t.turn_number}: {t.challenge_question} -> {t.user_response}"
                for t in r.turns
                if t.user_response
            )
            hat_summaries_list.append(f"Hat {r.hat.value}:\n{turns_text}")
        hat_summaries_str = "\n\n".join(hat_summaries_list)

        blue_agent = self._agent_registry.blue
        self._prefetch_cache.schedule_final_reflection(
            mindquest.id,
            blue_agent.generate_final_reflection(
                topic=mindquest.topic,
                target_level=mindquest.target_level.value,
                hat_summaries=hat_summaries_str,
            ),
        )
