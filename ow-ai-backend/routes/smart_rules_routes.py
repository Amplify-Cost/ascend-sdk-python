from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import SmartRule
from schemas import SmartRuleOut
from database import get_db
from dependencies import get_current_user, require_admin
from llm_utils import generate_smart_rule
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/smart-rules", tags=["Smart Rules"])

@router.get("", response_model=list[SmartRuleOut])
def list_smart_rules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all smart rules"""
    try:
        return db.query(SmartRule).order_by(SmartRule.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Failed to list smart rules: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve smart rules"
        )

@router.post("/generate")
async def generate_smart_rule_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Generate a new smart rule using AI"""
    try:
        data = await request.json()
        agent_id = data.get("agent_id", "demo-agent")
        action_type = data.get("action_type", "suspicious_activity")
        description = data.get("description", "Analyze security patterns")

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
                "condition": f"action_type == '{action_type}' and risk_level == 'high'",
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

@router.delete("/{rule_id}")
def delete_smart_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Delete a smart rule"""
    try:
        rule = db.query(SmartRule).filter(SmartRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Smart rule not found")
        
        db.delete(rule)
        db.commit()
        
        logger.info(f"Smart rule {rule_id} deleted by {admin_user['email']}")
        return {"message": "Smart rule deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete smart rule: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete smart rule"
        )

@router.post("/seed")
def seed_smart_rules(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """Seed demo smart rules"""
    try:
        demo_rules = [
            SmartRule(
                agent_id="demo-agent-001",
                action_type="data_exfiltration",
                description="Detect potential data exfiltration attempts",
                condition="action_type == 'data_exfiltration' and tool_name in ['curl', 'wget']",
                action="block_and_alert",
                risk_level="high",
                recommendation="Immediately investigate and block network access",
                justification="Data exfiltration attempts pose high security risk",
                created_at=datetime.utcnow()
            ),
            SmartRule(
                agent_id="demo-agent-002",
                action_type="privilege_escalation",
                description="Detect privilege escalation attempts",
                condition="action_type == 'privilege_escalation' and risk_level == 'high'",
                action="quarantine",
                risk_level="high",
                recommendation="Quarantine agent and review permissions",
                justification="Unauthorized privilege escalation must be prevented",
                created_at=datetime.utcnow()
            ),
            SmartRule(
                agent_id="demo-agent-003",
                action_type="suspicious_network",
                description="Monitor unusual network activity",
                condition="tool_name == 'network_scanner' and description contains 'internal'",
                action="monitor_closely",
                risk_level="medium",
                recommendation="Monitor network traffic and log activities",
                justification="Internal network scanning may indicate reconnaissance",
                created_at=datetime.utcnow()
            )
        ]
        
        db.add_all(demo_rules)
        db.commit()
        
        logger.info(f"Demo smart rules seeded by {admin_user['email']}")
        return {"message": f"✅ {len(demo_rules)} demo smart rules seeded"}
    
    except Exception as e:
        logger.error(f"Failed to seed smart rules: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to seed demo rules"
        )