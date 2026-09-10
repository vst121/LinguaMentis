"""Green Hat Agent — Creativity, alternatives, possibilities."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.domain.hats.types import HatType


class GreenHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.GREEN
