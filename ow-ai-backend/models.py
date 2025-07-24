from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # ✅ THIS MUST EXIST
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

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
    summary = Column(Text, nullable=True)  # ✅ LLM-generated summary
    tenant_id = Column(String, nullable=True, default="default")  # Added for multi-tenancy

# NEW MODEL FOR AUTHORIZATION SYSTEM
class PendingAgentAction(Base):
    __tablename__ = "pending_agent_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True, default="default")
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
    nist_control = Column(String)
    mitre_tactic = Column(String)
    mitre_technique = Column(String)
    
    # Execution tracking
    executed_at = Column(DateTime)
    execution_result = Column(Text)
    execution_status = Column(String)  # success, failed, partial

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer, ForeignKey("agent_actions.id"))
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    tenant_id = Column(String, nullable=True, default="default")  # Added for multi-tenancy
    status = Column(String, default="new")

class LogAuditTrail(Base):
    __tablename__ = "log_audit_trail"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("agent_actions.id"))
    decision = Column(String, nullable=False)  # "approved" or "rejected"
    reviewed_by = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

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