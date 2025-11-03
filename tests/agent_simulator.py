#!/usr/bin/env python3
"""
Enterprise Agent Simulator - Submits Actions via API
This simulates how real AI agents would connect to your OW-KAI platform
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Your API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://pilot.owkai.app")
ADMIN_EMAIL = "admin@owkai.com"
ADMIN_REDACTED-CREDENTIAL = "admin123"

# Enterprise AI Agent Scenarios
AGENT_SCENARIOS = [
    {
        "agent_id": "DataAnalyzer_AI",
        "tool_name": "PandasAI",
        "action_type": "database_query",
        "description": "Query customer purchase history for Q4 analytics report",
        "risk_level": "low"
    },
    {
        "agent_id": "EmailBot_AI",
        "tool_name": "SendGrid",
        "action_type": "send_email",
        "description": "Send automated welcome emails to 50 new enterprise customers",
        "risk_level": "low"
    },
    {
        "agent_id": "CodeReviewer_AI",
        "tool_name": "GitHub Actions",
        "action_type": "code_deployment",
        "description": "Deploy hotfix to production API gateway",
        "risk_level": "medium"
    },
    {
        "agent_id": "SecurityScanner_AI",
        "tool_name": "Nessus",
        "action_type": "firewall_modification",
        "description": "Modify production firewall rules for new microservice deployment",
        "risk_level": "high"
    },
    {
        "agent_id": "BackupManager_AI",
        "tool_name": "AWS S3",
        "action_type": "delete_files",
        "description": "Delete production database backups older than 90 days (2.5TB)",
        "risk_level": "high"
    },
    {
        "agent_id": "PaymentProcessor_AI",
        "tool_name": "Stripe API",
        "action_type": "financial_transaction",
        "description": "Process bulk vendor payments: 200 transactions totaling $2.5M",
        "risk_level": "high"
    }
]

def get_auth_token():
    """Authenticate and get access token"""
    print("\n🔐 Authenticating with OW-KAI API...")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/token",
            headers={"Content-Type": "application/json"},
            json={"email": ADMIN_EMAIL, "password": ADMIN_REDACTED-CREDENTIAL},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error authenticating: {e}")
        return None

def submit_agent_action(token, agent_data):
    """Submit an agent action via API"""
    
    emoji = "🟢" if agent_data['risk_level'] == 'low' else "🟡" if agent_data['risk_level'] == 'medium' else "🔴"
    print(f"\n{emoji} Submitting: {agent_data['agent_id']} - {agent_data['action_type']}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Try multiple possible endpoints
    endpoints = [
        "/agent-action",
        "/agent-actions",
        "/agent-control/request-authorization"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                headers=headers,
                json=agent_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✅ Success via {endpoint}")
                print(f"   Action ID: {result.get('action_id') or result.get('authorization_id') or result.get('id')}")
                return True
            elif response.status_code == 404:
                continue  # Try next endpoint
            else:
                print(f"   ⚠️  {endpoint} returned {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ⚠️  {endpoint} error: {e}")
            continue
    
    print(f"   ❌ Failed to submit via any endpoint")
    return False

def verify_pending_actions(token):
    """Check how many pending actions exist"""
    print("\n📊 Checking pending actions...")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/agent-control/pending-actions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            actions = response.json()
            count = len(actions) if isinstance(actions, list) else actions.get('count', 0)
            print(f"✅ Found {count} pending actions in Authorization Center")
            return count
        else:
            print(f"⚠️  Could not verify: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking pending actions: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("🤖 ENTERPRISE AI AGENT SIMULATOR")
    print("="*60)
    print("\nThis script simulates AI agents submitting actions to your")
    print("OW-KAI platform via API - just like in production!")
    print("="*60)
    
    # Step 1: Authenticate
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return 1
    
    # Step 2: Check current state
    initial_count = verify_pending_actions(token)
    
    # Step 3: Submit agent actions
    print("\n" + "="*60)
    print("📤 SUBMITTING AGENT ACTIONS VIA API")
    print("="*60)
    
    success_count = 0
    for agent_data in AGENT_SCENARIOS:
        if submit_agent_action(token, agent_data):
            success_count += 1
    
    # Step 4: Verify results
    print("\n" + "="*60)
    print("📊 VERIFICATION")
    print("="*60)
    
    final_count = verify_pending_actions(token)
    
    print(f"\n✅ Successfully submitted {success_count}/{len(AGENT_SCENARIOS)} agent actions")
    
    if final_count and initial_count is not None:
        new_actions = final_count - initial_count
        if new_actions > 0:
            print(f"📈 Pending actions increased by {new_actions}")
    
    print("\n" + "="*60)
    print("🎯 READY FOR DEMO!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Open: https://pilot.owkai.app")
    print("2. Navigate to: Authorization Center")
    print("3. You should see your new pending actions")
    print("4. Start recording your demo!")
    print("="*60 + "\n")
    
    return 0

if __name__ == "__main__":
    exit(main())
