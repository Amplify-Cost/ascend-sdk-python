"""
OW-AI SDK Authorized Agent
==========================

Wrapper for AI agents that require OW-AI authorization.
"""

import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union

from .client import OWKAIClient
from .models import (
    AgentAction,
    AuthorizationDecision,
    DecisionStatus,
    ActionContext,
    RiskIndicators
)
from .exceptions import AuthorizationError, TimeoutError

logger = logging.getLogger("owkai_sdk")

T = TypeVar("T")


class AuthorizedAgent:
    """
    Wrapper for AI agents that require OW-AI authorization.

    This class wraps your AI agent and automatically submits
    actions for authorization before execution.

    Example:
        agent = AuthorizedAgent(
            agent_id="financial-advisor-001",
            agent_name="Financial Advisor AI"
        )

        # Simple authorization check
        decision = await agent.request_authorization(
            action_type="transaction",
            resource="customer_account",
            details={"amount": 10000}
        )

        # Execute only if authorized
        result = agent.execute_if_authorized(
            action_type="data_access",
            resource="portfolio",
            execute_fn=lambda: fetch_portfolio_data()
        )

    Attributes:
        agent_id: Unique identifier for this agent
        agent_name: Human-readable name for display
        client: OWKAIClient instance for API communication
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        client: Optional[OWKAIClient] = None,
        default_timeout: int = 60
    ):
        """
        Initialize an authorized agent.

        Args:
            agent_id: Unique identifier for this agent
            agent_name: Human-readable agent name
            client: OWKAIClient instance (creates new if not provided)
            default_timeout: Default timeout for authorization decisions
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.client = client or OWKAIClient()
        self.default_timeout = default_timeout

        logger.info(f"AuthorizedAgent initialized: {agent_name} ({agent_id})")

    def request_authorization(
        self,
        action_type: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
        risk_indicators: Optional[Union[RiskIndicators, Dict[str, Any]]] = None,
        wait_for_decision: bool = True,
        timeout: Optional[int] = None
    ) -> AuthorizationDecision:
        """
        Request authorization for an action.

        Args:
            action_type: Type of action (data_access, transaction, etc.)
            resource: Resource being accessed
            resource_id: Specific resource identifier
            details: Additional action details
            context: Contextual information (ActionContext or dict)
            risk_indicators: Risk assessment data (RiskIndicators or dict)
            wait_for_decision: Whether to wait for decision
            timeout: Decision timeout in seconds

        Returns:
            AuthorizationDecision with approval status

        Example:
            decision = agent.request_authorization(
                action_type="transaction",
                resource="customer_account",
                resource_id="ACC-12345",
                details={
                    "operation": "transfer",
                    "amount": 50000,
                    "currency": "USD"
                },
                risk_indicators=RiskIndicators(
                    financial_data=True,
                    data_sensitivity="high"
                )
            )
        """
        action = AgentAction(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            action_details=details,
            context=context,
            risk_indicators=risk_indicators
        )

        decision = self.client.submit_action(action)

        if wait_for_decision and decision.decision == DecisionStatus.PENDING:
            effective_timeout = timeout or self.default_timeout
            decision = self.client.wait_for_decision(
                decision.action_id,
                timeout=effective_timeout
            )

        return decision

    def execute_if_authorized(
        self,
        action_type: str,
        resource: str,
        execute_fn: Callable[[], T],
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Union[ActionContext, Dict[str, Any]]] = None,
        risk_indicators: Optional[Union[RiskIndicators, Dict[str, Any]]] = None,
        timeout: Optional[int] = None,
        on_denied: Optional[Callable[[AuthorizationDecision], T]] = None
    ) -> T:
        """
        Execute a function only if authorized.

        This is the recommended pattern for most use cases. It:
        1. Submits the action for authorization
        2. Waits for a decision
        3. Executes the function if approved
        4. Raises AuthorizationError if denied

        Args:
            action_type: Type of action
            resource: Resource being accessed
            execute_fn: Function to execute if authorized (no arguments)
            resource_id: Specific resource identifier
            details: Additional action details
            context: Contextual information
            risk_indicators: Risk assessment data
            timeout: Decision timeout in seconds
            on_denied: Optional callback if action denied (receives decision)

        Returns:
            Result of execute_fn if authorized

        Raises:
            AuthorizationError: If action is denied (and no on_denied callback)
            TimeoutError: If decision times out

        Example:
            def fetch_customer_data():
                return db.query(Customer).filter_by(id=customer_id).first()

            try:
                customer = agent.execute_if_authorized(
                    action_type="data_access",
                    resource="customer_pii",
                    resource_id=customer_id,
                    execute_fn=fetch_customer_data
                )
            except AuthorizationError as e:
                logger.warning(f"Access denied: {e.message}")
        """
        decision = self.request_authorization(
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            details=details,
            context=context,
            risk_indicators=risk_indicators,
            wait_for_decision=True,
            timeout=timeout
        )

        if decision.decision == DecisionStatus.APPROVED:
            logger.info(f"Action authorized, executing...")
            return execute_fn()

        elif decision.decision == DecisionStatus.DENIED:
            if on_denied:
                return on_denied(decision)

            raise AuthorizationError(
                f"Action denied: {decision.comments or 'No reason provided'}",
                policy_violations=decision.policy_violations,
                risk_score=decision.risk_score
            )

        elif decision.decision == DecisionStatus.TIMEOUT:
            raise TimeoutError(
                "Authorization decision timed out",
                timeout_seconds=timeout or self.default_timeout
            )

        else:
            # PENDING, REQUIRES_MODIFICATION, etc.
            raise AuthorizationError(
                f"Unexpected authorization status: {decision.decision.value}",
                details={"decision": decision.decision.value}
            )

    def check_permission(
        self,
        action_type: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Quick permission check without waiting.

        Submits the action and returns immediately with initial decision.
        Useful for UI permission checks or preflight validation.

        Args:
            action_type: Type of action
            resource: Resource being accessed
            resource_id: Specific resource identifier
            details: Additional action details

        Returns:
            True if likely to be approved, False otherwise

        Note:
            This returns the initial auto-decision. Some actions may
            require manual approval even if this returns True initially.
        """
        decision = self.request_authorization(
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            details=details,
            wait_for_decision=False
        )

        return decision.decision in (
            DecisionStatus.APPROVED,
            DecisionStatus.AUTO_APPROVED
        )

    def get_recent_actions(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent actions for this agent.

        Args:
            limit: Maximum number of actions to return
            status: Filter by status

        Returns:
            Dictionary with actions list
        """
        return self.client.list_actions(
            limit=limit,
            agent_id=self.agent_id,
            status=status
        )
