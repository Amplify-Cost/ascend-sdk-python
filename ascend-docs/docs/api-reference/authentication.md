---
sidebar_position: 2
title: Authentication
description: API authentication methods and security
---

# Authentication

The Ascend API supports multiple authentication methods to accommodate different use cases, from browser-based admin access to automated SDK integrations.

## Authentication Methods

| Method | Best For | Security Level |
|--------|----------|----------------|
| **Session Cookie** | Admin UI, browser apps | Highest (HttpOnly, CSRF) |
| **JWT Bearer** | Cognito integration, mobile apps | High (RS256 signed) |
| **API Key** | SDK, automation, CI/CD | High (SHA-256 hashed) |

## Session Cookie Authentication

Used by the Admin UI for browser-based access with maximum security.

### How It Works

1. User authenticates via Cognito
2. Backend creates enterprise JWT
3. JWT stored in HttpOnly cookie (`access_token`)
4. CSRF token provided for mutation protection

### Cookie Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| `HttpOnly` | true | Prevent XSS access |
| `Secure` | true | HTTPS only |
| `SameSite` | Lax | CSRF protection |
| `Path` | / | All paths |

### CSRF Protection

Mutating requests (POST, PUT, DELETE) require CSRF token:

```bash
curl -X POST "https://pilot.owkai.app/api/actions" \
  -H "Cookie: access_token=..." \
  -H "X-CSRF-Token: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "create"}'
```

The CSRF token is provided in the `owai_csrf` cookie and must match the `X-CSRF-Token` header.

**Compliance:** OWASP CSRF Prevention, SOC 2 CC6.1

## JWT Bearer Authentication

For Cognito-authenticated clients and programmatic access.

### Cognito JWT

After authenticating with AWS Cognito, use the access token:

```bash
curl "https://pilot.owkai.app/api/v1/actions" \
  -H "Authorization: Bearer eyJraWQiOiJsNktH..."
```

### Token Verification

| Check | Description |
|-------|-------------|
| Signature | RS256 verified against Cognito JWKS |
| Expiration | Token must not be expired (1 hour default) |
| Issuer | Must match Cognito User Pool |
| Audience | Must match App Client ID |

### Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | Cognito user ID |
| `email` | User email address |
| `cognito:groups` | Cognito groups (for roles) |
| `token_use` | Must be "access" |

### Enterprise Token (SEC-081)

Internal endpoints use enterprise tokens with additional claims:

| Claim | Description |
|-------|-------------|
| `db_user_id` | Database user ID (integer) |
| `db_org_id` | Database organization ID |
| `role` | User role |
| `permissions` | Permission set |

**Source:** `services/token_service.py`

## API Key Authentication

For SDK integration, automation, and external systems.

### Key Format

```
owkai_admin_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
└────┬────┘└─┬─┘└──────────────┬──────────────┘
   prefix  role        random token (43 chars)
```

### Using API Keys

**Option 1: X-API-Key Header (Recommended)**

```bash
curl "https://pilot.owkai.app/api/v1/actions" \
  -H "X-API-Key: owkai_admin_your_api_key"
```

**Option 2: Bearer Token**

```bash
curl "https://pilot.owkai.app/api/v1/actions" \
  -H "Authorization: Bearer owkai_admin_your_api_key"
```

### Key Security

| Feature | Implementation |
|---------|----------------|
| Storage | SHA-256 hash with random salt |
| Comparison | Constant-time (timing attack resistant) |
| Display | Only prefix visible after creation |
| Expiration | Configurable (default: 365 days) |

### Key Prefixes by Role

| Role | Prefix |
|------|--------|
| Admin | `owkai_admin_` |
| User | `owkai_user_` |
| Manager | `owkai_manager_` |

**Source:** `routes/api_key_routes.py`, `dependencies_api_keys.py`

## Dual Authentication

Some endpoints support both JWT and API key:

```python
# Backend dependency
@router.get("/data")
async def get_data(
    current_user = Depends(get_current_user_or_api_key)
):
    # Works with either authentication method
    return {"org_id": current_user["organization_id"]}
```

### Priority Order

1. Session cookie (if present)
2. JWT Bearer token (if present and valid)
3. API key (Bearer or X-API-Key header)

## Multi-Tenant Isolation

All authentication methods enforce organization isolation:

```python
# Every authenticated request includes organization_id
{
    "user_id": 123,
    "email": "user@company.com",
    "organization_id": 4,  # Always present
    "role": "admin"
}
```

### Security Enforcement

| Layer | Protection |
|-------|------------|
| Application | `get_organization_filter()` dependency |
| Database | Row-Level Security (RLS) policies |
| Query | All queries filter by `organization_id` |

**Compliance:** SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)

## Token Expiration

| Token Type | Default | Maximum |
|------------|---------|---------|
| Access Token | 60 minutes | 24 hours |
| Refresh Token | 30 days | 365 days |
| API Key | 365 days | Never |
| Session Cookie | 60 minutes | 24 hours |

### Refresh Flow

```bash
# Refresh expired access token
curl -X POST "https://pilot.owkai.app/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your_refresh_token"}'
```

**Response:**

```json
{
  "access_token": "new_access_token",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Authentication required"
}
```

**Causes:**
- Missing authentication header/cookie
- Expired token
- Invalid token signature

### 403 Forbidden

```json
{
  "detail": "Admin access required"
}
```

**Causes:**
- Insufficient permissions
- CSRF validation failed
- Organization access denied

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

**Headers:**
```
Retry-After: 3600
```

## Security Best Practices

1. **Rotate API keys regularly** - Every 90 days recommended
2. **Use minimal permissions** - Only grant required access
3. **Set expiration dates** - Avoid never-expiring keys
4. **Monitor usage** - Review API key activity weekly
5. **Revoke promptly** - Disable compromised keys immediately
6. **Use HTTPS only** - All endpoints require TLS

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/cognito-session` | POST | Exchange Cognito tokens |
| `/api/auth/refresh` | POST | Refresh access token |
| `/api/auth/logout` | POST | Invalidate session |
| `/api/keys/generate` | POST | Generate API key |
| `/api/keys/list` | GET | List API keys |
| `/api/keys/{id}/revoke` | DELETE | Revoke API key |

**Compliance:** SOC 2 CC6.1, NIST IA-2/IA-5, PCI-DSS 8.3

---

*Source: [dependencies.py](https://github.com/owkai/ow-ai-backend/blob/main/dependencies.py), [dependencies_api_keys.py](https://github.com/owkai/ow-ai-backend/blob/main/dependencies_api_keys.py), [dependencies_cognito.py](https://github.com/owkai/ow-ai-backend/blob/main/dependencies_cognito.py)*
