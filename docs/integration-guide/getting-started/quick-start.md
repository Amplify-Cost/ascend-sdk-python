---
Document ID: ASCEND-START-003
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Quick Start

Submit your first agent action for authorization in under 5 minutes using the OW-AI Authorization Center.

## Prerequisites

- Python 3.8+ (or any language with HTTP client)
- An OW-AI account with API key
- `requests` library: `pip install requests python-dotenv`

## What You'll Build

A simple Python client that submits agent actions for governance review and waits for authorization decisions.

> **No Package Installation Required**
> There is **no pip package** to install. You integrate directly with the REST API using standard HTTP requests or by copying our reference implementation.


## Step 1: Get Your API Key

1. Log in to the [OW-AI Dashboard](https://pilot.owkai.app)
2. Navigate to **Settings** → **API Keys**
3. Click **Generate New Key**
4. Copy the key (shown only once)
5. Set environment variable:

```bash
export OWKAI_API_KEY="owkai_admin_xxxxxxxxxxxx"
export OWKAI_API_URL="https://pilot.owkai.app"
```

> **Important: Important**
> API keys are shown only once during generation. Store them securely in environment variables or a secrets manager.


## Step 2: Copy the Reference Client

Download the reference implementation from the backend repository:

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py` (622 lines)

Or create your own minimal client:

```python
import os
import requests
from typing import Dict, Optional

class OWKAIClient:
    """Minimal OW-AI client for agent authorization"""

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv('OWKAI_API_URL', 'https://pilot.owkai.app')
        self.api_key = api_key or os.getenv('OWKAI_API_KEY')

        if not self.api_key:
            raise ValueError("API key required. Set OWKAI_API_KEY environment variable.")

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def submit_action(self, agent_id: str, action_type: str, description: str,
                     tool_name: str, **kwargs) -> Dict:
        """
        Submit agent action for authorization.

        Endpoint: POST /api/v1/actions/submit
        Source: /ow-ai-backend/routes/authorization_routes.py:2202
        """
        payload = {
            "agent_id": agent_id,
            "action_type": action_type,
            "description": description,
            "tool_name": tool_name,
            **kwargs
        }

        response = requests.post(
            f"{self.api_url}/api/v1/actions/submit",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def get_action_status(self, action_id: int) -> Dict:
        """
        Get current status of an action.

        Endpoint: GET /api/v1/actions/{action_id}/status
        Source: /ow-ai-backend/routes/agent_routes.py:691
        """
        response = requests.get(
            f"{self.api_url}/api/v1/actions/{action_id}/status",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
```

## Step 3: Submit Your First Action

```python
from owkai_client import OWKAIClient

# Initialize client
client = OWKAIClient()

# Submit a low-risk action
result = client.submit_action(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    action_type="query",
    description="Retrieve public market prices for portfolio analysis",
    tool_name="market_data_api",
    resource="market_data"
)

print(f"Action ID: {result['id']}")
print(f"Status: {result['status']}")
print(f"Risk Score: {result['risk_score']}")
```

## Step 4: Handle the Response

The response contains the authorization decision:

```json
{
  "id": 12345,
  "agent_id": "financial-advisor-001",
  "status": "approved",
  "risk_score": 35.0,
  "risk_level": "low",
  "requires_approval": false,
  "alert_triggered": false,
  "message": "Action processed through platform workflow - Risk: 35.0"
}
```

### Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `approved` | Automatically approved | Proceed immediately |
| `pending_approval` | Requires human review | Wait for decision |
| `rejected` | Denied by policy | Do not proceed |

### Example: Handling Different Statuses

```python
if result['status'] == 'approved':
    # Proceed with the action
    print("✅ Action approved - proceeding")
    execute_action()

elif result['status'] == 'pending_approval':
    # Wait for human approval
    print("⏳ Waiting for approval...")

    import time
    while True:
        status = client.get_action_status(result['id'])
        if status['status'] != 'pending_approval':
            break
        time.sleep(5)  # Poll every 5 seconds

    if status['status'] == 'approved':
        execute_action()
    else:
        print(f"❌ Action denied: {status.get('reason')}")

elif result['status'] == 'rejected':
    print(f"❌ Action blocked: {result.get('message')}")
```

## Complete Example

Here's a production-ready example from the backend integration examples:

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:465-578`

```python
#!/usr/bin/env python3
"""Financial Advisor Agent with OW-AI Authorization"""

import os
from owkai_client import OWKAIClient

def example_financial_advisor():
    # Initialize client
    client = OWKAIClient()

    # Test connection
    print("Testing connection...")
    conn_status = client.test_connection()
    if conn_status['status'] != 'connected':
        print(f"❌ Connection failed: {conn_status.get('error')}")
        return

    print("✅ Connected to OW-AI Authorization Center")

    # Example 1: Low-risk action (auto-approved)
    print("\n--- Low-Risk Query ---")
    result = client.submit_action(
        agent_id="financial-advisor-001",
        agent_name="Financial Advisor AI",
        action_type="query",
        description="Retrieve public market data",
        tool_name="market_data_api",
        resource="market_data"
    )
    print(f"Decision: {result['status']} (Risk: {result['risk_score']})")

    # Example 2: Medium-risk action
    print("\n--- Customer Data Access ---")
    result = client.submit_action(
        agent_id="financial-advisor-001",
        agent_name="Financial Advisor AI",
        action_type="data_access",
        description="Access customer portfolio for account ID 12345",
        tool_name="customer_db",
        resource="customer_portfolio",
        resource_id="CUST-12345"
    )
    print(f"Decision: {result['status']} (Risk: {result['risk_score']})")

    # Example 3: High-risk action (requires approval)
    print("\n--- High-Value Transaction ---")
    result = client.submit_action(
        agent_id="financial-advisor-001",
        agent_name="Financial Advisor AI",
        action_type="transaction",
        description="Transfer $50,000 to external account",
        tool_name="payment_processor",
        resource="customer_account",
        resource_id="ACC-98765"
    )
    print(f"Decision: {result['status']} (Risk: {result['risk_score']})")

    if result['status'] == 'pending_approval':
        print("⏳ Action requires manual review")

if __name__ == "__main__":
    example_financial_advisor()
```

## What's Next?

- [Installation Guide](/getting-started/installation) - Setup and configuration
- [Authentication](/getting-started/authentication) - API key management
- [First Agent Action](/getting-started/first-agent-action) - Detailed walkthrough
- [Risk Scoring](/core-concepts/risk-scoring) - How risk is calculated

## Need Help?

- **Enterprise Support**: support@ascendowkai.com
- **Documentation**: [integration-examples/](https://github.com/OW-AI/ow-ai-backend/tree/main/integration-examples)
- **Reference Implementation**: `/ow-ai-backend/integration-examples/python_sdk_example.py`
