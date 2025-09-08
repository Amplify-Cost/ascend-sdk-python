"""
Complete Schemas module - All Pydantic models for enterprise application
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# User Management Schemas
class UserOut(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class LoginInput(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# Agent Action Schemas
class AgentActionOut(BaseModel):
    id: str
    agent_name: str
    action_type: str
    target_resource: Optional[str] = None
    parameters: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AgentActionCreate(BaseModel):
    agent_name: str
    action_type: str
    target_resource: Optional[str] = None
    parameters: Dict[str, Any]

# Alert Schemas
class AlertOut(BaseModel):
    id: str
    alert_type: str
    severity: str
    message: str
    source: str
    created_at: datetime
    resolved: bool = False
    
    class Config:
        from_attributes = True

# Automation Schemas
class AutomationPlaybookOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    triggers: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

class AutomationExecutionCreate(BaseModel):
    playbook_id: str
    trigger_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

# Authorization Schemas
class AuthorizationRequest(BaseModel):
    action_type: str
    resource: str
    context: Dict[str, Any]
    justification: Optional[str] = None

# Workflow Schemas  
class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    approval_required: bool = True

class WorkflowExecutionRequest(BaseModel):
    workflow_id: str
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

# Smart Rules Schema
class SmartRuleOut(BaseModel):
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
__all__ = [
    "UserOut", "UserCreate", "LoginInput", "TokenResponse",
    "AgentActionOut", "AgentActionCreate", 
    "AlertOut",
    "AutomationPlaybookOut", "AutomationExecutionCreate",
    "AuthorizationRequest", 
    "WorkflowCreateRequest", "WorkflowExecutionRequest",
    "SmartRuleOut"
]
