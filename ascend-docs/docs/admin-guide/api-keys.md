---
sidebar_position: 3
title: API Keys
description: Generate and manage API keys for SDK authentication
---

# API Keys

Generate and manage cryptographically secure API keys for authenticating SDK requests and external integrations.

## Overview

API keys provide secure, auditable authentication for programmatic access to the Ascend platform without requiring user credentials.

**Source**: `ow-ai-backend/routes/api_key_routes.py` (SEC-018)

**Compliance**: SOX, GDPR, HIPAA, PCI-DSS 8.3.1, SOC 2 CC6.1

## Security Features

### Cryptographic Security

| Feature | Implementation |
|---------|----------------|
| **Key Generation** | 256-bit entropy via `secrets.token_urlsafe(32)` |
| **Storage** | SHA-256 hash with random salt |
| **Display** | Full key shown ONCE at creation |
| **Masking** | Only prefix visible after creation |

### Key Format

```
owkai_admin_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8
└────┬────┘└─┬─┘└──────────────┬──────────────────┘
   prefix  role        random token (43 chars)
```

### Key Prefix by Role

| Role | Prefix Example |
|------|----------------|
| `admin` | `owkai_admin_...` |
| `user` | `owkai_user_...` |
| `manager` | `owkai_manager_...` |

## Generating API Keys

### Generate New Key

```bash
curl -X POST https://pilot.owkai.app/api/keys/generate \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production SDK Key",
    "description": "Used by customer service agent",
    "expires_in_days": 365,
    "permissions": [
      {"category": "agent_actions", "actions": ["create", "read"]},
      {"category": "alerts", "actions": ["read"]}
    ],
    "rate_limit": {
      "max_requests": 5000,
      "window_seconds": 3600
    }
  }'
```

**Response:**

```json
{
  "success": true,
  "api_key": "owkai_admin_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8",
  "key_id": 42,
  "key_prefix": "owkai_admin_a1b2",
  "name": "Production SDK Key",
  "expires_at": "2026-01-15T10:00:00Z",
  "created_at": "2025-01-15T10:00:00Z",
  "warning": "⚠️ Save this key now - you will NOT see it again!"
}
```

### Permission Shorthand (SEC-094)

You can use string shorthand for permissions:

```json
{
  "name": "Read-Only Key",
  "permissions": ["agent:read", "action:read", "alert:read"]
}
```

Converts to:
```json
{
  "permissions": [
    {"category": "agent", "actions": ["read"]},
    {"category": "action", "actions": ["read"]},
    {"category": "alert", "actions": ["read"]}
  ]
}
```

## Listing API Keys

### Get All Keys

```bash
curl "https://pilot.owkai.app/api/keys/list?include_revoked=false&page=1&page_size=20" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "success": true,
  "keys": [
    {
      "id": 42,
      "name": "Production SDK Key",
      "description": "Used by customer service agent",
      "key_prefix": "owkai_admin_a1b2",
      "is_active": true,
      "expires_at": "2026-01-15T10:00:00Z",
      "last_used_at": "2025-01-15T14:30:00Z",
      "usage_count": 1547,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total_count": 3,
  "page": 1,
  "page_size": 20
}
```

## Revoking API Keys

### Revoke a Key

```bash
curl -X DELETE "https://pilot.owkai.app/api/keys/42/revoke?reason=Replaced%20with%20new%20key" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "success": true,
  "message": "API key revoked successfully",
  "key_id": 42,
  "revoked_at": "2025-01-15T16:00:00Z"
}
```

### Revocation Details

| Field | Description |
|-------|-------------|
| `revoked_at` | Timestamp of revocation |
| `revoked_by` | User ID who revoked |
| `revoked_reason` | Audit trail reason |

## Usage Statistics

### Get Key Usage

```bash
curl "https://pilot.owkai.app/api/keys/42/usage?limit=100" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "success": true,
  "key_id": 42,
  "key_prefix": "owkai_admin_a1b2",
  "statistics": {
    "total_requests": 1547,
    "recent_requests": 100,
    "success_rate": 98.5,
    "last_used_at": "2025-01-15T14:30:00Z"
  },
  "recent_activity": [
    {
      "timestamp": "2025-01-15T14:30:00Z",
      "endpoint": "/api/v1/actions",
      "method": "POST",
      "status": 200,
      "ip_address": "192.168.1.100",
      "response_time_ms": 125
    }
  ]
}
```

## Rate Limiting

### Default Limits

| Setting | Default | Max |
|---------|---------|-----|
| `max_requests` | 1000 | 100,000 |
| `window_seconds` | 3600 (1 hour) | 86,400 (24 hours) |

### Rate Limit Algorithm

Sliding window rate limiting:
1. Request arrives
2. Check current window count
3. If under limit: increment and allow
4. If over limit: return 429 with `Retry-After` header

### Custom Rate Limits

Premium keys can have custom limits:

```json
{
  "rate_limit": {
    "max_requests": 10000,
    "window_seconds": 3600
  }
}
```

## Permissions

### Permission Categories

| Category | Actions |
|----------|---------|
| `agent_actions` | `create`, `read`, `update`, `delete` |
| `alerts` | `read`, `acknowledge`, `escalate` |
| `smart_rules` | `create`, `read`, `update`, `delete` |
| `analytics` | `read`, `export` |
| `audit` | `read`, `export` |

### Granular Resource Filters

```json
{
  "permissions": [
    {
      "category": "agent_actions",
      "actions": ["create"],
      "resource_filter": {
        "agent_id": "specific-agent",
        "risk_level": "low"
      }
    }
  ]
}
```

## Database Schema

### ApiKey Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | Owner user |
| `organization_id` | Integer | Multi-tenant isolation |
| `key_hash` | String(64) | SHA-256 hash |
| `key_prefix` | String(20) | Display prefix |
| `salt` | String(32) | Random salt |
| `name` | String(255) | User-friendly name |
| `is_active` | Boolean | Active status |
| `expires_at` | DateTime | Expiration (null = never) |
| `usage_count` | BigInteger | Total requests |
| `last_used_at` | DateTime | Last activity |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/keys/generate` | POST | Generate new key |
| `/api/keys/list` | GET | List all keys |
| `/api/keys/{id}/revoke` | DELETE | Revoke key |
| `/api/keys/{id}/usage` | GET | Get usage stats |

**Source**: `ow-ai-backend/routes/api_key_routes.py`

## Best Practices

1. **Rotate regularly**: Replace keys every 90 days
2. **Use minimal permissions**: Only grant required actions
3. **Set expiration**: Avoid never-expiring keys
4. **Monitor usage**: Review usage statistics weekly
5. **Revoke promptly**: Revoke compromised keys immediately
6. **Document purpose**: Use descriptive names

## Troubleshooting

### Key not working

**Check**:
- Is key active? (`is_active: true`)
- Is key expired? (check `expires_at`)
- Is key revoked? (check `revoked_at`)
- Rate limit exceeded? (check usage stats)

### 429 Too Many Requests

**Cause**: Rate limit exceeded.

**Solution**: Wait for `Retry-After` header duration or request higher limits.

### Authentication required error

**Solution**: Use `Authorization: Bearer YOUR_API_KEY` header format.

---

*Source: [api_key_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/api_key_routes.py), [models_api_keys.py](https://github.com/owkai/ow-ai-backend/blob/main/models_api_keys.py)*
