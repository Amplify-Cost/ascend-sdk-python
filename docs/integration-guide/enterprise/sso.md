---
title: SSO Configuration
sidebar_position: 1
---

# SSO Configuration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-ENT-007 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Ascend uses AWS Cognito as the identity provider, enabling enterprise-grade Single Sign-On (SSO) with support for SAML 2.0, OIDC, and social identity providers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enterprise SSO Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Your IdP   │───▶│ AWS Cognito │───▶│   Ascend Platform   │ │
│  │ (Okta/Azure)│    │  User Pool  │    │   (Backend API)     │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                                 │
│  • SAML 2.0 Federation                                         │
│  • OIDC Integration                                            │
│  • MFA Enforcement                                             │
│  • RS256 Token Validation                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Multi-Tenant Cognito Architecture

Each organization can have a dedicated Cognito user pool for complete tenant isolation:

| Configuration | Description |
|---------------|-------------|
| Per-Organization Pool | Dedicated Cognito pool per enterprise customer |
| Email Domain Mapping | Automatic routing based on email domain |
| Pool-Level MFA | MFA policies per organization |
| Custom Branding | Organization-specific login UI |

## Supported Identity Providers

### Through AWS Cognito Federation

| Provider | Protocol | Status |
|----------|----------|--------|
| Okta | SAML 2.0, OIDC | Supported |
| Azure AD | SAML 2.0, OIDC | Supported |
| OneLogin | SAML 2.0, OIDC | Supported |
| Google Workspace | OIDC | Supported |
| Auth0 | SAML 2.0, OIDC | Supported |
| PingIdentity | SAML 2.0 | Supported |
| ADFS | SAML 2.0 | Supported |
| Custom SAML IdP | SAML 2.0 | Supported |

### Social Identity Providers

| Provider | Status |
|----------|--------|
| Google | Supported |
| Microsoft | Supported |
| Amazon | Supported |
| Apple | Supported |

## Configuration

### Step 1: Get Cognito Pool Configuration

Retrieve your organization's Cognito configuration:

```bash
# By organization slug
curl https://pilot.owkai.app/api/cognito/pool-config/by-slug/acme-corp

# By email domain
curl https://pilot.owkai.app/api/cognito/pool-config/by-email-domain/user@acmecorp.com

# By organization ID
curl https://pilot.owkai.app/api/cognito/pool-config/by-id/123
```

**Response:**

```json
{
  "organization_id": 123,
  "organization_name": "Acme Corp",
  "cognito_user_pool_id": "us-east-2_AbCdEfGhI",
  "cognito_client_id": "1abc2def3ghi4jkl5mno6pqr",
  "cognito_region": "us-east-2",
  "mfa_required": true,
  "hosted_ui_domain": "acme-corp.auth.us-east-2.amazoncognito.com"
}
```

### Step 2: Configure Cognito User Pool Federation

#### SAML Configuration in AWS Console

1. Navigate to AWS Cognito → User Pools → Your Pool
2. Go to **Federation** → **Identity providers** → **Add SAML**
3. Configure your IdP:

| Cognito Setting | Value |
|-----------------|-------|
| Provider name | `OktaSSO` or `AzureAD` |
| Metadata document | Upload from your IdP |
| Attribute mapping | See below |

#### SAML Attribute Mapping

| Cognito Attribute | SAML Claim |
|-------------------|------------|
| `email` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` |
| `given_name` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname` |
| `family_name` | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname` |
| `custom:role` | `http://schemas.company.com/claims/role` |

### Step 3: Configure Hosted UI (Optional)

For organizations using Cognito Hosted UI:

```bash
# SSO Login URL
https://acme-corp.auth.us-east-2.amazoncognito.com/login?
  client_id=1abc2def3ghi4jkl5mno6pqr&
  response_type=code&
  scope=openid+email+profile&
  redirect_uri=https://pilot.owkai.app/auth/callback
```

### Step 4: Integrate with Ascend

#### Using Cognito Tokens Directly

```bash
# After Cognito authentication, use ID token
curl https://pilot.owkai.app/api/v1/actions \
  -H "Authorization: Bearer <cognito-id-token>"
```

#### Creating Ascend Session from Cognito

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/cognito-session \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "<cognito-id-token>",
    "access_token": "<cognito-access-token>"
  }' \
  -c cookies.txt
```

## Token Validation

Ascend validates Cognito tokens with enterprise-grade security:

### RS256 Signature Validation

```python
# Backend validation (simplified)
def validate_cognito_token(token):
    # 1. Fetch JWKS from Cognito
    jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

    # 2. Validate RS256 signature
    header = jwt.get_unverified_header(token)
    key = get_key_from_jwks(header['kid'])

    # 3. Verify claims
    payload = jwt.decode(
        token,
        key,
        algorithms=['RS256'],
        audience=client_id,
        issuer=f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    )

    return payload
```

### Validation Checks

| Check | Description |
|-------|-------------|
| Signature | RS256 against Cognito JWKS |
| Expiration | `exp` claim not passed |
| Issuer | Matches Cognito pool URL |
| Audience | Matches app client ID |
| Token Use | `id_token` for identity |
| Revocation | Not in revocation blacklist |

## MFA Configuration

### Cognito MFA Settings

Configure MFA at the user pool level:

| Setting | Options |
|---------|---------|
| MFA | Off / Optional / Required |
| Methods | SMS, TOTP (Authenticator app) |
| Remember Device | Yes / No |

### MFA in Ascend

Ascend validates MFA completion via the `auth_time` claim:

```json
{
  "auth_time": 1640995200,
  "cognito:username": "user@company.com",
  "custom:mfa_enabled": "true"
}
```

### Setup TOTP MFA

```bash
# Setup MFA for user
curl -X POST https://pilot.owkai.app/api/api/auth/mfa/setup-totp \
  -b cookies.txt

# Response includes QR code for authenticator app
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "otpauth://totp/Ascend:user@company.com?..."
}
```

## Provider-Specific Configuration

### Okta SAML Federation

1. **In Okta Admin Console:**
   - Create new SAML 2.0 Application
   - Single Sign On URL: `https://acme-corp.auth.us-east-2.amazoncognito.com/saml2/idpresponse`
   - Audience URI: `urn:amazon:cognito:sp:us-east-2_AbCdEfGhI`
   - Attribute Statements:
     - `email` → `user.email`
     - `firstName` → `user.firstName`
     - `lastName` → `user.lastName`

2. **In AWS Cognito:**
   - Add SAML identity provider with Okta metadata
   - Map attributes as shown above

### Azure AD Federation

1. **In Azure Portal:**
   - Enterprise Applications → New Application → Non-gallery
   - Single sign-on → SAML
   - Basic SAML Configuration:
     - Identifier: `urn:amazon:cognito:sp:us-east-2_AbCdEfGhI`
     - Reply URL: `https://acme-corp.auth.us-east-2.amazoncognito.com/saml2/idpresponse`

2. **In AWS Cognito:**
   - Add SAML provider with Azure Federation Metadata XML

### Google Workspace

1. **In Google Admin Console:**
   - Apps → Web and mobile apps → Add app → Add custom SAML app
   - ACS URL: `https://acme-corp.auth.us-east-2.amazoncognito.com/saml2/idpresponse`
   - Entity ID: `urn:amazon:cognito:sp:us-east-2_AbCdEfGhI`

## User Auto-Linking

Ascend automatically links Cognito users to existing accounts:

```python
# Auto-link flow (SEC-014)
user = db.query(User).filter(User.cognito_user_id == cognito_id).first()

if not user:
    # Check by email for existing users
    user = db.query(User).filter(
        User.email == email,
        User.organization_id == org_id
    ).first()

    if user:
        # Auto-link existing user to Cognito
        user.cognito_user_id = cognito_id
```

This handles:
- Cognito user recreation after deletion
- User pool migrations
- Identity recovery scenarios

## Role Mapping

Map Cognito groups or custom attributes to Ascend roles:

```json
{
  "role_mapping": {
    "Administrators": "admin",
    "SecurityTeam": "security_admin",
    "Developers": "developer",
    "Viewers": "viewer"
  },
  "default_role": "viewer"
}
```

## Security Best Practices

### Token Security

- Store tokens securely (HttpOnly cookies or secure storage)
- Validate token signature on every request
- Check token expiration before use
- Use short-lived access tokens (1 hour recommended)

### Session Security

- Enable MFA for all admin accounts
- Set appropriate session timeouts
- Implement concurrent session control
- Log all authentication events

### Cognito Configuration

- Enable advanced security features
- Configure password policies (12+ chars, complexity)
- Enable compromised credential detection
- Set up user activity logging

## API Endpoints

### SSO Provider Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sso/providers` | GET | List configured SSO providers |
| `/sso/login/{provider}` | GET | Initiate SSO login flow |
| `/sso/callback/{provider}` | GET | Handle SSO callback |
| `/sso/logout` | POST | Logout with SSO provider |
| `/sso/user-profile` | GET | Get SSO user profile |

### Cognito Pool Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cognito/pool-config/by-slug/{slug}` | GET | Get pool by org slug |
| `/cognito/pool-config/by-email-domain/{email}` | GET | Get pool by email domain |
| `/cognito/pool-status/{slug}` | GET | Get pool status |
| `/cognito/health` | GET | Health check |

## Troubleshooting

### Invalid Token Errors

1. **Signature validation failed**
   - Verify JWKS URL is accessible
   - Check token hasn't been tampered with
   - Ensure correct user pool ID

2. **Token expired**
   - Refresh token using Cognito SDK
   - Check client-side clock synchronization

3. **Invalid issuer/audience**
   - Verify user pool ID and region
   - Check app client ID

### User Not Found

1. **New SSO user**
   - Enable JIT (Just-In-Time) provisioning
   - Check attribute mapping includes email

2. **Existing user not linked**
   - Verify email matches exactly
   - Check organization ID is correct

### MFA Issues

1. **MFA not detected**
   - Check `auth_time` claim is recent
   - Verify Cognito MFA settings

2. **TOTP setup failed**
   - Ensure user pool allows TOTP
   - Check device time synchronization

## Next Steps

- [SIEM Integration](/enterprise/siem) - Forward security events
- [Multi-Tenancy](/core-concepts/multi-tenancy) - Organization isolation
- [API Authentication](/sdk/rest/authentication) - Detailed auth guide
