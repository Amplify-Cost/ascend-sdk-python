"""
Workflow Schemas
Pydantic models for workflow validation and serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution response"""
    id: int
    workflow_id: str
    action_id: int
    executed_by: str
    execution_status: str
    current_stage: int
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    """Schema for approval decision"""
    decision: str = Field(..., pattern="^(approve|deny|escalate)$")
    comments: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "approve",
                "comments": "Action reviewed and approved for execution"
            }
        }


class WorkflowCreateRequest(BaseModel):
    """Schema for creating a new workflow"""
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    trigger_conditions: Optional[Dict] = None
    approval_stages: Optional[List[Dict]] = None
    status: str = Field(default="active", pattern="^(active|inactive|draft)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "High Risk Approval",
                "description": "Multi-stage approval for high-risk actions",
                "trigger_conditions": {"min_risk": 70, "max_risk": 100},
                "approval_stages": [
                    {"stage": 1, "approvers": ["manager"]},
                    {"stage": 2, "approvers": ["director"]}
                ]
            }
        }


class WorkflowExecutionRequest(BaseModel):
    """Schema for executing a workflow"""
    workflow_id: str
    action_id: int
    triggered_by: Optional[str] = "system"
    input_data: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow-001",
                "action_id": 123,
                "triggered_by": "orchestration_service",
                "input_data": {"risk_score": 85.0}
            }
        }


class AuthorizationRequest(BaseModel):
    """Schema for authorization/approval request"""
    action_id: int
    requested_by: str
    justification: str = Field(..., min_length=10, max_length=1000)
    urgency: str = Field(default="normal", pattern="^(low|normal|high|critical)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_id": 123,
                "requested_by": "user@company.com",
                "justification": "Emergency database access required for incident response",
                "urgency": "high"
            }
        }
