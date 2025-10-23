"""
Test automation endpoints to verify they work
"""
import requests
import json
from datetime import datetime

print("=" * 80)
print("🧪 TESTING AUTOMATION ENDPOINTS")
print("=" * 80)
print()

BASE_URL = "http://localhost:8000"

# You'll need to replace this with actual session cookie
# Get it from browser DevTools → Application → Cookies → owai_session
COOKIE = "owai_session=YOUR_SESSION_COOKIE_HERE"

headers = {
    "Cookie": COOKIE,
    "Content-Type": "application/json"
}

print("⚠️  NOTE: Update COOKIE variable with your actual session cookie")
print("   Get it from: Browser DevTools → Application → Cookies → owai_session")
print()

tests = [
    {
        "name": "1. LIST Playbooks (GET)",
        "method": "GET",
        "url": f"{BASE_URL}/api/authorization/automation/playbooks",
        "expected_status": 200
    },
    {
        "name": "2. CREATE Playbook (POST)",
        "method": "POST",
        "url": f"{BASE_URL}/api/authorization/automation/playbooks",
        "body": {
            "id": f"pb-test-{int(datetime.now().timestamp())}",
            "name": "Test Playbook Created via API",
            "description": "Testing CREATE endpoint",
            "status": "active",
            "risk_level": "low",
            "approval_required": False,
            "trigger_conditions": {"test": True},
            "actions": [{"type": "log", "message": "Test action"}]
        },
        "expected_status": 200
    },
    {
        "name": "3. LIST Playbooks Again (verify CREATE worked)",
        "method": "GET",
        "url": f"{BASE_URL}/api/authorization/automation/playbooks",
        "expected_status": 200
    },
    {
        "name": "4. TOGGLE Playbook (POST)",
        "method": "POST",
        "url": f"{BASE_URL}/api/authorization/automation/playbook/pb-001/toggle",
        "expected_status": 200
    },
    {
        "name": "5. EXECUTE Playbook (POST)",
        "method": "POST",
        "url": f"{BASE_URL}/api/authorization/automation/execute-playbook",
        "body": {
            "playbook_id": "pb-001",
            "input_data": {"test": True}
        },
        "expected_status": 200
    },
    {
        "name": "6. LIST Active Workflows (GET)",
        "method": "GET",
        "url": f"{BASE_URL}/api/authorization/orchestration/active-workflows",
        "expected_status": 200
    }
]

print("🚀 Starting tests...\n")

# Manual testing guide
print("MANUAL TEST INSTRUCTIONS:")
print("-" * 80)
print("Since we need authentication, test manually:")
print()
for i, test in enumerate(tests, 1):
    print(f"{i}. {test['name']}")
    print(f"   Method: {test['method']}")
    print(f"   URL: {test['url']}")
    if 'body' in test:
        print(f"   Body: {json.dumps(test['body'], indent=6)}")
    print()

print("-" * 80)
print("\nOR use curl commands:")
print()

for test in tests:
    if test['method'] == 'GET':
        print(f"# {test['name']}")
        print(f"curl -X GET '{test['url']}' \\")
        print(f"  -H 'Cookie: owai_session=YOUR_SESSION' \n")
    else:
        print(f"# {test['name']}")
        print(f"curl -X POST '{test['url']}' \\")
        print(f"  -H 'Cookie: owai_session=YOUR_SESSION' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        if 'body' in test:
            print(f"  -d '{json.dumps(test['body'])}'\n")

print("=" * 80)
