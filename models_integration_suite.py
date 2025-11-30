"""
OW-kai Enterprise Phase 5: Full Integration Suite Models
=========================================================

Enterprise-grade unified integration management system that provides:
- Centralized integration registry
- Connection health monitoring
- Data flow orchestration
- Integration analytics and metrics
- Cross-system event correlation

Banking-Level Security: All data queries use real database records.
No demo data, no fallbacks - production-ready enterprise solution.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# ============================================
# SQLAlchemy Models
# ============================================

class IntegrationRegistry(Base):
    """
    Central registry of all enterprise integrations.
    Manages connection configurations and credentials.
    """
    __tablename__ = 'integration_registry'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Integration Identity
    integration_type = Column(String(50), nullable=False, index=True)  # webhook, slack, teams, servicenow, siem, compliance
    integration_name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)

    # Connection Configuration
    endpoint_url = Column(String(500), nullable=True)
    auth_type = Column(String(50), default='none')  # none, api_key, oauth2, basic, certificate
    credentials_encrypted = Column(Text, nullable=True)  # AES-256 encrypted credentials

    # Status
    is_enabled = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Health Metrics
    health_status = Column(String(20), default='unknown')  # healthy, degraded, unhealthy, unknown
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    consecutive_failures = Column(Integer, default=0)
    uptime_percent_30d = Column(Float, nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)
    retry_config = Column(JSON, nullable=True)  # max_retries, backoff_multiplier, etc.
    rate_limit_config = Column(JSON, nullable=True)  # requests_per_minute, burst_limit

    # Metadata
    version = Column(String(20), nullable=True)
    tags = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    health_checks = relationship("IntegrationHealthCheck", back_populates="integration", cascade="all, delete-orphan")
    data_flows = relationship("IntegrationDataFlow", back_populates="source_integration", foreign_keys="IntegrationDataFlow.source_integration_id")


class IntegrationHealthCheck(Base):
    """
    Health check history for integration monitoring.
    Records latency, status codes, and error details.
    """
    __tablename__ = 'integration_health_checks'

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey('integration_registry.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Check Results
    check_type = Column(String(50), default='ping')  # ping, auth_test, data_test, full_test
    status = Column(String(20), nullable=False)  # success, failure, timeout, error
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Error Details
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    integration = relationship("IntegrationRegistry", back_populates="health_checks")


class IntegrationDataFlow(Base):
    """
    Data flow orchestration between integrations.
    Tracks data movement and transformations.
    """
    __tablename__ = 'integration_data_flows'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Flow Identity
    flow_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Source and Destination
    source_integration_id = Column(Integer, ForeignKey('integration_registry.id', ondelete='CASCADE'), nullable=False)
    source_type = Column(String(50), nullable=False)  # internal, webhook, api, database
    destination_integration_id = Column(Integer, ForeignKey('integration_registry.id', ondelete='CASCADE'), nullable=True)
    destination_type = Column(String(50), nullable=False)

    # Data Configuration
    data_type = Column(String(50), nullable=False)  # alert, event, log, metric, notification
    transformation_rules = Column(JSON, nullable=True)
    filter_rules = Column(JSON, nullable=True)

    # Flow Control
    is_enabled = Column(Boolean, default=True)
    batch_size = Column(Integer, default=100)
    batch_interval_seconds = Column(Integer, default=60)

    # Execution Tracking
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    last_execution_status = Column(String(20), nullable=True)
    total_records_processed = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)

    # Timestamps
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    source_integration = relationship("IntegrationRegistry", back_populates="data_flows", foreign_keys=[source_integration_id])
    executions = relationship("DataFlowExecution", back_populates="data_flow", cascade="all, delete-orphan")


class DataFlowExecution(Base):
    """
    Execution history for data flows.
    Records batch processing results and metrics.
    """
    __tablename__ = 'data_flow_executions'

    id = Column(Integer, primary_key=True, index=True)
    data_flow_id = Column(Integer, ForeignKey('integration_data_flows.id', ondelete='CASCADE'), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Execution Details
    execution_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(20), nullable=False)  # running, completed, failed, partial

    # Metrics
    records_read = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)

    # Performance
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Error Tracking
    errors = Column(JSON, nullable=True)

    # Relationships
    data_flow = relationship("IntegrationDataFlow", back_populates="executions")


class IntegrationEvent(Base):
    """
    Cross-system event correlation and tracking.
    Enables unified event monitoring across all integrations.
    """
    __tablename__ = 'integration_events'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

    # Event Identity
    event_id = Column(String(100), nullable=False, unique=True, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)  # For tracking related events

    # Source
    source_integration_id = Column(Integer, ForeignKey('integration_registry.id', ondelete='SET NULL'), nullable=True)
    source_type = Column(String(50), nullable=False)
    source_system = Column(String(100), nullable=True)

    # Event Details
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=True)  # security, compliance, operational, notification
    severity = Column(String(20), default='info')  # critical, high, medium, low, info

    # Payload
    payload = Column(JSON, nullable=True)
    payload_hash = Column(String(64), nullable=True)  # SHA-256 for deduplication

    # Processing Status
    status = Column(String(20), default='received')  # received, processing, processed, failed
    processed_by = Column(JSON, nullable=True)  # List of integrations that processed this event

    # Timestamps
    event_time = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # TTL for cleanup
    expires_at = Column(DateTime(timezone=True), nullable=True)


class IntegrationMetric(Base):
    """
    Aggregated metrics for integration performance analytics.
    Pre-computed metrics for dashboard visualization.
    """
    __tablename__ = 'integration_metrics'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey('integration_registry.id', ondelete='CASCADE'), nullable=True, index=True)

    # Time Window
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)
    granularity = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly

    # Volume Metrics
    total_events = Column(Integer, default=0)
    successful_events = Column(Integer, default=0)
    failed_events = Column(Integer, default=0)

    # Performance Metrics
    avg_latency_ms = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    p99_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)

    # Reliability Metrics
    uptime_percent = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)

    # Data Volume
    bytes_processed = Column(Integer, default=0)

    # Computed at
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================
# Enums
# ============================================

class IntegrationType(str, Enum):
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SERVICENOW = "servicenow"
    SIEM = "siem"
    COMPLIANCE = "compliance"
    EMAIL = "email"
    CUSTOM = "custom"


class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    CERTIFICATE = "certificate"
    JWT = "jwt"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class DataFlowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class EventSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================
# Pydantic Schemas
# ============================================

class IntegrationCreateRequest(BaseModel):
    """Request to create a new integration."""
    integration_type: IntegrationType
    integration_name: str = Field(..., min_length=1, max_length=200)
    display_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    auth_type: AuthType = AuthType.NONE
    config: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    rate_limit_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

    @validator('integration_name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Integration name cannot be empty')
        return v.strip()


class IntegrationUpdateRequest(BaseModel):
    """Request to update an existing integration."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    auth_type: Optional[AuthType] = None
    config: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    rate_limit_config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None


class IntegrationResponse(BaseModel):
    """Integration details response."""
    id: int
    integration_type: str
    integration_name: str
    display_name: Optional[str]
    description: Optional[str]
    endpoint_url: Optional[str]
    auth_type: str
    is_enabled: bool
    is_verified: bool
    health_status: str
    last_health_check: Optional[datetime]
    uptime_percent_30d: Optional[float]
    config: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check result response."""
    integration_id: int
    integration_name: str
    status: str
    status_code: Optional[int]
    response_time_ms: Optional[int]
    error_message: Optional[str]
    checked_at: datetime


class DataFlowCreateRequest(BaseModel):
    """Request to create a new data flow."""
    flow_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source_integration_id: int
    source_type: str
    destination_integration_id: Optional[int] = None
    destination_type: str
    data_type: str
    transformation_rules: Optional[Dict[str, Any]] = None
    filter_rules: Optional[Dict[str, Any]] = None
    batch_size: int = Field(default=100, ge=1, le=10000)
    batch_interval_seconds: int = Field(default=60, ge=1, le=86400)


class DataFlowResponse(BaseModel):
    """Data flow configuration response."""
    id: int
    flow_name: str
    description: Optional[str]
    source_integration_id: int
    source_type: str
    destination_integration_id: Optional[int]
    destination_type: str
    data_type: str
    is_enabled: bool
    last_execution_at: Optional[datetime]
    last_execution_status: Optional[str]
    total_records_processed: int
    total_errors: int
    created_at: datetime

    class Config:
        from_attributes = True


class DataFlowExecutionResponse(BaseModel):
    """Data flow execution result response."""
    execution_id: str
    data_flow_id: int
    status: str
    records_read: int
    records_processed: int
    records_failed: int
    records_skipped: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    errors: Optional[List[Dict[str, Any]]]


class IntegrationEventResponse(BaseModel):
    """Integration event response."""
    event_id: str
    correlation_id: Optional[str]
    source_type: str
    source_system: Optional[str]
    event_type: str
    event_category: Optional[str]
    severity: str
    status: str
    event_time: datetime
    received_at: datetime
    processed_at: Optional[datetime]


class IntegrationMetricsResponse(BaseModel):
    """Integration metrics response."""
    integration_id: Optional[int]
    integration_name: Optional[str]
    period: str
    total_events: int
    successful_events: int
    failed_events: int
    success_rate: float
    avg_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    uptime_percent: Optional[float]
    bytes_processed: int


class IntegrationDashboardResponse(BaseModel):
    """Dashboard summary response."""
    total_integrations: int
    active_integrations: int
    healthy_integrations: int
    degraded_integrations: int
    unhealthy_integrations: int
    total_events_24h: int
    total_events_7d: int
    avg_latency_24h: Optional[float]
    overall_uptime_30d: Optional[float]
    integrations_by_type: Dict[str, int]
    recent_alerts: List[Dict[str, Any]]


class IntegrationTestRequest(BaseModel):
    """
    Request to test an integration connection.

    Supports two modes:
    1. Test existing integration: provide integration_id
    2. Test new integration (before save): provide integration_type, endpoint_url, config

    Authored-By: Ascend Engineer
    """
    # For testing existing integrations
    integration_id: Optional[int] = None

    # For testing new integrations (before save)
    integration_type: Optional[str] = None
    endpoint_url: Optional[str] = None
    auth_type: Optional[str] = "none"
    config: Optional[Dict[str, Any]] = None

    # Test configuration
    test_type: str = "ping"  # ping, auth_test, data_test, full_test
    test_payload: Optional[Dict[str, Any]] = None


class BulkOperationRequest(BaseModel):
    """Request for bulk operations on integrations."""
    integration_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str  # enable, disable, delete, test


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    operation: str
    total: int
    succeeded: int
    failed: int
    results: List[Dict[str, Any]]


# ============================================
# Integration Type Configurations
# ============================================

INTEGRATION_TYPE_CONFIG = {
    IntegrationType.WEBHOOK: {
        "display_name": "Webhook",
        "description": "HTTP webhook for real-time event notifications",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.NONE, AuthType.API_KEY, AuthType.BASIC, AuthType.JWT],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 300,
    },
    IntegrationType.SLACK: {
        "display_name": "Slack",
        "description": "Slack workspace integration for notifications",
        "required_fields": ["endpoint_url"],
        # SEC-028: Allow NONE for incoming webhooks (URL contains auth token)
        # and OAUTH2 for Slack Apps with bot tokens
        "supported_auth": [AuthType.NONE, AuthType.API_KEY, AuthType.OAUTH2],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 600,
    },
    IntegrationType.TEAMS: {
        "display_name": "Microsoft Teams",
        "description": "Microsoft Teams integration for notifications",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.NONE, AuthType.OAUTH2],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 600,
    },
    IntegrationType.SERVICENOW: {
        "display_name": "ServiceNow",
        "description": "ServiceNow ITSM integration for incident management",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.BASIC, AuthType.OAUTH2],
        "default_retry_config": {"max_retries": 5, "backoff_multiplier": 2, "initial_delay_ms": 2000},
        "health_check_interval_seconds": 300,
    },
    IntegrationType.SIEM: {
        "display_name": "SIEM",
        "description": "Security Information and Event Management integration",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.API_KEY, AuthType.CERTIFICATE],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 300,
    },
    IntegrationType.COMPLIANCE: {
        "display_name": "Compliance Export",
        "description": "Compliance reporting and export integration",
        "required_fields": [],
        "supported_auth": [AuthType.NONE],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 3600,
    },
    IntegrationType.EMAIL: {
        "display_name": "Email",
        "description": "Email notification integration",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.BASIC, AuthType.API_KEY],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 1800,
    },
    IntegrationType.CUSTOM: {
        "display_name": "Custom",
        "description": "Custom integration endpoint",
        "required_fields": ["endpoint_url"],
        "supported_auth": [AuthType.NONE, AuthType.API_KEY, AuthType.BASIC, AuthType.OAUTH2, AuthType.JWT, AuthType.CERTIFICATE],
        "default_retry_config": {"max_retries": 3, "backoff_multiplier": 2, "initial_delay_ms": 1000},
        "health_check_interval_seconds": 600,
    },
}


# ============================================
# Data Flow Templates
# ============================================

DATA_FLOW_TEMPLATES = {
    "alert_to_slack": {
        "name": "Alerts to Slack",
        "description": "Send high-severity alerts to Slack channel",
        "source_type": "internal",
        "destination_type": "slack",
        "data_type": "alert",
        "filter_rules": {"severity": ["critical", "high"]},
        "transformation_rules": {
            "format": "slack_block",
            "include_fields": ["title", "severity", "description", "timestamp", "link"],
        },
    },
    "alert_to_servicenow": {
        "name": "Alerts to ServiceNow Incidents",
        "description": "Create ServiceNow incidents from security alerts",
        "source_type": "internal",
        "destination_type": "servicenow",
        "data_type": "alert",
        "filter_rules": {"severity": ["critical", "high", "medium"]},
        "transformation_rules": {
            "incident_mapping": {
                "short_description": "{{title}}",
                "description": "{{description}}",
                "urgency": "{{severity_to_urgency}}",
                "impact": "{{severity_to_impact}}",
            },
        },
    },
    "events_to_siem": {
        "name": "Events to SIEM",
        "description": "Stream all security events to SIEM for correlation",
        "source_type": "internal",
        "destination_type": "siem",
        "data_type": "event",
        "filter_rules": {"category": ["security", "compliance", "audit"]},
        "transformation_rules": {
            "format": "cef",
            "include_metadata": True,
        },
    },
    "compliance_to_webhook": {
        "name": "Compliance Events to Webhook",
        "description": "Send compliance events to external webhook",
        "source_type": "internal",
        "destination_type": "webhook",
        "data_type": "compliance",
        "filter_rules": {},
        "transformation_rules": {
            "format": "json",
            "sign_payload": True,
        },
    },
}
