"""Unit tests for MindQuest state machine."""

import pytest

from linguamentis.domain.mindquests.enums import MindQuestEvent, MindQuestStatus
from linguamentis.domain.mindquests.state_machine import MindQuestStateMachine
from linguamentis.shared.exceptions import InvalidStateTransitionError


def test_valid_transitions_sequence():
    sm = MindQuestStateMachine

    s = sm.apply(MindQuestStatus.CREATED, MindQuestEvent.SELECT_TOPIC)
    assert s == MindQuestStatus.TOPIC_SELECTED

    s = sm.apply(s, MindQuestEvent.BEGIN_PROGRESS)
    assert s == MindQuestStatus.IN_PROGRESS

    s = sm.apply(s, MindQuestEvent.ACTIVATE_HAT)
    assert s == MindQuestStatus.HAT_ACTIVE

    s = sm.apply(s, MindQuestEvent.COMPLETE_HAT)
    assert s == MindQuestStatus.HAT_COMPLETED

    s = sm.apply(s, MindQuestEvent.ALL_HATS_DONE)
    assert s == MindQuestStatus.ALL_HATS_COMPLETED

    s = sm.apply(s, MindQuestEvent.START_FINAL_EVALUATION)
    assert s == MindQuestStatus.FINAL_EVALUATION

    s = sm.apply(s, MindQuestEvent.COMPLETE)
    assert s == MindQuestStatus.COMPLETED
    assert sm.is_terminal(s)


def test_invalid_transition_raises():
    sm = MindQuestStateMachine
    with pytest.raises(InvalidStateTransitionError):
        sm.apply(MindQuestStatus.CREATED, MindQuestEvent.COMPLETE)
