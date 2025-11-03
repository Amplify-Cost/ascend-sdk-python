#!/usr/bin/env python3
"""
Test acknowledge endpoint directly
"""
import requests

# Get auth token
login_response = requests.post(
    "http://localhost:8000/auth/token",
    data={"username": "admin@owkai.com", "password": "Admin123"}
)

print(f"Login status: {login_response.status_code}")

if login_response.status_code == 200:
    cookies = login_response.cookies

    # Get CSRF token from cookies
    csrf_token = cookies.get("owai_csrf")
    print(f"CSRF token: {csrf_token[:20]}..." if csrf_token else "No CSRF token")

    # Try to acknowledge alert ID 1
    alert_id = 1
    acknowledge_response = requests.post(
        f"http://localhost:8000/api/alerts/{alert_id}/acknowledge",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token} if csrf_token else {}
    )

    print(f"\nAcknowledge alert {alert_id}:")
    print(f"Status: {acknowledge_response.status_code}")
    print(f"Response: {acknowledge_response.text}")

    # Try escalate
    escalate_response = requests.post(
        f"http://localhost:8000/api/alerts/{alert_id}/escalate",
        cookies=cookies,
        headers={"X-CSRF-Token": csrf_token} if csrf_token else {}
    )

    print(f"\nEscalate alert {alert_id}:")
    print(f"Status: {escalate_response.status_code}")
    print(f"Response: {escalate_response.text}")
else:
    print(f"Login failed: {login_response.text}")
