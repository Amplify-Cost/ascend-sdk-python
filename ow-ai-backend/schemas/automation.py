"""
Automation & Playbook Schemas
For automation execution and playbook management
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class AutomationPlaybookOut(BaseModel):
    """Schema for automation playbook output"""
    id: int
    name: str
    description: Optional[str]
    playbook_type: str
    steps: Optional[List[Dict]]
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AutomationExecutionCreate(BaseModel):
    """Schema for creating automation execution"""
    playbook_id: int
    action_id: Optional[int]
    trigger_type: str = Field(..., max_length=100)
    parameters: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "playbook_id": 1,
                "action_id": 123,
                "trigger_type": "manual",
                "parameters": {"timeout": 300}
            }
        }
