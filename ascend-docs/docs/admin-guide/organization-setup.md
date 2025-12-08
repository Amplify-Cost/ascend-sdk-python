---
sidebar_position: 1
title: Organization Setup
description: Configure your organization settings and subscription
---

# Organization Setup

Configure your organization's settings, subscription tier, and multi-tenant isolation for enterprise AI governance.

## Overview

Each organization in Ascend operates in complete isolation with dedicated configuration, user management, and data separation.

**Source**: `ow-ai-backend/routes/organization_admin_routes.py`

**Compliance**: SOC 2 CC6.1, NIST AC-2, PCI-DSS 8.3

## Subscription Tiers

### Available Tiers

| Tier | User Limit | Features |
|------|------------|----------|
| **Trial** | 5 users | Basic features, 14-day trial |
| **Startup** | 10 users | Core governance features |
| **Business** | 50 users | Advanced analytics, API access |
| **Enterprise** | 1000 users | Full features, custom SLAs |

### Viewing Subscription Info

```bash
curl https://pilot.owkai.app/api/organizations/subscription-info \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "organization_id": 4,
  "organization_name": "Acme Corp",
  "subscription_tier": "business",
  "subscription_status": "active",
  "user_limit": 50,
  "current_users": 12,
  "available_slots": 38,
  "usage_percentage": 24.0
}
```

## Organization Settings

### Get Current Settings

```bash
curl https://pilot.owkai.app/api/organizations/settings \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "organization_id": 4,
  "organization_name": "Acme Corp",
  "mfa": {
    "configuration": "OPTIONAL",
    "enforced": false
  },
  "session": {
    "timeout_minutes": 60,
    "max_concurrent_sessions": 5
  },
  "password_policy": {
    "min_length": 12,
    "require_uppercase": true,
    "require_lowercase": true,
    "require_numbers": true,
    "require_special": true,
    "max_age_days": 90
  },
  "ip_restrictions": {
    "enabled": false,
    "allowed_ranges": []
  }
}
```

## Multi-Tenant Isolation

### Data Isolation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Request Flow                          │
├─────────────────────────────────────────────────────────────┤
│  1. JWT Token → Extract user_id                             │
│  2. User → Lookup organization_id                           │
│  3. Query → Filter by organization_id                       │
│  4. Response → Only tenant-specific data                    │
└─────────────────────────────────────────────────────────────┘
```

### Isolated Tables

All data tables enforce organization isolation:

| Table | Column | Status |
|-------|--------|--------|
| `alerts` | `organization_id` | Isolated |
| `agent_actions` | `organization_id` | Isolated |
| `smart_rules` | `organization_id` | Isolated |
| `workflows` | `organization_id` | Isolated |
| `governance_policies` | `organization_id` | Isolated |
| `api_keys` | `organization_id` | Isolated |
| `audit_logs` | `organization_id` | Isolated |
| `registered_agents` | `organization_id` | Isolated |

## AWS Cognito Integration

Each organization can have its own Cognito User Pool:

### Per-Organization Pool

| Field | Description |
|-------|-------------|
| `cognito_user_pool_id` | Dedicated user pool ID |
| `cognito_app_client_id` | App client for authentication |
| `cognito_mfa_configuration` | MFA enforcement level |

### Pool Configuration Options

| Setting | Options | Default |
|---------|---------|---------|
| MFA Configuration | `OFF`, `OPTIONAL`, `ON` | `OPTIONAL` |
| Password Policy | Configurable | 12 chars, mixed case, numbers, special |
| Token Validity | Access: 60min, Refresh: 30 days | Standard |

## Organization Administration

### Required Permissions

| Action | Required Role |
|--------|---------------|
| View subscription | `admin` |
| Manage users | `admin` |
| Update settings | `admin` |
| View audit logs | `admin`, `viewer` |

### Admin Capabilities

Administrators can:
- Invite new users to the organization
- Assign and modify user roles
- View subscription usage
- Configure security settings
- Access audit logs

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/organizations/settings` | GET | Get org settings |
| `/api/organizations/subscription-info` | GET | Get subscription |
| `/api/organizations/{id}/users` | GET | List users |
| `/api/organizations/{id}/users` | POST | Invite user |
| `/api/organizations/users` | GET | List users (auto org) |

**Source**: `ow-ai-backend/routes/organization_admin_routes.py`

## Best Practices

1. **Monitor usage**: Track user count against tier limits
2. **Plan upgrades**: Upgrade tier before hitting limits
3. **Enable MFA**: Enforce MFA for all admin users
4. **Review settings**: Audit security settings quarterly
5. **Document access**: Maintain records of admin assignments

## Troubleshooting

### Cannot invite users

**Cause**: User limit reached for subscription tier.

**Solution**: Upgrade subscription or remove inactive users.

### Settings not saving

**Cause**: Insufficient admin permissions.

**Solution**: Verify user has `admin` role with `is_org_admin: true`.

### Cognito pool mismatch

**Cause**: Organization using default pool instead of dedicated.

**Solution**: Contact support to configure per-organization pool.

---

*Source: [organization_admin_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/organization_admin_routes.py)*
