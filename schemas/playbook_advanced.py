"""
🏢 ENTERPRISE PLAYBOOK ADVANCED SCHEMAS

Phase 3: Versioning, Analytics, Scheduling, and Templates

Author: Donald King (OW-kai Enterprise)
Date: 2025-11-18
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ChangeType(str, Enum):
    """Type of playbook change"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    ROLLBACK = "ROLLBACK"
    CLONE = "CLONE"


class ExecutionMode(str, Enum):
    """How playbook was executed"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    DRY_RUN = "dry_run"


class ScheduleType(str, Enum):
    """Type of schedule"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    EVENT_BASED = "event_based"


class TemplateCategory(str, Enum):
    """Template category"""
    PRODUCTIVITY = "productivity"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    COST_OPTIMIZATION = "cost_optimization"


# ============================================================================
# PLAYBOOK VERSIONING SCHEMAS
# ============================================================================

class PlaybookVersionCreate(BaseModel):
    """Create new playbook version"""
    playbook_id: str = Field(..., description="Parent playbook ID")
    version_tag: Optional[str] = Field(None, description="Optional version tag (e.g., 'v1.0', 'stable')")
    change_summary: str = Field(..., description="Human-readable change description", min_length=10)
    change_type: ChangeType = Field(default=ChangeType.UPDATE)

    # Full playbook snapshot
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    status: str = Field(default="active")
    risk_level: str = Field(default="medium")
    approval_required: bool = Field(default=False)
    trigger_conditions: Dict[str, Any] = Field(...)
    actions: List[Dict[str, Any]] = Field(..., min_items=1)

    class Config:
        json_schema_extra = {
            "example": {
                "playbook_id": "pb-001",
                "version_tag": "v1.1",
                "change_summary": "Added email notification for high-risk actions",
                "change_type": "UPDATE",
                "name": "Auto-Approve Low Risk",
                "trigger_conditions": {"risk_score": {"min": 0, "max": 40}},
                "actions": [{"type": "approve", "parameters": {}}]
            }
        }


class PlaybookVersionResponse(BaseModel):
    """Playbook version response"""
    id: int
    playbook_id: str
    version_number: int
    version_tag: Optional[str]
    is_current: bool

    name: str
    description: Optional[str]
    status: str
    risk_level: str
    approval_required: bool
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]

    change_summary: Optional[str]
    change_type: str
    changed_fields: List[str]

    created_by: Optional[int]
    created_at: datetime

    execution_count: int
    success_count: int
    failure_count: int

    class Config:
        from_attributes = True


class PlaybookRollbackRequest(BaseModel):
    """Request to rollback to a specific version"""
    version_id: int = Field(..., description="Version ID to rollback to")
    rollback_reason: str = Field(..., description="Reason for rollback", min_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "version_id": 42,
                "rollback_reason": "Version 43 caused 50% failure rate in production"
            }
        }


class PlaybookVersionComparison(BaseModel):
    """Comparison between two playbook versions"""
    version_a_id: int
    version_b_id: int
    version_a_number: int
    version_b_number: int

    differences: Dict[str, Any] = Field(..., description="Field-by-field differences")
    changed_trigger_conditions: bool
    changed_actions: bool
    action_changes_count: int

    performance_comparison: Dict[str, Any] = Field(..., description="Performance metrics comparison")


# ============================================================================
# EXECUTION ANALYTICS SCHEMAS
# ============================================================================

class ExecutionLogCreate(BaseModel):
    """Create execution log entry"""
    playbook_id: str
    playbook_version_id: Optional[int] = None
    execution_id: Optional[int] = None
    triggered_by_action_id: Optional[int] = None
    execution_mode: ExecutionMode = Field(default=ExecutionMode.AUTOMATIC)

    started_at: datetime
    input_snapshot: Dict[str, Any]

    class Config:
        json_schema_extra = {
            "example": {
                "playbook_id": "pb-001",
                "execution_mode": "automatic",
                "started_at": "2025-11-18T10:00:00Z",
                "input_snapshot": {"risk_score": 35, "action_type": "database_read"}
            }
        }


class ExecutionLogUpdate(BaseModel):
    """Update execution log with results"""
    completed_at: datetime
    duration_ms: int
    execution_status: str
    final_action: Optional[str] = None

    steps_executed: List[Dict[str, Any]]
    steps_total: int
    steps_successful: int
    steps_failed: int

    was_successful: bool
    error_message: Optional[str] = None
    output_result: Optional[Dict[str, Any]] = None
    cost_impact: Optional[float] = None


class ExecutionAnalytics(BaseModel):
    """Playbook execution analytics summary"""
    playbook_id: str
    playbook_name: str

    # Time range
    start_date: datetime
    end_date: datetime

    # Execution metrics
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate_percent: float

    # Performance metrics
    avg_duration_ms: float
    min_duration_ms: int
    max_duration_ms: int
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float

    # Business impact
    total_cost_savings: float
    total_actions_automated: int
    manual_approvals_avoided: int

    # Trends
    executions_by_day: List[Dict[str, Any]]
    success_rate_by_day: List[Dict[str, Any]]
    most_common_triggers: List[Dict[str, Any]]

    # Version performance
    version_performance: List[Dict[str, Any]]


class PlaybookPerformanceMetrics(BaseModel):
    """Real-time performance metrics for a playbook"""
    playbook_id: str
    current_version: int

    last_24h_executions: int
    last_24h_success_rate: float
    last_24h_avg_duration_ms: float

    last_7d_executions: int
    last_7d_success_rate: float
    last_7d_cost_savings: float

    trending_up: bool = Field(..., description="Is performance improving?")
    health_score: float = Field(..., ge=0, le=100, description="Overall health (0-100)")

    alerts: List[str] = Field(default_factory=list, description="Performance warnings")


# ============================================================================
# SCHEDULING SCHEMAS
# ============================================================================

class PlaybookScheduleCreate(BaseModel):
    """Create playbook schedule"""
    playbook_id: str
    schedule_name: str = Field(..., min_length=3, max_length=255)
    schedule_type: ScheduleType

    # Schedule configuration (one must be provided based on type)
    cron_expression: Optional[str] = Field(None, description="Cron expression for cron schedules")
    interval_minutes: Optional[int] = Field(None, ge=1, description="Interval in minutes")
    scheduled_for: Optional[datetime] = Field(None, description="Datetime for one-time execution")
    event_type: Optional[str] = Field(None, description="Event type for event-based schedules")
    event_conditions: Optional[Dict[str, Any]] = None

    # Execution window
    start_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field(default="UTC")

    # Limits
    max_executions: Optional[int] = Field(None, ge=1, description="Maximum number of executions")

    @model_validator(mode='after')
    def validate_schedule_config(self):
        """Validate schedule type has required configuration"""
        if self.schedule_type == ScheduleType.CRON and not self.cron_expression:
            raise ValueError("cron_expression required for CRON schedule type")
        if self.schedule_type == ScheduleType.INTERVAL and not self.interval_minutes:
            raise ValueError("interval_minutes required for INTERVAL schedule type")
        if self.schedule_type == ScheduleType.ONE_TIME and not self.scheduled_for:
            raise ValueError("scheduled_for required for ONE_TIME schedule type")
        if self.schedule_type == ScheduleType.EVENT_BASED and not self.event_type:
            raise ValueError("event_type required for EVENT_BASED schedule type")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "playbook_id": "pb-001",
                "schedule_name": "Daily Low-Risk Auto-Approval",
                "schedule_type": "cron",
                "cron_expression": "0 2 * * *",
                "timezone": "America/New_York"
            }
        }


class PlaybookScheduleResponse(BaseModel):
    """Playbook schedule response"""
    id: int
    playbook_id: str
    schedule_name: str
    schedule_type: str

    cron_expression: Optional[str]
    interval_minutes: Optional[int]
    scheduled_for: Optional[datetime]
    event_type: Optional[str]

    is_active: bool
    is_paused: bool

    last_executed_at: Optional[datetime]
    last_execution_status: Optional[str]
    next_execution_at: Optional[datetime]

    executions_remaining: Optional[int]

    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TEMPLATE SCHEMAS
# ============================================================================

class PlaybookTemplateExport(BaseModel):
    """Export playbook as template"""
    playbook_id: str
    template_name: str = Field(..., min_length=3, max_length=255)
    template_description: str = Field(..., min_length=10)
    category: TemplateCategory
    use_case: str = Field(..., min_length=20, description="Detailed use case description")
    complexity: str = Field(default="medium", pattern="^(low|medium|high)$")
    estimated_savings_per_month: Optional[float] = Field(None, ge=0)
    is_public: bool = Field(default=False, description="Make template public for all users")
    industry_tags: List[str] = Field(default_factory=list, max_items=5)

    class Config:
        json_schema_extra = {
            "example": {
                "playbook_id": "pb-001",
                "template_name": "Auto-Approve Low Risk Actions",
                "template_description": "Automatically approves low-risk actions during business hours",
                "category": "productivity",
                "use_case": "Reduce approval queue by 60% while maintaining security standards",
                "complexity": "low",
                "estimated_savings_per_month": 2250.0,
                "is_public": True,
                "industry_tags": ["fintech", "saas"]
            }
        }


class PlaybookTemplateImport(BaseModel):
    """Import template as new playbook"""
    template_id: str
    new_playbook_id: str = Field(..., pattern="^[a-zA-Z0-9_-]+$", description="Unique ID for new playbook")
    customize_name: Optional[str] = Field(None, min_length=3)
    customize_description: Optional[str] = None
    modify_trigger_conditions: Optional[Dict[str, Any]] = None
    modify_actions: Optional[List[Dict[str, Any]]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "template-auto-approve-low",
                "new_playbook_id": "pb-custom-001",
                "customize_name": "Custom Low Risk Auto-Approval"
            }
        }


class PlaybookTemplateResponse(BaseModel):
    """Template response"""
    id: str
    name: str
    description: str
    category: str

    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]

    complexity: str
    estimated_savings_per_month: Optional[float]
    use_case: str

    times_used: int
    success_rate: Optional[float]
    average_rating: Optional[float]

    is_public: bool
    is_verified: bool

    template_version: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PLAYBOOK CLONE SCHEMA
# ============================================================================

class PlaybookCloneRequest(BaseModel):
    """Clone existing playbook"""
    source_playbook_id: str
    new_playbook_id: str = Field(..., pattern="^[a-zA-Z0-9_-]+$")
    new_name: str = Field(..., min_length=3, max_length=255)
    new_description: Optional[str] = None
    include_execution_history: bool = Field(default=False, description="Copy execution stats")

    class Config:
        json_schema_extra = {
            "example": {
                "source_playbook_id": "pb-001",
                "new_playbook_id": "pb-001-staging",
                "new_name": "Auto-Approve Low Risk (Staging)",
                "include_execution_history": False
            }
        }
