"""Gemini implementation of :class:`linguamentis.ai.client.LLMClient`."""

from __future__ import annotations

import asyncio
import json
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from linguamentis.infrastructure.configuration import Settings
from linguamentis.shared.exceptions import AIProviderError, StructuredOutputParsingError
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class GeminiClient:
    """Calls Gemini's generateContent API and validates structured JSON output."""

    def __init__(
        self, settings: Settings, *, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self._settings = settings
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(
            base_url=settings.gemini_base_url,
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
        last_error: ValidationError | None = None
        contents = [{"role": "user", "parts": [{"text": user_prompt}]}]

        for attempt in range(self._settings.ai_max_retries + 1):
            raw = await self._call(
                contents=contents,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                response_model=response_model,
            )
            try:
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
                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "Your previous response did not match the required JSON "
                                    f"schema. Validation error: {exc}. Reply again with ONLY "
                                    "valid JSON matching the schema, no prose or markdown."
                                )
                            }
                        ],
                    }
                )

        raise StructuredOutputParsingError(
            f"Failed to obtain a valid '{response_model.__name__}' from model '{model}' "
            f"after {self._settings.ai_max_retries + 1} attempts: {last_error}"
        )

    async def _call(
        self,
        *,
        contents: list[dict],
        system_prompt: str,
        model: str,
        temperature: float,
        response_model: type[BaseModel],
    ) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "responseJsonSchema": response_model.model_json_schema(),
            },
        }

        last_exc: Exception | None = None
        response: httpx.Response | None = None
        for attempt in range(self._settings.ai_max_retries + 1):
            try:
                response = await self._http.post(
                    f"/v1beta/models/{quote(model, safe='')}:generateContent",
                    headers={"x-goog-api-key": self._settings.gemini_api_key},
                    json=payload,
                )
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                status_code = exc.response.status_code
                if (
                    status_code in _RETRYABLE_STATUS_CODES
                    and attempt < self._settings.ai_max_retries
                ):
                    logger.warning(
                        "ai.gemini.retryable_http_error",
                        model=model,
                        status_code=status_code,
                        attempt=attempt,
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise AIProviderError(f"Gemini request failed: {exc}") from exc
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < self._settings.ai_max_retries:
                    logger.warning(
                        "ai.gemini.retryable_transport_error",
                        model=model,
                        attempt=attempt,
                        error=str(exc),
                    )
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise AIProviderError(f"Gemini request failed: {exc}") from exc
            except httpx.HTTPError as exc:
                raise AIProviderError(f"Gemini request failed: {exc}") from exc

        if response is None:
            raise AIProviderError(f"Gemini request failed: {last_exc}")

        data: dict = {}
        try:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                f"Unexpected Gemini response shape: {json.dumps(data)[:500]}"
            ) from exc
