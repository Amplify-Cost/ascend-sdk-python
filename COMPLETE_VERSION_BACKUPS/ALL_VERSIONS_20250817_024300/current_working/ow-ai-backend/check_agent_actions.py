# check_agent_actions.py
from sqlalchemy.orm import Session
from database import SessionLocal
from models import AgentAction

db: Session = SessionLocal()
actions = db.query(AgentAction).all()

print(f"Total Agent Actions: {len(actions)}")
for action in actions:
    print(f"{action.agent_id} - {action.action_type} - {action.timestamp} - {action.risk_level}")
