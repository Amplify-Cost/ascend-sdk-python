import requests
resp = requests.post(
    "http://localhost:8000/auth/token",
    data={"username": "admin@owkai.com", "password": "Admin123"}
)
print(resp.json().get("access_token", ""))
