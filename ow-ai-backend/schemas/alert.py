"""
Alert Schemas
Pydantic models for alert validation and serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class AlertCreate(BaseModel):
    """Schema for creating a new alert"""
    alert_type: str = Field(..., min_length=3, max_length=200)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    message: str = Field(..., min_length=10, max_length=1000)
    source: str = Field(default="system", max_length=100)
    agent_action_id: Optional[int] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "alert_type": "High Risk Agent Action",
                "severity": "high",
                "message": "High-risk action detected requiring review",
                "source": "orchestration_service",
                "agent_action_id": 123
            }
        }


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    status: Optional[str] = Field(None, pattern="^(new|investigating|resolved|dismissed|escalated)$")
    resolution_notes: Optional[str] = Field(None, max_length=1000)


class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    alert_type: str
    severity: str
    message: str
    status: str
    source: str
    timestamp: datetime
    agent_action_id: Optional[int]
    agent_id: Optional[str]
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Backward compatibility aliases
AlertOut = AlertResponse
