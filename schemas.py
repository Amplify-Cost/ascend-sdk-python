# schemas.py - Enterprise Security Compliant with Pydantic V2
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

# ------------------------------
# User Schemas - Enterprise Security
# ------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if len(v) > 254:  # RFC 5321 limit
            raise ValueError('Email address too long')
        return v.lower()  # Normalize email to lowercase
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    role: str
    created_at: datetime

# ------------------------------
# Auth Schemas - Enterprise Security
# ------------------------------
class LoginInput(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return v.lower()  # Normalize email

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ------------------------------
# AgentAction Schemas - Enterprise Security
# ------------------------------
class AgentActionBase(BaseModel):
    agent_id: str
    action_type: str
    description: Optional[str] = None
    tool_name: Optional[str] = None
    risk_level: Optional[str] = None
    rule_id: Optional[int] = None
    nist_control: Optional[str] = None
    nist_description: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    recommendation: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    is_false_positive: Optional[bool] = None
    approved: Optional[bool] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class AgentActionCreate(AgentActionBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    timestamp: datetime

    @field_validator('agent_id')
    @classmethod
    def validate_agent_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Agent ID cannot be empty')
        if len(v) > 100:
            raise ValueError('Agent ID too long')
        return v.strip()

    @field_validator('action_type')
    @classmethod
    def validate_action_type(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Action type cannot be empty')
        if len(v) > 100:
            raise ValueError('Action type too long')
        return v.strip()

class AgentActionOut(AgentActionBase):
    """Enterprise Agent Action Output Schema - All 32 Fields"""
    model_config = ConfigDict(from_attributes=True)

    # Primary key
    id: int
    timestamp: datetime

    # Risk Assessment (ARCH-001: CVSS v3.1)
    risk_score: Optional[float] = None              # 0-100 internal risk score
    cvss_score: Optional[float] = None              # 0.0-10.0 NIST CVSS score
    cvss_severity: Optional[str] = None             # NONE|LOW|MEDIUM|HIGH|CRITICAL
    cvss_vector: Optional[str] = None               # CVSS:3.1/AV:N/AC:L/PR:L/...

    # User & Authorization
    user_id: Optional[int] = None
    approved_by: Optional[str] = None
    requires_approval: Optional[bool] = None

    # Approval Levels
    approval_level: Optional[int] = None            # 1-5 (required approval tier)
    current_approval_level: Optional[int] = None    # 0-5 (approvals received so far)
    required_approval_level: Optional[int] = None   # 1-5 (total approvals needed)

    # Workflow
    workflow_id: Optional[str] = None
    workflow_execution_id: Optional[int] = None
    workflow_stage: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    pending_approvers: Optional[str] = None
    approval_chain: Optional[list] = None

    # Target Information
    target_system: Optional[str] = None
    target_resource: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional data
    extra_data: Optional[dict] = None

# ------------------------------
# Alert Schemas - Enterprise Security
# ------------------------------
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    alert_type: str
    severity: str
    message: str
    
    # From related AgentAction
    agent_id: str
    tool_name: Optional[str] = None
    risk_level: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    nist_control: Optional[str] = None
    nist_description: Optional[str] = None
    recommendation: Optional[str] = None

# ------------------------------
# Rule Feedback Schemas - Enterprise Security
# ------------------------------
class RuleFeedbackRequest(BaseModel):
    rule_id: int
    correct: int = 0
    false_positive: int = 0

class RuleFeedbackResponse(BaseModel):
    message: str

# ------------------------------
# Smart Rule Generation - Enterprise Security
# ------------------------------
class SmartRuleResponse(BaseModel):
    id: str
    agent_id: str
    action_type: str
    description: str
    condition: str
    action: str
    risk_level: str
    recommendation: str

class SmartRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    agent_id: str
    action_type: str
    description: str
    condition: str
    action: str
    risk_level: str
    recommendation: str
    justification: Optional[str] = None
    created_at: datetime

# ------------------------------
# Automation & Workflow Schemas - Enterprise Security
# ------------------------------
class AutomationPlaybookBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger_conditions: Optional[dict] = None
    success_rate: Optional[float] = 0.0
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Playbook name cannot be empty')
        if len(v) > 255:
            raise ValueError('Playbook name too long')
        return v.strip()

class AutomationPlaybookCreate(AutomationPlaybookBase):
    id: str
    created_by: Optional[str] = None
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Playbook ID cannot be empty')
        if len(v) > 255:
            raise ValueError('Playbook ID too long')
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Playbook ID can only contain letters, numbers, underscores, and hyphens')
        return v.strip()

class AutomationPlaybookOut(AutomationPlaybookBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class AutomationExecutionCreate(BaseModel):
    playbook_id: str
    execution_context: Optional[str] = "manual"
    input_data: Optional[dict] = None
    
    @field_validator('playbook_id')
    @classmethod
    def validate_playbook_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Playbook ID cannot be empty')
        return v.strip()

class AutomationExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    playbook_id: str
    executed_by: Optional[str] = None
    execution_status: str
    execution_details: Optional[dict] = None
    executed_at: datetime

# ------------------------------
# Workflow Schemas - Enterprise Security
# ------------------------------
class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: Optional[list] = None
    created_by: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow name cannot be empty')
        if len(v) > 255:
            raise ValueError('Workflow name too long')
        return v.strip()

class WorkflowCreate(WorkflowBase):
    id: str
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow ID cannot be empty')
        if len(v) > 255:
            raise ValueError('Workflow ID too long')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Workflow ID can only contain letters, numbers, underscores, and hyphens')
        return v.strip()

class WorkflowOut(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class WorkflowExecutionCreate(BaseModel):
    workflow_id: str
    input_data: Optional[dict] = None
    execution_context: Optional[str] = "manual"
    
    @field_validator('workflow_id')
    @classmethod
    def validate_workflow_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow ID cannot be empty')
        return v.strip()

class WorkflowExecutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    workflow_id: str
    executed_by: Optional[str] = None
    execution_status: str
    execution_details: Optional[dict] = None
    executed_at: datetime

class WorkflowStepCreate(BaseModel):
    name: str
    type: str  # 'approval', 'automated', 'notification', 'escalation'
    timeout: int = 24
    conditions: Optional[dict] = None
    
    @field_validator('type')
    @classmethod
    def validate_step_type(cls, v):
        allowed_types = ['approval', 'automated', 'notification', 'escalation']
        if v not in allowed_types:
            raise ValueError(f'Step type must be one of: {allowed_types}')
        return v

# ------------------------------
# Authorization Schemas - Enterprise Security
# ------------------------------
class AuthorizationRequest(BaseModel):
    decision: str  # 'approved', 'denied', 'conditional_approved', 'escalated'
    notes: Optional[str] = None
    conditions: Optional[dict] = None
    approval_duration: Optional[int] = None  # minutes
    execute_immediately: bool = False
    
    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        allowed_decisions = ['approved', 'denied', 'conditional_approved', 'escalated']
        if v not in allowed_decisions:
            raise ValueError(f'Decision must be one of: {allowed_decisions}')
        return v

class AuthorizationResponse(BaseModel):
    message: str
    execution_performed: bool = False
    execution_success: Optional[bool] = None
    execution_message: Optional[str] = None
    authorization_id: Optional[str] = None

class EmergencyOverrideRequest(BaseModel):
    justification: str
    
    @field_validator('justification')
    @classmethod
    def validate_justification(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Emergency justification must be at least 10 characters')
        if len(v) > 1000:
            raise ValueError('Emergency justification too long')
        return v.strip()

class EmergencyOverrideResponse(BaseModel):
    message: str
    override_id: str
    execution_performed: bool = False
    execution_success: Optional[bool] = None
    execution_message: Optional[str] = None

# ------------------------------
# Enterprise Workflow Schemas
# ------------------------------
class WorkflowCreateRequest(BaseModel):
    workflow_id: str
    workflow_data: dict
    created_by: Optional[str] = None
    
    @field_validator('workflow_id')
    @classmethod
    def validate_workflow_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow ID cannot be empty')
        if len(v) > 255:
            raise ValueError('Workflow ID too long')
        return v.strip()

class WorkflowExecutionRequest(BaseModel):
    input_data: Optional[dict] = None
    execution_context: Optional[str] = "manual"
    
class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    status: str
    steps: list
    real_time_stats: Optional[dict] = None
    success_metrics: Optional[dict] = None
class SmartRuleOutEnhanced(SmartRuleOut):
    """Extended model with performance metrics"""
    performance_score: Optional[int] = None
    triggers_last_24h: Optional[int] = None
    false_positives: Optional[int] = None
    effectiveness_rating: Optional[str] = None
    last_triggered: Optional[str] = None
