# seed_logs.py
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import AgentLog
import time

Base.metadata.create_all(bind=engine)

def seed():
    db: Session = SessionLocal()

    test_logs = [
        AgentLog(
            agent_id="agent_001",
            timestamp=time.time(),
            action_type="access_sensitive_file",
            description="Accessed /etc/passwd",
            tool_name="AuditTool",
            status="pending",
            risk_level="high",
            nist_control="AC-6",
            nist_description="Least Privilege",
            mitre_tactic="Privilege Escalation",
            mitre_technique="T1548",
            recommended_action="Restrict access to sensitive files and monitor access logs."
        ),
        AgentLog(
            agent_id="agent_002",
            timestamp=time.time(),
            action_type="network_scan",
            description="Performed network scan on internal subnet",
            tool_name="Nmap",
            status="pending",
            risk_level="medium",
            nist_control="SI-4",
            nist_description="Information System Monitoring",
            mitre_tactic="Discovery",
            mitre_technique="T1046",
            recommended_action="Flag unusual network scans and alert security teams."
        )
    ]

    db.add_all(test_logs)
    db.commit()
    db.close()
    print("✅ Seeded logs with security metadata.")

if __name__ == "__main__":
    seed()
