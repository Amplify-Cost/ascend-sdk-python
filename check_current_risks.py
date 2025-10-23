from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AgentAction
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Check what risk scores are currently stored
pending = db.query(AgentAction).filter(
    AgentAction.status.in_(["pending", "pending_approval"])
).limit(5).all()

print("Current Risk Scores in Database:")
for action in pending:
    print(f"ID: {action.id}")
    print(f"  Action: {action.action_type}")
    print(f"  Risk Score: {action.risk_score}")
    print(f"  Risk Level: {action.risk_level}")
    print(f"  NIST Control: {getattr(action, 'nist_control', 'Not set')}")
    print(f"  MITRE Technique: {getattr(action, 'mitre_technique', 'Not set')}")
    print("-" * 40)

db.close()
