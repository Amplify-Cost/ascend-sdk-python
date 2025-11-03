import requests
import json
from datetime import datetime, timezone
import time

# Configuration
# API_BASE = "http://localhost:8000"
API_BASE = "https://pilot.owkai.app"  # For production

# Login and get token
def get_token():
    response = requests.post(f"{API_BASE}/auth/token", json={
        "email": "admin@owkai.com",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

# Send agent actions using correct endpoints
def send_agent_actions(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test actions to send
    test_actions = [
        {
            "agent_id": "ai-assistant-001",
            "action_type": "database_query",
            "tool_name": "sql_executor",
            "parameters": {"query": "SELECT * FROM customer_data"},
            "risk_level": "high"
        },
        {
            "agent_id": "chatbot-002",
            "action_type": "api_call",
            "tool_name": "payment_api",
            "parameters": {"endpoint": "/charge", "amount": 5000},
            "risk_level": "critical"
        },
        {
            "agent_id": "data-processor-003",
            "action_type": "file_access",
            "tool_name": "file_system",
            "parameters": {"path": "/sensitive/data.csv"},
            "risk_level": "high"
        }
    ]
    
    results = []
    
    # Try different endpoints
    endpoints = [
        "/api/authorization/test-action",
        "/agent-control/request-authorization"
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        for action in test_actions:
            print(f"  Sending: {action['agent_id']} - {action['action_type']}")
            response = requests.post(
                f"{API_BASE}{endpoint}",
                headers=headers,
                json=action
            )
            
            if response.status_code == 200:
                print(f"    ✅ Success: {response.json()}")
                results.append(response.json())
                break  # Found working endpoint
            else:
                print(f"    ❌ Failed: {response.status_code}")
        
        if results:
            break
    
    return results

# Get pending actions
def get_pending_actions(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/authorization/pending-actions", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get pending actions: {response.status_code}")
        return []

# Main execution
if __name__ == "__main__":
    print("🚀 Testing Authorization Endpoints...")
    
    token = get_token()
    if not token:
        print("❌ Failed to authenticate")
        exit(1)
    
    print(f"✅ Authenticated successfully")
    
    # Send test actions
    results = send_agent_actions(token)
    
    # Get pending actions
    print("\n📋 Checking pending actions...")
    pending = get_pending_actions(token)
    
    if pending:
        print(f"Found {len(pending)} pending actions:")
        for action in pending:
            print(f"  - {action.get('agent_id', 'Unknown')} : {action.get('action_type', 'Unknown')}")
    else:
        print("No pending actions found")
    
    # Check dashboard
    print("\n📊 Checking authorization dashboard...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/authorization/dashboard", headers=headers)
    if response.status_code == 200:
        dashboard = response.json()
        print(f"Dashboard data: {json.dumps(dashboard, indent=2)}")
