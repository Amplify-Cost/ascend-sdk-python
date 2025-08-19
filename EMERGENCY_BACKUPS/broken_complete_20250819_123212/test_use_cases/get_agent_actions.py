
import requests

# ✅ Replace with your actual JWT token
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTlAZ21haWwuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4NjMzMDE1fQ.5EAJ71o4LgLUxifNqcADxeuuwm_jUUZgR6RMnmYYci8"

headers = {
    "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5OTlAZ21haWwuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4NjMzMDE1fQ.5EAJ71o4LgLUxifNqcADxeuuwm_jUUZgR6RMnmYYci8",
    "Content-Type": "application/json"
}

url = "http://127.0.0.1:8000/agent-actions"

response = requests.get(url, headers=headers)

print("Fetched Agent Actions:")
try:
    data = response.json()
    for action in data:
        print(f"- Agent: {action['agent_id']}, Action: {action['action_type']}, Risk: {action['risk_level']}")
except Exception as e:
    print("Error parsing response:", e)
    print("Raw response text:", response.text)
