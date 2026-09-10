"""Core Hat types shared by the domain, agents, and AI layers.

Per README.md / HatContracts.md #3 — Six Thinking Hats.
"""

from __future__ import annotations

from enum import StrEnum


class HatType(StrEnum):
    """The six de Bono thinking hats. Blue is the orchestrator, not a round type."""

    WHITE = "WHITE"
    RED = "RED"
    BLACK = "BLACK"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    BLUE = "BLUE"

    @property
    def is_orchestrator(self) -> bool:
        return self is HatType.BLUE


# The default hat sequence for a MindQuest once Blue introduces the topic.
# V1's vertical slice only activates BLACK; the others are wired but unused
# until "the remaining five hats" milestone (README.md — First Vertical Slice).
DEFAULT_HAT_SEQUENCE: tuple[HatType, ...] = (
    HatType.BLACK,
    HatType.WHITE,
    HatType.YELLOW,
    HatType.RED,
    HatType.GREEN,
)
