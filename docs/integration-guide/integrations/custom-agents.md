# Custom Agents

Build custom AI agents with OW-kai governance using the Python SDK reference implementation.

## Status

**Integration Status**: Example Available
**Source Code**: `ow-ai-backend/integration-examples/python_sdk_example.py`
**API Documentation**: REST API endpoints

## Installation

```bash
pip install requests python-dotenv
```

Note: There is no published `owkai-sdk` package. Copy the `OWKAIClient` class from `python_sdk_example.py` or use direct REST API calls.

## Quick Start

```python
from owkai import OWKAIClient, AuthorizedAgent

# Initialize client
client = OWKAIClient(
    api_key="owkai_admin_your_key_here",
    api_url="https://pilot.owkai.app"
)

# Create authorized agent
agent = AuthorizedAgent(
    agent_id="my-agent-001",
    agent_name="My Custom Agent",
    client=client
)

# Request authorization
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_database",
    details={"operation": "read"}
)

# Execute if approved
if decision.get('decision') == 'approved':
    result = execute_action()
```

For the complete OWKAIClient and AuthorizedAgent class implementations (500+ lines), see `ow-ai-backend/integration-examples/python_sdk_example.py`.

## Core Concepts

### AgentAction

```python
from dataclasses import dataclass

@dataclass
class AgentAction:
    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    resource_id: Optional[str] = None
    action_details: Optional[Dict] = None
    context: Optional[Dict] = None
    risk_indicators: Optional[Dict] = None
```

### Authorization Flow

```
1. Agent requests authorization
   ↓
2. OW-kai evaluates risk
   ↓
3. Policy engine checks rules
   ↓
4. Decision: ALLOW, DENY, or REQUIRE_APPROVAL
   ↓
5. If approved: Execute action
```

## Example: Financial Advisor Agent

From `python_sdk_example.py`:

```python
# Create agent
agent = AuthorizedAgent(
    agent_id="financial-advisor-001",
    agent_name="Financial Advisor AI"
)

# Low-risk: Auto-approved
decision = agent.request_authorization(
    action_type="query",
    resource="market_data",
    risk_indicators={"pii_involved": False}
)

# Medium-risk: Evaluated
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_portfolio",
    resource_id="CUST-12345",
    risk_indicators={
        "pii_involved": True,
        "data_sensitivity": "medium"
    }
)

# High-risk: Requires approval
decision = agent.request_authorization(
    action_type="transaction",
    resource="customer_account",
    details={
        "amount": 50000,
        "destination": "external_account"
    },
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True
    }
)
```

## API Endpoints

```
POST   /api/v1/actions/submit              # Submit action
GET    /api/v1/actions/{id}/status        # Check status
GET    /api/v1/actions                    # List actions
GET    /api/deployment-info               # API info
GET    /health                            # Health check
```

## Error Handling

```python
try:
    result = agent.execute_if_authorized(
        action_type="transaction",
        resource="payment",
        execute_fn=process_payment
    )
except PermissionError as e:
    print(f"Denied: {e}")
except TimeoutError:
    print("Approval timeout")
except ConnectionError:
    print("API unavailable")
```

## Best Practices

### 1. Rich Context

```python
decision = agent.request_authorization(
    action_type="data_access",
    resource="customer_database",
    resource_id="CUST-12345",
    details={
        "operation": "read",
        "fields": ["email", "phone"],
        "purpose": "support"
    },
    context={
        "ticket_id": "TICKET-789",
        "user_consent": True
    },
    risk_indicators={
        "pii_involved": True,
        "data_sensitivity": "high"
    }
)
```

### 2. Descriptive Action Types

```python
# Good
"data_access", "data_modification", "transaction"

# Bad
"action", "operation"
```

### 3. Unique Agent IDs

```python
# Good
agent_id = "customer-service-v2"

# Bad
agent_id = "bot1"
```

## Complete SDK Code

The full SDK implementation is available in:
- **File**: `ow-ai-backend/integration-examples/python_sdk_example.py`
- **Lines**: 622 total
- **Classes**: `OWKAIClient`, `AuthorizedAgent`, `AgentAction`
- **Methods**: Connection testing, action submission, approval polling, error handling

## Next Steps

- [MCP Server](/integrations/mcp-server) - MCP server governance
- [LangChain](/integrations/langchain) - LangChain integration
- [Overview](/integrations/overview) - All integrations
