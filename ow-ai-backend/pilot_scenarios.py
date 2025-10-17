import requests
import json
import time

BASE_URL = "https://pilot.owkai.app"

print("🎬 PILOT DEMO SCENARIOS")
print("=" * 50)

# Login first
login = requests.post(f"{BASE_URL}/auth/token", 
    json={"email":"admin@owkai.com","password":"admin123"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Scenario 1: Suspicious Activity Detection
print("\n📌 SCENARIO 1: AI Agent Suspicious Activity")
print("An AI agent attempts to access sensitive data...")
time.sleep(2)

alert_data = {
    "title": "PILOT DEMO: Suspicious Access Attempt",
    "message": "CustomerBot tried to access HR salary data - unauthorized attempt",
    "severity": "critical",
    "type": "security_breach",
    "source": "CustomerBot-DEMO"
}
resp = requests.post(f"{BASE_URL}/alerts", json=alert_data, headers=headers)
print("  → Alert created: Unauthorized access detected")
print("  → Security team notified")
print("  → Access BLOCKED")

# Scenario 2: Policy Enforcement
print("\n📌 SCENARIO 2: Real-time Policy Enforcement")
print("Marketing AI requests customer database access...")
time.sleep(2)

eval_data = {
    "resource": "database.customers.full_records",
    "action": "export",
    "principal": "Marketing-AI-DEMO"
}
resp = requests.post(f"{BASE_URL}/api/authorization/policies/evaluate-realtime",
    json=eval_data, headers=headers)
    
print("  → Policy evaluated in real-time")
print("  → Decision: REQUIRES APPROVAL")
print("  → Approval request sent to admin")

# Scenario 3: Smart Rule Creation
print("\n📌 SCENARIO 3: Business Rule → Technical Rule")
print("Business requirement: 'No data exports on weekends'")
time.sleep(2)

rule_data = {
    "natural_language": "Prevent any data exports on Saturdays and Sundays"
}
resp = requests.post(f"{BASE_URL}/api/smart-rules/generate-from-nl",
    json=rule_data, headers=headers)
    
print("  → AI converts to technical rule")
print("  → Rule active immediately")
print("  → Weekend data protection enabled")

print("\n" + "=" * 50)
print("✅ All pilot scenarios ready!")
print("=" * 50)
