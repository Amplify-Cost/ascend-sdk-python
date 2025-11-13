"""
Action Schemas
Pydantic models for action validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ActionCreate(BaseModel):
    """Schema for creating a new action"""
    agent_id: str = Field(..., min_length=3, max_length=100)
    action_type: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    risk_level: Optional[str] = Field(default="medium", pattern="^(low|medium|high|critical)$")
    
    @validator('description')
    def validate_description(cls, v):
        dangerous = ['DROP TABLE', 'DELETE FROM', 'INSERT INTO', '--', '/*']
        if any(pattern.lower() in v.lower() for pattern in dangerous):
            raise ValueError('Description contains potentially dangerous content')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "agent-security-001",
                "action_type": "database_access",
                "description": "Accessing production database for security audit",
                "risk_level": "medium"
            }
        }


class ActionUpdate(BaseModel):
    """Schema for updating an action"""
    status: Optional[str] = Field(None, pattern="^(pending_approval|approved|denied|completed)$")
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")


class ActionResponse(BaseModel):
    """Schema for action response"""
    id: int
    agent_id: str
    action_type: str
    description: str
    status: str
    risk_score: Optional[float]
    risk_level: Optional[str]
    created_at: datetime
    created_by: Optional[str]  # Enterprise audit trail - email address

    # Option 4: Hybrid Layered Architecture fields
    policy_evaluated: Optional[bool] = Field(None, description="Whether policy engine evaluated this action")
    policy_decision: Optional[str] = Field(None, description="Policy engine decision: ALLOW, DENY, REQUIRE_APPROVAL")
    policy_risk_score: Optional[int] = Field(None, ge=0, le=100, description="Risk score from policy engine (0-100)")
    risk_fusion_formula: Optional[str] = Field(None, description="Formula showing how final risk score was calculated")

    class Config:
        from_attributes = True


# Alias for backward compatibility
AgentActionOut = ActionResponse

# Backward compatibility aliases
AgentActionCreate = ActionCreate
