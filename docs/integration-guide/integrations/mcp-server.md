---
title: MCP Server Integration
sidebar_position: 1
---

# MCP Server Integration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-INT-006 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Build Model Context Protocol (MCP) servers with enterprise governance using OW-kai's authorization center. This integration ensures every tool invocation is evaluated against your policies.

## Status

**Integration Status**: Example Available
**Source Code**: `ow-ai-backend/integration-examples/03_mcp_server.py`, `08_mcp_server_v2.py`
**Backend API**: `ow-ai-backend/routes/mcp_governance_routes.py`

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  MCP Client  │────►│  Your MCP Server │────►│  OW-kai API  │
│  (Claude,    │     │  (Governance     │     │  (Policy     │
│   etc.)      │◄────│   Gateway)       │◄────│   Engine)    │
└──────────────┘     └──────────────────┘     └──────────────┘
```

## Prerequisites

```bash
pip install httpx asyncio
```

## Complete Example

From `integration-examples/03_mcp_server.py`:

### 1. Governance Client

```python
import os
import httpx
import asyncio
from typing import Dict, Any

class OWAIGovernanceClient:
    """Client for OW-kai MCP governance endpoints"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

    async def evaluate_action(
        self,
        server_id: str,
        namespace: str,
        verb: str,
        resource: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, Any] = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Submit MCP action to OW-kai for governance evaluation.

        Returns:
            {
                "decision": "ALLOW" | "DENY" | "REQUIRE_APPROVAL",
                "action_id": 123,
                "risk_score": 75,
                "risk_level": "HIGH",
                "reason": "...",
                "estimated_approval_time": 15
            }
        """
        payload = {
            "server_id": server_id,
            "namespace": namespace,
            "verb": verb,
            "resource": resource,
            "parameters": parameters,
            "user_context": user_context or {},
            "session_context": {
                "session_id": session_id or "mcp-session-default"
            }
        }

        response = await self.client.post(
            f"{self.base_url}/mcp/governance/evaluate",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def wait_for_approval(
        self,
        action_id: int,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Poll for action approval status.

        Returns:
            {
                "approved": True | False,
                "reviewed_by": "approver@company.com",
                "comments": "...",
                "timestamp": "..."
            }
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time

            if elapsed >= timeout:
                return {"approved": False, "reason": "Approval timeout"}

            response = await self.client.get(
                f"{self.base_url}/api/v1/actions/{action_id}/status"
            )
            response.raise_for_status()
            status = response.json()

            if status.get("status") == "approved":
                return {
                    "approved": True,
                    "reviewed_by": status.get("reviewed_by"),
                    "comments": status.get("comments")
                }
            elif status.get("status") == "rejected":
                return {
                    "approved": False,
                    "reason": status.get("comments", "Action rejected")
                }

            await asyncio.sleep(poll_interval)

# Initialize client
governance_client = OWAIGovernanceClient(
    api_key=os.getenv("OWKAI_API_KEY"),
    base_url=os.getenv("OWKAI_BASE_URL", "https://pilot.owkai.app")
)
```

### 2. MCP Tool Definitions

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    namespace: str
    verb: str
    risk_level: str

# Define available tools
MCP_TOOLS: List[MCPTool] = [
    MCPTool(
        name="query_database",
        description="Execute SQL queries on the database",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query"},
                "database": {
                    "type": "string",
                    "enum": ["production", "staging", "development"]
                }
            },
            "required": ["query", "database"]
        },
        namespace="database",
        verb="execute",
        risk_level="varies"
    ),
    MCPTool(
        name="read_file",
        description="Read contents of a file",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"]
        },
        namespace="filesystem",
        verb="read",
        risk_level="low"
    ),
    MCPTool(
        name="write_file",
        description="Write content to a file",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        },
        namespace="filesystem",
        verb="write",
        risk_level="medium"
    ),
    MCPTool(
        name="run_command",
        description="Execute shell commands (use with caution)",
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "working_directory": {"type": "string"}
            },
            "required": ["command"]
        },
        namespace="system",
        verb="execute",
        risk_level="high"
    )
]
```

### 3. Governed Tool Execution

```python
async def execute_governed_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: str = None
) -> Dict[str, Any]:
    """
    Execute MCP tool with OW-kai governance.

    Flow:
    1. Find tool definition
    2. Submit to OW-kai for evaluation
    3. Handle decision (ALLOW, DENY, REQUIRE_APPROVAL)
    4. Execute if approved
    5. Return result
    """
    # Find tool definition
    tool = next((t for t in MCP_TOOLS if t.name == tool_name), None)
    if not tool:
        return {
            "error": f"Unknown tool: {tool_name}",
            "available_tools": [t.name for t in MCP_TOOLS]
        }

    # Determine verb based on arguments
    verb = tool.verb
    if tool_name == "query_database":
        query = arguments.get("query", "").upper().strip()
        if query.startswith("SELECT"):
            verb = "read"
        elif query.startswith(("INSERT", "UPDATE")):
            verb = "write"
        elif query.startswith("DELETE"):
            verb = "delete"

    # Build resource identifier
    if tool_name == "query_database":
        resource = f"database://{arguments.get('database', 'unknown')}"
    elif tool_name in ("read_file", "write_file"):
        resource = f"file://{arguments.get('path', 'unknown')}"
    elif tool_name == "run_command":
        resource = f"command://{arguments.get('command', 'unknown')[:50]}"
    else:
        resource = f"tool://{tool_name}"

    # Submit to OW-kai for governance
    print(f"🔒 [Governance] Evaluating {tool_name}: {resource}")

    evaluation = await governance_client.evaluate_action(
        server_id="mcp-enterprise-tools",
        namespace=tool.namespace,
        verb=verb,
        resource=resource,
        parameters=arguments,
        session_id=session_id
    )

    decision = evaluation.get("decision", "DENY")
    action_id = evaluation.get("action_id")
    risk_score = evaluation.get("risk_score", 0)

    print(f"📊 [Governance] Decision: {decision}, Risk: {risk_score}")

    # Handle decision
    if decision == "DENY":
        return {
            "governance": {
                "status": "blocked",
                "reason": evaluation.get("reason", "Action denied by policy"),
                "risk_score": risk_score,
                "action_id": action_id
            },
            "error": "Action blocked by OW-kai governance policy"
        }

    elif decision == "REQUIRE_APPROVAL":
        print(f"⏳ [Governance] Waiting for approval (action_id: {action_id})")

        approval = await governance_client.wait_for_approval(
            action_id,
            timeout=300
        )

        if not approval.get("approved"):
            return {
                "governance": {
                    "status": "rejected",
                    "reason": approval.get("reason", "Action rejected"),
                    "reviewed_by": approval.get("reviewed_by"),
                    "action_id": action_id
                },
                "error": "Action rejected by approver"
            }

        print(f"✅ [Governance] Approved by: {approval.get('reviewed_by')}")

    else:  # ALLOW
        print(f"✅ [Governance] Auto-approved (low risk)")

    # Execute the actual tool
    result = await _execute_tool(tool_name, arguments)

    return {
        "governance": {
            "status": "approved",
            "risk_score": risk_score,
            "action_id": action_id,
            "decision": decision
        },
        "result": result
    }


async def _execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Execute the actual tool logic (simulated for safety)"""
    if tool_name == "query_database":
        return {
            "status": "success",
            "database": arguments.get("database"),
            "query": arguments.get("query"),
            "rows_affected": 0,
            "message": "Query executed (simulated)"
        }
    elif tool_name == "read_file":
        return {
            "status": "success",
            "path": arguments.get("path"),
            "content": f"[Simulated content]",
            "size": 1024
        }
    elif tool_name == "write_file":
        return {
            "status": "success",
            "path": arguments.get("path"),
            "bytes_written": len(arguments.get("content", "")),
            "message": "File written (simulated)"
        }
    elif tool_name == "run_command":
        return {
            "status": "success",
            "command": arguments.get("command"),
            "exit_code": 0,
            "stdout": "[Simulated output]",
            "stderr": ""
        }
    return {"error": f"Unknown tool: {tool_name}"}
```

### 4. MCP Protocol Handlers

```python
async def handle_list_tools() -> Dict[str, Any]:
    """Handle tools/list MCP request"""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": f"{tool.description} [Risk: {tool.risk_level}]",
                "inputSchema": tool.input_schema
            }
            for tool in MCP_TOOLS
        ]
    }


async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call MCP request with governance"""
    return await execute_governed_tool(name, arguments)


async def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main MCP request handler.

    Supports:
    - initialize
    - tools/list
    - tools/call
    """
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-11-05",
                "serverInfo": {
                    "name": "Enterprise Tools Server",
                    "version": "1.0.0"
                },
                "capabilities": {"tools": {}}
            }
        elif method == "tools/list":
            result = await handle_list_tools()
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = await handle_call_tool(tool_name, arguments)
        else:
            result = {"error": f"Unknown method: {method}"}

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(e)}
        }
```

### 5. STDIO MCP Server

```python
import sys
import json

async def run_stdio_server():
    """
    Run MCP server over stdio (for Claude Desktop integration).

    To use with Claude Desktop, add to claude_desktop_config.json:
    {
        "mcpServers": {
            "enterprise-tools": {
                "command": "python",
                "args": ["/path/to/03_mcp_server.py"]
            }
        }
    }
    """
    print(f"🚀 Starting MCP Server with OW-kai Governance", file=sys.stderr)

    while True:
        try:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )

            if not line:
                break

            request = json.loads(line.strip())

            # Handle request with governance
            response = await handle_mcp_request(request)

            # Write response to stdout
            print(json.dumps(response), flush=True)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(run_stdio_server())
```

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-tools": {
      "command": "python",
      "args": ["/path/to/your/mcp_server.py"],
      "env": {
        "OWKAI_API_KEY": "owkai_admin_your_key_here",
        "OWKAI_BASE_URL": "https://pilot.owkai.app"
      }
    }
  }
}
```

## Testing the MCP Server

From `integration-examples/03_mcp_server.py`, run with `--test` flag:

```python
async def test_mcp_server():
    """Test MCP server functionality"""

    # Test 1: List tools
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    response = await handle_mcp_request(request)
    print(f"Tools: {json.dumps(response['result'], indent=2)}")

    # Test 2: Low-risk query (SELECT)
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "SELECT * FROM users WHERE active = true",
                "database": "staging"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

    # Test 3: High-risk query (DELETE)
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "DELETE FROM users WHERE last_login < '2025-01-01'",
                "database": "production"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

# Run tests
if __name__ == "__main__":
    if "--test" in sys.argv:
        asyncio.run(test_mcp_server())
    else:
        asyncio.run(run_stdio_server())
```

```bash
python 03_mcp_server.py --test
```

## SDK v2.0 Integration

From `integration-examples/08_mcp_server_v2.py` (conceptual - SDK decorators):

```python
from owkai_sdk import AscendClient
from owkai_sdk.mcp import mcp_governance, high_risk_action

# Initialize client
ascend = AscendClient(
    api_key=os.getenv("ASCEND_API_KEY"),
    agent_id="mcp-server-001"
)

@mcp_governance(
    ascend,
    action_type="database.query",
    resource="analytics_db"
)
async def query_analytics(sql: str) -> dict:
    """Query with automatic governance"""
    return await execute_query(sql)

@high_risk_action(
    ascend,
    action_type="database.delete",
    resource="production_db"
)
async def delete_records(table: str, where_clause: str) -> dict:
    """Delete with required approval"""
    return await execute_delete(table, where_clause)
```

Note: The `owkai_sdk` decorators are conceptual - use the full governance client pattern from `03_mcp_server.py` for production.

## Risk Levels by Operation

| Operation | Namespace | Verb | Risk Level | Approval Required |
|-----------|-----------|------|------------|-------------------|
| SELECT query | database | read | LOW (15-30) | No |
| INSERT/UPDATE | database | write | MEDIUM (40-60) | Conditional |
| DELETE query | database | delete | HIGH (70-85) | Yes |
| Read file | filesystem | read | LOW (20) | No |
| Write file | filesystem | write | MEDIUM (50) | Conditional |
| Shell command | system | execute | HIGH (80-95) | Yes |

## Security Best Practices

### 1. Environment Variables

```bash
# Never hardcode API keys
export OWKAI_API_KEY="owkai_admin_your_key_here"
export OWKAI_BASE_URL="https://pilot.owkai.app"
```

### 2. Tool Allowlisting

```python
ALLOWED_TOOLS = {"query_database", "read_file"}
BLOCKED_TOOLS = {"execute_command", "delete_all"}

if tool_name in BLOCKED_TOOLS:
    return {"error": "Tool blocked by server policy"}
```

### 3. Localhost Only

```python
# Only listen on localhost for security
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=3000)
```

## Troubleshooting

### Connection Issues

```bash
# Test OW-kai connectivity
curl -H "Authorization: Bearer $OWKAI_API_KEY" \
  https://pilot.owkai.app/health
```

### Tool Not Responding

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Approval Timeout

```python
# Increase timeout for slow approvals
approval = await governance_client.wait_for_approval(
    action_id,
    timeout=600  # 10 minutes
)
```

## Next Steps

- [LangChain Integration](/integrations/langchain) - LangChain with governance
- [Custom Agents](/integrations/custom-agents) - Python SDK usage
- [AWS Lambda Example](https://github.com/yourusername/integration-examples) - Serverless governance
