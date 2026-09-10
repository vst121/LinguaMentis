"""Base Hat Agent abstract class.

Per Architecture.md #14 / HatContracts.md #4:
Each agent receives a controlled MindQuestContext and delegates structured
challenge generation to the AIGateway using its assigned HatContract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from linguamentis.ai.gateway import AIGateway
from linguamentis.ai.models import HatChallenge
from linguamentis.domain.hats.contracts import HatContract, get_hat_contract
from linguamentis.domain.hats.types import HatType
from linguamentis.domain.mindquests.value_objects import MindQuestContext


class HatAgent(ABC):
    """Abstract base for all Six Thinking Hat agents."""

    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway

    @property
    @abstractmethod
    def hat(self) -> HatType:
        ...

    @property
    def contract(self) -> HatContract:
        return get_hat_contract(self.hat)

    async def create_challenge(self, context: MindQuestContext) -> HatChallenge:
        """Ask the learner a question that requires thinking within this hat's mode."""
        return await self._gateway.generate_hat_challenge(
            contract=self.contract, context=context
        )
