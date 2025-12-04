"""
Authorized Agent Wrapper
=========================

High-level wrapper for AI agents requiring authorization.

This module provides a convenient interface for agents to request
authorization and conditionally execute actions.

Example:
    from ascend import AuthorizedAgent

    agent = AuthorizedAgent(
        agent_id="customer-bot-001",
        agent_name="Customer Service Bot"
    )

    # Execute only if authorized
    result = agent.execute_if_authorized(
        action_type="data_access",
        resource="customer_profile",
        execute_fn=lambda: get_customer_data("CUST-123")
    )
"""

import logging
from typing import Optional, Dict, Any, Callable, TypeVar

from .client import AscendClient
from .models import AgentAction, ActionResult
from .exceptions import AuthorizationDeniedError, TimeoutError
from .constants import DEFAULT_DECISION_TIMEOUT

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AuthorizedAgent:
    """
    Wrapper for AI agents that require Ascend authorization.

    This class wraps your AI agent and automatically submits
    actions for authorization before execution.

    Features:
    - Automatic action submission
    - Conditional execution based on authorization
    - Built-in waiting for manual approvals
    - Error handling with clear exceptions

    Args:
        agent_id: Unique identifier for this agent (e.g., "bot-001")
        agent_name: Human-readable agent name (e.g., "Customer Service Bot")
        client: AscendClient instance (creates new if not provided)

    Example:
        agent = AuthorizedAgent(
            agent_id="financial-advisor-001",
            agent_name="Financial Advisor AI"
        )

        # Request authorization and execute if approved
        try:
            portfolio = agent.execute_if_authorized(
                action_type="data_access",
                resource="customer_portfolio",
                execute_fn=lambda: fetch_portfolio(customer_id),
                resource_id=customer_id
            )
        except AuthorizationDeniedError as e:
            print(f"Access denied: {e.message}")
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        client: Optional[AscendClient] = None,
    ) -> None:
        """
        Initialize an authorized agent.

        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable agent name
            client: AscendClient instance (creates new if not provided)
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.client = client or AscendClient()

        logger.info(f"Authorized agent initialized: {agent_id} ({agent_name})")

    def request_authorization(
        self,
        action_type: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        risk_indicators: Optional[Dict[str, Any]] = None,
        wait_for_decision: bool = True,
        timeout: int = DEFAULT_DECISION_TIMEOUT,
    ) -> ActionResult:
        """
        Request authorization for an action.

        Submits the action to Ascend and optionally waits for a decision.

        Args:
            action_type: Type of action (data_access, transaction, etc.)
            resource: Resource being accessed/modified
            resource_id: Specific resource identifier (optional)
            details: Additional action details (optional)
            context: Contextual information (optional)
            risk_indicators: Risk assessment data (optional)
            wait_for_decision: Whether to wait for decision (default: True)
            timeout: Decision timeout in seconds (default: 60)

        Returns:
            ActionResult with authorization decision

        Raises:
            ValidationError: Invalid input data
            AuthenticationError: Invalid API key
            TimeoutError: Decision timeout (if wait_for_decision=True)

        Example:
            decision = agent.request_authorization(
                action_type="transaction",
                resource="customer_account",
                resource_id="ACC-12345",
                details={"amount": 50000, "currency": "USD"},
                risk_indicators={"amount_threshold": "exceeded"}
            )

            if decision.is_approved():
                print("Transaction authorized")
            elif decision.is_denied():
                print(f"Transaction denied: {decision.reason}")
        """
        # Create action
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            action_details=details,
            context=context,
            risk_indicators=risk_indicators,
        )

        logger.info(
            f"[{self.agent_id}] Requesting authorization: {action_type} on {resource}"
        )

        # Submit action
        result = self.client.submit_action(action)

        # Wait for decision if requested and currently pending
        if wait_for_decision and result.is_pending():
            logger.info(
                f"[{self.agent_id}] Action {result.action_id} pending, "
                f"waiting up to {timeout}s for decision"
            )
            result = self.client.wait_for_decision(
                result.action_id,
                timeout_ms=timeout * 1000
            )

        return result

    def execute_if_authorized(
        self,
        action_type: str,
        resource: str,
        execute_fn: Callable[[], T],
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        risk_indicators: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_DECISION_TIMEOUT,
    ) -> T:
        """
        Execute a function only if authorized by Ascend.

        This is the primary method for governed agent actions.
        It requests authorization and executes the function only
        if the action is approved.

        Args:
            action_type: Type of action
            resource: Resource being accessed
            execute_fn: Function to execute if authorized
            resource_id: Specific resource identifier
            details: Additional action details
            context: Contextual information
            risk_indicators: Risk assessment data
            timeout: Decision timeout in seconds

        Returns:
            Result of execute_fn if authorized

        Raises:
            AuthorizationDeniedError: If action is denied
            TimeoutError: If decision times out
            ValidationError: If input is invalid

        Example:
            # Execute database query only if authorized
            result = agent.execute_if_authorized(
                action_type="data_access",
                resource="customer_database",
                execute_fn=lambda: db.query("SELECT * FROM customers"),
                context={"query_type": "read_all"}
            )

            # Execute financial transaction only if authorized
            confirmation = agent.execute_if_authorized(
                action_type="transaction",
                resource="payment_gateway",
                execute_fn=lambda: process_payment(amount, recipient),
                details={"amount": amount, "recipient": recipient},
                risk_indicators={"high_value": amount > 10000}
            )
        """
        # Request authorization (always wait for decision)
        decision = self.request_authorization(
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            details=details,
            context=context,
            risk_indicators=risk_indicators,
            wait_for_decision=True,
            timeout=timeout,
        )

        # Check decision
        if decision.is_approved():
            logger.info(
                f"[{self.agent_id}] Action {decision.action_id} approved, executing"
            )
            return execute_fn()

        elif decision.is_denied():
            reason = decision.reason or "No reason provided"
            logger.warning(
                f"[{self.agent_id}] Action {decision.action_id} denied: {reason}"
            )
            raise AuthorizationDeniedError(
                f"Action denied: {reason}",
                status_code=None,
                response=decision.metadata,
            )

        elif decision.is_pending():
            # Should not happen if wait_for_decision=True, but handle anyway
            logger.error(
                f"[{self.agent_id}] Action {decision.action_id} still pending after timeout"
            )
            raise TimeoutError(
                f"Authorization decision not received within {timeout} seconds",
                status_code=None,
            )

        else:
            # Unexpected status
            logger.error(
                f"[{self.agent_id}] Unexpected authorization status: {decision.status}"
            )
            raise AuthorizationDeniedError(
                f"Unexpected authorization status: {decision.status}",
                status_code=None,
                response=decision.metadata,
            )

    def get_action_status(self, action_id: str) -> ActionResult:
        """
        Get current status of a previously submitted action.

        Args:
            action_id: The action ID

        Returns:
            ActionResult with current status

        Example:
            result = agent.request_authorization(
                action_type="data_access",
                resource="sensitive_data",
                wait_for_decision=False  # Don't wait
            )

            # Check status later
            status = agent.get_action_status(result.action_id)
            if status.is_approved():
                # Execute action
                pass
        """
        return self.client.get_action_status(action_id)

    def list_my_actions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list:
        """
        List recent actions by this agent.

        Note: Currently returns all actions for the organization.
        Filtering by agent_id is done client-side.

        Args:
            limit: Maximum number of actions to return
            offset: Pagination offset
            status: Filter by status

        Returns:
            List of ActionResults for this agent

        Example:
            pending_actions = agent.list_my_actions(status="pending")
            for action in pending_actions:
                print(f"Pending: {action.resource}")
        """
        result = self.client.list_actions(limit=limit, offset=offset, status=status)

        # Filter by this agent's ID (client-side)
        # TODO: Add server-side filtering when API supports it
        my_actions = [
            action for action in result.actions
            if action.metadata.get("agent_id") == self.agent_id
        ]

        return my_actions

    def close(self) -> None:
        """
        Close the underlying client connection.

        Only call this if you created the agent without passing
        a client parameter. If you passed a client, close it separately.
        """
        self.client.close()

    def __enter__(self) -> "AuthorizedAgent":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
