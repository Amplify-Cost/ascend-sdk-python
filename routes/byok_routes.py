"""
SEC-BYOK-004/005/007/011: BYOK API routes for key management.

This module provides API endpoints for:
- Key registration (BYOK-004)
- Key status and health check (BYOK-005)
- Manual key rotation (BYOK-007)
- Automatic rotation is handled by the health check service (BYOK-011)

All endpoints require authentication and enforce multi-tenant isolation.

Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP, NIST 800-53
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, field_validator

from dependencies import get_current_user, get_db
from services.encryption.byok_service import BYOKEncryptionService
from services.encryption.byok_exceptions import (
    KeyAccessDenied,
    KeyValidationFailed,
    EncryptionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/byok", tags=["BYOK"])


# === Request/Response Models ===

class RegisterKeyRequest(BaseModel):
    """Request model for registering a CMK."""

    cmk_arn: str
    cmk_alias: Optional[str] = None

    @field_validator("cmk_arn")
    @classmethod
    def validate_cmk_arn(cls, v: str) -> str:
        """Validate CMK ARN format."""
        # Pattern: arn:aws:kms:<region>:<account>:key/<key-id>
        pattern = r"^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/[a-f0-9-]{36}$"
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid KMS key ARN format. Expected: arn:aws:kms:<region>:<account>:key/<key-id>"
            )
        return v


class KeyStatusResponse(BaseModel):
    """Response model for key status."""

    organization_id: int
    cmk_arn: str
    cmk_alias: Optional[str] = None
    status: str
    status_reason: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    last_rotation_at: Optional[datetime] = None
    created_at: datetime


class KeyHealthResponse(BaseModel):
    """Response model for key health check."""

    byok_enabled: bool
    status: Optional[str] = None
    cmk_accessible: Optional[bool] = None
    last_validated_at: Optional[datetime] = None
    cmk_arn_prefix: Optional[str] = None  # Masked for security
    dek_version: Optional[int] = None


class KeyRotationResponse(BaseModel):
    """Response model for key rotation."""

    success: bool
    message: str
    new_dek_version: Optional[int] = None
    rotated_at: datetime


class BYOKAuditEntry(BaseModel):
    """Response model for audit log entry."""

    id: int
    operation: str
    success: bool
    error_message: Optional[str] = None
    created_at: datetime


class BYOKAuditResponse(BaseModel):
    """Response model for audit log query."""

    entries: List[BYOKAuditEntry]
    total_count: int


# === API Endpoints ===

@router.post("/keys", response_model=KeyStatusResponse, status_code=status.HTTP_201_CREATED)
async def register_encryption_key(
    request: RegisterKeyRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Register a customer-managed encryption key (CMK) for BYOK.

    Prerequisites:
    1. Customer must create KMS key in their AWS account
    2. Customer must apply key policy granting ASCEND access
    3. Key must be symmetric encryption key

    Returns:
        KeyStatusResponse with registration status

    Raises:
        409: Organization already has a registered key
        400: Key validation failed
    """
    org_id = current_user.organization_id

    # SEC-BYOK-004: Check if key already registered
    existing = await db.fetch_one(
        "SELECT id FROM tenant_encryption_keys WHERE organization_id = $1",
        org_id,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization already has a registered encryption key. Use DELETE first, then register new key.",
        )

    # SEC-BYOK-004: Validate ASCEND can access the key
    byok_service = BYOKEncryptionService(db_session=db)
    is_valid, cmk_key_id, error_msg = await byok_service.validate_cmk_access(
        request.cmk_arn, org_id
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to access the provided KMS key: {error_msg}. "
            "Please verify the key policy grants ASCEND access. "
            "See docs/byok/CUSTOMER_KMS_SETUP.md for setup instructions.",
        )

    # SEC-BYOK-004: Register the key
    now = datetime.now(timezone.utc)
    result = await db.fetch_one(
        """
        INSERT INTO tenant_encryption_keys
            (organization_id, cmk_arn, cmk_alias, cmk_key_id, last_key_version,
             status, status_reason, last_validated_at, created_by)
        VALUES ($1, $2, $3, $4, $5, 'active', 'Key validated successfully', $6, $7)
        RETURNING id, organization_id, cmk_arn, cmk_alias, status, status_reason,
                  last_validated_at, last_rotation_at, created_at
        """,
        org_id,
        request.cmk_arn,
        request.cmk_alias,
        cmk_key_id,
        cmk_key_id,  # Initial key version
        now,
        current_user.id,
    )

    # SEC-BYOK-004: Generate initial DEK in background
    async def generate_initial_dek():
        try:
            await byok_service.generate_dek(request.cmk_arn, org_id, cmk_key_id)
            logger.info(f"BYOK-004: Initial DEK generated for org {org_id}")
        except Exception as e:
            logger.error(f"BYOK-004: Initial DEK generation failed for org {org_id}: {e}")

    background_tasks.add_task(generate_initial_dek)

    logger.info(f"BYOK-004: Key registered for org {org_id} by user {current_user.email}")

    return KeyStatusResponse(**dict(result))


@router.get("/keys", response_model=Optional[KeyStatusResponse])
async def get_encryption_key_status(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get the current BYOK configuration for the organization.

    Returns:
        KeyStatusResponse if BYOK is configured, null otherwise
    """
    org_id = current_user.organization_id

    result = await db.fetch_one(
        """
        SELECT organization_id, cmk_arn, cmk_alias, status, status_reason,
               last_validated_at, last_rotation_at, created_at
        FROM tenant_encryption_keys
        WHERE organization_id = $1
        """,
        org_id,
    )

    if not result:
        return None

    return KeyStatusResponse(**dict(result))


@router.delete("/keys")
async def revoke_encryption_key(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Revoke BYOK configuration.

    WARNING: This does NOT delete encrypted data. Data encrypted with
    the previous key will remain encrypted. If you want to re-enable
    BYOK, register a new key.

    Returns:
        Status message confirming revocation
    """
    org_id = current_user.organization_id

    result = await db.fetch_one(
        "SELECT cmk_arn FROM tenant_encryption_keys WHERE organization_id = $1",
        org_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encryption key registered for this organization",
        )

    # SEC-BYOK-004: Update status to revoked (don't delete — need for audit trail)
    await db.execute(
        """
        UPDATE tenant_encryption_keys
        SET status = 'revoked',
            status_reason = 'Revoked by user',
            updated_at = NOW()
        WHERE organization_id = $1
        """,
        org_id,
    )

    # Audit log
    await db.execute(
        """
        INSERT INTO byok_audit_log (organization_id, operation, cmk_arn, success, metadata)
        VALUES ($1, 'key_revoked', $2, TRUE, $3)
        """,
        org_id,
        result["cmk_arn"],
        {"revoked_by": current_user.email},
    )

    logger.info(f"BYOK-004: Key revoked for org {org_id} by user {current_user.email}")

    return {"status": "revoked", "message": "Encryption key has been revoked"}


@router.get("/health", response_model=KeyHealthResponse)
async def byok_health_check(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Check BYOK health for the current organization.

    This endpoint validates that ASCEND can still access the customer's CMK
    and returns the current BYOK status.

    Returns:
        KeyHealthResponse with health status
    """
    org_id = current_user.organization_id

    config = await db.fetch_one(
        """
        SELECT cmk_arn, cmk_alias, status, last_validated_at
        FROM tenant_encryption_keys
        WHERE organization_id = $1
        """,
        org_id,
    )

    if not config:
        return KeyHealthResponse(byok_enabled=False)

    # SEC-BYOK-005: Validate key access now
    byok_service = BYOKEncryptionService(db_session=db)
    is_accessible, _, _ = await byok_service.validate_cmk_access(config["cmk_arn"], org_id)

    # Get current DEK version
    dek_info = await db.fetch_one(
        """
        SELECT version FROM encrypted_data_keys
        WHERE organization_id = $1 AND is_current = TRUE
        """,
        org_id,
    )

    # Audit the health check
    await db.execute(
        """
        INSERT INTO byok_audit_log (organization_id, operation, cmk_arn, success, metadata)
        VALUES ($1, 'health_check', $2, $3, $4)
        """,
        org_id,
        config["cmk_arn"],
        is_accessible,
        {"checked_by": current_user.email},
    )

    return KeyHealthResponse(
        byok_enabled=True,
        status=config["status"],
        cmk_accessible=is_accessible,
        last_validated_at=config["last_validated_at"],
        cmk_arn_prefix=config["cmk_arn"][:40] + "...",  # Don't expose full ARN
        dek_version=dek_info["version"] if dek_info else None,
    )


@router.post("/keys/rotate", response_model=KeyRotationResponse)
async def rotate_encryption_key(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Manually rotate the Data Encryption Key (DEK).

    This generates a new DEK encrypted with the customer's CMK.
    Old DEKs are kept for decrypting existing data.

    Note: This does NOT rotate the CMK itself — that's managed by the
    customer in their AWS account.

    Returns:
        KeyRotationResponse with new DEK version
    """
    org_id = current_user.organization_id

    # Get current BYOK config
    config = await db.fetch_one(
        """
        SELECT cmk_arn, status, cmk_key_id
        FROM tenant_encryption_keys
        WHERE organization_id = $1
        """,
        org_id,
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encryption key registered for this organization",
        )

    if config["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot rotate key: current status is '{config['status']}'",
        )

    # SEC-BYOK-007: Generate new DEK
    byok_service = BYOKEncryptionService(db_session=db)

    try:
        # Validate CMK access first
        is_valid, cmk_key_id, error_msg = await byok_service.validate_cmk_access(
            config["cmk_arn"], org_id
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot access CMK for rotation: {error_msg}",
            )

        # Get current DEK version
        current_dek = await db.fetch_one(
            """
            SELECT version FROM encrypted_data_keys
            WHERE organization_id = $1 AND is_current = TRUE
            """,
            org_id,
        )
        new_version = (current_dek["version"] + 1) if current_dek else 1

        # Generate new DEK
        _, encrypted_dek, key_id = await byok_service.generate_dek(
            config["cmk_arn"], org_id, cmk_key_id
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
            key_id,
            now,
        )

        # Update tenant_encryption_keys
        await db.execute(
            """
            UPDATE tenant_encryption_keys
            SET last_rotation_at = $1, updated_at = $1
            WHERE organization_id = $2
            """,
            now,
            org_id,
        )

        # Audit log
        await db.execute(
            """
            INSERT INTO byok_audit_log (organization_id, operation, cmk_arn, success, metadata)
            VALUES ($1, 'key_rotated', $2, TRUE, $3)
            """,
            org_id,
            config["cmk_arn"],
            {"rotated_by": current_user.email, "new_version": new_version},
        )

        # Clear DEK cache
        byok_service.clear_dek_cache(org_id)

        logger.info(
            f"BYOK-007: DEK rotated for org {org_id} to version {new_version} "
            f"by user {current_user.email}"
        )

        return KeyRotationResponse(
            success=True,
            message=f"DEK rotated to version {new_version}",
            new_dek_version=new_version,
            rotated_at=now,
        )

    except (KeyAccessDenied, EncryptionError) as e:
        logger.error(f"BYOK-007: Rotation failed for org {org_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.get("/audit", response_model=BYOKAuditResponse)
async def get_byok_audit_log(
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get BYOK audit log for the current organization.

    Returns recent BYOK operations including key registration,
    validation, rotation, and encryption/decryption events.

    Args:
        limit: Maximum entries to return (default 50, max 500)
        offset: Pagination offset

    Returns:
        BYOKAuditResponse with audit entries
    """
    org_id = current_user.organization_id

    # Clamp limit
    limit = min(max(1, limit), 500)

    # Get entries
    entries = await db.fetch_all(
        """
        SELECT id, operation, success, error_message, created_at
        FROM byok_audit_log
        WHERE organization_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        org_id,
        limit,
        offset,
    )

    # Get total count
    count_result = await db.fetch_one(
        "SELECT COUNT(*) as count FROM byok_audit_log WHERE organization_id = $1",
        org_id,
    )

    return BYOKAuditResponse(
        entries=[BYOKAuditEntry(**dict(e)) for e in entries],
        total_count=count_result["count"],
    )
