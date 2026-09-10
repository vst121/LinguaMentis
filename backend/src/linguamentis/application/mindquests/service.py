"""MindQuest application service and engine.

Per Architecture.md #12: MindQuestEngine coordinates the complete MindQuest
lifecycle using the deterministic state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.models import HatChallenge
from linguamentis.application.turns.service import TurnService, TurnSubmissionResult
from linguamentis.domain.hats.types import DEFAULT_HAT_SEQUENCE, HatType
from linguamentis.domain.mindquests.entities import MindQuest, Turn
from linguamentis.domain.mindquests.enums import (
    ActivityType,
    LanguageLevel,
    MindQuestStatus,
)
from linguamentis.domain.mindquests.value_objects import MindQuestContext
from linguamentis.infrastructure.database.repositories.activity_repository import (
    UserActivityRepository,
)
from linguamentis.infrastructure.database.repositories.evaluation_repository import (
    EvaluationRepository,
    FinalReflection,
)
from linguamentis.infrastructure.database.repositories.mindquest_repository import (
    MindQuestRepository,
)
from linguamentis.shared.exceptions import DomainError, NotFoundError
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class StartMindQuestResult:
    mindquest: MindQuest
    active_hat: HatType
    initial_turn: Turn
    challenge: HatChallenge


@dataclass(slots=True)
class AdvanceMindQuestResult:
    mindquest: MindQuest
    next_hat: HatType | None
    initial_turn: Turn | None
    challenge: HatChallenge | None
    is_completed: bool
    final_reflection: FinalReflection | None = None


class MindQuestService:
    def __init__(
        self,
        mindquest_repo: MindQuestRepository,
        evaluation_repo: EvaluationRepository,
        turn_service: TurnService,
        agent_registry: AgentRegistry,
        activity_repo: UserActivityRepository,
    ) -> None:
        self._mindquest_repo = mindquest_repo
        self._evaluation_repo = evaluation_repo
        self._turn_service = turn_service
        self._agent_registry = agent_registry
        self._activity_repo = activity_repo

    async def create_mindquest(
        self,
        *,
        user_id: UUID,
        topic: str,
        target_level: LanguageLevel = LanguageLevel.B2,
        planned_hats: tuple[HatType, ...] = DEFAULT_HAT_SEQUENCE,
    ) -> MindQuest:
        import uuid

        mq = MindQuest(
            id=uuid.uuid4(),
            user_id=user_id,
            topic=topic,
            target_level=target_level,
        )
        mq.select_topic(topic, planned_hats)
        await self._mindquest_repo.save(mq)

        await self._activity_repo.log_activity(
            user_id=user_id,
            activity_type=ActivityType.MINDQUEST_STARTED,
            mindquest_id=mq.id,
            payload={"topic": topic, "target_level": target_level.value},
        )
        return mq

    async def get_mindquest(self, mindquest_id: UUID) -> MindQuest:
        mq = await self._mindquest_repo.get_by_id(mindquest_id)
        if mq is None:
            raise NotFoundError("MindQuest", mindquest_id)
        return mq

    async def list_user_mindquests(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[MindQuest]:
        return await self._mindquest_repo.list_by_user(user_id, limit=limit, offset=offset)

    async def start_mindquest(self, mindquest_id: UUID) -> StartMindQuestResult:
        """Begin MindQuest progress and activate the first hat round."""
        mq = await self.get_mindquest(mindquest_id)

        if mq.status == MindQuestStatus.CREATED:
            mq.select_topic(mq.topic, mq.planned_hats or DEFAULT_HAT_SEQUENCE)

        if mq.status == MindQuestStatus.TOPIC_SELECTED:
            mq.begin()

        if mq.status != MindQuestStatus.IN_PROGRESS:
            raise DomainError(
                f"Cannot start MindQuest in status '{mq.status.value}'. Expected IN_PROGRESS."
            )

        first_hat = mq.planned_hats[0] if mq.planned_hats else HatType.BLACK
        active_round = mq.activate_hat(first_hat)

        # Generate initial challenge for first hat
        context = MindQuestContext(
            mindquest_id=mq.id,
            topic=mq.topic,
            target_level=mq.target_level.value,
            current_hat=first_hat,
            current_turn_number=1,
            completed_hats=(),
        )

        agent = self._agent_registry.get(first_hat)
        challenge = await agent.create_challenge(context)

        initial_turn = active_round.add_turn(
            challenge_question=challenge.question,
            challenge_instruction=challenge.instruction,
            difficulty=challenge.difficulty,
        )

        await self._mindquest_repo.save(mq)

        await self._activity_repo.log_activity(
            user_id=mq.user_id,
            activity_type=ActivityType.HAT_SELECTED,
            mindquest_id=mq.id,
            payload={"hat": first_hat.value},
        )

        return StartMindQuestResult(
            mindquest=mq,
            active_hat=first_hat,
            initial_turn=initial_turn,
            challenge=challenge,
        )

    async def submit_response(
        self, mindquest_id: UUID, user_response: str
    ) -> TurnSubmissionResult:
        mq = await self.get_mindquest(mindquest_id)
        return await self._turn_service.submit_response(
            mindquest=mq, user_response=user_response
        )

    async def advance_mindquest(self, mindquest_id: UUID) -> AdvanceMindQuestResult:
        """Advance to the next hat in sequence, or finish the MindQuest if all hats done."""
        mq = await self.get_mindquest(mindquest_id)

        if mq.status == MindQuestStatus.HAT_ACTIVE:
            mq.complete_current_hat()

            await self._activity_repo.log_activity(
                user_id=mq.user_id,
                activity_type=ActivityType.HAT_COMPLETED,
                mindquest_id=mq.id,
                payload={"hat": mq.completed_hats[-1].value if mq.completed_hats else ""},
            )

        if mq.all_planned_hats_completed():
            # All hats finished -> transition to final reflection & completion
            mq.finish_all_hats()
            mq.start_final_evaluation()

            # Generate Final Reflection via Blue Agent
            reflection = await self._generate_and_save_final_reflection(mq)
            mq.complete()
            await self._mindquest_repo.save(mq)

            await self._activity_repo.log_activity(
                user_id=mq.user_id,
                activity_type=ActivityType.MINDQUEST_COMPLETED,
                mindquest_id=mq.id,
                payload={"completed_hats": [h.value for h in mq.completed_hats]},
            )

            return AdvanceMindQuestResult(
                mindquest=mq,
                next_hat=None,
                initial_turn=None,
                challenge=None,
                is_completed=True,
                final_reflection=reflection,
            )
        else:
            # Activate next hat in sequence
            next_hat = mq.remaining_planned_hats[0]
            active_round = mq.activate_hat(next_hat)

            context = MindQuestContext(
                mindquest_id=mq.id,
                topic=mq.topic,
                target_level=mq.target_level.value,
                current_hat=next_hat,
                current_turn_number=1,
                completed_hats=mq.completed_hats,
            )

            agent = self._agent_registry.get(next_hat)
            challenge = await agent.create_challenge(context)

            initial_turn = active_round.add_turn(
                challenge_question=challenge.question,
                challenge_instruction=challenge.instruction,
                difficulty=challenge.difficulty,
            )

            await self._mindquest_repo.save(mq)

            await self._activity_repo.log_activity(
                user_id=mq.user_id,
                activity_type=ActivityType.HAT_SELECTED,
                mindquest_id=mq.id,
                payload={"hat": next_hat.value},
            )

            return AdvanceMindQuestResult(
                mindquest=mq,
                next_hat=next_hat,
                initial_turn=initial_turn,
                challenge=challenge,
                is_completed=False,
            )

    async def get_final_reflection(self, mindquest_id: UUID) -> FinalReflection | None:
        return await self._evaluation_repo.get_final_reflection(mindquest_id)

    async def _generate_and_save_final_reflection(
        self, mq: MindQuest
    ) -> FinalReflection:
        import uuid

        # Collect hat summaries
        hat_summaries_list = []
        for r in mq.hat_rounds:
            turns_text = "\n".join(
                f"  Turn {t.turn_number}: {t.challenge_question} -> {t.user_response}"
                for t in r.turns
                if t.user_response
            )
            hat_summaries_list.append(f"Hat {r.hat.value}:\n{turns_text}")
        hat_summaries_str = "\n\n".join(hat_summaries_list)

        blue_agent = self._agent_registry.blue
        reflection_out = await blue_agent.generate_final_reflection(
            topic=mq.topic,
            target_level=mq.target_level.value,
            hat_summaries=hat_summaries_str,
        )

        reflection = FinalReflection(
            id=uuid.uuid4(),
            mindquest_id=mq.id,
            thinking_summary=reflection_out.thinking.overall_summary,
            german_summary=reflection_out.german.overall_summary,
            thinking_section=reflection_out.thinking.model_dump(),
            german_section=reflection_out.german.model_dump(),
            closing_message=reflection_out.closing_message,
        )
        await self._evaluation_repo.save_final_reflection(reflection)
        return reflection
