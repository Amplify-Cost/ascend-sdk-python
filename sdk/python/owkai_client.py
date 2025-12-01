"""
OW-AI Enterprise SDK - Python Client
====================================

Enterprise-grade Python SDK for integrating AI agents with OW-AI governance.

Features:
- Agent registration and configuration
- Action submission with approval workflow
- Policy evaluation
- Webhook callbacks
- MCP server integration

Installation:
    pip install owkai-sdk  # Coming soon to PyPI

Usage:
    from owkai_client import OWKAIClient, AuthorizedAgent

    # Initialize client
    client = OWKAIClient(
        api_key="owkai_...",
        base_url="https://pilot.owkai.app"
    )

    # Create an authorized agent
    agent = AuthorizedAgent(
        client=client,
        agent_id="financial-advisor-001",
        display_name="Financial Advisor AI"
    )

    # Register the agent
    agent.register()

    # Submit action for approval
    result = agent.submit_action(
        action_type="transaction",
        description="Execute stock purchase order",
        risk_score=72,
        resource="trading_system",
        metadata={"symbol": "AAPL", "shares": 100}
    )

    if result.approved:
        # Execute the action
        execute_trade(result.action_id)
    else:
        # Wait for approval
        result.wait_for_approval(timeout=300)

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

import os
import time
import json
import logging
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Status of an agent action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ERROR = "error"


class RiskLevel(Enum):
    """Risk levels for agent actions."""
    LOW = "low"          # 0-29
    MEDIUM = "medium"    # 30-59
    HIGH = "high"        # 60-79
    CRITICAL = "critical"  # 80-100


@dataclass
class ActionResult:
    """Result of an action submission."""
    action_id: int
    status: ActionStatus
    risk_score: int
    risk_level: RiskLevel
    requires_approval: bool
    approved: bool
    alert_generated: bool = False
    alert_id: Optional[int] = None
    poll_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_pending(self) -> bool:
        return self.status == ActionStatus.PENDING

    @property
    def can_proceed(self) -> bool:
        return self.approved or self.status == ActionStatus.APPROVED


@dataclass
class AgentConfig:
    """Configuration for a registered agent."""
    agent_id: str
    display_name: str
    agent_type: str = "supervised"
    default_risk_score: int = 50
    max_risk_threshold: int = 80
    auto_approve_below: int = 30
    requires_mfa_above: int = 70
    allowed_action_types: List[str] = field(default_factory=list)
    allowed_resources: List[str] = field(default_factory=list)
    blocked_resources: List[str] = field(default_factory=list)
    alert_on_high_risk: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OWKAIClient:
    """
    OW-AI Enterprise API Client

    Thread-safe HTTP client with retry logic and proper error handling.

    Example:
        client = OWKAIClient(
            api_key="owkai_...",
            base_url="https://pilot.owkai.app"
        )
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the OW-AI client.

        Args:
            api_key: Your OW-AI API key (or set OWKAI_API_KEY env var)
            base_url: API base URL (or set OWKAI_API_URL env var)
            timeout: Request timeout in seconds
            max_retries: Number of retries for failed requests
        """
        self.api_key = api_key or os.getenv("OWKAI_API_KEY")
        self.base_url = (base_url or os.getenv("OWKAI_API_URL", "https://pilot.owkai.app")).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("API key required. Set OWKAI_API_KEY or pass api_key parameter.")

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Set default headers
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "OWKAI-Python-SDK/1.0.0"
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Make an API request with error handling."""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or unauthorized access")

            if response.status_code == 403:
                raise AuthorizationError("Forbidden - insufficient permissions")

            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")

            if response.status_code == 422:
                error_detail = response.json().get("detail", "Validation error")
                raise ValidationError(error_detail)

            if response.status_code >= 500:
                raise ServerError(f"Server error: {response.status_code}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Failed to connect to {self.base_url}")

    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._request("POST", endpoint, data=data)

    def put(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return self._request("PUT", endpoint, data=data)

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self._request("DELETE", endpoint)

    # =========================================================================
    # AGENT REGISTRY OPERATIONS
    # =========================================================================

    def register_agent(self, config: AgentConfig) -> Dict[str, Any]:
        """
        Register a new agent with the governance platform.

        Args:
            config: Agent configuration

        Returns:
            Registration result with agent details
        """
        data = {
            "agent_id": config.agent_id,
            "display_name": config.display_name,
            "agent_type": config.agent_type,
            "default_risk_score": config.default_risk_score,
            "max_risk_threshold": config.max_risk_threshold,
            "auto_approve_below": config.auto_approve_below,
            "requires_mfa_above": config.requires_mfa_above,
            "allowed_action_types": config.allowed_action_types,
            "allowed_resources": config.allowed_resources,
            "blocked_resources": config.blocked_resources,
            "alert_on_high_risk": config.alert_on_high_risk,
            "tags": config.tags,
            "metadata": config.metadata
        }

        return self.post("/api/registry/agents", data=data)

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details by ID."""
        return self.get(f"/api/registry/agents/{agent_id}")

    def list_agents(
        self,
        status_filter: str = None,
        type_filter: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List all registered agents."""
        params = {"limit": limit, "offset": offset}
        if status_filter:
            params["status_filter"] = status_filter
        if type_filter:
            params["type_filter"] = type_filter

        return self.get("/api/registry/agents", params=params)

    def activate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Activate an agent for production use (admin only)."""
        return self.post(f"/api/registry/agents/{agent_id}/activate")

    def suspend_agent(self, agent_id: str, reason: str = None) -> Dict[str, Any]:
        """Suspend an agent (admin only)."""
        params = {"reason": reason} if reason else None
        return self.post(f"/api/registry/agents/{agent_id}/suspend", data=params)

    # =========================================================================
    # ACTION SUBMISSION
    # =========================================================================

    def submit_action(
        self,
        agent_id: str,
        action_type: str,
        description: str,
        risk_score: int = None,
        resource: str = None,
        metadata: Dict = None
    ) -> ActionResult:
        """
        Submit an agent action for authorization.

        Args:
            agent_id: The registered agent ID
            action_type: Type of action (e.g., "transaction", "data_access")
            description: Human-readable description
            risk_score: Optional risk score override (0-100)
            resource: Target resource being accessed
            metadata: Additional context

        Returns:
            ActionResult with status and approval information
        """
        data = {
            "agent_id": agent_id,
            "action_type": action_type,
            "description": description,
            "resource": resource or "unknown",
            "metadata": metadata or {}
        }

        if risk_score is not None:
            data["risk_score"] = max(0, min(100, risk_score))

        result = self.post("/api/sdk/agent-action", data=data)

        return ActionResult(
            action_id=result.get("id") or result.get("action_id"),
            status=ActionStatus(result.get("status", "pending")),
            risk_score=result.get("risk_score", 50),
            risk_level=RiskLevel(result.get("risk_level", "medium")),
            requires_approval=result.get("requires_approval", True),
            approved=result.get("approved", False),
            alert_generated=result.get("alert_generated", False),
            alert_id=result.get("alert_id"),
            poll_url=result.get("poll_url"),
            metadata=result
        )

    def get_action_status(self, action_id: int) -> Dict[str, Any]:
        """Get the current status of an action."""
        return self.get(f"/api/agent-action/status/{action_id}")

    def wait_for_approval(
        self,
        action_id: int,
        timeout: int = 300,
        poll_interval: int = 5,
        callback: Callable[[Dict], None] = None
    ) -> ActionResult:
        """
        Wait for an action to be approved or rejected.

        Args:
            action_id: The action ID to wait for
            timeout: Maximum seconds to wait
            poll_interval: Seconds between status checks
            callback: Optional callback for status updates

        Returns:
            Final ActionResult
        """
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            result = self.get_action_status(action_id)

            if callback:
                callback(result)

            status = result.get("status", "pending")

            if status == "approved":
                return ActionResult(
                    action_id=action_id,
                    status=ActionStatus.APPROVED,
                    risk_score=result.get("risk_score", 50),
                    risk_level=RiskLevel(result.get("risk_level", "medium")),
                    requires_approval=True,
                    approved=True,
                    metadata=result
                )

            if status == "rejected":
                return ActionResult(
                    action_id=action_id,
                    status=ActionStatus.REJECTED,
                    risk_score=result.get("risk_score", 50),
                    risk_level=RiskLevel(result.get("risk_level", "medium")),
                    requires_approval=True,
                    approved=False,
                    error="Action was rejected",
                    metadata=result
                )

            time.sleep(poll_interval)

        return ActionResult(
            action_id=action_id,
            status=ActionStatus.EXPIRED,
            risk_score=0,
            risk_level=RiskLevel.MEDIUM,
            requires_approval=True,
            approved=False,
            error=f"Approval timeout after {timeout}s"
        )

    # =========================================================================
    # POLICY OPERATIONS
    # =========================================================================

    def add_policy(
        self,
        agent_id: str,
        policy_name: str,
        policy_action: str,
        conditions: Dict = None,
        priority: int = 100
    ) -> Dict[str, Any]:
        """
        Add a policy to an agent.

        Args:
            agent_id: Target agent ID
            policy_name: Human-readable policy name
            policy_action: "require_approval", "block", "allow", "escalate"
            conditions: When policy applies (e.g., {"action_type": "transaction"})
            priority: Lower = higher priority (default 100)
        """
        data = {
            "policy_name": policy_name,
            "policy_action": policy_action,
            "conditions": conditions or {},
            "priority": priority
        }

        return self.post(f"/api/registry/agents/{agent_id}/policies", data=data)

    def evaluate_policy(
        self,
        agent_id: str,
        action_type: str,
        resource: str = None,
        risk_score: int = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Evaluate policies for a proposed action (dry-run).

        Use this to test policy configuration before submitting real actions.
        """
        data = {
            "action_type": action_type,
            "resource": resource,
            "risk_score": risk_score,
            "metadata": metadata or {}
        }

        return self.post(f"/api/registry/agents/{agent_id}/evaluate", data=data)


class AuthorizedAgent:
    """
    Authorized Agent Wrapper

    Provides a high-level interface for AI agents to interact with OW-AI governance.

    Example:
        agent = AuthorizedAgent(
            client=client,
            agent_id="my-agent-001",
            display_name="My AI Agent"
        )

        # Register (idempotent)
        agent.register()

        # Submit action
        result = agent.request_permission(
            action_type="data_access",
            description="Reading customer records",
            resource="customer_database"
        )

        if result.can_proceed:
            # Execute action
            pass
    """

    def __init__(
        self,
        client: OWKAIClient,
        agent_id: str,
        display_name: str = None,
        agent_type: str = "supervised",
        auto_approve_below: int = 30,
        max_risk_threshold: int = 80
    ):
        """
        Initialize an authorized agent.

        Args:
            client: OWKAIClient instance
            agent_id: Unique agent identifier
            display_name: Human-readable name
            agent_type: "autonomous", "supervised", "advisory", "mcp_server"
            auto_approve_below: Risk score below which actions auto-approve
            max_risk_threshold: Max risk score allowed without escalation
        """
        self.client = client
        self.agent_id = agent_id
        self.display_name = display_name or agent_id
        self.agent_type = agent_type
        self.auto_approve_below = auto_approve_below
        self.max_risk_threshold = max_risk_threshold
        self._registered = False
        self._config = None

    def register(
        self,
        allowed_action_types: List[str] = None,
        allowed_resources: List[str] = None,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Register this agent with OW-AI governance (idempotent).

        Returns:
            Registration result
        """
        config = AgentConfig(
            agent_id=self.agent_id,
            display_name=self.display_name,
            agent_type=self.agent_type,
            auto_approve_below=self.auto_approve_below,
            max_risk_threshold=self.max_risk_threshold,
            allowed_action_types=allowed_action_types or [],
            allowed_resources=allowed_resources or [],
            tags=tags or [],
            metadata=metadata or {}
        )

        result = self.client.register_agent(config)
        self._registered = True
        self._config = result.get("agent", {})

        logger.info(f"Agent registered: {self.agent_id} (status: {self._config.get('status')})")
        return result

    def request_permission(
        self,
        action_type: str,
        description: str,
        risk_score: int = None,
        resource: str = None,
        metadata: Dict = None,
        wait_for_approval: bool = False,
        timeout: int = 300
    ) -> ActionResult:
        """
        Request permission to perform an action.

        This is the primary method for AI agents to interact with OW-AI governance.

        Args:
            action_type: Type of action (e.g., "transaction", "data_access", "api_call")
            description: Human-readable description of what the agent wants to do
            risk_score: Optional risk score override (0-100)
            resource: Target resource being accessed
            metadata: Additional context for the action
            wait_for_approval: If True, block until approved/rejected
            timeout: Timeout for waiting (seconds)

        Returns:
            ActionResult with approval status

        Example:
            result = agent.request_permission(
                action_type="transaction",
                description="Transfer $5,000 to vendor account",
                risk_score=65,
                resource="payment_gateway",
                metadata={"amount": 5000, "vendor_id": "V123"}
            )

            if result.can_proceed:
                process_payment(result.action_id)
            elif result.is_pending:
                # Notify user that approval is needed
                notify_pending_approval(result.action_id)
        """
        result = self.client.submit_action(
            agent_id=self.agent_id,
            action_type=action_type,
            description=description,
            risk_score=risk_score,
            resource=resource,
            metadata=metadata
        )

        if wait_for_approval and result.is_pending:
            result = self.client.wait_for_approval(
                action_id=result.action_id,
                timeout=timeout
            )

        return result

    def add_policy(
        self,
        policy_name: str,
        policy_action: str,
        conditions: Dict = None,
        priority: int = 100
    ) -> Dict[str, Any]:
        """Add a policy to this agent."""
        return self.client.add_policy(
            agent_id=self.agent_id,
            policy_name=policy_name,
            policy_action=policy_action,
            conditions=conditions,
            priority=priority
        )

    def evaluate(
        self,
        action_type: str,
        resource: str = None,
        risk_score: int = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Evaluate policies for a proposed action (dry-run)."""
        return self.client.evaluate_policy(
            agent_id=self.agent_id,
            action_type=action_type,
            resource=resource,
            risk_score=risk_score,
            metadata=metadata
        )


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class OWKAIError(Exception):
    """Base exception for OW-AI SDK errors."""
    pass


class AuthenticationError(OWKAIError):
    """Invalid or missing API key."""
    pass


class AuthorizationError(OWKAIError):
    """Insufficient permissions."""
    pass


class NotFoundError(OWKAIError):
    """Resource not found."""
    pass


class ValidationError(OWKAIError):
    """Invalid request data."""
    pass


class ServerError(OWKAIError):
    """Server-side error."""
    pass


class ApprovalTimeoutError(OWKAIError):
    """Approval request timed out."""
    pass


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_client(
    api_key: str = None,
    base_url: str = None
) -> OWKAIClient:
    """
    Create and return an OW-AI client.

    Uses environment variables if parameters not provided:
    - OWKAI_API_KEY
    - OWKAI_API_URL

    Example:
        client = create_client()
        agent = AuthorizedAgent(client, "my-agent")
    """
    return OWKAIClient(api_key=api_key, base_url=base_url)


def quick_agent(
    agent_id: str,
    api_key: str = None,
    base_url: str = None
) -> AuthorizedAgent:
    """
    Quick helper to create an authorized agent.

    Example:
        agent = quick_agent("my-agent-001")
        result = agent.request_permission("data_access", "Reading config")
    """
    client = create_client(api_key=api_key, base_url=base_url)
    return AuthorizedAgent(client=client, agent_id=agent_id)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Financial Advisor Agent
    print("OW-AI Enterprise SDK - Example Usage")
    print("=" * 50)

    # Initialize client (uses OWKAI_API_KEY and OWKAI_API_URL env vars)
    client = OWKAIClient(
        api_key=os.getenv("OWKAI_API_KEY", "your-api-key-here"),
        base_url=os.getenv("OWKAI_API_URL", "https://pilot.owkai.app")
    )

    # Create and register an agent
    agent = AuthorizedAgent(
        client=client,
        agent_id="example-financial-advisor",
        display_name="Example Financial Advisor",
        agent_type="supervised",
        auto_approve_below=30,
        max_risk_threshold=80
    )

    print(f"\nRegistering agent: {agent.agent_id}")
    try:
        result = agent.register(
            allowed_action_types=["query", "recommendation", "transaction"],
            allowed_resources=["portfolio_db", "trading_system"],
            tags=["finance", "example"]
        )
        print(f"  Status: {result.get('message')}")
    except Exception as e:
        print(f"  Registration failed: {e}")

    # Submit a low-risk action (should auto-approve)
    print("\nSubmitting low-risk action...")
    try:
        result = agent.request_permission(
            action_type="query",
            description="Retrieving account summary",
            risk_score=15,
            resource="portfolio_db"
        )
        print(f"  Action ID: {result.action_id}")
        print(f"  Status: {result.status.value}")
        print(f"  Approved: {result.approved}")
    except Exception as e:
        print(f"  Submission failed: {e}")

    # Submit a high-risk action (requires approval)
    print("\nSubmitting high-risk action...")
    try:
        result = agent.request_permission(
            action_type="transaction",
            description="Executing stock purchase order",
            risk_score=72,
            resource="trading_system",
            metadata={
                "symbol": "AAPL",
                "shares": 100,
                "estimated_value": 19000
            }
        )
        print(f"  Action ID: {result.action_id}")
        print(f"  Status: {result.status.value}")
        print(f"  Risk Level: {result.risk_level.value}")
        print(f"  Requires Approval: {result.requires_approval}")
        print(f"  Alert Generated: {result.alert_generated}")
        if result.alert_id:
            print(f"  Alert ID: {result.alert_id}")
    except Exception as e:
        print(f"  Submission failed: {e}")

    print("\n" + "=" * 50)
    print("Example complete!")
