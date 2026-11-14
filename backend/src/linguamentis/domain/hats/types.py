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


# Mandatory hat sequence for Answering Mode:
# White -> Yellow -> Green -> Red -> Black -> Blue (always last).
DEFAULT_HAT_SEQUENCE: tuple[HatType, ...] = (
    HatType.WHITE,
    HatType.YELLOW,
    HatType.GREEN,
    HatType.RED,
    HatType.BLACK,
    HatType.BLUE,
)

# Selectable hats for Argue Mode (Blue Hat is never selectable).
ARGUE_SELECTABLE_HATS: tuple[HatType, ...] = (
    HatType.WHITE,
    HatType.YELLOW,
    HatType.GREEN,
    HatType.RED,
    HatType.BLACK,
)
