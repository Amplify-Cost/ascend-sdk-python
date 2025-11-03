import requests
import json
from datetime import datetime, timezone
import time

# Configuration
API_BASE = "https://pilot.owkai.app"
# API_BASE = "http://localhost:8000"  # Use for local testing

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

# Send various agent actions
def send_agent_actions(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Different types of agent actions for testing
    agent_actions = [
        {
            "agent_id": "ai-assistant-001",
            "action_type": "database_query",
            "tool_name": "sql_executor",
            "parameters": {"query": "SELECT * FROM customer_data", "database": "production"},
            "risk_level": "high",
            "requires_approval": True,
            "context": {"purpose": "Customer analytics report", "requestor": "marketing-team"}
        },
        {
            "agent_id": "chatbot-002",
            "action_type": "api_call",
            "tool_name": "external_api",
            "parameters": {"endpoint": "https://api.payment.com/charge", "method": "POST", "amount": 5000},
            "risk_level": "critical",
            "requires_approval": True,
            "context": {"purpose": "Process payment", "customer_id": "CUST-12345"}
        },
        {
            "agent_id": "data-processor-003",
            "action_type": "file_access",
            "tool_name": "file_system",
            "parameters": {"action": "read", "path": "/sensitive/financial_records.xlsx"},
            "risk_level": "high",
            "requires_approval": True,
            "context": {"purpose": "Quarterly audit", "department": "finance"}
        },
        {
            "agent_id": "automation-bot-004",
            "action_type": "system_command",
            "tool_name": "shell_executor",
            "parameters": {"command": "restart_service", "service": "payment_gateway"},
            "risk_level": "critical",
            "requires_approval": True,
            "context": {"purpose": "Maintenance window", "scheduled": "true"}
        },
        {
            "agent_id": "analytics-agent-005",
            "action_type": "data_export",
            "tool_name": "export_manager",
            "parameters": {"format": "csv", "data_type": "user_profiles", "count": 10000},
            "risk_level": "medium",
            "requires_approval": True,
            "context": {"purpose": "Marketing campaign", "approved_by": "pending"}
        },
        {
            "agent_id": "support-bot-006",
            "action_type": "user_modification",
            "tool_name": "user_manager",
            "parameters": {"action": "reset_password", "user_id": "USER-789"},
            "risk_level": "medium",
            "requires_approval": False,
            "context": {"ticket_id": "TICK-4567", "reason": "User request"}
        },
        {
            "agent_id": "ml-model-007",
            "action_type": "model_training",
            "tool_name": "ml_pipeline",
            "parameters": {"dataset": "customer_behavior", "algorithm": "neural_network"},
            "risk_level": "low",
            "requires_approval": False,
            "context": {"experiment_id": "EXP-2024-10", "gpu_required": "true"}
        },
        {
            "agent_id": "compliance-checker-008",
            "action_type": "audit_log_access",
            "tool_name": "audit_viewer",
            "parameters": {"date_range": "last_30_days", "filter": "security_events"},
            "risk_level": "low",
            "requires_approval": False,
            "context": {"compliance_check": "SOC2", "auditor": "internal"}
        }
    ]
    
    results = []
    for i, action in enumerate(agent_actions):
        print(f"\nSending action {i+1}/{len(agent_actions)}: {action['agent_id']} - {action['action_type']}")
        
        # Send to authorization endpoint
        response = requests.post(
            f"{API_BASE}/api/authorization/evaluate",
            headers=headers,
            json=action
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status: {result.get('status', 'SENT')}")
            results.append(result)
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    return results

# Main execution
if __name__ == "__main__":
    print("🚀 Starting Agent Action Test...")
    
    # Get token
    token = get_token()
    if not token:
        print("❌ Failed to authenticate")
        exit(1)
    
    print(f"✅ Authenticated successfully")
    
    # Send actions
    results = send_agent_actions(token)
    
    print(f"\n📊 Summary:")
    print(f"Total actions sent: {len(results)}")
    approved = sum(1 for r in results if r.get('status') == 'approved')
    pending = sum(1 for r in results if r.get('status') == 'pending')
    denied = sum(1 for r in results if r.get('status') == 'denied')
    
    print(f"Approved: {approved}")
    print(f"Pending: {pending}")
    print(f"Denied: {denied}")
