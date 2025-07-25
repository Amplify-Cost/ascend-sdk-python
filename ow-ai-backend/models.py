from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # NEW: Authorization system fields (will be added via migration)
    approval_level = Column(Integer, default=1)  # 1=basic, 2=senior, 3=executive
    is_emergency_approver = Column(Boolean, default=False)
    max_risk_approval = Column(Integer, default=50)  # Max risk score they can approve

class AgentAction(Base):
    __tablename__ = "agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tool_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    risk_level = Column(String, nullable=True)
    rule_id = Column(Integer, nullable=True)
    nist_control = Column(String, nullable=True)
    nist_description = Column(Text, nullable=True)
    mitre_tactic = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)
    recommendation = Column(Text, nullable=True)
    status = Column(String, default="pending")
    notes = Column(Text, nullable=True)
    is_false_positive = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)

# COMPATIBLE: Simple PendingAgentAction for enterprise authorization
class PendingAgentAction(Base):
    __tablename__ = "pending_agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Action Info
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text)
    tool_name = Column(String)
    risk_level = Column(String)
    target_system = Column(String)
    
    # Enhanced Risk Assessment (will be added via migration)
    ai_risk_score = Column(Integer, default=50)
    contextual_risk_factors = Column(Text)  # JSON string
    
    # Multi-Level Approval Workflow (will be added via migration)
    authorization_status = Column(String, default="pending")
    workflow_stage = Column(String, default="initial")
    required_approval_level = Column(Integer, default=1)
    current_approval_level = Column(Integer, default=0)
    
    # Timing & Expiration
    requested_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    auto_approve_at = Column(DateTime)  # Emergency auto-approval time
    
    # Approval Chain (will be added via migration)
    approval_chain = Column(Text)  # JSON string
    required_approvers = Column(Text)  # JSON string
    pending_approvers = Column(Text)  # JSON string
    
    # Human Oversight
    primary_approver_id = Column(Integer, ForeignKey("users.id"))
    approved_by_user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Conditional Approval Features (will be added via migration)
    conditional_approval = Column(Boolean, default=False)
    conditions = Column(Text)  # JSON string
    approval_duration = Column(Integer)  # Minutes
    approval_scope = Column(Text)  # JSON string
    
    # Compliance & Audit (will be added via migration)
    compliance_frameworks = Column(Text)  # JSON string
    nist_control = Column(String)
    mitre_tactic = Column(String)
    mitre_technique = Column(String)
    audit_trail = Column(Text)  # JSON string
    
    # Emergency Procedures (will be added via migration)
    is_emergency = Column(Boolean, default=False)
    emergency_justification = Column(Text)
    emergency_approver_id = Column(Integer, ForeignKey("users.id"))
    break_glass_used = Column(Boolean, default=False)
    
    # Execution Tracking (will be added via migration)
    executed_at = Column(DateTime)
    execution_result = Column(Text)
    execution_status = Column(String)
    execution_duration = Column(Float)  # Seconds
    
    # Data Storage (will be added via migration)
    action_payload = Column(Text)  # JSON string
    affected_resources = Column(Text)  # JSON string

# COMPATIBLE: Keep existing Alert structure but add new fields
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer, ForeignKey("agent_actions.id"))
    pending_action_id = Column(Integer, ForeignKey("pending_agent_actions.id"))  # NEW field
    
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="new")
    
    # Enhanced alert features (will be added via migration)
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime)
    escalated_to = Column(String)
    auto_escalate_minutes = Column(Integer, default=30)
    
    # Notification tracking (will be added via migration)
    notifications_sent = Column(Text)  # JSON string
    acknowledged_by = Column(String)
    acknowledged_at = Column(DateTime)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime)

# Enhanced Audit Trail
class LogAuditTrail(Base):
    __tablename__ = "log_audit_trail"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("agent_actions.id"))
    pending_action_id = Column(Integer, ForeignKey("pending_agent_actions.id"))
    
    # Enhanced audit fields
    event_type = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    decision_reason = Column(Text)
    
    # User and timing
    user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Context and metadata (will be added via migration)
    context = Column(Text)  # JSON string
    risk_assessment = Column(Text)  # JSON string
    compliance_notes = Column(Text)
    
    # Session tracking (will be added via migration)
    ip_address = Column(String)
    user_agent = Column(String)
    session_id = Column(String)

# Keep existing models unchanged
class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, default="INFO")
    message = Column(Text, nullable=False)
    source = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

class RuleFeedback(Base):
    __tablename__ = "rule_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False)
    correct = Column(Integer, default=0)
    false_positive = Column(Integer, default=0)

class SmartRule(Base):
    __tablename__ = "smart_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text)
    condition = Column(Text)
    action = Column(Text)
    risk_level = Column(String)
    recommendation = Column(Text)
    justification = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    condition = Column(String)
    action = Column(String)
    risk_level = Column(String)
    recommendation = Column(String)
    justification = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# NEW: Workflow Templates (optional - can be added later)
class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Trigger Conditions
    risk_score_min = Column(Integer, default=0)
    risk_score_max = Column(Integer, default=100)
    action_types = Column(Text)  # JSON string
    target_systems = Column(Text)  # JSON string
    time_restrictions = Column(Text)  # JSON string
    
    # Workflow Configuration
    approval_levels = Column(Text)  # JSON string
    required_approvers_per_level = Column(Text)  # JSON string
    escalation_timeout = Column(Integer, default=60)
    auto_deny_timeout = Column(Integer, default=1440)
    
    # Emergency Procedures
    allows_emergency_override = Column(Boolean, default=True)
    emergency_timeout = Column(Integer, default=15)
    break_glass_enabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# NEW: Approval Rules Engine (optional - can be added later)
class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Rule Conditions (JSON-based rule engine)
    conditions = Column(Text)  # JSON string
    actions = Column(Text)  # JSON string
    
    # Risk-based routing
    risk_thresholds = Column(Text)  # JSON string
    approval_routing = Column(Text)  # JSON string
    
    # Time-based rules
    business_hours_only = Column(Boolean, default=False)
    weekend_restrictions = Column(Boolean, default=False)
    holiday_restrictions = Column(Boolean, default=False)
    
    # Priority and ordering
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Add this to your models.py file

class PendingAgentAction(Base):
    __tablename__ = "pending_agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text)
    tool_name = Column(String)
    risk_level = Column(String)
    
    # Action details for execution
    action_payload = Column(Text)  # JSON string of action parameters
    target_system = Column(String)  # What system the action targets
    
    # Authorization details
    authorization_status = Column(String, default="pending")
    requested_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-deny after expiration
    
    # Human oversight
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Risk assessment
    ai_risk_score = Column(Integer)  # 0-100 risk score from AI
    contextual_risk_factors = Column(Text)  # JSON string of risk factors
    
    # Multi-level approval workflow
    required_approval_level = Column(Integer, default=1)  # 1-3 levels
    current_approval_level = Column(Integer, default=0)
    workflow_stage = Column(String, default="initial")  # initial, review, approval, execution
    auto_approve_at = Column(DateTime)  # For time-based auto-approval
    
    # Approval chain tracking
    approval_chain = Column(Text)  # JSON array of approvers
    required_approvers = Column(Text)  # JSON array of required approver roles
    pending_approvers = Column(Text)  # JSON array of pending approvers
    primary_approver_id = Column(Integer)
    approved_by_user_id = Column(Integer)
    
    # Conditional approval
    conditional_approval = Column(Boolean, default=False)
    conditions = Column(Text)  # JSON string of approval conditions
    approval_duration = Column(Integer)  # Duration in minutes
    approval_scope = Column(String)  # Scope limitations
    
    # Compliance and audit
    nist_control = Column(String)
    mitre_tactic = Column(String)
    mitre_technique = Column(String)
    compliance_frameworks = Column(Text)  # JSON array
    audit_trail = Column(Text)  # JSON array of all actions taken
    
    # Emergency procedures
    emergency_approver_id = Column(Integer)
    break_glass_used = Column(Boolean, default=False)
    
    # Execution tracking
    executed_at = Column(DateTime)
    execution_result = Column(Text)
    execution_status = Column(String)  # success, failed, partial
    execution_duration = Column(Float)  # Duration in seconds
    
    # Additional metadata
    affected_resources = Column(Text)  # JSON array of affected resources    