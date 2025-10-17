import requests
import json

BASE_URL = "https://pilot.owkai.app"

# Login
login = requests.post(f"{BASE_URL}/auth/token", 
    json={"email":"admin@owkai.com","password":"admin123"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("🔧 Checking Smart Rules Display\n")

# Get current rules
resp = requests.get(f"{BASE_URL}/api/smart-rules", headers=headers)
if resp.status_code == 200:
    rules = resp.json()
    print(f"Found {len(rules) if isinstance(rules, list) else 'unknown'} rules\n")
    
    if isinstance(rules, list):
        for rule in rules[:3]:  # Show first 3
            print(f"Rule: {rule.get('name', 'Unnamed')}")
            print(f"  Description: {rule.get('description', 'N/A')}")
            print(f"  Natural Language: {rule.get('natural_language', 'N/A')}")
            print(f"  Conditions: {rule.get('conditions', 'N/A')}")
            print("-" * 40)

# Create a better formatted rule
print("\nCreating well-formatted rule...")
new_rule = {
    "natural_language": "Block all database deletions during weekends",
    "name": "Weekend Database Protection",
    "description": "Prevents any database deletion operations on Saturday and Sunday"
}

resp = requests.post(f"{BASE_URL}/api/smart-rules/generate-from-nl",
    json=new_rule, headers=headers)
    
if resp.status_code in [200, 201]:
    print("✅ Created formatted rule")
    result = resp.json()
    print(f"Generated conditions: {result.get('conditions', 'N/A')}")
