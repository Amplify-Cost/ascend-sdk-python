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

    This is the primary model for submitting actions to Ascend.

    Example:
        action = AgentAction(
            agent_id="financial-bot-001",
            agent_name="Financial Advisor",
            action_type="transaction",
            resource="customer_account",
            resource_id="ACC-12345",
            action_details={"amount": 50000, "currency": "USD"},
            risk_indicators={"amount_threshold": "exceeded"}
        )
    """

    agent_id: str
    agent_name: str
    action_type: str
    resource: str
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
