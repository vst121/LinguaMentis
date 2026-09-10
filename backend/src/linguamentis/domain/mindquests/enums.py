"""Enums for the MindQuest domain. Per Architecture.md #11, #13."""

from __future__ import annotations

from enum import StrEnum


class LanguageLevel(StrEnum):
    """Per PRD.md #13 — V1 supports B2 and C1 only."""

    B2 = "B2"
    C1 = "C1"


class MindQuestStatus(StrEnum):
    """The MindQuest lifecycle, per Architecture.md #11 (MindQuest State Machine).

        CREATED -> TOPIC_SELECTED -> IN_PROGRESS -> HAT_ACTIVE <-> HAT_COMPLETED
                -> ALL_HATS_COMPLETED -> FINAL_EVALUATION -> COMPLETED

    The state machine is deterministic and application-controlled; the LLM
    cannot directly change the state (Architecture.md #11).
    """

    CREATED = "CREATED"
    TOPIC_SELECTED = "TOPIC_SELECTED"
    IN_PROGRESS = "IN_PROGRESS"
    HAT_ACTIVE = "HAT_ACTIVE"
    HAT_COMPLETED = "HAT_COMPLETED"
    ALL_HATS_COMPLETED = "ALL_HATS_COMPLETED"
    FINAL_EVALUATION = "FINAL_EVALUATION"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class MindQuestEvent(StrEnum):
    """Events/transitions accepted by the MindQuest state machine."""

    SELECT_TOPIC = "SELECT_TOPIC"
    BEGIN_PROGRESS = "BEGIN_PROGRESS"
    ACTIVATE_HAT = "ACTIVATE_HAT"
    COMPLETE_HAT = "COMPLETE_HAT"
    ALL_HATS_DONE = "ALL_HATS_DONE"
    START_FINAL_EVALUATION = "START_FINAL_EVALUATION"
    COMPLETE = "COMPLETE"
    ABANDON = "ABANDON"


class TurnRole(StrEnum):
    """Who authored a message within a Turn."""

    AGENT_CHALLENGE = "AGENT_CHALLENGE"
    USER_RESPONSE = "USER_RESPONSE"


class ActivityType(StrEnum):
    """Per Architecture.md #30 — User Activity types. Not authoritative state."""

    MINDQUEST_STARTED = "MINDQUEST_STARTED"
    TOPIC_SELECTED = "TOPIC_SELECTED"
    HAT_SELECTED = "HAT_SELECTED"
    RESPONSE_SUBMITTED = "RESPONSE_SUBMITTED"
    THINKING_EVALUATED = "THINKING_EVALUATED"
    GERMAN_EVALUATED = "GERMAN_EVALUATED"
    HAT_COMPLETED = "HAT_COMPLETED"
    ACHIEVEMENT_UNLOCKED = "ACHIEVEMENT_UNLOCKED"
    MINDQUEST_COMPLETED = "MINDQUEST_COMPLETED"
