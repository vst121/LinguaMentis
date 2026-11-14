"""Gemini implementation of :class:`linguamentis.ai.client.LLMClient`."""

from __future__ import annotations

import asyncio
import json
import re
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ValidationError

from linguamentis.ai.models import SpeechTranscriptionOutput, SynthesizedSpeech
from linguamentis.infrastructure.configuration import Settings
from linguamentis.shared.exceptions import AIProviderError, StructuredOutputParsingError
from linguamentis.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)
_SCHEMA_CACHE: dict[type[BaseModel], dict] = {}


def _get_cached_schema(response_model: type[BaseModel]) -> dict:
    schema = _SCHEMA_CACHE.get(response_model)
    if schema is None:
        schema = response_model.model_json_schema()
        _SCHEMA_CACHE[response_model] = schema
    return schema


def _clean_json_text(raw: str) -> str:
    match = _CODE_FENCE_RE.match(raw)
    return match.group(1).strip() if match else raw.strip()


def _extract_response_text(data: dict) -> str:
    parts = data["candidates"][0]["content"]["parts"]
    non_thought_texts = [
        part["text"]
        for part in parts
        if isinstance(part, dict) and not part.get("thought") and isinstance(part.get("text"), str)
    ]
    if non_thought_texts:
        return _clean_json_text("\n".join(non_thought_texts))
    return _clean_json_text(parts[0]["text"])


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
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=120.0,
            ),
        )

    async def warmup(self) -> None:
        """Establish a warm TLS connection to Gemini API before the first user turn."""
        if not self._owns_client:
            return
        try:
            await self._http.head("/v1beta/models", timeout=5.0)
        except Exception:
            pass

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def transcribe_audio(
        self,
        *,
        audio_base64: str,
        mime_type: str,
        model: str,
    ) -> SpeechTranscriptionOutput:
        system_prompt = (
            "You are a verbatim German speech-to-text transcriber for LinguaMentis. "
            "Transcribe the spoken German audio accurately into plain text. "
            "IMPORTANT: Transcribe verbatim what the speaker said — do NOT auto-correct "
            "grammar or vocabulary mistakes. Output ONLY the spoken German text (or an "
            "empty string if silent), with no quotes, markdown, or commentary."
        )
        contents = [
            {
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": audio_base64,
                        }
                    },
                    {"text": "Transcribe this German audio verbatim."},
                ],
            }
        ]
        raw = await self._call(
            contents=contents,
            system_prompt=system_prompt,
            model=model,
            temperature=0.0,
            response_model=None,
        )
        cleaned = raw.strip()
        if cleaned.startswith("{"):
            try:
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    for key in ("text", "transcript", "transcription"):
                        if isinstance(parsed.get(key), str):
                            return SpeechTranscriptionOutput(text=parsed[key].strip())
            except Exception:
                pass
        return SpeechTranscriptionOutput(text=cleaned)

    async def synthesize_speech(
        self,
        *,
        text: str,
        model: str,
        voice_name: str = "Kore",
    ) -> SynthesizedSpeech:
        import base64
        import io
        import wave

        models_to_try = [model]
        if model != "gemini-2.5-flash-preview-tts":
            models_to_try.append("gemini-2.5-flash-preview-tts")

        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name}
                    }
                },
            },
        }

        last_err: Exception | None = None
        for candidate_model in models_to_try:
            try:
                resp = await self._http.post(
                    f"/v1beta/models/{quote(candidate_model, safe='')}:generateContent",
                    headers={"x-goog-api-key": self._settings.gemini_api_key},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                inline = data["candidates"][0]["content"]["parts"][0]["inlineData"]
                b64_data: str = inline["data"]
                mime: str = inline.get("mimeType", "audio/wav")

                if mime.startswith("audio/L16") or "pcm" in mime.lower():
                    pcm_bytes = base64.b64decode(b64_data)
                    wav_buf = io.BytesIO()
                    with wave.open(wav_buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(pcm_bytes)
                    b64_data = base64.b64encode(wav_buf.getvalue()).decode("ascii")
                    mime = "audio/wav"

                return SynthesizedSpeech(audio_base64=b64_data, mime_type=mime)
            except Exception as exc:
                last_err = exc
                logger.warning(
                    "ai.gemini.tts_attempt_failed",
                    model=candidate_model,
                    error=str(exc),
                )

        raise AIProviderError(f"Gemini TTS synthesis failed: {last_err}") from last_err

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str,
        temperature: float = 0.4,
    ) -> T:
        try:
            return await self._generate_with_model(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                model=model,
                temperature=temperature,
            )
        except (StructuredOutputParsingError, AIProviderError) as exc:
            fallback_model = self._settings.ai_model_structured_fallback.strip()
            if not fallback_model or fallback_model == model:
                raise
            if isinstance(exc, AIProviderError) and not exc.is_format_error:
                raise

            logger.warning(
                "ai.structured_output.fallback_triggered",
                primary_model=model,
                fallback_model=fallback_model,
                response_schema=response_model.__name__,
                error=str(exc),
            )
            return await self._generate_with_model(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                model=fallback_model,
                temperature=temperature,
            )

    async def _generate_with_model(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str,
        temperature: float,
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
        response_model: type[BaseModel] | None,
    ) -> str:
        gen_config: dict = {"temperature": temperature}
        if response_model is not None:
            gen_config["responseMimeType"] = "application/json"
            gen_config["responseJsonSchema"] = _get_cached_schema(response_model)

        lower_model = model.lower()
        if (
            self._settings.ai_disable_thinking_for_speed
            and "lite" not in lower_model
            and "transcribe" not in lower_model
            and ("2.5" in lower_model or "3." in lower_model)
        ):
            gen_config["thinkingConfig"] = {"thinkingBudget": 0}

        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": gen_config,
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
                is_format = status_code == 400
                raise AIProviderError(
                    f"Gemini request failed: {exc}", is_format_error=is_format
                ) from exc
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
            return _extract_response_text(data)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(
                f"Unexpected Gemini response shape: {json.dumps(data)[:500]}",
                is_format_error=True,
            ) from exc
