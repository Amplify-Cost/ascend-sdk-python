"""
ASCEND LangChain Integration
============================

Enterprise-grade AI governance for LangChain agents and tools.

Quick Start:
    from ascend_langchain import AscendToolWrapper, AscendCallbackHandler

    # Wrap existing tools with governance
    from langchain.tools import DuckDuckGoSearchRun
    search = AscendToolWrapper(
        tool=DuckDuckGoSearchRun(),
        action_type="web.search",
        risk_level="low"
    )

    # Or use callback handler for all tool calls
    handler = AscendCallbackHandler(agent_id="my-agent")
    executor = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])

Features:
- AscendToolWrapper: Wrap any LangChain tool with governance
- AscendCallbackHandler: Automatic governance for all agent actions
- governed decorator: Simple function-level governance
- Risk classification and policy enforcement
- Full audit trail of all AI agent actions

Documentation: https://docs.owkai.app/integration/frameworks/langchain
"""

from .wrapper import AscendToolWrapper
from .callback import AscendCallbackHandler
from .decorators import governed, governed_async
from .tools import (
    GovernedBaseTool,
    GovernedStructuredTool,
    create_governed_tool,
)

__version__ = "1.0.0"
__all__ = [
    # Core components
    "AscendToolWrapper",
    "AscendCallbackHandler",
    # Decorators
    "governed",
    "governed_async",
    # Tool classes
    "GovernedBaseTool",
    "GovernedStructuredTool",
    "create_governed_tool",
]
