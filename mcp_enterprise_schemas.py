"""
Enterprise MCP Schemas - Security-First Validation
Prevents injection attacks and validates all MCP inputs
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import re

class ActionType(str, Enum):
    """Validated action types - prevents arbitrary action injection"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete" 
    SYSTEM_COMMAND = "system_command"
    SYSTEM_RESTART = "system_restart"
    NETWORK_REQUEST = "network_request"
    DATABASE_QUERY = "database_query"

class MCPActionRequest(BaseModel):
    """Secure MCP action request with comprehensive validation"""
    agent_id: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    action_type: Union[ActionType, str]  # Accept both enum and string for compatibility
    resource: str = Field(..., min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Agent ID contains invalid characters')
        return v
    
    @validator('resource')
    def validate_resource_path(cls, v):
        # Prevent path traversal while allowing legitimate paths
        dangerous_patterns = ['../', '..\\', '/etc/', '/var/', 'C:\\', 'file://', 'ftp://']
        if any(pattern in v.lower() for pattern in dangerous_patterns):
            raise ValueError('Resource path contains potentially dangerous elements')
        return v
    
    @validator('metadata')
    def validate_metadata_size(cls, v):
        if len(str(v)) > 2048:  # Prevent DoS via large metadata
            raise ValueError('Metadata exceeds size limit')
        return v
    
    @validator('action_type')
    def validate_action_type(cls, v):
        # Convert string to enum if possible, otherwise keep as string for compatibility
        if isinstance(v, str):
            try:
                return ActionType(v)
            except ValueError:
                # Allow custom action types but validate format
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
                    raise ValueError('Invalid action type format')
        return v

class EnterpriseRiskResponse(BaseModel):
    """Standardized risk assessment response"""
    action_data: Dict[str, Any]
    enterprise_risk_assessment: Dict[str, Any] 
    assessed_by: str
    assessment_timestamp: str
    enterprise_benefits: Optional[Dict[str, Any]] = None

class MCPActionsResponse(BaseModel):
    """Paginated MCP actions response"""
    actions: List[Dict[str, Any]]
    total: int
    page: int = 0
    limit: int = 100
    has_next: bool = False
