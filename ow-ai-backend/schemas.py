from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

# ------------------------------
# User Schemas
# ------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# ------------------------------
# Auth Schemas
# ------------------------------

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ------------------------------
# AgentAction Schemas
# ------------------------------

class AgentActionBase(BaseModel):
    agent_id: str
    action_type: str
    description: Optional[str]
    tool_name: Optional[str]
    risk_level: Optional[str]
    rule_id: Optional[int]
    nist_control: Optional[str]
    nist_description: Optional[str]
    mitre_tactic: Optional[str]
    mitre_technique: Optional[str]
    recommendation: Optional[str]
    summary: Optional[str]
    status: Optional[str]
    is_false_positive: Optional[bool]
    approved: Optional[bool]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True

class AgentActionCreate(AgentActionBase):
    user_id: int
    timestamp: datetime

class AgentActionOut(AgentActionBase):
    id: int
    timestamp: datetime

# ------------------------------
# Alert Schemas
# ------------------------------

class AlertOut(BaseModel):
    id: int
    timestamp: datetime
    alert_type: str
    severity: str
    message: str

    # From related AgentAction
    agent_id: str
    tool_name: Optional[str]
    risk_level: Optional[str]
    mitre_tactic: Optional[str]
    mitre_technique: Optional[str]
    nist_control: Optional[str]
    nist_description: Optional[str]
    recommendation: Optional[str]

    class Config:
        from_attributes = True

# ------------------------------
# Rule Feedback Schemas
# ------------------------------

class RuleFeedbackRequest(BaseModel):
    rule_id: int
    correct: int = 0
    false_positive: int = 0

class RuleFeedbackResponse(BaseModel):
    message: str

# ------------------------------
# Smart Rule Generation
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
    id: int
    agent_id: str
    action_type: str
    description: str
    condition: str
    action: str
    risk_level: str
    recommendation: str
    justification: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

        # User Schemas with Security
# ------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    # Remove role field - only backend can assign roles
    
    @validator('email')
    def validate_email(cls, v):
        if len(v) > 254:  # RFC 5321 limit
            raise ValueError('Email address too long')
        return v.lower()  # Normalize email to lowercase
    
    @validator('password')
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
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# ------------------------------
# Auth Schemas with Security
# ------------------------------
class LoginInput(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()  # Normalize email

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# Add validation for all other schemas...
class AgentActionCreate(BaseModel):
    agent_id: str
    action_type: str
    description: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: datetime
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Agent ID cannot be empty')
        if len(v) > 100:
            raise ValueError('Agent ID too long')
        return v.strip()
    
    @validator('action_type') 
    def validate_action_type(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Action type cannot be empty')
        if len(v) > 100:
            raise ValueError('Action type too long')
        return v.strip()
    

# ------------------------------
# Automation & Workflow Schemas
# ------------------------------

class AutomationPlaybookBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    trigger_conditions: Optional[dict] = None
    success_rate: Optional[float] = 0.0
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Playbook name cannot be empty')
        if len(v) > 255:
            raise ValueError('Playbook name too long')
        return v.strip()

class AutomationPlaybookCreate(AutomationPlaybookBase):
    id: str
    created_by: Optional[str] = None
    
    @validator('id')
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
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class AutomationExecutionCreate(BaseModel):
    playbook_id: str
    execution_context: Optional[str] = "manual"
    input_data: Optional[dict] = None
    
    @validator('playbook_id')
    def validate_playbook_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Playbook ID cannot be empty')
        return v.strip()

class AutomationExecutionOut(BaseModel):
    id: int
    playbook_id: str
    executed_by: Optional[str] = None
    execution_status: str
    execution_details: Optional[dict] = None
    executed_at: datetime

    class Config:
        from_attributes = True

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: Optional[list] = None
    created_by: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow name cannot be empty')
        if len(v) > 255:
            raise ValueError('Workflow name too long')
        return v.strip()

class WorkflowCreate(WorkflowBase):
    id: str
    
    @validator('id')
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow ID cannot be empty')
        if len(v) > 255:
            raise ValueError('Workflow ID too long')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Workflow ID can only contain letters, numbers, underscores, and hyphens')
        return v.strip()

class WorkflowOut(WorkflowBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True

class WorkflowExecutionCreate(BaseModel):
    workflow_id: str
    input_data: Optional[dict] = None
    execution_context: Optional[str] = "manual"
    
    @validator('workflow_id')
    def validate_workflow_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Workflow ID cannot be empty')
        return v.strip()

class WorkflowExecutionOut(BaseModel):
    id: int
    workflow_id: str
    executed_by: Optional[str] = None
    execution_status: str
    execution_details: Optional[dict] = None
    executed_at: datetime

    class Config:
        from_attributes = True

# ------------------------------
# Authorization Schemas
# ------------------------------

class AuthorizationRequest(BaseModel):
    decision: str  # 'approved', 'denied', 'conditional_approved', 'escalated'
    notes: Optional[str] = None
    conditions: Optional[dict] = None
    approval_duration: Optional[int] = None  # minutes
    execute_immediately: bool = False
    
    @validator('decision')
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
    
    @validator('justification')
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


# Add to your schemas.py file

class WorkflowStepCreate(BaseModel):
    name: str
    type: str  # 'approval', 'automated', 'notification', 'escalation'
    timeout: int = 24
    conditions: Optional[dict] = None
    
    @validator('type')
    def validate_step_type(cls, v):
        allowed_types = ['approval', 'automated', 'notification', 'escalation']
        if v not in allowed_types:
            raise ValueError(f'Step type must be one of: {allowed_types}')
        return v

class WorkflowCreateRequest(BaseModel):
    workflow_id: str
    workflow_data: dict
    created_by: Optional[str] = None
    
    @validator('workflow_id')
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
    id: str
    name: str
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    status: str
    steps: list
    real_time_stats: Optional[dict] = None
    success_metrics: Optional[dict] = None
    
    class Config:
        from_attributes = True    