# API Endpoints Specification - API Key Management

**Date**: 2025-11-20
**Status**: Phase 2 - Architecture Design
**Framework**: FastAPI

---

## Overview

This document defines **7 new API endpoints** for API key management, designed to integrate seamlessly with the existing OW-AI backend.

**Design Principles**:
- ✅ RESTful design
- ✅ Enterprise security (JWT for admin, API key for SDK)
- ✅ Comprehensive error handling
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Backward compatible with existing endpoints

---

## Authentication Strategy

### Dual Authentication Support

```python
# New middleware: Support BOTH JWT and API keys
async def get_current_user_or_api_key(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Try JWT first (admin UI), then API key (SDK)
    Returns user context for either method
    """
    # 1. Try JWT from cookie/header (existing)
    try:
        return await get_current_user(request, db)
    except HTTPException:
        pass

    # 2. Try API key from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]  # Remove "Bearer "
        return await verify_api_key(api_key, db)

    raise HTTPException(status_code=401, detail="Authentication required")
```

### Which Endpoints Use Which Auth?

| Endpoint | Authentication | Why |
|----------|----------------|-----|
| POST /api/keys/generate | **JWT only** | Admin creates keys |
| GET /api/keys/list | **JWT only** | Admin views keys |
| DELETE /api/keys/:id/revoke | **JWT only** | Admin revokes keys |
| POST /api/agent-action | **JWT OR API key** | Both admin and SDK |
| GET /api/agent-action/status/:id | **JWT OR API key** | Both admin and SDK |

---

## Endpoint 1: Generate API Key

### POST /api/keys/generate

**Purpose**: Generate a new API key for a user.

**Authentication**: JWT required (admin or user for own keys)

**Request**:
```json
{
  "name": "Production SDK Key",
  "description": "Used by AWS Lambda functions",
  "expires_in_days": 365,  // Optional, null = never expires
  "permissions": [  // Optional, null = inherit user permissions
    {
      "category": "agent_actions",
      "actions": ["create", "read"]
    }
  ],
  "rate_limit": {  // Optional, null = default
    "max_requests": 1000,
    "window_seconds": 3600
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "api_key": "owkai_admin_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
  "key_id": 1,
  "key_prefix": "owkai_admin_a1b2",
  "name": "Production SDK Key",
  "expires_at": "2026-11-20T00:00:00Z",
  "created_at": "2025-11-20T15:00:00Z",
  "warning": "⚠️ Save this key now - you will NOT see it again!"
}
```

**Errors**:
- 401: Not authenticated
- 403: Not authorized (trying to create key for another user)
- 400: Invalid request (name too long, invalid expiration, etc.)

**Implementation** (`routes/api_key_routes.py`):

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import secrets
import hashlib
from datetime import datetime, timedelta, UTC

router = APIRouter(prefix="/api/keys", tags=["API Keys"])

class PermissionRequest(BaseModel):
    category: str
    actions: List[str]

class RateLimitRequest(BaseModel):
    max_requests: int
    window_seconds: int

class GenerateKeyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None
    permissions: Optional[List[PermissionRequest]] = None
    rate_limit: Optional[RateLimitRequest] = None

@router.post("/generate")
async def generate_api_key(
    request: GenerateKeyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # JWT only
):
    """Generate new API key for current user"""

    # 1. Generate cryptographically secure key
    raw_key = secrets.token_urlsafe(32)  # 43 chars
    role_prefix = f"owkai_{current_user['role']}_"
    full_key = role_prefix + raw_key

    # 2. Extract prefix for display
    key_prefix = full_key[:16]

    # 3. Generate salt and hash
    salt = secrets.token_hex(16)
    key_hash = hashlib.sha256((full_key + salt).encode()).hexdigest()

    # 4. Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=request.expires_in_days)

    # 5. Create API key record
    api_key = ApiKey(
        user_id=current_user["user_id"],
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

    # 6. Add permissions (if specified)
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

    # 7. Add rate limit (if specified)
    if request.rate_limit:
        rate_limit = ApiKeyRateLimit(
            api_key_id=api_key.id,
            max_requests=request.rate_limit.max_requests,
            window_seconds=request.rate_limit.window_seconds
        )
        db.add(rate_limit)

    # 8. Commit transaction
    db.commit()

    # 9. Log audit event
    audit_log = ImmutableAuditLog(
        user_id=current_user["user_id"],
        action="api_key_generated",
        resource_type="api_key",
        resource_id=api_key.id,
        outcome="success",
        metadata={
            "key_prefix": key_prefix,
            "expires_at": expires_at.isoformat() if expires_at else None
        }
    )
    db.add(audit_log)
    db.commit()

    # 10. Return full key (shown ONCE)
    return {
        "success": True,
        "api_key": full_key,  # ← User must save this
        "key_id": api_key.id,
        "key_prefix": key_prefix,
        "name": api_key.name,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": api_key.created_at.isoformat(),
        "warning": "⚠️ Save this key now - you will NOT see it again!"
    }
```

---

## Endpoint 2: List API Keys

### GET /api/keys/list

**Purpose**: List all API keys for the current user (masked).

**Authentication**: JWT required

**Query Parameters**:
- `include_revoked` (boolean, default: false)
- `page` (int, default: 1)
- `page_size` (int, default: 20)

**Response** (200 OK):
```json
{
  "success": true,
  "keys": [
    {
      "id": 1,
      "name": "Production SDK Key",
      "key_prefix": "owkai_admin_a1b2",
      "is_active": true,
      "expires_at": "2026-11-20T00:00:00Z",
      "last_used_at": "2025-11-20T14:30:00Z",
      "usage_count": 15234,
      "created_at": "2025-11-20T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Staging SDK Key",
      "key_prefix": "owkai_admin_x9y8",
      "is_active": false,
      "revoked_at": "2025-11-19T10:00:00Z",
      "revoked_reason": "Compromised key - regenerated",
      "created_at": "2025-11-01T10:00:00Z"
    }
  ],
  "total_count": 2,
  "page": 1,
  "page_size": 20
}
```

**Implementation**:

```python
@router.get("/list")
async def list_api_keys(
    include_revoked: bool = False,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List user's API keys (masked)"""

    query = db.query(ApiKey).filter(ApiKey.user_id == current_user["user_id"])

    if not include_revoked:
        query = query.filter(ApiKey.is_active == True)

    total_count = query.count()

    keys = query.order_by(ApiKey.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return {
        "success": True,
        "keys": [key.to_dict() for key in keys],
        "total_count": total_count,
        "page": page,
        "page_size": page_size
    }
```

---

## Endpoint 3: Revoke API Key

### DELETE /api/keys/{key_id}/revoke

**Purpose**: Permanently revoke an API key (soft delete).

**Authentication**: JWT required

**Request**:
```json
{
  "reason": "Key compromised - detected in public GitHub repo"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "API key revoked successfully",
  "key_id": 1,
  "revoked_at": "2025-11-20T15:30:00Z"
}
```

**Implementation**:

```python
@router.delete("/{key_id}/revoke")
async def revoke_api_key(
    key_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Revoke API key (soft delete)"""

    # 1. Find key
    api_key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user["user_id"]
    ).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if not api_key.is_active:
        raise HTTPException(status_code=400, detail="API key already revoked")

    # 2. Revoke key
    api_key.is_active = False
    api_key.revoked_at = datetime.now(UTC)
    api_key.revoked_by = current_user["user_id"]
    api_key.revoked_reason = reason

    # 3. Log audit event
    audit_log = ImmutableAuditLog(
        user_id=current_user["user_id"],
        action="api_key_revoked",
        resource_type="api_key",
        resource_id=key_id,
        outcome="success",
        metadata={
            "reason": reason,
            "key_prefix": api_key.key_prefix
        }
    )
    db.add(audit_log)
    db.commit()

    return {
        "success": True,
        "message": "API key revoked successfully",
        "key_id": key_id,
        "revoked_at": api_key.revoked_at.isoformat()
    }
```

---

## Endpoint 4-7: Additional Endpoints (Concise Specs)

### POST /api/keys/{key_id}/regenerate
- Revoke old key, generate new one with same permissions
- Returns new full key (shown once)

### POST /api/keys/{key_id}/rotate
- Generate new key, keep old active for grace period
- Both keys work during transition

### GET /api/keys/{key_id}/usage
- Return usage statistics and recent logs
- Pagination support

### PUT /api/keys/{key_id}/permissions
- Update permissions for existing key
- Requires admin role

---

## Updated Existing Endpoint: Agent Action Creation

### POST /api/agent-action (MODIFIED)

**Changes**: Support API key authentication in addition to JWT

**Before**:
```python
@router.post("/agent-action")
async def create_action(
    data: ActionCreate,
    current_user: dict = Depends(get_current_user)  # JWT only
):
    ...
```

**After**:
```python
@router.post("/agent-action")
async def create_action(
    data: ActionCreate,
    current_user: dict = Depends(get_current_user_or_api_key)  # JWT OR API key
):
    # Log which auth method was used
    auth_method = current_user.get("auth_method", "jwt")

    # If API key, log usage
    if auth_method == "api_key":
        log_api_key_usage(
            api_key_id=current_user["api_key_id"],
            endpoint="/api/agent-action",
            http_method="POST",
            ...
        )

    # Rest of existing logic unchanged
    ...
```

---

## API Key Authentication Middleware

**File**: `dependencies_api_keys.py`

```python
async def verify_api_key(provided_key: str, db: Session) -> dict:
    """
    Verify API key and return user context
    """
    # 1. Extract prefix
    if len(provided_key) < 16:
        raise HTTPException(status_code=401, detail="Invalid API key format")

    prefix = provided_key[:16]

    # 2. Look up key by prefix (fast index scan)
    api_key = db.query(ApiKey).filter(
        ApiKey.key_prefix == prefix,
        ApiKey.is_active == True
    ).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 3. Hash provided key with stored salt
    provided_hash = hashlib.sha256((provided_key + api_key.salt).encode()).hexdigest()

    # 4. Constant-time comparison (prevent timing attacks)
    if not secrets.compare_digest(provided_hash, api_key.key_hash):
        # Log failed attempt
        log_failed_auth_attempt(api_key.id, "invalid_key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    # 5. Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=401, detail="API key expired")

    # 6. Check rate limit
    if not check_rate_limit(api_key.id, db):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # 7. Update usage tracking
    api_key.last_used_at = datetime.now(UTC)
    api_key.usage_count += 1
    db.commit()

    # 8. Load user
    user = db.query(User).filter(User.id == api_key.user_id).first()

    # 9. Return user context
    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "api_key_id": api_key.id,
        "auth_method": "api_key"
    }


async def log_api_key_usage(
    api_key_id: int,
    endpoint: str,
    http_method: str,
    http_status: int,
    ip_address: str,
    user_agent: str,
    request_id: str,
    response_time_ms: int,
    metadata: dict,
    db: Session
):
    """Log API key usage for audit trail"""

    log = ApiKeyUsageLog(
        api_key_id=api_key_id,
        user_id=current_user["user_id"],
        endpoint=endpoint,
        http_method=http_method,
        http_status=http_status,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        response_time_ms=response_time_ms,
        metadata=metadata
    )
    db.add(log)
    db.commit()
```

---

## Error Handling Standards

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid or has been revoked",
    "details": {
      "key_prefix": "owkai_admin_xxxx",
      "revoked_at": "2025-11-19T10:00:00Z"
    }
  }
}
```

**Error Codes**:
- `INVALID_API_KEY` - Key not found or invalid hash
- `API_KEY_EXPIRED` - Key past expiration date
- `API_KEY_REVOKED` - Key has been revoked
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `PERMISSION_DENIED` - Key lacks required permission
- `AUTHENTICATION_REQUIRED` - No auth provided

---

## Summary

### Endpoints Created: 7

1. POST /api/keys/generate - Generate new key
2. GET /api/keys/list - List user's keys
3. DELETE /api/keys/:id/revoke - Revoke key
4. POST /api/keys/:id/regenerate - Regenerate key
5. POST /api/keys/:id/rotate - Rotate key
6. GET /api/keys/:id/usage - Get usage stats
7. PUT /api/keys/:id/permissions - Update permissions

### Endpoints Modified: 2

1. POST /api/agent-action - Support API key auth
2. GET /api/agent-action/status/:id - Support API key auth

### Middleware Created: 2

1. `verify_api_key()` - API key authentication
2. `get_current_user_or_api_key()` - Dual auth support

**Next**: SDK Architecture Design
