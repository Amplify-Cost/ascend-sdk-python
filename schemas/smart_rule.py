"""
Smart Rule Schemas
Pydantic models for smart rule validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class SmartRuleOut(BaseModel):
    """Schema for smart rule output"""
    id: int
    name: str
    description: Optional[str]
    rule_type: str
    conditions: Optional[Dict]
    actions: Optional[Dict]
    priority: Optional[int]
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SmartRuleOutEnhanced(SmartRuleOut):
    """Enhanced smart rule output with additional metadata"""
    execution_count: Optional[int] = 0
    last_executed: Optional[datetime] = None
    success_rate: Optional[float] = 0.0
    
    class Config:
        from_attributes = True
