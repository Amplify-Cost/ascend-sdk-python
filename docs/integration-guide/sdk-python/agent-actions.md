---
Document ID: ASCEND-SDK-PY-002
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Agent Actions

Learn how to submit, track, and manage AI agent actions through the OW-AI governance platform.

> **Source of Truth**: Based on `OWKAIClient` and `AuthorizedAgent` classes in `python_sdk_example.py`

## Action Types

Supported action types are defined in the `ActionType` enum (lines 55-62):

```python
from python_sdk_example import ActionType

# Available action types
ActionType.DATA_ACCESS          # "data_access"
ActionType.DATA_MODIFICATION    # "data_modification"
ActionType.TRANSACTION          # "transaction"
ActionType.RECOMMENDATION       # "recommendation"
ActionType.COMMUNICATION        # "communication"
ActionType.SYSTEM_OPERATION     # "system_operation"
```

## Decision Statuses

Action decisions are defined in the `DecisionStatus` enum (lines 65-72):

```python
from python_sdk_example import DecisionStatus

# Possible decision statuses
DecisionStatus.PENDING              # "pending"
DecisionStatus.APPROVED             # "approved"
DecisionStatus.DENIED               # "denied"
DecisionStatus.REQUIRES_MODIFICATION # "requires_modification"
DecisionStatus.TIMEOUT              # "timeout"
```

## Creating Agent Actions

### AgentAction Dataclass

The `AgentAction` dataclass represents an action requiring authorization (lines 74-102):

```python
from python_sdk_example import AgentAction, ActionType

action = AgentAction(
    agent_id: str,                              # Required
    agent_name: str,                            # Required
    action_type: str,                           # Required
    resource: str,                              # Required
    resource_id: Optional[str] = None,
    action_details: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    risk_indicators: Optional[Dict[str, Any]] = None
)
```

### Basic Action Submission

```python
from python_sdk_example import OWKAIClient, AgentAction, ActionType

client = OWKAIClient()

# Create action
action = AgentAction(
    agent_id="customer-service-agent",
    agent_name="Customer Service AI",
    action_type=ActionType.DATA_ACCESS.value,
    resource="customer_database"
)

# Submit for authorization
response = client.submit_action(action)

print(f"Action ID: {response['action_id']}")
print(f"Status: {response['status']}")
print(f"Decision: {response.get('decision', 'pending')}")
```

Implementation reference (lines 215-234):
```python
def submit_action(self, action: AgentAction) -> Dict:
    """
    Submit an agent action for authorization.

    Args:
        action: AgentAction object describing the action

    Returns:
        Authorization response with action_id and initial status
    """
    logger.info(f"Submitting action: {action.action_type} on {action.resource}")

    response = self._request(
        "POST",
        "/api/v1/actions/submit",
        data=action.to_dict()
    )

    logger.info(f"Action submitted: {response.get('action_id')} - Status: {response.get('status')}")
    return response
```

### Action with Resource ID

```python
action = AgentAction(
    agent_id="data-analyst-agent",
    agent_name="Data Analyst AI",
    action_type=ActionType.DATA_ACCESS.value,
    resource="customer_profiles",
    resource_id="CUST-12345"  # Specific resource identifier
)

response = client.submit_action(action)
```

### Action with Details

```python
action = AgentAction(
    agent_id="support-agent",
    agent_name="Support AI",
    action_type=ActionType.DATA_MODIFICATION.value,
    resource="customer_database",
    resource_id="CUST-12345",
    action_details={
        "operation": "update",
        "field": "email",
        "old_value": "old@example.com",
        "new_value": "new@example.com"
    }
)

response = client.submit_action(action)
```

### Action with Context

```python
action = AgentAction(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    action_type=ActionType.TRANSACTION.value,
    resource="customer_account",
    resource_id="ACC-98765",
    action_details={
        "operation": "transfer",
        "amount": 50000,
        "currency": "USD",
        "destination": "external_account"
    },
    context={
        "user_request": "Transfer $50,000 to savings",
        "session_id": "sess_abc123",
        "ip_address": "192.168.1.100"
    },
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True,
        "data_sensitivity": "critical"
    }
)

response = client.submit_action(action)
```

## Checking Action Status

### Get Current Status

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient()

# Get status by action ID
status = client.get_action_status("act_xyz789")

print(f"Status: {status.get('decision', status.get('status'))}")
print(f"Updated: {status.get('updated_at')}")
```

Implementation reference (lines 236-249):
```python
def get_action_status(self, action_id: str) -> Dict:
    """
    Get the current status of an action.

    Args:
        action_id: The action ID returned from submit_action

    Returns:
        Current status and decision information
    """
    return self._request(
        "GET",
        f"/api/v1/actions/{action_id}/status"
    )
```

## Waiting for Decisions

### Synchronous Wait

Use `wait_for_decision()` to poll for a decision (lines 251-283):

```python
from python_sdk_example import OWKAIClient, AgentAction

client = OWKAIClient()

# Submit action
action = AgentAction(
    agent_id="my-agent",
    agent_name="My Agent",
    action_type="data_access",
    resource="sensitive_data"
)

response = client.submit_action(action)

# Wait for decision (default: 60 seconds)
if response.get('decision') == 'pending':
    final_decision = client.wait_for_decision(
        action_id=response['action_id'],
        timeout=60,           # Max wait time in seconds
        poll_interval=2.0     # Check every 2 seconds
    )

    if final_decision.get('decision') == 'approved':
        print("Action approved!")
    elif final_decision.get('decision') == 'denied':
        print(f"Action denied: {final_decision.get('reason')}")
    elif final_decision.get('decision') == 'timeout':
        print("Decision timed out - manual approval required")
```

Implementation reference (lines 251-283):
```python
def wait_for_decision(
    self,
    action_id: str,
    timeout: int = 60,
    poll_interval: float = 2.0
) -> Dict:
    """
    Wait for an authorization decision.

    Args:
        action_id: The action ID to wait for
        timeout: Maximum time to wait in seconds
        poll_interval: Time between status checks

    Returns:
        Final decision status
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = self.get_action_status(action_id)

        if status.get('decision') != 'pending':
            return status

        logger.debug(f"Action {action_id} still pending...")
        time.sleep(poll_interval)

    return {
        "action_id": action_id,
        "decision": "timeout",
        "error": f"Decision not received within {timeout} seconds"
    }
```

## Listing Actions

### List Recent Actions

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient()

# List actions with pagination
actions = client.list_actions(
    limit=50,      # Max results (default: 50)
    offset=0,      # Pagination offset (default: 0)
    status=None    # Optional status filter
)

print(f"Total actions: {actions.get('total', 0)}")
for action in actions.get('actions', []):
    print(f"  {action['action_id']}: {action['action_type']} -> {action['status']}")
```

Implementation reference (lines 285-310):
```python
def list_actions(
    self,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
) -> Dict:
    """
    List recent agent actions for this organization.

    Args:
        limit: Maximum number of actions to return
        offset: Pagination offset
        status: Filter by status

    Returns:
        List of actions with pagination info
    """
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status

    return self._request(
        "GET",
        "/api/v1/actions",
        params=params
    )
```

### Filter by Status

```python
# Get only approved actions
approved_actions = client.list_actions(status="approved")

# Get only pending actions
pending_actions = client.list_actions(status="pending")

# Get only denied actions
denied_actions = client.list_actions(status="denied")
```

## Getting Action Details

### Full Action Information

```python
from python_sdk_example import OWKAIClient

client = OWKAIClient()

# Get complete action details
action = client.get_action_details("act_xyz789")

print(f"Agent: {action.get('agent_id')}")
print(f"Action Type: {action.get('action_type')}")
print(f"Resource: {action.get('resource')}")
print(f"Status: {action.get('status')}")
print(f"Risk Score: {action.get('risk_score')}")
print(f"Created: {action.get('created_at')}")
print(f"Decision: {action.get('decision')}")
```

Implementation reference (lines 312-326):
```python
def get_action_details(self, action_id: str) -> Dict:
    """
    Get detailed information about an action.

    Args:
        action_id: The action ID

    Returns:
        Full action details including audit trail
    """
    return self._request(
        "GET",
        f"/api/v1/actions/{action_id}"
    )
```

## Using AuthorizedAgent Wrapper

The `AuthorizedAgent` class simplifies authorization workflows (lines 328-458).

### Initialize Authorized Agent

```python
from python_sdk_example import OWKAIClient, AuthorizedAgent

# Option 1: With existing client
client = OWKAIClient()
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    client=client
)

# Option 2: Creates client automatically
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI"
)
```

### Request Authorization

```python
# Request authorization with automatic waiting
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_portfolio",
    resource_id="CUST-12345",
    details={
        "operation": "read",
        "fields": ["balance", "holdings"]
    },
    context={
        "user_request": "Show my portfolio",
        "session_id": "sess_abc123"
    },
    risk_indicators={
        "pii_involved": True,
        "financial_data": True,
        "data_sensitivity": "medium"
    },
    wait_for_decision=True,  # Wait for decision
    timeout=60               # Wait up to 60 seconds
)

print(f"Decision: {decision.get('decision', decision.get('status'))}")
```

Implementation reference (lines 354-400):
```python
def request_authorization(
    self,
    action_type: str,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict] = None,
    context: Optional[Dict] = None,
    risk_indicators: Optional[Dict] = None,
    wait_for_decision: bool = True,
    timeout: int = 60
) -> Dict:
    """
    Request authorization for an action.

    Args:
        action_type: Type of action (data_access, transaction, etc.)
        resource: Resource being accessed
        resource_id: Specific resource identifier
        details: Additional action details
        context: Contextual information
        risk_indicators: Risk assessment data
        wait_for_decision: Whether to wait for decision
        timeout: Decision timeout in seconds

    Returns:
        Authorization decision
    """
    action = AgentAction(
        agent_id=self.agent_id,
        agent_name=self.agent_name,
        action_type=action_type,
        resource=resource,
        resource_id=resource_id,
        action_details=details,
        context=context,
        risk_indicators=risk_indicators
    )

    response = self.client.submit_action(action)

    if wait_for_decision and response.get('decision') == 'pending':
        return self.client.wait_for_decision(
            response['action_id'],
            timeout=timeout
        )

    return response
```

### Execute If Authorized

The most powerful pattern - execute function only if authorized (lines 402-458):

```python
from python_sdk_example import AuthorizedAgent

agent = AuthorizedAgent(
    agent_id="data-analyst-001",
    agent_name="Data Analyst AI"
)

def get_customer_data():
    """Function to execute if authorized."""
    # Your actual data access logic here
    return {
        "customer_id": "CUST-12345",
        "balance": 125000.00,
        "account_status": "active"
    }

# Execute only if authorized
try:
    result = agent.execute_if_authorized(
        action_type="data_access",
        resource="customer_database",
        execute_fn=get_customer_data,
        resource_id="CUST-12345",
        details={"operation": "read"},
        context={"purpose": "customer_inquiry"},
        risk_indicators={"pii_involved": True},
        timeout=60
    )
    print(f"Authorized result: {result}")

except PermissionError as e:
    print(f"Action denied: {e}")

except TimeoutError as e:
    print(f"Authorization timeout: {e}")

except Exception as e:
    print(f"Error: {e}")
```

Implementation reference (lines 402-458):
```python
def execute_if_authorized(
    self,
    action_type: str,
    resource: str,
    execute_fn: callable,
    resource_id: Optional[str] = None,
    details: Optional[Dict] = None,
    context: Optional[Dict] = None,
    risk_indicators: Optional[Dict] = None,
    timeout: int = 60
) -> Any:
    """
    Execute a function only if authorized.

    Args:
        action_type: Type of action
        resource: Resource being accessed
        execute_fn: Function to execute if authorized
        resource_id: Specific resource identifier
        details: Additional action details
        context: Contextual information
        risk_indicators: Risk assessment data
        timeout: Decision timeout

    Returns:
        Result of execute_fn if authorized

    Raises:
        PermissionError: If action is denied
        TimeoutError: If decision times out
    """
    decision = self.request_authorization(
        action_type=action_type,
        resource=resource,
        resource_id=resource_id,
        details=details,
        context=context,
        risk_indicators=risk_indicators,
        wait_for_decision=True,
        timeout=timeout
    )

    status = decision.get('decision', decision.get('status'))

    if status == 'approved':
        logger.info(f"Action authorized, executing...")
        return execute_fn()

    elif status == 'denied':
        reason = decision.get('reason', 'No reason provided')
        raise PermissionError(f"Action denied: {reason}")

    elif status == 'timeout':
        raise TimeoutError("Authorization decision timed out")

    else:
        raise Exception(f"Unexpected authorization status: {status}")
```

## Complete Examples

### Example 1: Financial Advisor Agent

From the example implementation (lines 465-621):

```python
from python_sdk_example import OWKAIClient, AuthorizedAgent

# Initialize
client = OWKAIClient()
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    client=client
)

# Low-risk action (likely auto-approved)
decision = agent.request_authorization(
    action_type="query",
    resource="market_data",
    details={
        "operation": "read",
        "data_type": "public_prices"
    },
    risk_indicators={
        "pii_involved": False,
        "financial_data": False
    }
)
print(f"Decision: {decision.get('decision')}")

# High-risk action (requires approval)
decision = agent.request_authorization(
    action_type="transaction",
    resource="customer_account",
    resource_id="ACC-98765",
    details={
        "operation": "transfer",
        "amount": 50000,
        "currency": "USD",
        "destination": "external_account"
    },
    context={
        "user_request": "Transfer $50,000 to savings",
        "ip_address": "192.168.1.100"
    },
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True,
        "data_sensitivity": "critical"
    },
    timeout=30
)

if decision.get('decision') == 'pending':
    print("Action requires manual review by compliance officer")
```

### Example 2: Conditional Execution

```python
def get_portfolio_data():
    """Simulated function to get portfolio data."""
    return {
        "balance": 125000.00,
        "holdings": ["AAPL", "GOOGL", "MSFT"],
        "last_updated": "2025-12-04T10:30:00"
    }

try:
    result = agent.execute_if_authorized(
        action_type="data_access",
        resource="portfolio_summary",
        execute_fn=get_portfolio_data,
        details={"operation": "read"},
        risk_indicators={"pii_involved": False}
    )
    print(f"Authorized result: {result}")

except PermissionError as e:
    print(f"Not authorized: {e}")
```

## Best Practices

### 1. Use Descriptive Action Details

```python
# ✅ Good - Detailed information
action = AgentAction(
    agent_id="customer-service-agent",
    agent_name="Customer Service AI",
    action_type="data_access",
    resource="customer_database",
    resource_id="CUST-12345",
    action_details={
        "operation": "read",
        "fields": ["name", "email", "order_history"],
        "purpose": "customer_support",
        "ticket_id": "SUPPORT-789"
    },
    context={
        "user_request": "Show order history for refund",
        "session_id": "sess_abc123",
        "support_agent": "john@company.com"
    }
)

# ❌ Bad - Vague information
action = AgentAction(
    agent_id="agent",
    agent_name="Agent",
    action_type="read",
    resource="db"
)
```

### 2. Always Handle All Decision Outcomes

```python
response = client.submit_action(action)
status = response.get('decision', response.get('status'))

if status == 'approved':
    # Execute action
    execute_action()
elif status == 'denied':
    # Log denial
    logger.warning(f"Action denied: {response.get('reason')}")
elif status == 'pending':
    # Wait for decision or notify
    notify_pending_review(response['action_id'])
elif status == 'timeout':
    # Handle timeout
    handle_timeout(response['action_id'])
else:
    # Handle unexpected status
    logger.error(f"Unexpected status: {status}")
```

### 3. Include Risk Indicators

```python
# Always provide risk indicators for better governance
risk_indicators = {
    "pii_involved": True,           # Contains personal data
    "financial_data": True,          # Contains financial info
    "data_sensitivity": "high",      # Sensitivity level
    "external_transfer": False,      # Data leaving system
    "regulatory_scope": "HIPAA"      # Applicable regulations
}
```

### 4. Use AuthorizedAgent for Complex Workflows

```python
# ✅ Good - Use AuthorizedAgent wrapper
agent = AuthorizedAgent("my-agent", "My Agent")
result = agent.execute_if_authorized(
    action_type="data_access",
    resource="database",
    execute_fn=my_function
)

# ❌ Less ideal - Manual workflow
client = OWKAIClient()
action = AgentAction(...)
response = client.submit_action(action)
# ... manual status checking ...
```

## Next Steps

- [Error Handling](/sdk/python/error-handling) - Handle errors gracefully
- [API Reference](/sdk/python/api-reference) - Complete API documentation

## Source Code Reference

Implementation details:
- `ActionType` enum: lines 55-62
- `DecisionStatus` enum: lines 65-72
- `AgentAction` dataclass: lines 74-102
- `OWKAIClient.submit_action()`: lines 215-234
- `OWKAIClient.get_action_status()`: lines 236-249
- `OWKAIClient.wait_for_decision()`: lines 251-283
- `OWKAIClient.list_actions()`: lines 285-310
- `OWKAIClient.get_action_details()`: lines 312-326
- `AuthorizedAgent` class: lines 328-458
- Complete examples: lines 465-621
