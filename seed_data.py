from sqlalchemy.orm import Session
from database import SessionLocal
from models import AgentAction, Alert, Log
from datetime import datetime, UTC
import random

def seed_data():
    db: Session = SessionLocal()

    try:
        # Seed AgentAction records
        for i in range(10):
            agent_action = AgentAction(
                user_id=1,  # ensure a user with ID=1 exists
                agent_id=f"agent_{i}",
                action_type=random.choice(["READ", "WRITE", "EXECUTE"]),
                description=f"Test description {i}",
                tool_name=f"Tool {i}",
                timestamp=datetime.now(UTC),
                risk_level=random.choice(["low", "medium", "high"]),
                rule_id=random.randint(1, 5),
                nist_control="AC-1",
                nist_description="Access Control Policy and Procedures",
                mitre_tactic="Initial Access",
                mitre_technique="Phishing",
                recommendation="Use MFA and train employees on phishing attacks.",
                status="pending",
                notes="Seeded data",
                is_false_positive=False,
                approved=False,
                reviewed_by=None,
                reviewed_at=None,
            )
            db.add(agent_action)

        # Seed Alert records
        for i in range(5):
            alert = Alert(
                agent_action_id=i + 1,
                alert_type="Suspicious Behavior",
                severity=random.choice(["low", "medium", "high"]),
                message=f"Suspicious activity detected {i}",
                created_at=datetime.now(UTC),
                timestamp=datetime.now(UTC),
            )
            db.add(alert)

        # Seed Log records
        for i in range(5):
            log = Log(
                level="INFO",
                message=f"System log entry {i}",
                source="seed_data.py",
                timestamp=datetime.now(UTC),
            )
            db.add(log)

        db.commit()
        print("✅ Seed data inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
