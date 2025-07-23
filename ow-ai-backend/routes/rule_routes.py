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
# Add this to your rule_routes.py file at the end

@router.post("/generate-smart-rule")
async def generate_smart_rule_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Generate smart rule endpoint for backward compatibility"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        data = await request.json()
        agent_id = data.get("agent_id", "demo-agent")
        action_type = data.get("action_type", "suspicious_activity")
        description = data.get("description", "Analyze security patterns")

        # Import here to avoid circular imports
        from llm_utils import generate_smart_rule
        
        # Generate smart rule using AI
        try:
            rule_data = generate_smart_rule(agent_id, action_type, description)
        except Exception as e:
            logger.warning(f"AI rule generation failed: {e}")
            # Fallback rule generation
            rule_data = {
                "agent_id": agent_id,
                "action_type": action_type,
                "description": description,
                "condition": f"agent_id == '{agent_id}' and action_type == '{action_type}'",
                "action": "alert_admin",
                "risk_level": "high",
                "recommendation": "Review this activity pattern for security implications",
                "justification": "Generated based on common security patterns"
            }

        return rule_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart rule generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate smart rule"
        )