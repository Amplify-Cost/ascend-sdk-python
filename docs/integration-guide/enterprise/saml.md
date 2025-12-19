---
title: SAML Configuration
sidebar_position: 1
---

# SAML Configuration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-ENT-012 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Configure SAML 2.0 authentication through AWS Cognito for enterprise single sign-on.

## Overview

Ascend supports SAML 2.0 federation via AWS Cognito, enabling integration with enterprise identity providers.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Your SAML  │───▶│ AWS Cognito │───▶│   Ascend    │
│     IdP     │    │  User Pool  │    │  Platform   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Supported Identity Providers

| Provider | Status |
|----------|--------|
| Okta | Supported |
| Azure AD | Supported |
| OneLogin | Supported |
| PingFederate | Supported |
| ADFS | Supported |
| Google Workspace | Supported |
| Custom SAML IdP | Supported |

## Cognito SAML Settings

When configuring your IdP, use these settings:

| Setting | Value |
|---------|-------|
| ACS URL | `https://{domain}.auth.{region}.amazoncognito.com/saml2/idpresponse` |
| Entity ID | `urn:amazon:cognito:sp:{user-pool-id}` |
| Name ID Format | `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress` |

## Configuration Steps

### 1. Get Your Cognito Details

```bash
curl https://pilot.owkai.app/api/cognito/pool-config/by-slug/your-org \
  -b cookies.txt
```

Note the `user_pool_id` and `region` from the response.

### 2. Configure Your IdP

Create a SAML application in your IdP with:

- **ACS URL**: `https://your-domain.auth.us-east-2.amazoncognito.com/saml2/idpresponse`
- **Entity ID**: `urn:amazon:cognito:sp:us-east-2_AbCdEfGhI`
- **Name ID**: Email address

### 3. Download IdP Metadata

Download the SAML metadata XML from your IdP.

### 4. Configure Cognito

In AWS Cognito Console:

1. Navigate to **Federation** → **Identity providers**
2. Click **Add provider** → **SAML**
3. Upload metadata document or enter:
   - Provider name
   - Metadata document URL
4. Configure attribute mapping

## Attribute Mapping

### Required Attributes

| SAML Attribute | Cognito Attribute | Required |
|----------------|-------------------|----------|
| `email` | `email` | Yes |
| `firstName` / `givenName` | `given_name` | Yes |
| `lastName` / `surname` | `family_name` | Yes |

### SAML Claim Names

| IdP | Email Claim |
|-----|-------------|
| Okta | `user.email` |
| Azure AD | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` |
| OneLogin | `Email` |
| ADFS | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` |

## Provider-Specific Guides

### Okta

1. **Create Application**
   - Admin Console → Applications → Create App Integration
   - Select SAML 2.0

2. **Configure SAML Settings**
   ```
   Single sign on URL: https://your-domain.auth.us-east-2.amazoncognito.com/saml2/idpresponse
   Audience URI: urn:amazon:cognito:sp:us-east-2_AbCdEfGhI
   Name ID format: EmailAddress
   Application username: Email
   ```

3. **Attribute Statements**
   | Name | Value |
   |------|-------|
   | `email` | `user.email` |
   | `firstName` | `user.firstName` |
   | `lastName` | `user.lastName` |

4. **Download Metadata**
   - Click **View Setup Instructions**
   - Download IdP metadata

### Azure AD

1. **Register Enterprise Application**
   - Azure Portal → Enterprise Applications → New application
   - Create your own application

2. **Configure SAML**
   - Single sign-on → SAML
   - Basic SAML Configuration:
   ```
   Identifier (Entity ID): urn:amazon:cognito:sp:us-east-2_AbCdEfGhI
   Reply URL (ACS URL): https://your-domain.auth.us-east-2.amazoncognito.com/saml2/idpresponse
   ```

3. **User Attributes & Claims**
   | Claim | Source Attribute |
   |-------|------------------|
   | `emailaddress` | `user.mail` |
   | `givenname` | `user.givenname` |
   | `surname` | `user.surname` |

4. **Download Metadata**
   - Download Federation Metadata XML

### Google Workspace

1. **Create SAML App**
   - Admin Console → Apps → Web and mobile apps
   - Add app → Add custom SAML app

2. **Configure**
   ```
   ACS URL: https://your-domain.auth.us-east-2.amazoncognito.com/saml2/idpresponse
   Entity ID: urn:amazon:cognito:sp:us-east-2_AbCdEfGhI
   Name ID format: EMAIL
   Name ID: Basic Information > Primary email
   ```

3. **Attribute Mapping**
   | Google Directory | App Attribute |
   |------------------|---------------|
   | Primary email | `email` |
   | First name | `firstName` |
   | Last name | `lastName` |

## SP-Initiated SSO Flow

```
1. User navigates to Ascend login
2. User selects "Login with SSO"
3. Ascend redirects to Cognito Hosted UI
4. Cognito redirects to IdP login
5. User authenticates with IdP
6. IdP sends SAML assertion to Cognito ACS URL
7. Cognito validates assertion and issues tokens
8. Ascend creates session from tokens
```

## IdP-Initiated SSO

For IdP-initiated SSO, configure:

1. **RelayState**: `https://pilot.owkai.app`
2. Enable IdP-initiated SSO in your IdP

## Testing

### Test SAML Login

1. Navigate to Cognito Hosted UI:
   ```
   https://your-domain.auth.us-east-2.amazoncognito.com/login?
     client_id=your-client-id&
     response_type=code&
     scope=openid+email+profile&
     redirect_uri=https://pilot.owkai.app/auth/callback
   ```

2. Click on your SAML provider
3. Authenticate with your IdP
4. Verify redirect to Ascend

### Debug SAML Response

Use browser developer tools or a SAML tracer extension to inspect:

- SAML Response
- Assertions
- Attribute values

## Troubleshooting

### Invalid SAML Response

- Verify ACS URL is exactly correct
- Check Entity ID matches
- Ensure certificate is valid

### User Not Found

- Verify email attribute is mapped
- Check email format matches

### Clock Skew

- SAML assertions have time constraints
- Ensure IdP and Cognito times are synchronized

## Security Best Practices

1. **Sign assertions** - Enable assertion signing
2. **Encrypt assertions** - Enable assertion encryption for sensitive data
3. **Short validity** - Use short assertion validity periods
4. **Secure transport** - Use HTTPS only
5. **Audit logs** - Monitor SAML authentication events

## Next Steps

- [SSO Configuration](/enterprise/sso) - Complete SSO setup
- [OIDC Configuration](/enterprise/oidc) - OIDC alternative
- [Authentication](/sdk/rest/authentication) - API authentication
