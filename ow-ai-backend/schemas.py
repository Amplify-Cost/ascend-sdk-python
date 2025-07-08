from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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