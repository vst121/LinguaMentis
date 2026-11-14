import json

import httpx
import pytest
from pydantic import BaseModel

from linguamentis.ai.gemini import GeminiClient
from linguamentis.infrastructure.configuration import Settings


class SampleOutput(BaseModel):
    message: str


@pytest.mark.asyncio
async def test_gemini_client_uses_native_api_and_parses_structured_output():
    request_data: dict = {}

    def handle_request(request: httpx.Request) -> httpx.Response:
        request_data["url"] = str(request.url)
        request_data["headers"] = request.headers
        request_data["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": '{"message":"hello"}'}]}}
                ]
            },
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(Settings(gemini_api_key="test-key"), http_client=http_client)

    result = await client.generate_structured(
        system_prompt="Be concise",
        user_prompt="Say hello",
        response_model=SampleOutput,
        model="gemini-test",
    )
    await http_client.aclose()

    assert result == SampleOutput(message="hello")
    assert request_data["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-test:generateContent"
    )
    assert request_data["headers"]["x-goog-api-key"] == "test-key"
    assert request_data["payload"]["systemInstruction"]["parts"][0]["text"] == "Be concise"
    assert request_data["payload"]["contents"][0]["parts"][0]["text"] == "Say hello"
    assert request_data["payload"]["generationConfig"]["responseMimeType"] == "application/json"
    assert (
        request_data["payload"]["generationConfig"]["responseJsonSchema"]["properties"]["message"]
        ["type"]
        == "string"
    )


@pytest.mark.asyncio
async def test_gemini_client_retries_transient_timeout():
    attempts = 0

    def handle_request(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("timed out", request=request)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": '{"message":"recovered"}'}]}}
                ]
            },
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(
        Settings(gemini_api_key="test-key", ai_max_retries=1), http_client=http_client
    )

    result = await client.generate_structured(
        system_prompt="Be concise",
        user_prompt="Say hello",
        response_model=SampleOutput,
        model="gemini-test",
    )
    await http_client.aclose()

    assert attempts == 2
    assert result == SampleOutput(message="recovered")
