from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import SmartRule
from schemas import SmartRuleOut
from database import get_db
from datetime import datetime
# If you ever need raw SQL, import this:
# from sqlalchemy import text

router = APIRouter()

@router.get("/smart-rules", response_model=list[SmartRuleOut])
def list_smart_rules(db: Session = Depends(get_db)):
    return db.query(SmartRule).order_by(SmartRule.created_at.desc()).all()

@router.delete("/smart-rules/{rule_id}")
def delete_smart_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(SmartRule).filter(SmartRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Smart rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Smart rule deleted"}

@router.post("/test-add-smart-rule")
def add_test_rule(db: Session = Depends(get_db)):
    rule = SmartRule(
        agent_id="test-agent",
        action_type="network_access",
        description="Agent accessed external domain",
        condition="if domain not in allowlist",
        action="flag for review",
        risk_level="High",
        recommendation="Block unapproved domains",
        justification="Unusual outbound traffic",
        created_at=datetime.utcnow()
    )
    db.add(rule)
    db.commit()
    return {"message": "Test rule added"}

# 🛠️ NOTE: If you ever use raw SQL like this:
# db.execute("INSERT INTO smart_rules (...) VALUES (...)")
# You must do:
# db.execute(text("INSERT INTO smart_rules (...) VALUES (...)"))
