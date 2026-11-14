"""Integration tests for FastAPI endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_mindquest_lifecycle_api(async_client: AsyncClient):
    expected_sequence = ["WHITE", "YELLOW", "GREEN", "RED", "BLACK", "BLUE"]

    # 1. Create MindQuest (mandatory 6-hat order is enforced regardless of input)
    create_resp = await async_client.post(
        "/api/v1/mindquests",
        json={
            "topic": "Einsparung von Plastikmüll im Alltag",
            "target_level": "B2",
            "planned_hats": ["BLACK"],
        },
    )
    assert create_resp.status_code == 201
    mq_data = create_resp.json()
    mq_id = mq_data["id"]
    assert mq_data["status"] == "TOPIC_SELECTED"
    assert mq_data["planned_hats"] == expected_sequence

    # 2. Start MindQuest -> first hat must be WHITE
    start_resp = await async_client.post(f"/api/v1/mindquests/{mq_id}/start")
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["active_hat"] == "WHITE"
    assert "initial_turn" in start_data

    # 3. Complete each hat in mandatory sequence ending with BLUE
    for idx, expected_hat in enumerate(expected_sequence):
        submit_resp = await async_client.post(
            f"/api/v1/mindquests/{mq_id}/responses",
            json={
                "response": "Ein wichtiges Argument ist, dass wir sowohl Kosten als auch "
                "Umweltfolgen genau abwägen müssen."
            },
        )
        assert submit_resp.status_code == 200
        sub_data = submit_resp.json()
        assert sub_data["thinking_evaluation"]["score"] >= 0
        assert sub_data["german_evaluation"]["score"] >= 0
        assert "feedback" in sub_data
        assert sub_data["proposition"] is not None
        assert sub_data["proposition"]["improved_response"] != ""
        assert len(sub_data["proposition"]["highlights"]) >= 1

        advance_resp = await async_client.post(f"/api/v1/mindquests/{mq_id}/advance")
        assert advance_resp.status_code == 200
        adv_data = advance_resp.json()
        if idx < len(expected_sequence) - 1:
            assert adv_data["is_completed"] is False
            assert adv_data["next_hat"] == expected_sequence[idx + 1]
        else:
            assert expected_hat == "BLUE"
            assert adv_data["is_completed"] is True
            assert adv_data["final_reflection"] is not None

    # 5. Get Reflection (with single-MindQuest metrics)
    refl_resp = await async_client.get(f"/api/v1/mindquests/{mq_id}/reflection")
    assert refl_resp.status_code == 200
    refl_data = refl_resp.json()
    assert "thinking_summary" in refl_data
    assert refl_data["hats_completed"] == 6
    assert refl_data["hats_total"] == 6
    assert refl_data["thinking_overall"] is not None
    assert refl_data["german_overall"] is not None
    assert len(refl_data["thinking_dimensions"]) == 5
    assert len(refl_data["german_dimensions"]) == 5


@pytest.mark.asyncio
async def test_default_hat_order(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/mindquests",
        json={"topic": "Homeoffice in Deutschland", "target_level": "B2"},
    )
    assert resp.status_code == 201
    assert resp.json()["planned_hats"] == [
        "WHITE",
        "YELLOW",
        "GREEN",
        "RED",
        "BLACK",
        "BLUE",
    ]


@pytest.mark.asyncio
async def test_user_learning_profile_and_activities(async_client: AsyncClient):
    default_user_id = "00000000-0000-0000-0000-000000000001"

    profile_resp = await async_client.get(f"/api/v1/users/{default_user_id}/learning-profile")
    assert profile_resp.status_code == 200
    assert profile_resp.json()["user_id"] == default_user_id

    activities_resp = await async_client.get(f"/api/v1/users/{default_user_id}/activities")
    assert activities_resp.status_code == 200
    assert isinstance(activities_resp.json(), list)

    user_mqs_resp = await async_client.get(f"/api/v1/users/{default_user_id}/mindquests")
    assert user_mqs_resp.status_code == 200
    assert isinstance(user_mqs_resp.json(), list)


@pytest.mark.asyncio
async def test_api_error_handlers_and_edge_cases(async_client: AsyncClient, fake_llm_client):
    from uuid import uuid4

    from linguamentis.shared.exceptions import AIGatewayError

    missing_id = uuid4()

    # 1. 404 NotFoundError on unknown MindQuest
    resp_404 = await async_client.get(f"/api/v1/mindquests/{missing_id}")
    assert resp_404.status_code == 404
    assert resp_404.json()["error"] == "Not Found"

    # 2. 404 on missing reflection
    refl_404 = await async_client.get(f"/api/v1/mindquests/{missing_id}/reflection")
    assert refl_404.status_code == 404

    # 3. 422 Validation error on too short topic
    resp_422 = await async_client.post(
        "/api/v1/mindquests",
        json={"topic": "ab", "target_level": "B2"},
    )
    assert resp_422.status_code == 422

    # 4. Create valid MindQuest and test list + get + invalid state transition (400)
    create_resp = await async_client.post(
        "/api/v1/mindquests",
        json={"topic": "Künstliche Intelligenz in Schulen", "target_level": "B2"},
    )
    assert create_resp.status_code == 201
    mq_id = create_resp.json()["id"]

    list_resp = await async_client.get("/api/v1/mindquests")
    assert list_resp.status_code == 200
    assert any(item["id"] == mq_id for item in list_resp.json())

    get_resp = await async_client.get(f"/api/v1/mindquests/{mq_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["topic"] == "Künstliche Intelligenz in Schulen"

    # Submitting response before starting -> 400 Domain Violation
    bad_submit = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/responses",
        json={"response": "Zu früh geantwortet."},
    )
    assert bad_submit.status_code == 400
    assert bad_submit.json()["error"] == "Domain Violation"

    # Advancing before starting (in TOPIC_SELECTED) -> 400 Invalid State Transition
    bad_advance = await async_client.post(f"/api/v1/mindquests/{mq_id}/advance")
    assert bad_advance.status_code == 400
    assert bad_advance.json()["error"] == "Invalid State Transition"

    # Start twice -> second start triggers 400 Domain Violation
    await async_client.post(f"/api/v1/mindquests/{mq_id}/start")
    second_start = await async_client.post(f"/api/v1/mindquests/{mq_id}/start")
    assert second_start.status_code == 400
    assert second_start.json()["error"] == "Domain Violation"

    # 5. Simulate AIGatewayError -> 502 Bad Gateway
    fake_llm_client.error_to_raise = AIGatewayError("Upstream Gemini failure")
    try:
        resp_502 = await async_client.post(
            f"/api/v1/mindquests/{mq_id}/responses",
            json={"response": "Ein ernsthaftes Risiko besteht im Datenschutz."},
        )
        assert resp_502.status_code == 502
        assert resp_502.json()["error"] == "AI Gateway Failure"
    finally:
        fake_llm_client.error_to_raise = None

    # 6. Delete MindQuest -> 204, then GET returns 404, second DELETE returns 404
    del_resp = await async_client.delete(f"/api/v1/mindquests/{mq_id}")
    assert del_resp.status_code == 204
    after_del_get = await async_client.get(f"/api/v1/mindquests/{mq_id}")
    assert after_del_get.status_code == 404
    del_404 = await async_client.delete(f"/api/v1/mindquests/{missing_id}")
    assert del_404.status_code == 404

    # 7. Speech-to-Text endpoint (/api/v1/speech/transcribe) success and validation
    import base64

    valid_audio = base64.b64encode(b"fake-webm-audio-bytes").decode("ascii")
    stt_ok = await async_client.post(
        "/api/v1/speech/transcribe",
        json={"audio_base64": valid_audio, "mime_type": "audio/webm;codecs=opus"},
    )
    assert stt_ok.status_code == 200
    assert "Risiken" in stt_ok.json()["text"]

    stt_bad_mime = await async_client.post(
        "/api/v1/speech/transcribe",
        json={"audio_base64": valid_audio, "mime_type": "video/mp4"},
    )
    assert stt_bad_mime.status_code == 400


@pytest.mark.asyncio
async def test_conversation_mode_api_lifecycle(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/v1/mindquests",
        json={"topic": "Bargeldabschaffung in Europa", "target_level": "B2"},
    )
    assert create_resp.status_code == 201
    mq_id = create_resp.json()["id"]

    # 1. Open spoken conversation -> auto-starts MindQuest on WHITE hat and synthesizes speech
    open_resp = await async_client.post(f"/api/v1/mindquests/{mq_id}/conversation/opening")
    assert open_resp.status_code == 200
    open_data = open_resp.json()
    assert open_data["active_hat"] == "WHITE"
    assert "Bargeldabschaffung in Europa" in open_data["spoken_text"]
    assert open_data["audio_base64"] != ""
    assert open_data["is_completed"] is False

    # 2. Submit spoken turn -> evaluates Thinking & German, advances WHITE -> YELLOW
    turn_resp = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/conversation/turn",
        json={
            "transcript": (
                "Laut Bundesbank wird in Deutschland noch rund die Hälfte aller Einkäufe "
                "bar bezahlt."
            )
        },
    )
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()
    assert turn_data["thinking_evaluation"]["score"] >= 0
    assert turn_data["german_evaluation"]["score"] >= 0
    assert turn_data["transitioned_hat"] == "YELLOW"
    assert turn_data["active_hat"] == "YELLOW"
    assert turn_data["spoken_reply"] != ""
    assert turn_data["audio_base64"] != ""


@pytest.mark.asyncio
async def test_argue_mode_api_endpoints(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/v1/mindquests",
        json={
            "topic": "Vier-Tage-Woche in Deutschland",
            "target_level": "C1",
            "mode": "ARGUE",
        },
    )
    assert create_resp.status_code == 201
    mq_data = create_resp.json()
    mq_id = mq_data["id"]
    assert mq_data["mode"] == "ARGUE"
    assert mq_data["planned_hats"] == ["WHITE", "YELLOW", "GREEN", "RED", "BLACK"]

    # Selecting BLUE is rejected
    blue_resp = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/select-hat",
        json={"hat": "BLUE"},
    )
    assert blue_resp.status_code == 400

    # Selecting RED succeeds and activates RED
    sel_resp = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/select-hat",
        json={"hat": "RED"},
    )
    assert sel_resp.status_code == 200
    assert sel_resp.json()["active_hat"] == "RED"

    # Submitting response returns average_score > 80 with default FakeLLMClient
    sub_resp = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/responses",
        json={"response": "Spontan weckt diese Idee bei mir sowohl Neugier als auch Skepsis."},
    )
    assert sub_resp.status_code == 200
    assert sub_resp.json()["average_score"] > 80.0
    assert sub_resp.json()["round_should_complete"] is True

