# Enterprise Customer Onboarding & Verification Guide

**Document Version:** 1.0.0
**Last Updated:** 2025-11-30
**Engineer:** Ascend Engineer
**Compliance:** SOC 2, HIPAA, PCI-DSS, GDPR

---

## Overview

This guide provides step-by-step instructions to:
1. Onboard a new organization to OW-AI Enterprise
2. Verify the complete onboarding flow works correctly
3. Test SDK/API integration
4. Configure enterprise integrations (Slack, SIEM, etc.)

---

## Prerequisites

### Environment Requirements

```bash
# Verify you're in the backend directory
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

# Verify Python environment
python3 --version  # Should be 3.10+

# Verify AWS credentials are configured
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

### Required AWS Permissions

The AWS user/role needs these permissions:
- `cognito-idp:CreateUserPool`
- `cognito-idp:CreateUserPoolClient`
- `cognito-idp:CreateUserPoolDomain`
- `cognito-idp:AdminCreateUser`
- `cognito-idp:AdminSetUserPassword`
- `ses:SendEmail` (for welcome emails)

### Database Connection

Ensure the database is accessible:
```bash
# Test database connection
python3 -c "from database import engine; print('Database connected:', engine.url)"
```

---

## PHASE 1: Onboard a New Organization

### Step 1.1: Dry Run (Preview)

First, preview what the onboarding will do WITHOUT making changes:

```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

python scripts/onboard_pilot_customer.py \
  --company "Test Enterprise Corp" \
  --email "admin@testenterprise.com" \
  --dry-run
```

**Expected Output:**
```
============================================================
  OW-AI Enterprise Pilot Onboarding
============================================================

  Company: Test Enterprise Corp
  Admin Email: admin@testenterprise.com
  Send Email: Yes (AWS SES)

  [DRY RUN] Would execute the following steps:
  1. Create organization: Test Enterprise Corp (slug: test-enterprise-corp)
  2. Provision Cognito pool for: test-enterprise-corp
  3. Create admin user in Cognito with temp password
  4. Create admin user in local database: admin@testenterprise.com
  5. Send welcome email via AWS SES

  Run without --dry-run to execute.
```

### Step 1.2: Execute Full Onboarding

Run the actual onboarding:

```bash
python scripts/onboard_pilot_customer.py \
  --company "Test Enterprise Corp" \
  --email "admin@testenterprise.com"
```

**Expected Output:**
```
============================================================
  OW-AI Enterprise Pilot Onboarding
============================================================

  Company: Test Enterprise Corp
  Admin Email: admin@testenterprise.com
  Send Email: Yes (AWS SES)

------------------------------------------------------------

  [1] Creating organization record...
      ✅ Organization created: Test Enterprise Corp (ID: 5)
      ✅ Slug: test-enterprise-corp
      ✅ Email domain: testenterprise.com
      ✅ Trial ends: 2025-12-30

  [2] Provisioning AWS Cognito user pool...
      ✅ Pool created: us-east-2_XXXXXXXXX
      ✅ App client: xxxxxxxxxxxxxxxxxxxxxxxxxx
      ✅ Domain: test-enterprise-corp-auth

  [3] Creating admin user record...
      ✅ Admin user created: admin@testenterprise.com (ID: 10)
      ✅ Role: admin, Org Admin: Yes
      ✅ Cognito User ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

  [5] Sending welcome email via AWS SES...
      ✅ Welcome email sent to admin@testenterprise.com
      ✅ SES Message ID: 0100xxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

============================================================
                    ONBOARDING COMPLETE
============================================================

  Organization: Test Enterprise Corp (ID: 5)
  Slug: test-enterprise-corp
  Admin: admin@testenterprise.com (ID: 10)
  Cognito Pool: us-east-2_XXXXXXXXX
  Trial Ends: 2025-12-30
  Email Sent: ✅ Yes (AWS SES)
  Login URL: https://pilot.owkai.app/#org=test-enterprise-corp

  CREDENTIALS:
  Email: admin@testenterprise.com
  Temp Password: Xy7@Kp2#mN9$qR4w
```

**IMPORTANT:** Save the temporary password - it's only shown once!

### Step 1.3: Verify Database Records

Verify the organization was created:

```bash
python3 -c "
from database import SessionLocal
from models import Organization, User

db = SessionLocal()

# Find organization
org = db.query(Organization).filter(Organization.slug == 'test-enterprise-corp').first()
if org:
    print(f'Organization ID: {org.id}')
    print(f'Name: {org.name}')
    print(f'Slug: {org.slug}')
    print(f'Email Domains: {org.email_domains}')
    print(f'Cognito Pool ID: {org.cognito_user_pool_id}')
    print(f'Cognito Status: {org.cognito_pool_status}')
    print(f'Trial Ends: {org.trial_ends_at}')
else:
    print('ERROR: Organization not found!')

# Find admin user
user = db.query(User).filter(User.email == 'admin@testenterprise.com').first()
if user:
    print(f'\nUser ID: {user.id}')
    print(f'Email: {user.email}')
    print(f'Organization ID: {user.organization_id}')
    print(f'Cognito User ID: {user.cognito_user_id}')
    print(f'Is Org Admin: {user.is_org_admin}')
    print(f'Role: {user.role}')
else:
    print('ERROR: User not found!')

db.close()
"
```

**Expected Output:**
```
Organization ID: 5
Name: Test Enterprise Corp
Slug: test-enterprise-corp
Email Domains: ['testenterprise.com']
Cognito Pool ID: us-east-2_XXXXXXXXX
Cognito Status: active
Trial Ends: 2025-12-30 00:00:00+00:00

User ID: 10
Email: admin@testenterprise.com
Organization ID: 5
Cognito User ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Is Org Admin: True
Role: admin
```

---

## PHASE 2: Verify Login Flow

### Step 2.1: Test Production Login URL

Open the organization-specific login URL in a browser:

```
https://pilot.owkai.app/#org=test-enterprise-corp
```

**Expected Console Output (in browser):**
```
[ENTERPRISE] Org detected from hash: test-enterprise-corp
[ENTERPRISE] Org slug stored in session: test-enterprise-corp
🏢 [MULTI-TENANT] Using URL-detected org: test-enterprise-corp
📧 [COGNITO] Found pool for email domain: testenterprise.com
```

### Step 2.2: First Login with Temporary Password

1. Enter the email: `admin@testenterprise.com`
2. Enter the temporary password from onboarding output
3. You should be prompted to set a new password
4. Set a new password (meets enterprise requirements: 12+ chars, uppercase, lowercase, number, symbol)

**Password Requirements:**
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (!@#$%^&*)

### Step 2.3: Verify Dashboard Access

After successful login, verify:
- [ ] Dashboard loads without errors
- [ ] Organization name shows "Test Enterprise Corp" in the header
- [ ] No data from other organizations is visible
- [ ] AI Insights shows "No activity yet" (empty state)

### Step 2.4: Verify API Endpoint Isolation

Test that the logged-in user only sees their organization's data:

```bash
# Get a session cookie by logging in via the UI first
# Then test API endpoints in browser DevTools:

# Should return empty array (new org has no alerts)
fetch('/api/alerts').then(r => r.json()).then(console.log)

# Should return empty array (new org has no agent actions)
fetch('/api/agent-activity').then(r => r.json()).then(console.log)

# Should return organization settings
fetch('/api/organizations/settings').then(r => r.json()).then(console.log)
```

---

## PHASE 3: SDK/API Key Integration Testing

### Step 3.1: Generate API Key

1. In the dashboard, navigate to **Settings > API Keys**
2. Click **Generate New Key**
3. Enter a name: "SDK Test Key"
4. Select permissions: All
5. Click **Generate**
6. **COPY THE KEY IMMEDIATELY** - it's only shown once!

**Example Key Format:**
```
owkai_sk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3.2: Test API Key Authentication

Test the API key works for SDK operations:

```bash
# Replace with your actual API key
API_KEY="owkai_sk_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Test agent action endpoint (SDK primary endpoint)
curl -X POST https://pilot.owkai.app/api/authorization/agent-action \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "SDK Test Agent",
    "action_type": "data_access",
    "resource": "customer_database",
    "details": {
      "query_type": "SELECT",
      "table": "customers",
      "reason": "API integration test"
    },
    "risk_score": 25
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "status": "pending",
  "agent_name": "SDK Test Agent",
  "action_type": "data_access",
  "resource": "customer_database",
  "risk_score": 25,
  "organization_id": 5,
  "created_at": "2025-11-30T..."
}
```

### Step 3.3: Verify Action in Dashboard

1. Navigate to **Agent Authorization** in the dashboard
2. You should see the "SDK Test Agent" action with status "Pending"
3. Verify the action belongs to your organization only

### Step 3.4: Test Action Status Polling

```bash
# Replace ACTION_ID with the ID from previous response
ACTION_ID="uuid-from-previous-response"

curl https://pilot.owkai.app/api/agent-action/status/$ACTION_ID \
  -H "X-API-Key: $API_KEY"
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "status": "pending",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## PHASE 4: Integration Configuration Testing

### Step 4.1: Navigate to Integrations

1. In dashboard, go to **Settings > Integrations**
2. You should see 11 integration types:
   - SIEM: Splunk, QRadar, Sentinel
   - Identity: Active Directory, Okta, Azure AD
   - Notifications: Slack, Teams, PagerDuty
   - ITSM: ServiceNow
   - Custom: Webhook

### Step 4.2: Test Slack Webhook Integration

1. Get a Slack webhook URL from your Slack workspace:
   - Go to api.slack.com > Your Apps > Create New App
   - Enable Incoming Webhooks
   - Add to a channel
   - Copy the webhook URL

2. In OW-AI Integrations, click **Configure** on Slack

3. Enter configuration:
   - **Name:** "Test Slack Alerts"
   - **Endpoint URL:** Your Slack webhook URL
   - **Auth Type:** None (webhooks don't need auth)

4. Click **Test Connection**

**Expected Result:**
```
✅ Connection successful!
HTTP Method: POST
Response Time: 245ms
Health Status: healthy
```

5. Check your Slack channel - you should see a test message from OW-AI

### Step 4.3: Test Custom Webhook Integration

For testing without a real webhook, use webhook.site:

1. Go to https://webhook.site
2. Copy your unique URL

3. In OW-AI, configure a Custom Webhook:
   - **Name:** "Test Webhook"
   - **Endpoint URL:** Your webhook.site URL
   - **Auth Type:** None

4. Click **Test Connection**

5. Check webhook.site - you should see the test payload:
```json
{
  "test": true,
  "integration_type": "custom",
  "timestamp": "2025-11-30T...",
  "message": "OW-AI Integration Test",
  "source": "OW-AI Enterprise"
}
```

### Step 4.4: Save Integration Configuration

After successful test:
1. Click **Save Configuration**
2. Integration status should change to "Active"
3. The integration is now available for alerts and events

---

## PHASE 5: Invite Additional Users

### Step 5.1: Invite a Team Member

1. Navigate to **Settings > Users**
2. Click **Invite User**
3. Enter:
   - Email: `developer@testenterprise.com`
   - Role: `user` (or `admin`)
4. Click **Send Invitation**

### Step 5.2: Verify Invitation Email

The invited user should receive an email with:
- Organization name: Test Enterprise Corp
- Login URL with org slug
- Temporary password
- Instructions to change password on first login

### Step 5.3: Test Invited User Login

1. Open login URL: `https://pilot.owkai.app/#org=test-enterprise-corp`
2. Login with invited email and temp password
3. Set new password
4. Verify they see the same organization data (multi-tenant isolation)

---

## PHASE 6: Verify Multi-Tenant Isolation

### Step 6.1: Create Second Test Organization

```bash
python scripts/onboard_pilot_customer.py \
  --company "Second Test Corp" \
  --email "admin@secondtest.com"
```

### Step 6.2: Login to Second Organization

```
https://pilot.owkai.app/#org=second-test-corp
```

### Step 6.3: Verify Data Isolation

1. Create an agent action in First Org using API key
2. Login to Second Org
3. Verify Second Org CANNOT see First Org's agent actions
4. This confirms banking-level multi-tenant isolation

---

## Verification Checklist

### Onboarding
- [ ] Organization created in database
- [ ] Cognito user pool provisioned
- [ ] Admin user created in Cognito
- [ ] Admin user linked in local database
- [ ] Welcome email sent via AWS SES

### Authentication
- [ ] Multi-tenant URL routing works (/#org=slug)
- [ ] First login with temp password succeeds
- [ ] Password change required on first login
- [ ] Session persists after password change
- [ ] Logout works correctly

### Authorization
- [ ] Dashboard loads for organization
- [ ] API endpoints return only org-specific data
- [ ] API key generation works
- [ ] API key authentication works for SDK
- [ ] Agent actions scoped to organization

### Integrations
- [ ] Integration configuration UI loads
- [ ] Slack webhook test succeeds
- [ ] Custom webhook test succeeds
- [ ] Integration can be saved
- [ ] Integration appears as "Active"

### Multi-Tenant Isolation
- [ ] Org A cannot see Org B's data
- [ ] Org B cannot see Org A's data
- [ ] API keys are scoped to organization
- [ ] Audit logs are organization-specific

---

## Troubleshooting

### Issue: "Pool already exists" during onboarding

**Cause:** Organization was previously onboarded
**Solution:** This is idempotent - the script returns existing pool info

### Issue: Login fails with "User not found"

**Cause:** User not linked to Cognito properly
**Solution:** Check `cognito_user_id` is set in users table:
```sql
SELECT id, email, cognito_user_id, organization_id FROM users WHERE email = 'admin@testenterprise.com';
```

### Issue: Dashboard shows "Authentication required"

**Cause:** Session cookie not set properly
**Solution:**
1. Clear browser cookies for pilot.owkai.app
2. Login again with correct org slug in URL

### Issue: API key returns 401

**Cause:** API key not found or revoked
**Solution:** Generate a new API key in Settings > API Keys

### Issue: Integration test fails with "Connection failed"

**Cause:** Endpoint unreachable or incorrect auth
**Solution:**
1. Verify endpoint URL is correct
2. For webhooks, ensure it's a POST endpoint
3. Check auth type matches endpoint requirements

### Issue: Welcome email not received

**Cause:** AWS SES limits or email bounced
**Solution:**
1. Check AWS SES console for send status
2. Verify email domain is verified in SES
3. Check spam folder
4. Use `--no-email` flag and send manually

---

## API Endpoints Reference

### Public Endpoints (No Auth Required)
- `GET /api/cognito/pool-config/by-email-domain/{email}` - Get pool for email login

### Protected Endpoints (Session Cookie)
- `GET /api/agent-activity` - List agent actions
- `GET /api/alerts` - List alerts
- `GET /api/organizations/settings` - Get org settings
- `GET /api/integrations` - List integrations

### SDK Endpoints (API Key or Session)
- `POST /api/authorization/agent-action` - Create agent action
- `GET /api/agent-action/{id}` - Get action details
- `GET /api/agent-action/status/{id}` - Poll action status

### Admin Endpoints (Org Admin Required)
- `POST /api/keys/generate` - Generate API key
- `GET /api/keys` - List API keys
- `DELETE /api/keys/{id}` - Revoke API key

---

## Security Notes

1. **Temporary passwords** are single-use and expire in 7 days
2. **API keys** are hashed with SHA-256 before storage
3. **Session cookies** are HttpOnly and Secure
4. **All data** is filtered by organization_id at the database level
5. **Audit logs** record all sensitive operations
6. **Email credentials** are never stored - uses AWS IAM

---

*Document generated by Ascend Engineer - Enterprise Platform Engineering*
