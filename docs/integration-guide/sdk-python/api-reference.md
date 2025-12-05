# Python SDK API Reference

Complete reference for the OW-AI Python SDK.

> **Source of Truth**: This documentation is derived from the actual implementation in `/ow-ai-backend/integration-examples/python_sdk_example.py` (lines 1-622)

## Overview

The OW-AI Python SDK consists of:

| Class/Module | Lines | Purpose |
|--------------|-------|---------|
| `ActionType` | 55-62 | Action type enum |
| `DecisionStatus` | 65-72 | Decision status enum |
| `AgentAction` | 74-102 | Action dataclass |
| `OWKAIClient` | 105-326 | Main SDK client |
| `AuthorizedAgent` | 328-458 | High-level agent wrapper |

## Imports

```python
from python_sdk_example import (
    OWKAIClient,
    AuthorizedAgent,
    AgentAction,
    ActionType,
    DecisionStatus
)
```

---

## ActionType Enum

**Source**: Lines 55-62

Supported action types for agent authorization.

```python
class ActionType(Enum):
    """Supported action types for agent authorization"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION = "transaction"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    SYSTEM_OPERATION = "system_operation"
```

**Usage**:
```python
from python_sdk_example import ActionType

action_type = ActionType.DATA_ACCESS.value  # "data_access"
```

---

## DecisionStatus Enum

**Source**: Lines 65-72

Authorization decision statuses.

```python
class DecisionStatus(Enum):
    """Authorization decision statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_MODIFICATION = "requires_modification"
    TIMEOUT = "timeout"
```

**Usage**:
```python
from python_sdk_example import DecisionStatus

if decision == DecisionStatus.APPROVED.value:
    execute_action()
```

---

## AgentAction Dataclass

**Source**: Lines 74-102

Represents an agent action requiring authorization.

### Constructor

```python
@dataclass
class AgentAction:
    agent_id: str                               # Required
    agent_name: str                             # Required
    action_type: str                            # Required
    resource: str                               # Required
    resource_id: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    risk_indicators: Optional[Dict[str, Any]] = None
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | str | Yes | Unique identifier for the agent |
| `agent_name` | str | Yes | Human-readable agent name |
| `action_type` | str | Yes | Type of action (use `ActionType` enum) |
| `resource` | str | Yes | Resource being accessed |
| `resource_id` | str | No | Specific resource identifier |
| `action_details` | dict | No | Additional action details |
| `context` | dict | No | Contextual information |
| `risk_indicators` | dict | No | Risk assessment data |

### Methods

#### to_dict()

**Source**: Lines 86-102

Convert action to API-compatible dictionary.

```python
def to_dict(self) -> Dict:
    """Convert to API-compatible dictionary"""
```

**Returns**: `Dict` - API-ready dictionary representation

**Example**:
```python
action = AgentAction(
    agent_id="agent-001",
    agent_name="My Agent",
    action_type="data_access",
    resource="database"
)

data = action.to_dict()
# {
#     "agent_id": "agent-001",
#     "agent_name": "My Agent",
#     "action_type": "data_access",
#     "resource": "database"
# }
```

---

## OWKAIClient Class

**Source**: Lines 105-326

Enterprise-grade client for submitting agent actions for authorization and policy enforcement.

### Constructor

**Source**: Lines 113-150

```python
def __init__(
    self,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    organization_slug: Optional[str] = None,
    timeout: int = 30,
    debug: bool = False
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | str | `https://pilot.owkai.app` | API endpoint URL (reads from `OWKAI_API_URL`) |
| `api_key` | str | None | Organization API key (reads from `OWKAI_API_KEY`) **REQUIRED** |
| `organization_slug` | str | None | Organization identifier (reads from `OWKAI_ORG_SLUG`) |
| `timeout` | int | 30 | Request timeout in seconds |
| `debug` | bool | False | Enable debug logging |

**Raises:**
- `ValueError` - If API key is not provided

**Example**:
```python
# From environment variables
client = OWKAIClient()

# Explicit configuration
client = OWKAIClient(
    api_url="https://pilot.owkai.app",
    api_key="owkai_live_your_key_here",
    timeout=60,
    debug=True
)
```

---

### test_connection()

**Source**: Lines 195-213

Test API connectivity and authentication.

```python
def test_connection(self) -> Dict
```

**Returns**: `Dict` with keys:
- `status` (str): "connected" or "error"
- `api_version` (str): API version if connected
- `server_time` (str): Server timestamp if connected
- `error` (str): Error message if failed

**Example**:
```python
status = client.test_connection()

if status['status'] == 'connected':
    print(f"Connected! Version: {status['api_version']}")
else:
    print(f"Failed: {status['error']}")
```

**API Endpoints Used:**
- `GET /health` - Health check
- `GET /api/deployment-info` - Version information

---

### submit_action()

**Source**: Lines 215-234

Submit an agent action for authorization.

```python
def submit_action(self, action: AgentAction) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | AgentAction | Yes | Action object to submit |

**Returns**: `Dict` with keys:
- `action_id` (str): Unique action identifier
- `status` (str): Initial status ("approved", "pending", "denied")
- `decision` (str): Decision status (same as status)
- `risk_score` (int): Calculated risk score (0-100)
- `reason` (str): Reason for decision (if denied)

**Raises:**
- `Exception` - On API errors
- `TimeoutError` - On request timeout
- `ConnectionError` - On connection failure

**Example**:
```python
action = AgentAction(
    agent_id="agent-001",
    agent_name="My Agent",
    action_type="data_access",
    resource="customer_database"
)

response = client.submit_action(action)
print(f"Action ID: {response['action_id']}")
print(f"Decision: {response['decision']}")
```

**API Endpoint Used:**
- `POST /api/v1/actions/submit`

---

### get_action_status()

**Source**: Lines 236-249

Get the current status of an action.

```python
def get_action_status(self, action_id: str) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action_id` | str | Yes | Action ID from `submit_action()` |

**Returns**: `Dict` with current status and decision information

**Example**:
```python
status = client.get_action_status("act_xyz789")
print(f"Status: {status.get('decision')}")
```

**API Endpoint Used:**
- `GET /api/v1/actions/{action_id}/status`

---

### wait_for_decision()

**Source**: Lines 251-283

Wait for an authorization decision with polling.

```python
def wait_for_decision(
    self,
    action_id: str,
    timeout: int = 60,
    poll_interval: float = 2.0
) -> Dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action_id` | str | - | Action ID to wait for |
| `timeout` | int | 60 | Maximum wait time in seconds |
| `poll_interval` | float | 2.0 | Time between status checks (seconds) |

**Returns**: `Dict` with final decision status, or timeout indicator

**Example**:
```python
response = client.submit_action(action)

if response.get('decision') == 'pending':
    final = client.wait_for_decision(
        action_id=response['action_id'],
        timeout=300,
        poll_interval=5.0
    )

    if final.get('decision') == 'approved':
        print("Approved!")
    elif final.get('decision') == 'timeout':
        print("Decision timeout")
```

**Behavior:**
- Polls `get_action_status()` every `poll_interval` seconds
- Returns immediately if status is not "pending"
- Returns timeout indicator if decision not received within `timeout` seconds

---

### list_actions()

**Source**: Lines 285-310

List recent agent actions for the organization.

```python
def list_actions(
    self,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
) -> Dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|----------|-------------|
| `limit` | int | 50 | Maximum number of actions to return |
| `offset` | int | 0 | Pagination offset |
| `status` | str | None | Filter by status ("approved", "pending", "denied") |

**Returns**: `Dict` with keys:
- `actions` (list): List of action objects
- `total` (int): Total number of matching actions
- Pagination metadata

**Example**:
```python
# Get all recent actions
actions = client.list_actions(limit=100)

# Get only approved actions
approved = client.list_actions(status="approved", limit=50)

# Paginate through actions
page1 = client.list_actions(limit=50, offset=0)
page2 = client.list_actions(limit=50, offset=50)

# List all actions
for action in actions.get('actions', []):
    print(f"{action['action_id']}: {action['status']}")
```

**API Endpoint Used:**
- `GET /api/v1/actions?limit={limit}&offset={offset}&status={status}`

---

### get_action_details()

**Source**: Lines 312-326

Get detailed information about a specific action.

```python
def get_action_details(self, action_id: str) -> Dict
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action_id` | str | Yes | Action ID |

**Returns**: `Dict` with full action details including:
- Agent information
- Action type and resource
- Status and decision
- Risk score
- Timestamps
- Audit trail

**Example**:
```python
details = client.get_action_details("act_xyz789")

print(f"Agent: {details['agent_id']}")
print(f"Resource: {details['resource']}")
print(f"Risk Score: {details['risk_score']}")
print(f"Created: {details['created_at']}")
```

**API Endpoint Used:**
- `GET /api/v1/actions/{action_id}`

---

## AuthorizedAgent Class

**Source**: Lines 328-458

Wrapper for AI agents that require OW-AI authorization. Provides high-level authorization workflows.

### Constructor

**Source**: Lines 336-352

```python
def __init__(
    self,
    agent_id: str,
    agent_name: str,
    client: Optional[OWKAIClient] = None
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_id` | str | Yes | Unique identifier for this agent |
| `agent_name` | str | Yes | Human-readable agent name |
| `client` | OWKAIClient | No | OWKAIClient instance (creates new if not provided) |

**Example**:
```python
# With existing client
client = OWKAIClient()
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    client=client
)

# Creates client automatically
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI"
)
```

---

### request_authorization()

**Source**: Lines 354-400

Request authorization for an action.

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
) -> Dict
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action_type` | str | - | Type of action (use `ActionType` enum) |
| `resource` | str | - | Resource being accessed |
| `resource_id` | str | None | Specific resource identifier |
| `details` | dict | None | Additional action details |
| `context` | dict | None | Contextual information |
| `risk_indicators` | dict | None | Risk assessment data |
| `wait_for_decision` | bool | True | Whether to wait for decision |
| `timeout` | int | 60 | Decision timeout in seconds (if waiting) |

**Returns**: `Dict` with authorization decision

**Example**:
```python
agent = AuthorizedAgent("my-agent", "My Agent")

# Request with automatic waiting
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_database",
    resource_id="CUST-12345",
    details={"operation": "read"},
    context={"user_request": "Show customer"},
    risk_indicators={"pii_involved": True},
    wait_for_decision=True,
    timeout=60
)

if decision.get('decision') == 'approved':
    execute_action()
```

**Behavior:**
- Creates `AgentAction` internally
- Submits action via client
- Optionally waits for decision if `wait_for_decision=True`
- Returns immediately if action is auto-approved/denied

---

### execute_if_authorized()

**Source**: Lines 402-458

Execute a function only if authorized.

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
) -> Any
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action_type` | str | - | Type of action |
| `resource` | str | - | Resource being accessed |
| `execute_fn` | callable | - | Function to execute if authorized |
| `resource_id` | str | None | Specific resource identifier |
| `details` | dict | None | Additional action details |
| `context` | dict | None | Contextual information |
| `risk_indicators` | dict | None | Risk assessment data |
| `timeout` | int | 60 | Decision timeout in seconds |

**Returns**: Result of `execute_fn()` if authorized

**Raises:**
- `PermissionError` - If action is denied (lines 450-452)
- `TimeoutError` - If decision times out (lines 454-455)
- `Exception` - For unexpected status (lines 457-458)

**Example**:
```python
agent = AuthorizedAgent("my-agent", "My Agent")

def get_customer_data():
    """Function to execute if authorized."""
    return fetch_from_database()

try:
    result = agent.execute_if_authorized(
        action_type="data_access",
        resource="customer_database",
        execute_fn=get_customer_data,
        resource_id="CUST-12345",
        timeout=60
    )
    print(f"Result: {result}")

except PermissionError as e:
    print(f"Denied: {e}")

except TimeoutError as e:
    print(f"Timeout: {e}")
```

**Behavior:**
1. Requests authorization via `request_authorization()`
2. Waits for decision (up to `timeout` seconds)
3. If approved: executes `execute_fn()` and returns result
4. If denied: raises `PermissionError`
5. If timeout: raises `TimeoutError`

---

## Data Types

### Response Structures

#### Action Response

Returned by `submit_action()`:

```python
{
    "action_id": "act_xyz789",
    "status": "approved",  # or "pending", "denied"
    "decision": "approved",
    "risk_score": 45,
    "reason": "Policy matched",  # if denied
    "created_at": "2025-12-04T10:30:00Z"
}
```

#### Status Response

Returned by `get_action_status()`:

```python
{
    "action_id": "act_xyz789",
    "decision": "approved",
    "status": "approved",
    "updated_at": "2025-12-04T10:30:05Z",
    "risk_score": 45
}
```

#### Action Details

Returned by `get_action_details()`:

```python
{
    "action_id": "act_xyz789",
    "agent_id": "agent-001",
    "agent_name": "My Agent",
    "action_type": "data_access",
    "resource": "customer_database",
    "resource_id": "CUST-12345",
    "action_details": {...},
    "context": {...},
    "risk_indicators": {...},
    "status": "approved",
    "decision": "approved",
    "risk_score": 45,
    "created_at": "2025-12-04T10:30:00Z",
    "updated_at": "2025-12-04T10:30:05Z"
}
```

#### Actions List

Returned by `list_actions()`:

```python
{
    "actions": [
        {
            "action_id": "act_001",
            "agent_id": "agent-001",
            "action_type": "data_access",
            "resource": "database",
            "status": "approved",
            "created_at": "2025-12-04T10:00:00Z"
        },
        # ... more actions
    ],
    "total": 150,
    "limit": 50,
    "offset": 0
}
```

---

## Exception Reference

### ValueError

**Source**: Lines 139-140

Raised when required configuration is missing.

```python
if not self.api_key:
    raise ValueError("API key is required. Set OWKAI_API_KEY environment variable.")
```

### TimeoutError

**Source**: Lines 188-189, 454-455

Raised when requests or authorization decisions timeout.

```python
# Request timeout
except requests.exceptions.Timeout:
    raise TimeoutError("API request timed out")

# Authorization timeout
elif status == 'timeout':
    raise TimeoutError("Authorization decision timed out")
```

### ConnectionError

**Source**: Lines 191-193

Raised when API connection fails.

```python
except requests.exceptions.ConnectionError:
    raise ConnectionError("Failed to connect to OW-AI API")
```

### PermissionError

**Source**: Lines 450-452

Raised by `execute_if_authorized()` when action is denied.

```python
elif status == 'denied':
    reason = decision.get('reason', 'No reason provided')
    raise PermissionError(f"Action denied: {reason}")
```

### Exception

**Source**: Lines 177-185

General API errors are wrapped in `Exception`.

```python
except requests.exceptions.HTTPError as e:
    error_detail = e.response.json().get('detail', str(e))
    raise Exception(f"API Error: {error_detail}")
```

---

## Complete Example

```python
from python_sdk_example import (
    OWKAIClient,
    AuthorizedAgent,
    AgentAction,
    ActionType
)

# Initialize client
client = OWKAIClient()

# Test connection
status = client.test_connection()
print(f"Connected: {status['status']}")

# Create agent
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI",
    client=client
)

# Define operation
def process_transaction():
    return {"status": "completed", "amount": 50000}

# Execute with authorization
try:
    result = agent.execute_if_authorized(
        action_type=ActionType.TRANSACTION.value,
        resource="customer_account",
        execute_fn=process_transaction,
        resource_id="ACC-12345",
        details={"amount": 50000, "currency": "USD"},
        risk_indicators={"external_transfer": True},
        timeout=60
    )
    print(f"Success: {result}")

except PermissionError as e:
    print(f"Denied: {e}")

except TimeoutError as e:
    print(f"Timeout: {e}")

# List recent actions
actions = client.list_actions(limit=10)
for action in actions.get('actions', []):
    print(f"{action['action_id']}: {action['status']}")
```

---

## Next Steps

- [Installation](/sdk/python/installation) - Set up the SDK
- [Client Configuration](/sdk/python/client-configuration) - Configure the client
- [Agent Actions](/sdk/python/agent-actions) - Submit actions
- [Error Handling](/sdk/python/error-handling) - Handle errors

## Source Code

Complete implementation:
```
/ow-ai-backend/integration-examples/python_sdk_example.py (622 lines)
```

## API Endpoints

Summary of backend endpoints used by the SDK:

| Endpoint | Method | SDK Method | Purpose |
|----------|--------|------------|---------|
| `/health` | GET | `test_connection()` | Health check |
| `/api/deployment-info` | GET | `test_connection()` | Version info |
| `/api/v1/actions/submit` | POST | `submit_action()` | Submit action |
| `/api/v1/actions/{id}/status` | GET | `get_action_status()` | Get status |
| `/api/v1/actions` | GET | `list_actions()` | List actions |
| `/api/v1/actions/{id}` | GET | `get_action_details()` | Get details |
