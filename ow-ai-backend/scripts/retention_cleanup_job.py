#!/usr/bin/env python3
"""
Enterprise Retention Cleanup Job
Scheduled job for automated retention enforcement

Usage:
    # Dry run (default)
    python3 scripts/retention_cleanup_job.py

    # Actual cleanup
    python3 scripts/retention_cleanup_job.py --execute

    # Custom batch size
    python3 scripts/retention_cleanup_job.py --execute --max-delete 500

Schedule with cron:
    # Run daily at 2 AM
    0 2 * * * /usr/bin/python3 /path/to/retention_cleanup_job.py --execute

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    RETENTION_MAX_DELETE: Maximum logs to delete per run (default: 1000)
    RETENTION_DRY_RUN: Set to 'false' to enable actual deletion
"""

import sys
import os
import argparse
import logging
from datetime import datetime, UTC

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from services.retention_policy_service import RetentionPolicyService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('retention_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

def run_retention_cleanup(dry_run: bool = True, max_delete: int = 1000):
    """
    Execute retention cleanup job

    Args:
        dry_run: If True, only report what would be deleted
        max_delete: Maximum number of logs to delete

    Returns:
        Statistics dict
    """
    logger.info("=" * 80)
    logger.info(f"Starting retention cleanup job at {datetime.now(UTC).isoformat()}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.info(f"Max delete: {max_delete}")
    logger.info("=" * 80)

    db = SessionLocal()

    try:
        service = RetentionPolicyService(db)

        # Get statistics before cleanup
        logger.info("Fetching retention statistics...")
        stats_before = service.get_retention_statistics()
        logger.info(f"Total logs: {stats_before['total_logs']}")
        logger.info(f"Expired logs: {stats_before['expired_logs']}")
        logger.info(f"Legal hold logs: {stats_before['legal_hold_logs']}")
        logger.info(f"Eligible for deletion: {stats_before['eligible_for_deletion']}")

        # Execute cleanup
        logger.info("\nExecuting cleanup...")
        result = service.cleanup_expired_logs(
            dry_run=dry_run,
            max_delete=max_delete
        )

        if dry_run:
            logger.info(f"DRY RUN: Would delete {result['would_delete']} logs")
            logger.info(f"Total expired: {result['total_expired']}")
            if result['oldest_retention_date']:
                logger.info(f"Oldest retention date: {result['oldest_retention_date']}")
            if result['newest_retention_date']:
                logger.info(f"Newest retention date: {result['newest_retention_date']}")
        else:
            logger.warning(f"DELETED {result['deleted']} expired logs")
            logger.warning("Hash chain may be broken for deleted logs")
            logger.info(f"Remaining expired: {result['remaining_expired']}")

            # Log some deleted IDs (first 10)
            if result['deleted_ids']:
                logger.info(f"Sample deleted IDs: {result['deleted_ids'][:10]}")

        # Get statistics after cleanup (if not dry run)
        if not dry_run:
            logger.info("\nFetching post-cleanup statistics...")
            stats_after = service.get_retention_statistics()
            logger.info(f"Total logs after: {stats_after['total_logs']}")
            logger.info(f"Logs deleted: {stats_before['total_logs'] - stats_after['total_logs']}")

        logger.info("=" * 80)
        logger.info("Retention cleanup job completed successfully")
        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error(f"Retention cleanup job failed: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()

def main():
    """Main entry point for retention cleanup job"""
    parser = argparse.ArgumentParser(
        description='Enterprise Retention Cleanup Job',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute actual deletion (default is dry run)'
    )

    parser.add_argument(
        '--max-delete',
        type=int,
        default=int(os.getenv('RETENTION_MAX_DELETE', '1000')),
        help='Maximum number of logs to delete per run (default: 1000)'
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.execute
    if os.getenv('RETENTION_DRY_RUN', '').lower() == 'false':
        dry_run = False

    try:
        result = run_retention_cleanup(
            dry_run=dry_run,
            max_delete=args.max_delete
        )

        # Exit with appropriate code
        sys.exit(0)

    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
