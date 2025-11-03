import requests
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"

print("🎯 OW-AI Platform Demo Data Creator")
print("=" * 50)

# Step 1: Login
print("\n📌 Step 1: Logging in as admin...")
login_response = requests.post(
    f"{BASE_URL}/auth/token",
    json={"email": "admin@owkai.com", "password": "admin123"},
    headers={"Content-Type": "application/json"}
)

if login_response.status_code != 200:
    print("❌ Failed to login. Check credentials.")
    exit()

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ Logged in successfully!")

# Step 2: Create Policies
print("\n📌 Step 2: Creating security policies...")
policies = [
    {
        "name": "Customer Database Access Control",
        "description": "Restricts AI agents from accessing sensitive customer data without approval",
        "resource": "database.customers.personal_info",
        "action": "read",
        "effect": "deny",
        "risk_level": "high",
        "requires_approval": True,
        "conditions": {"time_restriction": "business_hours_only"}
    },
    {
        "name": "Production File Deletion Block",
        "description": "Prevents any AI agent from deleting production files",
        "resource": "filesystem.production.*",
        "action": "delete",
        "effect": "deny",
        "risk_level": "critical",
        "requires_approval": False
    },
    {
        "name": "API Rate Limiting",
        "description": "Limits external API calls to prevent abuse",
        "resource": "api.external.*",
        "action": "call",
        "effect": "allow",
        "risk_level": "medium",
        "conditions": {"max_calls": 100, "time_window": "1h"}
    },
    {
        "name": "Financial Data Protection",
        "description": "Protects financial records from unauthorized access",
        "resource": "database.financial.*",
        "action": "*",
        "effect": "deny",
        "risk_level": "critical",
        "requires_approval": True
    }
]

for policy in policies:
    resp = requests.post(f"{BASE_URL}/api/authorization/policies", json=policy, headers=headers)
    if resp.status_code in [200, 201]:
        print(f"  ✅ Created: {policy['name']}")
    else:
        print(f"  ⚠️  Skipped: {policy['name']} (may already exist)")

# Step 3: Create Alerts
print("\n📌 Step 3: Creating security alerts...")
alerts = [
    {
        "title": "⚠️ Unusual Database Access Pattern",
        "message": "CustomerService-Bot accessed 523 customer records in 2 minutes - potential data scraping attempt",
        "severity": "high",
        "type": "anomaly",
        "source": "CustomerService-Bot",
        "metadata": {
            "records_accessed": 523,
            "time_window": "2 minutes",
            "normal_rate": "10-20 per minute"
        }
    },
    {
        "title": "🌙 After-Hours Activity Detected",
        "message": "DataAnalysis-Agent accessed production files at 3:47 AM EST - outside normal operation hours",
        "severity": "medium",
        "type": "suspicious_activity",
        "source": "DataAnalysis-Agent",
        "metadata": {
            "access_time": "03:47 AM",
            "files_accessed": 15,
            "location": "production/reports"
        }
    },
    {
        "title": "🔒 Repeated Authorization Failures",
        "message": "Marketing-Bot attempted unauthorized access to financial database 5 times in last hour",
        "severity": "high",
        "type": "security",
        "source": "Marketing-Bot",
        "metadata": {
            "failed_attempts": 5,
            "target": "database.financial.transactions",
            "time_span": "1 hour"
        }
    },
    {
        "title": "📊 Abnormal Data Export Volume",
        "message": "Analytics-Agent exported 10GB of data - 500% above normal volume",
        "severity": "medium",
        "type": "data_exfiltration",
        "source": "Analytics-Agent",
        "metadata": {
            "data_volume": "10GB",
            "normal_volume": "2GB",
            "increase_percentage": "500%"
        }
    }
]

for alert in alerts:
    resp = requests.post(f"{BASE_URL}/alerts", json=alert, headers=headers)
    if resp.status_code in [200, 201]:
        print(f"  ✅ Created: {alert['title']}")
    else:
        print(f"  ⚠️  Skipped: {alert['title']}")

# Step 4: Create Smart Rules
print("\n📌 Step 4: Creating AI-generated smart rules...")
smart_rules = [
    {
        "natural_language": "Block any file deletion on production servers after 6 PM",
        "name": "After-Hours File Protection",
        "description": "Prevents file deletions during non-business hours"
    },
    {
        "natural_language": "Alert when any agent accesses more than 100 customer records in 5 minutes",
        "name": "Bulk Access Detection",
        "description": "Monitors for potential data scraping"
    }
]

for rule in smart_rules:
    # Generate rule from natural language
    resp = requests.post(
        f"{BASE_URL}/api/smart-rules/generate-from-nl",
        json={"natural_language": rule["natural_language"]},
        headers=headers
    )
    if resp.status_code in [200, 201]:
        print(f"  ✅ Generated: {rule['name']}")

# Step 5: Create Demo Authorization Requests
print("\n📌 Step 5: Creating recent authorization requests...")
auth_requests = [
    {
        "agent": "CustomerService-Bot",
        "resource": "database.customers.contact_info",
        "action": "read",
        "status": "approved",
        "risk_score": 0.3,
        "approver": "admin@owkai.com"
    },
    {
        "agent": "Marketing-Bot",
        "resource": "database.financial.budgets",
        "action": "read",
        "status": "denied",
        "risk_score": 0.9,
        "reason": "Insufficient privileges for financial data"
    },
    {
        "agent": "DataAnalysis-Agent",
        "resource": "filesystem.reports.generate",
        "action": "write",
        "status": "pending_approval",
        "risk_score": 0.6
    }
]

for req in auth_requests:
    resp = requests.post(
        f"{BASE_URL}/api/authorization/requests",
        json=req,
        headers=headers
    )
    if resp.status_code in [200, 201]:
        print(f"  ✅ Created: {req['agent']} - {req['status']}")

print("\n" + "=" * 50)
print("✅ DEMO ENVIRONMENT READY!")
print("=" * 50)
print("\n📋 What was created:")
print("  • 4 Security Policies")
print("  • 4 Active Alerts") 
print("  • 2 Smart Rules")
print("  • 3 Authorization Requests")
print("\n🎬 Your platform is ready for demo recording!")
