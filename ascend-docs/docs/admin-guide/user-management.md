---
sidebar_position: 2
title: User Management
description: Invite, manage, and control user access
---

# User Management

Manage users across your organization with AWS Cognito integration, role-based access control, and complete audit trails.

## Overview

Enterprise user management provides secure onboarding, role management, and access control with Cognito SSO integration.

**Source**: `ow-ai-backend/routes/organization_admin_routes.py` (SEC-046)

**Compliance**: SOC 2 CC6.1, NIST AC-2, PCI-DSS 8.3

## User Roles

### Available Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | Full system access | All operations |
| `manager` | Team management | View all, approve actions |
| `user` | Standard access | Submit actions, view own data |
| `viewer` | Read-only access | View dashboards only |

### Role Hierarchy

```
admin (Level 4)
  └── manager (Level 3)
        └── user (Level 2)
              └── viewer (Level 1)
```

## Inviting Users

### Via API

```bash
curl -X POST https://pilot.owkai.app/api/organizations/users \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@company.com",
    "role": "user",
    "first_name": "John",
    "last_name": "Smith",
    "is_org_admin": false
  }'
```

### Invitation Flow

1. Admin submits invitation request
2. System validates subscription user limit
3. Cognito user created with temp password
4. Database user record created
5. Invitation email sent (if SES configured)
6. User receives credentials
7. User logs in and sets permanent password

### Request Validation

| Field | Validation | Limit |
|-------|------------|-------|
| `email` | EmailStr format | Required |
| `role` | Whitelist: user, admin, manager, viewer | Required |
| `first_name` | Sanitized, no HTML | 100 chars |
| `last_name` | Sanitized, no HTML | 100 chars |
| `is_org_admin` | Boolean | Only with admin role |

## Listing Users

### Get All Organization Users

```bash
curl https://pilot.owkai.app/api/organizations/users \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "users": [
    {
      "id": 15,
      "email": "admin@company.com",
      "first_name": "Admin",
      "last_name": "User",
      "department": "IT",
      "role": "admin",
      "access_level": "Level 4 - Full Access",
      "status": "Active",
      "mfa_enabled": true,
      "login_attempts": 0,
      "last_login": "2025-01-15T10:30:00Z",
      "created_at": "2025-01-01T00:00:00Z",
      "risk_score": 15,
      "permissions": ["view", "create", "update", "delete", "approve"],
      "compliance_status": "Compliant"
    }
  ],
  "total_count": 12,
  "stats": {
    "active_users": 10,
    "mfa_enabled_count": 8,
    "high_risk_users": 1
  }
}
```

## Updating User Roles

### Change User Role

```bash
curl -X PATCH https://pilot.owkai.app/api/organizations/users/15/role \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "manager",
    "is_org_admin": false
  }'
```

### Role Change Effects

When role changes:
1. Cognito custom attributes updated
2. Database record updated
3. **All user tokens revoked** (forces re-login)
4. Audit log entry created

## Removing Users

### Remove User from Organization

```bash
curl -X DELETE https://pilot.owkai.app/api/organizations/users/15 \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

### Removal Process

1. Validation (cannot remove self)
2. Cognito user disabled
3. All tokens revoked
4. Database: `cognito_user_id` cleared, role set to `disabled`
5. Audit log entry created

**Note**: This is a soft delete. User data retained for compliance.

## Access Levels

### Enterprise Access Levels

| Level | Name | Description |
|-------|------|-------------|
| Level 1 | Basic | Read-only dashboards |
| Level 2 | Standard | Submit actions, view data |
| Level 3 | Manager | Approve actions, manage team |
| Level 4 | Full Access | All administrative functions |

### Risk Score Calculation

User risk score based on:
- Login attempts (failed attempts increase risk)
- Access level (higher access = higher risk)
- MFA status (MFA disabled increases risk)

```
Risk Score = (login_attempts × 5) + access_level_factor - (mfa_bonus)
```

## Subscription Limits

### Enforced User Limits

| Tier | Limit | Enforcement |
|------|-------|-------------|
| Trial | 5 | Hard limit |
| Startup | 10 | Hard limit |
| Business | 50 | Hard limit |
| Enterprise | 1000 | Soft limit |

When limit reached:
- New invitations blocked
- Error message with upgrade suggestion
- Existing users unaffected

## Audit Trail

All user management actions logged:

| Event | Details Captured |
|-------|------------------|
| `user_invited` | Email, role, inviter |
| `user_removed` | Email, remover |
| `user_role_updated` | Old role, new role, updater |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/organizations/users` | GET | List all users |
| `/api/organizations/users` | POST | Invite user |
| `/api/organizations/users/{id}` | DELETE | Remove user |
| `/api/organizations/users/{id}/role` | PATCH | Update role |
| `/api/organizations/{org_id}/users` | GET | List users (explicit org) |

**Source**: `ow-ai-backend/routes/organization_admin_routes.py`

## Best Practices

1. **Principle of least privilege**: Assign minimum required role
2. **Enable MFA**: Require MFA for all admin users
3. **Regular audits**: Review user access quarterly
4. **Prompt removal**: Remove users immediately on departure
5. **Document assignments**: Maintain role assignment records

## Troubleshooting

### User cannot log in after invitation

**Cause**: Cognito user may not have been created (SEC-034).

**Solution**: Check Cognito user pool directly; re-invite if needed.

### Cannot change own admin status

**Cause**: Self-demotion prevention security feature.

**Solution**: Another admin must change your role.

### Invitation fails with user exists

**Cause**: Email already registered in organization.

**Solution**: Check existing users; consider role update instead.

---

*Source: [organization_admin_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/organization_admin_routes.py), [enterprise_user_management_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/enterprise_user_management_routes.py)*
