#!/usr/bin/env python3
"""
ASCEND SDK v2.0 - MCP Server Integration
=========================================

This example demonstrates MCP (Model Context Protocol) server integration:
1. @mcp_governance decorator for tool authorization
2. @high_risk_action for elevated approval requirements
3. MCPGovernanceMiddleware for bulk tool wrapping
4. Approval workflow handling

Prerequisites:
- Python 3.8+
- pip install ascend-sdk mcp

Usage:
    export ASCEND_API_KEY="owkai_your_key"
    python 08_mcp_server_v2.py

Security: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.2, NIST AI RMF

Author: Ascend Engineering Team
"""

import os
import asyncio
import logging
from datetime import datetime

from owkai_sdk import AscendClient, FailMode
from owkai_sdk.mcp import (
    mcp_governance,
    high_risk_action,
    MCPGovernanceMiddleware,
    MCPGovernanceConfig,
)
from owkai_sdk.exceptions import AuthorizationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize ASCEND client
ascend = AscendClient(
    api_key=os.getenv("ASCEND_API_KEY"),
    api_url=os.getenv("ASCEND_API_URL", "https://pilot.owkai.app"),
    agent_id="mcp-server-001",
    agent_name="Enterprise MCP Server",
    fail_mode=FailMode.CLOSED,
    enable_circuit_breaker=True,
)


# ============================================================
# Example 1: Basic @mcp_governance Decorator
# ============================================================

@mcp_governance(
    ascend,
    action_type="database.query",
    resource="analytics_db"
)
async def query_analytics(sql: str) -> dict:
    """
    Query the analytics database.

    This function is wrapped with ASCEND governance.
    Before execution:
    - Action is evaluated against policies
    - If denied, AuthorizationError is raised
    - If pending, waits for approval (configurable)

    After execution:
    - Completion/failure is logged automatically
    """
    logger.info(f"Executing query: {sql[:50]}...")

    # Simulate database query
    await asyncio.sleep(0.1)

    return {
        "rows": [
            {"user_id": 1, "name": "Alice"},
            {"user_id": 2, "name": "Bob"},
        ],
        "count": 2,
    }


# ============================================================
# Example 2: @high_risk_action Decorator
# ============================================================

@high_risk_action(
    ascend,
    action_type="database.delete",
    resource="production_db"
)
async def delete_records(table: str, where_clause: str) -> dict:
    """
    Delete records from production database.

    @high_risk_action automatically:
    - Sets risk_level="high"
    - Sets require_human_approval=True
    - Waits for human approval before execution
    """
    logger.warning(f"DELETING from {table} WHERE {where_clause}")

    # Simulate deletion
    await asyncio.sleep(0.2)

    return {
        "deleted_count": 5,
        "table": table,
    }


# ============================================================
# Example 3: Custom Configuration
# ============================================================

custom_config = MCPGovernanceConfig(
    # Approval handling
    wait_for_approval=True,
    approval_timeout_seconds=120,  # 2 minute timeout
    approval_poll_interval_seconds=3,

    # Error handling
    raise_on_denial=True,
    log_all_decisions=True,

    # Callbacks
    on_approval_required=lambda d, t: logger.info(f"Approval needed for {t}"),
    on_denied=lambda d, t: logger.warning(f"Action {t} was denied"),
    on_allowed=lambda d, t: logger.info(f"Action {t} was allowed"),
)


@mcp_governance(
    ascend,
    action_type="email.send",
    resource="smtp_server",
    config=custom_config,
    risk_level="medium",
    metadata={"department": "support"},
)
async def send_email(to: str, subject: str, body: str) -> dict:
    """Send email with custom governance configuration."""
    logger.info(f"Sending email to {to}: {subject}")

    await asyncio.sleep(0.1)

    return {
        "message_id": "msg_12345",
        "status": "sent",
    }


# ============================================================
# Example 4: MCPGovernanceMiddleware
# ============================================================

# Create middleware instance
middleware = MCPGovernanceMiddleware(
    ascend,
    default_config=MCPGovernanceConfig(
        wait_for_approval=False,  # Don't block on pending
        raise_on_denial=True,
    )
)


# Wrap functions with middleware
async def _read_file(path: str) -> str:
    """Read a file."""
    return f"Contents of {path}"


async def _write_file(path: str, content: str) -> dict:
    """Write to a file."""
    return {"path": path, "bytes_written": len(content)}


# Apply governance via middleware
read_file = middleware.wrap("file.read", "/var/data", _read_file)
write_file = middleware.wrap("file.write", "/var/data", _write_file)


# ============================================================
# Simulated MCP Server
# ============================================================

class MCPServer:
    """Simulated MCP server with governed tools."""

    def __init__(self):
        self.tools = {
            "query_analytics": query_analytics,
            "delete_records": delete_records,
            "send_email": send_email,
            "read_file": read_file,
            "write_file": write_file,
        }

    async def call_tool(self, tool_name: str, **kwargs):
        """Call a tool by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.tools[tool_name]
        try:
            result = await tool(**kwargs)
            logger.info(f"Tool {tool_name} completed: {result}")
            return result
        except AuthorizationError as e:
            logger.error(f"Tool {tool_name} denied: {e.message}")
            raise


# ============================================================
# Demo
# ============================================================

async def main():
    """Run MCP server demo."""
    server = MCPServer()

    logger.info("=== MCP Server with ASCEND Governance ===\n")

    # List governed tools
    logger.info(f"Governed tools via middleware: {middleware.governed_tools}")
    logger.info("")

    # Test 1: Low-risk query
    logger.info("--- Test 1: Analytics Query (Low Risk) ---")
    try:
        result = await server.call_tool(
            "query_analytics",
            sql="SELECT * FROM users LIMIT 10"
        )
        logger.info(f"Result: {result}\n")
    except AuthorizationError as e:
        logger.error(f"Denied: {e}\n")

    # Test 2: File read
    logger.info("--- Test 2: File Read (Via Middleware) ---")
    try:
        result = await server.call_tool(
            "read_file",
            path="/var/data/config.json"
        )
        logger.info(f"Result: {result}\n")
    except AuthorizationError as e:
        logger.error(f"Denied: {e}\n")

    # Test 3: Email send
    logger.info("--- Test 3: Email Send (Medium Risk) ---")
    try:
        result = await server.call_tool(
            "send_email",
            to="customer@example.com",
            subject="Order Confirmation",
            body="Your order has shipped!"
        )
        logger.info(f"Result: {result}\n")
    except AuthorizationError as e:
        logger.error(f"Denied: {e}\n")

    # Test 4: High-risk deletion (will likely require approval)
    logger.info("--- Test 4: Database Delete (High Risk) ---")
    try:
        result = await server.call_tool(
            "delete_records",
            table="audit_logs",
            where_clause="created_at < '2024-01-01'"
        )
        logger.info(f"Result: {result}\n")
    except AuthorizationError as e:
        logger.error(f"Denied: {e}\n")
    except Exception as e:
        logger.warning(f"Action pending or timed out: {e}\n")

    logger.info("=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
