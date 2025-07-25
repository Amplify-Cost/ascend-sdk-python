from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="created_by_user")
    logs = relationship("Log", back_populates="user")

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    message = Column(Text)
    severity = Column(String)  # low, medium, high, critical
    status = Column(String, default="open")  # open, in_progress, closed
    source = Column(String)  # source system or component
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # Foreign key to user who created the alert
    created_by = Column(Integer, ForeignKey("users.id"))
    created_by_user = relationship("User", back_populates="alerts")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now(UTC))
    level = Column(String)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    source = Column(String)  # source component or service
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    extra_data = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # Relationship
    user = relationship("User", back_populates="logs")

class AgentAction(Base):
    __tablename__ = "agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    action_type = Column(String)
    description = Column(Text)
    risk_level = Column(String)  # low, medium, high, critical
    risk_score = Column(Float)
    status = Column(String, default="pending")  # pending, approved, denied, executed
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    extra_data = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # NIST/MITRE framework fields
    nist_control = Column(String, nullable=True)
    mitre_tactic = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)
    
    # Target system information
    target_system = Column(String, nullable=True)
    target_resource = Column(String, nullable=True)
    
    # Approval workflow
    requires_approval = Column(Boolean, default=True)
    approval_level = Column(Integer, default=1)  # 1, 2, or 3 level approval
    
    # Relationships
    approver = relationship("User", foreign_keys=[approved_by])

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    rule_type = Column(String)  # detection, prevention, response
    severity = Column(String)  # low, medium, high, critical
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Rule definition
    conditions = Column(JSON)  # Rule conditions in JSON format
    actions = Column(JSON)     # Actions to take when rule triggers
    
    # NIST/MITRE framework mapping
    nist_controls = Column(JSON, nullable=True)
    mitre_tactics = Column(JSON, nullable=True)
    mitre_techniques = Column(JSON, nullable=True)
    
    # Rule metrics
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class PendingAgentAction(Base):
    __tablename__ = "pending_agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    agent_id = Column(String, index=True)
    action_type = Column(String)
    description = Column(Text)
    risk_level = Column(String)
    risk_score = Column(Float)
    target_system = Column(String, nullable=True)
    
    # Enterprise Authorization Fields
    approval_level_required = Column(Integer, default=1)  # 1-3 approval levels
    current_approval_level = Column(Integer, default=0)
    approval_chain = Column(JSON, default=list)  # List of approvers
    escalation_timer = Column(DateTime, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    
    # Compliance Framework Integration
    nist_control = Column(String, nullable=True)
    mitre_tactic = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    # Status and Workflow
    status = Column(String, default="pending")  # pending, approved, denied, escalated, expired
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)
    
    # Decision Making
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    denied_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_reason = Column(Text, nullable=True)
    denial_reason = Column(Text, nullable=True)
    
    # Emergency Override
    emergency_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    override_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Audit and Tracking
    extra_data = Column(JSON, nullable=True)  # Changed from 'metadata'
    audit_trail = Column(JSON, default=list)
    
    # Relationships
    approver = relationship("User", foreign_keys=[approved_by])
    denier = relationship("User", foreign_keys=[denied_by])
    override_user = relationship("User", foreign_keys=[override_by])

class SystemConfiguration(Base):
    __tablename__ = "system_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(JSON)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Configuration metadata
    config_type = Column(String)  # security, integration, ui, workflow
    is_sensitive = Column(Boolean, default=False)  # For sensitive configs like API keys
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now(UTC))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, DENY
    resource_type = Column(String)  # users, alerts, rules, agent_actions, etc.
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Compliance and Risk
    risk_level = Column(String, nullable=True)
    compliance_impact = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class IntegrationEndpoint(Base):
    __tablename__ = "integration_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    endpoint_type = Column(String)  # siem, webhook, api, sso
    url = Column(String)
    method = Column(String, default="POST")
    headers = Column(JSON, nullable=True)
    authentication = Column(JSON, nullable=True)  # Encrypted auth details
    enabled = Column(Boolean, default=True)
    
    # Configuration
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    rate_limit = Column(Integer, nullable=True)  # Requests per minute
    
    # Monitoring
    last_success = Column(DateTime, nullable=True)
    last_failure = Column(DateTime, nullable=True)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])