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
    
    try:
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
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to add rule: {str(e)}")

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

# ADD THIS NEW ROUTE FOR BACKWARD COMPATIBILITY
@router.post("/generate-smart-rule")
async def generate_smart_rule_old_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Temporary route for backward compatibility with old frontend"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Import here to avoid circular imports
        from routes.smart_rules_routes import generate_smart_rule_endpoint
        from dependencies import require_admin
        
        # Call the actual smart rule generation function
        return await generate_smart_rule_endpoint(request, db, user)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate smart rule: {str(e)}")