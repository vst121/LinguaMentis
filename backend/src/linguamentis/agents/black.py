"""Black Hat Agent — Critical thinking, risks, weaknesses."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.domain.hats.types import HatType


class BlackHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.BLACK
