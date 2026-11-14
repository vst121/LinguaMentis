"""Speech-to-Text REST API endpoint.

Provides server-side German audio transcription fallback via AIGateway so
learners can speak their responses across all browsers.
"""

from __future__ import annotations

import base64
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from linguamentis.ai.gateway import AIGateway
from linguamentis.api.dependencies import get_ai_gateway
from linguamentis.shared.exceptions import DomainError

router = APIRouter(prefix="/speech", tags=["Speech"])

ALLOWED_AUDIO_MIME_PREFIXES = (
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
)
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB


class SpeechTranscribeRequest(BaseModel):
    audio_base64: str = Field(min_length=4, description="Base64-encoded audio payload.")
    mime_type: str = Field(default="audio/webm", description="Audio MIME type.")


class SpeechTranscribeResponse(BaseModel):
    text: str


@router.post("/transcribe", response_model=SpeechTranscribeResponse)
async def transcribe_speech(
    body: SpeechTranscribeRequest,
    gateway: Annotated[AIGateway, Depends(get_ai_gateway)],
) -> SpeechTranscribeResponse:
    base_mime = body.mime_type.split(";")[0].strip().lower()
    if not any(base_mime.startswith(prefix) for prefix in ALLOWED_AUDIO_MIME_PREFIXES):
        raise DomainError(f"Unsupported audio MIME type '{body.mime_type}'.")

    try:
        decoded = base64.b64decode(body.audio_base64, validate=True)
    except Exception as exc:
        raise DomainError("Invalid base64 audio payload.") from exc

    if len(decoded) == 0:
        raise DomainError("Audio payload must not be empty.")
    if len(decoded) > MAX_AUDIO_BYTES:
        raise DomainError("Audio payload exceeds maximum allowed size of 10 MB.")

    output = await gateway.transcribe_german_speech(
        audio_base64=body.audio_base64,
        mime_type=base_mime,
    )
    return SpeechTranscribeResponse(text=output.text.strip())


class SpeechSynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)


class SpeechSynthesizeResponse(BaseModel):
    audio_base64: str
    mime_type: str = "audio/wav"


@router.post("/synthesize", response_model=SpeechSynthesizeResponse)
async def synthesize_speech(
    body: SpeechSynthesizeRequest,
    gateway: Annotated[AIGateway, Depends(get_ai_gateway)],
) -> SpeechSynthesizeResponse:
    res = await gateway.synthesize_german_speech(text=body.text.strip())
    return SpeechSynthesizeResponse(audio_base64=res.audio_base64, mime_type=res.mime_type)

