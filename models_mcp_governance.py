# File: ow-ai-backend/models_mcp_governance.py
# MCP Server Governance Data Models
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, UTC
import uuid
import json
import hashlib

from database import Base

class MCPServerAction(Base):
    """
    🏢 ENTERPRISE MCP Server Action Model
    Tracks all MCP server interactions with same governance as agent actions

    Enterprise Features:
    - UUID primary keys for distributed systems
    - Compatibility fields for unified governance loader
    - Full audit trail integration
    - Multi-level approval workflow
    - Real-time risk assessment

    Aligns with: Palo Alto Networks Cortex XSOAR, Splunk SOAR patterns
    """
    __tablename__ = "mcp_server_actions"

    # Primary identification (Enterprise UUID-based)
    id = Column(Integer, primary_key=True, autoincrement=True)  # Sequential ID for compatibility
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)  # Enterprise UUID
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # SEC-045: Multi-tenant isolation (required for enterprise_unified_loader.py)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # 🏢 COMPATIBILITY FIELDS (for enterprise_unified_loader.py)
    agent_id = Column(String(255), nullable=False, index=True)  # Maps to mcp_server_name for compatibility
    action_type = Column(String(100), nullable=False, index=True)  # Maps to verb for compatibility
    description = Column(Text, nullable=True)  # Human-readable description
    context = Column(JSON, nullable=True)  # Replaces parameters for JSONB compatibility

    # MCP Server Identity
    mcp_server_id = Column(String(200), nullable=True, index=True)  # Changed from UUID FK to String for flexibility
    mcp_server_name = Column(String(200), nullable=False)  # Human readable name
    mcp_server_version = Column(String(50))  # Version info

    # MCP Protocol Details
    namespace = Column(String(100), nullable=False, index=True)  # e.g., "filesystem", "database", "tools"
    verb = Column(String(100), nullable=False, index=True)  # e.g., "read_file", "write_file", "execute"
    resource = Column(String(500), nullable=False)  # Target resource path/identifier
    
    # Request Details
    request_id = Column(String(100), nullable=False, unique=True)  # MCP request ID
    session_id = Column(String(100), nullable=False, index=True)  # MCP session
    client_id = Column(String(100), nullable=False, index=True)  # Requesting client
    
    # Action Parameters
    parameters = Column(JSON, nullable=False, default=dict)  # MCP action parameters
    payload_size = Column(Integer, default=0)  # Size of request payload
    
    # Risk Assessment (Same as Agent Actions)
    risk_score = Column(Integer, nullable=False, default=0)  # 0-100 risk score
    risk_level = Column(String(20), nullable=False, default='LOW')  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSON, default=list)  # List of risk factors identified
    
    # Governance Status
    status = Column(String(50), nullable=False, default='PENDING')  # PENDING, APPROVED, DENIED, EXECUTED, FAILED
    requires_approval = Column(Boolean, nullable=False, default=True)
    approval_level = Column(Integer, default=1)  # 1-5 approval levels
    
    # User Context
    user_id = Column(String(100), nullable=False, index=True)  # User requesting action
    user_email = Column(String(255), nullable=False)
    user_role = Column(String(100))  # User's role/department
    
    # Policy & Rules
    policy_result = Column(String(50), default='EVALUATE')  # ALLOW, DENY, EVALUATE
    rule_id = Column(String(100), index=True)  # Applied rule ID
    policy_reason = Column(Text)  # Policy decision reason

    # 🏢 OPTION 4 POLICY FUSION FIELDS (Enterprise hybrid risk scoring)
    policy_evaluated = Column(Boolean, default=False, nullable=False)  # Was policy engine consulted?
    policy_decision = Column(String(50), nullable=True)  # ALLOW, DENY, ESCALATE from policy engine
    policy_risk_score = Column(Float, nullable=True)  # Policy engine's risk score (0-100)
    risk_fusion_formula = Column(String(255), nullable=True)  # Formula used for fusion
    
    # Approval Workflow (Enhanced for enterprise_unified_loader compatibility)
    approver_id = Column(String(100), index=True)  # Who approved/denied
    approver_email = Column(String(255))
    approved_by = Column(String(255), nullable=True)  # Compatibility field
    approved_at = Column(DateTime)
    approval_reason = Column(Text)
    reviewed_by = Column(String(255), nullable=True)  # Compatibility field
    reviewed_at = Column(DateTime, nullable=True)  # Compatibility field
    created_by = Column(String(255), nullable=True)  # Compatibility field
    
    # Execution Details
    executed_at = Column(DateTime)
    execution_duration_ms = Column(Integer)  # Execution time
    execution_result = Column(String(50))  # SUCCESS, FAILED, TIMEOUT
    execution_output = Column(Text)  # Execution output/result
    error_message = Column(Text)  # Error details if failed
    
    # Security & Compliance
    environment = Column(String(50), default='production')  # production, staging, dev
    data_classification = Column(String(50), default='internal')  # public, internal, confidential, restricted
    compliance_tags = Column(JSON, default=list)  # SOX, HIPAA, PCI, GDPR tags
    
    # Audit Trail Integration
    audit_trail_id = Column(UUID(as_uuid=True), index=True)  # Links to immutable audit
    evidence_pack_id = Column(UUID(as_uuid=True))  # Evidence pack for investigations
    
    # Network & Context
    source_ip = Column(String(45))  # IPv4/IPv6 address
    user_agent = Column(String(500))  # Client user agent
    geo_location = Column(String(100))  # Geographic location
    
    # Performance Metrics
    response_time_ms = Column(Integer)  # Gateway response time
    bytes_transferred = Column(Integer)  # Data transfer size
    
    # Database indexes for enterprise performance
    __table_args__ = (
        Index('idx_mcp_server_namespace', 'mcp_server_id', 'namespace'),
        Index('idx_mcp_risk_level', 'risk_level', 'status'),
        Index('idx_mcp_user_time', 'user_id', 'created_at'),
        Index('idx_mcp_approval', 'status', 'requires_approval'),
        Index('idx_mcp_compliance', 'compliance_tags'),
        Index('idx_mcp_session', 'session_id', 'created_at'),
        Index('idx_mcp_agent_action_type', 'agent_id', 'action_type'),  # Compatibility index
        Index('idx_mcp_uuid', 'uuid'),  # Enterprise UUID lookups
    )

class MCPServer(Base):
    """
    🏢 ENTERPRISE MCP Server Registry
    Tracks all registered MCP servers for governance and monitoring

    Enterprise Features:
    - Server trust levels (trusted, restricted, sandbox)
    - Real-time health monitoring
    - Capability-based authorization
    - Performance metrics tracking
    """
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Sequential ID
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)  # Enterprise UUID
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Server Identity
    server_id = Column(String(100), nullable=False, unique=True, index=True)  # Unique server identifier
    server_name = Column(String(200), nullable=False)
    server_description = Column(Text)
    server_version = Column(String(50))
    
    # Connection Details
    endpoint_url = Column(String(500))  # Server endpoint
    connection_type = Column(String(50), default='websocket')  # websocket, http, stdio
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime)
    
    # Capabilities
    supported_namespaces = Column(JSON, default=list)  # List of supported namespaces
    capabilities = Column(JSON, default=dict)  # Server capabilities
    
    # Security Configuration
    requires_auth = Column(Boolean, default=True)
    auth_method = Column(String(50), default='jwt')  # jwt, apikey, mtls
    trust_level = Column(String(20), default='restricted')  # trusted, restricted, sandbox
    
    # Governance Settings
    default_risk_level = Column(String(20), default='MEDIUM')
    requires_approval_by_default = Column(Boolean, default=True)
    max_approval_level = Column(Integer, default=3)
    
    # Monitoring
    total_actions = Column(Integer, default=0)
    failed_actions = Column(Integer, default=0)
    avg_response_time_ms = Column(Float, default=0.0)

    # Note: No FK relationship - mcp_server_id in actions is String for flexibility

class MCPSession(Base):
    """
    MCP Session Tracking - Tracks active MCP client sessions
    """
    __tablename__ = "mcp_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Session Identity
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    server_id = Column(String(100), ForeignKey('mcp_servers.server_id'), nullable=False)
    
    # User Context
    user_id = Column(String(100), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    authenticated_at = Column(DateTime)
    
    # Session Status
    status = Column(String(50), default='ACTIVE')  # ACTIVE, TERMINATED, EXPIRED
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime)
    
    # Connection Details
    connection_type = Column(String(50))
    source_ip = Column(String(45))
    user_agent = Column(String(500))
    
    # Activity Metrics
    total_actions = Column(Integer, default=0)
    successful_actions = Column(Integer, default=0)
    failed_actions = Column(Integer, default=0)
    bytes_transferred = Column(Integer, default=0)
    
    # Security
    auth_token_hash = Column(String(64))  # Hashed auth token
    permissions = Column(JSON, default=list)  # Session permissions
    
    # Relationships
    server = relationship("MCPServer", backref="sessions")

class MCPPolicy(Base):
    """
    MCP Governance Policies - Rules for MCP server actions
    Integrates with existing smart rules engine
    """
    __tablename__ = "mcp_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Policy Identity
    policy_name = Column(String(200), nullable=False)
    policy_description = Column(Text)
    policy_version = Column(String(20), default='1.0')
    
    # Scope
    server_patterns = Column(JSON, default=list)  # Server ID patterns
    namespace_patterns = Column(JSON, default=list)  # Namespace patterns
    verb_patterns = Column(JSON, default=list)  # Verb patterns
    resource_patterns = Column(JSON, default=list)
    
    # Enterprise Policy Versioning Fields
    policy_status = Column(String(50), nullable=False, default='draft')  # draft, testing, approved, deployed, deprecated
    major_version = Column(Integer, nullable=False, default=1)
    minor_version = Column(Integer, nullable=False, default=0) 
    patch_version = Column(Integer, nullable=False, default=0)
    version_hash = Column(String(64), nullable=True)  # SHA256 of policy content
    parent_policy_id = Column(UUID(as_uuid=True), ForeignKey('mcp_policies.id'), nullable=True)
    deployment_timestamp = Column(DateTime, nullable=True)
    rollback_target_id = Column(UUID(as_uuid=True), ForeignKey('mcp_policies.id'), nullable=True)
    
    # Natural Language Policy Support
    natural_language_description = Column(Text, nullable=True)
    test_results = Column(JSON, nullable=True)
    
    # Enterprise Approval Workflow
    approval_required = Column(Boolean, nullable=False, default=True)
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime, nullable=True)  # Resource patterns
    
    # Conditions
    conditions = Column(JSON, default=dict)  # Policy conditions (JSON/CEL format)
    risk_threshold = Column(Integer, default=50)  # Risk score threshold
    
    # Actions
    action = Column(String(50), default='EVALUATE')  # ALLOW, DENY, EVALUATE
    required_approval_level = Column(Integer, default=1)
    auto_approve_conditions = Column(JSON, default=dict)
    
    # Governance
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Higher priority = evaluated first
    created_by = Column(String(100), nullable=False)
    
    # Compliance
    compliance_framework = Column(String(50))  # SOX, HIPAA, PCI, GDPR
    regulatory_reference = Column(String(200))  # Legal reference
    
    # Performance
    execution_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)

