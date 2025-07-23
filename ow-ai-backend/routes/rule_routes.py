from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from dependencies import verify_token
from models import Rule, RuleFeedback, AgentAction, LogAuditTrail
from llm_utils import generate_smart_rule
import json
import logging

logger = logging.getLogger(__name__)
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

@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Delete a specific rule"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete rules")
    
    try:
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Also delete associated feedback
        feedback = db.query(RuleFeedback).filter(RuleFeedback.rule_id == rule_id).first()
        if feedback:
            db.delete(feedback)
        
        db.delete(rule)
        db.commit()
        
        logger.info(f"Rule {rule_id} deleted by {user['email']}")
        return {"message": "Rule deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete rule")

@router.get("/feedback/{rule_id}")
def get_rule_feedback(
    rule_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Get audit log/feedback for a specific rule"""
    try:
        # Check if rule exists
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Get feedback data for this rule
        feedback = db.query(RuleFeedback).filter(RuleFeedback.rule_id == rule_id).first()
        
        if not feedback:
            # Create default feedback record if none exists
            feedback = RuleFeedback(
                rule_id=rule_id,
                correct=0,
                false_positive=0
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
        
        # Calculate audit statistics based on actual agent actions
        # For production, we'll look at actions that could be related to this rule
        
        # Parse rule condition to extract relevant filters
        rule_condition = rule.condition or ""
        agent_filter = None
        action_type_filter = None
        
        # Extract agent_id from condition if present
        if "agent_id" in rule_condition and "==" in rule_condition:
            try:
                # Simple parsing: agent_id == 'agent-076'
                parts = rule_condition.split("agent_id == ")
                if len(parts) > 1:
                    agent_part = parts[1].split(" and ")[0].strip("'\"")
                    agent_filter = agent_part
            except:
                pass
        
        # Extract action_type from condition if present
        if "action_type" in rule_condition and "==" in rule_condition:
            try:
                parts = rule_condition.split("action_type == ")
                if len(parts) > 1:
                    action_part = parts[1].split(" and ")[0].strip("'\"")
                    action_type_filter = action_part
            except:
                pass
        
        # Build query based on rule conditions
        base_query = db.query(AgentAction)
        
        if agent_filter:
            base_query = base_query.filter(AgentAction.agent_id == agent_filter)
        if action_type_filter:
            base_query = base_query.filter(AgentAction.action_type == action_type_filter)
        
        # If no specific filters, use all actions (for general rules)
        total_triggered = base_query.count()
        
        # Get status-based counts
        approved_count = base_query.filter(AgentAction.status == "approved").count()
        rejected_count = base_query.filter(AgentAction.status == "rejected").count()
        false_positive_count = base_query.filter(AgentAction.is_false_positive == True).count()
        
        # Get recent audit trail entries for this rule's scope
        recent_actions = base_query.order_by(AgentAction.timestamp.desc()).limit(10).all()
        
        logger.info(f"Rule {rule_id} audit: triggered={total_triggered}, approved={approved_count}, rejected={rejected_count}, false_positives={false_positive_count}")
        
        return {
            "rule_id": rule_id,
            "rule_description": rule.description,
            "rule_condition": rule.condition,
            "total_triggered": total_triggered,
            "approved": approved_count,
            "rejected": rejected_count,
            "false_positives": false_positive_count,
            "feedback_stats": {
                "correct": feedback.correct,
                "false_positive": feedback.false_positive
            },
            "recent_actions": [
                {
                    "id": action.id,
                    "agent_id": action.agent_id,
                    "action_type": action.action_type,
                    "status": action.status,
                    "timestamp": action.timestamp.isoformat() if action.timestamp else None,
                    "reviewed_by": action.reviewed_by
                }
                for action in recent_actions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rule feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule feedback: {str(e)}")

@router.post("/feedback/{rule_id}")
async def update_rule_feedback(
    rule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_token)
):
    """Update feedback for a rule (mark as correct or false positive)"""
    try:
        data = await request.json()
        feedback_type = data.get("type")  # "correct" or "false_positive"
        
        if feedback_type not in ["correct", "false_positive"]:
            raise HTTPException(status_code=400, detail="Invalid feedback type. Use 'correct' or 'false_positive'")
        
        # Check if rule exists
        rule = db.query(Rule).filter(Rule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Get or create feedback record
        feedback = db.query(RuleFeedback).filter(RuleFeedback.rule_id == rule_id).first()
        if not feedback:
            feedback = RuleFeedback(rule_id=rule_id, correct=0, false_positive=0)
            db.add(feedback)
        
        # Update the appropriate counter
        if feedback_type == "correct":
            feedback.correct += 1
        else:
            feedback.false_positive += 1
        
        db.commit()
        
        logger.info(f"Rule {rule_id} feedback updated: {feedback_type} by {user['email']}")
        return {
            "message": f"Feedback recorded: {feedback_type}",
            "updated_stats": {
                "correct": feedback.correct,
                "false_positive": feedback.false_positive
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rule feedback: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update feedback")

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

        # Generate smart rule using AI
        try:
            rule_data = generate_smart_rule(agent_id, action_type, description)
            logger.info(f"Smart rule generated for {agent_id}/{action_type}")
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