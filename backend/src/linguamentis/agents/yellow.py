"""Yellow Hat Agent — Benefits, value, positive consequences."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.domain.hats.types import HatType


class YellowHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.YELLOW
