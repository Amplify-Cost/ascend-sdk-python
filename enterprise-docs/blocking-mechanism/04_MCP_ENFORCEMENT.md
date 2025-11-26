# OW-AI Enterprise MCP Server Enforcement Module

**Document Version:** 1.0
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-01-15
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [MCP Protocol Compliance](#mcp-protocol-compliance)
4. [EnforcedMCPServer Class](#enforcedmcpserver-class)
5. [Tool Registration](#tool-registration)
6. [Error Response Format](#error-response-format)
7. [Claude Desktop Integration](#claude-desktop-integration)
8. [Implementation Examples](#implementation-examples)

---

## Overview

The OW-AI MCP Enforcement Module (`owkai.mcp_enforced`) provides **banking-level mandatory enforcement** for Model Context Protocol (MCP) servers. This module ensures that MCP tools **CANNOT execute** without explicit governance approval.

### Key Principles

| Principle | Implementation |
|-----------|----------------|
| **Fail-Closed** | Network errors block tool execution |
| **Non-Bypassable** | Enforcement at protocol handler level |
| **MCP Compliant** | Standard JSON-RPC 2.0 error responses |
| **Claude Compatible** | Works with Claude Desktop out of the box |

### Module Location

```
owkai-sdk/
└── owkai/
    └── mcp_enforced.py     # This module
```

### Import Statement

```python
from owkai.mcp_enforced import (
    # Server
    EnforcedMCPServer,

    # Response Types
    MCPGovernanceResponse,
    MCPToolDefinition,

    # Error Response Creators
    create_governance_blocked_error,
    create_action_rejected_error,
    create_approval_timeout_error,
    create_governance_unavailable_error,

    # Constants
    JSONRPC_GOVERNANCE_BLOCKED,
    JSONRPC_ACTION_REJECTED,
    JSONRPC_APPROVAL_TIMEOUT,
    JSONRPC_GOVERNANCE_UNAVAILABLE,
)
```

---

## Architecture

### Enforcement Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ENFORCED MCP SERVER ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐                                                   │
│   │  Claude Desktop /   │                                                   │
│   │  LLM Client         │                                                   │
│   └──────────┬──────────┘                                                   │
│              │                                                              │
│              │ MCP Protocol (JSON-RPC 2.0 over stdio)                       │
│              │                                                              │
│              │ {"jsonrpc":"2.0","method":"tools/call",                      │
│              │  "params":{"name":"query_database",                          │
│              │            "arguments":{"query":"DELETE FROM users"}}}       │
│              │                                                              │
│              ▼                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    EnforcedMCPServer                                │   │
│   │                                                                     │   │
│   │   handle_request()                                                  │   │
│   │        │                                                            │   │
│   │        ▼                                                            │   │
│   │   tools/call ────► _execute_governed_tool()                         │   │
│   │                           │                                         │   │
│   │                           │                                         │   │
│   │   ┌───────────────────────▼───────────────────────────────────┐     │   │
│   │   │           GOVERNANCE ENFORCEMENT                          │     │   │
│   │   │                                                           │     │   │
│   │   │  1. _evaluate_governance()                                │     │   │
│   │   │     │                                                     │     │   │
│   │   │     └─► POST /api/authorization/agent-action              │     │   │
│   │   │         │                                                 │     │   │
│   │   │         ▼                                                 │     │   │
│   │   │     Response: decision, risk_score, action_id             │     │   │
│   │   │                                                           │     │   │
│   │   │  2. Handle Decision                                       │     │   │
│   │   │     │                                                     │     │   │
│   │   │     ├── DENY ────────► GovernanceBlockedError             │     │   │
│   │   │     │                         │                           │     │   │
│   │   │     │                         ▼                           │     │   │
│   │   │     │                  MCP Error Response                 │     │   │
│   │   │     │                                                     │     │   │
│   │   │     ├── REQUIRE_APPROVAL ──► _wait_for_approval()         │     │   │
│   │   │     │         │                                           │     │   │
│   │   │     │         ├── Approved ──► Execute Tool               │     │   │
│   │   │     │         ├── Rejected ──► ActionRejectedError        │     │   │
│   │   │     │         └── Timeout ───► ApprovalTimeoutError       │     │   │
│   │   │     │                                                     │     │   │
│   │   │     └── ALLOW ──────────────► Execute Tool                │     │   │
│   │   │                                   │                       │     │   │
│   │   │                                   ▼                       │     │   │
│   │   │                           tool.handler(**arguments)       │     │   │
│   │   │                                   │                       │     │   │
│   │   │                                   ▼                       │     │   │
│   │   │                           MCP Success Response            │     │   │
│   │   │                                                           │     │   │
│   │   └───────────────────────────────────────────────────────────┘     │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Security Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| Tool cannot bypass governance | Handler only called after approval |
| All tools are governed | `@server.tool()` decorator enforces |
| Errors block execution | Fail-closed on network/timeout |
| Complete audit trail | All decisions logged with context |

---

## MCP Protocol Compliance

### Protocol Version

```python
MCP_PROTOCOL_VERSION = "2024-11-05"
```

### JSON-RPC 2.0 Compliance

All responses follow the JSON-RPC 2.0 specification.

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Query executed successfully"
      }
    ],
    "governance": {
      "status": "approved",
      "action_id": 12345,
      "risk_score": 45,
      "approved_by": "security@company.com"
    }
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Tool execution blocked by OW-AI governance",
    "data": {
      "governance_error": { ... },
      "user_message": "..."
    }
  }
}
```

### Governance Error Codes

| JSON-RPC Code | Error Type | Description |
|---------------|------------|-------------|
| `-32000` | GovernanceBlockedError | Policy blocks action |
| `-32001` | ActionRejectedError | Approver rejected |
| `-32002` | ApprovalTimeoutError | Approval timeout |
| `-32003` | GovernanceUnavailableError | Service unavailable |

```python
# Constants defined in module
JSONRPC_GOVERNANCE_BLOCKED = -32000
JSONRPC_ACTION_REJECTED = -32001
JSONRPC_APPROVAL_TIMEOUT = -32002
JSONRPC_GOVERNANCE_UNAVAILABLE = -32003
```

---

## EnforcedMCPServer Class

### Class Overview

```python
class EnforcedMCPServer:
    """
    MCP Server with Banking-Level Mandatory Enforcement.

    Features:
    - True blocking (not advisory)
    - Fail-closed on errors
    - Complete audit trail
    - MCP protocol compliant
    - Claude Desktop compatible
    """
```

### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    *,
    base_url: str = "https://pilot.owkai.app",
    server_id: Optional[str] = None,
    server_name: str = "OW-AI Enforced MCP Server",
    enforcement_mode: str = "mandatory",
    fail_closed: bool = True,
    approval_timeout: int = 300,
    auto_approve_below: int = 30,
    require_approval_above: int = 70,
):
    """
    Initialize enforced MCP server.

    Args:
        api_key: OW-AI API key (or OWKAI_API_KEY env var)
        base_url: OW-AI API base URL
        server_id: Unique server identifier (auto-generated if not provided)
        server_name: Human-readable server name
        enforcement_mode: Level of enforcement
            - "mandatory" (recommended)
            - "cooperative"
            - "advisory"
        fail_closed: Block on errors (REQUIRED for mandatory mode)
        approval_timeout: Max seconds to wait for approval (default: 300)
        auto_approve_below: Risk score for auto-approval (default: 30)
        require_approval_above: Risk score requiring approval (default: 70)

    Raises:
        ValueError: If mandatory mode without fail_closed=True
    """
```

### Running the Server

```python
async def run_stdio(self):
    """
    Run MCP server over stdio.

    Compatible with Claude Desktop configuration.
    Reads JSON-RPC requests from stdin, writes responses to stdout.
    """
```

### Request Handler

```python
async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP JSON-RPC request.

    Supported methods:
    - initialize: Server initialization
    - tools/list: List available tools
    - tools/call: Execute a tool (with governance)

    Args:
        request: JSON-RPC request object

    Returns:
        JSON-RPC response object
    """
```

---

## Tool Registration

### @server.tool() Decorator

```python
def tool(
    self,
    name: str,
    description: str,
    input_schema: Optional[Dict[str, Any]] = None,
    *,
    namespace: str = "default",
    verb: str = "execute",
    risk_hint: str = "medium",
):
    """
    Decorator to register a governed tool.

    The decorated function will ONLY execute if governance approves.

    Args:
        name: Tool name (used in MCP protocol)
        description: Human-readable description (shown to Claude)
        input_schema: JSON Schema for tool inputs (auto-inferred if not provided)
        namespace: Governance namespace (database, filesystem, api, etc.)
        verb: Governance verb (read, write, execute, delete)
        risk_hint: Initial risk assessment hint (low, medium, high, critical)

    Returns:
        Decorator function
    """
```

### Tool Definition Structure

```python
@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool with governance metadata."""
    name: str                  # Tool identifier
    description: str           # Human-readable description
    input_schema: Dict         # JSON Schema for inputs
    handler: Callable          # Actual function to execute
    namespace: str = "default" # Governance namespace
    default_verb: str = "execute"  # Default action verb
    risk_hint: str = "medium"  # Risk assessment hint
```

### Registration Examples

```python
server = EnforcedMCPServer(api_key="owkai_admin_...")

# Low-risk read operation
@server.tool(
    name="list_tables",
    description="List available database tables",
    namespace="database",
    verb="read",
    risk_hint="low"
)
async def list_tables(database: str = "main"):
    return await db.execute(f"SHOW TABLES IN {database}")

# Medium-risk write operation
@server.tool(
    name="insert_record",
    description="Insert a new record into a table",
    input_schema={
        "type": "object",
        "properties": {
            "table": {"type": "string", "description": "Table name"},
            "data": {"type": "object", "description": "Record data"}
        },
        "required": ["table", "data"]
    },
    namespace="database",
    verb="write",
    risk_hint="medium"
)
async def insert_record(table: str, data: dict):
    return await db.insert(table, data)

# High-risk delete operation
@server.tool(
    name="delete_records",
    description="Delete records from a database table",
    namespace="database",
    verb="delete",
    risk_hint="high"
)
async def delete_records(table: str, condition: str):
    return await db.execute(f"DELETE FROM {table} WHERE {condition}")

# Critical system operation
@server.tool(
    name="run_command",
    description="Execute a shell command on the server",
    namespace="system",
    verb="execute",
    risk_hint="critical"
)
async def run_command(command: str):
    import subprocess
    return subprocess.check_output(command, shell=True).decode()
```

### Auto-Inferred Schema

If `input_schema` is not provided, the schema is inferred from the function signature:

```python
@server.tool(
    name="search_logs",
    description="Search application logs"
)
async def search_logs(
    query: str,           # Required string
    limit: int = 100,     # Optional integer with default
    include_debug: bool = False  # Optional boolean
):
    pass

# Auto-generated schema:
# {
#   "type": "object",
#   "properties": {
#     "query": {"type": "string"},
#     "limit": {"type": "integer"},
#     "include_debug": {"type": "boolean"}
#   },
#   "required": ["query"]
# }
```

---

## Error Response Format

### Governance Blocked Error

```python
def create_governance_blocked_error(
    request_id: Any,
    error: GovernanceBlockedError,
) -> Dict[str, Any]:
    """Create MCP-compliant error response for blocked action."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32000,  # JSONRPC_GOVERNANCE_BLOCKED
            "message": "Tool execution blocked by OW-AI governance",
            "data": {
                "governance_error": {
                    "type": "GovernanceBlockedError",
                    "code": "GOVN_BLOCKED_001",
                    "message": error.message,
                    "action_id": error.action_id,
                    "risk_score": error.risk_score,
                    "risk_level": error.risk_level,
                    "blocking_reason": error.blocking_reason,
                    "policy_id": error.policy_id,
                    "policy_name": error.policy_name,
                    "nist_control": error.nist_control,
                    "mitre_technique": error.mitre_technique,
                    "remediation": error.remediation,
                },
                "user_message": _format_user_message_blocked(error),
            }
        }
    }
```

### User-Facing Message Format

When Claude receives a blocked error, the user sees a formatted message:

```
❌ **Action Blocked by Governance**

**Reason:** Production database DELETE operations are prohibited by policy

**Risk Score:** 95/100 (CRITICAL)
**Policy:** no-production-deletes
**NIST Control:** AC-6 (Least Privilege)

**What you can do:**
• Contact your security administrator for a policy exception
• Use a less privileged operation
• Verify you have the necessary permissions
• Use staging environment for testing
```

### Action Rejected Error

```python
def create_action_rejected_error(
    request_id: Any,
    error: ActionRejectedError,
) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32001,  # JSONRPC_ACTION_REJECTED
            "message": "Tool execution rejected by approver",
            "data": {
                "governance_error": {
                    "type": "ActionRejectedError",
                    "code": "GOVN_REJECTED_001",
                    "message": error.message,
                    "action_id": error.action_id,
                    "rejected_by": error.rejected_by,
                    "rejection_reason": error.rejection_reason,
                    "can_resubmit": error.can_resubmit,
                    "resubmit_requirements": error.resubmit_requirements,
                },
                "user_message": _format_user_message_rejected(error),
            }
        }
    }
```

### Approval Timeout Error

```python
def create_approval_timeout_error(
    request_id: Any,
    error: ApprovalTimeoutError,
) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32002,  # JSONRPC_APPROVAL_TIMEOUT
            "message": "Tool execution blocked - approval timeout",
            "data": {
                "governance_error": {
                    "type": "ApprovalTimeoutError",
                    "code": "GOVN_TIMEOUT_001",
                    "message": error.message,
                    "action_id": error.action_id,
                    "timeout_seconds": error.timeout_seconds,
                    "pending_approvers": error.pending_approvers,
                },
                "user_message": _format_user_message_timeout(error),
            }
        }
    }
```

### Governance Unavailable Error

```python
def create_governance_unavailable_error(
    request_id: Any,
    error: GovernanceUnavailableError,
) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32003,  # JSONRPC_GOVERNANCE_UNAVAILABLE
            "message": "Tool execution blocked - governance service unavailable",
            "data": {
                "governance_error": {
                    "type": "GovernanceUnavailableError",
                    "code": "GOVN_UNAVAILABLE_001",
                    "message": error.message,
                    "fail_mode": error.fail_mode,
                    "retry_after_seconds": error.retry_after_seconds,
                },
                "user_message": _format_user_message_unavailable(error),
            }
        }
    }
```

---

## Claude Desktop Integration

### Configuration File

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-database": {
      "command": "python",
      "args": ["/path/to/your_mcp_server.py"],
      "env": {
        "OWKAI_API_KEY": "owkai_admin_your_key_here",
        "OWKAI_BASE_URL": "https://pilot.owkai.app"
      }
    }
  }
}
```

### Server Implementation File

```python
#!/usr/bin/env python3
"""
Enterprise Database MCP Server with OW-AI Governance

This server provides governed database access to Claude.
All operations are subject to OW-AI policy enforcement.
"""

import asyncio
import os
from owkai.mcp_enforced import EnforcedMCPServer

# Initialize server with mandatory enforcement
server = EnforcedMCPServer(
    api_key=os.environ.get("OWKAI_API_KEY"),
    base_url=os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app"),
    server_name="Enterprise Database Tools",
    enforcement_mode="mandatory",
    fail_closed=True,
)

# Simulated database connection
class MockDatabase:
    async def execute(self, query: str):
        return f"Executed: {query}"

db = MockDatabase()

# Low-risk: Read operations
@server.tool(
    name="query_database",
    description="Execute a SELECT query on the database",
    namespace="database",
    verb="read",
    risk_hint="low"
)
async def query_database(query: str, database: str = "main"):
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries allowed")
    return await db.execute(query)

# Medium-risk: Write operations
@server.tool(
    name="insert_data",
    description="Insert data into a database table",
    namespace="database",
    verb="write",
    risk_hint="medium"
)
async def insert_data(table: str, data: dict):
    columns = ", ".join(data.keys())
    values = ", ".join(f"'{v}'" for v in data.values())
    query = f"INSERT INTO {table} ({columns}) VALUES ({values})"
    return await db.execute(query)

# High-risk: Update operations
@server.tool(
    name="update_data",
    description="Update existing records in the database",
    namespace="database",
    verb="write",
    risk_hint="high"
)
async def update_data(table: str, data: dict, condition: str):
    set_clause = ", ".join(f"{k}='{v}'" for k, v in data.items())
    query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
    return await db.execute(query)

# Critical-risk: Delete operations
@server.tool(
    name="delete_data",
    description="Delete records from the database",
    namespace="database",
    verb="delete",
    risk_hint="critical"
)
async def delete_data(table: str, condition: str):
    query = f"DELETE FROM {table} WHERE {condition}"
    return await db.execute(query)

# Run the server
if __name__ == "__main__":
    asyncio.run(server.run_stdio())
```

### User Experience in Claude Desktop

When Claude attempts to use a governed tool:

**Low-risk (auto-approved):**
```
User: Can you show me the users table?

Claude: I'll query the database for you.

[Tool: query_database]
Result: Users table returned with 150 records.
```

**High-risk (approval required):**
```
User: Can you delete all inactive users?

Claude: I'll attempt to delete the inactive users.

[Tool: delete_data]
[Waiting for approval from security team...]
[Approved by security@company.com]

Result: Deleted 45 inactive user records.
```

**Blocked by policy:**
```
User: Delete the entire production database

Claude: I attempted to execute the deletion, but OW-AI governance blocked the action:

❌ **Action Blocked by Governance**

**Reason:** Production database bulk DELETE operations are prohibited
by your organization's security policy.

**Risk Score:** 98/100 (CRITICAL)
**Policy:** no-production-bulk-delete

**What you can do:**
• Contact your security administrator for a policy exception
• Use the staging database for testing
• Perform deletions in smaller batches with approval

Would you like me to suggest an alternative approach?
```

---

## Implementation Examples

### Example 1: File System MCP Server

```python
from owkai.mcp_enforced import EnforcedMCPServer
import os

server = EnforcedMCPServer(
    server_name="File System Tools",
    enforcement_mode="mandatory"
)

@server.tool(
    name="read_file",
    description="Read contents of a file",
    namespace="filesystem",
    verb="read",
    risk_hint="low"
)
async def read_file(path: str):
    with open(path, 'r') as f:
        return f.read()

@server.tool(
    name="write_file",
    description="Write content to a file",
    namespace="filesystem",
    verb="write",
    risk_hint="medium"
)
async def write_file(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)
    return f"Written {len(content)} bytes to {path}"

@server.tool(
    name="delete_file",
    description="Delete a file from the filesystem",
    namespace="filesystem",
    verb="delete",
    risk_hint="high"
)
async def delete_file(path: str):
    os.remove(path)
    return f"Deleted {path}"

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio())
```

### Example 2: AWS Operations MCP Server

```python
from owkai.mcp_enforced import EnforcedMCPServer
import boto3

server = EnforcedMCPServer(
    server_name="AWS Operations",
    enforcement_mode="mandatory"
)

@server.tool(
    name="list_s3_buckets",
    description="List all S3 buckets",
    namespace="aws",
    verb="read",
    risk_hint="low"
)
async def list_s3_buckets():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    return [b['Name'] for b in response['Buckets']]

@server.tool(
    name="create_s3_bucket",
    description="Create a new S3 bucket",
    namespace="aws",
    verb="write",
    risk_hint="medium"
)
async def create_s3_bucket(bucket_name: str, region: str = "us-east-1"):
    s3 = boto3.client('s3')
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': region}
    )
    return f"Created bucket: {bucket_name}"

@server.tool(
    name="delete_s3_bucket",
    description="Delete an S3 bucket (must be empty)",
    namespace="aws",
    verb="delete",
    risk_hint="critical"
)
async def delete_s3_bucket(bucket_name: str):
    s3 = boto3.client('s3')
    s3.delete_bucket(Bucket=bucket_name)
    return f"Deleted bucket: {bucket_name}"

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio())
```

### Example 3: API Gateway MCP Server

```python
from owkai.mcp_enforced import EnforcedMCPServer
import httpx

server = EnforcedMCPServer(
    server_name="API Gateway",
    enforcement_mode="mandatory"
)

@server.tool(
    name="get_request",
    description="Make a GET request to an API endpoint",
    namespace="api",
    verb="read",
    risk_hint="low"
)
async def get_request(url: str, headers: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        return response.json()

@server.tool(
    name="post_request",
    description="Make a POST request to an API endpoint",
    namespace="api",
    verb="write",
    risk_hint="medium"
)
async def post_request(url: str, data: dict, headers: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.json()

@server.tool(
    name="delete_request",
    description="Make a DELETE request to an API endpoint",
    namespace="api",
    verb="delete",
    risk_hint="high"
)
async def delete_request(url: str, headers: dict = None):
    async with httpx.AsyncClient() as client:
        response = await client.delete(url, headers=headers)
        return {"status": response.status_code}

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run_stdio())
```

---

## Testing Your MCP Server

### Manual Testing

```bash
# Test with direct stdin/stdout
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python your_server.py

# Test tools/list
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python your_server.py

# Test tool execution
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"query_database","arguments":{"query":"SELECT * FROM users"}}}' | python your_server.py
```

### Automated Testing

```python
import asyncio
import json
from your_server import server

async def test_governance():
    # Test initialize
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize"
    })
    assert response["result"]["enforcement"]["mode"] == "mandatory"

    # Test tool execution
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {"query": "SELECT * FROM users"}
        }
    })

    # Check governance was applied
    if "result" in response:
        assert "governance" in response["result"]
        assert response["result"]["governance"]["status"] == "approved"
    elif "error" in response:
        assert response["error"]["code"] in [-32000, -32001, -32002, -32003]

asyncio.run(test_governance())
```

---

## Next Documents

- [05_INTEGRATION_GUIDE.md](./05_INTEGRATION_GUIDE.md) - Step-by-step integration guide

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | OW-AI Engineering | Initial release |
