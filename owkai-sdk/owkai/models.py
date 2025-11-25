"""
OW-AI SDK Data Models

Enterprise-grade Pydantic models for request/response handling.
All models include comprehensive validation and serialization.

Compliance:
- Field validation prevents injection attacks
- Enum constraints ensure valid values
- Immutable configurations where appropriate
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """Risk level classification aligned with NIST standards."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    """Status of an agent action in the approval workflow."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXECUTION_FAILED = "execution_failed"
    EMERGENCY_APPROVED = "emergency_approved"


class ApprovalStatus(BaseModel):
    """
    Status of an action's approval workflow.

    Returned by get_action_status() and wait_for_approval().
    """

    action_id: int = Field(..., description="Unique action identifier")
    status: ActionStatus = Field(..., description="Current workflow status")
    approved: bool = Field(..., description="Whether action is approved")
    requires_approval: bool = Field(True, description="Whether approval is required")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    reviewed_by: Optional[str] = Field(None, description="Approver email")
    reviewed_at: Optional[datetime] = Field(None, description="Approval timestamp")
    comments: Optional[str] = Field(None, description="Approval/rejection comments")
    polling_interval_seconds: int = Field(30, description="Recommended polling interval")

    @property
    def is_final(self) -> bool:
        """Check if the action has reached a final state."""
        return self.status in (
            ActionStatus.APPROVED,
            ActionStatus.REJECTED,
            ActionStatus.EXECUTED,
            ActionStatus.EXECUTION_FAILED,
        )

    @property
    def is_successful(self) -> bool:
        """Check if the action was successfully approved/executed."""
        return self.status in (ActionStatus.APPROVED, ActionStatus.EXECUTED)


class ActionResult(BaseModel):
    """
    Result of submitting an agent action.

    Returned by execute_action() with initial risk assessment
    and workflow routing information.
    """

    action_id: int = Field(..., alias="id", description="Unique action identifier")
    agent_id: str = Field(..., description="Agent that submitted the action")
    action_type: str = Field(..., description="Type of action")
    status: ActionStatus = Field(..., description="Initial workflow status")
    risk_score: float = Field(..., ge=0, le=100, description="Calculated risk score")
    risk_level: RiskLevel = Field(..., description="Risk level classification")
    requires_approval: bool = Field(..., description="Whether manual approval needed")
    alert_triggered: bool = Field(False, description="Whether alert was generated")
    message: Optional[str] = Field(None, description="Processing message")

    # Enterprise metadata
    nist_control: Optional[str] = Field(None, description="NIST SP 800-53 control")
    mitre_tactic: Optional[str] = Field(None, description="MITRE ATT&CK tactic")
    mitre_technique: Optional[str] = Field(None, description="MITRE ATT&CK technique")
    cvss_score: Optional[float] = Field(None, ge=0, le=10, description="CVSS v3.1 score")
    cvss_severity: Optional[str] = Field(None, description="CVSS severity")

    model_config = {"populate_by_name": True}

    @property
    def polling_interval(self) -> int:
        """Recommended polling interval based on risk level."""
        if self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return 15  # Higher priority actions poll faster
        return 30


class ActionRequest(BaseModel):
    """
    Request to submit an agent action for authorization.

    All fields are validated before submission to ensure
    compliance with enterprise requirements.
    """

    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique identifier for the agent",
    )
    action_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of action (e.g., database_write, file_access)",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Detailed description of the action",
    )
    tool_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tool or service being used",
    )
    target_system: Optional[str] = Field(
        None,
        max_length=255,
        description="Target system (e.g., production-db)",
    )
    target_resource: Optional[str] = Field(
        None,
        max_length=1000,
        description="Specific resource being accessed",
    )
    risk_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for risk assessment",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Custom metadata for audit trail",
    )

    @field_validator("agent_id", "action_type", "tool_name")
    @classmethod
    def validate_no_special_chars(cls, v: str) -> str:
        """Prevent injection attacks via special characters."""
        forbidden = ["<", ">", "&", '"', "'", ";", "--", "/*"]
        for char in forbidden:
            if char in v:
                raise ValueError(f"Invalid character '{char}' in field")
        return v


class APIKeyInfo(BaseModel):
    """Information about an API key (masked)."""

    id: int = Field(..., description="Key ID")
    name: str = Field(..., description="User-friendly name")
    key_prefix: str = Field(..., description="Visible prefix (e.g., owkai_admin_a1b2)")
    is_active: bool = Field(..., description="Whether key is active")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    usage_count: int = Field(0, description="Total request count")
    created_at: datetime = Field(..., description="Creation timestamp")


class UsageStatistics(BaseModel):
    """API key usage statistics."""

    total_requests: int = Field(..., description="Total requests made")
    recent_requests: int = Field(..., description="Requests in current window")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate %")
    last_used_at: Optional[datetime] = Field(None, description="Last usage")
    recent_activity: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent request details",
    )


class HealthStatus(BaseModel):
    """API health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Check timestamp")
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Individual service statuses",
    )
