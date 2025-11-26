#!/usr/bin/env python3
"""
OW-AI Integration Example 1: LangChain Agent with Governed Tools

USE CASE: AI Agent that executes database queries, file operations, and API calls
          with enterprise governance and approval workflows.

This example shows how to:
1. Wrap LangChain tools with OW-AI governance
2. Submit actions for risk assessment before execution
3. Handle approval workflows (auto-approve, manual approval, rejection)
4. Maintain audit trails for compliance

ARCHITECTURE:
    User Request → LangChain Agent → Governed Tool → OW-AI Platform
                                                          ↓
                                    Risk Assessment (CVSS, NIST, MITRE)
                                                          ↓
                                    Approval Workflow (if required)
                                                          ↓
                                    Execute Action (if approved)

Engineer: OW-AI Enterprise
"""

import os
import json
from typing import Any, Optional
from dataclasses import dataclass

# OW-AI SDK
from owkai import OWKAIClient, OWKAIActionRejectedError, OWKAIApprovalTimeoutError

# LangChain imports (install: pip install langchain langchain-openai)
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import BaseTool, StructuredTool
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install langchain langchain-openai")


# ============================================
# CONFIGURATION
# ============================================

OWAI_API_KEY = os.environ.get("OWKAI_API_KEY", "owkai_admin_your_key_here")
OWAI_BASE_URL = os.environ.get("OWKAI_BASE_URL", "https://pilot.owkai.app")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OW-AI client
owai_client = OWKAIClient(
    api_key=OWAI_API_KEY,
    base_url=OWAI_BASE_URL
)


# ============================================
# GOVERNED TOOL WRAPPER
# ============================================

@dataclass
class GovernanceResult:
    """Result of governance check."""
    allowed: bool
    action_id: Optional[int] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None


def govern_action(
    action_type: str,
    description: str,
    tool_name: str,
    agent_id: str = "langchain-agent",
    target_system: Optional[str] = None,
    risk_context: Optional[dict] = None,
    timeout: int = 300
) -> GovernanceResult:
    """
    Submit action to OW-AI for governance before execution.

    Args:
        action_type: Type of action (database_write, file_delete, api_call, etc.)
        description: Human-readable description of what the action does
        tool_name: Name of the tool being used
        agent_id: Unique identifier for this agent
        target_system: Target system (production-db, staging-api, etc.)
        risk_context: Additional context for risk assessment
        timeout: Max seconds to wait for approval

    Returns:
        GovernanceResult with approval status and metadata
    """
    try:
        # Submit action to OW-AI
        result = owai_client.execute_action(
            action_type=action_type,
            description=description,
            tool_name=tool_name,
            agent_id=agent_id,
            target_system=target_system,
            risk_context=risk_context or {}
        )

        print(f"📊 [OW-AI] Risk Score: {result.risk_score}, Level: {result.risk_level}")
        print(f"📋 [OW-AI] NIST Control: {result.nist_control}, MITRE: {result.mitre_technique}")

        # Check if approval required
        if result.requires_approval:
            print(f"⏳ [OW-AI] Waiting for approval (action_id: {result.action_id})...")

            status = owai_client.wait_for_approval(
                result.action_id,
                timeout=timeout
            )

            print(f"✅ [OW-AI] Approved by: {status.reviewed_by}")

            return GovernanceResult(
                allowed=True,
                action_id=result.action_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                approved_by=status.reviewed_by
            )
        else:
            print(f"✅ [OW-AI] Auto-approved (low risk)")

            return GovernanceResult(
                allowed=True,
                action_id=result.action_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level
            )

    except OWKAIApprovalTimeoutError:
        print(f"⏰ [OW-AI] Approval timeout - action not executed")
        return GovernanceResult(
            allowed=False,
            rejection_reason="Approval timeout"
        )

    except OWKAIActionRejectedError as e:
        print(f"❌ [OW-AI] Action rejected: {e.rejection_reason}")
        return GovernanceResult(
            allowed=False,
            rejection_reason=e.rejection_reason
        )


# ============================================
# GOVERNED TOOLS
# ============================================

def governed_database_query(query: str, database: str = "production") -> str:
    """
    Execute a database query with OW-AI governance.

    Args:
        query: SQL query to execute
        database: Target database (production, staging, development)

    Returns:
        Query result or error message
    """
    # Determine action type based on query
    query_upper = query.upper().strip()
    if query_upper.startswith("SELECT"):
        action_type = "database_read"
    elif query_upper.startswith(("INSERT", "UPDATE")):
        action_type = "database_write"
    elif query_upper.startswith("DELETE"):
        action_type = "database_delete"
    else:
        action_type = "database_admin"

    # Submit to OW-AI for governance
    governance = govern_action(
        action_type=action_type,
        description=f"Execute SQL: {query[:200]}...",
        tool_name="postgresql",
        target_system=f"{database}-db",
        risk_context={
            "query_type": action_type,
            "database": database,
            "is_production": database == "production",
            "full_query": query
        }
    )

    if not governance.allowed:
        return f"❌ Action blocked: {governance.rejection_reason}"

    # Execute the actual query (replace with your database code)
    # In production, this would execute against your actual database
    return f"✅ Query executed successfully on {database} (simulated)\nQuery: {query}"


def governed_file_operation(operation: str, path: str, content: str = None) -> str:
    """
    Execute a file operation with OW-AI governance.

    Args:
        operation: Operation type (read, write, delete)
        path: File path
        content: Content to write (for write operations)

    Returns:
        Operation result or error message
    """
    action_type = f"file_{operation}"

    governance = govern_action(
        action_type=action_type,
        description=f"File {operation}: {path}",
        tool_name="filesystem",
        target_system="local-filesystem",
        risk_context={
            "operation": operation,
            "path": path,
            "has_content": content is not None,
            "is_sensitive_path": any(p in path for p in ["/etc", "/var", "config", "secret"])
        }
    )

    if not governance.allowed:
        return f"❌ Action blocked: {governance.rejection_reason}"

    # Execute the actual operation (simulated for safety)
    if operation == "read":
        return f"✅ File read: {path} (simulated)"
    elif operation == "write":
        return f"✅ File written: {path} with {len(content or '')} chars (simulated)"
    elif operation == "delete":
        return f"✅ File deleted: {path} (simulated)"

    return f"Unknown operation: {operation}"


def governed_api_call(url: str, method: str = "GET", data: dict = None) -> str:
    """
    Make an API call with OW-AI governance.

    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request payload

    Returns:
        API response or error message
    """
    governance = govern_action(
        action_type="api_call",
        description=f"{method} {url}",
        tool_name="http_client",
        target_system="external-api",
        risk_context={
            "url": url,
            "method": method,
            "has_payload": data is not None,
            "is_external": not url.startswith(("http://localhost", "http://127.0.0.1"))
        }
    )

    if not governance.allowed:
        return f"❌ Action blocked: {governance.rejection_reason}"

    # Execute the actual API call (simulated for safety)
    return f"✅ API call completed: {method} {url} (simulated)"


# ============================================
# LANGCHAIN AGENT SETUP
# ============================================

def create_governed_agent():
    """
    Create a LangChain agent with OW-AI governed tools.

    Returns:
        AgentExecutor configured with governed tools
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain not available")

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable required")

    # Define tools
    tools = [
        StructuredTool.from_function(
            func=governed_database_query,
            name="database_query",
            description="Execute a SQL query on the database. Use for reading, writing, or modifying data."
        ),
        StructuredTool.from_function(
            func=governed_file_operation,
            name="file_operation",
            description="Perform file operations (read, write, delete) on the filesystem."
        ),
        StructuredTool.from_function(
            func=governed_api_call,
            name="api_call",
            description="Make HTTP API calls to external services."
        ),
    ]

    # Create LLM
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        api_key=OPENAI_API_KEY
    )

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to database, file, and API tools.
All your actions are governed by OW-AI Enterprise for security and compliance.
High-risk actions may require approval before execution.

When using tools:
1. Be specific about what you're doing
2. Use production database only when necessary
3. Prefer read operations over writes when possible
4. Report any blocked actions to the user"""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )


# ============================================
# USAGE EXAMPLES
# ============================================

def example_low_risk_query():
    """Example: Low-risk SELECT query (auto-approved)."""
    print("\n" + "=" * 60)
    print("Example 1: Low-Risk Database Query (Auto-Approved)")
    print("=" * 60)

    result = governed_database_query(
        query="SELECT name, email FROM users WHERE status = 'active'",
        database="staging"
    )
    print(f"\nResult: {result}")


def example_high_risk_query():
    """Example: High-risk DELETE query (requires approval)."""
    print("\n" + "=" * 60)
    print("Example 2: High-Risk Database Query (Requires Approval)")
    print("=" * 60)

    result = governed_database_query(
        query="DELETE FROM users WHERE last_login < '2024-01-01'",
        database="production"
    )
    print(f"\nResult: {result}")


def example_file_operation():
    """Example: File write operation."""
    print("\n" + "=" * 60)
    print("Example 3: File Write Operation")
    print("=" * 60)

    result = governed_file_operation(
        operation="write",
        path="/tmp/report.csv",
        content="id,name,status\n1,John,active\n2,Jane,active"
    )
    print(f"\nResult: {result}")


def example_langchain_agent():
    """Example: Full LangChain agent with governed tools."""
    print("\n" + "=" * 60)
    print("Example 4: LangChain Agent with OW-AI Governance")
    print("=" * 60)

    if not LANGCHAIN_AVAILABLE:
        print("Skipping: LangChain not installed")
        return

    if not OPENAI_API_KEY:
        print("Skipping: OPENAI_API_KEY not set")
        return

    agent = create_governed_agent()

    # Test query
    response = agent.invoke({
        "input": "Get a list of active users from the staging database"
    })

    print(f"\nAgent Response: {response['output']}")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     OW-AI Integration Example: LangChain Agent                ║
║                                                               ║
║     This example demonstrates how to integrate OW-AI          ║
║     governance with LangChain agents for enterprise           ║
║     security and compliance.                                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Run examples
    example_low_risk_query()
    example_high_risk_query()
    example_file_operation()
    example_langchain_agent()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
