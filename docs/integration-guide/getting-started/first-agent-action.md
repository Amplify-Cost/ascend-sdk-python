# Your First Agent Action

This guide walks you through submitting an agent action, understanding the response, and handling authorization decisions.

## What is an Agent Action?

An **Agent Action** represents any operation your AI agent wants to perform that requires governance oversight. The OW-AI Authorization Center evaluates each action against:

- **Risk Assessment**: CVSS scoring, MITRE ATT&CK mapping, NIST 800-53 controls
- **Policy Evaluation**: Enterprise governance policies
- **Approval Workflows**: Automatic approval vs. human review

**Implementation:** `/ow-ai-backend/routes/authorization_routes.py:2202-2395`

## Step 1: Submit an Action

### Required Fields

**Source:** `/ow-ai-backend/routes/authorization_routes.py:2227-2233`

```python
required_fields = [
    "agent_id",      # Unique identifier for your agent
    "action_type",   # Type of action (query, data_access, transaction, etc.)
    "description",   # Human-readable description
    "tool_name"      # Tool/resource being accessed
]
```

### Basic Example

```python
import requests
import os

api_key = os.getenv('OWKAI_API_KEY')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Submit a low-risk action
response = requests.post(
    "https://pilot.owkai.app/api/v1/actions/submit",
    headers=headers,
    json={
        "agent_id": "customer-service-agent-001",
        "agent_name": "Customer Service AI",
        "action_type": "query",
        "description": "Retrieve customer profile for support ticket #4521",
        "tool_name": "customer_database",
        "resource": "customer_profiles"
    }
)

result = response.json()
print(f"Action ID: {result['id']}")
print(f"Status: {result['status']}")
print(f"Risk Score: {result['risk_score']}")
```

### Using the Reference Client

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:215-234`

```python
from owkai_client import OWKAIClient

client = OWKAIClient()

# Submit action using AgentAction data class
from owkai_client import AgentAction

action = AgentAction(
    agent_id="customer-service-agent-001",
    agent_name="Customer Service AI",
    action_type="query",
    resource="customer_profiles",
    action_details={
        "operation": "read",
        "fields": ["name", "email", "support_tier"]
    },
    context={
        "ticket_id": "4521",
        "purpose": "support_ticket_resolution"
    }
)

result = client.submit_action(action)
```

## Step 2: Understand the Response

### Response Structure

**Source:** `/ow-ai-backend/routes/authorization_routes.py:2386-2395`

```json
{
  "id": 12345,
  "agent_id": "customer-service-agent-001",
  "status": "approved",
  "risk_score": 35.0,
  "risk_level": "low",
  "requires_approval": false,
  "alert_triggered": false,
  "message": "Action processed through platform workflow - Risk: 35.0"
}
```

### Status Values

| Status | Meaning | Risk Score | Action Required |
|--------|---------|------------|-----------------|
| `approved` | Automatically approved | < 70 | Proceed immediately |
| `pending_approval` | Human review required | ≥ 70 | Wait for decision |
| `rejected` | Denied by policy | N/A | Do not proceed |

**Implementation:** `/ow-ai-backend/routes/authorization_routes.py:2288-2290`

```python
# Authorization decision logic
requires_approval = risk_score >= 70
status = "pending_approval" if requires_approval else "approved"
```

### Risk Assessment

The platform performs automatic risk assessment:

**Source:** `/ow-ai-backend/routes/authorization_routes.py:2238-2278`

1. **First-pass enrichment**: Action type + description → risk level
2. **CVSS scoring**: Normalized score (0-10 scale)
3. **Risk level mapping**:
   - Low: risk_score = 35
   - Medium: risk_score = 60
   - High: risk_score = 85
   - Critical: risk_score = 95

```python
# From enrichment.py
enrichment = evaluate_action_enrichment(
    action_type=data["action_type"],
    description=data["description"],
    context={
        "agent_id": data["agent_id"],
        "tool_name": data["tool_name"]
    }
)

risk_level = enrichment.get("risk_level", "medium")
```

## Step 3: Handle Authorization Decisions

### Approved Actions

```python
if result['status'] == 'approved':
    # Proceed immediately
    print("✅ Action approved - executing")

    customer_data = fetch_customer_profile(
        customer_id="12345",
        fields=["name", "email", "support_tier"]
    )

    print(f"Retrieved customer data: {customer_data}")
```

### Pending Approval (High-Risk Actions)

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:251-283`

```python
if result['status'] == 'pending_approval':
    print(f"⏳ Action {result['id']} requires human approval")

    # Option 1: Wait synchronously with timeout
    import time

    timeout = 60  # seconds
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Poll status endpoint
        status_response = requests.get(
            f"https://pilot.owkai.app/api/v1/actions/{result['id']}/status",
            headers=headers
        )
        status = status_response.json()

        if status['status'] != 'pending_approval':
            break

        time.sleep(5)  # Poll every 5 seconds

    if status['status'] == 'approved':
        print("✅ Action approved after human review")
        execute_action()
    elif status['status'] == 'rejected':
        print(f"❌ Action denied: {status.get('reason')}")
    else:
        print("⏱️ Approval timeout - action still pending")
```

### Using wait_for_decision Helper

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:251-283`

```python
# Built-in wait helper from reference client
if result['decision'] == 'pending':
    final_status = client.wait_for_decision(
        action_id=result['action_id'],
        timeout=60,
        poll_interval=2.0
    )

    if final_status['decision'] == 'approved':
        execute_action()
    else:
        print(f"Action not approved: {final_status.get('error')}")
```

### Rejected Actions

```python
if result['status'] == 'rejected':
    print(f"❌ Action blocked by policy")
    print(f"Reason: {result.get('message')}")

    # Log the denial
    logger.warning(
        "Agent action rejected",
        extra={
            "action_id": result['id'],
            "agent_id": result['agent_id'],
            "risk_score": result['risk_score']
        }
    )

    # Do NOT proceed with the action
```

## Step 4: Check Action Status

Use the status endpoint for lightweight polling:

**Endpoint:** `GET /api/v1/actions/{action_id}/status`
**Source:** `/ow-ai-backend/routes/agent_routes.py:691-721`

```python
def poll_action_status(action_id: int, timeout: int = 60) -> dict:
    """
    Poll action status until decision made or timeout.

    Returns: Final status dict
    """
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(
            f"https://pilot.owkai.app/api/v1/actions/{action_id}/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        status = response.json()

        # Check if decision made
        if status['status'] in ['approved', 'rejected', 'executed']:
            return status

        # Wait before next poll
        time.sleep(5)

    return {"status": "timeout", "action_id": action_id}
```

### Status Response

```json
{
  "id": 12345,
  "status": "approved",
  "risk_score": 35.0,
  "risk_level": "low",
  "created_at": "2025-12-03T10:30:00Z",
  "decision_at": "2025-12-03T10:30:01Z"
}
```

## Complete Production Example

Here's a production-ready example with full error handling:

**Source:** `/ow-ai-backend/integration-examples/python_sdk_example.py:465-578`

```python
#!/usr/bin/env python3
"""
Production-ready agent with OW-AI authorization.
"""

import os
import logging
from typing import Dict, Any
from owkai_client import OWKAIClient, AgentAction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthorizedAgent:
    """AI agent with built-in authorization checks"""

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.client = OWKAIClient()

    def execute_with_authorization(
        self,
        action_type: str,
        description: str,
        tool_name: str,
        execute_fn: callable,
        **kwargs
    ) -> Any:
        """
        Execute function only if authorized by OW-AI.

        Args:
            action_type: Type of action
            description: Human-readable description
            tool_name: Tool/resource being accessed
            execute_fn: Function to execute if approved
            **kwargs: Additional action metadata

        Returns:
            Result of execute_fn if approved

        Raises:
            PermissionError: If action denied
            TimeoutError: If approval times out
        """
        # Submit action for authorization
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=action_type,
            resource=kwargs.get('resource', 'unknown'),
            action_details=kwargs.get('action_details'),
            context=kwargs.get('context'),
            risk_indicators=kwargs.get('risk_indicators')
        )

        try:
            result = self.client.submit_action(action)
            logger.info(f"Action {result['id']}: {result['status']} (risk: {result['risk_score']})")

            if result['status'] == 'approved':
                logger.info("✅ Executing approved action")
                return execute_fn()

            elif result['status'] == 'pending_approval':
                logger.info("⏳ Waiting for human approval")

                # Wait for decision
                final_status = self.client.wait_for_decision(
                    action_id=result['id'],
                    timeout=60
                )

                if final_status.get('decision') == 'approved':
                    logger.info("✅ Approved after review - executing")
                    return execute_fn()
                else:
                    reason = final_status.get('reason', 'No reason provided')
                    raise PermissionError(f"Action denied: {reason}")

            else:
                raise PermissionError(f"Action not approved: {result['status']}")

        except Exception as e:
            logger.error(f"Authorization failed: {e}")
            raise


# Example usage
def example_customer_lookup():
    """Example: Customer service agent accessing customer data"""

    agent = AuthorizedAgent(
        agent_id="customer-service-001",
        agent_name="Customer Service AI"
    )

    def fetch_customer_data():
        """Actual data fetch (only called if approved)"""
        return {
            "customer_id": "12345",
            "name": "John Doe",
            "email": "john@example.com",
            "support_tier": "premium"
        }

    try:
        # This will only execute if OW-AI approves
        customer_data = agent.execute_with_authorization(
            action_type="data_access",
            description="Retrieve customer profile for support ticket",
            tool_name="customer_database",
            execute_fn=fetch_customer_data,
            resource="customer_profiles",
            context={
                "ticket_id": "4521",
                "support_agent": "agent-001"
            },
            risk_indicators={
                "pii_involved": True,
                "data_sensitivity": "medium"
            }
        )

        print(f"✅ Retrieved customer data: {customer_data}")

    except PermissionError as e:
        print(f"❌ Access denied: {e}")
    except TimeoutError:
        print("⏱️ Authorization timeout - escalating to supervisor")


if __name__ == "__main__":
    example_customer_lookup()
```

## Action Types

Common action types and their typical risk levels:

| Action Type | Description | Typical Risk | Auto-Approve |
|-------------|-------------|--------------|--------------|
| `query` | Read-only data queries | Low (35) | Yes |
| `data_access` | Access PII or sensitive data | Medium (60) | Usually |
| `data_modification` | Update existing data | High (85) | Requires approval |
| `transaction` | Financial transactions | High (85) | Requires approval |
| `system_operation` | System changes | Critical (95) | Requires approval |

## Best Practices

### 1. Provide Detailed Context

```python
# GOOD - Detailed context helps governance
result = client.submit_action(
    agent_id="support-agent",
    agent_name="Support AI",
    action_type="data_modification",
    description="Update customer email per verified change request CR-789",
    tool_name="customer_database",
    resource="customer_profiles",
    action_details={
        "customer_id": "12345",
        "field": "email",
        "old_value": "old@example.com",
        "new_value": "new@example.com"
    },
    context={
        "change_request_id": "CR-789",
        "verification_method": "phone_callback",
        "verified_by": "agent-456",
        "ticket_id": "SUPP-8901"
    },
    risk_indicators={
        "pii_involved": True,
        "customer_requested": True,
        "verified": True
    }
)
```

### 2. Handle All Status Codes

```python
STATUS_HANDLERS = {
    'approved': lambda r: execute_action(r),
    'pending_approval': lambda r: wait_for_approval(r),
    'rejected': lambda r: log_denial(r),
}

handler = STATUS_HANDLERS.get(result['status'], handle_unknown)
handler(result)
```

### 3. Implement Graceful Degradation

```python
try:
    result = client.submit_action(action)
except requests.exceptions.ConnectionError:
    # Fallback: Log and notify operator
    logger.error("OW-AI Authorization Center unreachable")
    send_alert("Authorization system down - manual review required")

    # Option: Deny by default (fail-safe)
    raise PermissionError("Authorization system unavailable")

    # Or: Allow with audit trail (fail-open)
    logger.warning("Proceeding without authorization - HIGH RISK")
    audit_log.write("unauthorized_action", action)
```

### 4. Monitor Action Outcomes

```python
# Track authorization metrics
metrics = {
    "total_actions": 0,
    "approved": 0,
    "pending": 0,
    "rejected": 0,
    "timeouts": 0
}

def track_action(result):
    metrics["total_actions"] += 1
    metrics[result['status']] += 1

    # Alert on high rejection rate
    rejection_rate = metrics["rejected"] / metrics["total_actions"]
    if rejection_rate > 0.1:  # 10%
        send_alert(f"High rejection rate: {rejection_rate:.1%}")
```

## Next Steps

- [Risk Scoring](/core-concepts/risk-scoring) - How risk is calculated
- [Approval Workflows](/core-concepts/approval-workflows) - Configure human review
- [Integration Examples](https://github.com/OW-AI/ow-ai-backend/tree/main/integration-examples) - Production code examples
- [API Reference](/api/overview) - Complete endpoint documentation
