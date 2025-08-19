from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, LargeBinary, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base  # ✅ Use shared Base here

print("LOADING BACKEND MODELS.PY FROM:", __file__)


# ✅ User Model
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(LargeBinary, nullable=False)
    role = Column(String, default="user", nullable=False)

    agent_actions = relationship("AgentAction", back_populates="user", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan")


# ✅ AgentLog Model
class AgentLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String)
    timestamp = Column(Float)
    action_type = Column(String)
    description = Column(String)
    tool_name = Column(String, nullable=True)
    status = Column(String, default="pending")
    risk_level = Column(String, default="medium")
    nist_control = Column(String, nullable=True)
    nist_description = Column(String, nullable=True)


# ✅ AgentAction Model
class AgentAction(Base):
    __tablename__ = "agent_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(String)
    action_type = Column(String)
    description = Column(Text)
    tool_name = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(String)

    rule_id = Column(Integer, nullable=True)

    nist_control = Column(String)
    nist_description = Column(String)
    mitre_tactic = Column(String)
    mitre_technique = Column(String)

    recommendation = Column(String, nullable=True)

    status = Column(String, default="pending")
    notes = Column(String, nullable=True)
    is_false_positive = Column(Boolean, default=False)

    user = relationship("User", back_populates="agent_actions")


# ✅ Alert Model
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alert_type = Column(String)
    description = Column(String)
    severity = Column(String)


# ✅ Log Audit Trail Model
class LogAuditTrail(Base):
    __tablename__ = "audit_trails"

    id = Column(Integer, primary_key=True, index=True)
    agent_action_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)
    performed_by = Column(String)
    notes = Column(String, nullable=True)
    nist_control = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)


# ✅ Rule Feedback
class RuleFeedback(Base):
    __tablename__ = "rule_feedback"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer)
    agent_action_id = Column(Integer)
    decision = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# ✅ Support Ticket
class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    timestamp = Column(Integer)

    user = relationship("User", back_populates="support_tickets")
