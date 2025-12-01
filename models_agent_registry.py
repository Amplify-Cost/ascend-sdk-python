"""
OW-AI Enterprise Agent Registry Models
======================================

Enterprise-grade agent registration and configuration management.
Enables organizations to register, configure, and govern their AI agents.

Features:
- Agent registration with versioning
- Risk policy configuration per agent
- MCP server integration
- Approval workflow configuration
- Audit trail for all changes

Compliance: SOC 2 CC6.1, PCI-DSS 8.3, NIST 800-53 AC-2
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text,
    JSON, Float, UniqueConstraint, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base
import enum


class AgentType(str, enum.Enum):
    """Classification of AI agent types for governance policies."""
    AUTONOMOUS = "autonomous"           # Fully autonomous decision-making
    SUPERVISED = "supervised"           # Requires human approval for actions
    ADVISORY = "advisory"               # Provides recommendations only
    MCP_SERVER = "mcp_server"           # Model Context Protocol server
    CUSTOM = "custom"                   # Custom agent type


class AgentStatus(str, enum.Enum):
    """Lifecycle status of registered agents."""
    DRAFT = "draft"                     # Being configured
    PENDING_APPROVAL = "pending_approval"  # Awaiting admin approval
    ACTIVE = "active"                   # Operational
    SUSPENDED = "suspended"             # Temporarily disabled
    DEPRECATED = "deprecated"           # Scheduled for removal
    RETIRED = "retired"                 # No longer operational


class RegisteredAgent(Base):
    """
    Enterprise Agent Registry - Core Agent Registration

    Each AI agent that interacts with the OW-AI governance platform
    must be registered with proper configuration and risk policies.

    Multi-tenant: Agents are scoped to organizations with proper isolation.
    Versioning: Supports multiple versions with rollback capability.

    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 8.3
    """
    __tablename__ = "registered_agents"

    __table_args__ = (
        # Agent ID must be unique within an organization
        UniqueConstraint('agent_id', 'organization_id', name='uq_agent_org'),
        # Optimize queries by organization
        Index('ix_registered_agents_org_status', 'organization_id', 'status'),
        Index('ix_registered_agents_agent_type', 'agent_type'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Agent Identification
    agent_id = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Agent Classification
    agent_type = Column(String(50), default=AgentType.SUPERVISED.value, nullable=False)
    status = Column(String(50), default=AgentStatus.DRAFT.value, nullable=False)

    # Version Control
    version = Column(String(50), default="1.0.0", nullable=False)
    version_notes = Column(Text, nullable=True)

    # Multi-Tenant Isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Risk Configuration
    default_risk_score = Column(Integer, default=50, nullable=False)
    max_risk_threshold = Column(Integer, default=80, nullable=False)
    auto_approve_below = Column(Integer, default=30, nullable=False)
    requires_mfa_above = Column(Integer, default=70, nullable=False)

    # Capabilities & Permissions
    allowed_action_types = Column(JSONB, default=list)  # ["query", "data_access", "transaction"]
    allowed_resources = Column(JSONB, default=list)     # ["database", "api", "file_system"]
    blocked_resources = Column(JSONB, default=list)     # Explicit deny list

    # MCP Server Integration
    is_mcp_server = Column(Boolean, default=False, nullable=False)
    mcp_server_url = Column(String(500), nullable=True)
    mcp_capabilities = Column(JSONB, default=dict)      # {"tools": [], "prompts": [], "resources": []}

    # Notification Settings
    alert_on_high_risk = Column(Boolean, default=True, nullable=False)
    alert_recipients = Column(JSONB, default=list)      # ["admin@company.com"]
    webhook_url = Column(String(500), nullable=True)

    # Audit Fields
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    updated_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)

    # Metadata
    tags = Column(JSONB, default=list)                  # ["finance", "customer-facing"]
    agent_metadata = Column(JSONB, default=dict)        # Custom key-value pairs (renamed from 'metadata' - reserved in SQLAlchemy)

    # Relationships
    organization = relationship("Organization", backref="registered_agents")
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    policies = relationship("AgentPolicy", back_populates="agent", cascade="all, delete-orphan")


class AgentVersion(Base):
    """
    Agent Version History - Immutable Version Records

    Maintains complete history of agent configurations for:
    - Audit compliance (SOC 2, SOX)
    - Rollback capability
    - Change tracking

    Each version is immutable once created.
    """
    __tablename__ = "agent_versions"

    __table_args__ = (
        UniqueConstraint('agent_id', 'version', name='uq_agent_version'),
        Index('ix_agent_versions_agent', 'agent_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key to Agent
    agent_id = Column(Integer, ForeignKey("registered_agents.id", ondelete="CASCADE"), nullable=False)

    # Version Information
    version = Column(String(50), nullable=False)
    version_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    # Snapshot of Configuration at Version Time
    config_snapshot = Column(JSONB, nullable=False)     # Full agent config at this version

    # Audit Fields
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(255), nullable=True)

    # Relationships
    agent = relationship("RegisteredAgent", back_populates="versions")


class AgentPolicy(Base):
    """
    Agent-Specific Policies - Fine-Grained Access Control

    Allows organizations to define specific policies for each agent:
    - Action-level restrictions
    - Resource access rules
    - Time-based policies
    - Approval escalation paths

    Compliance: NIST AC-3, PCI-DSS 7.1, HIPAA 164.312(a)
    """
    __tablename__ = "agent_policies"

    __table_args__ = (
        Index('ix_agent_policies_agent', 'agent_id'),
        Index('ix_agent_policies_org', 'organization_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    agent_id = Column(Integer, ForeignKey("registered_agents.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Policy Definition
    policy_name = Column(String(255), nullable=False)
    policy_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)  # Lower = higher priority

    # Conditions (when policy applies)
    conditions = Column(JSONB, default=dict)            # {"action_type": "transaction", "risk_above": 60}

    # Actions (what happens when conditions match)
    policy_action = Column(String(50), nullable=False)  # "require_approval", "block", "allow", "escalate"
    action_params = Column(JSONB, default=dict)         # {"escalate_to": "security-team", "timeout": 3600}

    # Audit Fields
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    agent = relationship("RegisteredAgent", back_populates="policies")


class AgentActivityLog(Base):
    """
    Agent Activity Audit Log - Compliance Tracking

    Immutable log of all agent registration and configuration changes.
    Required for SOC 2, SOX, and HIPAA compliance.

    All entries are append-only (no updates or deletes).
    """
    __tablename__ = "agent_activity_logs"

    __table_args__ = (
        Index('ix_agent_activity_logs_agent', 'agent_id'),
        Index('ix_agent_activity_logs_org', 'organization_id'),
        Index('ix_agent_activity_logs_timestamp', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # References
    agent_id = Column(Integer, ForeignKey("registered_agents.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Activity Information
    activity_type = Column(String(100), nullable=False)  # "registered", "updated", "activated", "suspended"
    activity_description = Column(Text, nullable=True)

    # Actor Information
    performed_by = Column(String(255), nullable=False)
    performed_via = Column(String(50), nullable=True)    # "api", "dashboard", "sdk"

    # Change Details
    previous_state = Column(JSONB, nullable=True)        # State before change
    new_state = Column(JSONB, nullable=True)             # State after change

    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp (immutable)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class MCPServerConfig(Base):
    """
    MCP Server Configuration - Model Context Protocol Integration

    Stores configuration for MCP servers integrated with OW-AI governance.
    Enables governance over AI tool usage across the organization.

    Features:
    - Tool-level governance
    - Capability discovery
    - Usage tracking

    Compliance: SOC 2 CC6.1, NIST AC-6
    """
    __tablename__ = "mcp_server_configs"

    __table_args__ = (
        UniqueConstraint('server_name', 'organization_id', name='uq_mcp_server_org'),
        Index('ix_mcp_server_configs_org', 'organization_id'),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Server Identification
    server_name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Connection Configuration
    server_url = Column(String(500), nullable=True)
    transport_type = Column(String(50), default="stdio", nullable=False)  # "stdio", "http", "websocket"
    connection_config = Column(JSONB, default=dict)     # Transport-specific config

    # Multi-Tenant Isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Discovered Capabilities
    discovered_tools = Column(JSONB, default=list)      # [{"name": "read_file", "description": "..."}]
    discovered_prompts = Column(JSONB, default=list)
    discovered_resources = Column(JSONB, default=list)
    last_discovery = Column(DateTime, nullable=True)

    # Governance Settings
    governance_enabled = Column(Boolean, default=True, nullable=False)
    auto_approve_tools = Column(JSONB, default=list)    # Tools that don't need approval
    blocked_tools = Column(JSONB, default=list)         # Tools that are always blocked
    tool_risk_overrides = Column(JSONB, default=dict)   # {"tool_name": risk_score}

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(50), default="unknown", nullable=False)
    last_health_check = Column(DateTime, nullable=True)

    # Audit Fields
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    organization = relationship("Organization", backref="mcp_server_configs")
