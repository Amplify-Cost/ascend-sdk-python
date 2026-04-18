"""
ASCEND SDK Data Models
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

    This is the primary model for submitting actions to ASCEND.

    SDK 2.3.0 / FEAT-007: Multi-agent orchestration fields.
        orchestration_session_id - groups related agent actions into a session
        parent_action_id - AgentAction.id on the ASCEND backend for the parent
                           step. Backend enforces cross-tenant scoping and
                           session-graft protection on submit.
        orchestration_depth - delegation depth (0-5). Server caps at 5.
    """
    agent_id: str
    agent_name: str
    action_type: str
    resource: str
    resource_id: Optional[str] = None
    action_details: Optional[Dict[str, Any]] = None
    context: Optional[ActionContext] = None
    risk_indicators: Optional[RiskIndicators] = None
    # SDK 2.3.0 orchestration linkage (optional; backend validates).
    orchestration_session_id: Optional[str] = None
    parent_action_id: Optional[int] = None
    orchestration_depth: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to API-compatible dictionary.

        PY-SEC-005: Strips risk_score/risk_level from outbound payloads.
        Risk scoring is server-side only — clients must never influence it.
        """
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

        # SDK 2.3.0: Orchestration pass-through fields (only when set).
        if self.orchestration_session_id is not None:
            data["orchestration_session_id"] = self.orchestration_session_id
        if self.parent_action_id is not None:
            data["parent_action_id"] = self.parent_action_id
        if self.orchestration_depth is not None:
            data["orchestration_depth"] = self.orchestration_depth

        # PY-SEC-005: Strip risk scoring fields from outbound payload
        data.pop("risk_score", None)
        data.pop("riskScore", None)
        data.pop("risk_level", None)

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


# =========================================================================
# Enterprise Dataclasses (v2.1.0)
# =========================================================================


@dataclass
class KillSwitchStatus:
    """Kill switch status from the ASCEND API."""
    active: bool
    reason: Optional[str] = None
    activated_at: Optional[str] = None
    activated_by: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KillSwitchStatus":
        return cls(
            active=data.get("active", data.get("is_active", False)),
            reason=data.get("reason"),
            activated_at=data.get("activated_at"),
            activated_by=data.get("activated_by"),
        )


@dataclass
class PolicyEvaluationResult:
    """Result of a real-time policy evaluation."""
    decision: str
    matched_policies: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    risk_score: Optional[int] = None
    evaluation_time_ms: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyEvaluationResult":
        return cls(
            decision=data.get("decision", "unknown"),
            matched_policies=data.get("matched_policies", []),
            violations=data.get("violations", []),
            risk_score=data.get("risk_score"),
            evaluation_time_ms=data.get("evaluation_time_ms"),
        )


@dataclass
class ResourceClassification:
    """Resource classification entry."""
    resource_id: str
    resource_type: str
    sensitivity_level: str
    compliance_tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceClassification":
        return cls(
            resource_id=data.get("resource_id", data.get("id", "")),
            resource_type=data.get("resource_type", ""),
            sensitivity_level=data.get("sensitivity_level", ""),
            compliance_tags=data.get("compliance_tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AuditEvent:
    """A single audit log event."""
    event_id: str
    event_type: str
    timestamp: str
    actor: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    outcome: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        return cls(
            event_id=data.get("event_id", data.get("id", "")),
            event_type=data.get("event_type", ""),
            timestamp=data.get("timestamp", ""),
            actor=data.get("actor"),
            resource=data.get("resource"),
            action=data.get("action"),
            outcome=data.get("outcome"),
            details=data.get("details", {}),
        )


@dataclass
class AuditLogResponse:
    """Paginated audit log response."""
    events: List[AuditEvent] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditLogResponse":
        events_data = data.get("events", data.get("logs", data.get("items", [])))
        return cls(
            events=[AuditEvent.from_dict(e) for e in events_data],
            total=data.get("total", len(events_data)),
            page=data.get("page", 1),
            page_size=data.get("page_size", data.get("limit", 50)),
        )


@dataclass
class AgentHealthStatus:
    """Health status of a registered agent."""
    agent_id: str
    status: str
    last_heartbeat: Optional[str] = None
    uptime_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentHealthStatus":
        return cls(
            agent_id=data.get("agent_id", ""),
            status=data.get("status", "unknown"),
            last_heartbeat=data.get("last_heartbeat"),
            uptime_seconds=data.get("uptime_seconds"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Webhook:
    """Webhook configuration."""
    webhook_id: str
    url: str
    events: List[str] = field(default_factory=list)
    active: bool = True
    secret: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        return cls(
            webhook_id=data.get("webhook_id", data.get("id", "")),
            url=data.get("url", ""),
            events=data.get("events", []),
            active=data.get("active", True),
            secret=data.get("secret"),
            created_at=data.get("created_at"),
        )


@dataclass
class WebhookTestResult:
    """Result of testing a webhook."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookTestResult":
        return cls(
            success=data.get("success", False),
            status_code=data.get("status_code"),
            response_time_ms=data.get("response_time_ms"),
            error=data.get("error"),
        )


@dataclass
class BulkActionResult:
    """Result for a single action within a bulk evaluation."""
    action_type: str
    resource: str
    decision: Optional[AuthorizationDecision] = None
    error: Optional[str] = None
    succeeded: bool = True


@dataclass
class BulkEvaluationResult:
    """Aggregate result from bulk action evaluation."""
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: List[BulkActionResult] = field(default_factory=list)
