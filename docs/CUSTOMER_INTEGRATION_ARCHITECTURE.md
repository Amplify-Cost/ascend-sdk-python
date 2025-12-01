# OW-AI Enterprise Customer Integration Architecture

## Executive Summary

OW-AI provides enterprise-grade AI governance that integrates seamlessly with your existing AI infrastructure. This document outlines how customers integrate OW-AI into their architecture from both client and server perspectives.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │  LangChain/      │    │   Custom AI      │    │   MCP Server     │     │
│   │  LangGraph       │    │   Agents         │    │   (Claude, etc)  │     │
│   │  Agents          │    │                  │    │                  │     │
│   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘     │
│            │                       │                       │                │
│            └───────────────────────┼───────────────────────┘                │
│                                    │                                        │
│                                    ▼                                        │
│                    ┌───────────────────────────────┐                        │
│                    │      OW-AI Python SDK         │                        │
│                    │   (owkai_client.py)           │                        │
│                    └───────────────┬───────────────┘                        │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     │ HTTPS (TLS 1.2+)
                                     │ X-API-Key Authentication
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OW-AI GOVERNANCE PLATFORM                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                     API Gateway (FastAPI)                         │     │
│   │  /api/sdk/agent-action  /api/registry/*  /api/agent-activity     │     │
│   └──────────────────────────┬───────────────────────────────────────┘     │
│                              │                                              │
│   ┌──────────────────────────┼──────────────────────────────────────┐      │
│   │                          ▼                                       │      │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │      │
│   │  │   Agent     │  │   Policy    │  │   Alert     │              │      │
│   │  │  Registry   │──│   Engine    │──│   System    │              │      │
│   │  └─────────────┘  └─────────────┘  └─────────────┘              │      │
│   │         │               │                │                       │      │
│   │         └───────────────┼────────────────┘                       │      │
│   │                         ▼                                        │      │
│   │              ┌──────────────────┐                               │      │
│   │              │  PostgreSQL RDS  │                               │      │
│   │              │  (Multi-Tenant)  │                               │      │
│   │              └──────────────────┘                               │      │
│   │                                                                  │      │
│   │                 GOVERNANCE ENGINE                                │      │
│   └──────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                    Notification System                            │     │
│   │  Webhooks │ Email (SES) │ Slack │ Teams │ PagerDuty │ ServiceNow │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integration Patterns

### Pattern 1: Direct SDK Integration (Recommended)

Best for: Custom AI agents, LangChain/LangGraph applications

```python
from owkai_client import OWKAIClient, AuthorizedAgent

# Initialize client
client = OWKAIClient(
    api_key=os.getenv("OWKAI_API_KEY"),
    base_url="https://pilot.owkai.app"
)

# Create authorized agent
agent = AuthorizedAgent(
    client=client,
    agent_id="financial-advisor-001",
    display_name="Financial Advisor AI",
    agent_type="supervised",
    auto_approve_below=30,     # Auto-approve low risk
    max_risk_threshold=80      # Escalate high risk
)

# Register agent (idempotent)
agent.register(
    allowed_action_types=["query", "recommendation", "transaction"],
    allowed_resources=["portfolio_db", "trading_system"],
    tags=["finance", "customer-facing"]
)

# Request permission before performing actions
result = agent.request_permission(
    action_type="transaction",
    description="Execute stock purchase order",
    risk_score=72,
    resource="trading_system",
    metadata={"symbol": "AAPL", "shares": 100}
)

if result.can_proceed:
    # Execute the action
    execute_trade(result.action_id)
elif result.is_pending:
    # Wait for human approval
    result = agent.request_permission(
        ...,
        wait_for_approval=True,
        timeout=300
    )
```

### Pattern 2: LangChain Tool Integration

Best for: LangChain/LangGraph agents using tools

```python
from langchain.tools import tool
from owkai_client import quick_agent

# Create authorized agent
owkai_agent = quick_agent("langchain-data-analyst")

@tool
def query_customer_database(query: str) -> str:
    """Query the customer database for information."""

    # Request permission from OW-AI
    result = owkai_agent.request_permission(
        action_type="data_access",
        description=f"Executing database query: {query[:100]}",
        risk_score=45,
        resource="customer_database",
        metadata={"query": query}
    )

    if not result.can_proceed:
        return f"Action requires approval. Action ID: {result.action_id}"

    # Execute the actual query
    return execute_query(query)

@tool
def send_customer_email(to: str, subject: str, body: str) -> str:
    """Send an email to a customer."""

    # Request permission
    result = owkai_agent.request_permission(
        action_type="communication",
        description=f"Sending email to {to}: {subject}",
        risk_score=35,
        resource="email_system",
        metadata={"to": to, "subject": subject}
    )

    if not result.can_proceed:
        return f"Email pending approval. Action ID: {result.action_id}"

    return send_email(to, subject, body)
```

### Pattern 3: MCP Server Integration

Best for: Claude Desktop, Cursor, or MCP-enabled applications

```python
# MCP Server with OW-AI Governance
from mcp import Server
from owkai_client import OWKAIClient, AuthorizedAgent

# Initialize OW-AI governance
owkai = OWKAIClient()
governance_agent = AuthorizedAgent(
    client=owkai,
    agent_id="mcp-file-server",
    agent_type="mcp_server"
)

# Register MCP server with OW-AI
owkai.post("/api/registry/mcp-servers", data={
    "server_name": "file-operations",
    "display_name": "File Operations Server",
    "transport_type": "stdio",
    "governance_enabled": True,
    "auto_approve_tools": ["read_file"],  # Low-risk tools
    "blocked_tools": ["delete_file"],      # Blocked tools
    "tool_risk_overrides": {
        "write_file": 60,
        "execute_command": 90
    }
})

@server.tool("write_file")
async def write_file(path: str, content: str):
    """Write content to a file."""

    # Request governance approval
    result = governance_agent.request_permission(
        action_type="file_write",
        description=f"Writing to file: {path}",
        risk_score=60,
        resource=f"file:{path}",
        metadata={"path": path, "size": len(content)}
    )

    if not result.can_proceed:
        raise PermissionError(f"Write blocked. Approval required: {result.action_id}")

    # Execute file write
    with open(path, 'w') as f:
        f.write(content)

    return {"success": True, "action_id": result.action_id}
```

### Pattern 4: Webhook-Based Async Approval

Best for: Long-running processes, background jobs

```python
import requests

# Configure webhook URL in OW-AI dashboard
# OW-AI will POST to this URL when actions are approved/rejected

# Submit action
response = requests.post(
    "https://pilot.owkai.app/api/sdk/agent-action",
    headers={"X-API-Key": api_key},
    json={
        "agent_id": "batch-processor",
        "action_type": "batch_operation",
        "description": "Processing 10,000 customer records",
        "risk_score": 75,
        "metadata": {
            "record_count": 10000,
            "callback_url": "https://your-service.com/webhooks/owkai"
        }
    }
)

action_id = response.json()["action_id"]

# Your webhook endpoint receives:
# POST /webhooks/owkai
# {
#     "event": "action.approved",
#     "action_id": 12345,
#     "approved_by": "admin@company.com",
#     "timestamp": "2025-12-01T10:30:00Z"
# }
```

## Approval Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ACTION SUBMISSION FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   AI Agent submits action                                                    │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────────┐                                                       │
│   │  Risk Scoring   │  ◄── Evaluates action context, agent policies         │
│   └────────┬────────┘                                                       │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────┐           │
│   │                    RISK-BASED ROUTING                        │           │
│   ├─────────────────────────────────────────────────────────────┤           │
│   │                                                              │           │
│   │   Risk < 30    ──────────► AUTO-APPROVE ──► Agent Proceeds  │           │
│   │                                                              │           │
│   │   Risk 30-59   ──────────► PENDING ──────► Manager Approval │           │
│   │                                                              │           │
│   │   Risk 60-79   ──────────► HIGH RISK ────► Security Review  │           │
│   │                           + ALERT         + Manager + CISO   │           │
│   │                                                              │           │
│   │   Risk 80+     ──────────► CRITICAL ─────► Executive        │           │
│   │                           + ALERT         + Emergency Team   │           │
│   │                                                              │           │
│   └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│   Approved/Rejected notification sent to:                                    │
│   • SDK (polling or webhook)                                                 │
│   • Agent dashboard                                                          │
│   • Audit log                                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API Reference

### Authentication

All API requests require authentication via API key:

```bash
curl -X POST https://pilot.owkai.app/api/sdk/agent-action \
  -H "X-API-Key: owkai_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "my-agent", "action_type": "query", "description": "Test"}'
```

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sdk/agent-action` | POST | Submit action for authorization |
| `/api/agent-action/status/{id}` | GET | Check action status |
| `/api/registry/agents` | POST | Register a new agent |
| `/api/registry/agents` | GET | List all agents |
| `/api/registry/agents/{id}` | GET | Get agent details |
| `/api/registry/agents/{id}` | PUT | Update agent config |
| `/api/registry/agents/{id}/activate` | POST | Activate agent |
| `/api/registry/agents/{id}/suspend` | POST | Suspend agent |
| `/api/registry/agents/{id}/policies` | POST | Add policy |
| `/api/registry/agents/{id}/evaluate` | POST | Evaluate policies |
| `/api/registry/mcp-servers` | POST | Register MCP server |
| `/api/registry/mcp-servers` | GET | List MCP servers |

### Action Submission Request

```json
{
    "agent_id": "financial-advisor-001",
    "action_type": "transaction",
    "description": "Execute stock purchase order",
    "risk_score": 72,
    "resource": "trading_system",
    "metadata": {
        "symbol": "AAPL",
        "shares": 100,
        "estimated_value": 19000
    }
}
```

### Action Response

```json
{
    "id": 12345,
    "action_id": 12345,
    "agent_id": "financial-advisor-001",
    "action_type": "transaction",
    "status": "pending",
    "risk_score": 72,
    "risk_level": "high",
    "requires_approval": true,
    "approved": false,
    "alert_generated": true,
    "alert_id": 6789,
    "poll_url": "/api/agent-action/status/12345",
    "enterprise_grade": true,
    "sdk_integration": true
}
```

## Security Best Practices

### API Key Management

1. **Never hardcode API keys** - Use environment variables
2. **Rotate keys regularly** - 90-day rotation recommended
3. **Use separate keys per environment** - Dev, staging, production
4. **Monitor key usage** - Alert on anomalies

### Network Security

1. **TLS 1.2+ required** - All API calls encrypted
2. **IP allowlisting** - Restrict API access to known IPs
3. **Rate limiting** - Automatic rate limiting applied
4. **Request signing** - Optional HMAC signing for webhooks

### Audit & Compliance

1. **All actions logged** - Immutable audit trail
2. **SOC 2 compliant** - Full compliance evidence
3. **HIPAA ready** - PHI access controls
4. **PCI-DSS ready** - Payment data protection

## Error Handling

```python
from owkai_client import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ServerError,
    ApprovalTimeoutError
)

try:
    result = agent.request_permission(...)
except AuthenticationError:
    # Invalid API key
    logger.error("Check OWKAI_API_KEY")
except AuthorizationError:
    # Insufficient permissions
    logger.error("API key lacks required permissions")
except ValidationError as e:
    # Invalid request data
    logger.error(f"Validation error: {e}")
except ApprovalTimeoutError:
    # Approval wait timed out
    logger.warning("Approval not received in time")
except ServerError:
    # OW-AI service error
    logger.error("Retry with exponential backoff")
```

## Monitoring & Observability

### Metrics Available

- Action submission rate
- Approval latency
- Risk score distribution
- Auto-approve vs manual approval ratio
- Alert generation rate
- Agent activity by type

### Webhook Events

Configure webhooks to receive real-time notifications:

- `action.approved` - Action approved
- `action.rejected` - Action rejected
- `action.expired` - Action expired without approval
- `alert.created` - High-risk alert generated
- `agent.suspended` - Agent suspended

## Getting Started

1. **Get API Key**: Contact admin@ow-kai.com or generate via dashboard
2. **Install SDK**: `pip install owkai-sdk` (or copy `owkai_client.py`)
3. **Set Environment**:
   ```bash
   export OWKAI_API_KEY="owkai_your_key_here"
   export OWKAI_API_URL="https://pilot.owkai.app"
   ```
4. **Register Agent**: Use SDK to register your AI agent
5. **Integrate**: Wrap your agent's actions with permission requests
6. **Monitor**: View activity in OW-AI dashboard

## Support

- Documentation: https://pilot.owkai.app/docs
- API Reference: https://pilot.owkai.app/api/docs
- Support: support@ow-kai.com
- Enterprise: enterprise@ow-kai.com

---

**OW-AI Enterprise** - Banking-Level AI Governance
*Compliance: SOC 2 Type II | HIPAA | PCI-DSS | GDPR | SOX*
