"""Turn application service.

Coordinates submitting responses, triggering evaluation, generating feedback,
and determining next turn challenge within a hat round.
"""

from __future__ import annotations

from dataclasses import dataclass

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.models import HatChallenge, HatFeedback
from linguamentis.application.evaluation.service import EvaluationResult, EvaluationService
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
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
    ) -> None:
        self._mindquest_repo = mindquest_repo
        self._evaluation_service = evaluation_service
        self._agent_registry = agent_registry
        self._activity_repo = activity_repo

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
            payload={"turn_id": str(latest_turn.id), "hat": mindquest.current_hat.value},
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

        # Evaluate turn response
        eval_result: EvaluationResult = await self._evaluation_service.evaluate_turn_response(
            user_id=mindquest.user_id,
            turn=latest_turn,
            context=context,
            user_response=user_response,
        )

        # Check if the hat round has reached completion threshold
        thinking_score = eval_result.thinking.score
        turn_count = len(active_round.turns)

        round_should_complete = (
            thinking_score >= COMPLETION_SCORE_THRESHOLD
            or turn_count >= MAX_TURNS_PER_HAT_ROUND
        )

        next_challenge: HatChallenge | None = None
        if not round_should_complete:
            # Generate next challenge in the same hat round
            agent = self._agent_registry.get(active_round.hat)
            # Update context to include the turn just answered
            updated_previous = list(previous_turn_contexts) + [
                TurnContext(
                    hat=latest_turn.hat,
                    challenge_question=latest_turn.challenge_question,
                    user_response=user_response,
                    thinking_score=eval_result.thinking.score,
                    german_score=eval_result.german.score,
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
            next_challenge = await agent.create_challenge(updated_context)

            # Create new Turn on active round
            active_round.add_turn(
                challenge_question=next_challenge.question,
                challenge_instruction=next_challenge.instruction,
                difficulty=next_challenge.difficulty,
            )

        await self._mindquest_repo.save(mindquest)

        return TurnSubmissionResult(
            turn=latest_turn,
            thinking_evaluation=eval_result.thinking,
            german_evaluation=eval_result.german,
            feedback=eval_result.feedback,
            next_challenge=next_challenge,
            round_should_complete=round_should_complete,
        )
