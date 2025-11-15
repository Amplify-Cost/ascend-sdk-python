"""
Risk Scoring Configuration Schemas
Pydantic models for API request/response validation

Engineer: Donald King (OW-kai Enterprise)
Created: 2025-11-14
"""
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, List
from datetime import datetime

class RiskConfigCreate(BaseModel):
    """Schema for creating a new risk scoring configuration"""

    config_version: str = Field(..., examples=["2.1.0"])
    algorithm_version: str = Field(..., examples=["2.0.0"])

    environment_weights: Dict[str, int] = Field(..., examples=[{
        "production": 35,
        "staging": 18,
        "development": 5
    }])

    action_weights: Dict[str, int] = Field(..., examples=[{
        "delete": 23,
        "write": 17,
        "read": 8
    }])

    resource_multipliers: Dict[str, float] = Field(..., examples=[{
        "rds": 1.2,
        "s3": 1.0,
        "lambda": 0.8
    }])

    pii_weights: Dict[str, int] = Field(..., examples=[{
        "high_sensitivity": 25,
        "medium_sensitivity": 15,
        "low_sensitivity": 5
    }])

    component_percentages: Dict[str, int] = Field(..., examples=[{
        "environment": 35,
        "data_sensitivity": 30,
        "action_type": 25,
        "operational_context": 10
    }])

    description: Optional[str] = Field(None, examples=["Custom config for healthcare compliance"])

    @field_validator('component_percentages')
    @classmethod
    def validate_percentages_sum(cls, v):
        total = sum(v.values())
        if total != 100:
            raise ValueError(f"Component percentages must sum to 100, got {total}")
        return v

class RiskConfigResponse(BaseModel):
    """Schema for risk scoring configuration response"""

    id: int
    config_version: str
    algorithm_version: str
    environment_weights: Dict[str, int]
    action_weights: Dict[str, int]
    resource_multipliers: Dict[str, float]
    pii_weights: Dict[str, int]
    component_percentages: Dict[str, int]
    description: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    created_by: str
    activated_at: Optional[datetime]
    activated_by: Optional[str]

    class Config:
        from_attributes = True

class RiskConfigValidation(BaseModel):
    """Schema for configuration validation response"""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
