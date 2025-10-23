import json
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, UTC
from database import get_db
from dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

async def ingest_mcp_action(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        action = data.get("action", "")
        resource = data.get("resource", "")
        risk_score = 30.0
        
        if any(term in action.lower() for term in ["delete", "write", "modify"]):
            risk_score += 40.0
        if any(term in resource.lower() for term in ["database", "config", "secret"]):
            risk_score += 30.0
        risk_score = min(100.0, risk_score)
        
        result = db.execute(text("""
            INSERT INTO agent_actions (
                agent_id, action_type, description, risk_level, risk_score,
                policy_id, result, metadata, status
            ) VALUES (
                :agent_id, :action_type, :description, :risk_level, :risk_score,
                :policy_id, :result, :metadata, :status
            ) RETURNING id
        """), {
            'agent_id': data.get("agent_id", "unknown"),
            'action_type': data.get("action", "mcp_action"),
            'description': f"MCP: {resource}",
            'risk_level': "high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
            'risk_score': risk_score,
            'policy_id': data.get("policy_id", "mcp_default"),
            'result': "approved" if risk_score < 40 else "pending_approval",
            'metadata': json.dumps(data),
            'status': "pending" if risk_score > 40 else "approved"
        })
        
        action_id = result.fetchone()[0]
        
        if risk_score > 40:
            db.execute(text("INSERT INTO approvals (agent_action_id, status) VALUES (:action_id, 'pending')"), 
                      {'action_id': action_id})
        
        db.commit()
        return {
            "action_id": action_id,
            "result": "approved" if risk_score < 40 else "requires_approval",
            "risk_score": risk_score,
            "status": "success"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"MCP ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_agents_activity(limit: int = 50, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT id, agent_id, action_type, description, risk_level, 
                   risk_score, result, policy_id, created_at, status
            FROM agent_actions 
            ORDER BY created_at DESC NULLS LAST, id DESC LIMIT :limit
        """), {'limit': limit}).fetchall()
        
        return [{
            "id": row[0],
            "agent_id": row[1] or "unknown",
            "action_type": row[2] or "action", 
            "description": row[3] or "No description",
            "risk_level": row[4] or "medium",
            "risk_score": float(row[5]) if row[5] else 50.0,
            "result": row[6] or "pending",
            "policy_id": row[7] or "default",
            "created_at": row[8].isoformat() if row[8] else datetime.now(UTC).isoformat(),
            "status": row[9] or "pending"
        } for row in result]
    except Exception as e:
        logger.error(f"Get activity failed: {e}")
        return []
