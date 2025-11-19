"""
🏢 ENTERPRISE PLAYBOOK DELETION ROUTES

Phase 4: Soft Delete with Recovery

Author: Donald King (OW-kai Enterprise)
Date: 2025-11-18
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, timedelta, UTC
from pydantic import BaseModel, Field

from database import get_db
from dependencies import get_current_user, require_admin
from models import AutomationPlaybook, PlaybookExecution, User
from models_playbook_versioning import PlaybookVersion, PlaybookSchedule
from services.immutable_audit_service import ImmutableAuditService

router = APIRouter(prefix="/api/authorization/automation", tags=["Playbook Deletion"])

# Initialize audit service
audit_service = ImmutableAuditService()


# ============================================================================
# SCHEMAS
# ============================================================================

class PlaybookDeleteRequest(BaseModel):
    """Request to soft delete a playbook"""
    reason: Optional[str] = Field(None, description="Optional reason for deletion (audit trail)")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Playbook no longer needed - replaced by pb-002"
            }
        }


class PlaybookRestoreRequest(BaseModel):
    """Request to restore a deleted playbook"""
    restart_schedules: bool = Field(default=False, description="Restart active schedules after restore")


class DeletedPlaybookResponse(BaseModel):
    """Response with deleted playbook info"""
    id: str
    name: str
    description: Optional[str]
    deleted_at: datetime
    deleted_by: Optional[int]
    deletion_reason: Optional[str]
    days_until_purge: int
    can_restore: bool
    execution_count: int
    version_count: int
    schedule_count: int

    class Config:
        from_attributes = True


# ============================================================================
# SOFT DELETE ENDPOINT
# ============================================================================

@router.delete("/playbook/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    delete_request: PlaybookDeleteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 SOFT DELETE PLAYBOOK

    Enterprise soft delete with 30-day recovery window.

    **Features:**
    - Soft delete (data preserved)
    - 30-day recovery window
    - Immutable audit log
    - Stop active schedules
    - Admin-only operation

    **What Happens:**
    1. Playbook marked as deleted (is_deleted = TRUE)
    2. Status changed to 'deleted'
    3. All active schedules stopped
    4. Immutable audit log entry created
    5. Can be restored within 30 days

    **Compliance:**
    - SOX Section 404: Complete audit trail
    - PCI-DSS Requirement 10: Deletion logging
    - HIPAA: 6-year retention of audit logs

    **Pattern:** Splunk SOAR Soft Delete
    """
    # Get playbook
    playbook = db.query(AutomationPlaybook).filter(
        and_(
            AutomationPlaybook.id == playbook_id,
            AutomationPlaybook.is_deleted == False
        )
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found or already deleted")

    # Gather pre-deletion stats for audit
    execution_count = db.query(func.count(PlaybookExecution.id)).filter(
        PlaybookExecution.playbook_id == playbook_id
    ).scalar()

    version_count = db.query(func.count(PlaybookVersion.id)).filter(
        PlaybookVersion.playbook_id == playbook_id
    ).scalar()

    schedule_count = db.query(func.count(PlaybookSchedule.id)).filter(
        and_(
            PlaybookSchedule.playbook_id == playbook_id,
            PlaybookSchedule.is_active == True
        )
    ).scalar()

    # Soft delete the playbook
    playbook.is_deleted = True
    playbook.deleted_at = datetime.now(UTC)
    playbook.deleted_by = current_user.get('user_id')
    playbook.deletion_reason = delete_request.reason
    playbook.status = 'deleted'

    # Stop all active schedules
    active_schedules = db.query(PlaybookSchedule).filter(
        and_(
            PlaybookSchedule.playbook_id == playbook_id,
            PlaybookSchedule.is_active == True
        )
    ).all()

    for schedule in active_schedules:
        schedule.is_active = False
        schedule.is_paused = True

    db.commit()

    # 🏢 ENTERPRISE: Immutable audit log
    audit_service.log_event(
        event_type="PLAYBOOK_DELETED",
        actor_id=str(current_user.get('user_id')),
        actor_email=current_user.get('email', 'unknown'),
        resource_type="PLAYBOOK",
        resource_id=playbook_id,
        action="SOFT_DELETE",
        event_data={
            "playbook_name": playbook.name,
            "playbook_risk_level": playbook.risk_level,
            "deletion_reason": delete_request.reason,
            "execution_count": execution_count,
            "version_count": version_count,
            "schedules_stopped": schedule_count,
            "recovery_window_days": 30
        },
        outcome="SUCCESS",
        risk_level="HIGH",
        compliance_tags=["SOX", "PCI-DSS", "HIPAA", "AUDIT", "CHANGE_MANAGEMENT"]
    )

    return {
        "status": "success",
        "message": f"Playbook '{playbook.name}' soft deleted successfully",
        "playbook_id": playbook_id,
        "deleted_at": playbook.deleted_at.isoformat(),
        "recovery_window_days": 30,
        "schedules_stopped": schedule_count,
        "data_preserved": {
            "executions": execution_count,
            "versions": version_count,
            "schedules": schedule_count
        },
        "recovery_info": "Use POST /playbook/{id}/restore to recover within 30 days"
    }


# ============================================================================
# RESTORE ENDPOINT
# ============================================================================

@router.post("/playbook/{playbook_id}/restore")
async def restore_playbook(
    playbook_id: str,
    restore_request: PlaybookRestoreRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 RESTORE DELETED PLAYBOOK

    Undelete a soft-deleted playbook (within 30-day window).

    **Features:**
    - Restore deleted playbook
    - Optional schedule restart
    - Immutable audit log
    - Admin-only operation

    **What Happens:**
    1. is_deleted set to FALSE
    2. Status changed to 'active'
    3. Optionally restart schedules
    4. Audit log entry created

    **Pattern:** ServiceNow Recycle Bin Restore
    """
    # Get deleted playbook
    playbook = db.query(AutomationPlaybook).filter(
        and_(
            AutomationPlaybook.id == playbook_id,
            AutomationPlaybook.is_deleted == True
        )
    ).first()

    if not playbook:
        raise HTTPException(status_code=404, detail="Deleted playbook not found")

    # Check if still within recovery window (30 days)
    if playbook.deleted_at:
        days_since_deletion = (datetime.now(UTC) - playbook.deleted_at).days
        if days_since_deletion > 30:
            raise HTTPException(
                status_code=410,
                detail=f"Playbook deleted {days_since_deletion} days ago (recovery window is 30 days)"
            )

    # Restore the playbook
    playbook.is_deleted = False
    playbook.status = 'active'
    # Keep deleted_at and deleted_by for audit trail

    # Optionally restart schedules
    schedules_restarted = 0
    if restore_request.restart_schedules:
        paused_schedules = db.query(PlaybookSchedule).filter(
            and_(
                PlaybookSchedule.playbook_id == playbook_id,
                PlaybookSchedule.is_paused == True
            )
        ).all()

        for schedule in paused_schedules:
            schedule.is_active = True
            schedule.is_paused = False
            schedules_restarted += 1

    db.commit()

    # 🏢 ENTERPRISE: Immutable audit log
    audit_service.log_event(
        event_type="PLAYBOOK_RESTORED",
        actor_id=str(current_user.get('user_id')),
        actor_email=current_user.get('email', 'unknown'),
        resource_type="PLAYBOOK",
        resource_id=playbook_id,
        action="RESTORE",
        event_data={
            "playbook_name": playbook.name,
            "originally_deleted_at": playbook.deleted_at.isoformat() if playbook.deleted_at else None,
            "originally_deleted_by": playbook.deleted_by,
            "schedules_restarted": schedules_restarted,
            "restart_schedules_requested": restore_request.restart_schedules
        },
        outcome="SUCCESS",
        risk_level="MEDIUM",
        compliance_tags=["SOX", "AUDIT", "CHANGE_MANAGEMENT"]
    )

    return {
        "status": "success",
        "message": f"Playbook '{playbook.name}' restored successfully",
        "playbook_id": playbook_id,
        "restored_at": datetime.now(UTC).isoformat(),
        "schedules_restarted": schedules_restarted
    }


# ============================================================================
# LIST DELETED PLAYBOOKS
# ============================================================================

@router.get("/playbooks/deleted", response_model=List[DeletedPlaybookResponse])
async def list_deleted_playbooks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 LIST DELETED PLAYBOOKS

    Admin-only view of soft-deleted playbooks eligible for recovery.

    **Features:**
    - Shows all deleted playbooks
    - Calculates days until auto-purge
    - Shows recovery eligibility
    - Includes deletion metadata

    **Recovery Window:** 30 days
    **Auto-Purge:** Playbooks deleted >30 days ago (future enhancement)
    """
    deleted_playbooks = db.query(AutomationPlaybook).filter(
        AutomationPlaybook.is_deleted == True
    ).order_by(AutomationPlaybook.deleted_at.desc()).all()

    result = []
    for playbook in deleted_playbooks:
        # Calculate days until purge
        if playbook.deleted_at:
            days_since_deletion = (datetime.now(UTC) - playbook.deleted_at).days
            days_until_purge = max(0, 30 - days_since_deletion)
            can_restore = days_since_deletion <= 30
        else:
            days_until_purge = 30
            can_restore = True

        # Get counts
        execution_count = db.query(func.count(PlaybookExecution.id)).filter(
            PlaybookExecution.playbook_id == playbook.id
        ).scalar()

        version_count = db.query(func.count(PlaybookVersion.id)).filter(
            PlaybookVersion.playbook_id == playbook.id
        ).scalar()

        schedule_count = db.query(func.count(PlaybookSchedule.id)).filter(
            PlaybookSchedule.playbook_id == playbook.id
        ).scalar()

        result.append(DeletedPlaybookResponse(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            deleted_at=playbook.deleted_at,
            deleted_by=playbook.deleted_by,
            deletion_reason=playbook.deletion_reason,
            days_until_purge=days_until_purge,
            can_restore=can_restore,
            execution_count=execution_count or 0,
            version_count=version_count or 0,
            schedule_count=schedule_count or 0
        ))

    return result


# ============================================================================
# PERMANENT DELETE (Super Admin Only - Future)
# ============================================================================

@router.delete("/playbook/{playbook_id}/permanent")
async def permanent_delete_playbook(
    playbook_id: str,
    confirmation: str = Query(..., description="Type playbook name to confirm"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """
    🏢 PERMANENT DELETE (HARD DELETE)

    **⚠️ WARNING: This action CANNOT be undone!**

    **Requirements:**
    - Super admin only (future: require_super_admin)
    - Must type playbook name to confirm
    - Playbook must be soft-deleted first
    - Creates evidence pack before deletion

    **What Gets Deleted:**
    - Playbook record
    - All versions (CASCADE)
    - All executions (CASCADE)
    - All execution logs (CASCADE)
    - All schedules (CASCADE)

    **Audit Trail:** Immutable log entry created before deletion

    **Pattern:** ServiceNow Permanent Delete
    """
    # Get soft-deleted playbook
    playbook = db.query(AutomationPlaybook).filter(
        and_(
            AutomationPlaybook.id == playbook_id,
            AutomationPlaybook.is_deleted == True
        )
    ).first()

    if not playbook:
        raise HTTPException(
            status_code=404,
            detail="Playbook not found or not soft-deleted (must soft delete first)"
        )

    # Require exact name confirmation
    if confirmation != playbook.name:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmation failed. Type exact playbook name: '{playbook.name}'"
        )

    # Create evidence pack (snapshot for audit)
    evidence_pack = {
        "playbook_id": playbook.id,
        "playbook_name": playbook.name,
        "description": playbook.description,
        "trigger_conditions": playbook.trigger_conditions,
        "actions": playbook.actions,
        "created_at": playbook.created_at.isoformat() if playbook.created_at else None,
        "deleted_at": playbook.deleted_at.isoformat() if playbook.deleted_at else None,
        "deleted_by": playbook.deleted_by,
        "deletion_reason": playbook.deletion_reason,
        "execution_count": playbook.execution_count,
        "success_rate": playbook.success_rate
    }

    # 🏢 ENTERPRISE: Immutable audit log BEFORE deletion
    audit_service.log_event(
        event_type="PLAYBOOK_PERMANENTLY_DELETED",
        actor_id=str(current_user.get('user_id')),
        actor_email=current_user.get('email', 'unknown'),
        resource_type="PLAYBOOK",
        resource_id=playbook_id,
        action="HARD_DELETE",
        event_data={
            "evidence_pack": evidence_pack,
            "warning": "PERMANENT_DELETION_CANNOT_BE_UNDONE"
        },
        outcome="SUCCESS",
        risk_level="CRITICAL",
        compliance_tags=["SOX", "PCI-DSS", "HIPAA", "AUDIT", "PERMANENT_DELETE"]
    )

    # Hard delete (CASCADE will delete related records)
    db.delete(playbook)
    db.commit()

    return {
        "status": "success",
        "message": f"Playbook '{playbook.name}' permanently deleted",
        "playbook_id": playbook_id,
        "evidence_pack_created": True,
        "audit_log_id": "See immutable_audit_logs table",
        "warning": "THIS ACTION CANNOT BE UNDONE"
    }
