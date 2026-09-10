"""Application-wide exception hierarchy.

The API layer translates these into HTTP responses (see
``api/dependencies.py`` / exception handlers registered in ``main.py``).
Domain and application code should raise these instead of leaking
infrastructure-specific exceptions (SQLAlchemy errors, httpx errors, ...).
"""

from __future__ import annotations


class LinguaMentisError(Exception):
    """Base class for all application-defined errors."""


# --- Domain / state errors -------------------------------------------------


class DomainError(LinguaMentisError):
    """Raised when a domain invariant would be violated."""


class InvalidStateTransitionError(DomainError):
    """Raised when the MindQuest state machine rejects a transition."""

    def __init__(self, current_state: str, attempted_event: str) -> None:
        self.current_state = current_state
        self.attempted_event = attempted_event
        super().__init__(
            f"Cannot apply event '{attempted_event}' while MindQuest is in state "
            f"'{current_state}'."
        )


# --- Not found ---------------------------------------------------------


class NotFoundError(LinguaMentisError):
    """Raised when an entity cannot be located."""

    def __init__(self, entity: str, identifier: object) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} '{identifier}' was not found.")


# --- AI / gateway errors -------------------------------------------------


class AIGatewayError(LinguaMentisError):
    """Raised when the AI Gateway cannot produce a usable structured result."""


class AIProviderError(AIGatewayError):
    """Raised when the upstream LLM provider (OpenRouter) fails or times out."""


class StructuredOutputParsingError(AIGatewayError):
    """Raised when the LLM response cannot be parsed into the expected schema."""


class AgentContractViolationError(AIGatewayError):
    """Raised when an agent response cannot be reconciled with its Hat Contract."""
