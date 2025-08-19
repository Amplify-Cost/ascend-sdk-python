# test/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_register_and_login(test_client):
    # Register the test user
    register_response = await test_client.post("/auth/register", json={
        "email": "testuser@example.com",
        "password": "testpass"
    })

    # Acceptable responses: 200 OK or 400 if user already exists
    assert register_response.status_code in [200, 400]

    # Attempt login with the same credentials
    login_response = await test_client.post("/auth/token", json={
        "email": "testuser@example.com",
        "password": "testpass"
    })

    assert login_response.status_code == 200
    json_data = login_response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"
