import pytest
from datetime import datetime, UTC

@pytest.mark.asyncio
async def test_submit_manual_agent_action(test_client):
    # Register a user
    await test_client.post("/auth/register", json={
        "email": "manualuser@example.com",
        "password": "securepass"
    })

    # Login the user
    login_response = await test_client.post("/auth/token", json={
        "email": "manualuser@example.com",
        "password": "securepass"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit an agent action
    response = await test_client.post("/agent-action", headers=headers, json={
        "agent_id": "agent-001",
        "action_type": "inference-query",
        "description": "Testing from pytest",
        "tool_name": "OWASP-ZAP",
        "timestamp": datetime.now(UTC).isoformat()
    })

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["agent_id"] == "agent-001"
