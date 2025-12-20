"""
Ascend AI SDK Models
=====================

Data models for agent actions and API responses.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class AgentAction:
    """
    Represents an agent action requiring authorization.

    This is the primary model for submitting actions to the ASCEND governance platform.
    All fields marked as required must be provided; the backend will return HTTP 422
    if any required field is missing.

    Attributes:
        agent_id (str): Unique identifier for the AI agent (required).
            Must match a registered agent in your organization.
        agent_name (str): Human-readable name of the agent (required).
            Used for display in dashboards and audit logs.
        action_type (str): Category of action being performed (required).
            Standard types: data_access, data_modification, transaction,
            recommendation, communication, system_operation, query,
            file_access, api_call, database_operation.
        resource (str): Description of the resource being accessed (required).
            Maps to 'description' field in backend API.
        tool_name (str): Name of the tool/service being governed (required).
            Examples: "sql_client", "trading_api", "crm_api", "s3_client".
            Backend evidence: actions_v1_routes.py:287
        resource_id (str, optional): Unique identifier for the target resource.
        action_details (dict, optional): Additional action parameters.
        context (dict, optional): Execution context (environment, user info, etc.).
        risk_indicators (dict, optional): Pre-computed risk signals.

    Note:
        organization_id is NOT sent in the payload. Multi-tenant isolation
        is enforced by deriving org_id from the API key on the backend.
        This is a security requirement for SOC 2, PCI-DSS, HIPAA compliance.

    Example:
        action = AgentAction(
            agent_id="financial-bot-001",
            agent_name="Financial Advisor",
            action_type="transaction",
            resource="Process wire transfer for customer",
            tool_name="trading_api",
            resource_id="ACC-12345",
            action_details={"amount": 50000, "currency": "USD"},
            risk_indicators={"amount_threshold": "exceeded"}
        )
    """

    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    tool_name: str  # Required by backend (actions_v1_routes.py:287)
    resource_id: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    risk_indicators: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to API-compatible dictionary.

        Only includes non-None fields to keep payload minimal.
        """
        data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "description": self.resource,  # Map resource to description for API compatibility
            "tool_name": self.tool_name,  # Required by backend (actions_v1_routes.py:287)
        }

        if self.resource_id:
            data["resource_id"] = self.resource_id
        if self.action_details:
            data["action_details"] = self.action_details
        if self.context:
            data["context"] = self.context
        if self.risk_indicators:
            data["risk_indicators"] = self.risk_indicators

        return data

    def __repr__(self) -> str:
        return (
            f"AgentAction(agent_id={self.agent_id!r}, "
            f"action_type={self.action_type!r}, resource={self.resource!r})"
        )


@dataclass
class ActionResult:
    """
    Response from action submission or status check.

    Contains the authorization decision and metadata.

    Attributes:
        action_id: Unique identifier for this action
        status: Current status (pending, approved, denied, etc.)
        decision: Authorization decision (same as status for compatibility)
        risk_score: Calculated risk score (0-100)
        risk_level: Risk classification (low, medium, high, critical)
        reason: Human-readable explanation of decision
        policy_matched: Name of policy that made the decision
        timestamp: When the action was evaluated
        metadata: Additional response data
    """

    action_id: str
    status: str
    decision: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    reason: Optional[str] = None
    policy_matched: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionResult":
        """Create ActionResult from API response."""
        return cls(
            action_id=str(data.get("id", data.get("action_id", ""))),
            status=data.get("status", "unknown"),
            decision=data.get("decision", data.get("status")),
            risk_score=data.get("risk_score"),
            risk_level=data.get("risk_level"),
            reason=data.get("reason", data.get("summary")),
            policy_matched=data.get("policy_matched"),
            timestamp=data.get("timestamp", data.get("created_at")),
            metadata=data
        )

    def is_approved(self) -> bool:
        """Check if action was approved."""
        return self.status == "approved" or self.decision == "approved"

    def is_denied(self) -> bool:
        """Check if action was denied."""
        return self.status == "denied" or self.decision == "denied"

    def is_pending(self) -> bool:
        """Check if action is pending decision."""
        return self.status == "pending" or self.decision == "pending"

    def __repr__(self) -> str:
        return (
            f"ActionResult(action_id={self.action_id!r}, "
            f"status={self.status!r}, risk_level={self.risk_level!r})"
        )


@dataclass
class ListResult:
    """
    Response from list_actions API call.

    Contains paginated list of actions and metadata.
    """

    actions: List[ActionResult]
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ListResult":
        """Create ListResult from API response."""
        actions_data = data.get("actions", [])
        actions = [ActionResult.from_dict(a) for a in actions_data]

        return cls(
            actions=actions,
            total=data.get("total", len(actions)),
            limit=data.get("limit", 50),
            offset=data.get("offset", 0),
            has_more=data.get("has_more", False)
        )


@dataclass
class ConnectionStatus:
    """
    Response from connection test.

    Indicates whether API is reachable and authenticated.
    """

    status: str
    api_version: Optional[str] = None
    server_time: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None

    def is_connected(self) -> bool:
        """Check if connection is successful."""
        return self.status == "connected"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionStatus":
        """Create ConnectionStatus from API response."""
        return cls(
            status=data.get("status", "unknown"),
            api_version=data.get("api_version"),
            server_time=data.get("server_time"),
            error=data.get("error"),
            latency_ms=data.get("latency_ms")
        )
