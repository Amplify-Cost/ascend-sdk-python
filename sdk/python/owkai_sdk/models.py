"""
OW-AI SDK Data Models
=====================

Type-safe data models for API interactions.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class ActionType(str, Enum):
    """Supported action types for agent authorization."""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION = "transaction"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    SYSTEM_OPERATION = "system_operation"
    QUERY = "query"
    ANALYSIS = "analysis"
    REPORT_GENERATION = "report_generation"
    API_CALL = "api_call"


class DecisionStatus(str, Enum):
    """Authorization decision statuses (legacy)."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    REQUIRES_MODIFICATION = "requires_modification"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"
    ESCALATED = "escalated"


class Decision(str, Enum):
    """
    Authorization decision values (v2.0).

    Used by AscendClient.evaluate_action() response.
    """
    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING = "pending"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskIndicators:
    """Risk assessment indicators for an action."""
    pii_involved: bool = False
    financial_data: bool = False
    external_transfer: bool = False
    data_sensitivity: str = "low"
    amount_threshold: Optional[str] = None
    compliance_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-compatible dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ActionContext:
    """Contextual information for an action."""
    user_request: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-compatible dictionary."""
        result = {}
        if self.user_request:
            result["user_request"] = self.user_request
        if self.session_id:
            result["session_id"] = self.session_id
        if self.ip_address:
            result["ip_address"] = self.ip_address
        if self.user_agent:
            result["user_agent"] = self.user_agent
        if self.timestamp:
            result["timestamp"] = self.timestamp
        result.update(self.custom_fields)
        return result


@dataclass
class AgentAction:
    """
    Represents an agent action requiring authorization.

    This is the primary model for submitting actions to OW-AI.
    """
    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    resource_id: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    context: Optional[ActionContext] = None
    risk_indicators: Optional[RiskIndicators] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-compatible dictionary."""
        data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "resource": self.resource,
        }

        if self.resource_id:
            data["resource_id"] = self.resource_id
        if self.action_details:
            data["action_details"] = self.action_details
        if self.context:
            data["context"] = (
                self.context.to_dict()
                if isinstance(self.context, ActionContext)
                else self.context
            )
        if self.risk_indicators:
            data["risk_indicators"] = (
                self.risk_indicators.to_dict()
                if isinstance(self.risk_indicators, RiskIndicators)
                else self.risk_indicators
            )

        return data


@dataclass
class AuthorizationDecision:
    """
    Authorization decision response from ASCEND.

    Supports both v1.0 (legacy) and v2.0 response formats.
    v2.0 uses Decision enum (ALLOWED/DENIED/PENDING).
    """
    action_id: str
    decision: Decision  # v2.0: Decision enum
    risk_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    reason: Optional[str] = None
    policy_violations: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    approval_request_id: Optional[str] = None
    required_approvers: List[str] = field(default_factory=list)
    expires_at: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None
    execution_allowed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorizationDecision":
        """Create from API response dictionary (v2.0 format)."""
        # Map v1.0 status to v2.0 decision
        raw_decision = data.get("decision", data.get("status", "pending"))
        if raw_decision == "approved":
            decision = Decision.ALLOWED
        elif raw_decision == "denied":
            decision = Decision.DENIED
        elif raw_decision in ("allowed", "denied", "pending"):
            decision = Decision(raw_decision)
        else:
            decision = Decision.PENDING

        return cls(
            action_id=data.get("action_id", ""),
            decision=decision,
            risk_score=data.get("risk_score"),
            risk_level=RiskLevel(data["risk_level"]) if data.get("risk_level") else None,
            reason=data.get("reason"),
            policy_violations=data.get("policy_violations", []),
            conditions=data.get("conditions", []),
            approval_request_id=data.get("approval_request_id"),
            required_approvers=data.get("required_approvers", []),
            expires_at=data.get("expires_at"),
            approved_by=data.get("approved_by", data.get("reviewed_by")),
            approved_at=data.get("approved_at", data.get("reviewed_at")),
            comments=data.get("comments"),
            execution_allowed=data.get("execution_allowed", decision == Decision.ALLOWED),
            metadata=data.get("metadata", {})
        )


@dataclass
class ActionDetails:
    """Detailed information about an action."""
    action_id: str
    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    resource_id: Optional[str]
    status: DecisionStatus
    risk_score: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionDetails":
        """Create from API response dictionary."""
        return cls(
            action_id=str(data.get("id", data.get("action_id", ""))),
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", ""),
            action_type=data.get("action_type", ""),
            resource=data.get("resource", ""),
            resource_id=data.get("resource_id"),
            status=DecisionStatus(data.get("status", "pending")),
            risk_score=data.get("risk_score"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            audit_trail=data.get("audit_trail", [])
        )
