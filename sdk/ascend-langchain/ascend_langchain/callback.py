"""
AscendCallbackHandler - Automatic governance for all LangChain agent actions.

Usage:
    from ascend_langchain import AscendCallbackHandler
    from langchain.agents import AgentExecutor

    # Create callback handler
    handler = AscendCallbackHandler(
        agent_id="my-agent",
        agent_name="Production Agent"
    )

    # Use with agent executor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        callbacks=[handler]
    )
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.outputs import LLMResult

try:
    from ascend import AscendClient, AgentAction as AscendAction
    from ascend.exceptions import AscendError
except ImportError:
    raise ImportError(
        "ascend-ai-sdk is required. Install with: pip install ascend-ai-sdk"
    )

logger = logging.getLogger(__name__)


class AscendCallbackHandler(BaseCallbackHandler):
    """
    LangChain callback handler that integrates ASCEND governance.

    This handler automatically:
    - Logs all tool invocations to ASCEND
    - Enforces governance policies on tool execution
    - Tracks agent chains and LLM calls
    - Provides full audit trail

    Args:
        agent_id: Unique agent identifier
        agent_name: Human-readable agent name
        api_key: ASCEND API key (defaults to ASCEND_API_KEY env var)
        base_url: ASCEND API URL (defaults to ASCEND_API_URL env var)
        enforce_governance: If True, block denied actions (default: True)
        log_llm_calls: If True, log LLM invocations (default: False)
        log_chain_events: If True, log chain start/end (default: False)
        fail_open: If True, allow on governance errors (default: False)

    Example:
        >>> from ascend_langchain import AscendCallbackHandler
        >>> from langchain.agents import AgentExecutor
        >>>
        >>> handler = AscendCallbackHandler(
        ...     agent_id="customer-support-agent",
        ...     agent_name="Customer Support Bot"
        ... )
        >>>
        >>> executor = AgentExecutor(
        ...     agent=agent,
        ...     tools=tools,
        ...     callbacks=[handler]
        ... )
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        agent_name: str = "LangChain Agent",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enforce_governance: bool = True,
        log_llm_calls: bool = False,
        log_chain_events: bool = False,
        fail_open: bool = False,
    ):
        super().__init__()
        self.agent_id = agent_id or os.environ.get("ASCEND_AGENT_ID", "langchain-agent")
        self.agent_name = agent_name
        self.api_key = api_key or os.environ.get("ASCEND_API_KEY", "")
        self.base_url = base_url or os.environ.get("ASCEND_API_URL", "https://api.owkai.app")
        self.enforce_governance = enforce_governance
        self.log_llm_calls = log_llm_calls
        self.log_chain_events = log_chain_events
        self.fail_open = fail_open

        # Track action IDs for completion logging
        self._action_ids: Dict[str, str] = {}
        self._chain_ids: Dict[str, str] = {}

        # Initialize client
        self._client: Optional[AscendClient] = None

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
                base_url=self.base_url,
            )
        return self._client

    def _generate_run_key(self, run_id: UUID, parent_run_id: Optional[UUID] = None) -> str:
        """Generate a unique key for tracking runs."""
        return f"{run_id}:{parent_run_id or 'root'}"

    # ==================== Tool Callbacks ====================

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when a tool starts - check governance."""
        tool_name = serialized.get("name", "unknown")

        logger.info(f"[ASCEND] Tool starting: {tool_name}")

        # Build action for governance
        action = AscendAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=f"langchain.tool.{tool_name}",
            resource=f"Tool execution: {tool_name}",
            tool_name=tool_name,
            action_details={
                "input": input_str[:1000] if input_str else "",
                "tool_description": serialized.get("description", "")[:500],
                "tags": tags or [],
            },
            context={
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
                "metadata": metadata,
            },
        )

        try:
            result = self.client.submit_action(action)

            # Track action ID for completion
            run_key = self._generate_run_key(run_id, parent_run_id)
            self._action_ids[run_key] = result.action_id

            if result.is_approved():
                logger.info(
                    f"[ASCEND] Tool '{tool_name}' APPROVED - Action ID: {result.action_id}"
                )
                return None

            if result.is_pending():
                logger.warning(
                    f"[ASCEND] Tool '{tool_name}' PENDING - Action ID: {result.action_id}"
                )
                if self.enforce_governance:
                    raise PermissionError(
                        f"Tool '{tool_name}' requires approval. "
                        f"Action ID: {result.action_id}"
                    )
                return None

            # Denied
            logger.warning(f"[ASCEND] Tool '{tool_name}' DENIED - Reason: {result.reason}")
            if self.enforce_governance:
                raise PermissionError(
                    f"Tool '{tool_name}' denied by governance: {result.reason}"
                )

        except AscendError as e:
            logger.error(f"[ASCEND] Governance error for tool '{tool_name}': {e}")
            if not self.fail_open and self.enforce_governance:
                raise PermissionError(f"Governance check failed: {e}")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when a tool ends - log completion."""
        run_key = self._generate_run_key(run_id, parent_run_id)
        action_id = self._action_ids.pop(run_key, None)

        if action_id:
            logger.debug(f"[ASCEND] Tool completed - Action ID: {action_id}")
            # Could log completion to ASCEND if API supports it

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called on tool error - log failure."""
        run_key = self._generate_run_key(run_id, parent_run_id)
        action_id = self._action_ids.pop(run_key, None)

        logger.error(f"[ASCEND] Tool error - Action ID: {action_id}, Error: {error}")

    # ==================== Chain Callbacks ====================

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when a chain starts."""
        if not self.log_chain_events:
            return

        chain_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        logger.debug(f"[ASCEND] Chain starting: {chain_name}")

        # Optionally log chain start to ASCEND
        action = AscendAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type="langchain.chain.start",
            resource=f"Chain: {chain_name}",
            tool_name="langchain_chain",
            action_details={
                "chain_name": chain_name,
                "input_keys": list(inputs.keys()),
            },
        )

        try:
            result = self.client.submit_action(action)
            run_key = self._generate_run_key(run_id, parent_run_id)
            self._chain_ids[run_key] = result.action_id
        except AscendError as e:
            logger.warning(f"[ASCEND] Failed to log chain start: {e}")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when a chain ends."""
        if not self.log_chain_events:
            return

        run_key = self._generate_run_key(run_id, parent_run_id)
        self._chain_ids.pop(run_key, None)
        logger.debug(f"[ASCEND] Chain completed - Run ID: {run_id}")

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called on chain error."""
        if not self.log_chain_events:
            return

        run_key = self._generate_run_key(run_id, parent_run_id)
        self._chain_ids.pop(run_key, None)
        logger.error(f"[ASCEND] Chain error - Run ID: {run_id}, Error: {error}")

    # ==================== LLM Callbacks ====================

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when an LLM starts."""
        if not self.log_llm_calls:
            return

        model_name = serialized.get("name", serialized.get("id", ["unknown"])[-1])
        logger.debug(f"[ASCEND] LLM call starting: {model_name}")

        action = AscendAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type="langchain.llm.call",
            resource=f"LLM: {model_name}",
            tool_name=model_name,
            action_details={
                "model": model_name,
                "prompt_count": len(prompts),
                "total_chars": sum(len(p) for p in prompts),
            },
        )

        try:
            self.client.submit_action(action)
        except AscendError as e:
            logger.warning(f"[ASCEND] Failed to log LLM call: {e}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when an LLM ends."""
        if not self.log_llm_calls:
            return

        logger.debug(f"[ASCEND] LLM call completed - Run ID: {run_id}")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called on LLM error."""
        if not self.log_llm_calls:
            return

        logger.error(f"[ASCEND] LLM error - Run ID: {run_id}, Error: {error}")

    # ==================== Agent Callbacks ====================

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when an agent takes an action."""
        logger.debug(f"[ASCEND] Agent action: {action.tool} - Input: {action.tool_input[:100]}")

    def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Called when an agent finishes."""
        logger.debug(f"[ASCEND] Agent finished - Run ID: {run_id}")
