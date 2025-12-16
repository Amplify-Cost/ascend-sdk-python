"""
Governance decorators for LangChain functions.

Usage:
    from ascend_langchain import governed

    @governed(action_type="database.query", tool_name="postgresql")
    def query_database(query: str) -> list:
        return db.execute(query).fetchall()
"""

import os
import functools
import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar, cast

try:
    from ascend import AscendClient, AgentAction
    from ascend.exceptions import AscendError
except ImportError:
    raise ImportError(
        "ascend-ai-sdk is required. Install with: pip install ascend-ai-sdk"
    )

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Global client instance
_client: Optional[AscendClient] = None


def _get_client() -> AscendClient:
    """Get or create the global ASCEND client."""
    global _client
    if _client is None:
        api_key = os.environ.get("ASCEND_API_KEY")
        if not api_key:
            raise ValueError(
                "ASCEND API key required. Set ASCEND_API_KEY environment variable."
            )
        _client = AscendClient(
            api_key=api_key,
            base_url=os.environ.get("ASCEND_API_URL", "https://api.owkai.app"),
        )
    return _client


def governed(
    action_type: str,
    tool_name: str,
    risk_level: str = "medium",
    agent_id: Optional[str] = None,
    agent_name: str = "LangChain Agent",
    fail_open: bool = False,
) -> Callable[[F], F]:
    """
    Decorator to add ASCEND governance to any function.

    Args:
        action_type: ASCEND action type (e.g., "database.query", "file.write")
        tool_name: Name of the tool/service being used
        risk_level: Risk classification ("low", "medium", "high", "critical")
        agent_id: Agent identifier (defaults to ASCEND_AGENT_ID env var)
        agent_name: Human-readable agent name
        fail_open: If True, allow execution on governance errors

    Returns:
        Decorated function with governance checks

    Example:
        >>> @governed("database.query", "postgresql", risk_level="medium")
        ... def execute_query(query: str) -> list:
        ...     return db.execute(query).fetchall()
        >>>
        >>> # This will check governance before executing
        >>> results = execute_query("SELECT * FROM users")

    Example with high-risk operation:
        >>> @governed("file.delete", "filesystem", risk_level="high")
        ... def delete_file(path: str) -> None:
        ...     os.remove(path)
    """
    resolved_agent_id = agent_id or os.environ.get("ASCEND_AGENT_ID", "langchain-agent")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = _get_client()

            # Build action
            action = AgentAction(
                agent_id=resolved_agent_id,
                agent_name=agent_name,
                action_type=action_type,
                resource=f"Execute {func.__name__}",
                tool_name=tool_name,
                action_details={
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                },
                risk_indicators={
                    "risk_level": risk_level,
                },
            )

            try:
                result = client.submit_action(action)

                if result.is_approved():
                    logger.info(
                        f"[ASCEND] Function '{func.__name__}' APPROVED - "
                        f"Action ID: {result.action_id}"
                    )
                    return func(*args, **kwargs)

                if result.is_pending():
                    raise PermissionError(
                        f"Function '{func.__name__}' requires approval. "
                        f"Action ID: {result.action_id}"
                    )

                # Denied
                raise PermissionError(
                    f"Function '{func.__name__}' denied: {result.reason}"
                )

            except AscendError as e:
                logger.error(f"[ASCEND] Governance error for '{func.__name__}': {e}")
                if fail_open:
                    logger.warning("[ASCEND] fail_open=True, allowing execution")
                    return func(*args, **kwargs)
                raise PermissionError(f"Governance check failed: {e}")

        return cast(F, wrapper)

    return decorator


def governed_async(
    action_type: str,
    tool_name: str,
    risk_level: str = "medium",
    agent_id: Optional[str] = None,
    agent_name: str = "LangChain Agent",
    fail_open: bool = False,
) -> Callable[[F], F]:
    """
    Async version of the governed decorator.

    Same parameters as `governed`, but for async functions.

    Example:
        >>> @governed_async("api.call", "external_api", risk_level="medium")
        ... async def fetch_data(url: str) -> dict:
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get(url) as response:
        ...             return await response.json()
    """
    resolved_agent_id = agent_id or os.environ.get("ASCEND_AGENT_ID", "langchain-agent")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = _get_client()

            # Build action
            action = AgentAction(
                agent_id=resolved_agent_id,
                agent_name=agent_name,
                action_type=action_type,
                resource=f"Execute {func.__name__}",
                tool_name=tool_name,
                action_details={
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "async": True,
                },
                risk_indicators={
                    "risk_level": risk_level,
                },
            )

            try:
                # Run sync governance check in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: client.submit_action(action)
                )

                if result.is_approved():
                    logger.info(
                        f"[ASCEND] Async function '{func.__name__}' APPROVED - "
                        f"Action ID: {result.action_id}"
                    )
                    return await func(*args, **kwargs)

                if result.is_pending():
                    raise PermissionError(
                        f"Async function '{func.__name__}' requires approval. "
                        f"Action ID: {result.action_id}"
                    )

                # Denied
                raise PermissionError(
                    f"Async function '{func.__name__}' denied: {result.reason}"
                )

            except AscendError as e:
                logger.error(f"[ASCEND] Governance error for '{func.__name__}': {e}")
                if fail_open:
                    logger.warning("[ASCEND] fail_open=True, allowing execution")
                    return await func(*args, **kwargs)
                raise PermissionError(f"Governance check failed: {e}")

        return cast(F, wrapper)

    return decorator
