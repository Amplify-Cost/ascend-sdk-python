"""
OW-kai Enterprise Integration Phase 3: ServiceNow Connector Models

Banking-Level Enterprise ITSM Integration with:
- OAuth2 authentication (client credentials flow)
- Encrypted credential storage (AES-256)
- Incident/Change Request/Problem ticket creation
- CMDB Configuration Item integration
- Multi-tenant isolation
- Complete audit trail

Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, ITIL v4
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    BigInteger, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


# ============================================
# Enums
# ============================================

class ServiceNowTicketType(str, Enum):
    """ServiceNow ticket types supported"""
    INCIDENT = "incident"
    CHANGE_REQUEST = "change_request"
    PROBLEM = "problem"
    SERVICE_REQUEST = "sc_request"
    TASK = "sc_task"


class ServiceNowPriority(str, Enum):
    """ServiceNow priority levels (1=Critical, 5=Planning)"""
    CRITICAL = "1"
    HIGH = "2"
    MODERATE = "3"
    LOW = "4"
    PLANNING = "5"


class ServiceNowImpact(str, Enum):
    """ServiceNow impact levels"""
    HIGH = "1"
    MEDIUM = "2"
    LOW = "3"


class ServiceNowUrgency(str, Enum):
    """ServiceNow urgency levels"""
    HIGH = "1"
    MEDIUM = "2"
    LOW = "3"


class ServiceNowState(str, Enum):
    """ServiceNow incident states"""
    NEW = "1"
    IN_PROGRESS = "2"
    ON_HOLD = "3"
    RESOLVED = "6"
    CLOSED = "7"
    CANCELED = "8"


class ServiceNowSyncStatus(str, Enum):
    """Sync status between OW-kai and ServiceNow"""
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    CONFLICT = "conflict"


class ServiceNowAuthType(str, Enum):
    """Authentication types for ServiceNow"""
    BASIC = "basic"
    OAUTH2 = "oauth2"


# ============================================
# SQLAlchemy Models
# ============================================

class ServiceNowConnection(Base):
    """
    ServiceNow instance connection configuration.
    Stores encrypted credentials and connection settings.
    """
    __tablename__ = "servicenow_connections"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)

    # Instance configuration
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instance_url = Column(String(512), nullable=False)  # e.g., https://company.service-now.com

    # Authentication (encrypted)
    auth_type = Column(SQLEnum(ServiceNowAuthType), default=ServiceNowAuthType.OAUTH2, nullable=False)
    encrypted_credentials = Column(Text, nullable=False)  # AES-256 encrypted JSON
    encryption_salt = Column(String(32), nullable=False)

    # OAuth2 specific (encrypted)
    encrypted_client_id = Column(Text, nullable=True)
    encrypted_client_secret = Column(Text, nullable=True)
    token_endpoint = Column(String(512), nullable=True)  # Custom token endpoint if needed

    # Connection settings
    api_version = Column(String(20), default="v2", nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Default ticket configuration
    default_assignment_group = Column(String(255), nullable=True)
    default_caller_id = Column(String(255), nullable=True)
    default_category = Column(String(255), nullable=True)
    default_subcategory = Column(String(255), nullable=True)

    # CMDB integration
    cmdb_class = Column(String(255), nullable=True)  # e.g., cmdb_ci_server
    cmdb_lookup_field = Column(String(255), nullable=True)  # e.g., name, ip_address

    # Field mappings (JSONB)
    field_mappings = Column(JSONB, nullable=True)  # Map OW-kai fields to ServiceNow fields
    custom_fields = Column(JSONB, nullable=True)  # Additional custom fields to send

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_error = Column(Text, nullable=True)

    # Metrics
    total_tickets_created = Column(Integer, default=0, nullable=False)
    total_sync_errors = Column(Integer, default=0, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tickets = relationship("ServiceNowTicket", back_populates="connection", cascade="all, delete-orphan")


class ServiceNowTicket(Base):
    """
    ServiceNow tickets created from OW-kai.
    Tracks full lifecycle and sync status.
    """
    __tablename__ = "servicenow_tickets"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("servicenow_connections.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ticket identification
    ticket_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    servicenow_sys_id = Column(String(64), nullable=True, index=True)  # ServiceNow sys_id
    servicenow_number = Column(String(64), nullable=True, index=True)  # e.g., INC0012345

    # Ticket type and content
    ticket_type = Column(SQLEnum(ServiceNowTicketType), nullable=False, index=True)
    short_description = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    work_notes = Column(Text, nullable=True)

    # Classification
    priority = Column(SQLEnum(ServiceNowPriority), default=ServiceNowPriority.MODERATE, nullable=False)
    impact = Column(SQLEnum(ServiceNowImpact), default=ServiceNowImpact.MEDIUM, nullable=False)
    urgency = Column(SQLEnum(ServiceNowUrgency), default=ServiceNowUrgency.MEDIUM, nullable=False)
    state = Column(SQLEnum(ServiceNowState), default=ServiceNowState.NEW, nullable=False, index=True)

    # Assignment
    assignment_group = Column(String(255), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    caller_id = Column(String(255), nullable=True)

    # Categorization
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)

    # CMDB reference
    cmdb_ci = Column(String(255), nullable=True)  # Configuration Item
    cmdb_ci_sys_id = Column(String(64), nullable=True)

    # OW-kai source reference
    source_type = Column(String(100), nullable=True, index=True)  # alert, action, policy_violation
    source_id = Column(String(64), nullable=True, index=True)  # ID of the source record
    source_data = Column(JSONB, nullable=True)  # Original data for reference

    # ServiceNow response data
    servicenow_response = Column(JSONB, nullable=True)
    servicenow_link = Column(String(1024), nullable=True)  # Direct link to ticket

    # Sync status
    sync_status = Column(SQLEnum(ServiceNowSyncStatus), default=ServiceNowSyncStatus.PENDING, nullable=False, index=True)
    sync_attempts = Column(Integer, default=0, nullable=False)
    last_sync_error = Column(Text, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)

    # Bidirectional sync
    servicenow_updated_at = Column(DateTime(timezone=True), nullable=True)
    local_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Custom fields sent to ServiceNow
    custom_fields = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    connection = relationship("ServiceNowConnection", back_populates="tickets")


class ServiceNowSyncLog(Base):
    """
    Audit log for all ServiceNow sync operations.
    """
    __tablename__ = "servicenow_sync_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(Integer, ForeignKey("servicenow_connections.id", ondelete="SET NULL"), nullable=True)
    ticket_id = Column(BigInteger, ForeignKey("servicenow_tickets.id", ondelete="SET NULL"), nullable=True)

    # Operation details
    operation = Column(String(50), nullable=False, index=True)  # create, update, sync, verify
    direction = Column(String(20), nullable=False)  # outbound, inbound, bidirectional

    # Request/Response
    request_payload = Column(JSONB, nullable=True)
    response_payload = Column(JSONB, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Status
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


# ============================================
# Pydantic Schemas - Request/Response
# ============================================

class ServiceNowConnectionCreate(BaseModel):
    """Schema for creating a new ServiceNow connection"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Connection name")
    description: Optional[str] = Field(default=None, max_length=2000)
    instance_url: str = Field(..., min_length=10, max_length=512, description="ServiceNow instance URL")

    # Authentication
    auth_type: ServiceNowAuthType = Field(default=ServiceNowAuthType.OAUTH2)
    username: Optional[str] = Field(default=None, max_length=255, description="For basic auth")
    password: Optional[str] = Field(default=None, max_length=500, description="For basic auth")
    client_id: Optional[str] = Field(default=None, max_length=255, description="For OAuth2")
    client_secret: Optional[str] = Field(default=None, max_length=500, description="For OAuth2")

    # Connection settings
    api_version: str = Field(default="v2", max_length=20)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_retries: int = Field(default=3, ge=0, le=10)

    # Defaults
    default_assignment_group: Optional[str] = Field(default=None, max_length=255)
    default_caller_id: Optional[str] = Field(default=None, max_length=255)
    default_category: Optional[str] = Field(default=None, max_length=255)
    default_subcategory: Optional[str] = Field(default=None, max_length=255)

    # CMDB
    cmdb_class: Optional[str] = Field(default=None, max_length=255)
    cmdb_lookup_field: Optional[str] = Field(default=None, max_length=255)

    # Mappings
    field_mappings: Optional[Dict[str, str]] = Field(default=None)
    custom_fields: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator('instance_url')
    @classmethod
    def validate_instance_url(cls, v: str) -> str:
        """Validate ServiceNow instance URL format"""
        v = v.strip().rstrip('/')
        if not v.startswith(('https://', 'http://')):
            v = f"https://{v}"
        if not ('.service-now.com' in v or '.servicenow.com' in v or 'localhost' in v):
            raise ValueError('URL must be a valid ServiceNow instance (*.service-now.com)')
        return v


class ServiceNowConnectionUpdate(BaseModel):
    """Schema for updating a ServiceNow connection"""
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    instance_url: Optional[str] = Field(default=None, min_length=10, max_length=512)

    # Authentication updates
    username: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, max_length=500)
    client_id: Optional[str] = Field(default=None, max_length=255)
    client_secret: Optional[str] = Field(default=None, max_length=500)

    # Settings
    api_version: Optional[str] = Field(default=None, max_length=20)
    timeout_seconds: Optional[int] = Field(default=None, ge=5, le=120)
    max_retries: Optional[int] = Field(default=None, ge=0, le=10)

    # Defaults
    default_assignment_group: Optional[str] = Field(default=None, max_length=255)
    default_caller_id: Optional[str] = Field(default=None, max_length=255)
    default_category: Optional[str] = Field(default=None, max_length=255)
    default_subcategory: Optional[str] = Field(default=None, max_length=255)

    # CMDB
    cmdb_class: Optional[str] = Field(default=None, max_length=255)
    cmdb_lookup_field: Optional[str] = Field(default=None, max_length=255)

    # Mappings
    field_mappings: Optional[Dict[str, str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    is_active: Optional[bool] = None


class ServiceNowConnectionResponse(BaseModel):
    """Response schema for ServiceNow connection"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_id: str
    name: str
    description: Optional[str]
    instance_url: str
    auth_type: ServiceNowAuthType
    api_version: str
    timeout_seconds: int
    max_retries: int

    default_assignment_group: Optional[str]
    default_caller_id: Optional[str]
    default_category: Optional[str]
    default_subcategory: Optional[str]

    cmdb_class: Optional[str]
    cmdb_lookup_field: Optional[str]

    field_mappings: Optional[Dict[str, str]]
    custom_fields: Optional[Dict[str, Any]]

    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime]
    verification_error: Optional[str]

    total_tickets_created: int
    total_sync_errors: int
    last_sync_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime


class ServiceNowTicketCreate(BaseModel):
    """Schema for creating a ServiceNow ticket"""
    model_config = ConfigDict(from_attributes=True)

    connection_id: int = Field(..., description="ServiceNow connection to use")
    ticket_type: ServiceNowTicketType = Field(default=ServiceNowTicketType.INCIDENT)

    short_description: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=10000)
    work_notes: Optional[str] = Field(default=None, max_length=5000)

    priority: ServiceNowPriority = Field(default=ServiceNowPriority.MODERATE)
    impact: ServiceNowImpact = Field(default=ServiceNowImpact.MEDIUM)
    urgency: ServiceNowUrgency = Field(default=ServiceNowUrgency.MEDIUM)

    assignment_group: Optional[str] = Field(default=None, max_length=255)
    assigned_to: Optional[str] = Field(default=None, max_length=255)
    caller_id: Optional[str] = Field(default=None, max_length=255)

    category: Optional[str] = Field(default=None, max_length=255)
    subcategory: Optional[str] = Field(default=None, max_length=255)

    cmdb_ci: Optional[str] = Field(default=None, max_length=255)

    # Source reference
    source_type: Optional[str] = Field(default=None, max_length=100)
    source_id: Optional[str] = Field(default=None, max_length=64)
    source_data: Optional[Dict[str, Any]] = None

    custom_fields: Optional[Dict[str, Any]] = None


class ServiceNowTicketUpdate(BaseModel):
    """Schema for updating a ServiceNow ticket"""
    model_config = ConfigDict(from_attributes=True)

    short_description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=10000)
    work_notes: Optional[str] = Field(default=None, max_length=5000)

    priority: Optional[ServiceNowPriority] = None
    impact: Optional[ServiceNowImpact] = None
    urgency: Optional[ServiceNowUrgency] = None
    state: Optional[ServiceNowState] = None

    assignment_group: Optional[str] = Field(default=None, max_length=255)
    assigned_to: Optional[str] = Field(default=None, max_length=255)

    category: Optional[str] = Field(default=None, max_length=255)
    subcategory: Optional[str] = Field(default=None, max_length=255)

    custom_fields: Optional[Dict[str, Any]] = None


class ServiceNowTicketResponse(BaseModel):
    """Response schema for ServiceNow ticket"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    servicenow_sys_id: Optional[str]
    servicenow_number: Optional[str]
    servicenow_link: Optional[str]

    ticket_type: ServiceNowTicketType
    short_description: str
    description: Optional[str]

    priority: ServiceNowPriority
    impact: ServiceNowImpact
    urgency: ServiceNowUrgency
    state: ServiceNowState

    assignment_group: Optional[str]
    assigned_to: Optional[str]
    caller_id: Optional[str]

    category: Optional[str]
    subcategory: Optional[str]
    cmdb_ci: Optional[str]

    source_type: Optional[str]
    source_id: Optional[str]

    sync_status: ServiceNowSyncStatus
    sync_attempts: int
    last_sync_error: Optional[str]
    last_synced_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]


class ServiceNowTestResponse(BaseModel):
    """Response for connection test"""
    success: bool
    message: str
    instance_info: Optional[Dict[str, Any]] = None
    response_time_ms: int
    error_details: Optional[str] = None


class ServiceNowSyncResponse(BaseModel):
    """Response for sync operation"""
    success: bool
    tickets_synced: int
    tickets_failed: int
    errors: List[str] = []


class ServiceNowMetricsResponse(BaseModel):
    """Metrics for ServiceNow integration"""
    total_connections: int
    active_connections: int
    total_tickets: int
    tickets_by_type: Dict[str, int]
    tickets_by_status: Dict[str, int]
    sync_success_rate: float
    average_sync_time_ms: float
    last_24h_tickets: int
    last_24h_errors: int


# ============================================
# Event Type Mappings
# ============================================

# Map OW-kai events to ServiceNow ticket defaults
OWKAI_TO_SERVICENOW_MAPPING = {
    "alert.critical": {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.CRITICAL,
        "impact": ServiceNowImpact.HIGH,
        "urgency": ServiceNowUrgency.HIGH,
        "category": "Security",
    },
    "alert.triggered": {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.HIGH,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.HIGH,
        "category": "Security",
    },
    "policy.violated": {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.HIGH,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.MEDIUM,
        "category": "Compliance",
    },
    "action.escalated": {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.HIGH,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.HIGH,
        "category": "Authorization",
    },
    "workflow.failed": {
        "ticket_type": ServiceNowTicketType.PROBLEM,
        "priority": ServiceNowPriority.MODERATE,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.MEDIUM,
        "category": "Automation",
    },
    "security.suspicious_activity": {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.CRITICAL,
        "impact": ServiceNowImpact.HIGH,
        "urgency": ServiceNowUrgency.HIGH,
        "category": "Security",
        "subcategory": "Threat Detection",
    },
    "risk.threshold_exceeded": {
        "ticket_type": ServiceNowTicketType.CHANGE_REQUEST,
        "priority": ServiceNowPriority.HIGH,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.HIGH,
        "category": "Risk Management",
    },
}


def get_servicenow_defaults(event_type: str) -> Dict[str, Any]:
    """Get ServiceNow ticket defaults for an OW-kai event type"""
    return OWKAI_TO_SERVICENOW_MAPPING.get(event_type, {
        "ticket_type": ServiceNowTicketType.INCIDENT,
        "priority": ServiceNowPriority.MODERATE,
        "impact": ServiceNowImpact.MEDIUM,
        "urgency": ServiceNowUrgency.MEDIUM,
    })
