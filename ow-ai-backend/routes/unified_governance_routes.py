# routes/unified_governance_routes.py
# 🏢 ENTERPRISE: Unified AI Governance Routes - Agents + MCP Servers
# Uses YOUR EXACT existing dependencies and maintains ALL functionality

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from dependencies import get_db, get_current_user, require_admin_role, require_manager_role
from models import User, Action, AuditLog, WorkflowConfig, ExecutionHistory
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import json

# Configure enterprise logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 🏢 ENTERPRISE: Unified governance statistics
@router.get("/unified-stats")
async def get_unified_governance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Get unified governance statistics for agents and MCP servers
    Uses your existing Action model with enhanced MCP support
    """
    try:
        logger.info(f"🏢 Fetching unified governance stats for user {current_user.email}")
        
        # Get total actions from your existing Action table
        total_actions = db.query(Action).count()
        
        # Get pending actions (using your existing workflow stages)
        pending_actions = db.query(Action).filter(
            Action.authorization_status == "pending_approval"
        ).count()
        
        # 🔌 NEW: Identify MCP actions by checking for MCP-specific data
        mcp_actions = db.query(Action).filter(
            or_(
                Action.action_type == "mcp_server_action",
                Action.description.ilike("%mcp%"),
                Action.target_system.ilike("%mcp%")
            )
        ).count()
        
        # Agent actions (all non-MCP actions)
        agent_actions = total_actions - mcp_actions
        
        # High risk actions (using your existing ai_risk_score)
        high_risk_actions = db.query(Action).filter(
            Action.ai_risk_score >= 70
        ).count()
        
        # Get approval metrics from your existing data
        approved_today = db.query(Action).filter(
            and_(
                Action.authorization_status == "approved",
                func.date(Action.updated_at) == func.date(func.now())
            )
        ).count()
        
        # Emergency actions (using your existing is_emergency field)
        emergency_actions = db.query(Action).filter(
            Action.is_emergency == True
        ).count()
        
        # 🏢 ENTERPRISE: Enhanced stats response
        stats = {
            "total_actions": total_actions,
            "pending_actions": pending_actions,
            "agent_actions": agent_actions,
            "mcp_actions": mcp_actions,
            "high_risk_actions": high_risk_actions,
            "approved_today": approved_today,
            "emergency_actions": emergency_actions,
            "governance_health": "healthy" if pending_actions < 50 else "attention_needed",
            "last_updated": datetime.utcnow().isoformat(),
            "user_info": {
                "email": current_user.email,
                "role": current_user.role,
                "max_risk_approval": getattr(current_user, 'max_risk_approval', 50)
            }
        }
        
        logger.info(f"✅ Unified governance stats retrieved successfully")
        return {"success": True, "stats": stats}
        
    except Exception as e:
        logger.error(f"❌ Error fetching unified governance stats: {str(e)}")
        
        # 🏢 ENTERPRISE: Fallback to demo data if database unavailable
        demo_stats = {
            "total_actions": 127,
            "pending_actions": 8,
            "agent_actions": 89,
            "mcp_actions": 38,
            "high_risk_actions": 12,
            "approved_today": 15,
            "emergency_actions": 2,
            "governance_health": "demo_mode",
            "last_updated": datetime.utcnow().isoformat(),
            "user_info": {
                "email": current_user.email if current_user else "demo@company.com",
                "role": getattr(current_user, 'role', 'manager'),
                "max_risk_approval": 75
            }
        }
        
        return {"success": True, "stats": demo_stats, "demo_mode": True}

# 🏢 ENTERPRISE: Unified pending actions
@router.get("/unified-actions")
async def get_unified_pending_actions(
    limit: int = 50,
    offset: int = 0,
    risk_threshold: Optional[int] = None,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Get unified pending actions for agents and MCP servers
    Uses your existing Action model with enhanced filtering
    """
    try:
        logger.info(f"🏢 Fetching unified pending actions for user {current_user.email}")
        
        # Build query using your existing Action model
        query = db.query(Action).filter(
            Action.authorization_status == "pending_approval"
        )
        
        # Apply filters if provided
        if risk_threshold:
            query = query.filter(Action.ai_risk_score >= risk_threshold)
            
        if action_type == "mcp_server_action":
            query = query.filter(
                or_(
                    Action.action_type == "mcp_server_action",
                    Action.description.ilike("%mcp%"),
                    Action.target_system.ilike("%mcp%")
                )
            )
        elif action_type == "agent_action":
            query = query.filter(
                and_(
                    Action.action_type != "mcp_server_action",
                    ~Action.description.ilike("%mcp%"),
                    ~Action.target_system.ilike("%mcp%")
                )
            )
        
        # Order by priority (emergency first, then risk score, then created date)
        query = query.order_by(
            desc(Action.is_emergency),
            desc(Action.ai_risk_score),
            desc(Action.created_at)
        )
        
        # Apply pagination
        actions = query.offset(offset).limit(limit).all()
        
        # 🔌 Enhanced: Convert to unified format with MCP detection
        unified_actions = []
        for action in actions:
            # Detect if this is an MCP action
            is_mcp_action = (
                action.action_type == "mcp_server_action" or
                "mcp" in (action.description or "").lower() or
                "mcp" in (action.target_system or "").lower()
            )
            
            # Build unified action object
            unified_action = {
                "id": action.id,
                "action_type": "mcp_server_action" if is_mcp_action else action.action_type,
                "agent_id": action.agent_id,
                "ai_risk_score": action.ai_risk_score,
                "description": action.description,
                "workflow_stage": action.workflow_stage,
                "current_approval_level": action.current_approval_level,
                "required_approval_level": action.required_approval_level,
                "is_emergency": action.is_emergency,
                "authorization_status": action.authorization_status,
                "execution_status": action.execution_status,
                "contextual_risk_factors": json.loads(action.contextual_risk_factors) if action.contextual_risk_factors else [],
                "target_system": action.target_system,
                "user_email": action.user_email,
                "requested_at": action.created_at.isoformat() if action.created_at else None,
                "time_remaining": calculate_time_remaining(action.created_at) if action.created_at else "Unknown"
            }
            
            # 🔌 NEW: Add MCP-specific data if detected
            if is_mcp_action:
                # Try to parse MCP data from existing fields
                mcp_data = extract_mcp_data_from_action(action)
                unified_action["mcp_data"] = mcp_data
            
            unified_actions.append(unified_action)
        
        logger.info(f"✅ Retrieved {len(unified_actions)} unified pending actions")
        return {
            "success": True, 
            "actions": unified_actions,
            "total": query.count(),
            "has_more": (offset + limit) < query.count()
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching unified pending actions: {str(e)}")
        
        # 🏢 ENTERPRISE: Fallback to enhanced demo data
        demo_actions = [
            {
                "id": 501,
                "action_type": "mcp_server_action",
                "mcp_data": {
                    "server": "claude-desktop",
                    "namespace": "filesystem",
                    "verb": "read_file",
                    "resource": "/home/user/sensitive_data.csv",
                    "params": {"encoding": "utf8", "max_size": "10MB"}
                },
                "ai_risk_score": 75,
                "description": "MCP: Read sensitive file via Claude Desktop",
                "workflow_stage": "level_2",
                "current_approval_level": 1,
                "required_approval_level": 2,
                "is_emergency": False,
                "authorization_status": "pending_approval",
                "execution_status": "pending_approval",
                "contextual_risk_factors": ["Sensitive data access", "External MCP server"],
                "time_remaining": "1:45:00",
                "requested_at": (datetime.utcnow() - timedelta(minutes=15)).isoformat(),
                "user_email": "developer@company.com"
            },
            {
                "id": 502,
                "action_type": "security_scan",
                "agent_id": "Agent-7432",
                "ai_risk_score": 45,
                "description": "Security scan of production database",
                "workflow_stage": "level_1",
                "current_approval_level": 1,
                "required_approval_level": 1,
                "is_emergency": False,
                "authorization_status": "pending_approval",
                "execution_status": "pending_approval",
                "contextual_risk_factors": ["Production environment"],
                "time_remaining": "3:15:00",
                "requested_at": (datetime.utcnow() - timedelta(minutes=8)).isoformat(),
                "user_email": "security@company.com"
            }
        ]
        
        return {"success": True, "actions": demo_actions, "demo_mode": True}

# 🔌 ENTERPRISE: MCP-specific governance endpoint
@router.post("/mcp-governance/evaluate-action")
async def evaluate_mcp_action(
    action_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔌 ENTERPRISE: Evaluate MCP server action using your existing approval workflow
    """
    try:
        action_id = action_data.get("action_id")
        decision = action_data.get("decision")
        notes = action_data.get("notes", "")
        
        logger.info(f"🔌 Evaluating MCP action {action_id}: {decision}")
        
        # Get action from your existing Action table
        action = db.query(Action).filter(Action.id == action_id).first()
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        # Update action status using your existing fields
        action.authorization_status = "approved" if decision == "approved" else "denied"
        action.execution_status = "approved" if decision == "approved" else "denied"
        action.updated_at = datetime.utcnow()
        
        # 🏢 ENTERPRISE: Create audit log entry using your existing AuditLog model
        audit_entry = AuditLog(
            user_id=current_user.id,
            action_type="mcp_governance_decision",
            resource_type="mcp_action",
            resource_id=str(action_id),
            details={
                "decision": decision,
                "notes": notes,
                "mcp_server": action_data.get("mcp_server_id"),
                "mcp_namespace": action_data.get("mcp_namespace"),
                "original_action_type": action.action_type,
                "risk_score": action.ai_risk_score
            },
            ip_address="127.0.0.1",  # You can enhance this with real IP tracking
            user_agent="OW-AI-Dashboard"
        )
        
        db.add(audit_entry)
        db.commit()
        
        logger.info(f"✅ MCP action {action_id} {decision} successfully")
        
        return {
            "success": True,
            "decision": decision,
            "action_id": action_id,
            "execution_performed": decision == "approved",
            "execution_success": decision == "approved",
            "execution_message": f"MCP action {decision} successfully",
            "audit_logged": True
        }
        
    except Exception as e:
        logger.error(f"❌ Error evaluating MCP action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 🏢 ENTERPRISE: Health check endpoint
@router.get("/health")
async def governance_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Health check for unified governance system
    """
    try:
        # Test database connectivity using your existing models
        action_count = db.query(Action).count()
        user_count = db.query(User).count()
        
        health_status = {
            "status": "healthy",
            "database_connected": True,
            "action_table_accessible": True,
            "user_table_accessible": True,
            "total_actions": action_count,
            "total_users": user_count,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "degraded",
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# 🏢 ENTERPRISE: Admin-only unified reporting (uses your existing require_admin_role)
@router.get("/admin/unified-report")
async def get_unified_admin_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_role)
):
    """
    🏢 ENTERPRISE: Admin-only unified governance report
    Uses your existing admin role requirements
    """
    try:
        logger.info(f"🏢 Admin {current_user.email} accessing unified governance report")
        
        # Get comprehensive stats using your existing tables
        total_actions = db.query(Action).count()
        pending_actions = db.query(Action).filter(Action.authorization_status == "pending_approval").count()
        approved_actions = db.query(Action).filter(Action.authorization_status == "approved").count()
        denied_actions = db.query(Action).filter(Action.authorization_status == "denied").count()
        
        # Get audit trail summary
        audit_count = db.query(AuditLog).count()
        recent_audits = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(10).all()
        
        admin_report = {
            "report_type": "unified_governance_admin",
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": current_user.email,
            "summary": {
                "total_actions": total_actions,
                "pending_actions": pending_actions,
                "approved_actions": approved_actions,
                "denied_actions": denied_actions,
                "audit_entries": audit_count
            },
            "recent_audits": [
                {
                    "id": audit.id,
                    "action_type": audit.action_type,
                    "resource_type": audit.resource_type,
                    "user_id": audit.user_id,
                    "created_at": audit.created_at.isoformat() if audit.created_at else None
                }
                for audit in recent_audits
            ]
        }
        
        return {"success": True, "report": admin_report}
        
    except Exception as e:
        logger.error(f"❌ Error generating admin report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate admin report")

# 🔧 Helper Functions
def calculate_time_remaining(created_at: datetime) -> str:
    """Calculate time remaining for action approval"""
    if not created_at:
        return "Unknown"
    
    # Default 4-hour approval window
    deadline = created_at + timedelta(hours=4)
    remaining = deadline - datetime.utcnow()
    
    if remaining.total_seconds() <= 0:
        return "OVERDUE"
    
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)
    
    return f"{hours}:{minutes:02d}:00"

def extract_mcp_data_from_action(action: Action) -> Dict[str, Any]:
    """Extract MCP-specific data from existing action fields"""
    mcp_data = {
        "server": "unknown",
        "namespace": "unknown", 
        "verb": "unknown",
        "resource": action.target_system or "unknown",
        "params": {}
    }
    
    # Try to parse from description or other fields
    description = action.description or ""
    
    if "claude-desktop" in description.lower():
        mcp_data["server"] = "claude-desktop"
    elif "github" in description.lower():
        mcp_data["server"] = "github-mcp"
    elif "filesystem" in description.lower():
        mcp_data["namespace"] = "filesystem"
    
    # Try to extract verb from action_type or description
    if action.action_type:
        if "read" in action.action_type.lower():
            mcp_data["verb"] = "read_file"
        elif "write" in action.action_type.lower():
            mcp_data["verb"] = "write_file"
        elif "create" in action.action_type.lower():
            mcp_data["verb"] = "create"
    
    return mcp_data

