from datetime import datetime, UTC
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import AgentAction, Alert, Base

# Re-create tables if needed (optional if already migrated)
Base.metadata.create_all(bind=engine)

# Create DB session
db: Session = SessionLocal()

# Seed AgentAction records
actions = [
    AgentAction(
        user_id=1,  # Change this to a valid user ID in your DB
        agent_id="agent-001",
        action_type="network_scan",
        description="Agent performed a port scan on internal subnet",
        tool_name="Nmap",
        timestamp=datetime.now(UTC),
        risk_level="high",
        rule_id=101,
        nist_control="AC-2",
        nist_description="Ensure only authorized users have access",
        mitre_tactic="Reconnaissance",
        mitre_technique="Active Scanning",
        recommendation="Block scanning IP and review credentials",
        summary="Suspicious scan from agent-001",
    ),
    AgentAction(
        user_id=1,
        agent_id="agent-002",
        action_type="exec_chain",
        description="Agent ran a suspicious script via shell",
        tool_name="CommandShell",
        timestamp=datetime.now(UTC),
        risk_level="medium",
        rule_id=102,
        nist_control="SI-4",
        nist_description="Monitor and analyze operational logs",
        mitre_tactic="Execution",
        mitre_technique="Command and Scripting Interpreter",
        recommendation="Inspect execution history and logs",
        summary="Potential malicious script activity",
    ),
    AgentAction(
        user_id=1,
        agent_id="agent-003",
        action_type="web_access",
        description="Agent accessed an untrusted domain over HTTP",
        tool_name="Browser",
        timestamp=datetime.now(UTC),
        risk_level="low",
        rule_id=103,
        nist_control="SC-7",
        nist_description="Boundary protection mechanisms",
        mitre_tactic="Initial Access",
        mitre_technique="Drive-by Compromise",
        recommendation="Limit HTTP traffic and use secure DNS",
        summary="Non-secure domain access detected",
    )
]

db.add_all(actions)
db.commit()

# Create alerts linked to AgentActions
for action in actions:
    alert = Alert(
        timestamp=action.timestamp,
        created_at=action.timestamp,
        alert_type="Security Alert",
        severity=action.risk_level.upper(),
        message=action.description,
        agent_action_id=action.id,
    )
    db.add(alert)

db.commit()
db.close()

print("✅ Seeded 3 AgentActions and related Alerts.")
