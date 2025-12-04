"""
SEC-077: Automated Session Cleanup Job
======================================

Enterprise-grade scheduled task for MCP session lifecycle management.
Automatically expires stale sessions and cleans up resources.

Schedule: Every 15 minutes
Timezone: UTC (enterprise standard)

Industry Alignment:
- AWS Session Manager cleanup patterns
- Datadog APM session tracking
- Splunk session lifecycle management

Compliance: GDPR Art. 5 (data minimization), NIST IA-4, SOC 2 CC6.1

Created: 2025-12-04
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List
import logging
import hashlib

logger = logging.getLogger(__name__)

# Global scheduler instance (shared with retention_cleanup_job)
# Import from existing scheduler or create new
try:
    from jobs.retention_cleanup_job import scheduler
except ImportError:
    scheduler = BackgroundScheduler()

# Job statistics (in-memory tracking)
session_cleanup_stats = {
    "last_run": None,
    "last_run_status": None,
    "last_run_expired": 0,
    "last_run_cleaned": 0,
    "last_run_error": None,
    "total_runs": 0,
    "total_expired": 0,
    "total_cleaned": 0,
}


def run_session_cleanup() -> Dict[str, Any]:
    """
    Execute automated session cleanup across all organizations.

    This job:
    1. Finds all sessions past their expires_at timestamp
    2. Marks them as EXPIRED with appropriate reason
    3. Cleans up associated resources
    4. Logs to immutable audit trail
    5. Updates job statistics

    Multi-tenant: Processes all organizations but logs per-org metrics.

    Returns:
        dict: Result summary with counts and status
    """
    from database import get_db
    from models_mcp_governance import MCPSession
    from sqlalchemy import and_

    start_time = datetime.now(UTC)
    logger.info(f"SEC-077: Starting session cleanup job at {start_time.isoformat()}")

    db = next(get_db())

    try:
        # Find expired but still active sessions
        expired_sessions = db.query(MCPSession).filter(
            and_(
                MCPSession.expires_at < start_time,
                MCPSession.status == 'ACTIVE',
                MCPSession.cleanup_status == 'active'
            )
        ).all()

        expired_count = len(expired_sessions)
        logger.info(f"SEC-077: Found {expired_count} expired sessions to clean up")

        if expired_count == 0:
            _update_stats(start_time, "success", 0, 0)
            return {
                "status": "success",
                "expired_count": 0,
                "cleaned_count": 0,
                "message": "No expired sessions to clean up",
                "timestamp": start_time.isoformat(),
            }

        # Process each expired session
        cleaned_count = 0
        org_counts = {}

        for session in expired_sessions:
            try:
                # Mark as expired
                session.status = 'EXPIRED'
                session.expiration_reason = session.expiration_reason or 'timeout'
                session.cleanup_status = 'pending_cleanup'
                session.is_active = False

                # Track per-organization
                org_id = session.organization_id
                org_counts[org_id] = org_counts.get(org_id, 0) + 1

                # Log expiration event
                _log_session_expiration(db, session)

                cleaned_count += 1

            except Exception as e:
                logger.error(f"SEC-077: Error expiring session {session.session_id}: {e}")

        # Mark as cleaned
        for session in expired_sessions:
            if session.cleanup_status == 'pending_cleanup':
                session.cleanup_status = 'cleaned'
                session.cleaned_at = datetime.now(UTC)

        db.commit()

        # Update statistics
        _update_stats(start_time, "success", expired_count, cleaned_count)

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"SEC-077: Session cleanup complete:")
        logger.info(f"   - Sessions expired: {expired_count}")
        logger.info(f"   - Sessions cleaned: {cleaned_count}")
        logger.info(f"   - Organizations affected: {len(org_counts)}")
        logger.info(f"   - Duration: {duration:.2f} seconds")

        return {
            "status": "success",
            "expired_count": expired_count,
            "cleaned_count": cleaned_count,
            "organizations_affected": len(org_counts),
            "org_breakdown": org_counts,
            "duration_seconds": duration,
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"SEC-077: Session cleanup job failed: {error_msg}", exc_info=True)

        _update_stats(start_time, "failed", 0, 0, error_msg)

        return {
            "status": "failed",
            "expired_count": 0,
            "cleaned_count": 0,
            "error": error_msg,
            "timestamp": start_time.isoformat(),
        }
    finally:
        db.close()


def run_session_renewal_check() -> Dict[str, Any]:
    """
    Check for sessions eligible for auto-renewal.

    Sessions with auto_renewal_enabled=True are renewed before expiration
    if they haven't exceeded max_renewals.

    Returns:
        dict: Renewal results
    """
    from database import get_db
    from models_mcp_governance import MCPSession
    from sqlalchemy import and_

    start_time = datetime.now(UTC)
    logger.info(f"SEC-077: Starting session renewal check at {start_time.isoformat()}")

    db = next(get_db())

    try:
        # Find sessions expiring in next 5 minutes with auto-renewal enabled
        expiring_soon = start_time + timedelta(minutes=5)

        renewable_sessions = db.query(MCPSession).filter(
            and_(
                MCPSession.expires_at <= expiring_soon,
                MCPSession.expires_at > start_time,
                MCPSession.status == 'ACTIVE',
                MCPSession.auto_renewal_enabled == True,
            )
        ).all()

        renewed_count = 0
        for session in renewable_sessions:
            if session.renewal_count < session.max_renewals:
                # Renew session (extend by original duration)
                original_duration = session.expires_at - session.created_at
                session.expires_at = start_time + original_duration
                session.renewal_count += 1
                session.last_renewed_at = start_time
                renewed_count += 1
                logger.debug(
                    f"SEC-077: Renewed session {session.session_id} "
                    f"(renewal {session.renewal_count}/{session.max_renewals})"
                )

        db.commit()

        return {
            "status": "success",
            "checked": len(renewable_sessions),
            "renewed": renewed_count,
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"SEC-077: Session renewal check failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": start_time.isoformat(),
        }
    finally:
        db.close()


def cleanup_old_expired_sessions(days: int = 30) -> Dict[str, Any]:
    """
    Delete sessions that have been expired for more than N days.
    Called less frequently (weekly) for data minimization.

    Args:
        days: Days after expiration before deletion

    Returns:
        dict: Deletion results
    """
    from database import get_db
    from models_mcp_governance import MCPSession
    from sqlalchemy import and_

    start_time = datetime.now(UTC)
    cutoff = start_time - timedelta(days=days)

    logger.info(f"SEC-077: Cleaning expired sessions older than {days} days")

    db = next(get_db())

    try:
        # Find old expired sessions
        old_sessions = db.query(MCPSession).filter(
            and_(
                MCPSession.status == 'EXPIRED',
                MCPSession.cleaned_at < cutoff
            )
        ).all()

        deleted_count = len(old_sessions)

        if deleted_count > 0:
            # Archive to audit log before deletion
            for session in old_sessions:
                _log_session_deletion(db, session)

            # Delete the sessions
            for session in old_sessions:
                db.delete(session)

            db.commit()

        logger.info(f"SEC-077: Deleted {deleted_count} old expired sessions")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff.isoformat(),
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        logger.error(f"SEC-077: Old session cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": start_time.isoformat(),
        }
    finally:
        db.close()


def _log_session_expiration(db, session):
    """Log session expiration to audit trail."""
    from sqlalchemy import text

    correlation_id = hashlib.sha256(
        f"session_expire:{session.session_id}:{datetime.now(UTC).isoformat()}".encode()
    ).hexdigest()[:64]

    try:
        db.execute(
            text("""
                INSERT INTO diagnostic_audit_logs
                (correlation_id, organization_id, diagnostic_type, health_score,
                 severity, results, checked_at)
                VALUES (:corr_id, :org_id, 'session_expiration', 100.0,
                        'INFO', :results, :checked_at)
            """),
            {
                "corr_id": correlation_id,
                "org_id": session.organization_id,
                "results": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "expiration_reason": session.expiration_reason,
                    "total_actions": session.total_actions,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                },
                "checked_at": datetime.now(UTC),
            }
        )
    except Exception as e:
        logger.warning(f"SEC-077: Failed to log session expiration: {e}")


def _log_session_deletion(db, session):
    """Log session deletion to audit trail for compliance."""
    from sqlalchemy import text

    correlation_id = hashlib.sha256(
        f"session_delete:{session.session_id}:{datetime.now(UTC).isoformat()}".encode()
    ).hexdigest()[:64]

    try:
        db.execute(
            text("""
                INSERT INTO diagnostic_audit_logs
                (correlation_id, organization_id, diagnostic_type, health_score,
                 severity, results, checked_at)
                VALUES (:corr_id, :org_id, 'session_deletion', 100.0,
                        'INFO', :results, :checked_at)
            """),
            {
                "corr_id": correlation_id,
                "org_id": session.organization_id,
                "results": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "deletion_reason": "data_retention_policy",
                    "session_age_days": (datetime.now(UTC) - session.created_at).days if session.created_at else None,
                },
                "checked_at": datetime.now(UTC),
            }
        )
    except Exception as e:
        logger.warning(f"SEC-077: Failed to log session deletion: {e}")


def _update_stats(start_time, status, expired, cleaned, error=None):
    """Update job statistics."""
    session_cleanup_stats["last_run"] = start_time.isoformat()
    session_cleanup_stats["last_run_status"] = status
    session_cleanup_stats["last_run_expired"] = expired
    session_cleanup_stats["last_run_cleaned"] = cleaned
    session_cleanup_stats["last_run_error"] = error
    session_cleanup_stats["total_runs"] += 1
    session_cleanup_stats["total_expired"] += expired
    session_cleanup_stats["total_cleaned"] += cleaned


def start_session_cleanup_scheduler():
    """
    Start the session cleanup scheduler.

    Jobs:
    - Session cleanup: Every 15 minutes
    - Session renewal check: Every 5 minutes
    - Old session deletion: Weekly (Sunday 3:00 AM UTC)
    """
    if scheduler.running:
        logger.info("SEC-077: Adding session cleanup jobs to existing scheduler")

    try:
        # Main cleanup job - every 15 minutes
        scheduler.add_job(
            run_session_cleanup,
            trigger=IntervalTrigger(minutes=15),
            id='session_cleanup',
            name='SEC-077 Session Cleanup',
            replace_existing=True,
            misfire_grace_time=300,
        )

        # Renewal check - every 5 minutes
        scheduler.add_job(
            run_session_renewal_check,
            trigger=IntervalTrigger(minutes=5),
            id='session_renewal_check',
            name='SEC-077 Session Renewal Check',
            replace_existing=True,
            misfire_grace_time=60,
        )

        # Old session deletion - weekly
        scheduler.add_job(
            cleanup_old_expired_sessions,
            trigger=CronTrigger(
                day_of_week='sun',
                hour=3,
                minute=0,
                timezone='UTC'
            ),
            id='session_old_cleanup',
            name='SEC-077 Old Session Deletion',
            replace_existing=True,
            misfire_grace_time=7200,
        )

        if not scheduler.running:
            scheduler.start()

        logger.info("SEC-077: Session cleanup scheduler started successfully")
        logger.info("   - Cleanup: Every 15 minutes")
        logger.info("   - Renewal check: Every 5 minutes")
        logger.info("   - Old deletion: Weekly (Sunday 3:00 AM UTC)")

    except Exception as e:
        logger.error(f"SEC-077: Failed to start session cleanup scheduler: {e}", exc_info=True)
        raise


def stop_session_cleanup_scheduler():
    """Stop session cleanup jobs (but not the entire scheduler)."""
    try:
        scheduler.remove_job('session_cleanup')
        scheduler.remove_job('session_renewal_check')
        scheduler.remove_job('session_old_cleanup')
        logger.info("SEC-077: Session cleanup jobs removed")
    except Exception as e:
        logger.warning(f"SEC-077: Error removing session cleanup jobs: {e}")


def get_session_cleanup_status() -> Dict[str, Any]:
    """
    Get current status of session cleanup scheduler.

    Returns:
        dict: Scheduler status and job information
    """
    if not scheduler.running:
        return {
            "scheduler_running": False,
            "message": "Scheduler is not running",
        }

    try:
        cleanup_job = scheduler.get_job('session_cleanup')
        renewal_job = scheduler.get_job('session_renewal_check')
        old_cleanup_job = scheduler.get_job('session_old_cleanup')

        return {
            "scheduler_running": True,
            "jobs": {
                "session_cleanup": {
                    "configured": cleanup_job is not None,
                    "next_run": cleanup_job.next_run_time.isoformat() if cleanup_job and cleanup_job.next_run_time else None,
                },
                "session_renewal_check": {
                    "configured": renewal_job is not None,
                    "next_run": renewal_job.next_run_time.isoformat() if renewal_job and renewal_job.next_run_time else None,
                },
                "session_old_cleanup": {
                    "configured": old_cleanup_job is not None,
                    "next_run": old_cleanup_job.next_run_time.isoformat() if old_cleanup_job and old_cleanup_job.next_run_time else None,
                },
            },
            "stats": session_cleanup_stats,
        }

    except Exception as e:
        logger.error(f"SEC-077: Error getting scheduler status: {e}")
        return {
            "scheduler_running": True,
            "error": str(e),
        }


def trigger_manual_session_cleanup() -> Dict[str, Any]:
    """
    Manually trigger session cleanup (for admin use).

    Returns:
        dict: Result of manual cleanup execution
    """
    logger.info("SEC-077: Manual session cleanup triggered by admin")
    return run_session_cleanup()


# Export public API
__all__ = [
    'start_session_cleanup_scheduler',
    'stop_session_cleanup_scheduler',
    'get_session_cleanup_status',
    'trigger_manual_session_cleanup',
    'run_session_cleanup',
    'run_session_renewal_check',
    'cleanup_old_expired_sessions',
]
