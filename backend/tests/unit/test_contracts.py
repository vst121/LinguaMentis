"""Unit tests for HatContracts & AgentRegistry."""

from linguamentis.agents.registry import AgentRegistry
from linguamentis.domain.hats.contracts import (
    get_hat_contract,
)
from linguamentis.domain.hats.types import HatType


def test_get_hat_contract_returns_valid_contracts():
    for hat in HatType:
        contract = get_hat_contract(hat)
        assert contract.hat == hat
        assert len(contract.should) > 0
        assert len(contract.should_not) > 0


def test_agent_registry_instantiates_all_hats(fake_gateway):
    registry = AgentRegistry(gateway=fake_gateway)
    for hat in HatType:
        agent = registry.get(hat)
        assert agent.hat == hat
        assert agent.contract == get_hat_contract(hat)
