from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func, JSON, Float, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta
from database import Base


class User(Base):
    """
    Enterprise User Model with Multi-Tenant Isolation

    SEC-025: Banking-Level Security Architecture
    ============================================
    - Email uniqueness is PER-ORGANIZATION (not global)
    - Same email can exist in multiple organizations as separate users
    - Each organization has isolated Cognito user pool
    - Cognito user_id is the primary identity link within an org

    Compliance: SOC 2 CC6.1, NIST AC-2, PCI-DSS 7.1
    """
    __tablename__ = "users"

    # SEC-025: Composite unique constraint for multi-tenant email isolation
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_users_email_organization'),
    )

    id = Column(Integer, primary_key=True, index=True)
    # SEC-025: Email is unique per-organization, not globally
    # Index maintained for fast lookups, uniqueness enforced by composite constraint
    email = Column(String, index=True, nullable=False)
    password = Column(String)  # Changed from hashed_password to match auth_routes.py
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(UTC))
    last_login = Column(DateTime, nullable=True)

    # PHASE 2 RBAC: Account lockout and password management
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    login_attempts = Column(Integer, default=0, nullable=False)  # Total successful logins
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_last_changed = Column(DateTime, nullable=True)
    force_password_change = Column(Boolean, default=False, nullable=False)

    # Enterprise authorization fields that main.py expects
    approval_level = Column(Integer, default=1)
    is_emergency_approver = Column(Boolean, default=False)
    max_risk_approval = Column(Integer, default=50)

    # PHASE 2: AWS Cognito Integration
    cognito_user_id = Column(String(255), unique=True, nullable=True, index=True)
    # Note: Using existing last_login and login_attempts columns from production schema

    # PHASE 2: Multi-Tenancy - organization_id is part of email uniqueness constraint
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    is_org_admin = Column(Boolean, default=False, nullable=False)

    # SEC-046 Phase 2: User Profile Extended Fields
    # Compliance: SOC 2 CC6.1, HIPAA 164.312, PCI-DSS 8.1
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    job_title = Column(String(100), nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # SEC-046 Phase 2: User Suspension Management
    # Banking-level: Suspend without delete for audit compliance
    is_suspended = Column(Boolean, default=False, nullable=False, index=True)
    suspended_at = Column(DateTime, nullable=True)
    suspended_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    suspension_reason = Column(String(500), nullable=True)

    # SEC-046 Phase 2: Session & Token Management
    # Banking-level: Token versioning for force logout compliance
    token_version = Column(Integer, default=0, nullable=False)
    last_logout = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)

    # SEC-071: Admin Console - MFA Status Tracking
    # Compliance: SOC 2 CC6.1, NIST IA-2, PCI-DSS 8.3
    mfa_enabled = Column(Boolean, default=False, nullable=False)

    # Relationships

    logs = relationship("Log", back_populates="user")
    # SEC-071: Explicit foreign_keys to disambiguate from Organization.owner_user_id
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    # SEC-066: Enterprise Unified Metrics audit relationship
    metric_audits = relationship("MetricCalculationAudit", back_populates="user")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, index=True)
    severity = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(UTC))
    agent_id = Column(String, index=True)
    agent_action_id = Column(Integer, nullable=True)
    status = Column(String, default="new")
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    escalated_by = Column(String, nullable=True)
    escalated_at = Column(DateTime, nullable=True)

    # SEC-021: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # A/B Test Tracking (for real metrics)
    ab_test_id = Column(String(100), nullable=True, index=True)  # UUID of A/B test
    evaluated_by_variant = Column(String(20), nullable=True, index=True)  # 'variant_a' or 'variant_b'
    variant_rule_id = Column(Integer, nullable=True, index=True)  # Which variant rule evaluated this
    detected_by_rule_id = Column(Integer, nullable=True, index=True)  # Which rule detected this
    detection_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    is_true_positive = Column(Boolean, nullable=True)  # NULL = not yet determined
    is_false_positive = Column(Boolean, default=False)

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

    # SEC-021: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
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

    # SEC-046: Performance tracking for analytics
    processing_time_ms = Column(Integer, nullable=True, index=True)
    nist_description = Column(Text, nullable=True)
    mitre_tactic = Column(String(255), nullable=True)
    mitre_technique = Column(String(255), nullable=True)
    recommendation = Column(Text, nullable=True)
    target_system = Column(String(255), nullable=True)
    target_resource = Column(String(255), nullable=True)

    # ARCH-001: CVSS v3.1 Integration fields
    cvss_score = Column(Float, nullable=True)           # 0.0-10.0 (official NIST base score)
    cvss_severity = Column(String(20), nullable=True)   # NONE|LOW|MEDIUM|HIGH|CRITICAL
    cvss_vector = Column(String(255), nullable=True)    # CVSS:3.1/AV:N/AC:L/PR:L/...

    # SEC-021: Policy evaluation fields (match production)
    created_by = Column(String(255), nullable=True)
    policy_evaluated = Column(Boolean, default=False)
    policy_decision = Column(String(50), nullable=True)
    # SEC-045: Decision column for analytics (ALLOW, DENY, PENDING)
    decision = Column(String(50), nullable=True, index=True)
    policy_risk_score = Column(Integer, nullable=True)
    risk_fusion_formula = Column(Text, nullable=True)
    
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

    # 🏢 ENTERPRISE: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # SEC-045: Rule enabled status for filtering
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)

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
    """
    SEC-044: Enterprise Audit Log with Multi-Tenant Isolation

    Banking-Level Compliance: SOC 2 CC6.1, HIPAA 164.312(b), PCI-DSS 10.2, SOX 302/404
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    # SEC-044: Multi-tenant isolation for audit trails
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, DENY
    resource_type = Column(String)  # users, alerts, rules, agent_actions, etc.
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)  # SEC-044: Track field-level changes
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # SEC-044: Audit timestamp for compliance
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)

    # Compliance and Risk
    risk_level = Column(String, nullable=True)
    compliance_impact = Column(String, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])

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
    """
    Enterprise Workflow Orchestration Model

    Stores multi-step workflow orchestrations for complex agent action processing.
    Enables dynamic workflow execution with full audit trails and compliance tracking.

    Business Value:
    - Enforces multi-level approval workflows
    - Ensures compliance with regulatory requirements
    - Complete audit trail for enterprise governance
    - SLA tracking and escalation management

    Example Use Cases:
    - High-risk action approval workflows
    - Critical incident response workflows
    - Compliance-focused data access workflows
    """
    __tablename__ = "workflows"

    # Primary identification
    id = Column(String(255), primary_key=True, index=True)  # e.g., "wf-high-risk-approval"
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # Status and configuration
    status = Column(String(50), default='active', index=True)  # active|inactive|disabled|maintenance
    created_by = Column(String(255))  # User/system that created this workflow
    owner = Column(String(255))  # Team responsible for this workflow

    # Workflow definition (stored as JSON)
    steps = Column(JSON)  # Ordered list of workflow steps with actions/approvals
    trigger_conditions = Column(JSON)  # When to execute: {"risk_score": {"min": 50}, "action_types": [...]}
    workflow_metadata = Column(JSON)  # Additional metadata for flexibility

    # SLA and execution tracking
    sla_hours = Column(Integer, default=24)  # Service Level Agreement in hours
    auto_approve_on_timeout = Column(Boolean, default=False)  # Auto-approve if SLA exceeded
    last_executed = Column(DateTime, nullable=True, index=True)
    execution_count = Column(Integer, default=0)  # Total number of executions
    success_rate = Column(Float, default=0.0)  # Calculated success rate (0-100)
    avg_completion_time_hours = Column(Float, nullable=True)  # Average time to complete

    # Compliance and governance
    compliance_frameworks = Column(JSON)  # ["SOX", "PCI-DSS", "HIPAA", "GDPR"]
    tags = Column(JSON)  # ["high-risk", "multi-approval", "24x7"]

    # 🏢 ENTERPRISE: Workflow Configuration Fields (Real-time editable)
    risk_threshold_min = Column(Integer, nullable=True)  # Min risk score (0-100)
    risk_threshold_max = Column(Integer, nullable=True)  # Max risk score (0-100)
    approval_levels = Column(Integer, default=1)  # Required approval count (1-5)
    approvers = Column(JSONB)  # List of approver emails/user IDs
    timeout_hours = Column(Integer, default=24)  # Workflow timeout in hours
    emergency_override = Column(Boolean, default=False)  # Allow emergency overrides
    escalation_minutes = Column(Integer, default=480)  # Time before escalation
    is_active = Column(Boolean, default=True, index=True)  # Workflow enabled/disabled
    modified_by = Column(String(255), nullable=True)  # Last user to modify
    last_modified = Column(DateTime, nullable=True)  # Last modification time

    # SEC-017: ENTERPRISE Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

class WorkflowExecution(Base):
    """
    Workflow Execution tracking model.

    SEC-076: Added organization_id for multi-tenant isolation.
    Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312
    """
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
    # SEC-076: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)


class WorkflowStep(Base):
    """
    Workflow Step definition model.

    SEC-076: Added organization_id for multi-tenant isolation.
    Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312
    """
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String, ForeignKey('workflows.id'))
    step_order = Column(Integer)
    step_name = Column(String)
    step_type = Column(String)
    timeout_hours = Column(Integer, default=24)
    conditions = Column(JSON)
    created_at = Column(DateTime, default=datetime.now(UTC))
    # SEC-076: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)    
class EnterprisePolicy(Base):
    """
    Enterprise Policy Model for MCP Governance

    SEC-015: Added organization_id for multi-tenant isolation
    Banking-Level: SOC 2 CC6.1, NIST AC-3, PCI-DSS 7.1
    """
    __tablename__ = "enterprise_policies"

    id = Column(Integer, primary_key=True, index=True)
    # SEC-015: ENTERPRISE Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
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


class PolicyEvaluation(Base):
    """
    Policy Evaluation Tracking Model

    Tracks every policy evaluation for compliance audit trail and analytics.
    Enables real-time metrics, forensic analysis, and policy effectiveness measurement.

    Business Value:
    - SOX/HIPAA/PCI-DSS/GDPR compliance through complete audit trail
    - Real-time policy effectiveness monitoring
    - Security incident forensics with full evaluation history
    - Performance optimization through evaluation metrics

    Example Use Cases:
    - Compliance audits requiring proof of authorization decisions
    - Security investigations tracking unauthorized access attempts
    - Policy performance analysis identifying slow or inefficient policies
    - Risk analytics measuring policy coverage and effectiveness
    """
    __tablename__ = "policy_evaluations"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)

    # References
    policy_id = Column(Integer, ForeignKey('enterprise_policies.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Evaluation Request
    principal = Column(String(512), nullable=False)  # User/service making request
    action = Column(String(255), nullable=False, index=True)  # Action attempted
    resource = Column(String(512), nullable=False)  # Resource accessed

    # Evaluation Result
    decision = Column(String(50), nullable=False, index=True)  # ALLOW, DENY, REQUIRE_APPROVAL
    allowed = Column(Boolean, nullable=False, default=False, index=True)  # Boolean for quick queries

    # Performance Metrics
    evaluation_time_ms = Column(Integer, nullable=True)  # Evaluation latency
    cache_hit = Column(Boolean, default=False)  # Was result from cache

    # Policy Matching (JSONB for flexible querying)
    policies_triggered = Column(JSONB, nullable=True)  # [{policy_id, policy_name, effect}]
    matched_conditions = Column(JSONB, nullable=True)  # {environment: "production", risk_level: "high"}

    # Timestamps
    evaluated_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)

    # Additional Context
    context = Column(JSONB, nullable=True)  # Full request context for forensic analysis
    error_message = Column(Text, nullable=True)  # If evaluation failed

    # SEC-076: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Relationships
    policy = relationship("EnterprisePolicy", foreign_keys=[policy_id])
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<PolicyEvaluation(id={self.id}, decision={self.decision}, policy_id={self.policy_id})>"


class AutomationPlaybook(Base):
    """
    Enterprise Automation Playbook Model
    
    Stores automated response playbooks for agent action processing.
    Enables dynamic automation rules with full audit trails.
    
    Business Value:
    - 60-80% reduction in manual approvals
    - ~$45 cost savings per automated action
    - Consistent policy enforcement
    - Perfect compliance audit trail
    
    Example Use Cases:
    - Auto-approve low-risk actions during business hours
    - Auto-escalate high-risk actions after hours
    - Auto-notify security team for critical events
    """
    __tablename__ = "automation_playbooks"
    
    # Primary identification
    id = Column(String(255), primary_key=True, index=True)  # e.g., "pb-001", "pb-high-risk-auto"
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)

    # SEC-074: Enterprise Multi-Tenant Isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)
    
    # Status and risk management
    status = Column(String(50), default='active', index=True)  # active|inactive|disabled|maintenance
    risk_level = Column(String(50), default='medium', index=True)  # low|medium|high|critical
    approval_required = Column(Boolean, default=False)
    
    # Playbook configuration (stored as JSON)
    trigger_conditions = Column(JSON)  # When to execute: {"risk_score": {"min": 80}, "action_type": [...]}
    actions = Column(JSON)  # What to do: [{"type": "escalate", "params": {...}}, ...]
    
    # Execution tracking
    last_executed = Column(DateTime, nullable=True)
    execution_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Calculated from execution history (0-100)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    # 🏢 ENTERPRISE: Soft Delete (Phase 4)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    deletion_reason = Column(Text, nullable=True)

    # Relationships
    executions = relationship("PlaybookExecution", back_populates="playbook", cascade="all, delete-orphan")

class PlaybookExecution(Base):
    """
    Playbook Execution History and Audit Trail
    
    Records every execution of an automation playbook for:
    - Compliance audit trails
    - Success rate calculation
    - Troubleshooting failed automations
    - Performance analytics
    
    Each execution represents one time a playbook was triggered
    and includes complete details of input, output, and duration.
    """
    __tablename__ = "playbook_executions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # SEC-074: Enterprise Multi-Tenant Isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True, index=True)

    # Playbook reference
    playbook_id = Column(String(255), ForeignKey('automation_playbooks.id'), nullable=False, index=True)

    # Execution context
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    execution_context = Column(String(50), default='manual')  # manual|automatic|scheduled|trigger
    input_data = Column(JSON)  # Data that triggered the playbook
    
    # Execution results
    execution_status = Column(String(50), index=True)  # pending|running|completed|failed|cancelled
    execution_details = Column(JSON)  # Step-by-step results
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, default=datetime.now(UTC), index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Relationships
    playbook = relationship("AutomationPlaybook", back_populates="executions")


# ARCH-001: CVSS v3.1 Assessment Model
class CVSSAssessment(Base):
    """
    Stores detailed CVSS v3.1 metric breakdowns for agent actions.
    Provides audit trail for compliance reporting (SOX, PCI-DSS, HIPAA).
    """
    __tablename__ = "cvss_assessments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("agent_actions.id", ondelete="CASCADE"), nullable=False)

    # CVSS v3.1 Base Metrics (8 required metrics)
    attack_vector = Column(String(20), nullable=False)          # NETWORK|ADJACENT|LOCAL|PHYSICAL
    attack_complexity = Column(String(20), nullable=False)      # LOW|HIGH
    privileges_required = Column(String(20), nullable=False)    # NONE|LOW|HIGH
    user_interaction = Column(String(20), nullable=False)       # NONE|REQUIRED
    scope = Column(String(20), nullable=False)                  # UNCHANGED|CHANGED
    confidentiality_impact = Column(String(20), nullable=False) # NONE|LOW|HIGH
    integrity_impact = Column(String(20), nullable=False)       # NONE|LOW|HIGH
    availability_impact = Column(String(20), nullable=False)    # NONE|LOW|HIGH

    # Calculated Scores (from official NIST formula)
    base_score = Column(Float, nullable=False, index=True)      # 0.0-10.0
    severity = Column(String(20), nullable=False, index=True)   # NONE|LOW|MEDIUM|HIGH|CRITICAL
    vector_string = Column(String(100), nullable=False)         # CVSS:3.1/AV:N/AC:L/PR:L/...

    # Metadata
    assessed_by = Column(String(50), nullable=False, default='system')  # system|auto_mapper|manual
    assessed_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    action = relationship("AgentAction", backref="cvss_assessments")


# 🏢 ENTERPRISE RISK SCORING CONFIGURATION MODEL
# Modeled after industry-leading platforms: Wiz.io, Splunk Enterprise Security, Palo Alto Networks
# Provides database-driven, versioned, auditable risk scoring configuration
class RiskScoringConfig(Base):
    """
    Enterprise Risk Scoring Configuration Model

    Provides configurable, versioned risk scoring similar to:
    - Wiz.io: Cloud resource risk scoring with environment-specific weights
    - Splunk Enterprise Security: Risk scoring framework with configurable action weights
    - Palo Alto Networks: Multi-factor threat assessment with component percentages

    Features:
    - Database-driven configuration (not hardcoded)
    - Full version control (config_version)
    - Activation management (is_active flag for safe transitions)
    - Complete audit trail (created_by, activated_by, timestamps)
    - JSONB storage for flexible configuration without schema changes
    - Factory defaults support (is_default flag)
    - RBAC protection (admin-only access)
    """
    __tablename__ = "risk_scoring_configs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # 🏢 ENTERPRISE: Multi-tenant isolation
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # Version Management
    config_version = Column(String(20), nullable=False, index=True)
    algorithm_version = Column(String(20), nullable=False, default="2.0.0")

    # 🔧 ENTERPRISE WEIGHT CONFIGURATIONS
    # Using JSONB for flexibility - allows configuration updates without schema migrations

    # Environment-specific multipliers (like Wiz.io cloud environment risk)
    # Example: {"production": 1.5, "staging": 1.2, "development": 0.8}
    environment_weights = Column(JSONB, nullable=False)

    # Action type weights (like Splunk risk scoring framework)
    # Example: {"database_write": 0.9, "database_delete": 1.0, "system_command": 0.85}
    action_weights = Column(JSONB, nullable=False)

    # Resource sensitivity multipliers (like Palo Alto data classification)
    # Example: {"pii_data": 1.3, "financial": 1.4, "health_records": 1.5}
    resource_multipliers = Column(JSONB, nullable=False)

    # PII detection weights
    # Example: {"contains_ssn": 1.5, "contains_email": 1.1, "contains_phone": 1.2}
    pii_weights = Column(JSONB, nullable=False)

    # Hybrid scoring component percentages
    # Example: {"cvss_weight": 40, "policy_weight": 30, "context_weight": 30}
    component_percentages = Column(JSONB, nullable=False)

    # 📋 CONFIGURATION MANAGEMENT
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False)

    # 📝 ENTERPRISE AUDIT TRAIL
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ENTERPRISE FIX: Add server_default to match database NOT NULL constraint
    # Matches industry standards (Wiz.io, Splunk, Palo Alto) for timestamp tracking
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # Sets timestamp on INSERT (fixes NULL constraint violation)
        onupdate=func.now(),         # Updates timestamp on UPDATE
        nullable=False                # Matches database NOT NULL constraint
    )
    updated_by = Column(String(255), nullable=True)  # Complete audit trail (who modified)

    # Activation tracking (when config was made active)
    activated_by = Column(String(255), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)

    # Optional description for configuration purpose
    description = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<RiskScoringConfig(id={self.id}, version={self.config_version}, active={self.is_active})>"


# ============================================================================
# PHASE 2: AWS Cognito Integration & Multi-Tenancy Models
# ============================================================================

class Organization(Base):
    """
    Organization model for multi-tenant support.

    Each organization represents a separate customer tenant with:
    - Isolated data via PostgreSQL RLS
    - Subscription tier and billing
    - Usage tracking and limits
    - Stripe integration for payments

    Engineer: Donald King (OW-AI Enterprise)
    """
    __tablename__ = "organizations"

    # Primary key and identifiers
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)

    # Subscription and billing
    subscription_tier = Column(String(50), nullable=False, default='pilot')  # pilot, growth, enterprise, mega
    subscription_status = Column(String(50), nullable=False, default='trial')  # trial, active, past_due, cancelled, suspended
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)

    # Usage limits based on subscription tier
    included_api_calls = Column(Integer, nullable=False, default=100000)
    included_users = Column(Integer, nullable=False, default=5)
    included_mcp_servers = Column(Integer, nullable=False, default=3)

    # Overage rates
    overage_rate_per_call = Column(Float, nullable=False, default=0.005)
    overage_rate_per_user = Column(Float, nullable=False, default=50.00)
    overage_rate_per_server = Column(Float, nullable=False, default=100.00)

    # Current usage tracking
    current_month_api_calls = Column(Integer, nullable=False, default=0)
    current_month_overage_calls = Column(Integer, nullable=False, default=0)
    current_month_overage_cost = Column(Float, nullable=False, default=0.00)
    last_usage_reset_date = Column(DateTime, nullable=True)

    # Stripe integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    next_billing_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # User ID who created (platform admin)

    # PHASE 3: AWS Cognito Multi-Pool Integration
    # Enterprise-grade authentication with dedicated Cognito user pool per organization
    cognito_user_pool_id = Column(String(255), nullable=True, unique=True, index=True)
    cognito_app_client_id = Column(String(255), nullable=True, unique=True)
    cognito_domain = Column(String(255), nullable=True, unique=True)
    cognito_region = Column(String(50), nullable=True, default='us-east-2')
    cognito_pool_created_at = Column(DateTime(timezone=True), nullable=True)
    cognito_pool_status = Column(String(50), nullable=True, default='pending')  # pending, active, disabled
    cognito_pool_arn = Column(String(500), nullable=True)
    cognito_mfa_configuration = Column(String(50), nullable=True, default='OPTIONAL')  # OFF, OPTIONAL, ON
    cognito_password_policy = Column(JSONB, nullable=True)
    cognito_advanced_security = Column(Boolean, nullable=True, default=False)

    # PHASE 4: Multi-Tenant Email Domain Mapping
    # Maps email domains to organizations for automatic org detection
    # Example: ['acme.com', 'acme.net'] -> Acme Corp organization
    email_domains = Column(postgresql.ARRAY(String(255)), nullable=True)

    # SEC-071: Admin Console - Organization Owner Tracking
    # Used for permission enforcement in admin_console_routes.py
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    # SEC-071: Explicit foreign_keys to disambiguate from owner_user_id
    users = relationship("User", back_populates="organization", foreign_keys="[User.organization_id]")
    # SEC-023: Phase 4 Compliance Export relationship (required by models_compliance_export.py)
    compliance_exports = relationship("ComplianceExportJob", back_populates="organization")
    # SEC-066: Enterprise Unified Metrics relationships
    metric_audits = relationship("MetricCalculationAudit", back_populates="organization")
    metric_config = relationship("OrgMetricConfig", back_populates="organization", uselist=False)

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, tier={self.subscription_tier})>"


class LoginAttempt(Base):
    """
    Login attempt tracking for brute force detection.

    Tracks all login attempts (successful and failed) for:
    - Brute force attack detection
    - Security monitoring
    - Compliance audit requirements

    Brute force limits:
    - 5 failed attempts per IP in 15 minutes
    - 10 failed attempts per email in 15 minutes

    Engineer: Donald King (OW-AI Enterprise)
    """
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 support (max 45 chars)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=False, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    cognito_user_id = Column(String(255), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    attempted_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<LoginAttempt(email={self.email}, success={self.success}, ip={self.ip_address})>"


class AuthAuditLog(Base):
    """
    Complete authentication audit log for compliance.

    Logs all authentication events including:
    - User logins (Cognito)
    - User logouts
    - Token refreshes
    - API key usage
    - Permission denials

    Used for:
    - SOC2 compliance
    - HIPAA compliance
    - Security incident investigation
    - User activity monitoring

    Engineer: Donald King (OW-AI Enterprise)
    """
    __tablename__ = "auth_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # login, logout, token_refresh, api_key_use, permission_denied
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    cognito_user_id = Column(String(255), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    api_key_id = Column(Integer, nullable=True)  # ForeignKey to api_keys table
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255), nullable=True)
    audit_metadata = Column("metadata", JSON, nullable=True)  # Maps to database column 'metadata', named audit_metadata to avoid SQLAlchemy reserved word
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuthAuditLog(event={self.event_type}, user_id={self.user_id}, success={self.success})>"


class CognitoToken(Base):
    """
    Cognito token tracking for immediate revocation support.

    Tracks all issued JWT tokens to enable:
    - Immediate token revocation (user logout, role change, security incident)
    - Token lifecycle management
    - Session monitoring

    Token types:
    - id: Identity token (user info)
    - access: Access token (API access)
    - refresh: Refresh token (long-lived)

    Engineer: Donald King (OW-AI Enterprise)
    """
    __tablename__ = "cognito_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cognito_user_id = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    token_jti = Column(String(255), nullable=False, unique=True, index=True)  # JWT ID claim (unique identifier)
    token_type = Column(String(50), nullable=False)  # id, access, refresh
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revocation_reason = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<CognitoToken(jti={self.token_jti}, type={self.token_type}, revoked={self.is_revoked})>"


class SupportTicket(Base):
    """
    Support ticket tracking for user issues and requests.

    Enables:
    - Customer support tracking
    - Issue resolution workflow
    - Multi-tenant data isolation
    - Audit trail for compliance

    Engineer: Donald King (OW-AI Enterprise)
    """
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="open", index=True)  # open, in_progress, resolved, closed
    priority = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical
    category = Column(String(100), nullable=True)  # technical, billing, feature_request, bug_report
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    created_at = Column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<SupportTicket(id={self.id}, user_id={self.user_id}, status={self.status}, org_id={self.organization_id})>"


# =============================================================================
# SEC-065: Cross-Module Model Registration
# =============================================================================
# Models defined in separate files are imported here for:
# 1. SQLAlchemy registry - Enables relationship lookups
# 2. Alembic autogenerate - Detects all models for migrations
# 3. Centralized discovery - Single import point for all models
#
# Compliance: SOC 2 CC6.1 - Logical access controls
# =============================================================================

try:
    from models_executive_brief import ExecutiveBrief
except ImportError:
    pass  # Model module may not exist in older deployments

try:
    from models_compliance_export import ComplianceExportJob
except ImportError:
    pass  # Model module may not exist in older deployments

try:
    from models_metrics import MetricCalculationAudit, OrgMetricConfig
except ImportError:
    pass  # SEC-066: Model module may not exist in older deployments

try:
    from models_diagnostics import DiagnosticAuditLog, DiagnosticThreshold
except ImportError:
    pass  # SEC-076: Diagnostics module may not exist in older deployments
