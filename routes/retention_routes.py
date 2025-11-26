"""
Enterprise Retention Policy API Routes
Provides REST API for retention policy management

Endpoints:
- GET /api/retention/statistics - Get retention statistics
- POST /api/retention/backfill - Backfill retention dates
- GET /api/retention/expired - List expired logs
- POST /api/retention/cleanup - Execute retention cleanup
- POST /api/retention/legal-hold - Apply legal hold
- POST /api/retention/legal-hold/release - Release legal hold
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, UTC
from dependencies import verify_token, get_db, require_admin, get_organization_filter
from services.retention_policy_service import RetentionPolicyService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class LegalHoldRequest(BaseModel):
    log_ids: List[str]
    reason: str

class LegalHoldReleaseRequest(BaseModel):
    log_ids: List[str]

class CleanupRequest(BaseModel):
    dry_run: bool = True
    max_delete: int = 1000

@router.get("/retention/health")
def get_retention_health(
    db: Session = Depends(get_db),
    org_id: int = Depends(get_organization_filter)
):
    """
    Enterprise Health Check for Retention Policy Service

    Returns:
        Service health status with system metrics

    Enterprise Features:
    - Database connectivity verification
    - Service availability monitoring
    - System metrics for monitoring/alerting
    - Multi-tenant isolation
    """
    try:
        # Check database connectivity (SQLAlchemy 2.0 requires text() wrapper)
        db.execute(text("SELECT 1"))

        # Get basic statistics
        from models_audit import ImmutableAuditLog
        query = db.query(ImmutableAuditLog)

        # 🏢 ENTERPRISE: Multi-tenant isolation
        if org_id is not None:
            query = query.filter(ImmutableAuditLog.organization_id == org_id)

        total_logs = query.count()

        logger.info(f"Retention health check completed [org_id={org_id}]")
        return {
            "status": "healthy",
            "service": "retention_policy",
            "database": "connected",
            "total_logs": total_logs,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Retention health check failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@router.get("/retention/statistics")
def get_retention_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get statistics about retention status of audit logs

    Returns:
        Statistics including:
        - Total logs
        - Logs with/without retention dates
        - Expired logs
        - Legal hold logs
        - Eligible for deletion

    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        logger.info(f"Fetching retention statistics [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        stats = service.get_retention_statistics()

        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get retention statistics [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/retention/backfill")
def backfill_retention_dates(
    batch_size: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Backfill retention dates for logs without them

    Args:
        batch_size: Number of logs to process (1-10000)

    Returns:
        Statistics about backfill operation

    Security: Admin only
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        logger.info(f"Starting retention backfill (batch_size={batch_size}) [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        result = service.backfill_retention_dates(batch_size=batch_size)

        logger.info(f"Backfill completed: {result['updated']} logs updated [org_id={org_id}]")
        return {
            "status": "success",
            "result": result,
            "message": f"Backfilled {result['updated']} logs"
        }
    except Exception as e:
        logger.error(f"Backfill failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backfill failed: {str(e)}")

@router.get("/retention/expired")
def get_expired_logs(
    exclude_legal_hold: bool = Query(True),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
):
    """
    List audit logs that have passed their retention period

    Args:
        exclude_legal_hold: Exclude logs with legal hold
        limit: Maximum number of logs to return

    Returns:
        List of expired logs with details

    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        logger.info(f"Fetching expired logs (exclude_legal_hold={exclude_legal_hold}, limit={limit}) [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        expired_logs = service.find_expired_logs(exclude_legal_hold=exclude_legal_hold)

        # Limit results
        expired_logs = expired_logs[:limit]

        # Format response
        logs_data = []
        for log in expired_logs:
            logs_data.append({
                "id": str(log.id),
                "sequence_number": log.sequence_number,
                "timestamp": log.timestamp.isoformat(),
                "retention_until": log.retention_until.isoformat() if log.retention_until else None,
                "legal_hold": log.legal_hold,
                "event_type": log.event_type,
                "actor_id": log.actor_id,
                "risk_level": log.risk_level,
                "compliance_tags": log.compliance_tags
            })

        logger.info(f"Found {len(logs_data)} expired logs [org_id={org_id}]")
        return {
            "status": "success",
            "count": len(logs_data),
            "logs": logs_data
        }
    except Exception as e:
        logger.error(f"Failed to get expired logs [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get expired logs: {str(e)}")

@router.post("/retention/cleanup")
def cleanup_expired_logs(
    request: CleanupRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Execute retention cleanup to delete expired logs

    Args:
        dry_run: If True, only report what would be deleted
        max_delete: Maximum number of logs to delete

    Returns:
        Cleanup statistics

    Security: Admin only
    WARNING: Actual deletion breaks hash chain
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        logger.info(f"Starting retention cleanup (dry_run={request.dry_run}, max_delete={request.max_delete}) [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        result = service.cleanup_expired_logs(
            dry_run=request.dry_run,
            max_delete=request.max_delete
        )

        if request.dry_run:
            message = f"DRY RUN: Would delete {result['would_delete']} logs"
            logger.info(f"Cleanup dry run completed [org_id={org_id}]")
        else:
            message = f"DELETED {result['deleted']} expired logs"
            logger.warning(f"Cleanup executed: {result['deleted']} logs deleted [org_id={org_id}]")

        return {
            "status": "success",
            "result": result,
            "message": message,
            "warning": "Actual deletion breaks hash chain" if not request.dry_run else None
        }
    except Exception as e:
        logger.error(f"Cleanup failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.post("/retention/legal-hold")
def apply_legal_hold(
    request: LegalHoldRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Apply legal hold to specific audit logs

    Args:
        log_ids: List of log IDs to apply hold to
        reason: Legal reason for the hold

    Returns:
        Statistics about applied holds

    Security: Admin only
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        if not request.log_ids:
            raise HTTPException(status_code=400, detail="log_ids is required")

        if not request.reason:
            raise HTTPException(status_code=400, detail="reason is required")

        logger.info(f"Applying legal hold to {len(request.log_ids)} logs [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        result = service.apply_legal_hold(
            log_ids=request.log_ids,
            reason=request.reason,
            applied_by=current_user.get('email', 'unknown')
        )

        logger.info(f"Legal hold applied to {result['applied']} logs [org_id={org_id}]")
        return {
            "status": "success",
            "result": result,
            "message": f"Applied legal hold to {result['applied']} logs"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Legal hold failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Legal hold failed: {str(e)}")

@router.post("/retention/legal-hold/release")
def release_legal_hold(
    request: LegalHoldReleaseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Release legal hold from audit logs

    Args:
        log_ids: List of log IDs to release hold from

    Returns:
        Statistics about released holds

    Security: Admin only
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        if not request.log_ids:
            raise HTTPException(status_code=400, detail="log_ids is required")

        logger.info(f"Releasing legal hold from {len(request.log_ids)} logs [org_id={org_id}]")
        service = RetentionPolicyService(db, organization_id=org_id)
        result = service.release_legal_hold(
            log_ids=request.log_ids,
            released_by=current_user.get('email', 'unknown')
        )

        logger.info(f"Legal hold released from {result['released']} logs [org_id={org_id}]")
        return {
            "status": "success",
            "result": result,
            "message": f"Released legal hold from {result['released']} logs"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hold release failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hold release failed: {str(e)}")

@router.get("/retention/job-status")
def get_retention_job_status(
    current_user: dict = Depends(verify_token),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get status of the automated retention cleanup job

    Returns:
        Scheduler status including:
        - scheduler_running: Boolean indicating if scheduler is active
        - job_configured: Boolean indicating if cleanup job is configured
        - next_run_time: ISO timestamp of next scheduled run
        - last_run: ISO timestamp of last execution
        - last_run_status: success/failed
        - last_run_deleted: Number of records deleted in last run
        - total_runs: Total number of executions
        - total_deleted: Total number of records deleted (all time)

    Security: Requires authentication
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        from jobs.retention_cleanup_job import get_scheduler_status

        logger.info(f"Fetching retention job status [org_id={org_id}]")
        status = get_scheduler_status()

        return {
            "status": "success",
            "scheduler": status,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get scheduler status [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.post("/retention/trigger-manual-cleanup")
def trigger_manual_retention_cleanup(
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Manually trigger retention cleanup job (admin only)

    Executes the retention cleanup process immediately,
    outside of the normal schedule. Useful for:
    - Testing the cleanup process
    - Running cleanup on-demand
    - Recovering from schedule failures

    Returns:
        Result of cleanup execution

    Security: Admin only
    Enterprise Features:
    - Multi-tenant data isolation
    """
    try:
        from jobs.retention_cleanup_job import trigger_manual_cleanup

        user_email = current_user.get('email', 'unknown')
        logger.info(f"Manual retention cleanup triggered by {user_email} [org_id={org_id}]")

        result = trigger_manual_cleanup()

        logger.info(f"Manual cleanup completed [org_id={org_id}]")
        return {
            "status": "success",
            "result": result,
            "triggered_by": user_email,
            "timestamp": datetime.now(UTC).isoformat()
        }
    except Exception as e:
        logger.error(f"Manual cleanup failed [org_id={org_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Manual cleanup failed: {str(e)}")
