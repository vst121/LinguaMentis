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


@pytest.mark.asyncio
async def test_gemini_client_ignores_thought_parts_and_strips_fences():
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"thought": True, "text": "internal reasoning"},
                                {"text": '```json\n{"message":"clean"}\n```'},
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

    result = await client.generate_structured(
        system_prompt="Be concise",
        user_prompt="Say hello",
        response_model=SampleOutput,
        model="gemini-4-hydrogen",
    )
    await http_client.aclose()

    assert result == SampleOutput(message="clean")


@pytest.mark.asyncio
async def test_gemini_client_falls_back_on_structured_format_failure():
    called_models: list[str] = []

    def handle_request(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "gemini-4-hydrogen" in url:
            called_models.append("gemini-4-hydrogen")
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "not valid json"}]}}]},
            )
        called_models.append("gemini-2.5-flash")
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": '{"message":"from-fallback"}'}]}}]
            },
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(
        Settings(
            gemini_api_key="test-key",
            ai_max_retries=1,
            ai_model_structured_fallback="gemini-2.5-flash",
        ),
        http_client=http_client,
    )

    result = await client.generate_structured(
        system_prompt="Be concise",
        user_prompt="Say hello",
        response_model=SampleOutput,
        model="gemini-4-hydrogen",
    )
    await http_client.aclose()

    assert result == SampleOutput(message="from-fallback")
    assert called_models == ["gemini-4-hydrogen", "gemini-4-hydrogen", "gemini-2.5-flash"]


@pytest.mark.asyncio
async def test_gemini_client_raises_ai_provider_error_on_exhausted_http_errors():
    from linguamentis.shared.exceptions import AIProviderError

    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"message": "Service unavailable"}})

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(
        Settings(gemini_api_key="test-key", ai_max_retries=0),
        http_client=http_client,
    )

    with pytest.raises(AIProviderError):
        await client.generate_structured(
            system_prompt="Be concise",
            user_prompt="Say hello",
            response_model=SampleOutput,
            model="gemini-2.5-flash",
        )
    await http_client.aclose()


@pytest.mark.asyncio
async def test_gemini_client_self_corrects_on_invalid_json_then_succeeds():
    attempts = 0

    def handle_request(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        body = json.loads(request.content)
        if attempts == 1:
            return httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "{broken json"}]}}]},
            )
        # Second attempt includes correction prompt in contents
        assert len(body["contents"]) == 2
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": '{"message":"corrected"}'}]}}]},
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_request),
        base_url="https://generativelanguage.googleapis.com",
    )
    client = GeminiClient(
        Settings(gemini_api_key="test-key", ai_max_retries=1),
        http_client=http_client,
    )
    res = await client.generate_structured(
        system_prompt="Sys",
        user_prompt="User",
        response_model=SampleOutput,
        model="gemini-2.5-flash",
    )
    await http_client.aclose()
    assert attempts == 2
    assert res.message == "corrected"


@pytest.mark.asyncio
async def test_gemini_client_non_retryable_401_and_malformed_candidates():
    from linguamentis.ai.gemini import _get_cached_schema
    from linguamentis.shared.exceptions import AIProviderError

    # Schema cache returns identical dict object on repeated calls
    assert _get_cached_schema(SampleOutput) is _get_cached_schema(SampleOutput)

    calls = 0

    def handle_401(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, json={"error": "unauthorized"})

    http_401 = httpx.AsyncClient(
        transport=httpx.MockTransport(handle_401),
        base_url="https://generativelanguage.googleapis.com",
    )
    client_401 = GeminiClient(
        Settings(gemini_api_key="bad-key", ai_max_retries=3),
        http_client=http_401,
    )
    with pytest.raises(AIProviderError) as exc_info:
        await client_401.generate_structured(
            system_prompt="Sys",
            user_prompt="User",
            response_model=SampleOutput,
            model="gemini-2.5-flash",
        )
    await http_401.aclose()
    # 401 is not in _RETRYABLE_STATUS_CODES -> must fail on 1st call without retrying
    assert calls == 1
    assert exc_info.value.is_format_error is False

    # Empty candidates list -> AIProviderError with is_format_error=True
    http_empty = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"candidates": []})),
        base_url="https://generativelanguage.googleapis.com",
    )
    client_empty = GeminiClient(
        Settings(gemini_api_key="key", ai_max_retries=0),
        http_client=http_empty,
    )
    with pytest.raises(AIProviderError) as empty_exc:
        await client_empty.generate_structured(
            system_prompt="Sys",
            user_prompt="User",
            response_model=SampleOutput,
            model="gemini-2.5-flash",
        )
    await http_empty.aclose()
    assert empty_exc.value.is_format_error is True


