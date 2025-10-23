from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func, JSON, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  # Changed from hashed_password to match auth_routes.py
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    last_login = Column(DateTime, nullable=True)
    
    # Enterprise authorization fields that main.py expects
    approval_level = Column(Integer, default=1)
    is_emergency_approver = Column(Boolean, default=False)
    max_risk_approval = Column(Integer, default=50)
    
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
    
    # Field that main.py expects
    pending_action_id = Column(Integer, nullable=True)
    
    # Foreign key to user who created the alert
    created_by = Column(Integer, ForeignKey("users.id"))
    created_by_user = relationship("User", back_populates="alerts")

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    source = Column(String)  # source component or service
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    extra_data = Column(JSON, nullable=True)  # Changed from 'metadata'
    
    # Relationship
    user = relationship("User", back_populates="logs")

class AgentAction(Base):
    __tablename__ = "agent_actions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core fields (match production exactly)
    agent_id = Column(String(255), nullable=False)
    action_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)
    risk_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)
    approved = Column(Boolean, nullable=True)
    
    # Timestamps (production has both created_at and timestamp)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=func.now())
    timestamp = Column(DateTime(timezone=True), default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # User references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    # JSON fields
    extra_data = Column(JSONB, nullable=True)
    approval_chain = Column(JSONB, default=list)
    
    # Boolean flags
    is_false_positive = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    
    # Enterprise fields
    tool_name = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    nist_control = Column(String(255), nullable=True)
    nist_description = Column(Text, nullable=True)
    mitre_tactic = Column(String(255), nullable=True)
    mitre_technique = Column(String(255), nullable=True)
    recommendation = Column(Text, nullable=True)
    target_system = Column(String(255), nullable=True)
    target_resource = Column(String(255), nullable=True)
    
    # Approval levels
    approval_level = Column(Integer, default=1)
    current_approval_level = Column(Integer, default=0)
    required_approval_level = Column(Integer, default=1)
    
    # Workflow fields
    workflow_id = Column(String, nullable=True)
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=True)
    workflow_stage = Column(String, nullable=True)
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    pending_approvers = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    # name = Column(String, index=True)  # REMOVED - doesn't exist in database
    description = Column(Text)
    rule_type = Column(String)  # detection, prevention, response
    severity = Column(String)  # low, medium, high, critical
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Fields your routes expect
    condition = Column(Text, nullable=True)  # Rule condition
    action = Column(String, nullable=True)   # Action to take
    risk_level = Column(String, nullable=True)  # Risk level
    recommendation = Column(Text, nullable=True)  # Recommendation text
    justification = Column(Text, nullable=True)   # Justification text
    
    # Rule definition (original fields)
    conditions = Column(JSON, nullable=True)  # Rule conditions in JSON format
    actions = Column(JSON, nullable=True)     # Actions to take when rule triggers
    
    # NIST/MITRE framework mapping
    nist_controls = Column(JSON, nullable=True)
    mitre_tactics = Column(JSON, nullable=True)
    mitre_techniques = Column(JSON, nullable=True)
    
    # Rule metrics
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

class SmartRule(Base):
    __tablename__ = "smart_rules"
    
    # ENTERPRISE CORE COLUMNS - Only columns that exist in database
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    action_type = Column(String)
    description = Column(Text)
    condition = Column(Text)
    action = Column(Text)
    risk_level = Column(String)
    recommendation = Column(Text)
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.now(UTC))
    
    # THESE TWO WERE ADDED DURING DATABASE FIXES
    name = Column(String)
    updated_at = Column(DateTime)

class RuleFeedback(Base):
    __tablename__ = "rule_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("rules.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Feedback counters that your routes expect
    correct = Column(Integer, default=0)
    false_positive = Column(Integer, default=0)
    
    # Additional enterprise feedback fields
    feedback_type = Column(String, nullable=True)  # positive, negative, improvement, bug
    rating = Column(Integer, nullable=True)  # 1-5 scale
    comment = Column(Text, nullable=True)
    effectiveness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    # Improvement suggestions
    suggested_changes = Column(JSON, nullable=True)
    priority = Column(String, default="medium")  # low, medium, high, critical
    
    # Relationships
    rule = relationship("Rule", foreign_keys=[rule_id])
    user = relationship("User", foreign_keys=[user_id])

class LogAuditTrail(Base):
    __tablename__ = "log_audit_trails"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type = Column(String)  # agents, actions, alerts, logs
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    
    # Risk and compliance
    risk_level = Column(String, nullable=True)
    compliance_framework = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])

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
    
    # Fields that main.py schema fix expects
    tool_name = Column(String, nullable=True)
    action_payload = Column(Text, nullable=True)
    authorization_status = Column(String, default="pending")
    requested_at = Column(DateTime, default=datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    ai_risk_score = Column(Integer, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result = Column(Text, nullable=True)
    execution_status = Column(String, nullable=True)
    
    # Additional enterprise fields from main.py
    contextual_risk_factors = Column(Text, nullable=True)
    required_approval_level = Column(Integer, default=1)
    current_approval_level = Column(Integer, default=0)
    workflow_stage = Column(String, default="initial")
    auto_approve_at = Column(DateTime, nullable=True)
    approval_chain = Column(JSONB, nullable=True)
    required_approvers = Column(Text, nullable=True)
    pending_approvers = Column(Text, nullable=True)
    primary_approver_id = Column(Integer, nullable=True)
    approved_by_user_id = Column(Integer, nullable=True)
    conditional_approval = Column(Boolean, default=False)
    conditions = Column(Text, nullable=True)
    approval_duration = Column(Integer, nullable=True)
    approval_scope = Column(Text, nullable=True)
    compliance_frameworks = Column(Text, nullable=True)
    audit_trail = Column(Text, nullable=True)
    emergency_approver_id = Column(Integer, nullable=True)
    break_glass_used = Column(Boolean, default=False)
    execution_duration = Column(Float, nullable=True)
    affected_resources = Column(Text, nullable=True)
    
    # Enterprise Authorization Fields
    approval_level_required = Column(Integer, default=1)  # 1-3 approval levels
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
    extra_data = Column(JSON, nullable=True)
    
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


# Add these workflow models to the end of your models.py file

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    status = Column(String, default='active')
    steps = Column(JSON)
    trigger_conditions = Column(JSON)
    workflow_metadata = Column(JSON)

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey('workflows.id'))
    executed_by = Column(String)
    execution_status = Column(String)
    execution_details = Column(JSON)
    action_id = Column(Integer, ForeignKey("agent_actions.id"), nullable=True)
    current_stage = Column(String, nullable=True)
    approval_chain = Column(JSON, nullable=True)
    input_data = Column(JSON)
    started_at = Column(DateTime, default=datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey('workflows.id'))
    step_order = Column(Integer)
    step_name = Column(String)
    step_type = Column(String)
    timeout_hours = Column(Integer, default=24)
    conditions = Column(JSON)
    created_at = Column(DateTime, default=datetime.now(UTC))    
class EnterprisePolicy(Base):
    __tablename__ = "enterprise_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_name = Column(String, nullable=False)
    description = Column(Text)
    effect = Column(String, nullable=False)
    actions = Column(JSON)
    resources = Column(JSON)
    conditions = Column(JSON)
    priority = Column(Integer, default=100)
    status = Column(String, default='active')
    created_by = Column(String)
    created_at = Column(DateTime, default=datetime.now(UTC))
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
