"""Blue Hat Agent — Process orchestration, synthesis, final reflection."""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.ai.models import FinalReflectionOutput
from linguamentis.domain.hats.types import HatType


class BlueHatAgent(HatAgent):
    @property
    def hat(self) -> HatType:
        return HatType.BLUE

    async def generate_final_reflection(
        self,
        *,
        topic: str,
        target_level: str,
        hat_summaries: str,
        previous_mindquest_summary: str = "(no previous MindQuests)",
    ) -> FinalReflectionOutput:
        return await self._gateway.generate_final_reflection(
            topic=topic,
            target_level=target_level,
            hat_summaries=hat_summaries,
            previous_mindquest_summary=previous_mindquest_summary,
        )
