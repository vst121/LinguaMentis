"""Red Hat Agent — Emotion, intuition, feelings."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.domain.hats.types import HatType


class RedHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.RED
