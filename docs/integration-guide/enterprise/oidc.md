# OIDC Configuration

Configure OpenID Connect (OIDC) authentication through AWS Cognito for enterprise single sign-on.

## Overview

Ascend supports OIDC authentication via AWS Cognito, which can federate with external OIDC providers.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Your OIDC  │───▶│ AWS Cognito │───▶│   Ascend    │
│  Provider   │    │  User Pool  │    │  Platform   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Supported OIDC Providers

| Provider | Status |
|----------|--------|
| Auth0 | Supported |
| Okta | Supported |
| Azure AD | Supported |
| Google | Supported |
| OneLogin | Supported |
| PingIdentity | Supported |
| Custom OIDC | Supported |

## Configuration Steps

### 1. Configure OIDC in AWS Cognito

In your Cognito User Pool:

1. Navigate to **Federation** → **Identity providers** → **Add provider**
2. Select **OpenID Connect**
3. Configure:

| Setting | Value |
|---------|-------|
| Provider name | `YourProvider` |
| Client ID | Your OIDC client ID |
| Client secret | Your OIDC client secret |
| Authorize scope | `openid email profile` |
| Issuer URL | `https://your-provider.com` |

### 2. Attribute Mapping

Map OIDC claims to Cognito attributes:

| OIDC Claim | Cognito Attribute |
|------------|-------------------|
| `sub` | `username` |
| `email` | `email` |
| `given_name` | `given_name` |
| `family_name` | `family_name` |
| `groups` | `custom:groups` |

### 3. Configure App Client

Enable the OIDC provider in your Cognito app client:

1. Navigate to **App integration** → **App client settings**
2. Enable your OIDC identity provider
3. Configure callback URLs:
   - `https://pilot.owkai.app/auth/callback`
   - `https://pilot.owkai.app/api/api/auth/callback`

## OIDC Flow

### Authorization Code Flow

```
1. User clicks "Login with [Provider]"
2. Redirect to Cognito Hosted UI
3. Cognito redirects to OIDC provider
4. User authenticates with provider
5. Provider redirects back to Cognito
6. Cognito issues tokens
7. Ascend validates tokens and creates session
```

### Token Exchange

```bash
# Exchange authorization code for tokens
curl -X POST https://acme-corp.auth.us-east-2.amazoncognito.com/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=your-client-id" \
  -d "code=authorization-code" \
  -d "redirect_uri=https://pilot.owkai.app/auth/callback"
```

### Create Ascend Session

```bash
curl -X POST https://pilot.owkai.app/api/api/auth/cognito-session \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "eyJhbGciOiJSUzI1NiIs...",
    "access_token": "eyJhbGciOiJSUzI1NiIs..."
  }' \
  -c cookies.txt
```

## Provider-Specific Configuration

### Auth0

1. Create Auth0 Application (Regular Web Application)
2. Configure:
   - Allowed Callback URLs: Cognito callback URL
   - Allowed Logout URLs: Cognito logout URL
3. Note: Client ID, Client Secret, Domain

Cognito OIDC Settings:
```
Issuer URL: https://your-tenant.auth0.com/
Authorize scope: openid email profile
```

### Okta

1. Create Okta Application (Web Application)
2. Configure Sign-in redirect URI: Cognito callback URL
3. Note: Client ID, Client Secret, Okta Domain

Cognito OIDC Settings:
```
Issuer URL: https://your-org.okta.com
Authorize scope: openid email profile groups
```

### Azure AD

1. Register Application in Azure AD
2. Add redirect URI: Cognito callback URL
3. Create client secret
4. Configure API permissions: `openid`, `email`, `profile`

Cognito OIDC Settings:
```
Issuer URL: https://login.microsoftonline.com/{tenant-id}/v2.0
Authorize scope: openid email profile
```

## Token Claims

### Required Claims

| Claim | Description |
|-------|-------------|
| `sub` | Subject identifier (user ID) |
| `email` | User email address |
| `email_verified` | Email verification status |

### Optional Claims

| Claim | Description |
|-------|-------------|
| `given_name` | First name |
| `family_name` | Last name |
| `groups` | Group memberships |
| `roles` | User roles |

## Role Mapping

Map OIDC groups/roles to Ascend roles:

```json
{
  "role_mapping": {
    "oidc_admins": "admin",
    "oidc_security": "security_admin",
    "oidc_developers": "developer",
    "oidc_viewers": "viewer"
  },
  "default_role": "viewer",
  "groups_claim": "groups"
}
```

## Security Considerations

### Token Validation

Ascend validates OIDC tokens via Cognito:

1. **Signature** - RS256 signature against JWKS
2. **Issuer** - Must match Cognito pool URL
3. **Audience** - Must match client ID
4. **Expiration** - Token must not be expired
5. **Nonce** - Prevents replay attacks

### Best Practices

1. **Use PKCE** - Enable Proof Key for Code Exchange
2. **Secure secrets** - Store client secrets securely
3. **Rotate secrets** - Rotate client secrets regularly
4. **Audit logs** - Monitor authentication events
5. **MFA** - Enable MFA in your OIDC provider

## Troubleshooting

### Invalid Token

- Verify issuer URL is correct
- Check client ID matches
- Ensure token is not expired

### Claims Missing

- Verify attribute mapping in Cognito
- Check OIDC scopes include required claims
- Review provider's claim configuration

### Redirect Errors

- Verify callback URLs are correct
- Check for URL encoding issues
- Ensure HTTPS is used

## Next Steps

- [SSO Configuration](/enterprise/sso) - Complete SSO setup
- [Authentication](/sdk/rest/authentication) - API authentication
- [Security](/security/overview) - Security overview
