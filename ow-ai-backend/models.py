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
    agent_id = Column(String, nullable)
    role = Column(String, default="user")  # user, admin, security_admin, emergency_approver
    approval_level = Column(Integer, default=1)  # 1=basic, 2=senior, 3=executive
    created_at = Column(DateTime, default=datetime.utcnow)
    is_emergency_approver = Column(Boolean, default=False)
    max_risk_approval = Column(Integer, default=50)  # Max risk score they can approve
    
    # Relationships
    approved_actions = relationship("PendingAgentAction", foreign_keys="PendingAgentAction.approved_by_user_id")

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

# ENHANCED: Advanced Authorization System
class PendingAgentAction(Base):
    __tablename__ = "pending_agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Action Info
    agent_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    description = Column(Text)
    tool_name = Column(String)
    risk_level = Column(String)  # low, medium, high, critical
    
    # Enhanced Risk Assessment
    ai_risk_score = Column(Integer)  # 0-100 AI-calculated risk
    human_risk_score = Column(Integer)  # Human-reviewed risk score
    contextual_risk_factors = Column(JSON)  # Store risk factors as JSON
    
    # Action Payload & Targeting
    action_payload = Column(Text)  # JSON string of action parameters
    target_system = Column(String)  # What system the action targets
    affected_resources = Column(JSON)  # List of affected resources
    
    # ENHANCED: Multi-Level Approval Workflow
    authorization_status = Column(String, default="pending")  # pending, approved, denied, escalated, emergency_approved
    workflow_stage = Column(String, default="initial")  # initial, level_1, level_2, executive, emergency
    required_approval_level = Column(Integer, default=1)  # 1, 2, 3 based on risk
    current_approval_level = Column(Integer, default=0)  # Current level achieved
    
    # Timing & Expiration
    requested_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-deny after expiration
    auto_approve_at = Column(DateTime)  # Emergency auto-approval time
    
    # Approval Chain
    approval_chain = Column(JSON)  # Store approval history
    required_approvers = Column(JSON)  # List of required approver user IDs
    pending_approvers = Column(JSON)  # Current pending approvers
    
    # Human Oversight
    primary_approver_id = Column(Integer, ForeignKey("users.id"))
    approved_by_user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Conditional Approval Features
    conditional_approval = Column(Boolean, default=False)
    conditions = Column(JSON)  # Time limits, scope restrictions, etc.
    approval_duration = Column(Integer)  # Minutes the approval is valid
    approval_scope = Column(JSON)  # Specific limitations on the approval
    
    # Compliance & Audit
    compliance_frameworks = Column(JSON)  # NIST, SOC2, etc.
    nist_control = Column(String)
    mitre_tactic = Column(String)
    mitre_technique = Column(String)
    audit_trail = Column(JSON)  # Complete action history
    
    # Emergency Procedures
    is_emergency = Column(Boolean, default=False)
    emergency_justification = Column(Text)
    emergency_approver_id = Column(Integer, ForeignKey("users.id"))
    break_glass_used = Column(Boolean, default=False)
    
    # Execution Tracking
    executed_at = Column(DateTime)
    execution_result = Column(Text)
    execution_status = Column(String)  # success, failed, partial, timeout
    execution_duration = Column(Float)  # Seconds
    
    # Relationships
    primary_approver = relationship("User", foreign_keys=[primary_approver_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by_user_id])
    emergency_approver = relationship("User", foreign_keys=[emergency_approver_id])

# NEW: Approval Workflow Templates
class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Trigger Conditions
    risk_score_min = Column(Integer, default=0)
    risk_score_max = Column(Integer, default=100)
    action_types = Column(JSON)  # List of action types this applies to
    target_systems = Column(JSON)  # List of target systems
    time_restrictions = Column(JSON)  # After hours, weekends, etc.
    
    # Workflow Configuration
    approval_levels = Column(JSON)  # Definition of approval levels required
    required_approvers_per_level = Column(JSON)  # How many approvers needed per level
    escalation_timeout = Column(Integer, default=60)  # Minutes before escalation
    auto_deny_timeout = Column(Integer, default=1440)  # Minutes before auto-deny
    
    # Emergency Procedures
    allows_emergency_override = Column(Boolean, default=True)
    emergency_timeout = Column(Integer, default=15)  # Minutes for emergency approval
    break_glass_enabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# NEW: Approval Rules Engine
class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Rule Conditions (JSON-based rule engine)
    conditions = Column(JSON)  # Complex rule conditions
    actions = Column(JSON)  # What to do when rule matches
    
    # Risk-based routing
    risk_thresholds = Column(JSON)  # Risk score ranges
    approval_routing = Column(JSON)  # Where to route based on conditions
    
    # Time-based rules
    business_hours_only = Column(Boolean, default=False)
    weekend_restrictions = Column(Boolean, default=False)
    holiday_restrictions = Column(Boolean, default=False)
    
    # Priority and ordering
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Enhanced Alert System
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer, ForeignKey("agent_actions.id"))
    pending_action_id = Column(Integer, ForeignKey("pending_agent_actions.id"))  # NEW: Link to pending actions
    
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    status = Column(String, default="new")  # new, acknowledged, investigating, resolved
    
    # Enhanced alert features
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime)
    escalated_to = Column(String)
    auto_escalate_minutes = Column(Integer, default=30)
    
    # Notification tracking
    notifications_sent = Column(JSON)  # Track who was notified when
    acknowledged_by = Column(String)
    acknowledged_at = Column(DateTime)
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime)

# Audit and Compliance
class LogAuditTrail(Base):
    __tablename__ = "log_audit_trail"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("agent_actions.id"))
    pending_action_id = Column(Integer, ForeignKey("pending_agent_actions.id"))
    
    # Enhanced audit fields
    event_type = Column(String, nullable=False)  # approval, denial, escalation, execution
    decision = Column(String, nullable=False)  # approved, rejected, escalated, executed
    decision_reason = Column(Text)
    
    # User and timing
    user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_by = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Context and metadata
    context = Column(JSON)  # Additional context about the decision
    risk_assessment = Column(JSON)  # Risk factors considered
    compliance_notes = Column(Text)
    
    # IP and session tracking
    ip_address = Column(String)
    user_agent = Column(String)
    session_id = Column(String)

# Remaining models stay the same...
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


