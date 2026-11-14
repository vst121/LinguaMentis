"""Unit tests for Result type and application exception hierarchy."""

from __future__ import annotations

import pytest

from linguamentis.shared.exceptions import (
    AgentContractViolationError,
    AIGatewayError,
    AIProviderError,
    DomainError,
    InvalidStateTransitionError,
    LinguaMentisError,
    NotFoundError,
    StructuredOutputParsingError,
)
from linguamentis.shared.result import Result


def test_result_ok_unwrap_and_map():
    res: Result[int, str] = Result.ok(21)
    assert res.is_ok is True
    assert res.is_err is False
    assert res.unwrap() == 21

    mapped = res.map(lambda x: x * 2)
    assert mapped.is_ok is True
    assert mapped.unwrap() == 42

    with pytest.raises(ValueError, match="Called unwrap_err\\(\\) on an ok Result"):
        res.unwrap_err()


def test_result_err_unwrap_err_and_map():
    res: Result[int, str] = Result.err("invalid input")
    assert res.is_ok is False
    assert res.is_err is True
    assert res.unwrap_err() == "invalid input"

    mapped = res.map(lambda x: x * 2)
    assert mapped.is_err is True
    assert mapped.unwrap_err() == "invalid input"

    with pytest.raises(ValueError, match="Called unwrap\\(\\) on an error Result"):
        res.unwrap()


def test_exception_hierarchy_and_attributes():
    err_transition = InvalidStateTransitionError("CREATED", "COMPLETE")
    assert isinstance(err_transition, DomainError)
    assert isinstance(err_transition, LinguaMentisError)
    assert err_transition.current_state == "CREATED"
    assert err_transition.attempted_event == "COMPLETE"
    assert "CREATED" in str(err_transition)
    assert "COMPLETE" in str(err_transition)

    err_not_found = NotFoundError("MindQuest", "123")
    assert isinstance(err_not_found, LinguaMentisError)
    assert err_not_found.entity == "MindQuest"
    assert err_not_found.identifier == "123"
    assert "MindQuest '123' was not found." in str(err_not_found)

    err_provider = AIProviderError("upstream timeout", is_format_error=True)
    assert isinstance(err_provider, AIGatewayError)
    assert err_provider.is_format_error is True

    assert issubclass(StructuredOutputParsingError, AIGatewayError)
    assert issubclass(AgentContractViolationError, AIGatewayError)
