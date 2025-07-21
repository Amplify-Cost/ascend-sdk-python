from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from dependencies import verify_token
from models import Rule
import json

router = APIRouter()

@router.get("/rules")
def get_rules(db: Session = Depends(get_db), _: dict = Depends(verify_token)):
    return db.query(Rule).order_by(Rule.created_at.desc()).all()

@router.post("/rules")
async def add_rule(request: Request, db: Session = Depends(get_db), user: dict = Depends(verify_token)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add rules")
    data = await request.json()

    if isinstance(data, list):
        for rule_data in data:
            rule = Rule(**rule_data)
            db.add(rule)
    else:
        rule = Rule(**data)
        db.add(rule)

    db.commit()
    return {"message": "✅ Rule(s) added"}

@router.post("/rules/seed")
def seed_rules(db: Session = Depends(get_db)):
    demo_rules = [
        Rule(
            description="Block suspicious outbound requests",
            condition="if outbound to unknown domains",
            action="alert admin",
            risk_level="High",
            recommendation="Restrict outbound network activity",
            justification="Prevent exfiltration attempts"
        ),
        Rule(
            description="Flag excessive login attempts",
            condition="if login attempts > 5 in 1hr",
            action="lock account",
            risk_level="Medium",
            recommendation="Monitor and lock",
            justification="Potential brute-force attack"
        )
    ]
    db.add_all(demo_rules)
    db.commit()
    return {"message": "✅ Demo rules seeded"}
