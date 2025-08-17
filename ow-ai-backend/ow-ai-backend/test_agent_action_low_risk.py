import requests
import time

# Replace this with your actual token from the login response
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxNSIsImVtYWlsIjoibXlAZ21haWwuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4OTY1NjA4fQ.uoT9t5xTkmd2d-jvGq5AETQGLJmoZr9v_j5ApXqiMfI"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "agent_id": "agent-test-001",
    "action_type": "log_file_read",
    "tool_name": "TestTool",
    "description": "Reading local logs for debugging",
    "timestamp": time.time()
}

response = requests.post("http://localhost:8000/agent-action", json=payload, headers=headers)

print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception as e:
    print("Failed to parse JSON.")
    print("Raw Response:", response.text)
    print("Error:", str(e))
