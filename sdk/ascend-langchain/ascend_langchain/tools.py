"""
Governed tool base classes for LangChain.

Usage:
    from ascend_langchain import GovernedBaseTool, create_governed_tool

    # Option 1: Subclass GovernedBaseTool
    class MySQLTool(GovernedBaseTool):
        name = "sql_query"
        description = "Execute SQL queries"
        action_type = "database.query"
        tool_name = "postgresql"
        risk_level = "high"

        def _execute(self, query: str) -> str:
            return db.execute(query).fetchall()

    # Option 2: Use factory function
    sql_tool = create_governed_tool(
        name="sql_query",
        description="Execute SQL queries",
        func=lambda query: db.execute(query).fetchall(),
        action_type="database.query",
        tool_name="postgresql"
    )
"""

import os
import logging
from typing import Any, Callable, Dict, Optional, Type, Union
from abc import abstractmethod

from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import Field

try:
    from ascend import AscendClient, AgentAction
    from ascend.exceptions import AscendError
except ImportError:
    raise ImportError(
        "ascend-ai-sdk is required. Install with: pip install ascend-ai-sdk"
    )

logger = logging.getLogger(__name__)


class GovernedBaseTool(BaseTool):
    """
    Base class for LangChain tools with built-in ASCEND governance.

    Subclass this to create tools that automatically check governance
    before execution.

    Attributes:
        action_type: ASCEND action type for this tool
        tool_name: Tool identifier for ASCEND
        risk_level: Risk classification ("low", "medium", "high", "critical")

    Example:
        >>> class DatabaseQueryTool(GovernedBaseTool):
        ...     name = "query_db"
        ...     description = "Query the database"
        ...     action_type = "database.query"
        ...     tool_name = "postgresql"
        ...     risk_level = "medium"
        ...
        ...     def _execute(self, query: str) -> str:
        ...         return str(db.execute(query).fetchall())
    """

    # Governance configuration - override in subclass
    action_type: str = Field(default="langchain.tool", description="ASCEND action type")
    tool_name_override: str = Field(default="", description="Tool name for ASCEND")
    risk_level: str = Field(default="medium", description="Risk level")

    # Agent configuration
    agent_id: str = Field(default="", description="Agent ID")
    agent_name: str = Field(default="LangChain Agent", description="Agent name")

    # Behavior
    fail_open: bool = Field(default=False, description="Allow on error")

    # Internal
    _client: Optional[AscendClient] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs: Any):
        # Get defaults from environment
        if "agent_id" not in kwargs or not kwargs["agent_id"]:
            kwargs["agent_id"] = os.environ.get("ASCEND_AGENT_ID", "langchain-agent")

        super().__init__(**kwargs)

    @property
    def client(self) -> AscendClient:
        """Lazy-initialize the ASCEND client."""
        if self._client is None:
            api_key = os.environ.get("ASCEND_API_KEY")
            if not api_key:
                raise ValueError(
                    "ASCEND API key required. Set ASCEND_API_KEY environment variable."
                )
            self._client = AscendClient(
                api_key=api_key,
                base_url=os.environ.get("ASCEND_API_URL", "https://api.owkai.app"),
            )
        return self._client

    @property
    def governed_tool_name(self) -> str:
        """Get the tool name for ASCEND."""
        return self.tool_name_override or self.name

    def _check_governance(self, input_str: str) -> Dict[str, Any]:
        """Check governance before execution."""
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=self.action_type,
            resource=f"{self.name}: {input_str[:200]}",
            tool_name=self.governed_tool_name,
            action_details={
                "input": input_str[:1000],
                "description": self.description[:500] if self.description else "",
            },
            risk_indicators={
                "risk_level": self.risk_level,
            },
        )

        try:
            result = self.client.submit_action(action)

            if result.is_approved():
                logger.info(f"[ASCEND] Tool '{self.name}' APPROVED")
                return {"approved": True, "action_id": result.action_id}

            if result.is_pending():
                logger.warning(f"[ASCEND] Tool '{self.name}' PENDING")
                return {
                    "approved": False,
                    "action_id": result.action_id,
                    "reason": f"Requires approval. Action ID: {result.action_id}",
                    "pending": True,
                }

            logger.warning(f"[ASCEND] Tool '{self.name}' DENIED: {result.reason}")
            return {
                "approved": False,
                "action_id": result.action_id,
                "reason": result.reason or "Denied",
            }

        except AscendError as e:
            logger.error(f"[ASCEND] Governance error: {e}")
            if self.fail_open:
                return {"approved": True, "action_id": None, "reason": "fail_open"}
            return {"approved": False, "action_id": None, "reason": str(e)}

    @abstractmethod
    def _execute(self, tool_input: str) -> str:
        """
        Execute the tool logic. Override this in subclass.

        Args:
            tool_input: The input to the tool

        Returns:
            The tool output as a string
        """
        raise NotImplementedError("Subclass must implement _execute()")

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Run the tool with governance check."""
        governance = self._check_governance(tool_input)

        if not governance["approved"]:
            return f"[GOVERNANCE DENIED] {governance.get('reason', 'Unknown')}"

        return self._execute(tool_input)

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async run with governance check."""
        governance = self._check_governance(tool_input)

        if not governance["approved"]:
            return f"[GOVERNANCE DENIED] {governance.get('reason', 'Unknown')}"

        # Call sync _execute by default
        return self._execute(tool_input)


class GovernedStructuredTool(StructuredTool):
    """
    StructuredTool with built-in ASCEND governance.

    Similar to GovernedBaseTool but for structured tools with
    defined input schemas.
    """

    action_type: str = "langchain.tool"
    tool_name_override: str = ""
    risk_level: str = "medium"
    agent_id: str = ""
    agent_name: str = "LangChain Agent"
    fail_open: bool = False

    _client: Optional[AscendClient] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    def client(self) -> AscendClient:
        """Lazy-initialize the ASCEND client."""
        if self._client is None:
            api_key = os.environ.get("ASCEND_API_KEY")
            if not api_key:
                raise ValueError("ASCEND API key required.")
            self._client = AscendClient(api_key=api_key)
        return self._client


def create_governed_tool(
    name: str,
    description: str,
    func: Callable[..., str],
    action_type: str,
    tool_name: str,
    risk_level: str = "medium",
    agent_id: Optional[str] = None,
    agent_name: str = "LangChain Agent",
    fail_open: bool = False,
    return_direct: bool = False,
) -> StructuredTool:
    """
    Factory function to create a governed LangChain tool.

    This is the simplest way to add governance to existing functions.

    Args:
        name: Tool name
        description: Tool description for the LLM
        func: The function to execute
        action_type: ASCEND action type
        tool_name: Tool identifier for ASCEND
        risk_level: Risk classification
        agent_id: Agent identifier
        agent_name: Agent display name
        fail_open: Allow on governance error
        return_direct: Return result directly to user

    Returns:
        A StructuredTool with governance checks

    Example:
        >>> def query_database(query: str) -> str:
        ...     return str(db.execute(query).fetchall())
        >>>
        >>> sql_tool = create_governed_tool(
        ...     name="sql_query",
        ...     description="Execute SQL queries against the database",
        ...     func=query_database,
        ...     action_type="database.query",
        ...     tool_name="postgresql",
        ...     risk_level="high"
        ... )
    """
    resolved_agent_id = agent_id or os.environ.get("ASCEND_AGENT_ID", "langchain-agent")

    # Create client lazily
    _client: Optional[AscendClient] = None

    def get_client() -> AscendClient:
        nonlocal _client
        if _client is None:
            api_key = os.environ.get("ASCEND_API_KEY")
            if not api_key:
                raise ValueError("ASCEND API key required.")
            _client = AscendClient(api_key=api_key)
        return _client

    def governed_func(**kwargs: Any) -> str:
        """Wrapper that checks governance before execution."""
        input_str = str(kwargs)[:500]

        action = AgentAction(
            agent_id=resolved_agent_id,
            agent_name=agent_name,
            action_type=action_type,
            resource=f"{name}: {input_str[:200]}",
            tool_name=tool_name,
            action_details=kwargs,
            risk_indicators={"risk_level": risk_level},
        )

        try:
            result = get_client().submit_action(action)

            if result.is_approved():
                logger.info(f"[ASCEND] Tool '{name}' APPROVED")
                return func(**kwargs)

            if result.is_pending():
                return (
                    f"[GOVERNANCE PENDING] Tool '{name}' requires approval. "
                    f"Action ID: {result.action_id}"
                )

            return f"[GOVERNANCE DENIED] {result.reason or 'Policy violation'}"

        except AscendError as e:
            logger.error(f"[ASCEND] Governance error: {e}")
            if fail_open:
                return func(**kwargs)
            return f"[GOVERNANCE ERROR] {e}"

    return StructuredTool.from_function(
        func=governed_func,
        name=name,
        description=description,
        return_direct=return_direct,
    )
