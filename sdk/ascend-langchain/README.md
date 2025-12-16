# ASCEND LangChain Integration

Enterprise-grade AI governance for LangChain agents and tools.

[![PyPI version](https://badge.fury.io/py/ascend-langchain.svg)](https://pypi.org/project/ascend-langchain/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install ascend-langchain
```

## Quick Start

### 1. Wrap Existing Tools

The simplest way to add governance - wrap any LangChain tool:

```python
from ascend_langchain import AscendToolWrapper
from langchain_community.tools import DuckDuckGoSearchRun

# Wrap existing tool with governance
search = AscendToolWrapper(
    tool=DuckDuckGoSearchRun(),
    action_type="web.search",
    risk_level="low"
)

# Use as normal - governance happens automatically
result = search.invoke("latest AI governance news")
```

### 2. Use Callback Handler

Automatic governance for all agent tool calls:

```python
from ascend_langchain import AscendCallbackHandler
from langchain.agents import AgentExecutor

# Create callback handler
handler = AscendCallbackHandler(
    agent_id="customer-support-agent",
    agent_name="Customer Support Bot"
)

# Add to agent executor
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[handler]
)

# All tool calls are now governed
result = executor.invoke({"input": "Help me with my order"})
```

### 3. Use Decorator

Simple function-level governance:

```python
from ascend_langchain import governed

@governed(action_type="database.query", tool_name="postgresql", risk_level="high")
def query_database(query: str) -> list:
    return db.execute(query).fetchall()

# Governance check happens automatically
results = query_database("SELECT * FROM customers")
```

### 4. Create Governed Tools

Build governed tools from scratch:

```python
from ascend_langchain import GovernedBaseTool

class DatabaseQueryTool(GovernedBaseTool):
    name = "query_database"
    description = "Execute SQL queries against the database"
    action_type = "database.query"
    tool_name = "postgresql"
    risk_level = "high"

    def _execute(self, query: str) -> str:
        return str(db.execute(query).fetchall())

# Use in LangChain agent
tool = DatabaseQueryTool()
```

Or use the factory function:

```python
from ascend_langchain import create_governed_tool

sql_tool = create_governed_tool(
    name="sql_query",
    description="Execute SQL queries",
    func=lambda query: str(db.execute(query).fetchall()),
    action_type="database.query",
    tool_name="postgresql",
    risk_level="high"
)
```

## Configuration

### Environment Variables

```bash
export ASCEND_API_KEY="owkai_your_key_here"
export ASCEND_API_URL="https://api.owkai.app"  # Optional
export ASCEND_AGENT_ID="my-langchain-agent"   # Optional
```

### Risk Levels

| Level | Description | Default Behavior |
|-------|-------------|------------------|
| `low` | Read-only, non-sensitive | Auto-approve |
| `medium` | Write operations | Evaluate policy |
| `high` | Delete, modify critical | Require review |
| `critical` | Financial, PII access | Require approval |

## Complete Example

```python
import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from ascend_langchain import (
    AscendCallbackHandler,
    GovernedBaseTool,
    create_governed_tool
)

# Set API key
os.environ["ASCEND_API_KEY"] = "owkai_your_key_here"

# Create governed tools
class CustomerLookupTool(GovernedBaseTool):
    name = "customer_lookup"
    description = "Look up customer information by ID"
    action_type = "database.read"
    tool_name = "crm_database"
    risk_level = "medium"

    def _execute(self, customer_id: str) -> str:
        # Your actual lookup logic
        return f"Customer {customer_id}: John Doe, Premium tier"

# Create callback handler for automatic governance
handler = AscendCallbackHandler(
    agent_id="support-agent-prod",
    agent_name="Customer Support Agent"
)

# Set up agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
tools = [CustomerLookupTool()]

prompt = PromptTemplate.from_template("""
You are a customer support assistant.

Tools: {tools}
Tool Names: {tool_names}

Question: {input}
{agent_scratchpad}
""")

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    callbacks=[handler],
    verbose=True
)

# Run agent - all tool calls are governed
result = executor.invoke({"input": "Look up customer 12345"})
print(result["output"])
```

## Features

- **AscendToolWrapper**: Wrap any existing LangChain tool
- **AscendCallbackHandler**: Automatic governance for all agent actions
- **@governed decorator**: Simple function-level governance
- **GovernedBaseTool**: Base class for custom governed tools
- **create_governed_tool()**: Factory function for quick tool creation
- **Full audit trail**: All actions logged to ASCEND
- **Risk classification**: Automatic risk-based policy enforcement
- **Fail-secure design**: Deny by default on errors

## Documentation

- [Full Documentation](https://docs.owkai.app/integration/frameworks/langchain)
- [ASCEND Platform](https://owkai.app)
- [API Reference](https://docs.owkai.app/api-reference)

## License

MIT License - see [LICENSE](LICENSE) for details.
