"""
AscendToolWrapper - Wrap any LangChain tool with ASCEND governance.

Usage:
    from ascend_langchain import AscendToolWrapper
    from langchain.tools import DuckDuckGoSearchRun

    # Wrap existing tool
    search = AscendToolWrapper(
        tool=DuckDuckGoSearchRun(),
        action_type="web.search",
        risk_level="low"
    )

    # Use in agent
    result = search.invoke("latest AI news")
"""

import os
import logging
from typing import Any, Dict, Optional, Type, Union
from langchain_core.tools import BaseTool
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


class AscendToolWrapper(BaseTool):
    """
    Wrapper that adds ASCEND governance to any LangChain tool.

    This wrapper intercepts all tool invocations, submits them to ASCEND
    for governance evaluation, and only executes the tool if approved.

    Args:
        tool: The LangChain tool to wrap
        action_type: ASCEND action type (e.g., "database.read", "web.search")
        risk_level: Risk classification ("low", "medium", "high", "critical")
        agent_id: Unique agent identifier (defaults to ASCEND_AGENT_ID env var)
        agent_name: Human-readable agent name
        api_key: ASCEND API key (defaults to ASCEND_API_KEY env var)
        base_url: ASCEND API URL (defaults to ASCEND_API_URL env var)
        fail_open: If True, allow execution on governance errors (default: False)
        auto_approve_low_risk: Auto-approve low risk actions (default: True)

    Example:
        >>> from langchain.tools import DuckDuckGoSearchRun
        >>> from ascend_langchain import AscendToolWrapper
        >>>
        >>> search = AscendToolWrapper(
        ...     tool=DuckDuckGoSearchRun(),
        ...     action_type="web.search",
        ...     risk_level="low"
        ... )
        >>> result = search.invoke("ASCEND AI governance")
    """

    # The wrapped tool
    wrapped_tool: BaseTool = Field(description="The LangChain tool being wrapped")

    # Governance configuration
    action_type: str = Field(default="langchain.tool", description="ASCEND action type")
    risk_level: str = Field(default="medium", description="Risk classification")
    agent_id: str = Field(default="", description="Agent identifier")
    agent_name: str = Field(default="LangChain Agent", description="Agent display name")

    # Client configuration
    api_key: str = Field(default="", description="ASCEND API key")
    base_url: str = Field(default="", description="ASCEND API URL")

    # Behavior configuration
    fail_open: bool = Field(default=False, description="Allow on governance error")
    auto_approve_low_risk: bool = Field(default=True, description="Auto-approve low risk")

    # Internal
    _client: Optional[AscendClient] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        tool: BaseTool,
        action_type: str = "langchain.tool",
        risk_level: str = "medium",
        agent_id: Optional[str] = None,
        agent_name: str = "LangChain Agent",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        fail_open: bool = False,
        auto_approve_low_risk: bool = True,
        **kwargs: Any,
    ):
        # Get values from environment if not provided
        resolved_api_key = api_key or os.environ.get("ASCEND_API_KEY", "")
        resolved_agent_id = agent_id or os.environ.get("ASCEND_AGENT_ID", "langchain-agent")
        resolved_base_url = base_url or os.environ.get(
            "ASCEND_API_URL", "https://api.owkai.app"
        )

        super().__init__(
            wrapped_tool=tool,
            action_type=action_type,
            risk_level=risk_level,
            agent_id=resolved_agent_id,
            agent_name=agent_name,
            api_key=resolved_api_key,
            base_url=resolved_base_url,
            fail_open=fail_open,
            auto_approve_low_risk=auto_approve_low_risk,
            name=tool.name,
            description=tool.description,
            **kwargs,
        )

    @property
    def client(self) -> AscendClient:
        """Lazy-initialize the ASCEND client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "ASCEND API key required. Set ASCEND_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self._client = AscendClient(
                api_key=self.api_key,
                base_url=self.base_url if self.base_url else None,
            )
        return self._client

    def _check_governance(self, input_str: str) -> Dict[str, Any]:
        """
        Check governance before tool execution.

        Returns:
            dict with keys: approved (bool), action_id (str), reason (str)
        """
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=self.action_type,
            resource=f"{self.name}: {input_str[:200]}",
            tool_name=self.name,
            action_details={
                "input": input_str[:1000],
                "tool_description": self.description[:500] if self.description else "",
            },
            risk_indicators={
                "risk_level": self.risk_level,
                "auto_approve": self.auto_approve_low_risk and self.risk_level == "low",
            },
        )

        try:
            result = self.client.submit_action(action)

            if result.is_approved():
                logger.info(
                    f"[ASCEND] Tool '{self.name}' APPROVED - Action ID: {result.action_id}"
                )
                return {
                    "approved": True,
                    "action_id": result.action_id,
                    "reason": "approved",
                    "risk_score": result.risk_score,
                }

            if result.is_pending():
                logger.warning(
                    f"[ASCEND] Tool '{self.name}' PENDING approval - Action ID: {result.action_id}"
                )
                return {
                    "approved": False,
                    "action_id": result.action_id,
                    "reason": f"Requires approval. Action ID: {result.action_id}",
                    "pending": True,
                }

            # Denied
            logger.warning(
                f"[ASCEND] Tool '{self.name}' DENIED - Reason: {result.reason}"
            )
            return {
                "approved": False,
                "action_id": result.action_id,
                "reason": result.reason or "Policy violation",
            }

        except AscendError as e:
            logger.error(f"[ASCEND] Governance error for '{self.name}': {e}")
            if self.fail_open:
                logger.warning("[ASCEND] fail_open=True, allowing execution")
                return {"approved": True, "action_id": None, "reason": "fail_open"}
            return {"approved": False, "action_id": None, "reason": str(e)}

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute the tool with governance check."""
        # Check governance
        governance = self._check_governance(tool_input)

        if not governance["approved"]:
            return f"[GOVERNANCE DENIED] {governance['reason']}"

        # Execute the wrapped tool
        try:
            if hasattr(self.wrapped_tool, "_run"):
                return self.wrapped_tool._run(tool_input, run_manager=run_manager)
            else:
                return self.wrapped_tool.invoke(tool_input)
        except Exception as e:
            logger.error(f"[ASCEND] Tool execution error: {e}")
            raise

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async execution with governance check."""
        # Check governance (sync for now)
        governance = self._check_governance(tool_input)

        if not governance["approved"]:
            return f"[GOVERNANCE DENIED] {governance['reason']}"

        # Execute the wrapped tool
        try:
            if hasattr(self.wrapped_tool, "_arun"):
                return await self.wrapped_tool._arun(tool_input, run_manager=run_manager)
            else:
                return self.wrapped_tool.invoke(tool_input)
        except Exception as e:
            logger.error(f"[ASCEND] Tool execution error: {e}")
            raise


def wrap_tools(
    tools: list[BaseTool],
    action_type_map: Optional[Dict[str, str]] = None,
    risk_level_map: Optional[Dict[str, str]] = None,
    default_risk_level: str = "medium",
    **kwargs: Any,
) -> list[AscendToolWrapper]:
    """
    Wrap multiple LangChain tools with ASCEND governance.

    Args:
        tools: List of LangChain tools to wrap
        action_type_map: Map tool names to action types
        risk_level_map: Map tool names to risk levels
        default_risk_level: Default risk level if not in map
        **kwargs: Additional args passed to AscendToolWrapper

    Returns:
        List of wrapped tools

    Example:
        >>> from ascend_langchain import wrap_tools
        >>> wrapped = wrap_tools(
        ...     tools=[search_tool, db_tool],
        ...     action_type_map={
        ...         "search": "web.search",
        ...         "database": "database.query"
        ...     },
        ...     risk_level_map={
        ...         "search": "low",
        ...         "database": "high"
        ...     }
        ... )
    """
    action_type_map = action_type_map or {}
    risk_level_map = risk_level_map or {}

    wrapped = []
    for tool in tools:
        action_type = action_type_map.get(tool.name, f"langchain.{tool.name}")
        risk_level = risk_level_map.get(tool.name, default_risk_level)

        wrapped.append(
            AscendToolWrapper(
                tool=tool,
                action_type=action_type,
                risk_level=risk_level,
                **kwargs,
            )
        )

    return wrapped
