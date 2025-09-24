#!/usr/bin/env python3
"""
Simple test script for OW-AI Authorization System
Run this after deploying to test the functionality
"""

import requests
import json
import time

# Configuration - UPDATE THESE VALUES
API_BASE = "https://pilot.owkai.app"  # AWS Production URL
TOKEN = "your-auth-token-here"  # Get this from your login

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_high_risk_action():
    """Test requesting authorization for a high-risk action"""
    print("🧪 Testing high-risk action authorization...")
    
    data = {
        "agent_id": "test-agent-001",
        "action_type": "delete_database",
        "description": "Delete production database for maintenance",
        "risk_level": "critical",
        "target_system": "production_database",
        "tool_name": "mysql_client",
        "action_payload": {
            "database_name": "production_db",
            "backup_created": True,
            "maintenance_window": "2025-07-23T02:00:00Z"
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/agent-control/request-authorization",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Authorization requested successfully!")
            print(f"   ID: {result.get('authorization_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Risk Score: {result.get('risk_score')}/100")
            return result.get('authorization_id')
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return None

def test_low_risk_action():
    """Test requesting authorization for a low-risk action"""
    print("\n🧪 Testing low-risk action authorization...")
    
    data = {
        "agent_id": "test-agent-002",
        "action_type": "health_check",
        "description": "Routine system health check",
        "risk_level": "low",
        "target_system": "monitoring_system",
        "action_payload": {"check_type": "basic"}
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/agent-control/request-authorization",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Low-risk action processed!")
            print(f"   Status: {result.get('status')}")
            print(f"   Should be: auto_approved")
        else:
            print(f"❌ Request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_pending_actions():
    """Check what actions are pending approval"""
    print("\n🧪 Checking pending authorizations...")
    
    try:
        response = requests.get(
            f"{API_BASE}/agent-control/pending-authorizations",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('pending_count', 0)
            print(f"✅ Found {count} pending authorization(s)")
            
            if count > 0:
                print("   Pending actions:")
                for action in result.get('actions', [])[:3]:
                    print(f"   • ID {action['id']}: {action['agent_id']} - {action['action_type']} (Risk: {action['ai_risk_score']}/100)")
        else:
            print(f"❌ Request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def approve_action(auth_id):
    """Approve a specific action"""
    print(f"\n🧪 Approving authorization {auth_id}...")
    
    data = {
        "decision": "approve",
        "notes": "Approved by automated test script"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/agent-control/authorize/{auth_id}",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Action approved successfully!")
        else:
            print(f"❌ Approval failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def main():
    """Run all tests"""
    print("🔒 OW-AI Authorization System Test Suite")
    print("=" * 50)
    
    # Test 1: Low-risk action (should auto-approve)
    test_low_risk_action()
    
    # Test 2: High-risk action (should require approval)
    auth_id = test_high_risk_action()
    
    # Test 3: Check pending actions
    check_pending_actions()
    
    # Test 4: Approve the high-risk action (if we got an ID)
    if auth_id:
        approve_action(auth_id)
    
    print("\n🎉 Test suite completed!")
    print("\n📋 Next steps:")
    print("1. Check your 'Authorization Center' tab in the dashboard")
    print("2. Verify you can see and approve/deny actions")
    print("3. Test with real customer scenarios")

if __name__ == "__main__":
    if TOKEN == "your-auth-token-here":
        print("❌ Please update the TOKEN variable with your actual auth token")
        print("   You can get this by logging into your app and checking localStorage")
        exit(1)
    
    main()