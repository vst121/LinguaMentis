"""White Hat Agent — Information, facts, evidence."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.domain.hats.types import HatType


class WhiteHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.WHITE
