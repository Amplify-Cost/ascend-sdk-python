"""Debug authentication endpoint"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

print("=== Testing Auth Endpoints ===\n")

# Test 1: Form data (OAuth2 style)
print("Test 1: OAuth2 form data")
response = client.post("/auth/token", data={
    "username": "admin@owkai.com",
    "password": "Admin123!@#"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Success! Token: {response.json().get('access_token', 'N/A')[:50]}...")
else:
    print(f"Error: {response.text[:200]}")

# Test 2: JSON body
print("\nTest 2: JSON body")
response = client.post("/auth/token", json={
    "email": "admin@owkai.com",
    "password": "Admin123!@#"
})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Success! Token: {response.json().get('access_token', 'N/A')[:50]}...")
else:
    print(f"Error: {response.text[:200]}")
