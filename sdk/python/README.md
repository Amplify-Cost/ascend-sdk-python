# ASCEND Python SDK v2.0

Enterprise-grade AI governance SDK for Python applications.

## Features

- **Fail Mode Configuration** - Choose between fail-closed (secure) or fail-open (available) when ASCEND is unreachable
- **Circuit Breaker Pattern** - Automatic failure detection with graceful recovery
- **Agent Registration** - Register agents with capabilities and permissions
- **Action Evaluation** - Real-time authorization decisions with risk scoring
- **Completion Logging** - Track action success/failure for audit trails
- **Approval Workflows** - Human-in-the-loop approval for high-risk actions
- **MCP Integration** - Native decorator for MCP server tools
- **HMAC-SHA256 Signing** - Request integrity verification
- **Structured Logging** - JSON logs with automatic API key masking

## Installation

```bash
pip install ascend-sdk
```

Or from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

```python
from owkai_sdk import AscendClient, FailMode, Decision

# Initialize client
client = AscendClient(
    api_key="owkai_your_api_key",
    agent_id="agent-001",
    agent_name="My AI Agent",
    fail_mode=FailMode.CLOSED,  # Block on ASCEND unreachable
)

# Register agent (call once on startup)
client.register(
    agent_type="automation",
    capabilities=["data_access", "file_operations"],
    allowed_resources=["production_db", "/var/log/*"]
)

# Evaluate action before execution
decision = client.evaluate_action(
    action_type="database.query",
    resource="production_db",
    parameters={"query": "SELECT * FROM users WHERE active = true"}
)

if decision.decision == Decision.ALLOWED:
    # Execute your action
    result = execute_database_query()

    # Log completion
    client.log_action_completed(
        action_id=decision.action_id,
        result={"rows_returned": len(result)},
        duration_ms=150
    )
elif decision.decision == Decision.DENIED:
    print(f"Action denied: {decision.reason}")
    print(f"Policy violations: {decision.policy_violations}")
elif decision.decision == Decision.PENDING:
    print(f"Awaiting approval from: {decision.required_approvers}")
```

## Fail Mode Configuration

ASCEND supports two fail modes for handling service unavailability:

### Fail-Closed (Recommended for Production)

```python
client = AscendClient(
    api_key="...",
    agent_id="...",
    agent_name="...",
    fail_mode=FailMode.CLOSED  # Default
)
```

When ASCEND is unreachable:
- All actions are **blocked**
- `ConnectionError` or `CircuitBreakerOpen` exception raised
- Ensures no unauthorized actions occur

### Fail-Open (Use with Caution)

```python
client = AscendClient(
    api_key="...",
    agent_id="...",
    agent_name="...",
    fail_mode=FailMode.OPEN
)
```

When ASCEND is unreachable:
- Actions are **allowed** to proceed
- Returns synthetic `ALLOWED` decision with `fail_open_mode` condition
- Use only when availability is critical

## Circuit Breaker

The SDK includes an automatic circuit breaker to prevent cascading failures:

```python
# Circuit breaker is enabled by default
# Customize thresholds:
client = AscendClient(
    api_key="...",
    agent_id="...",
    agent_name="...",
    circuit_breaker_failure_threshold=5,   # Open after 5 failures
    circuit_breaker_recovery_timeout=30,   # Try recovery after 30s
    circuit_breaker_half_open_max_calls=3  # Allow 3 test calls in half-open
)
```

Circuit states:
- **CLOSED**: Normal operation, requests flow through
- **OPEN**: After threshold failures, requests fail immediately
- **HALF_OPEN**: After recovery timeout, limited test requests allowed

## MCP Server Integration

Integrate ASCEND governance with MCP (Model Context Protocol) servers:

```python
from owkai_sdk import AscendClient
from owkai_sdk.mcp import mcp_governance, high_risk_action

client = AscendClient(api_key="...", agent_id="...", agent_name="...")

# Basic governance
@mcp_server.tool()
@mcp_governance(client, action_type="database.query", resource="production_db")
async def query_database(sql: str):
    """Execute SQL query on production database."""
    return await db.execute(sql)

# High-risk action requiring human approval
@mcp_server.tool()
@high_risk_action(client, action_type="database.delete", resource="production_db")
async def delete_records(table: str, where_clause: str):
    """Delete records from production database."""
    return await db.execute(f"DELETE FROM {table} WHERE {where_clause}")
```

### MCP Governance Configuration

```python
from owkai_sdk.mcp import mcp_governance, MCPGovernanceConfig

config = MCPGovernanceConfig(
    wait_for_approval=True,           # Wait for pending approvals
    approval_timeout_seconds=300,     # 5 minute timeout
    approval_poll_interval_seconds=5, # Check every 5 seconds
    raise_on_denial=True,             # Raise exception on denial
    log_all_decisions=True,           # Log all authorization decisions
    on_approval_required=notify_admin # Custom callback
)

@mcp_governance(client, "file.write", "/etc/config", config=config)
async def write_config(content: str):
    return write_to_file(content)
```

### Middleware Pattern

```python
from owkai_sdk.mcp import MCPGovernanceMiddleware

middleware = MCPGovernanceMiddleware(client)

# Wrap multiple tools
query_tool = middleware.govern("database.query", "prod_db")(query_fn)
write_tool = middleware.govern("file.write", "/var/log")(write_fn)
delete_tool = middleware.govern("database.delete", "prod_db", require_human_approval=True)(delete_fn)

# Check governed tools
print(f"Governed tools: {middleware.governed_tools}")
```

## Approval Workflows

Handle human-in-the-loop approvals for high-risk actions:

```python
# Request with automatic approval waiting
decision = client.evaluate_action(
    action_type="financial.transfer",
    resource="payment_gateway",
    parameters={"amount": 50000, "currency": "USD"},
    wait_for_approval=True,        # Block until approved/denied
    approval_timeout=300,          # 5 minute timeout
    require_human_approval=True    # Force human review
)

# Manual approval polling
decision = client.evaluate_action(
    action_type="financial.transfer",
    resource="payment_gateway",
    parameters={"amount": 50000}
)

if decision.decision == Decision.PENDING:
    approval_id = decision.approval_request_id

    # Poll for approval
    while True:
        status = client.check_approval(approval_id)
        if status["status"] == "approved":
            # Execute action
            break
        elif status["status"] == "rejected":
            # Handle rejection
            break
        time.sleep(5)
```

## Webhook Configuration

Receive real-time notifications for authorization events:

```python
client.configure_webhook(
    url="https://your-app.com/webhooks/ascend",
    events=[
        "action.evaluated",
        "action.approved",
        "action.denied",
        "action.completed",
        "action.failed"
    ],
    secret="your_webhook_secret"  # For signature verification
)
```

## Structured Logging

The SDK includes structured JSON logging with automatic API key masking:

```python
from owkai_sdk import AscendClient, AscendLogger

# Configure log level
client = AscendClient(
    api_key="...",
    agent_id="...",
    agent_name="...",
    log_level="DEBUG",  # DEBUG, INFO, WARNING, ERROR
    json_logs=True      # Enable JSON format
)

# Logs automatically mask API keys:
# {"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Evaluating action", "api_key": "owkai_****"}
```

## Error Handling

```python
from owkai_sdk import (
    AscendClient,
    AuthenticationError,
    AuthorizationError,
    CircuitBreakerOpen,
    ConnectionError,
    TimeoutError,
    RateLimitError
)

try:
    decision = client.evaluate_action(...)
except AuthenticationError as e:
    print(f"Invalid API key: {e}")
except AuthorizationError as e:
    print(f"Authorization denied: {e}")
    print(f"Policy violations: {e.policy_violations}")
    print(f"Risk score: {e.risk_score}")
except CircuitBreakerOpen as e:
    print(f"Service unavailable: {e}")
    print(f"Recovery in: {e.recovery_time}s")
except ConnectionError as e:
    print(f"Connection failed: {e}")
except TimeoutError as e:
    print(f"Request timed out after {e.timeout_seconds}s")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
```

## API Reference

### AscendClient

```python
AscendClient(
    api_key: str,                    # Required: Organization API key
    agent_id: str,                   # Required: Unique agent identifier
    agent_name: str,                 # Required: Human-readable name
    api_url: str = "https://pilot.owkai.app",
    environment: str = "production",
    fail_mode: FailMode = FailMode.CLOSED,
    timeout: int = 30000,            # Request timeout in ms
    max_retries: int = 3,
    log_level: str = "INFO",
    json_logs: bool = True,
    signing_secret: str = None,      # For HMAC signing
    circuit_breaker_failure_threshold: int = 5,
    circuit_breaker_recovery_timeout: int = 30,
    circuit_breaker_half_open_max_calls: int = 3
)
```

### Methods

| Method | Description |
|--------|-------------|
| `register(agent_type, capabilities, allowed_resources, metadata)` | Register agent with ASCEND |
| `evaluate_action(action_type, resource, parameters, context, ...)` | Evaluate action for authorization |
| `log_action_completed(action_id, result, duration_ms)` | Log successful completion |
| `log_action_failed(action_id, error, duration_ms)` | Log action failure |
| `check_approval(approval_request_id)` | Check approval status |
| `configure_webhook(url, events, secret)` | Configure webhook notifications |

## Compliance

This SDK supports the following compliance frameworks:

- **SOC 2 Type II** (CC6.1) - Access control and audit trails
- **HIPAA** (164.312(e)) - Transmission security
- **PCI-DSS** (8.2, 8.3) - API key management, MFA
- **NIST AI RMF** - Govern, Map, Measure, Manage
- **NIST 800-63B** - Authentication standards

## Support

- Documentation: https://docs.ascendowkai.com
- Issues: https://github.com/anthropics/ascend-sdk-python/issues
- Email: support@ascendowkai.com
