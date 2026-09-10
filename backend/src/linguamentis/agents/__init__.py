"""Agents package re-exports."""

from linguamentis.agents.base import HatAgent
from linguamentis.agents.black import BlackHatAgent
from linguamentis.agents.blue import BlueHatAgent
from linguamentis.agents.green import GreenHatAgent
from linguamentis.agents.red import RedHatAgent
from linguamentis.agents.registry import AgentRegistry
from linguamentis.agents.white import WhiteHatAgent
from linguamentis.agents.yellow import YellowHatAgent

__all__ = [
    "HatAgent",
    "AgentRegistry",
    "WhiteHatAgent",
    "RedHatAgent",
    "BlackHatAgent",
    "YellowHatAgent",
    "GreenHatAgent",
    "BlueHatAgent",
]
