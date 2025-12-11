---
Document ID: ASCEND-INT-005
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# LangChain Integration

Wrap your LangChain tools and agent actions with OW-kai enterprise governance for risk assessment, approval workflows, and compliance auditing.

## Status

**Integration Status**: Example Available
**Source Code**: `ow-ai-backend/integration-examples/01_langchain_agent.py`
**API Endpoint**: `POST /api/v1/actions/submit`

## Prerequisites

```bash
pip install langchain langchain-openai
# No separate SDK needed - use REST API or copy OWKAIClient from examples
```

## Architecture

```
LangChain Agent → Governed Tool → OW-kai API
                                     ↓
                     Risk Assessment (CVSS, NIST, MITRE)
                                     ↓
                     Approval Workflow (if required)
                                     ↓
                     Execute Action (if approved)
```

## Complete Example

From `integration-examples/01_langchain_agent.py`:

### 1. OW-kai Client Integration

```python
from owkai import OWKAIClient, OWKAIActionRejectedError, OWKAIApprovalTimeoutError
import os

# Initialize OW-kai client
owai_client = OWKAIClient(
    api_key=os.getenv("OWKAI_API_KEY", "owkai_admin_your_key_here"),
    base_url=os.getenv("OWKAI_BASE_URL", "https://pilot.owkai.app")
)
```

Note: The `owkai` import references example code. In production, copy the `OWKAIClient` class from `python_sdk_example.py` or make direct REST API calls.

### 2. Governance Wrapper

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class GovernanceResult:
    """Result of governance check"""
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
    Submit action to OW-kai for governance before execution.

    Args:
        action_type: database_write, file_delete, api_call, etc.
        description: Human-readable description
        tool_name: Name of the tool being used
        agent_id: Unique identifier for this agent
        target_system: production-db, staging-api, etc.
        risk_context: Additional context for risk assessment
        timeout: Max seconds to wait for approval

    Returns:
        GovernanceResult with approval status and metadata
    """
    try:
        # Submit action to OW-kai
        result = owai_client.execute_action(
            action_type=action_type,
            description=description,
            tool_name=tool_name,
            agent_id=agent_id,
            target_system=target_system,
            risk_context=risk_context or {}
        )

        print(f"📊 [OW-kai] Risk Score: {result.risk_score}, Level: {result.risk_level}")
        print(f"📋 [OW-kai] NIST Control: {result.nist_control}, MITRE: {result.mitre_technique}")

        # Check if approval required
        if result.requires_approval:
            print(f"⏳ [OW-kai] Waiting for approval (action_id: {result.action_id})...")

            status = owai_client.wait_for_approval(
                result.action_id,
                timeout=timeout
            )

            print(f"✅ [OW-kai] Approved by: {status.reviewed_by}")

            return GovernanceResult(
                allowed=True,
                action_id=result.action_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                approved_by=status.reviewed_by
            )
        else:
            print(f"✅ [OW-kai] Auto-approved (low risk)")

            return GovernanceResult(
                allowed=True,
                action_id=result.action_id,
                risk_score=result.risk_score,
                risk_level=result.risk_level
            )

    except OWKAIApprovalTimeoutError:
        print(f"⏰ [OW-kai] Approval timeout - action not executed")
        return GovernanceResult(
            allowed=False,
            rejection_reason="Approval timeout"
        )

    except OWKAIActionRejectedError as e:
        print(f"❌ [OW-kai] Action rejected: {e.rejection_reason}")
        return GovernanceResult(
            allowed=False,
            rejection_reason=e.rejection_reason
        )
```

### 3. Governed Tools

#### Database Query Tool

```python
def governed_database_query(query: str, database: str = "production") -> str:
    """
    Execute database query with OW-kai governance.

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

    # Submit to OW-kai for governance
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

    # Execute the actual query
    # In production, connect to your actual database
    return f"✅ Query executed successfully on {database} (simulated)\nQuery: {query}"
```

#### File Operation Tool

```python
def governed_file_operation(operation: str, path: str, content: str = None) -> str:
    """
    Execute file operation with OW-kai governance.

    Args:
        operation: read, write, delete
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

    # Execute the actual operation
    if operation == "read":
        return f"✅ File read: {path} (simulated)"
    elif operation == "write":
        return f"✅ File written: {path} with {len(content or '')} chars (simulated)"
    elif operation == "delete":
        return f"✅ File deleted: {path} (simulated)"

    return f"Unknown operation: {operation}"
```

#### API Call Tool

```python
def governed_api_call(url: str, method: str = "GET", data: dict = None) -> str:
    """
    Make API call with OW-kai governance.

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

    # Execute the actual API call
    return f"✅ API call completed: {method} {url} (simulated)"
```

### 4. LangChain Agent Integration

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

def create_governed_agent():
    """
    Create LangChain agent with OW-kai governed tools.

    Returns:
        AgentExecutor configured with governed tools
    """
    # Define tools
    tools = [
        StructuredTool.from_function(
            func=governed_database_query,
            name="database_query",
            description="Execute SQL query on the database. Use for reading, writing, or modifying data."
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
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to database, file, and API tools.
All your actions are governed by OW-kai Enterprise for security and compliance.
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
```

### 5. Usage Examples

```python
# Example 1: Low-risk SELECT query (auto-approved)
result = governed_database_query(
    query="SELECT name, email FROM users WHERE status = 'active'",
    database="staging"
)
print(result)

# Example 2: High-risk DELETE query (requires approval)
result = governed_database_query(
    query="DELETE FROM users WHERE last_login < '2025-01-01'",
    database="production"
)
print(result)

# Example 3: Full LangChain agent
agent = create_governed_agent()
response = agent.invoke({
    "input": "Get a list of active users from the staging database"
})
print(response['output'])
```

## Risk Levels by Action Type

| Action Type | Typical Risk Level | Approval Required |
|-------------|-------------------|-------------------|
| `database_read` (SELECT) | LOW (10-30) | No |
| `database_write` (INSERT/UPDATE) | MEDIUM (40-60) | Conditional |
| `database_delete` (DELETE) | HIGH (70-85) | Yes |
| `file_read` | LOW (15-25) | No |
| `file_write` | MEDIUM (45-55) | Conditional |
| `file_delete` | HIGH (70-80) | Yes |
| `api_call` (GET) | LOW (20-30) | No |
| `api_call` (POST/PUT) | MEDIUM (50-60) | Conditional |
| `api_call` (DELETE) | HIGH (75) | Yes |

## Error Handling

```python
from owkai import OWKAIActionRejectedError, OWKAIApprovalTimeoutError

try:
    result = governed_database_query(
        query="DELETE FROM audit_logs WHERE created_at < '2025-01-01'",
        database="production"
    )

except OWKAIActionRejectedError as e:
    print(f"Action rejected: {e.rejection_reason}")
    print(f"Risk score: {e.risk_score}")
    # Handle rejection - maybe notify security team
    notify_security_team(e)

except OWKAIApprovalTimeoutError:
    print("Approval timeout - action not executed")
    # Handle timeout - maybe retry or escalate
```

## Best Practices

### 1. Rich Risk Context

```python
governance = govern_action(
    action_type="database_delete",
    description="Delete old audit logs for compliance",
    tool_name="postgresql",
    target_system="production-db",
    risk_context={
        "database": "production",
        "table": "audit_logs",
        "where_clause": "created_at < '2025-01-01'",
        "estimated_rows": 10000,
        "is_production": True,
        "has_backup": True,
        "retention_policy": "6_months",
        "compliance_requirement": "GDPR_data_minimization"
    }
)
```

### 2. Descriptive Action Types

```python
# Good - specific action types
"database_read", "database_write", "database_delete"
"file_read", "file_write", "file_delete"
"api_call_get", "api_call_post", "api_call_delete"

# Bad - vague action types
"query", "action", "operation"
```

### 3. Unique Agent IDs

```python
# Good
agent_id = "customer-service-langchain-v2"
agent_id = "data-analyst-production"

# Bad
agent_id = "agent1"
agent_id = str(uuid4())  # Random makes tracking difficult
```

### 4. Appropriate Timeouts

```python
# Short timeout for low-latency use cases
governance = govern_action(..., timeout=30)  # 30 seconds

# Standard timeout for most operations
governance = govern_action(..., timeout=300)  # 5 minutes

# Long timeout for batch operations
governance = govern_action(..., timeout=1800)  # 30 minutes
```

## Integration Patterns

### Pattern 1: Wrap Existing Tools

```python
# Your existing tool
def original_database_query(query: str) -> str:
    return database.execute(query)

# Wrapped with governance
def database_query(query: str) -> str:
    governance = govern_action(
        action_type="database_query",
        description=f"Execute: {query}",
        tool_name="postgresql"
    )

    if not governance.allowed:
        raise PermissionError(governance.rejection_reason)

    return original_database_query(query)
```

### Pattern 2: Conditional Governance

```python
def smart_database_query(query: str, require_governance: bool = True) -> str:
    """Query with optional governance bypass for testing"""

    if require_governance:
        governance = govern_action(...)
        if not governance.allowed:
            return f"Blocked: {governance.rejection_reason}"

    return database.execute(query)
```

### Pattern 3: Governance Context Manager

```python
from contextlib import contextmanager

@contextmanager
def governed_operation(action_type: str, description: str):
    """Context manager for governed operations"""
    governance = govern_action(
        action_type=action_type,
        description=description
    )

    if not governance.allowed:
        raise PermissionError(governance.rejection_reason)

    try:
        yield governance
    finally:
        # Log completion
        print(f"✅ Operation completed: {governance.action_id}")

# Usage
with governed_operation("database_write", "Insert user record"):
    database.insert({"name": "Alice", "email": "alice@example.com"})
```

## Monitoring and Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("langchain-agent")

def governed_database_query(query: str, database: str = "production") -> str:
    logger.info(f"🔒 Submitting query for governance: {query[:100]}")

    governance = govern_action(...)

    if governance.allowed:
        logger.info(f"✅ Query approved (action_id: {governance.action_id})")
    else:
        logger.warning(f"❌ Query blocked: {governance.rejection_reason}")

    return execute_query(query)
```

## Limitations

1. **No Published SDK**: The example references `owkai` package which doesn't exist as a published library. Copy the client code from `python_sdk_example.py` or use direct REST API calls.

2. **Simulated Execution**: The example code simulates actual tool execution for safety. Replace with your real database/filesystem/API logic.

3. **Error Handling**: Add proper exception handling for network failures, timeouts, and API errors.

## Next Steps

- [MCP Server Integration](/integrations/mcp-server) - Build MCP servers with governance
- [Custom Agents](/integrations/custom-agents) - Direct Python SDK usage
- [AWS Lambda Example](https://github.com/yourusername/integration-examples) - Serverless governance
