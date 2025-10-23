import requests

BASE_URL = "https://pilot.owkai.app"

print("🔍 Debugging API Endpoints\n")

# Login first
login = requests.post(f"{BASE_URL}/auth/token", 
    json={"email":"admin@owkai.com","password":"admin123"})
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Check available endpoints from API docs
endpoints_to_test = [
    ("GET", "/alerts"),
    ("POST", "/alerts"),
    ("POST", "/api/alerts"),
    ("POST", "/api/alerts/create"),
    ("GET", "/api/alerts"),
    ("POST", "/alerts/new"),
]

for method, endpoint in endpoints_to_test:
    url = f"{BASE_URL}{endpoint}"
    if method == "GET":
        resp = requests.get(url, headers=headers)
    else:
        resp = requests.post(url, json={}, headers=headers)
    
    print(f"{method:6} {endpoint:30} → {resp.status_code}")
    if resp.status_code in [200, 201]:
        print(f"       ✅ This endpoint works!")
