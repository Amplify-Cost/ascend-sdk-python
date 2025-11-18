"""
🏢 Enterprise Playbook Schemas
Pydantic models for playbook creation, validation, and API contracts

Author: Donald King (OW-kai Enterprise)
Version: 1.0.0
Date: 2025-11-18
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Supported playbook action types"""
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate_approval"
    NOTIFY = "notify"
    STAKEHOLDER_NOTIFICATION = "stakeholder_notification"
    QUARANTINE = "temporary_quarantine"
    RISK_ASSESSMENT = "risk_assessment"
    LOG = "log"
    WEBHOOK = "webhook"


class EscalationLevel(str, Enum):
    """Approval escalation levels"""
    L1 = "L1"  # Team Lead
    L2 = "L2"  # Manager
    L3 = "L3"  # Director
    L4 = "L4"  # VP/Executive


class Environment(str, Enum):
    """Target environments for playbook triggers"""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    ALL = "all"


# ============================================================================
# TRIGGER CONDITION MODELS
# ============================================================================

class RiskScoreRange(BaseModel):
    """Risk score threshold configuration"""
    min: Optional[int] = Field(None, ge=0, le=100, description="Minimum risk score (inclusive)")
    max: Optional[int] = Field(None, ge=0, le=100, description="Maximum risk score (inclusive)")

    @model_validator(mode='after')
    def validate_range(self):
        """Ensure min <= max"""
        if self.min is not None and self.max is not None:
            if self.min > self.max:
                raise ValueError('min must be <= max')
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "min": 0,
                "max": 40
            }
        }


class TimeRange(BaseModel):
    """Time-of-day range configuration"""
    start: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Start time (HH:MM)")
    end: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="End time (HH:MM)")

    class Config:
        json_schema_extra = {
            "example": {
                "start": "09:00",
                "end": "17:00"
            }
        }


class TriggerConditions(BaseModel):
    """
    Enterprise trigger conditions for playbook matching

    ALL specified conditions must match for playbook to trigger.
    Omitted conditions are ignored (not evaluated).
    """
    risk_score: Optional[RiskScoreRange] = Field(
        None,
        description="Risk score range (0-100)"
    )

    # Legacy field names for backward compatibility
    risk_score_min: Optional[int] = Field(None, ge=0, le=100, description="[DEPRECATED] Use risk_score.min")
    risk_score_max: Optional[int] = Field(None, ge=0, le=100, description="[DEPRECATED] Use risk_score.max")

    action_type: Optional[List[str]] = Field(
        None,
        min_items=1,
        description="List of action types that trigger this playbook"
    )

    # Legacy field name for backward compatibility
    action_types: Optional[List[str]] = Field(None, description="[DEPRECATED] Use action_type")

    environment: Optional[List[Environment]] = Field(
        None,
        min_items=1,
        description="Target environments (production, staging, development)"
    )

    agent_id: Optional[List[str]] = Field(
        None,
        min_items=1,
        description="Specific agent IDs to match"
    )

    business_hours: Optional[bool] = Field(
        None,
        description="Trigger only during business hours (9am-5pm EST, Mon-Fri)"
    )

    weekend: Optional[bool] = Field(
        None,
        description="Trigger only on weekends (Sat-Sun)"
    )

    time_range: Optional[TimeRange] = Field(
        None,
        description="Specific time range for triggering (24-hour format)"
    )

    @model_validator(mode='after')
    def migrate_legacy_fields(self):
        """Migrate legacy field names to new structure"""
        # Migrate risk_score_min/max to risk_score
        if self.risk_score_min or self.risk_score_max:
            if not self.risk_score:
                self.risk_score = RiskScoreRange(
                    min=self.risk_score_min,
                    max=self.risk_score_max
                )

        # Migrate action_types to action_type
        if self.action_types and not self.action_type:
            self.action_type = self.action_types

        # Validate business_hours and weekend are not both True
        if self.business_hours is True and self.weekend is True:
            raise ValueError('Cannot have both business_hours and weekend set to True')

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "risk_score": {
                    "min": 0,
                    "max": 40
                },
                "action_type": ["database_read", "file_read"],
                "environment": ["production"],
                "business_hours": True
            }
        }


# ============================================================================
# ACTION PARAMETER MODELS
# ============================================================================

class NotifyParameters(BaseModel):
    """Parameters for notify/stakeholder_notification action"""
    recipients: List[str] = Field(
        ...,
        min_items=1,
        description="Email addresses to notify"
    )
    subject: Optional[str] = Field(None, description="Email subject")
    template: Optional[str] = Field(None, description="Email template ID")

    @field_validator('recipients')
    @classmethod
    def validate_emails(cls, v):
        """Basic email validation"""
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in v:
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email address: {email}')
        return v


class EscalateParameters(BaseModel):
    """Parameters for escalate_approval action"""
    level: EscalationLevel = Field(..., description="Escalation level (L1-L4)")
    reason: Optional[str] = Field(None, description="Escalation reason")
    assignee: Optional[str] = Field(None, description="Specific assignee email")


class QuarantineParameters(BaseModel):
    """Parameters for temporary_quarantine action"""
    duration_minutes: int = Field(..., ge=1, le=1440, description="Quarantine duration (1-1440 minutes)")
    reason: Optional[str] = Field(None, description="Quarantine reason")


class RiskAssessmentParameters(BaseModel):
    """Parameters for risk_assessment action"""
    deep_scan: bool = Field(False, description="Perform deep security scan")
    include_context: bool = Field(True, description="Include action context")


class WebhookParameters(BaseModel):
    """Parameters for webhook action"""
    url: str = Field(..., description="Webhook URL")
    method: str = Field("POST", pattern="^(GET|POST|PUT)$", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")


class PlaybookAction(BaseModel):
    """
    Single automated action within a playbook

    Each action type requires specific parameters.
    Actions are executed in order when playbook triggers.
    """
    type: ActionType = Field(..., description="Action type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    enabled: bool = Field(True, description="Whether this action is enabled")
    order: Optional[int] = Field(None, description="Execution order (optional)")

    @model_validator(mode='after')
    def validate_parameters(self):
        """Validate parameters based on action type"""
        if self.type == ActionType.NOTIFY or self.type == ActionType.STAKEHOLDER_NOTIFICATION:
            if 'recipients' not in self.parameters:
                raise ValueError('notify action requires "recipients" parameter')
            NotifyParameters(**self.parameters)  # Validate structure

        elif self.type == ActionType.ESCALATE:
            if 'level' not in self.parameters:
                raise ValueError('escalate action requires "level" parameter')
            EscalateParameters(**self.parameters)  # Validate structure

        elif self.type == ActionType.QUARANTINE:
            if 'duration_minutes' not in self.parameters:
                raise ValueError('quarantine action requires "duration_minutes" parameter')
            QuarantineParameters(**self.parameters)  # Validate structure

        elif self.type == ActionType.RISK_ASSESSMENT:
            if self.parameters:
                RiskAssessmentParameters(**self.parameters)  # Validate structure

        elif self.type == ActionType.WEBHOOK:
            if 'url' not in self.parameters:
                raise ValueError('webhook action requires "url" parameter')
            WebhookParameters(**self.parameters)  # Validate structure

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "type": "notify",
                "parameters": {
                    "recipients": ["security@company.com", "ops@company.com"],
                    "subject": "Low-risk action auto-approved"
                },
                "enabled": True
            }
        }


# ============================================================================
# PLAYBOOK CRUD MODELS
# ============================================================================

class PlaybookBase(BaseModel):
    """Base playbook fields (shared between create/update)"""
    name: str = Field(..., min_length=3, max_length=255, description="Playbook name")
    description: Optional[str] = Field(None, max_length=2000, description="Playbook description")
    status: str = Field("active", pattern="^(active|inactive|maintenance)$", description="Playbook status")
    risk_level: str = Field(
        ...,
        pattern="^(low|medium|high|critical)$",
        description="Target risk level for this playbook"
    )
    approval_required: bool = Field(
        False,
        description="Whether manual approval is required after playbook execution"
    )


class PlaybookCreate(PlaybookBase):
    """
    Enterprise playbook creation model

    Validates all fields and ensures trigger conditions and actions are properly configured.
    """
    id: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-z0-9-]+$",
        description="Unique playbook ID (lowercase, numbers, hyphens only)"
    )

    trigger_conditions: TriggerConditions = Field(
        ...,
        description="Conditions that trigger this playbook"
    )

    actions: List[PlaybookAction] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Automated actions to execute (1-10 actions)"
    )

    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v):
        """Ensure ID follows naming convention"""
        if not v.startswith('pb-'):
            raise ValueError('Playbook ID must start with "pb-"')
        if len(v) < 5:
            raise ValueError('Playbook ID must be at least 5 characters (e.g., "pb-01")')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "pb-low-risk-auto",
                "name": "Auto-Approve Low Risk Actions",
                "description": "Automatically approve low-risk read operations during business hours",
                "status": "active",
                "risk_level": "low",
                "approval_required": False,
                "trigger_conditions": {
                    "risk_score": {
                        "min": 0,
                        "max": 40
                    },
                    "action_type": ["database_read", "file_read"],
                    "business_hours": True
                },
                "actions": [
                    {
                        "type": "approve",
                        "parameters": {},
                        "enabled": True
                    },
                    {
                        "type": "notify",
                        "parameters": {
                            "recipients": ["ops@company.com"],
                            "subject": "Low-risk action auto-approved"
                        },
                        "enabled": True
                    }
                ]
            }
        }


class PlaybookUpdate(BaseModel):
    """Playbook update model (all fields optional)"""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None, pattern="^(active|inactive|maintenance)$")
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    approval_required: Optional[bool] = None
    trigger_conditions: Optional[TriggerConditions] = None
    actions: Optional[List[PlaybookAction]] = Field(None, min_items=1, max_items=10)


class PlaybookResponse(PlaybookBase):
    """Playbook response model (what API returns)"""
    id: str
    trigger_conditions: Optional[Dict] = None
    actions: Optional[List[Dict]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    execution_count: int = 0
    success_rate: float = 0.0
    last_executed: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "pb-low-risk-auto",
                "name": "Auto-Approve Low Risk Actions",
                "description": "Automatically approve low-risk read operations",
                "status": "active",
                "risk_level": "low",
                "approval_required": False,
                "trigger_conditions": {
                    "risk_score": {"min": 0, "max": 40},
                    "action_type": ["database_read", "file_read"]
                },
                "actions": [
                    {"type": "approve", "parameters": {}}
                ],
                "created_by": 7,
                "created_at": "2025-11-18T10:00:00Z",
                "updated_at": "2025-11-18T10:00:00Z",
                "execution_count": 15,
                "success_rate": 98.5,
                "last_executed": "2025-11-18T14:30:00Z"
            }
        }


# ============================================================================
# TESTING MODELS
# ============================================================================

class PlaybookTestRequest(BaseModel):
    """Request model for testing playbook against data"""
    test_data: Dict[str, Any] = Field(..., description="Test action data")

    class Config:
        json_schema_extra = {
            "example": {
                "test_data": {
                    "risk_score": 35,
                    "action_type": "database_read",
                    "agent_id": "analytics-agent",
                    "timestamp": "2025-11-18T14:00:00Z"
                }
            }
        }


class PlaybookTestResponse(BaseModel):
    """Response model for playbook testing"""
    matches: bool = Field(..., description="Whether test data matches trigger conditions")
    playbook_id: str
    playbook_name: str
    test_data: Dict[str, Any]
    matched_conditions: List[str] = Field(default_factory=list, description="Conditions that matched")
    failed_conditions: List[str] = Field(default_factory=list, description="Conditions that didn't match")
    would_execute_actions: List[str] = Field(default_factory=list, description="Actions that would execute")


# ============================================================================
# TEMPLATE MODELS
# ============================================================================

class PlaybookTemplate(BaseModel):
    """Pre-built playbook template"""
    id: str
    name: str
    description: str
    category: str = Field(..., pattern="^(productivity|security|compliance|cost_optimization)$")
    use_case: str
    trigger_conditions: TriggerConditions
    actions: List[PlaybookAction]
    estimated_savings_per_month: Optional[float] = None
    complexity: str = Field("medium", pattern="^(low|medium|high)$")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "template-low-risk-auto",
                "name": "Auto-Approve Low Risk",
                "description": "Automatically approve low-risk read operations",
                "category": "productivity",
                "use_case": "Reduce manual approvals for safe, read-only operations",
                "trigger_conditions": {
                    "risk_score": {"min": 0, "max": 40},
                    "action_type": ["database_read", "file_read"]
                },
                "actions": [
                    {"type": "approve", "parameters": {}}
                ],
                "estimated_savings_per_month": 2250.0,
                "complexity": "low"
            }
        }
