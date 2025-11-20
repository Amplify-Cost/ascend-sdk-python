#!/usr/bin/env python3
"""Simple API test to verify endpoints work"""
import requests
import json

API_URL = "https://pilot.owkai.app"

# Authenticate
print("🔐 Authenticating...")
auth_response = requests.post(
    f"{API_URL}/api/auth/token",
    json={"email": "admin@owkai.com", "password": "admin123"}
)
auth_data = auth_response.json()
token = auth_data.get("access_token")
print(f"✅ Token: {token[:30]}...")

# Test agent action
print("\n📊 Creating agent action...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

action_data = {
    "agent_id": "test-demo-agent-001",
    "action_type": "database_read",
    "description": "Testing database read operation for analytics dashboard"
}

response = requests.post(
    f"{API_URL}/api/agent-action",
    headers=headers,
    json=action_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
