import requests
import time

# ✅ Replace with your actual JWT token
TOKEN = "eeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMjNAZ21haWwuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4NjM2ODQzfQ.boSFC4CQIEbSrSlKBSvR6ihZ6PPrztAsJyrtiwZbUyE"

headers = {
    "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMjNAZ21haWwuY29tIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ4NjM2ODQzfQ.boSFC4CQIEbSrSlKBSvR6ihZ6PPrztAsJyrtiwZbUyE",
    "Content-Type": "application/json"
}

# ✅ Use the correct endpoint: /agent-action
url = "http://127.0.0.1:8000/agent-action"

sample_actions = [
    {
        "agent_id": "agent-001",
        "action_type": "file_access",
        "tool_name": "Notepad++",
        "description": "Accessed a restricted file",
        "timestamp": time.time()
    },
    {
        "agent_id": "agent-002",
        "action_type": "api_call",
        "tool_name": "Postman",
        "description": "Made an unauthorized API call",
        "timestamp": time.time()
    },
    {
        "agent_id": "agent-003",
        "action_type": "system_command",
        "tool_name": "Terminal",
        "description": "Ran elevated privilege command",
        "timestamp": time.time()
    }
]

for action in sample_actions:
    response = requests.post(url, json=action, headers=headers)
    print(f"POST to {url}")
    print(f"Status: {response.status_code}")
    try:
        print(response.json())
    except Exception:
        print("No JSON response body.")
