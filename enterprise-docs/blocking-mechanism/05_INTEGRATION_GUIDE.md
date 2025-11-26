# OW-AI Enterprise Integration Guide

**Document Version:** 1.0
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-01-15
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [SDK Integration](#sdk-integration)
4. [MCP Server Integration](#mcp-server-integration)
5. [boto3 AWS Integration](#boto3-aws-integration)
6. [FastAPI Middleware Integration](#fastapi-middleware-integration)
7. [Testing Your Integration](#testing-your-integration)
8. [Production Checklist](#production-checklist)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Components

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| Python | 3.9+ | SDK runtime |
| OW-AI API Key | `owkai_admin_*` | Authentication |
| Network Access | HTTPS to pilot.owkai.app | API communication |
| SDK Package | `owkai` | Enforcement modules |

### Environment Variables

```bash
# Required
export OWKAI_API_KEY="owkai_admin_your_key_here"

# Optional (defaults shown)
export OWKAI_BASE_URL="https://pilot.owkai.app"
export OWKAI_APPROVAL_TIMEOUT="300"
export OWKAI_FAIL_CLOSED="true"
```

### Installation

```bash
# Install SDK
pip install owkai

# Or install from source
pip install git+https://github.com/owkai/owkai-sdk.git
```

---

## Quick Start

### 5-Minute Integration

```python
#!/usr/bin/env python3
"""Minimal OW-AI governance integration."""

from owkai.enforcement import EnforcedClient, GovernanceBlockedError

# Initialize client
client = EnforcedClient(
    api_key="owkai_admin_...",  # Or use OWKAI_API_KEY env var
    enforcement_mode="mandatory"
)

# Wrap any action with governance
try:
    result = client.execute_governed(
        action=lambda: perform_sensitive_operation(),
        action_type="database_write",
        description="Update user permissions"
    )
    print(f"Success: {result}")
except GovernanceBlockedError as e:
    print(f"Blocked: {e.blocking_reason}")
```

---

## SDK Integration

### Step 1: Import and Initialize

```python
from owkai.enforcement import (
    EnforcedClient,
    GovernanceBlockedError,
    ActionRejectedError,
    ApprovalTimeoutError,
    GovernanceUnavailableError,
)

# Initialize with mandatory enforcement
client = EnforcedClient(
    api_key="owkai_admin_...",
    enforcement_mode="mandatory",
    fail_closed=True,  # Required for mandatory mode
    approval_timeout=300,  # 5 minutes
)
```

### Step 2: Wrap Actions

```python
def perform_database_operation():
    # Method 1: Inline lambda
    result = client.execute_governed(
        action=lambda: db.execute("DELETE FROM logs WHERE age > 30"),
        action_type="database_delete",
        description="Clean up old log entries",
        tool_name="postgresql",
        target_system="production"
    )
    return result

# Method 2: Using the decorator
from owkai.enforcement import governed, configure_enforcement

# Configure once at startup
configure_enforcement(api_key="owkai_admin_...")

@governed(
    action_type="database_delete",
    description="Delete old logs",
    tool_name="postgresql"
)
def cleanup_logs(days_old: int = 30):
    return db.execute(f"DELETE FROM logs WHERE age > {days_old}")
```

### Step 3: Handle Exceptions

```python
def safe_execute():
    try:
        return client.execute_governed(
            action=lambda: risky_operation(),
            action_type="system_modify",
            description="Modify system configuration"
        )

    except GovernanceBlockedError as e:
        # Policy permanently blocks this action
        logger.warning(
            "Action blocked by policy",
            policy=e.policy_name,
            reason=e.blocking_reason,
            risk_score=e.risk_score,
            action_id=e.action_id
        )
        return {"error": "blocked", "reason": e.blocking_reason}

    except ActionRejectedError as e:
        # Human approver rejected
        logger.info(
            "Action rejected",
            rejected_by=e.rejected_by,
            reason=e.rejection_reason
        )
        return {"error": "rejected", "reason": e.rejection_reason}

    except ApprovalTimeoutError as e:
        # No approval in time
        logger.warning(
            "Approval timeout",
            timeout=e.timeout_seconds,
            pending=e.pending_approvers
        )
        return {"error": "timeout", "retry": True}

    except GovernanceUnavailableError as e:
        # Service down - fail-closed
        logger.error(
            "Governance unavailable",
            endpoint=e.endpoint,
            fail_mode=e.fail_mode
        )
        return {"error": "service_unavailable", "retry_after": e.retry_after_seconds}
```

### Step 4: Add Risk Context

```python
# Provide additional context for risk assessment
result = client.execute_governed(
    action=lambda: bulk_delete_users(user_ids),
    action_type="database_delete",
    description="Bulk delete inactive users",
    tool_name="postgresql",
    target_system="production",
    target_resource="users",
    risk_context={
        "affected_rows": len(user_ids),
        "user_type": "inactive",
        "requested_by": "cleanup_job",
        "business_justification": "GDPR compliance",
        "scheduled_maintenance": True
    }
)
```

---

## MCP Server Integration

### Step 1: Create Server

```python
from owkai.mcp_enforced import EnforcedMCPServer

server = EnforcedMCPServer(
    api_key="owkai_admin_...",
    server_name="Enterprise Tools",
    enforcement_mode="mandatory",
    fail_closed=True
)
```

### Step 2: Register Tools

```python
# Low-risk read operation
@server.tool(
    name="list_users",
    description="List all users in the system",
    namespace="database",
    verb="read",
    risk_hint="low"
)
async def list_users(limit: int = 100):
    return await db.query(f"SELECT * FROM users LIMIT {limit}")

# High-risk delete operation
@server.tool(
    name="delete_user",
    description="Permanently delete a user account",
    namespace="database",
    verb="delete",
    risk_hint="high"
)
async def delete_user(user_id: int, reason: str):
    await db.execute(f"DELETE FROM users WHERE id = {user_id}")
    return {"deleted": user_id, "reason": reason}
```

### Step 3: Run Server

```python
import asyncio

if __name__ == "__main__":
    asyncio.run(server.run_stdio())
```

### Step 4: Configure Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-tools": {
      "command": "python",
      "args": ["/path/to/your_server.py"],
      "env": {
        "OWKAI_API_KEY": "owkai_admin_..."
      }
    }
  }
}
```

---

## boto3 AWS Integration

### Step 1: Enable Governance

```python
# IMPORTANT: Call BEFORE importing boto3
from owkai.enforcement import enable_mandatory_governance

enable_mandatory_governance(
    api_key="owkai_admin_...",
    fail_closed=True,
    risk_threshold=70,
    auto_approve_below=30
)
```

### Step 2: Use boto3 Normally

```python
import boto3

# All boto3 calls are now governed
s3 = boto3.client('s3')

# Low risk - auto-approved
buckets = s3.list_buckets()

# High risk - requires approval
s3.delete_bucket(Bucket='backup-data')  # Blocks until approved
```

### Step 3: Handle Exceptions

```python
from owkai.enforcement import GovernanceBlockedError

try:
    ec2 = boto3.client('ec2')
    ec2.terminate_instances(InstanceIds=['i-1234567890abcdef0'])
except GovernanceBlockedError as e:
    print(f"Cannot terminate instance: {e.blocking_reason}")
```

---

## FastAPI Middleware Integration

### Step 1: Create Middleware

```python
from fastapi import FastAPI, Request, HTTPException
from owkai.enforcement import EnforcedClient, GovernanceBlockedError

app = FastAPI()
client = EnforcedClient(enforcement_mode="mandatory")

@app.middleware("http")
async def governance_middleware(request: Request, call_next):
    # Check if request is from an agent
    agent_id = request.headers.get("X-Agent-ID")

    if not agent_id:
        # Human user - no governance
        return await call_next(request)

    # Determine action type from request
    action_type = f"api_{request.method.lower()}"
    if "admin" in request.url.path:
        action_type += "_admin"

    try:
        # Submit to governance (actual execution is the route handler)
        response = await call_next(request)
        return response
    except GovernanceBlockedError as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "governance_blocked",
                "reason": e.blocking_reason,
                "policy": e.policy_name,
                "action_id": e.action_id
            }
        )
```

### Step 2: Protected Routes

```python
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, request: Request):
    agent_id = request.headers.get("X-Agent-ID")

    if agent_id:
        # Agent request - use governed execution
        return client.execute_governed(
            action=lambda: db.delete_user(user_id),
            action_type="api_delete_user",
            description=f"Delete user {user_id}",
            tool_name="user_api",
            target_resource=f"user:{user_id}"
        )
    else:
        # Human request - direct execution
        return db.delete_user(user_id)
```

---

## Testing Your Integration

### Unit Test Example

```python
import pytest
from unittest.mock import Mock, patch
from owkai.enforcement import (
    EnforcedClient,
    GovernanceBlockedError,
    ActionRejectedError
)

@pytest.fixture
def client():
    with patch('owkai.enforcement.httpx.Client') as mock:
        return EnforcedClient(
            api_key="test_key",
            enforcement_mode="mandatory"
        )

def test_allowed_action(client):
    # Mock governance allowing action
    client._client.post.return_value.json.return_value = {
        "action_id": 123,
        "risk_score": 25,
        "requires_approval": False
    }

    action_called = False
    def my_action():
        nonlocal action_called
        action_called = True
        return "success"

    result = client.execute_governed(
        action=my_action,
        action_type="test",
        description="Test action"
    )

    assert action_called
    assert result == "success"

def test_blocked_action(client):
    # Mock governance blocking action
    client._client.post.return_value.json.return_value = {
        "action_id": 123,
        "risk_score": 98,
        "requires_approval": False,
        "blocking_reason": "Test policy blocks this"
    }

    action_called = False
    def my_action():
        nonlocal action_called
        action_called = True

    with pytest.raises(GovernanceBlockedError) as exc:
        client.execute_governed(
            action=my_action,
            action_type="test",
            description="Test action"
        )

    assert not action_called  # Action should NOT have been called
    assert "Test policy" in str(exc.value)
```

### Integration Test Example

```python
import pytest
import os

@pytest.mark.integration
def test_real_governance():
    """Test against real OW-AI API (requires API key)."""
    api_key = os.environ.get("OWKAI_API_KEY")
    if not api_key:
        pytest.skip("OWKAI_API_KEY not set")

    client = EnforcedClient(
        api_key=api_key,
        enforcement_mode="mandatory"
    )

    # Low-risk action should auto-approve
    result = client.execute_governed(
        action=lambda: "read_result",
        action_type="database_read",
        description="Test read operation",
        tool_name="test"
    )
    assert result == "read_result"

    # High-risk action should require approval or block
    with pytest.raises((GovernanceBlockedError, ApprovalTimeoutError)):
        client.execute_governed(
            action=lambda: "delete_result",
            action_type="database_delete",
            description="Test delete operation",
            tool_name="test",
            target_system="production",
            risk_context={"test_mode": True}
        )
```

### MCP Server Test

```python
import asyncio
import json

async def test_mcp_server():
    from your_server import server

    # Test initialization
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize"
    })
    assert response["result"]["enforcement"]["mode"] == "mandatory"

    # Test tools list
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })
    assert len(response["result"]["tools"]) > 0

    # Test governed tool execution
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_users",
            "arguments": {"limit": 10}
        }
    })

    # Check either success or governance error
    if "result" in response:
        assert "governance" in response["result"]
    else:
        assert response["error"]["code"] in [-32000, -32001, -32002, -32003]

asyncio.run(test_mcp_server())
```

---

## Production Checklist

### Security Requirements

| Requirement | Check | Notes |
|-------------|-------|-------|
| API key in secure storage | ☐ | Use secrets manager, not env vars in code |
| HTTPS only | ☐ | All API communication over TLS |
| Fail-closed enabled | ☐ | `fail_closed=True` for mandatory mode |
| Network egress allowed | ☐ | Allow HTTPS to pilot.owkai.app |
| Audit logging enabled | ☐ | `log_all_decisions=True` |

### Configuration Checklist

```python
# Production configuration
client = EnforcedClient(
    api_key=secrets_manager.get("OWKAI_API_KEY"),  # ✓ Secure storage
    base_url="https://pilot.owkai.app",            # ✓ HTTPS
    enforcement_mode="mandatory",                   # ✓ Mandatory mode
    fail_closed=True,                              # ✓ Fail-closed
    approval_timeout=300,                          # ✓ Reasonable timeout
)
```

### Monitoring Checklist

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| Governance API latency | > 5s | Check network, API status |
| Block rate | > 50% | Review policies |
| Timeout rate | > 10% | Increase timeout or add approvers |
| Error rate | > 1% | Check API key, network |

### Logging Requirements

```python
import logging

# Configure structured logging
logging.basicConfig(
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
    level=logging.INFO
)

# The SDK logs all governance decisions
# You should also log in your application:
logger = logging.getLogger("myapp")

try:
    result = client.execute_governed(...)
    logger.info("Action executed", extra={
        "action_type": "database_write",
        "result": "success"
    })
except GovernanceBlockedError as e:
    logger.warning("Action blocked", extra={
        "action_id": e.action_id,
        "policy": e.policy_name,
        "risk_score": e.risk_score
    })
```

---

## Troubleshooting

### Common Issues

#### Issue: "GovernanceUnavailableError: Service unreachable"

**Cause:** Cannot connect to OW-AI API

**Solutions:**
1. Check network connectivity: `curl https://pilot.owkai.app/health`
2. Verify firewall allows HTTPS egress
3. Check API key is valid
4. Check for service outages at https://status.owkai.app

#### Issue: "ValueError: Mandatory enforcement requires fail_closed=True"

**Cause:** Trying to use mandatory mode without fail-closed

**Solution:**
```python
# Correct configuration
client = EnforcedClient(
    enforcement_mode="mandatory",
    fail_closed=True  # Required
)
```

#### Issue: All actions are being blocked

**Causes:**
1. Policy too restrictive
2. Risk thresholds too low
3. No approvers configured

**Solutions:**
1. Review policies in OW-AI dashboard
2. Adjust thresholds:
   ```python
   client = EnforcedClient(
       auto_approve_below=30,      # Increase if too restrictive
       require_approval_above=70   # Adjust as needed
   )
   ```
3. Configure approvers in organization settings

#### Issue: ApprovalTimeoutError happening frequently

**Causes:**
1. Approvers not available
2. Timeout too short
3. No notification configured

**Solutions:**
1. Configure on-call schedule for approvers
2. Increase timeout:
   ```python
   client = EnforcedClient(approval_timeout=600)  # 10 minutes
   ```
3. Set up Slack/email notifications in OW-AI dashboard

#### Issue: MCP Server not receiving requests

**Cause:** Claude Desktop configuration issue

**Solutions:**
1. Verify config file syntax:
   ```bash
   python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
2. Check server can start:
   ```bash
   python your_server.py
   # Type: {"jsonrpc":"2.0","id":1,"method":"initialize"}
   ```
3. Check Claude Desktop logs

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("owkai").setLevel(logging.DEBUG)

# Or via environment
export OWKAI_LOG_LEVEL=DEBUG
```

### Support Resources

| Resource | URL |
|----------|-----|
| Documentation | https://docs.owkai.app |
| API Status | https://status.owkai.app |
| Support | support@owkai.com |
| Enterprise Support | Contact your account manager |

---

## Related Documents

- [01_ARCHITECTURE_OVERVIEW.md](./01_ARCHITECTURE_OVERVIEW.md) - Architecture overview
- [02_ERROR_RESPONSES.md](./02_ERROR_RESPONSES.md) - Error response specification
- [03_SDK_ENFORCEMENT.md](./03_SDK_ENFORCEMENT.md) - SDK enforcement details
- [04_MCP_ENFORCEMENT.md](./04_MCP_ENFORCEMENT.md) - MCP server enforcement details

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | OW-AI Engineering | Initial release |
