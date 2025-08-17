"""
Enterprise Audit Routes
Provides APIs for immutable audit logs, evidence packs, and compliance reporting
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from database import get_db
from dependencies import verify_token

router = APIRouter()

# Basic audit log model
class AuditLogRequest(BaseModel):
    event_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    action: str
    event_data: Dict[str, Any]
    risk_level: str = "MEDIUM"
    compliance_tags: Optional[List[str]] = None

@router.get("/audit/health")
def audit_health_check():
    """Health check for audit system"""
    return {
        "status": "healthy",
        "audit_system": "operational",
        "timestamp": datetime.now(UTC),
        "features": ["immutable_logs", "hash_chaining", "evidence_packs"]
    }

@router.post("/audit/log")
def create_audit_log(
    request: AuditLogRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Create immutable audit log entry"""
    try:
        from services.immutable_audit_service import ImmutableAuditService
        service = ImmutableAuditService(db)
        
        # Extract client information
        ip_address = getattr(http_request.client, 'host', None)
        user_agent = http_request.headers.get("user-agent")
        
        audit_log = service.log_event(
            event_type=request.event_type,
            actor_id=request.actor_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            action=request.action,
            event_data=request.event_data,
            risk_level=request.risk_level,
            compliance_tags=request.compliance_tags,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=current_user.get("session_id")
        )
        
        return {
            "id": str(audit_log.id),
            "sequence_number": audit_log.sequence_number,
            "timestamp": audit_log.timestamp,
            "content_hash": audit_log.content_hash,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit log: {str(e)}")

@router.get("/audit/logs")
def get_audit_logs(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Get audit logs with pagination"""
    try:
        from models_audit import ImmutableAuditLog
        query = db.query(ImmutableAuditLog)
        
        total = query.count()
        logs = query.order_by(ImmutableAuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "logs": [
                {
                    "id": str(log.id),
                    "sequence_number": log.sequence_number,
                    "timestamp": log.timestamp,
                    "event_type": log.event_type,
                    "actor_id": log.actor_id,
                    "resource_type": log.resource_type,
                    "action": log.action,
                    "risk_level": log.risk_level
                }
                for log in logs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}")

@router.post("/audit/verify-integrity")
def verify_chain_integrity(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Verify audit log chain integrity"""
    try:
        from services.immutable_audit_service import ImmutableAuditService
        service = ImmutableAuditService(db)
        integrity_check = service.verify_chain_integrity()
        
        return {
            "id": str(integrity_check.id),
            "check_time": integrity_check.check_time,
            "status": integrity_check.status,
            "total_records": integrity_check.total_records,
            "check_duration_ms": integrity_check.check_duration_ms,
            "records_per_second": integrity_check.records_per_second
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")
