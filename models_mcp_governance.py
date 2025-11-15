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
    🏢 ENTERPRISE: MCP Server Action Model - Unified Policy Engine Compatible

    NOW COMPATIBLE WITH: Production mcp_actions table
    SUPPORTS: Option 4 Policy Fusion (EnterpriseRealTimePolicyEngine)

    Tracks all MCP server interactions with same governance as agent actions.
    Uses unified policy engine for consistent risk scoring and policy evaluation.
    """
    __tablename__ = "mcp_actions"  # ✅ FIXED: Changed from "mcp_server_actions" to match production

    # Primary identification (matches production schema)
    id = Column(Integer, primary_key=True, index=True)  # ✅ FIXED: INTEGER to match production (not UUID)
    created_at = Column(DateTime, nullable=True, default=lambda: datetime.now(UTC))

    # Core fields (match production mcp_actions table)
    agent_id = Column(String(255), nullable=True)  # MCP server identifier (reuses agent_id column)
    action_type = Column(String(255), nullable=True)  # Action type (reuses column, populated from verb)
    resource = Column(Text, nullable=True)  # Target resource path
    context = Column(JSON, nullable=True)  # Additional context as JSONB
    risk_level = Column(String(50), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), nullable=True, default='pending')  # pending, approved, denied, executed

    # 🏢 OPTION 4 POLICY FUSION FIELDS (Added by migration 20251115_unified)
    policy_evaluated = Column(Boolean, default=False, nullable=True)  # True if EnterpriseRealTimePolicyEngine evaluated
    policy_decision = Column(String(50), nullable=True)  # ALLOW|DENY|REQUIRE_APPROVAL|ESCALATE|CONDITIONAL
    policy_risk_score = Column(Integer, nullable=True)  # 0-100 policy engine risk score
    risk_fusion_formula = Column(Text, nullable=True)  # Formula used for risk fusion

    # MCP Protocol Details (Added by migration)
    namespace = Column(String(100), nullable=True)  # e.g., "filesystem", "database", "tools"
    verb = Column(String(100), nullable=True)  # e.g., "read_file", "write_file", "execute"

    # User Context (Added by migration)
    user_email = Column(String(255), nullable=True)  # Email of user who initiated
    user_role = Column(String(100), nullable=True)  # Role of user (for policy evaluation)
    created_by = Column(String(255), nullable=True)  # Email/username of creator

    # Approval Workflow (Added by migration)
    approved_by = Column(String(255), nullable=True)  # Email of approver
    approved_at = Column(DateTime, nullable=True)  # Timestamp when approved
    reviewed_by = Column(String(255), nullable=True)  # Email of reviewer
    reviewed_at = Column(DateTime, nullable=True)  # Timestamp when reviewed

    # Risk Scoring Standardization (Added by migration)
    risk_score = Column(Float, nullable=True)  # 0-100 comprehensive risk score (matches agent_actions type)

    # Note: Production mcp_actions table has minimal schema (8 base columns + migration additions)
    # Extended enterprise fields (execution details, compliance, audit trail, etc.) will be stored in context JSONB
    # This keeps the model compatible with production while supporting rich metadata

class MCPServer(Base):
    """
    MCP Server Registry - Tracks all registered MCP servers
    """
    __tablename__ = "mcp_servers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Server Identity
    server_id = Column(String(100), nullable=False, unique=True)  # Unique server identifier
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

    # Relationships - DISABLED: mcp_actions table doesn't have server_id foreign key
    # actions = relationship("MCPServerAction", backref="mcp_server")

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

