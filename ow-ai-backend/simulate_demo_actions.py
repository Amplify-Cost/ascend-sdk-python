#!/usr/bin/env python3
"""
OW-KAI Demo Action Simulator
Uses proven /agent-actions endpoint
"""

import time
import requests
from datetime import datetime

# Demo scenarios using the working agent-actions format
DEMO_SCENARIOS = [
    # Low-risk actions
    {
        "agent_id": "data-analyst-bot",
        "action_type": "read",
        "description": "Reading Q3 sales data for analysis",
        "tool_name": "data-reader",
        "risk_level": "low",
        "delay": 3
    },
    {
        "agent_id": "research-assistant",
        "action_type": "list",
        "description": "Listing available research documents",
        "tool_name": "file-explorer",
        "risk_level": "low",
        "delay": 2
    },
    {
        "agent_id": "report-generator",
        "action_type": "read",
        "description": "Accessing monthly performance metrics",
        "tool_name": "metrics-reader",
        "risk_level": "low",
        "delay": 3
    },
    
    # Medium-risk actions
    {
        "agent_id": "data-processor",
        "action_type": "write",
        "description": "Updating customer contact information",
        "tool_name": "database-writer",
        "risk_level": "medium",
        "delay": 5
    },
    {
        "agent_id": "api-integration-bot",
        "action_type": "execute",
        "description": "Processing batch payment transactions",
        "tool_name": "stripe-api",
        "risk_level": "high",
        "delay": 4
    },
    {
        "agent_id": "backup-automation",
        "action_type": "write",
        "description": "Creating automated database backup",
        "tool_name": "backup-manager",
        "risk_level": "medium",
        "delay": 4
    },
    
    # High-risk actions
    {
        "agent_id": "admin-automation",
        "action_type": "delete",
        "description": "Removing old archived system logs",
        "tool_name": "log-cleaner",
        "risk_level": "high",
        "delay": 6
    },
    {
        "agent_id": "database-admin-bot",
        "action_type": "modify",
        "description": "Optimizing production database indexes",
        "tool_name": "db-optimizer",
        "risk_level": "high",
        "delay": 5
    },
    
    # Critical-risk actions
    {
        "agent_id": "security-bot",
        "action_type": "delete",
        "description": "Purging expired user credentials from production",
        "tool_name": "credential-manager",
        "risk_level": "critical",
        "delay": 7
    },
]

def login_and_get_token():
    """Login and get authentication token"""
    api_base = "https://pilot.owkai.app"
    
    print("🔐 Logging in as admin...")
    
    try:
        response = requests.post(
            f"{api_base}/auth/token",
            json={
                "email": "admin@owkai.com",
                "password": "admin123"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Authentication successful!\n")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def simulate_agent_action(scenario, token):
    """Send agent action using proven /agent-actions endpoint"""
    
    api_base = "https://pilot.owkai.app"
    endpoint = f"{api_base}/agent-actions"
    
    payload = {
        "agent_id": scenario["agent_id"],
        "action_type": scenario["action_type"],
        "description": scenario["description"],
        "tool_name": scenario.get("tool_name", "unknown"),
        "risk_level": scenario.get("risk_level", "medium")
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            action_id = data.get('action_id', 'N/A')
            status = data.get('status', 'N/A')
            
            print(f"✅ Action created: {scenario['agent_id']}")
            print(f"   └─ ID: {action_id}")
            print(f"   └─ Type: {scenario['action_type']}")
            print(f"   └─ Risk: {scenario['risk_level']}")
            print(f"   └─ Status: {status}\n")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}\n")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False

def run_demo_simulation():
    """Run through all demo scenarios"""
    
    print("\n" + "=" * 70)
    print("OW-KAI DEMO ACTION SIMULATOR")
    print("=" * 70)
    
    # Login first
    token = login_and_get_token()
    if not token:
        print("\n❌ Cannot proceed without authentication\n")
        return
    
    print(f"\n🎬 Starting demo simulation...")
    print(f"📡 API: https://pilot.owkai.app")
    print(f"⏱️  Total scenarios: {len(DEMO_SCENARIOS)}")
    print(f"⏳ Estimated time: ~40 seconds")
    print("\n" + "=" * 70 + "\n")
    
    success_count = 0
    
    for i, scenario in enumerate(DEMO_SCENARIOS, 1):
        print(f"[{i}/{len(DEMO_SCENARIOS)}] Simulating: {scenario['description']}")
        
        if simulate_agent_action(scenario, token):
            success_count += 1
        
        # Wait before next action for demo pacing
        if i < len(DEMO_SCENARIOS):
            delay = scenario.get('delay', 3)
            print(f"⏳ Waiting {delay} seconds before next action...\n")
            time.sleep(delay)
    
    print("=" * 70)
    print(f"\n✅ Demo simulation complete!")
    print(f"   └─ Successful: {success_count}/{len(DEMO_SCENARIOS)}")
    print(f"   └─ Failed: {len(DEMO_SCENARIOS) - success_count}\n")

if __name__ == "__main__":
    print("\n⚠️  This will send realistic agent actions to your OW-KAI platform")
    print("⚠️  Make sure your browser is open to https://pilot.owkai.app")
    
    confirm = input("\n🎬 Ready to start demo simulation? (yes/no): ")
    
    if confirm.lower() == 'yes':
        run_demo_simulation()
    else:
        print("\n❌ Simulation cancelled\n")
