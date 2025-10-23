"""
Workflow Schemas
Pydantic models for workflow validation and serialization
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict
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
        schema_extra = {
            "example": {
                "decision": "approve",
                "comments": "Action reviewed and approved for execution"
            }
        }
