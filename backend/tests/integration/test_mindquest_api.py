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
