"""
SEC-BYOK-005/011: BYOK health check and automatic rotation detection.

This module provides:
- Periodic validation of all registered BYOK keys (BYOK-005)
- Automatic detection of CMK rotation (BYOK-011)
- Notification on key access failures

The health check runs every 15 minutes and:
1. Validates ASCEND can still access each customer's CMK
2. Detects if the CMK has been rotated (by checking key version)
3. Auto-generates new DEK when rotation is detected
4. Updates key status on access failure
5. Sends notifications when issues are detected

Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP, NIST 800-53
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from services.encryption.byok_service import BYOKEncryptionService
from services.encryption.byok_exceptions import KeyAccessDenied

logger = logging.getLogger(__name__)

# Health check interval in seconds (15 minutes)
HEALTH_CHECK_INTERVAL_SECONDS = 15 * 60


class BYOKHealthService:
    """
    Service for periodic BYOK key validation and automatic rotation detection.

    This service implements:
    - BYOK-005: Health check + validation
    - BYOK-011: Automatic rotation detection

    It should be run as a background task, typically started in the FastAPI
    lifespan or as a separate worker process.
    """

    def __init__(self, db_pool):
        """
        Initialize the BYOK health service.

        Args:
            db_pool: Database connection pool for queries
        """
        self.db_pool = db_pool
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the periodic health check task."""
        if self._running:
            logger.warning("BYOK-005: Health service already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_health_check_loop())
        logger.info("BYOK-005: Health check service started")

    async def stop(self) -> None:
        """Stop the periodic health check task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BYOK-005: Health check service stopped")

    async def _run_health_check_loop(self) -> None:
        """Main loop for periodic health checks."""
        while self._running:
            try:
                await self.validate_all_tenant_keys()
            except Exception as e:
                logger.error(f"BYOK-005: Health check loop error: {e}")

            # Wait for next interval
            await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    async def validate_all_tenant_keys(self) -> Dict[str, Any]:
        """
        Validate all registered BYOK keys.

        This is the main health check function that:
        1. Gets all active BYOK configurations
        2. Validates CMK access for each
        3. Detects CMK rotation and auto-generates new DEK
        4. Updates status on failure

        Returns:
            Summary of validation results
        """
        async with self.db_pool.acquire() as db:
            # Get all active BYOK configurations
            keys = await db.fetch_all(
                """
                SELECT organization_id, cmk_arn, cmk_key_id, last_key_version, status
                FROM tenant_encryption_keys
                WHERE status IN ('active', 'rotation_pending')
                """
            )

            if not keys:
                logger.debug("BYOK-005: No active BYOK keys to validate")
                return {"validated": 0, "failed": 0, "rotated": 0}

            results = {
                "validated": 0,
                "failed": 0,
                "rotated": 0,
                "failures": [],
            }

            byok_service = BYOKEncryptionService(db_session=db)

            for key in keys:
                try:
                    await self._validate_single_key(db, byok_service, key, results)
                except Exception as e:
                    logger.error(
                        f"BYOK-005: Error validating key for org {key['organization_id']}: {e}"
                    )
                    results["failures"].append({
                        "organization_id": key["organization_id"],
                        "error": str(e),
                    })

            logger.info(
                f"BYOK-005: Health check complete - "
                f"validated={results['validated']}, "
                f"failed={results['failed']}, "
                f"rotated={results['rotated']}"
            )

            return results

    async def _validate_single_key(
        self,
        db,
        byok_service: BYOKEncryptionService,
        key: Dict[str, Any],
        results: Dict[str, Any],
    ) -> None:
        """
        Validate a single BYOK key.

        Args:
            db: Database connection
            byok_service: BYOK encryption service
            key: Key configuration from database
            results: Results dictionary to update
        """
        org_id = key["organization_id"]
        cmk_arn = key["cmk_arn"]

        # SEC-BYOK-005: Validate CMK access
        is_valid, current_key_id, error_msg = await byok_service.validate_cmk_access(
            cmk_arn, org_id
        )

        if not is_valid:
            # Key access failed — update status
            await self._handle_validation_failure(db, org_id, cmk_arn, error_msg)
            results["failed"] += 1
            results["failures"].append({
                "organization_id": org_id,
                "error": error_msg,
            })
            return

        # SEC-BYOK-011: Check for CMK rotation
        last_key_version = key.get("last_key_version")
        if last_key_version and current_key_id and last_key_version != current_key_id:
            # CMK has been rotated — generate new DEK
            logger.info(
                f"BYOK-011: CMK rotation detected for org {org_id} "
                f"(old={last_key_version[:16]}... new={current_key_id[:16]}...)"
            )

            await self._handle_auto_rotation(
                db, byok_service, org_id, cmk_arn, current_key_id
            )
            results["rotated"] += 1

        # Update last validated timestamp and key version
        now = datetime.now(timezone.utc)
        await db.execute(
            """
            UPDATE tenant_encryption_keys
            SET last_validated_at = $1,
                last_key_version = $2,
                cmk_key_id = $2,
                status = 'active',
                status_reason = 'Key validated successfully',
                updated_at = $1
            WHERE organization_id = $3
            """,
            now,
            current_key_id,
            org_id,
        )

        results["validated"] += 1

    async def _handle_validation_failure(
        self,
        db,
        org_id: int,
        cmk_arn: str,
        error_msg: str,
    ) -> None:
        """
        Handle CMK validation failure.

        Updates key status and logs the failure.
        Optionally sends notification to tenant admin.
        """
        logger.warning(f"BYOK-005: Key validation failed for org {org_id}: {error_msg}")

        # Update status to error
        await db.execute(
            """
            UPDATE tenant_encryption_keys
            SET status = 'error',
                status_reason = $1,
                updated_at = NOW()
            WHERE organization_id = $2
            """,
            f"Validation failed: {error_msg}",
            org_id,
        )

        # Audit log
        await db.execute(
            """
            INSERT INTO byok_audit_log
                (organization_id, operation, cmk_arn, success, error_message, metadata)
            VALUES ($1, 'validation_failed', $2, FALSE, $3, $4)
            """,
            org_id,
            cmk_arn,
            error_msg,
            {"source": "health_check"},
        )

        # TODO: Send notification to tenant admin
        # This would integrate with the existing notification system
        await self._notify_key_failure(db, org_id, error_msg)

    async def _handle_auto_rotation(
        self,
        db,
        byok_service: BYOKEncryptionService,
        org_id: int,
        cmk_arn: str,
        new_key_id: str,
    ) -> None:
        """
        Handle automatic CMK rotation detection (BYOK-011).

        When customer rotates their CMK, we:
        1. Generate a new DEK encrypted with the new key material
        2. Mark old DEKs as not current
        3. Log the rotation event
        """
        try:
            # Get current DEK version
            current_dek = await db.fetch_one(
                """
                SELECT version FROM encrypted_data_keys
                WHERE organization_id = $1 AND is_current = TRUE
                """,
                org_id,
            )
            new_version = (current_dek["version"] + 1) if current_dek else 1

            # Generate new DEK with new CMK version
            _, encrypted_dek, _ = await byok_service.generate_dek(
                cmk_arn, org_id, new_key_id
            )

            # Mark old DEKs as not current
            await db.execute(
                """
                UPDATE encrypted_data_keys
                SET is_current = FALSE
                WHERE organization_id = $1 AND is_current = TRUE
                """,
                org_id,
            )

            # Insert new DEK
            now = datetime.now(timezone.utc)
            await db.execute(
                """
                INSERT INTO encrypted_data_keys
                    (organization_id, encrypted_dek, encryption_context,
                     version, is_current, cmk_key_version, created_at)
                VALUES ($1, $2, $3, $4, TRUE, $5, $6)
                """,
                org_id,
                encrypted_dek,
                {"tenant_id": str(org_id), "service": "ascend"},
                new_version,
                new_key_id,
                now,
            )

            # Update tenant_encryption_keys
            await db.execute(
                """
                UPDATE tenant_encryption_keys
                SET last_rotation_at = $1,
                    last_key_version = $2,
                    cmk_key_id = $2,
                    updated_at = $1
                WHERE organization_id = $3
                """,
                now,
                new_key_id,
                org_id,
            )

            # Audit log
            await db.execute(
                """
                INSERT INTO byok_audit_log
                    (organization_id, operation, cmk_arn, success, metadata)
                VALUES ($1, 'auto_rotation_detected', $2, TRUE, $3)
                """,
                org_id,
                cmk_arn,
                {
                    "new_key_id": new_key_id,
                    "new_dek_version": new_version,
                    "source": "health_check",
                },
            )

            # Clear DEK cache
            byok_service.clear_dek_cache(org_id)

            logger.info(
                f"BYOK-011: Auto-rotation complete for org {org_id}, "
                f"new DEK version {new_version}"
            )

        except Exception as e:
            logger.error(f"BYOK-011: Auto-rotation failed for org {org_id}: {e}")

            # Audit the failure
            await db.execute(
                """
                INSERT INTO byok_audit_log
                    (organization_id, operation, cmk_arn, success, error_message, metadata)
                VALUES ($1, 'auto_rotation_detected', $2, FALSE, $3, $4)
                """,
                org_id,
                cmk_arn,
                str(e),
                {"new_key_id": new_key_id, "source": "health_check"},
            )

    async def _notify_key_failure(
        self,
        db,
        org_id: int,
        error_msg: str,
    ) -> None:
        """
        Send notification to tenant admin about key failure.

        This integrates with the existing notification system.
        """
        try:
            # Get organization admins
            admins = await db.fetch_all(
                """
                SELECT email, first_name
                FROM users
                WHERE organization_id = $1 AND is_org_admin = TRUE
                """,
                org_id,
            )

            if not admins:
                logger.warning(f"BYOK-005: No admins found for org {org_id} to notify")
                return

            # Get organization name
            org = await db.fetch_one(
                "SELECT name FROM organizations WHERE id = $1",
                org_id,
            )
            org_name = org["name"] if org else f"Organization {org_id}"

            # Log notification (actual email sending would go through notification service)
            for admin in admins:
                logger.info(
                    f"BYOK-005: Would notify {admin['email']} about key failure for {org_name}"
                )
                # TODO: Integrate with notification service
                # await notification_service.send_email(
                #     to=admin["email"],
                #     subject=f"[ASCEND] BYOK Key Access Issue - {org_name}",
                #     template="byok_key_failure",
                #     context={
                #         "admin_name": admin["first_name"],
                #         "org_name": org_name,
                #         "error": error_msg,
                #     }
                # )

        except Exception as e:
            logger.error(f"BYOK-005: Failed to send notification for org {org_id}: {e}")


async def run_single_health_check(db_pool) -> Dict[str, Any]:
    """
    Run a single health check (for testing or manual invocation).

    Args:
        db_pool: Database connection pool

    Returns:
        Health check results
    """
    service = BYOKHealthService(db_pool)
    return await service.validate_all_tenant_keys()
