---
Document ID: ASCEND-SDK-REST-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# REST API Authentication

Ascend supports three authentication methods to accommodate different use cases: cookie-based sessions for web applications, AWS Cognito JWT for enterprise SSO, and API keys for server-to-server communication.

## Authentication Methods Overview

| Method | Use Case | Security Level |
|--------|----------|----------------|
| Cookie Sessions | Web applications, dashboards | Banking-grade (HttpOnly, Secure, SameSite) |
| AWS Cognito JWT | Enterprise SSO, mobile apps | Enterprise (RS256 signature validation) |
| API Keys | Server-to-server, SDKs, automation | High (SHA-256 hashing with salt) |

## 1. Cookie-Based Sessions

Recommended for web applications. Uses secure HttpOnly cookies with CSRF protection.

### Login

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "your-password"
  }' \
  -c cookies.txt
```

**Response:**

```json
{
  "user": {
    "id": 123,
    "email": "user@company.com",
    "name": "John Doe",
    "role": "admin",
    "organization_id": 1,
    "organization_name": "Acme Corp"
  },
  "mfa_required": false
}
```

### Using Session Cookie

```bash
# All subsequent requests use the cookie
curl https://pilot.owkai.app/api/v1/actions \
  -b cookies.txt
```

### CSRF Protection

For state-changing requests (POST, PUT, DELETE), include the CSRF token:

```bash
# Get CSRF token
CSRF_TOKEN=$(curl -s https://pilot.owkai.app/api/api/auth/csrf \
  -b cookies.txt | jq -r '.csrf_token')

# Use in request
curl -X POST https://pilot.owkai.app/api/v1/actions/submit \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -b cookies.txt \
  -d '{"action_type": "database_query", "target_resource": "users"}'
```

### MFA Flow

If MFA is enabled, the login response includes `mfa_required: true`:

```json
{
  "mfa_required": true,
  "mfa_session": "session_abc123",
  "mfa_type": "totp"
}
```

Complete MFA verification:

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/mfa/verify-totp \
  -H "Content-Type: application/json" \
  -d '{
    "mfa_session": "session_abc123",
    "totp_code": "123456"
  }' \
  -c cookies.txt
```

### Logout

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/logout \
  -b cookies.txt
```

This invalidates the session and revokes all tokens (including Cognito GlobalSignOut).

### Session Security Features

- **HttpOnly**: Cookies not accessible via JavaScript
- **Secure**: Only transmitted over HTTPS
- **SameSite=Strict**: Prevents CSRF attacks
- **Session Fixation Prevention**: New session ID on login
- **Concurrent Session Control**: Optional single-session enforcement

## 2. AWS Cognito JWT Authentication

For enterprise SSO integration with AWS Cognito user pools.

### Prerequisites

1. Configure your organization's Cognito user pool in Ascend
2. Obtain Cognito credentials from your identity provider

### Authentication Flow

```bash
# 1. Authenticate with Cognito (via AWS SDK or hosted UI)
# This returns an ID token and access token

# 2. Use the ID token with Ascend API
curl https://pilot.owkai.app/api/v1/actions \
  -H "Authorization: Bearer <cognito-id-token>"
```

### Token Validation

Ascend validates Cognito tokens using:

- RS256 signature verification against Cognito JWKS
- Token expiration check
- Issuer validation
- Audience validation
- Token revocation check

### Cognito Session Creation

For web apps using Cognito authentication:

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/cognito-session \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "<cognito-id-token>",
    "access_token": "<cognito-access-token>"
  }' \
  -c cookies.txt
```

### MFA with Cognito

Cognito MFA is validated server-side. The `auth_time` claim is checked to ensure MFA was completed within the session.

### Organization Mapping

Users are mapped to organizations by:
1. Email domain matching
2. Cognito user pool association
3. Organization ID in token claims

## 3. API Key Authentication

For server-to-server communication, SDKs, and automated workflows.

### Generate API Key

```bash
curl -X POST https://pilot.owkai.app/api/api/keys/generate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production SDK",
    "description": "API key for production environment",
    "permissions": ["agent_actions:read", "agent_actions:write"],
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

**Response:**

```json
{
  "key_id": "key_abc123",
  "api_key": "asc_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "name": "Production SDK",
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-12-31T23:59:59Z",
  "permissions": ["agent_actions:read", "agent_actions:write"]
}
```

> **Warning: Important**
> The `api_key` is only shown once at creation time. Store it securely - it cannot be retrieved later. Only a masked version (first/last 4 characters) is stored.


### Using API Keys

```bash
curl https://pilot.owkai.app/api/api/agent/sdk/agent-action \
  -H "X-API-Key: asc_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "database_query",
    "target_resource": "users",
    "agent_id": "agent-001"
  }'
```

### API Key Security

- **SHA-256 Hashing**: Keys are hashed with random salt before storage
- **Key Prefix**: `asc_live_` for production, `asc_test_` for sandbox
- **Rate Limiting**: Configurable per-key rate limits (default: 1000/hour)
- **Permissions**: Fine-grained permission control
- **Usage Logging**: All API key usage is logged for audit

### List API Keys

```bash
curl https://pilot.owkai.app/api/api/keys/list \
  -b cookies.txt
```

**Response:**

```json
{
  "keys": [
    {
      "key_id": "key_abc123",
      "name": "Production SDK",
      "key_prefix": "asc_live_xxxx",
      "key_suffix": "xxxx",
      "created_at": "2025-01-15T10:30:00Z",
      "last_used_at": "2025-01-20T15:45:00Z",
      "expires_at": "2025-12-31T23:59:59Z",
      "is_active": true,
      "usage_count": 1547
    }
  ]
}
```

### Revoke API Key

```bash
curl -X DELETE https://pilot.owkai.app/api/api/keys/key_abc123/revoke \
  -b cookies.txt
```

### API Key Permissions

| Permission | Description |
|------------|-------------|
| `agent_actions:read` | Read agent actions |
| `agent_actions:write` | Create/update agent actions |
| `policies:read` | Read policies |
| `policies:write` | Create/update policies |
| `users:read` | Read user data |
| `users:write` | Manage users |
| `audit:read` | Read audit logs |
| `compliance:export` | Export compliance reports |

## Brute Force Protection

Ascend implements aggressive brute force protection:

| Limit | Threshold | Window |
|-------|-----------|--------|
| IP-based | 5 failed attempts | 15 minutes |
| Email-based | 10 failed attempts | 15 minutes |
| Account lockout | Exponential backoff | Up to 24 hours |

After exceeding limits, requests return `429 Too Many Requests`.

## Token Refresh

### Cookie Session Refresh

Sessions are automatically refreshed. For explicit refresh:

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/refresh-token \
  -b cookies.txt \
  -c cookies.txt
```

### Cognito Token Refresh

Use the Cognito refresh token with AWS SDK or:

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<cognito-refresh-token>"
  }'
```

## Password Management

### Change Password

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/change-password \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "current_password": "old-password",
    "new_password": "new-secure-password"
  }'
```

### Forgot Password

```bash
# Request reset
curl -X POST https://pilot.owkai.app/api/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@company.com"}'

# Confirm reset (with code from email)
curl -X POST https://pilot.owkai.app/api/api/auth/confirm-reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "confirmation_code": "123456",
    "new_password": "new-secure-password"
  }'
```

## MFA Management

### Check MFA Status

```bash
curl https://pilot.owkai.app/api/api/auth/mfa-status \
  -b cookies.txt
```

### Setup TOTP MFA

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/mfa/setup-totp \
  -b cookies.txt
```

**Response:**

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/Ascend:user@company.com?secret=JBSWY3DPEHPK3PXP&issuer=Ascend",
  "backup_codes": ["12345678", "87654321", "..."]
}
```

### Verify TOTP Setup

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/mfa/verify-totp \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"totp_code": "123456"}'
```

### Disable MFA

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/mfa/disable \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"totp_code": "123456"}'
```

## Security Headers

All responses include security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Invalid or expired token",
  "error_code": "AUTH_TOKEN_INVALID"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions",
  "error_code": "AUTH_FORBIDDEN",
  "required_permission": "policies:write"
}
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 900
}
```

## Security Best Practices

1. **Web Applications**: Use cookie-based sessions with CSRF protection
2. **Mobile Apps**: Use Cognito authentication with secure token storage
3. **Server-to-Server**: Use API keys with minimal required permissions
4. **Enable MFA**: Require MFA for admin accounts
5. **Rotate API Keys**: Regularly rotate API keys (90-day maximum recommended)
6. **Monitor Usage**: Review API key usage logs for anomalies
7. **Use HTTPS**: All API calls must use HTTPS

## Next Steps

- [API Endpoints Reference](/api/overview)
- [Webhooks Configuration](/sdk/rest/webhooks)
- [Enterprise SSO Setup](/enterprise/sso)
