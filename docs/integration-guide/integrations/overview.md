# Integrations Overview

OW-kai provides enterprise-grade governance for AI agents through multiple integration patterns. All integrations route through our authorization center for policy evaluation, approval workflows, and compliance audit trails.

## Integration Status

### AI Agent Frameworks

| Framework | Integration Type | Status | Source Code |
|-----------|-----------------|--------|-------------|
| [MCP Server](/integrations/mcp-server) | Python Example | Example Available | `integration-examples/03_mcp_server.py`, `08_mcp_server_v2.py` |
| [LangChain](/integrations/langchain) | Python SDK | Example Available | `integration-examples/01_langchain_agent.py` |
| [Custom Agents](/integrations/custom-agents) | REST API + SDK | Example Available | `integration-examples/python_sdk_example.py` |
| [Claude Code](/integrations/claude-code) | Documentation | Planned | - |
| [AutoGPT](/integrations/autogpt) | Documentation | Planned | - |

### Backend Integration Examples

| Pattern | Purpose | Status | Source Code |
|---------|---------|--------|-------------|
| AWS Lambda | Serverless governance | Example Available | `integration-examples/02_aws_lambda.py` |
| FastAPI Middleware | API governance | Example Available | `integration-examples/04_fastapi_middleware.py` |
| Webhook Handler | Event-driven workflows | Example Available | `integration-examples/06_webhook_handler.py` |

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        YOUR AI INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  LangChain  │  │   MCP       │  │   Custom    │  │  AWS Lambda │    │
│  │    Agent    │  │   Server    │  │   Agents    │  │   Function  │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                   │                                      │
│                          ┌────────▼────────┐                            │
│                          │   OWKAIClient   │                            │
│                          │   Python SDK    │                            │
│                          └────────┬────────┘                            │
│                                   │                                      │
└───────────────────────────────────┼──────────────────────────────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  OW-KAI PLATFORM  │
                          │   • Risk Engine   │
                          │   • Policy Engine │
                          │   • Workflows     │
                          │   • Audit Logs    │
                          └─────────┬─────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────▼─────────┐ ┌────────▼────────┐ ┌─────────▼─────────┐
    │   Slack/Teams     │ │     Splunk      │ │   ServiceNow      │
    │   (Approvals)     │ │     (SIEM)      │ │   (Tickets)       │
    └───────────────────┘ └─────────────────┘ └───────────────────┘
```

## Quick Integration Guide

### 1. Choose Your Integration Pattern

| If you're building... | Use this integration |
|--------------------|----------------------|
| MCP-compatible tools | [MCP Server Example](/integrations/mcp-server) |
| LangChain agents | [LangChain Integration](/integrations/langchain) |
| Custom Python agents | [Python SDK](/integrations/custom-agents) |
| Serverless functions | AWS Lambda example |
| API backends | FastAPI middleware example |

### 2. Install SDK

```bash
pip install requests python-dotenv
```

Note: There is no published `ascend-sdk` or `owkai-sdk` package. Use the examples with direct REST API calls or copy the client code from `integration-examples/python_sdk_example.py`.

### 3. Basic Integration Pattern

All integrations follow this pattern from `python_sdk_example.py`:

```python
import os
import requests

class OWKAIClient:
    """OW-kai Authorization Center SDK Client"""

    def __init__(self, api_url=None, api_key=None):
        self.api_url = api_url or os.getenv('OWKAI_API_URL', 'https://pilot.owkai.app')
        self.api_key = api_key or os.getenv('OWKAI_API_KEY')

        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
        }

    def submit_action(self, action):
        """Submit agent action for authorization"""
        response = requests.post(
            f"{self.api_url}/api/v1/actions/submit",
            headers=self.headers,
            json=action.to_dict()
        )
        response.raise_for_status()
        return response.json()

    def get_action_status(self, action_id):
        """Get current status of an action"""
        response = requests.get(
            f"{self.api_url}/api/v1/actions/{action_id}/status",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

### 4. Test Connection

```python
client = OWKAIClient()

# Test connectivity
health = client.test_connection()
print(f"Connection: {health['status']}")
```

## Integration Examples

### Example 1: LangChain Agent with Governance

From `integration-examples/01_langchain_agent.py`:

```python
from owkai import OWKAIClient

# Initialize client
client = OWKAIClient(
    api_key=os.getenv("OWKAI_API_KEY"),
    base_url="https://pilot.owkai.app"
)

def governed_database_query(query: str, database: str = "production"):
    """Execute database query with governance"""

    # Determine action type
    if query.upper().startswith("SELECT"):
        action_type = "database_read"
    elif query.upper().startswith(("INSERT", "UPDATE")):
        action_type = "database_write"
    elif query.upper().startswith("DELETE"):
        action_type = "database_delete"

    # Submit to OW-kai for governance
    result = client.execute_action(
        action_type=action_type,
        description=f"Execute SQL: {query}",
        tool_name="postgresql",
        target_system=f"{database}-db",
        risk_context={
            "database": database,
            "is_production": database == "production",
        }
    )

    if result.requires_approval:
        print(f"⏳ Waiting for approval...")
        status = client.wait_for_approval(result.action_id, timeout=300)
        print(f"✅ Approved by: {status.reviewed_by}")

    # Execute actual query
    return execute_query(query)
```

### Example 2: MCP Server with Governance Gateway

From `integration-examples/03_mcp_server.py`:

```python
async def execute_governed_tool(tool_name: str, arguments: dict):
    """Execute MCP tool with OW-kai governance"""

    # Evaluate with OW-kai
    evaluation = await governance_client.evaluate_action(
        server_id="mcp-enterprise-tools",
        namespace="database",
        verb="execute",
        resource=f"database://{arguments.get('database')}",
        parameters=arguments
    )

    if evaluation["decision"] == "DENY":
        return {"error": "Action blocked by governance policy"}

    elif evaluation["decision"] == "REQUIRE_APPROVAL":
        print(f"⏳ Waiting for approval...")
        approval = await governance_client.wait_for_approval(
            evaluation["action_id"],
            timeout=300
        )
        if not approval["approved"]:
            return {"error": "Action rejected by approver"}

    # Execute tool
    result = await _execute_tool(tool_name, arguments)
    return {"result": result}
```

### Example 3: AWS Lambda with Governance

From `integration-examples/02_aws_lambda.py`:

```python
from owkai.boto3_patch import enable_governance

# Enable governance BEFORE importing boto3
enable_governance(
    api_key=os.getenv("OWKAI_API_KEY"),
    base_url="https://pilot.owkai.app",
    risk_threshold=70,
    auto_approve_below=30,
    agent_id="aws-lambda-agent"
)

import boto3

def lambda_handler(event, context):
    """All boto3 calls are now governed"""
    s3 = boto3.client("s3")

    # Low-risk: auto-approved
    buckets = s3.list_buckets()

    # High-risk: requires approval
    s3.delete_bucket(Bucket="production-data")
```

## Integration Best Practices

### 1. Environment Variables

```bash
# .env
OWKAI_API_URL=https://pilot.owkai.app
OWKAI_API_KEY=owkai_admin_your_key_here
```

### 2. Consistent Agent IDs

```python
# Good
agent_id = "customer-service-agent-v2"
agent_id = "data-analyst-production"

# Bad
agent_id = "agent1"
agent_id = str(uuid4())  # Random IDs make tracking difficult
```

### 3. Rich Risk Context

```python
result = client.execute_action(
    action_type="database_delete",
    description="Delete old audit logs",
    tool_name="postgresql",
    risk_context={
        "database": "production",
        "table": "audit_logs",
        "where_clause": "created_at < '2025-01-01'",
        "estimated_rows": 10000,
        "is_production": True,
        "has_backup": True
    }
)
```

### 4. Error Handling

```python
from owkai import OWKAIActionRejectedError, OWKAIApprovalTimeoutError

try:
    result = client.execute_action(...)

    if result.requires_approval:
        status = client.wait_for_approval(result.action_id, timeout=300)

    execute_action()

except OWKAIActionRejectedError as e:
    logger.error(f"Action rejected: {e.rejection_reason}")
    notify_security_team(e)

except OWKAIApprovalTimeoutError:
    logger.warning("Approval timeout - action not executed")
```

## Available Endpoints

### Core Governance API

```
POST   /api/v1/actions/submit              # Submit action for evaluation
GET    /api/v1/actions/{id}/status        # Check approval status
GET    /api/v1/actions                    # List recent actions
GET    /api/deployment-info               # API version info
GET    /health                            # Health check
```

### MCP Governance API

```
POST   /mcp/governance/evaluate           # Evaluate MCP action
POST   /mcp/servers/register              # Register MCP server
GET    /mcp/servers                       # List registered servers
POST   /mcp/policies                      # Create governance policy
```

## Monitoring Integrations

### Health Check

```python
response = requests.get(
    "https://pilot.owkai.app/health",
    headers={"Authorization": f"Bearer {api_key}"}
)
print(response.json())  # {"status": "healthy"}
```

### Recent Actions

```python
response = requests.get(
    "https://pilot.owkai.app/api/v1/actions",
    headers={"Authorization": f"Bearer {api_key}"}
)
actions = response.json()
```

## Getting Help

- **Integration Issues**: Review example code in `/ow-ai-backend/integration-examples/`
- **API Documentation**: See `/docs` in the backend repository
- **Backend Source**: `/ow-ai-backend/routes/` for API route implementations

## Next Steps

- [MCP Server Integration](/integrations/mcp-server) - MCP governance examples
- [LangChain Integration](/integrations/langchain) - LangChain agent examples
- [Custom Agents](/integrations/custom-agents) - Python SDK usage
