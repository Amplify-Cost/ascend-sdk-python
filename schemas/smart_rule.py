"""
Smart Rule Schemas - Match actual database structure
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SmartRuleOut(BaseModel):
    """Schema for smart rule output - matches database columns"""
    id: int
    agent_id: Optional[str] = "*"
    action_type: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None  # Database has 'condition', not 'conditions'
    action: Optional[str] = None     # Database has 'action', not 'actions'
    risk_level: Optional[str] = None
    recommendation: Optional[str] = None
    justification: Optional[str] = None
    created_at: Optional[datetime] = None
    performance_score: Optional[int] = None
    triggers_last_24h: Optional[int] = None
    false_positives: Optional[int] = None
    effectiveness_rating: Optional[str] = None
    last_triggered: Optional[str] = None
    
    # Add these as optional for backward compatibility with new schema
    name: Optional[str] = None
    rule_type: Optional[str] = None
    conditions: Optional[Dict] = None
    actions: Optional[Dict] = None
    priority: Optional[int] = 0
    enabled: Optional[bool] = True
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "agent_id": "*",
                "action_type": "database_write",
                "description": "Validates database modifications",
                "condition": "action_type == 'database_write'",
                "action": "require_approval",
                "risk_level": "high",
                "enabled": True
            }
        }


class SmartRuleOutEnhanced(SmartRuleOut):
    """Enhanced schema with analytics"""
    performance_metrics: Optional[Dict[str, Any]] = None
    compliance_score: Optional[float] = None
