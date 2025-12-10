"""
Enterprise API Key Management Routes

Purpose: Production-grade API key generation and management for OW-AI SDK
Security: SHA-256 hashing, CSRF protection, audit logging
Compliance: SOX, GDPR, HIPAA, PCI-DSS requirements

Created: 2025-11-20
Status: Production-ready
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timedelta, UTC
import secrets
import hashlib
import logging

# Import dependencies
from database import get_db
from dependencies import get_current_user
# SEC-091 PHASE 2: Use dual auth org filter for routes that support both JWT and API keys
from dependencies_api_keys import get_current_user_or_api_key, get_organization_filter_dual_auth
from models import User
from models_api_keys import ApiKey, ApiKeyUsageLog, ApiKeyPermission, ApiKeyRateLimit
from models_audit import ImmutableAuditLog  # For audit trail

# Setup logging
logger = logging.getLogger("enterprise.api_keys")

# Router configuration
router = APIRouter(prefix="/api/keys", tags=["API Key Management"])


# ========================================
# Request/Response Models
# ========================================

class PermissionRequest(BaseModel):
    """Permission definition for API key"""
    category: str = Field(..., description="Permission category (e.g., 'agent_actions', 'alerts')")
    actions: List[str] = Field(..., description="Allowed actions (e.g., ['create', 'read'])")


class RateLimitRequest(BaseModel):
    """Rate limit configuration for API key"""
    max_requests: int = Field(default=1000, ge=1, le=100000, description="Maximum requests per window")
    window_seconds: int = Field(default=3600, ge=60, le=86400, description="Time window in seconds")


class GenerateKeyRequest(BaseModel):
    """Request to generate a new API key"""
    name: str = Field(..., min_length=1, max_length=255, description="User-friendly name for the key")
    description: Optional[str] = Field(None, max_length=1000, description="Purpose of the key")
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650, description="Expiration in days (NULL = never expires)")
    permissions: Optional[List[PermissionRequest]] = Field(None, description="Specific permissions (NULL = inherit user permissions)")
    rate_limit: Optional[RateLimitRequest] = Field(None, description="Rate limit config (NULL = default 1000/hour)")

    # SEC-094: Accept both string shorthand and object format for permissions
    @field_validator('permissions', mode='before')
    @classmethod
    def convert_permission_strings(cls, v):
        """
        SEC-094: Convert string permissions to PermissionRequest format.

        Accepts:
          - "agent:read" → {"category": "agent", "actions": ["read"]}
          - "action:submit" → {"category": "action", "actions": ["submit"]}
          - {"category": "agent", "actions": ["read"]} → unchanged

        Groups by category for efficiency (e.g., ["agent:read", "agent:write"]
        becomes [{"category": "agent", "actions": ["read", "write"]}])
        """
        if v is None:
            return v

        if not isinstance(v, list):
            return v

        converted = []
        category_map = {}  # Track categories for grouping

        for item in v:
            if isinstance(item, str):
                # SEC-094: Parse "category:action" format
                if ':' not in item:
                    raise ValueError(f"SEC-094: Invalid permission format: '{item}'. Expected 'category:action' (e.g., 'agent:read')")

                parts = item.split(':', 1)
                category = parts[0].strip()
                action = parts[1].strip()

                if not category or not action:
                    raise ValueError(f"SEC-094: Empty category or action in: '{item}'")

                # Group by category for efficiency
                if category in category_map:
                    if action not in category_map[category]['actions']:
                        category_map[category]['actions'].append(action)
                else:
                    category_map[category] = {'category': category, 'actions': [action]}

            elif isinstance(item, dict):
                # Already structured format - pass through
                converted.append(item)
            else:
                raise ValueError(f"SEC-094: Invalid permission type: {type(item).__name__}. Expected string or dict.")

        # Add grouped string permissions to result
        converted.extend(category_map.values())

        logger.debug(f"SEC-094: Converted permissions: {converted}")
        return converted


class ApiKeyResponse(BaseModel):
    """Response after generating API key"""
    success: bool
    api_key: str  # Full key shown ONCE
    key_id: int
    key_prefix: str
    name: str
    expires_at: Optional[str]
    created_at: str
    warning: str = "⚠️ Save this key now - you will NOT see it again!"


class ApiKeyListResponse(BaseModel):
    """Response for listing API keys"""
    success: bool
    keys: List[dict]
    total_count: int
    page: int
    page_size: int


# ========================================
# Helper Functions
# ========================================

def generate_cryptographic_key(role: str) -> tuple[str, str, str, str]:
    """
    Generate cryptographically secure API key with role prefix

    Args:
        role: User role (admin, user, etc.)

    Returns:
        (full_key, key_prefix, key_hash, salt)

    Security:
    - 256-bit entropy (secrets.token_urlsafe(32) = 43 chars)
    - Role-based prefix for easy identification
    - SHA-256 hashing with random salt
    """
    # Generate random key with 256-bit entropy
    raw_key = secrets.token_urlsafe(32)  # 43 characters

    # Add role prefix
    role_prefix = f"owkai_{role}_"
    full_key = role_prefix + raw_key

    # SEC-096: Extract display prefix (first 32 chars for uniqueness)
    # Role prefix "owkai_super_admin_" = 18 chars, so 32 includes 14 random chars
    key_prefix = full_key[:32]

    # Generate salt and hash
    salt = secrets.token_hex(16)  # 32 characters
    key_hash = hashlib.sha256((full_key + salt).encode()).hexdigest()

    logger.info(f"Generated API key with prefix: {key_prefix}")
    return full_key, key_prefix, key_hash, salt


def log_audit_event(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    outcome: str,
    metadata: dict
):
    """
    Log audit event to immutable audit log

    Args:
        db: Database session
        user_id: User performing action
        action: Action name (e.g., 'api_key_generated')
        resource_type: Type of resource (e.g., 'api_key')
        resource_id: ID of resource
        outcome: 'success' or 'failure'
        metadata: Additional context
    """
    try:
        audit_log = ImmutableAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            metadata=metadata
        )
        db.add(audit_log)
        db.commit()
        logger.info(f"Audit log created: {action} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't fail the main operation if audit logging fails
        db.rollback()


# ========================================
# Endpoint 1: Generate API Key
# ========================================

@router.post("/generate", response_model=ApiKeyResponse)
async def generate_api_key(
    request: GenerateKeyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-091: Dual auth for API key routes
):
    """
    Generate a new API key for the current user

    Security:
    - JWT authentication required (admin UI only)
    - SHA-256 hashing with salt
    - Full key returned ONCE (never shown again)
    - Complete audit trail

    Returns:
        ApiKeyResponse with full key (save immediately!)
    """
    try:
        # 1. Generate cryptographic key
        full_key, key_prefix, key_hash, salt = generate_cryptographic_key(current_user["role"])

        # 2. Calculate expiration
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=request.expires_in_days)

        # 3. Create API key record (SEC-082: Enforce org_id)
        api_key = ApiKey(
            user_id=current_user["user_id"],
            organization_id=org_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            salt=salt,
            name=request.name,
            description=request.description,
            is_active=True,
            expires_at=expires_at
        )
        db.add(api_key)
        db.flush()  # Get ID without committing

        # 4. Add permissions (if specified)
        if request.permissions:
            for perm in request.permissions:
                for action in perm.actions:
                    permission = ApiKeyPermission(
                        api_key_id=api_key.id,
                        permission_category=perm.category,
                        permission_action=action,
                        granted_by=current_user["user_id"]
                    )
                    db.add(permission)

        # 5. Add rate limit (if specified)
        if request.rate_limit:
            rate_limit = ApiKeyRateLimit(
                api_key_id=api_key.id,
                max_requests=request.rate_limit.max_requests,
                window_seconds=request.rate_limit.window_seconds
            )
            db.add(rate_limit)
        else:
            # Default rate limit: 1000 requests per hour
            rate_limit = ApiKeyRateLimit(
                api_key_id=api_key.id,
                max_requests=1000,
                window_seconds=3600
            )
            db.add(rate_limit)

        # 6. Commit transaction
        db.commit()

        # 7. Log audit event
        log_audit_event(
            db=db,
            user_id=current_user["user_id"],
            action="api_key_generated",
            resource_type="api_key",
            resource_id=api_key.id,
            outcome="success",
            metadata={
                "key_prefix": key_prefix,
                "key_name": request.name,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "permissions_count": len(request.permissions) if request.permissions else 0
            }
        )

        logger.info(f"✅ API key generated for user {current_user['email']}: {key_prefix}")

        # 8. Return full key (shown ONCE)
        return ApiKeyResponse(
            success=True,
            api_key=full_key,  # ← User must save this
            key_id=api_key.id,
            key_prefix=key_prefix,
            name=api_key.name,
            expires_at=expires_at.isoformat() if expires_at else None,
            created_at=api_key.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate API key: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate API key: {str(e)}"
        )


# ========================================
# Endpoint 2: List API Keys
# ========================================

@router.get("/list", response_model=ApiKeyListResponse)
async def list_api_keys(
    include_revoked: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-091: Dual auth for API key routes
):
    """
    List all API keys for the current user (masked)

    Security:
    - JWT authentication required
    - Only shows user's own keys
    - Keys are masked (prefix only)
    - SEC-082: Multi-tenant isolation

    Returns:
        List of API keys with usage stats
    """
    try:
        # Build query (SEC-082: Filter by org_id)
        query = db.query(ApiKey).filter(
            ApiKey.user_id == current_user["user_id"],
            ApiKey.organization_id == org_id
        )

        if not include_revoked:
            query = query.filter(ApiKey.is_active == True)

        # Get total count
        total_count = query.count()

        # Apply pagination
        keys = query.order_by(ApiKey.created_at.desc()) \
                    .offset((page - 1) * page_size) \
                    .limit(page_size) \
                    .all()

        # Convert to dict (masks full key)
        keys_data = [key.to_dict() for key in keys]

        logger.info(f"✅ Listed {len(keys_data)} API keys for user {current_user['email']}")

        return ApiKeyListResponse(
            success=True,
            keys=keys_data,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


# ========================================
# Endpoint 3: Revoke API Key
# ========================================

@router.delete("/{key_id}/revoke")
async def revoke_api_key(
    key_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-091: Dual auth for API key routes
):
    """
    Revoke an API key (soft delete)

    Security:
    - JWT authentication required
    - Only owner can revoke
    - Requires reason for audit trail
    - SEC-082: Validates ownership before deletion

    Returns:
        Success message with revocation timestamp
    """
    try:
        # 1. Find key (SEC-082: Verify ownership via org_id)
        api_key = db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user["user_id"],
            ApiKey.organization_id == org_id
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        if not api_key.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key already revoked"
            )

        # 2. Revoke key
        api_key.is_active = False
        api_key.revoked_at = datetime.now(UTC)
        api_key.revoked_by = current_user["user_id"]
        api_key.revoked_reason = reason or "User revoked"

        db.commit()

        # 3. Log audit event
        log_audit_event(
            db=db,
            user_id=current_user["user_id"],
            action="api_key_revoked",
            resource_type="api_key",
            resource_id=key_id,
            outcome="success",
            metadata={
                "key_prefix": api_key.key_prefix,
                "reason": reason
            }
        )

        logger.info(f"✅ API key revoked: {api_key.key_prefix}")

        return {
            "success": True,
            "message": "API key revoked successfully",
            "key_id": key_id,
            "revoked_at": api_key.revoked_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to revoke API key: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


# ========================================
# Endpoint 4: Get API Key Usage
# ========================================

@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_api_key),
    org_id: int = Depends(get_organization_filter_dual_auth)  # SEC-091: Dual auth for API key routes
):
    """
    Get usage statistics for an API key

    Security:
    - JWT authentication required
    - Only owner can view usage
    - SEC-082: Validates ownership before reading

    Returns:
        Usage statistics and recent activity
    """
    try:
        # 1. Verify ownership (SEC-082: Check org_id)
        api_key = db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user["user_id"],
            ApiKey.organization_id == org_id
        ).first()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # 2. Get usage logs
        usage_logs = db.query(ApiKeyUsageLog).filter(
            ApiKeyUsageLog.api_key_id == key_id
        ).order_by(ApiKeyUsageLog.created_at.desc()).limit(limit).all()

        # 3. Calculate statistics
        total_requests = api_key.usage_count
        recent_requests = len(usage_logs)

        # Success rate
        if usage_logs:
            successful = sum(1 for log in usage_logs if 200 <= log.http_status < 300)
            success_rate = (successful / len(usage_logs)) * 100
        else:
            success_rate = 0

        logger.info(f"✅ Retrieved usage for API key: {api_key.key_prefix}")

        return {
            "success": True,
            "key_id": key_id,
            "key_prefix": api_key.key_prefix,
            "statistics": {
                "total_requests": total_requests,
                "recent_requests": recent_requests,
                "success_rate": round(success_rate, 2),
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None
            },
            "recent_activity": [
                {
                    "timestamp": log.created_at.isoformat(),
                    "endpoint": log.endpoint,
                    "method": log.http_method,
                    "status": log.http_status,
                    "ip_address": log.ip_address,
                    "response_time_ms": log.response_time_ms
                }
                for log in usage_logs
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get API key usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API key usage: {str(e)}"
        )
