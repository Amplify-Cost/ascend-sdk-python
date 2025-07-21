from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import SmartRule
from schemas import SmartRuleOut
from database import get_db
from datetime import datetime

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

@router.post("/smart-rules/seed")
def seed_smart_rules(db: Session = Depends(get_db)):
    demo_rule = SmartRule(
        agent_id="demo-agent",
        action_type="login_failure",
        description="Multiple failed logins",
        condition="login_attempts > 5",
        action="lock account",
        risk_level="High",
        recommendation="Monitor failed logins",
        justification="Suspicious login activity",
        created_at=datetime.utcnow()
    )
    db.add(demo_rule)
    db.commit()
    return {"message": "✅ Demo SmartRule seeded"}
