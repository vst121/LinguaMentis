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
    # 1. Create MindQuest
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

    # 2. Start MindQuest
    start_resp = await async_client.post(f"/api/v1/mindquests/{mq_id}/start")
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["active_hat"] == "BLACK"
    assert "initial_turn" in start_data

    # 3. Submit Response
    submit_resp = await async_client.post(
        f"/api/v1/mindquests/{mq_id}/responses",
        json={
            "response": "Ein großes Risiko ist, dass Plastikersatzstoffe oft teurer sind "
            "und nicht recycelt werden können."
        },
    )
    assert submit_resp.status_code == 200
    sub_data = submit_resp.json()
    assert sub_data["thinking_evaluation"]["score"] >= 0
    assert sub_data["german_evaluation"]["score"] >= 0
    assert "feedback" in sub_data

    # 4. Advance MindQuest
    advance_resp = await async_client.post(f"/api/v1/mindquests/{mq_id}/advance")
    assert advance_resp.status_code == 200
    adv_data = advance_resp.json()
    assert adv_data["is_completed"] is True
    assert adv_data["final_reflection"] is not None

    # 5. Get Reflection
    refl_resp = await async_client.get(f"/api/v1/mindquests/{mq_id}/reflection")
    assert refl_resp.status_code == 200
    assert "thinking_summary" in refl_resp.json()


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

