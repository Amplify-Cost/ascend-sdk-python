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

    # PHASE 2 RBAC: Account lockout and password management
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_last_changed = Column(DateTime, nullable=True)
    force_password_change = Column(Boolean, default=False, nullable=False)

    # Enterprise authorization fields that main.py expects
    approval_level = Column(Integer, default=1)
    is_emergency_approver = Column(Boolean, default=False)
    max_risk_approval = Column(Integer, default=50)

    # Relationships

    logs = relationship("Log", back_populates="user")

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
    created_by = Column(String(255), nullable=True)  # Enterprise audit trail
    
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

    # ARCH-001: CVSS v3.1 Integration fields
    cvss_score = Column(Float, nullable=True)           # 0.0-10.0 (official NIST base score)
    cvss_severity = Column(String(20), nullable=True)   # NONE|LOW|MEDIUM|HIGH|CRITICAL
    cvss_vector = Column(String(100), nullable=True)    # CVSS:3.1/AV:N/AC:L/PR:L/...

    # Option 4: Policy Fusion fields (Hybrid Layered Architecture)
    policy_evaluated = Column(Boolean, default=False, nullable=True)    # True if policy engine evaluated
    policy_decision = Column(String(50), nullable=True)                 # ALLOW|DENY|REQUIRE_APPROVAL|ESCALATE
    policy_risk_score = Column(Integer, nullable=True)                  # 0-100 policy engine risk score
    risk_fusion_formula = Column(Text, nullable=True)                   # Formula used for risk fusion (80/20 hybrid)

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

class RiskScoringConfig(Base):
    """
    Enterprise Risk Scoring Configuration
    Enables runtime adjustment of risk scoring weights without code deployment
    """
    __tablename__ = "risk_scoring_configs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Version tracking
    config_version = Column(String(20), nullable=False, index=True)
    algorithm_version = Column(String(20), nullable=False)

    # Configuration weights (JSONB for flexibility)
    environment_weights = Column(JSONB, nullable=False)
    action_weights = Column(JSONB, nullable=False)
    resource_multipliers = Column(JSONB, nullable=False)
    pii_weights = Column(JSONB, nullable=False)
    component_percentages = Column(JSONB, nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # Audit trail
    created_at = Column(DateTime, default=datetime.now(UTC))
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    updated_by = Column(String(255), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by = Column(String(255), nullable=True)

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

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.now(UTC), index=True)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

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
