---
sidebar_position: 6
title: MFA Setup
description: Configure multi-factor authentication for enhanced security
---

# MFA Setup

Configure multi-factor authentication (MFA) using AWS Cognito TOTP for enhanced security across your organization.

## Overview

MFA adds an additional layer of security by requiring users to provide a time-based one-time password (TOTP) in addition to their password.

**Source**: AWS Cognito User Pool configuration

**Compliance**: SOC 2 CC6.1, NIST IA-2, PCI-DSS 8.3.1, HIPAA 164.312(d)

## MFA Configuration Levels

### Organization-Level MFA

| Setting | Description |
|---------|-------------|
| `OFF` | MFA disabled |
| `OPTIONAL` | User can enable MFA |
| `ON` | MFA required for all users |

### Current Configuration

Check your organization's MFA setting:

```bash
curl https://pilot.owkai.app/api/organizations/settings \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "mfa": {
    "configuration": "OPTIONAL",
    "enforced": false
  }
}
```

## User MFA Enrollment

### Enrollment Flow

1. User logs in with username/password
2. System detects MFA not configured
3. User presented with TOTP setup screen
4. User scans QR code with authenticator app
5. User enters verification code
6. MFA successfully configured

### Supported Authenticator Apps

| App | Platform | Recommended |
|-----|----------|-------------|
| Google Authenticator | iOS, Android | Yes |
| Microsoft Authenticator | iOS, Android | Yes |
| Authy | iOS, Android, Desktop | Yes |
| 1Password | All platforms | Yes |

## Admin MFA Management

### Requiring MFA for Admin Users

For admin users, MFA should be enforced:

```json
{
  "role": "admin",
  "is_org_admin": true,
  "mfa_required": true
}
```

### Per-User MFA Status

View user MFA status in user list:

```json
{
  "id": 15,
  "email": "admin@company.com",
  "mfa_enabled": true,
  "compliance_status": "Compliant"
}
```

## MFA Triggers

### Risk-Based MFA Requirement

MFA can be triggered based on agent risk scores:

| Setting | Default | Description |
|---------|---------|-------------|
| `requires_mfa_above` | 70 | Trigger MFA for high-risk actions |

Actions with risk score above threshold require MFA confirmation.

## Cognito MFA Configuration

### Pool-Level Settings

| Setting | Value | Description |
|---------|-------|-------------|
| MFA Type | TOTP | Time-based one-time password |
| Recovery | Enabled | Recovery codes available |
| Remember Device | 30 days | Skip MFA on trusted devices |

### App Client Settings

| Setting | Description |
|---------|-------------|
| `ExplicitAuthFlows` | USER_SRP_AUTH, ALLOW_REFRESH_TOKEN_AUTH |
| `PreventUserExistenceErrors` | ENABLED (security) |

## Password Policy

MFA works alongside strong password requirements:

| Requirement | Setting |
|-------------|---------|
| Minimum Length | 12 characters |
| Uppercase | Required |
| Lowercase | Required |
| Numbers | Required |
| Special Characters | Required |
| Password Age | 90 days maximum |

## Session Settings

### Session Security with MFA

| Setting | Value | Description |
|---------|-------|-------------|
| `timeout_minutes` | 60 | Session timeout |
| `max_concurrent_sessions` | 5 | Max active sessions |

### Token Configuration

| Token Type | Validity |
|------------|----------|
| Access Token | 60 minutes |
| ID Token | 60 minutes |
| Refresh Token | 30 days |

## Enterprise MFA Features

### High-Risk Action Re-Authentication

For actions exceeding `requires_mfa_above`:

1. User attempts high-risk action
2. System prompts for MFA code
3. User enters TOTP code
4. Action proceeds if verified

### Admin Override Logging

All MFA bypasses are logged:

| Event | Details |
|-------|---------|
| `mfa_bypass` | Admin user, reason, timestamp |
| `mfa_reset` | Target user, admin, timestamp |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/organizations/settings` | GET | Get MFA config |
| `/api/auth/mfa/setup` | POST | Initiate MFA setup |
| `/api/auth/mfa/verify` | POST | Verify MFA code |
| `/api/auth/mfa/disable` | POST | Disable user MFA (admin) |

## Known Issues

### SEC-035: MFA Setup Missing QR Code

**Status**: Pending

**Issue**: MFA setup screen may not display QR code.

**Workaround**: Use manual setup key if QR code unavailable.

### SEC-037: MFA Cannot Be Disabled

**Status**: Under investigation

**Issue**: MFA prompt may appear even after disabling.

**Workaround**: Contact support for pool-level configuration.

## Best Practices

1. **Enforce for admins**: Require MFA for all admin users
2. **Gradual rollout**: Start with OPTIONAL, move to ON
3. **Backup codes**: Ensure users save recovery codes
4. **Recovery process**: Document MFA recovery procedure
5. **Regular audits**: Review MFA adoption rates
6. **Monitor failures**: Alert on repeated MFA failures

## Troubleshooting

### User cannot complete MFA setup

**Check**:
- Authenticator app time sync (should match server time)
- QR code scanning (try manual key entry)
- Network connectivity

### MFA code rejected

**Causes**:
- Clock drift on user device
- Code expired (30-second window)
- Wrong account selected in authenticator

**Solution**: Ensure device time is synced; codes valid for 30 seconds.

### Lost authenticator access

**Process**:
1. User contacts admin
2. Admin verifies identity
3. Admin resets MFA via Cognito console
4. User re-enrolls

### MFA prompt on every login

**Cause**: "Remember Device" not working.

**Solution**: Check browser cookies; ensure device is trusted.

---

*Source: AWS Cognito User Pool configuration, organization_admin_routes.py*
