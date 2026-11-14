"""MindQuest application service and engine.

Per Architecture.md #12: MindQuestEngine coordinates the complete MindQuest
lifecycle using the deterministic state machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from linguamentis.agents.registry import AgentRegistry
from linguamentis.ai.models import HatChallenge
from linguamentis.application.learning.service import (
    EvaluationMetricsSummary,
    aggregate_evaluation_metrics,
)
from linguamentis.application.mindquests.prefetch import ChallengePrefetchCache
from linguamentis.application.turns.service import (
    TurnService,
    TurnSubmissionResult,
    compute_response_average_score,
)
from linguamentis.domain.evaluations.german import GermanEvaluation
from linguamentis.domain.evaluations.proposition import ResponseProposition
from linguamentis.domain.evaluations.thinking import ThinkingEvaluation
from linguamentis.domain.hats.types import (
    ARGUE_SELECTABLE_HATS,
    DEFAULT_HAT_SEQUENCE,
    HatType,
)
from linguamentis.domain.mindquests.entities import MindQuest, Turn
from linguamentis.domain.mindquests.enums import (
    ActivityType,
    LanguageLevel,
    MindQuestMode,
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


# Instant German opening prompts for Argue Mode so choosing a hat has zero LLM delay
_ARGUE_OPENING_PROMPTS: dict[HatType, tuple[str, str]] = {
    HatType.WHITE: (
        "Welche gesicherten Fakten, Daten oder Wissenslücken sind beim Thema "
        "„{topic}“ entscheidend?",
        "Bleibe objektiv (Weißer Hut): Trenne Fakten klar von Annahmen.",
    ),
    HatType.YELLOW: (
        "Welche konkreten Chancen und positiven Folgen siehst du beim Thema „{topic}“?",
        "Argumentiere konstruktiv (Gelber Hut): Begründe den konkreten Nutzen.",
    ),
    HatType.GREEN: (
        "Welche kreativen Alternativen oder unkonventionellen Ansätze gibt es für „{topic}“?",
        "Denke kreativ (Grüner Hut): Entwickle originelle Möglichkeiten.",
    ),
    HatType.RED: (
        "Welche unmittelbare Intuition oder emotionale Reaktion löst „{topic}“ bei dir aus?",
        "Zeige dein Bauchgefühl (Roter Hut): Beschreibe Eindrücke klar und authentisch.",
    ),
    HatType.BLACK: (
        "Welche konkreten Risiken, Schwächen oder negativen Folgen birgt „{topic}“?",
        "Analysiere kritisch (Schwarzer Hut): Nenne konkrete Gefahren und Folgeeffekte.",
    ),
}


@dataclass(slots=True)
class StartMindQuestResult:
    mindquest: MindQuest
    active_hat: HatType
    initial_turn: Turn
    challenge: HatChallenge
    is_read_only: bool = False
    last_answered_turn: Turn | None = None
    last_thinking_evaluation: ThinkingEvaluation | None = None
    last_german_evaluation: GermanEvaluation | None = None
    last_proposition: ResponseProposition | None = None
    last_average_score: float | None = None


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
        prefetch_cache: ChallengePrefetchCache | None = None,
    ) -> None:
        self._mindquest_repo = mindquest_repo
        self._evaluation_repo = evaluation_repo
        self._turn_service = turn_service
        self._agent_registry = agent_registry
        self._activity_repo = activity_repo
        self._prefetch_cache = prefetch_cache

    async def create_mindquest(
        self,
        *,
        user_id: UUID,
        topic: str,
        target_level: LanguageLevel = LanguageLevel.B2,
        mode: MindQuestMode = MindQuestMode.ANSWERING,
        planned_hats: tuple[HatType, ...] = DEFAULT_HAT_SEQUENCE,
    ) -> MindQuest:
        import uuid

        # Both modes plan all 6 hats (BLUE is always last); Argue Mode allows free choice of first 5
        enforced_hats = DEFAULT_HAT_SEQUENCE

        mq = MindQuest(
            id=uuid.uuid4(),
            user_id=user_id,
            topic=topic,
            target_level=target_level,
            mode=mode,
        )
        mq.select_topic(topic, enforced_hats)
        await self._mindquest_repo.save(mq)

        await self._activity_repo.log_activity(
            user_id=user_id,
            activity_type=ActivityType.MINDQUEST_STARTED,
            mindquest_id=mq.id,
            payload={
                "topic": topic,
                "target_level": target_level.value,
                "mode": mode.value,
            },
        )

        # In Answering Mode, warm the first hat challenge while frontend navigates
        if mode == MindQuestMode.ANSWERING and self._prefetch_cache is not None:
            first_hat = mq.planned_hats[0] if mq.planned_hats else DEFAULT_HAT_SEQUENCE[0]
            first_context = MindQuestContext(
                mindquest_id=mq.id,
                topic=mq.topic,
                target_level=mq.target_level.value,
                current_hat=first_hat,
                current_turn_number=1,
                completed_hats=(),
            )
            agent = self._agent_registry.get(first_hat)
            self._prefetch_cache.schedule_hat_challenge(
                mq.id, first_hat, agent.create_challenge(first_context)
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

    async def delete_mindquest(self, mindquest_id: UUID) -> None:
        deleted = await self._mindquest_repo.delete(mindquest_id)
        if not deleted:
            raise NotFoundError("MindQuest", mindquest_id)

    async def start_mindquest(self, mindquest_id: UUID) -> StartMindQuestResult:
        """Begin MindQuest progress and activate the first hat round."""
        mq = await self.get_mindquest(mindquest_id)

        if mq.mode == MindQuestMode.ARGUE:
            raise DomainError(
                "In Argue Mode, select one of the 5 available hats via select-hat."
            )

        if mq.status == MindQuestStatus.CREATED:
            mq.select_topic(mq.topic, mq.planned_hats or DEFAULT_HAT_SEQUENCE)

        if mq.status == MindQuestStatus.TOPIC_SELECTED:
            mq.begin()

        if mq.status != MindQuestStatus.IN_PROGRESS:
            raise DomainError(
                f"Cannot start MindQuest in status '{mq.status.value}'. Expected IN_PROGRESS."
            )

        first_hat = mq.planned_hats[0] if mq.planned_hats else DEFAULT_HAT_SEQUENCE[0]
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

        # Use speculative prefetched challenge if already generated
        challenge = (
            await self._prefetch_cache.consume_hat_challenge(mq.id, first_hat)
            if self._prefetch_cache is not None
            else None
        )
        if challenge is None:
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

    async def select_hat(
        self, mindquest_id: UUID, hat: HatType
    ) -> StartMindQuestResult:
        """Select or switch to a hat in Argue Mode.

        - The 5 non-BLUE hats can be selected/switched freely at any time.
        - BLUE is always last: rejected until all 5 other hats are completed, then
          generates the Blue Agent synthesis question just like Answering Mode.
        - Completed hats return read-only state & scores.
        """
        mq = await self.get_mindquest(mindquest_id)

        if mq.mode != MindQuestMode.ARGUE:
            raise DomainError("Manual hat selection is only available in Argue Mode.")

        if hat not in DEFAULT_HAT_SEQUENCE:
            raise DomainError(f"Unsupported hat '{hat.value}'.")

        if hat == HatType.BLUE:
            other_hats_done = all(h in mq.completed_hats for h in ARGUE_SELECTABLE_HATS)
            if not other_hats_done:
                raise DomainError(
                    "Der Blaue Hut muss immer als letzter Schritt nach allen anderen "
                    "5 Hüten beantwortet werden."
                )

        if mq.status in (MindQuestStatus.COMPLETED, MindQuestStatus.ABANDONED):
            raise DomainError(
                f"Cannot select a hat when MindQuest status is '{mq.status.value}'."
            )

        if mq.status == MindQuestStatus.CREATED:
            mq.select_topic(mq.topic, mq.planned_hats or DEFAULT_HAT_SEQUENCE)

        if mq.status == MindQuestStatus.TOPIC_SELECTED:
            mq.begin()

        existing_round = next((r for r in mq.hat_rounds if r.hat == hat), None)
        is_completed_hat = existing_round is not None and existing_round.is_completed

        if is_completed_hat and existing_round is not None:
            # Viewing a completed hat: never re-activate or allow editing, just point current_hat
            mq.current_hat = hat
            active_round = existing_round
        else:
            if mq.status not in (
                MindQuestStatus.IN_PROGRESS,
                MindQuestStatus.HAT_ACTIVE,
                MindQuestStatus.HAT_COMPLETED,
            ):
                raise DomainError(
                    f"Cannot select a hat when MindQuest status is '{mq.status.value}'."
                )
            active_round = mq.activate_hat(hat)

        if not active_round.turns:
            if hat == HatType.BLUE:
                context = MindQuestContext(
                    mindquest_id=mq.id,
                    topic=mq.topic,
                    target_level=mq.target_level.value,
                    current_hat=HatType.BLUE,
                    current_turn_number=1,
                    completed_hats=mq.completed_hats,
                )
                challenge = (
                    await self._prefetch_cache.consume_hat_challenge(mq.id, HatType.BLUE)
                    if self._prefetch_cache is not None
                    else None
                )
                if challenge is None:
                    agent = self._agent_registry.get(HatType.BLUE)
                    challenge = await agent.create_challenge(context)
            else:
                q_tpl, instr = _ARGUE_OPENING_PROMPTS[hat]
                challenge = HatChallenge(
                    question=q_tpl.format(topic=mq.topic),
                    instruction=instr,
                    expected_thinking_mode=hat,
                    difficulty=4 if mq.target_level == LanguageLevel.C1 else 3,
                    rationale="Instant Argue Mode opening prompt",
                )
            current_turn = active_round.add_turn(
                challenge_question=challenge.question,
                challenge_instruction=challenge.instruction,
                difficulty=challenge.difficulty,
            )
            await self._activity_repo.log_activity(
                user_id=mq.user_id,
                activity_type=ActivityType.HAT_SELECTED,
                mindquest_id=mq.id,
                payload={"hat": hat.value},
            )
        else:
            latest = active_round.latest_turn
            assert latest is not None
            current_turn = latest
            challenge = HatChallenge(
                question=latest.challenge_question,
                instruction=latest.challenge_instruction,
                expected_thinking_mode=hat,
                difficulty=latest.difficulty,
                rationale="Restored existing turn",
            )

        await self._mindquest_repo.save(mq)

        last_answered = next(
            (t for t in reversed(active_round.turns) if t.is_answered), None
        )
        last_thinking: ThinkingEvaluation | None = None
        last_german: GermanEvaluation | None = None
        last_prop: ResponseProposition | None = None
        last_avg: float | None = None
        if last_answered is not None:
            last_thinking = await self._evaluation_repo.get_thinking_by_turn(
                last_answered.id
            )
            last_german = await self._evaluation_repo.get_german_by_turn(
                last_answered.id
            )
            last_prop = await self._evaluation_repo.get_proposition_by_turn(
                last_answered.id
            )
            if last_thinking is not None and last_german is not None:
                last_avg = compute_response_average_score(last_thinking, last_german)

        return StartMindQuestResult(
            mindquest=mq,
            active_hat=hat,
            initial_turn=current_turn,
            challenge=challenge,
            is_read_only=is_completed_hat,
            last_answered_turn=last_answered,
            last_thinking_evaluation=last_thinking,
            last_german_evaluation=last_german,
            last_proposition=last_prop,
            last_average_score=last_avg,
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

        if mq.status == MindQuestStatus.COMPLETED:
            return AdvanceMindQuestResult(
                mindquest=mq,
                next_hat=None,
                initial_turn=None,
                challenge=None,
                is_completed=True,
                final_reflection=await self.get_final_reflection(mindquest_id),
            )

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
            if (
                mq.mode == MindQuestMode.ARGUE
                and mq.remaining_planned_hats != (HatType.BLUE,)
            ):
                # In Argue Mode, wait for the learner to select among remaining non-Blue hats
                await self._mindquest_repo.save(mq)
                return AdvanceMindQuestResult(
                    mindquest=mq,
                    next_hat=None,
                    initial_turn=None,
                    challenge=None,
                    is_completed=False,
                )

            # Activate next hat in sequence (or final BLUE hat in Argue Mode)
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

            # Use speculative prefetched challenge if available
            challenge = (
                await self._prefetch_cache.consume_hat_challenge(mq.id, next_hat)
                if self._prefetch_cache is not None
                else None
            )
            if challenge is None:
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

    async def get_current_turn_evaluation(
        self, mindquest_id: UUID
    ) -> tuple[
        Turn,
        ThinkingEvaluation | None,
        GermanEvaluation | None,
        ResponseProposition | None,
        float | None,
    ] | None:
        mq = await self.get_mindquest(mindquest_id)
        active_round = mq.current_hat_round
        if active_round is None:
            return None
        last_answered = next(
            (t for t in reversed(active_round.turns) if t.is_answered), None
        )
        if last_answered is None:
            return None
        thinking = await self._evaluation_repo.get_thinking_by_turn(last_answered.id)
        german = await self._evaluation_repo.get_german_by_turn(last_answered.id)
        prop = await self._evaluation_repo.get_proposition_by_turn(last_answered.id)
        avg = (
            compute_response_average_score(thinking, german)
            if thinking is not None and german is not None
            else None
        )
        return last_answered, thinking, german, prop, avg

    async def get_mindquest_evaluation_metrics(
        self, mindquest_id: UUID
    ) -> EvaluationMetricsSummary:
        thinking_evals = await self._evaluation_repo.list_thinking_evaluations_by_mindquest(
            mindquest_id
        )
        german_evals = await self._evaluation_repo.list_german_evaluations_by_mindquest(
            mindquest_id
        )
        return aggregate_evaluation_metrics(thinking_evals, german_evals)

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

        reflection_out = (
            await self._prefetch_cache.consume_final_reflection(mq.id)
            if self._prefetch_cache is not None
            else None
        )
        if reflection_out is None:
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
