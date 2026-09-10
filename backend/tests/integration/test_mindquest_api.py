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
