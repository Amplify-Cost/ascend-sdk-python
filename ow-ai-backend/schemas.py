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