"""
Automated Data Retention Cleanup Job
Enterprise-grade scheduled task for policy enforcement

Created: 2025-11-12
Purpose: Automatically enforce data retention policies with compliance frameworks
Schedule: Daily at 2:00 AM UTC
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, UTC
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()

# Job statistics (in-memory tracking)
job_stats = {
    "last_run": None,
    "last_run_status": None,
    "last_run_deleted": 0,
    "last_run_error": None,
    "total_runs": 0,
    "total_deleted": 0,
}


def run_retention_cleanup():
    """
    Execute automated retention policy cleanup

    This job:
    1. Finds all expired audit logs and agent actions
    2. Respects legal holds (will not delete held records)
    3. Deletes eligible expired records
    4. Generates immutable audit trail
    5. Updates job statistics

    Returns:
        dict: Result summary with counts and status
    """
    from database import get_db
    from services.retention_policy_service import RetentionPolicyService

    start_time = datetime.now(UTC)
    logger.info(f"🔄 Starting automated retention cleanup job at {start_time.isoformat()}")

    db = next(get_db())
    service = RetentionPolicyService(db)

    try:
        # Find expired logs (respecting legal holds)
        expired_logs = service.find_expired_logs()
        expired_count = len(expired_logs)

        logger.info(f"📋 Found {expired_count} expired records eligible for deletion")

        if expired_count == 0:
            logger.info("✅ No expired records found - retention policies up to date")
            job_stats["last_run"] = start_time.isoformat()
            job_stats["last_run_status"] = "success"
            job_stats["last_run_deleted"] = 0
            job_stats["last_run_error"] = None
            job_stats["total_runs"] += 1

            return {
                "status": "success",
                "deleted_count": 0,
                "message": "No expired records to clean up",
                "timestamp": start_time.isoformat(),
            }

        # Execute cleanup
        result = service.cleanup_expired_logs()
        deleted_count = result.get("deleted_count", 0)

        # Update statistics
        job_stats["last_run"] = start_time.isoformat()
        job_stats["last_run_status"] = "success"
        job_stats["last_run_deleted"] = deleted_count
        job_stats["last_run_error"] = None
        job_stats["total_runs"] += 1
        job_stats["total_deleted"] += deleted_count

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        logger.info(f"✅ Retention cleanup complete:")
        logger.info(f"   - Records deleted: {deleted_count}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        logger.info(f"   - Compliance enforced: SOX, HIPAA, PCI-DSS, GDPR, CCPA, FERPA")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "duration_seconds": duration,
            "message": f"Successfully deleted {deleted_count} expired records",
            "timestamp": start_time.isoformat(),
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Retention cleanup job failed: {error_msg}", exc_info=True)

        # Update error statistics
        job_stats["last_run"] = start_time.isoformat()
        job_stats["last_run_status"] = "failed"
        job_stats["last_run_deleted"] = 0
        job_stats["last_run_error"] = error_msg
        job_stats["total_runs"] += 1

        return {
            "status": "failed",
            "deleted_count": 0,
            "error": error_msg,
            "timestamp": start_time.isoformat(),
        }
    finally:
        db.close()


def start_retention_scheduler():
    """
    Start the retention cleanup scheduler

    Schedule: Daily at 2:00 AM UTC
    Timezone: UTC (enterprise standard)
    Misfire Grace Time: 3600 seconds (1 hour)
    """
    if scheduler.running:
        logger.warning("⚠️  Retention scheduler is already running")
        return

    try:
        # Add retention cleanup job
        # Runs daily at 2:00 AM UTC
        scheduler.add_job(
            run_retention_cleanup,
            trigger=CronTrigger(
                hour=2,
                minute=0,
                timezone='UTC'
            ),
            id='retention_cleanup',
            name='Automated Data Retention Cleanup',
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1 hour grace period
        )

        # Start the scheduler
        scheduler.start()

        logger.info("✅ Retention cleanup scheduler started successfully")
        logger.info("   - Schedule: Daily at 2:00 AM UTC")
        logger.info("   - Job ID: retention_cleanup")
        logger.info("   - Next run: {}".format(
            scheduler.get_job('retention_cleanup').next_run_time
        ))

    except Exception as e:
        logger.error(f"❌ Failed to start retention scheduler: {e}", exc_info=True)
        raise


def stop_retention_scheduler():
    """
    Stop the retention cleanup scheduler gracefully
    """
    if not scheduler.running:
        logger.info("ℹ️  Retention scheduler is not running")
        return

    try:
        scheduler.shutdown(wait=True)
        logger.info("🛑 Retention cleanup scheduler stopped successfully")
    except Exception as e:
        logger.error(f"❌ Error stopping retention scheduler: {e}", exc_info=True)


def get_scheduler_status():
    """
    Get current status of the retention scheduler

    Returns:
        dict: Scheduler status and job information
    """
    if not scheduler.running:
        return {
            "scheduler_running": False,
            "message": "Scheduler is not running",
        }

    try:
        job = scheduler.get_job('retention_cleanup')

        if not job:
            return {
                "scheduler_running": True,
                "job_configured": False,
                "message": "Retention cleanup job not configured",
            }

        return {
            "scheduler_running": True,
            "job_configured": True,
            "job_id": job.id,
            "job_name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "last_run": job_stats.get("last_run"),
            "last_run_status": job_stats.get("last_run_status"),
            "last_run_deleted": job_stats.get("last_run_deleted"),
            "last_run_error": job_stats.get("last_run_error"),
            "total_runs": job_stats.get("total_runs"),
            "total_deleted": job_stats.get("total_deleted"),
        }

    except Exception as e:
        logger.error(f"❌ Error getting scheduler status: {e}")
        return {
            "scheduler_running": True,
            "error": str(e),
        }


def trigger_manual_cleanup():
    """
    Manually trigger retention cleanup (for testing or admin use)

    Returns:
        dict: Result of manual cleanup execution
    """
    logger.info("🔧 Manual retention cleanup triggered by admin")
    return run_retention_cleanup()


# Export public API
__all__ = [
    'start_retention_scheduler',
    'stop_retention_scheduler',
    'get_scheduler_status',
    'trigger_manual_cleanup',
    'run_retention_cleanup',
]
