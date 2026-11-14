"""Unit tests for ConversationAgent and GeminiClient TTS synthesis."""

from __future__ import annotations

import base64
import json

import httpx
import pytest

from linguamentis.ai.gemini import GeminiClient
from linguamentis.domain.hats.types import HatType
from linguamentis.infrastructure.configuration import Settings
from linguamentis.shared.exceptions import AIProviderError


@pytest.mark.asyncio
async def test_conversation_agent_opening_reply_and_tts_graceful_degradation(
    agent_registry, fake_llm_client
):
    conv_agent = agent_registry.conversation

    opening_first = conv_agent.build_opening_utterance(
        hat=HatType.WHITE,
        topic="KI im Unterricht",
        challenge_question="Welche Studien gibt es dazu?",
        is_first_turn_overall=True,
    )
    assert "Willkommen zu unserem Gespräch" in opening_first
    assert "Weißen Hut" in opening_first
    assert "Welche Studien gibt es dazu?" in opening_first

    opening_next = conv_agent.build_opening_utterance(
        hat=HatType.YELLOW,
        topic="KI im Unterricht",
        challenge_question="Welche Chancen entstehen?",
        is_first_turn_overall=False,
    )
    assert "Gelben Hut" in opening_next

    reply = await conv_agent.compose_turn_reply(
        topic="KI im Unterricht",
        target_level="B2",
        previous_hat=HatType.WHITE,
        user_response="Es gibt erste Pilotstudien an Universitäten.",
        thinking_feedback="Guter Faktenbezug.",
        german_feedback="Klarer Satzbau.",
        transitioned_hat=HatType.YELLOW,
        next_question="Welche Chancen entstehen?",
        is_completed=False,
    )
    assert reply.spoken_reply != ""

    speech_ok = await conv_agent.synthesize_safe("Guten Tag!")
    assert speech_ok.mime_type == "audio/wav"
    assert speech_ok.audio_base64 != ""

    # Verify graceful degradation when TTS provider fails
    class BrokenTTSGateway:
        async def synthesize_german_speech(self, *, text: str):
            raise AIProviderError("TTS quota exceeded")

    from linguamentis.agents.conversation import ConversationAgent

    degraded_agent = ConversationAgent(BrokenTTSGateway())  # type: ignore[arg-type]
    speech_fallback = await degraded_agent.synthesize_safe("Trotzdem weiter!")
    assert speech_fallback.audio_base64 == ""
    assert speech_fallback.mime_type == "audio/wav"


@pytest.mark.asyncio
async def test_gemini_client_synthesize_speech_handles_wav_and_pcm_l16():
    raw_pcm = b"\x00\x00" * 400
    pcm_b64 = base64.b64encode(raw_pcm).decode("ascii")
    captured: dict = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        captured["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "audio/L16;codec=pcm;rate=24000",
                                        "data": pcm_b64,
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(Settings(gemini_api_key="test-key"), http_client=http_client)
    res = await client.synthesize_speech(
        text="Hallo Welt", model="gemini-3.8-flash-lite-tts", voice_name="Kore"
    )
    await http_client.aclose()

    assert res.mime_type == "audio/wav"
    wav_bytes = base64.b64decode(res.audio_base64)
    assert wav_bytes[:4] == b"RIFF"
    assert captured["payload"]["generationConfig"]["responseModalities"] == ["AUDIO"]
