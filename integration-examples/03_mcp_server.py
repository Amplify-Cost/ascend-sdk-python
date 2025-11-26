#!/usr/bin/env python3
"""
OW-AI Integration Example 3: MCP Server with Governance Gateway

USE CASE: Model Context Protocol (MCP) servers that need enterprise governance
          for tool execution by Claude and other LLM clients.

This example shows how to:
1. Create an MCP server with OW-AI governance
2. Intercept tool calls before execution
3. Route through approval workflow based on risk
4. Return governed responses to Claude clients

ARCHITECTURE:
    Claude Desktop / LLM Client
              │
              │ MCP Protocol (JSON-RPC)
              ▼
    ┌─────────────────────────────────┐
    │   MCP Server (This Example)     │
    │                                 │
    │   ┌─────────────────────────┐   │
    │   │ OW-AI Governance Layer  │   │
    │   │ - Intercept tool calls  │   │
    │   │ - Evaluate risk         │   │
    │   │ - Route for approval    │   │
    │   └─────────────────────────┘   │
    │              │                  │
    │              ▼                  │
    │   ┌─────────────────────────┐   │
    │   │ Actual Tool Execution   │   │
    │   │ - Database queries      │   │
    │   │ - File operations       │   │
    │   │ - API calls             │   │
    │   └─────────────────────────┘   │
    └─────────────────────────────────┘

MCP TOOLS PROVIDED:
    ┌──────────────────────────────────────────────────────────┐
    │ query_database  │ Execute SQL queries (governed)         │
    │ read_file       │ Read files from filesystem (governed)  │
    │ write_file      │ Write files to filesystem (governed)   │
    │ call_api        │ Make HTTP API calls (governed)         │
    │ run_command     │ Execute shell commands (governed)      │
    └──────────────────────────────────────────────────────────┘

Engineer: OW-AI Enterprise
"""

import os
import sys
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

# ============================================
# CONFIGURATION
# ============================================

OWAI_API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
OWAI_BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")
MCP_SERVER_ID = os.environ.get("MCP_SERVER_ID", "mcp-enterprise-tools")
MCP_SERVER_NAME = os.environ.get("MCP_SERVER_NAME", "Enterprise Tools Server")


# ============================================
# OW-AI GOVERNANCE CLIENT
# ============================================

class OWAIGovernanceClient:
    """
    Client for OW-AI MCP governance endpoints.

    Handles:
    - Action evaluation (risk assessment)
    - Approval polling
    - Audit logging
    """

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
        user_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit MCP action to OW-AI for governance evaluation.

        Args:
            server_id: MCP server identifier
            namespace: Action namespace (database, filesystem, api, etc.)
            verb: Action verb (read, write, execute, delete)
            resource: Target resource identifier
            parameters: Action parameters
            user_context: Optional user context (user_id, email, role)
            session_id: Optional session identifier

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

        logger.info(f"[OW-AI] Evaluating action: {namespace}.{verb} on {resource}")

        try:
            response = await self.client.post(
                f"{self.base_url}/mcp/governance/evaluate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"[OW-AI] Decision: {result.get('decision')}, "
                       f"Risk: {result.get('risk_score')}")

            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"[OW-AI] Evaluation failed: {e.response.text}")
            # Fail-safe: deny on error
            return {
                "decision": "DENY",
                "reason": f"Governance evaluation failed: {str(e)}",
                "risk_score": 100,
                "risk_level": "CRITICAL"
            }

    async def wait_for_approval(
        self,
        action_id: int,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Poll for action approval status.

        Args:
            action_id: Action ID from evaluation
            timeout: Max seconds to wait
            poll_interval: Seconds between polls

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
                return {
                    "approved": False,
                    "reason": "Approval timeout",
                    "timeout": True
                }

            try:
                response = await self.client.get(
                    f"{self.base_url}/api/agent-action/status/{action_id}"
                )
                response.raise_for_status()
                status = response.json()

                if status.get("status") == "approved":
                    return {
                        "approved": True,
                        "reviewed_by": status.get("reviewed_by"),
                        "comments": status.get("comments"),
                        "timestamp": status.get("reviewed_at")
                    }
                elif status.get("status") == "rejected":
                    return {
                        "approved": False,
                        "reviewed_by": status.get("reviewed_by"),
                        "reason": status.get("comments", "Action rejected"),
                        "timestamp": status.get("reviewed_at")
                    }

                # Still pending, wait and retry
                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(f"[OW-AI] Polling failed: {e}")
                await asyncio.sleep(poll_interval)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Initialize governance client
governance_client = OWAIGovernanceClient(OWAI_API_KEY, OWAI_BASE_URL)


# ============================================
# MCP TOOL DEFINITIONS
# ============================================

@dataclass
class MCPTool:
    """MCP tool definition."""
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
        description="Execute SQL queries on the database. Supports SELECT, INSERT, UPDATE, DELETE.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "database": {
                    "type": "string",
                    "description": "Target database (production, staging, development)",
                    "enum": ["production", "staging", "development"]
                }
            },
            "required": ["query", "database"]
        },
        namespace="database",
        verb="execute",
        risk_level="varies"  # Depends on query type
    ),
    MCPTool(
        name="read_file",
        description="Read contents of a file from the filesystem.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        },
        namespace="filesystem",
        verb="read",
        risk_level="low"
    ),
    MCPTool(
        name="write_file",
        description="Write content to a file on the filesystem.",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        },
        namespace="filesystem",
        verb="write",
        risk_level="medium"
    ),
    MCPTool(
        name="call_api",
        description="Make HTTP API calls to external services.",
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "API endpoint URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers"
                },
                "body": {
                    "type": "object",
                    "description": "Request body (for POST, PUT, PATCH)"
                }
            },
            "required": ["url", "method"]
        },
        namespace="api",
        verb="call",
        risk_level="medium"
    ),
    MCPTool(
        name="run_command",
        description="Execute shell commands on the system. Use with caution.",
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute"
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for command execution"
                }
            },
            "required": ["command"]
        },
        namespace="system",
        verb="execute",
        risk_level="high"
    )
]


# ============================================
# GOVERNED TOOL EXECUTION
# ============================================

async def execute_governed_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute an MCP tool with OW-AI governance.

    Flow:
    1. Find tool definition
    2. Submit to OW-AI for evaluation
    3. Handle decision (ALLOW, DENY, REQUIRE_APPROVAL)
    4. Execute if approved
    5. Return result

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        session_id: Optional session ID for tracking

    Returns:
        Tool execution result or governance rejection
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
        else:
            verb = "admin"

    # Build resource identifier
    resource = _build_resource_identifier(tool_name, arguments)

    # Submit to OW-AI for governance
    logger.info(f"🔒 [Governance] Evaluating {tool_name}: {resource}")

    evaluation = await governance_client.evaluate_action(
        server_id=MCP_SERVER_ID,
        namespace=tool.namespace,
        verb=verb,
        resource=resource,
        parameters=arguments,
        session_id=session_id
    )

    decision = evaluation.get("decision", "DENY")
    action_id = evaluation.get("action_id")
    risk_score = evaluation.get("risk_score", 0)

    logger.info(f"📊 [Governance] Decision: {decision}, Risk: {risk_score}")

    # Handle decision
    if decision == "DENY":
        return {
            "governance": {
                "status": "blocked",
                "reason": evaluation.get("reason", "Action denied by policy"),
                "risk_score": risk_score,
                "action_id": action_id
            },
            "error": "Action blocked by OW-AI governance policy"
        }

    elif decision == "REQUIRE_APPROVAL":
        logger.info(f"⏳ [Governance] Waiting for approval (action_id: {action_id})")

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
                    "risk_score": risk_score,
                    "action_id": action_id
                },
                "error": "Action rejected by approver"
            }

        logger.info(f"✅ [Governance] Approved by: {approval.get('reviewed_by')}")

    else:  # ALLOW
        logger.info(f"✅ [Governance] Auto-approved (low risk)")

    # Execute the actual tool
    try:
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

    except Exception as e:
        logger.error(f"❌ [Execution] Tool failed: {e}")
        return {
            "governance": {
                "status": "approved",
                "action_id": action_id
            },
            "error": f"Tool execution failed: {str(e)}"
        }


def _build_resource_identifier(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Build resource identifier for governance."""
    if tool_name == "query_database":
        db = arguments.get("database", "unknown")
        return f"database://{db}"
    elif tool_name in ("read_file", "write_file"):
        path = arguments.get("path", "unknown")
        return f"file://{path}"
    elif tool_name == "call_api":
        url = arguments.get("url", "unknown")
        return f"api://{url}"
    elif tool_name == "run_command":
        cmd = arguments.get("command", "unknown")[:50]
        return f"command://{cmd}"
    return f"tool://{tool_name}"


async def _execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute the actual tool logic.

    In production, this would connect to real databases, filesystems, etc.
    For this example, we simulate the operations.
    """
    if tool_name == "query_database":
        # Simulated database query
        query = arguments.get("query", "")
        database = arguments.get("database", "unknown")
        return {
            "status": "success",
            "database": database,
            "query": query,
            "rows_affected": 0,
            "message": f"Query executed on {database} (simulated)"
        }

    elif tool_name == "read_file":
        path = arguments.get("path", "")
        # In production: return actual file contents
        return {
            "status": "success",
            "path": path,
            "content": f"[Simulated content of {path}]",
            "size": 1024
        }

    elif tool_name == "write_file":
        path = arguments.get("path", "")
        content = arguments.get("content", "")
        # In production: actually write the file
        return {
            "status": "success",
            "path": path,
            "bytes_written": len(content),
            "message": f"File written to {path} (simulated)"
        }

    elif tool_name == "call_api":
        url = arguments.get("url", "")
        method = arguments.get("method", "GET")
        # In production: make actual HTTP request
        return {
            "status": "success",
            "url": url,
            "method": method,
            "response_code": 200,
            "body": {"message": "API response (simulated)"}
        }

    elif tool_name == "run_command":
        command = arguments.get("command", "")
        # In production: execute actual command (with extreme caution)
        return {
            "status": "success",
            "command": command,
            "exit_code": 0,
            "stdout": f"[Simulated output of: {command}]",
            "stderr": ""
        }

    return {"error": f"Unknown tool: {tool_name}"}


# ============================================
# MCP SERVER PROTOCOL HANDLERS
# ============================================

async def handle_list_tools() -> Dict[str, Any]:
    """Handle tools/list MCP request."""
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
    """Handle tools/call MCP request with governance."""
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
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": MCP_SERVER_NAME,
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {}
                }
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
        logger.error(f"MCP request failed: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# ============================================
# STDIO MCP SERVER
# ============================================

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
    logger.info(f"🚀 Starting MCP Server: {MCP_SERVER_NAME}")
    logger.info(f"🔒 OW-AI Governance: {OWAI_BASE_URL}")

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
            logger.error(f"Server error: {e}")


# ============================================
# TESTING
# ============================================

async def test_mcp_server():
    """Test MCP server functionality."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OW-AI Integration Example: MCP Server                     ║
║                                                               ║
║     This example demonstrates how to build an MCP server      ║
║     with OW-AI governance for enterprise security.            ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Test 1: List tools
    print("\n" + "=" * 60)
    print("Test 1: List Available Tools")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    response = await handle_mcp_request(request)
    print(f"Tools: {json.dumps(response['result'], indent=2)}")

    # Test 2: Low-risk query (SELECT)
    print("\n" + "=" * 60)
    print("Test 2: Database SELECT Query (LOW RISK)")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "SELECT name, email FROM users WHERE active = true",
                "database": "staging"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

    # Test 3: High-risk query (DELETE)
    print("\n" + "=" * 60)
    print("Test 3: Database DELETE Query (HIGH RISK - Requires Approval)")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "DELETE FROM users WHERE last_login < '2024-01-01'",
                "database": "production"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

    # Test 4: File read (low risk)
    print("\n" + "=" * 60)
    print("Test 4: Read File (LOW RISK)")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "read_file",
            "arguments": {
                "path": "/var/log/app.log"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

    # Test 5: Shell command (high risk)
    print("\n" + "=" * 60)
    print("Test 5: Shell Command (HIGH RISK - Requires Approval)")
    print("=" * 60)

    request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "run_command",
            "arguments": {
                "command": "rm -rf /tmp/cache/*"
            }
        }
    }
    response = await handle_mcp_request(request)
    print(f"Result: {json.dumps(response['result'], indent=2)}")

    # Cleanup
    await governance_client.close()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run tests
        asyncio.run(test_mcp_server())
    else:
        # Run as MCP server
        asyncio.run(run_stdio_server())
