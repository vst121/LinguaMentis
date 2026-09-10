"""The MindQuest state machine.

Per Architecture.md #11 and Principle 1 ("Application owns state"), this is
a small, explicit, deterministic state machine. It has no dependency on
FastAPI, SQLAlchemy, or any LLM client — the LLM never drives a transition
directly; the application decides which event to raise based on its own
rules (e.g. "the Thinking Evaluator scored above the completion threshold").
"""

from __future__ import annotations

from linguamentis.domain.mindquests.enums import MindQuestEvent, MindQuestStatus
from linguamentis.shared.exceptions import InvalidStateTransitionError

# Adjacency table: current status -> {event -> next status}.
# HAT_ACTIVE deliberately has no self-transition entry: submitting another
# response/challenge within the same hat round does not change the
# MindQuest's status at all (see MindQuestEngine.submit_response), only the
# Turn count changes. The status only moves once the engine explicitly
# decides the hat round is complete (COMPLETE_HAT).
_TRANSITIONS: dict[MindQuestStatus, dict[MindQuestEvent, MindQuestStatus]] = {
    MindQuestStatus.CREATED: {
        MindQuestEvent.SELECT_TOPIC: MindQuestStatus.TOPIC_SELECTED,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.TOPIC_SELECTED: {
        MindQuestEvent.BEGIN_PROGRESS: MindQuestStatus.IN_PROGRESS,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.IN_PROGRESS: {
        MindQuestEvent.ACTIVATE_HAT: MindQuestStatus.HAT_ACTIVE,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.HAT_ACTIVE: {
        MindQuestEvent.COMPLETE_HAT: MindQuestStatus.HAT_COMPLETED,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.HAT_COMPLETED: {
        MindQuestEvent.ACTIVATE_HAT: MindQuestStatus.HAT_ACTIVE,
        MindQuestEvent.ALL_HATS_DONE: MindQuestStatus.ALL_HATS_COMPLETED,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.ALL_HATS_COMPLETED: {
        MindQuestEvent.START_FINAL_EVALUATION: MindQuestStatus.FINAL_EVALUATION,
        MindQuestEvent.ABANDON: MindQuestStatus.ABANDONED,
    },
    MindQuestStatus.FINAL_EVALUATION: {
        MindQuestEvent.COMPLETE: MindQuestStatus.COMPLETED,
    },
    MindQuestStatus.COMPLETED: {},
    MindQuestStatus.ABANDONED: {},
}


class MindQuestStateMachine:
    """A pure, stateless helper that validates/executes transitions."""

    @staticmethod
    def can_apply(current: MindQuestStatus, event: MindQuestEvent) -> bool:
        return event in _TRANSITIONS.get(current, {})

    @staticmethod
    def apply(current: MindQuestStatus, event: MindQuestEvent) -> MindQuestStatus:
        """Return the next status, or raise ``InvalidStateTransitionError``."""

        allowed = _TRANSITIONS.get(current, {})
        if event not in allowed:
            raise InvalidStateTransitionError(
                current_state=current.value, attempted_event=event.value
            )
        return allowed[event]

    @staticmethod
    def allowed_events(current: MindQuestStatus) -> tuple[MindQuestEvent, ...]:
        return tuple(_TRANSITIONS.get(current, {}).keys())

    @staticmethod
    def is_terminal(current: MindQuestStatus) -> bool:
        return current in (MindQuestStatus.COMPLETED, MindQuestStatus.ABANDONED)
