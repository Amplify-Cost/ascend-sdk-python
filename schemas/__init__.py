"""
Schemas module - Enterprise Pydantic models
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SmartRuleOut(BaseModel):
    """Smart Rule output schema for API responses"""
    id: str
    name: str
    description: Optional[str] = None
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 0
    enabled: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Export all schemas
__all__ = ["SmartRuleOut"]
