"""LLM client abstraction.

Per Architecture.md #22 (AI Gateway) / Principle 6 (Provider independence):

    Agent -> ILLMClient -> OpenRouterClient -> OpenRouter API

Agents and evaluators depend only on ``LLMClient``; they must never import
``httpx`` or reference OpenRouter directly. This makes it possible to swap
providers (or use a fake client in tests) without touching agent/evaluator
code.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    """The single capability the AI layer needs from a provider: turn a
    (system prompt, user prompt) pair into a validated, structured object.
    """

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str,
        temperature: float = 0.4,
    ) -> T:
        """Call the LLM and return a validated instance of ``response_model``.

        Implementations must raise ``AIProviderError`` on transport/HTTP
        failures and ``StructuredOutputParsingError`` when the response
        cannot be parsed/validated against ``response_model`` after
        retries.
        """
        ...
