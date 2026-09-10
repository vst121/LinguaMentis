"""OpenRouter implementation of :class:`linguamentis.ai.client.LLMClient`.

This is the only module in the codebase allowed to know about OpenRouter's
HTTP API and payload shape (Architecture.md #22, #45 — Security Boundaries:
the API key never leaves the backend).
"""

from __future__ import annotations

import json
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from linguamentis.infrastructure.configuration import Settings
from linguamentis.shared.exceptions import AIProviderError, StructuredOutputParsingError
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


def _json_schema_for(model: type[BaseModel]) -> dict:
    """Build a strict JSON schema OpenRouter/most OpenAI-compatible models
    accept for structured outputs (``response_format: json_schema``)."""

    schema = model.model_json_schema()
    schema["additionalProperties"] = False
    return {
        "type": "json_schema",
        "json_schema": {
            "name": model.__name__,
            "strict": True,
            "schema": schema,
        },
    }


class OpenRouterClient:
    """Talks to OpenRouter's ``/chat/completions`` endpoint using structured
    (JSON schema) outputs, with a bounded number of repair retries when a
    response fails to validate.
    """

    def __init__(self, settings: Settings, *, http_client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            timeout=settings.ai_request_timeout_seconds,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str,
        temperature: float = 0.4,
    ) -> T:
        last_error: Exception | None = None
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(self._settings.ai_max_retries + 1):
            try:
                raw = await self._call(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    response_model=response_model,
                )
                return response_model.model_validate_json(raw)
            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "ai.structured_output.validation_failed",
                    model=model,
                    response_schema=response_model.__name__,
                    attempt=attempt,
                    error=str(exc),
                )
                # Ask the model to repair its own output on the next attempt.
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not match the required JSON schema. "
                            f"Validation error: {exc}. Reply again with ONLY valid JSON matching "
                            "the schema, no prose, no markdown fences."
                        ),
                    }
                )
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning(
                    "ai.provider.request_failed",
                    model=model,
                    attempt=attempt,
                    error=str(exc),
                )

        raise StructuredOutputParsingError(
            f"Failed to obtain a valid '{response_model.__name__}' from model '{model}' "
            f"after {self._settings.ai_max_retries + 1} attempts: {last_error}"
        )

    async def _call(
        self,
        *,
        messages: list[dict],
        model: str,
        temperature: float,
        response_model: type[BaseModel],
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        if self._settings.openrouter_http_referer:
            headers["HTTP-Referer"] = self._settings.openrouter_http_referer
        if self._settings.openrouter_app_title:
            headers["X-Title"] = self._settings.openrouter_app_title

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": _json_schema_for(response_model),
        }

        try:
            resp = await self._http.post("/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AIProviderError(f"OpenRouter request failed: {exc}") from exc

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIProviderError(f"Unexpected OpenRouter response shape: {json.dumps(data)[:500]}") from exc

        return content
