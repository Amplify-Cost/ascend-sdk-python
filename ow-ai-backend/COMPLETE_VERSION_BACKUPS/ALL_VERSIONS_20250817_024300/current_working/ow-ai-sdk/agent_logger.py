import requests
import time
from datetime import datetime

class AgentLogger:
    def __init__(self, agent_id="agent-default", backend_url="http://localhost:8000"):
        self.agent_id = agent_id
        self.backend_url = backend_url

    def log_action(self, action_type, description, tool_name=None, risk_level="low", user_id=1):
        payload = {
            "agent_id": self.agent_id,
            "user_id": user_id,
            "action_type": action_type,
            "description": description,
            "tool_name": tool_name,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            response = requests.post(f"{self.backend_url}/agent-actions", json=payload)
            response.raise_for_status()
            action_id = response.json().get("id")
            print(f"[OW-AI SDK] Logged action: {action_type} (ID: {action_id})")

            if risk_level != "low" and action_id:
                print(f"[OW-AI SDK] Waiting for review on action ID: {action_id}")
                self._poll_for_review(action_id)
            return action_id

        except requests.exceptions.RequestException as e:
            print(f"[OW-AI SDK] Failed to log action or poll: {e}")
            return None

    def _poll_for_review(self, action_id):
        while True:
            try:
                response = requests.get(f"{self.backend_url}/agent-actions/{action_id}")
                response.raise_for_status()
                data = response.json()
                status = data.get("status")

                if status in ["approved", "rejected"]:
                    print(f"[OW-AI SDK] Action ID {action_id} was {status.upper()}.")
                    break
                else:
                    print(f"[OW-AI SDK] Still pending... checking again in 2s.")
                    time.sleep(2)
            except requests.exceptions.RequestException as e:
                print(f"[OW-AI SDK] Polling failed: {e}")
                time.sleep(2)

# Example usage
if __name__ == "__main__":
    logger = AgentLogger(agent_id="agent007")
    logger.log_action(
        action_type="AccessFile",
        description="Accessed sensitive document",
        tool_name="ReconTool",
        risk_level="high",
        user_id=1  # You can dynamically assign this later via auth
    )
