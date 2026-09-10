"""AgentRegistry — lookup registry for Hat Agents.

Per Architecture.md #15: Resolves HatType to concrete HatAgent implementation.
"""

from __future__ import annotations

from linguamentis.agents.base import HatAgent
from linguamentis.agents.black import BlackHatAgent
from linguamentis.agents.blue import BlueHatAgent
from linguamentis.agents.green import GreenHatAgent
from linguamentis.agents.red import RedHatAgent
from linguamentis.agents.white import WhiteHatAgent
from linguamentis.agents.yellow import YellowHatAgent
from linguamentis.ai.gateway import AIGateway
from linguamentis.domain.hats.types import HatType


class AgentRegistry:
    """Registry managing instances of all Six Thinking Hat agents."""

    def __init__(self, gateway: AIGateway) -> None:
        self._gateway = gateway
        self._agents: dict[HatType, HatAgent] = {
            HatType.WHITE: WhiteHatAgent(gateway),
            HatType.RED: RedHatAgent(gateway),
            HatType.BLACK: BlackHatAgent(gateway),
            HatType.YELLOW: YellowHatAgent(gateway),
            HatType.GREEN: GreenHatAgent(gateway),
            HatType.BLUE: BlueHatAgent(gateway),
        }

    def get(self, hat: HatType) -> HatAgent:
        agent = self._agents.get(hat)
        if agent is None:
            raise KeyError(f"No agent registered for hat '{hat}'.")
        return agent

    @property
    def blue(self) -> BlueHatAgent:
        return self._agents[HatType.BLUE]  # type: ignore[return-value]
