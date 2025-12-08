# Enterprise End-to-End Integration Testing Guide

**Version:** 2.0
**Date:** 2025-11-30
**Security Level:** Banking-Grade (SOC 2, PCI-DSS, HIPAA Compliant)
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Organization Onboarding](#phase-1-organization-onboarding)
4. [Phase 2: User Management](#phase-2-user-management)
5. [Phase 3: Authentication Flow Testing](#phase-3-authentication-flow-testing)
6. [Phase 4: SDK Integration](#phase-4-sdk-integration)
7. [Phase 5: Real Agent Action Testing](#phase-5-real-agent-action-testing)
8. [Phase 6: Multi-Tenant Isolation Verification](#phase-6-multi-tenant-isolation-verification)
9. [Phase 7: Enterprise Policy Testing](#phase-7-enterprise-policy-testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for:
- Onboarding a new customer organization to OW-AI Enterprise
- Configuring their Cognito user pool and authentication
- Integrating the OW-AI SDK into their AI agent infrastructure
- Testing real agent actions with enterprise policy enforcement
- Verifying multi-tenant data isolation

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Customer Organization Architecture                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │   AI Agent   │────▶│  OW-AI SDK   │────▶│  OW-AI Authorization     │ │
│  │  (Customer)  │     │  (Embedded)  │     │  Center (SaaS)           │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│         │                    │                        │                  │
│         │                    │                        ▼                  │
│         │                    │              ┌──────────────────────────┐ │
│         │                    │              │  Customer Cognito Pool   │ │
│         │                    │              │  (Dedicated per Org)     │ │
│         │                    │              └──────────────────────────┘ │
│         │                    │                        │                  │
│         ▼                    ▼                        ▼                  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    Customer Data (Isolated)                       │   │
│  │  - Agent Actions (organization_id filtered)                       │   │
│  │  - Audit Logs (organization_id filtered)                          │   │
│  │  - Smart Rules (organization_id filtered)                         │   │
│  │  - Policies (organization_id filtered)                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Access
- [ ] Platform Admin account (for organization provisioning)
- [ ] AWS Console access (for Cognito verification)
- [ ] Production API endpoint: `https://pilot.owkai.app`
- [ ] GitHub access to SDK repository

### Environment Variables (Customer Side)
```bash
# Customer's .env file for their AI agent
OWKAI_API_URL=https://pilot.owkai.app
OWKAI_API_KEY=<generated-api-key>
OWKAI_ORG_SLUG=<customer-org-slug>
```

---

## Phase 1: Organization Onboarding

### Step 1.1: Create New Organization

**As Platform Admin:**

```bash
# Login as platform admin
curl -X POST https://pilot.owkai.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@owkai.app",
    "password": "<admin-password>"
  }' \
  -c cookies.txt

# Create new organization
curl -X POST https://pilot.owkai.app/api/platform-admin/organizations \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Acme Financial Corp",
    "slug": "acme-financial",
    "email_domains": ["acme-financial.com", "acmefinancial.io"],
    "plan": "enterprise",
    "settings": {
      "mfa_required": true,
      "session_timeout_minutes": 30,
      "max_users": 100
    }
  }'
```

**Expected Response:**
```json
{
  "id": 5,
  "name": "Acme Financial Corp",
  "slug": "acme-financial",
  "status": "pending_cognito_setup",
  "created_at": "2025-11-30T10:00:00Z"
}
```

### Step 1.2: Provision Cognito User Pool

```bash
# Provision dedicated Cognito pool for organization
curl -X POST https://pilot.owkai.app/api/cognito-pools/provision \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "organization_id": 5,
    "mfa_configuration": "OPTIONAL",
    "password_policy": {
      "minimum_length": 12,
      "require_uppercase": true,
      "require_lowercase": true,
      "require_numbers": true,
      "require_symbols": true
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "organization_id": 5,
  "cognito_user_pool_id": "us-east-2_AbCdEfGhI",
  "cognito_app_client_id": "1234567890abcdefghijklmnop",
  "status": "active"
}
```

### Step 1.3: Verify Organization Setup

```bash
# Get organization details
curl -X GET https://pilot.owkai.app/api/platform-admin/organizations/5 \
  -b cookies.txt

# Verify Cognito pool status
curl -X GET https://pilot.owkai.app/api/cognito-pools/5/status \
  -b cookies.txt
```

**Verification Checklist:**
- [ ] Organization created with correct slug
- [ ] Cognito user pool provisioned
- [ ] App client ID generated
- [ ] MFA configuration applied
- [ ] Email domains registered

---

## Phase 2: User Management

### Step 2.1: Create Organization Admin

```bash
# Create first admin user for the organization
curl -X POST https://pilot.owkai.app/api/platform-admin/organizations/5/users \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "email": "admin@acme-financial.com",
    "role": "org_admin",
    "name": "John Smith",
    "send_invite": true
  }'
```

**Expected Response:**
```json
{
  "user_id": 42,
  "email": "admin@acme-financial.com",
  "role": "org_admin",
  "cognito_user_id": "abc123-def456-ghi789",
  "status": "FORCE_CHANGE_PASSWORD",
  "temporary_password": "TempPass123!@#",
  "invite_sent": true
}
```

### Step 2.2: Create Regular Users (As Org Admin)

**Login as Org Admin first:**
```bash
# Org admin login URL
# https://pilot.owkai.app/#org=acme-financial

# After login, create team members
curl -X POST https://pilot.owkai.app/api/enterprise/users \
  -H "Content-Type: application/json" \
  -b org_admin_cookies.txt \
  -d '{
    "email": "developer@acme-financial.com",
    "role": "developer",
    "name": "Jane Developer"
  }'
```

### Step 2.3: Verify User Creation in Cognito

```bash
# List users in organization
curl -X GET "https://pilot.owkai.app/api/enterprise/users" \
  -b org_admin_cookies.txt
```

**Expected Response:**
```json
{
  "users": [
    {
      "id": 42,
      "email": "admin@acme-financial.com",
      "role": "org_admin",
      "mfa_enabled": false,
      "status": "active"
    },
    {
      "id": 43,
      "email": "developer@acme-financial.com",
      "role": "developer",
      "mfa_enabled": false,
      "status": "FORCE_CHANGE_PASSWORD"
    }
  ],
  "total": 2
}
```

---

## Phase 3: Authentication Flow Testing

### Step 3.1: Test NEW_PASSWORD_REQUIRED Flow

**Scenario:** New user logs in with temporary password

```javascript
// Frontend test - CognitoLogin.jsx handles this automatically
// Navigate to: https://pilot.owkai.app/#org=acme-financial

// Expected flow:
// 1. User enters email + temporary password
// 2. Cognito returns NEW_PASSWORD_REQUIRED challenge
// 3. NewPasswordRequired.jsx component appears
// 4. User sets new password (12+ chars, uppercase, lowercase, number, symbol)
// 5. Password changed successfully
// 6. If MFA required, MFA setup screen appears
// 7. User completes MFA setup with authenticator app
// 8. Login complete, redirected to dashboard
```

**Console logs to verify (SEC-030):**
```
SEC-030: Received NEW_PASSWORD_REQUIRED challenge
SEC-030: Responding to NEW_PASSWORD_REQUIRED challenge
SEC-030: Password change response: {AuthenticationResult: {...}}
SEC-030: Server session created successfully
```

### Step 3.2: Test MFA Setup Flow

**Scenario:** User setting up MFA for first time

```javascript
// After password change, if MFA required:
// 1. MFA_SETUP challenge returned
// 2. MFASetupChallenge.jsx component appears
// 3. QR code displayed (SEC-035 fix)
// 4. User scans with Google Authenticator / Authy
// 5. User enters 6-digit code
// 6. MFA verified and enabled
// 7. Login complete
```

**Console logs to verify (SEC-035):**
```
SEC-035: MFA setup initiated
SEC-035: QR code generated successfully
SEC-035: MFA verification successful
```

### Step 3.3: Test MFA Disable Flow

**Scenario:** User disabling MFA (if org policy allows)

```javascript
// In Security Settings:
// 1. Click "Disable MFA"
// 2. Modal appears requesting 6-digit code
// 3. Enter current authenticator code
// 4. MFA disabled
```

**Console logs to verify (SEC-037):**
```
SEC-037: Disabling MFA with Cognito token
SEC-037: MFA code verified for user@acme-financial.com
SEC-037: MFA disabled successfully
```

### Step 3.4: Test Session Expiration

```bash
# Test session timeout (should be org-configurable)
# 1. Login to application
# 2. Wait for session timeout (default 30 minutes)
# 3. Attempt API call
# 4. Should receive 401 Unauthorized
# 5. Redirect to login page
```

---

## Phase 4: SDK Integration

### Step 4.1: Generate API Key

**As Org Admin:**

```bash
# Navigate to Settings > API Keys in the UI
# Or use API:
curl -X POST https://pilot.owkai.app/api/keys/generate \
  -H "Content-Type: application/json" \
  -b org_admin_cookies.txt \
  -d '{
    "name": "Production AI Agent",
    "description": "API key for production AI agent integration",
    "permissions": ["agent_actions", "read_policies"]
  }'
```

**Expected Response:**
```json
{
  "key_id": "key_abc123def456",
  "api_key": "owkai_live_1234567890abcdefghijklmnopqrstuvwxyz",
  "name": "Production AI Agent",
  "created_at": "2025-11-30T12:00:00Z",
  "warning": "This is the only time the full API key will be shown. Store it securely."
}
```

**IMPORTANT:** Save this API key immediately - it's only shown once!

### Step 4.2: Install OW-AI SDK

**Python SDK:**
```bash
pip install owkai-sdk
```

**Node.js SDK:**
```bash
npm install @owkai/sdk
```

### Step 4.3: SDK Configuration

**Python Example:**
```python
# config.py
from owkai import OWKAIClient

client = OWKAIClient(
    api_url="https://pilot.owkai.app",
    api_key="owkai_live_1234567890abcdefghijklmnopqrstuvwxyz",
    organization_slug="acme-financial"
)
```

**Node.js Example:**
```javascript
// config.js
const { OWKAIClient } = require('@owkai/sdk');

const client = new OWKAIClient({
    apiUrl: 'https://pilot.owkai.app',
    apiKey: 'owkai_live_1234567890abcdefghijklmnopqrstuvwxyz',
    organizationSlug: 'acme-financial'
});
```

### Step 4.4: Test SDK Connection

```python
# test_connection.py
from owkai import OWKAIClient

client = OWKAIClient(
    api_url="https://pilot.owkai.app",
    api_key="owkai_live_..."
)

# Test connection
result = client.test_connection()
print(f"Connection status: {result['status']}")
print(f"Organization: {result['organization']}")
print(f"API version: {result['api_version']}")
```

**Expected Output:**
```
Connection status: connected
Organization: Acme Financial Corp
API version: 2.0.0
```

---

## Phase 5: Real Agent Action Testing

### Step 5.1: Submit Agent Action for Authorization

**Python SDK:**
```python
from owkai import OWKAIClient, AgentAction

client = OWKAIClient(
    api_url="https://pilot.owkai.app",
    api_key="owkai_live_..."
)

# Create an agent action request
action = AgentAction(
    agent_id="financial-advisor-agent-001",
    agent_name="Financial Advisor AI",
    action_type="data_access",
    resource="customer_portfolio",
    resource_id="CUST-12345",
    action_details={
        "operation": "read",
        "fields": ["balance", "holdings", "transactions"],
        "customer_segment": "premium"
    },
    context={
        "user_request": "Show me my investment portfolio",
        "session_id": "sess_abc123",
        "ip_address": "192.168.1.100"
    },
    risk_indicators={
        "data_sensitivity": "high",
        "pii_involved": True,
        "financial_data": True
    }
)

# Submit for authorization
response = client.submit_action(action)
print(f"Action ID: {response['action_id']}")
print(f"Status: {response['status']}")
print(f"Decision: {response['decision']}")
```

**Expected Response:**
```json
{
  "action_id": "act_xyz789abc123",
  "status": "pending_review",
  "decision": "pending",
  "estimated_review_time": "immediate",
  "risk_score": 75,
  "risk_level": "high",
  "policy_matches": [
    {
      "policy_id": "pol_financial_data",
      "policy_name": "Financial Data Access Policy",
      "action": "require_approval"
    }
  ]
}
```

### Step 5.2: Poll for Authorization Decision

```python
import time

action_id = "act_xyz789abc123"

# Poll for decision (with exponential backoff)
max_attempts = 10
for attempt in range(max_attempts):
    status = client.get_action_status(action_id)

    if status['decision'] != 'pending':
        print(f"Decision: {status['decision']}")
        print(f"Approved by: {status.get('approved_by', 'auto')}")
        print(f"Reason: {status.get('reason', 'N/A')}")
        break

    wait_time = min(2 ** attempt, 30)  # Max 30 seconds
    print(f"Waiting {wait_time}s for decision...")
    time.sleep(wait_time)
```

### Step 5.3: Handle Authorization Decisions

```python
def execute_with_authorization(action: AgentAction):
    """Execute action only if authorized"""

    response = client.submit_action(action)
    action_id = response['action_id']

    # Wait for decision
    decision = client.wait_for_decision(action_id, timeout=60)

    if decision['status'] == 'approved':
        print(f"Action approved: {decision['reason']}")
        # Execute the actual action
        return execute_action(action)

    elif decision['status'] == 'denied':
        print(f"Action denied: {decision['reason']}")
        raise PermissionError(f"Action not authorized: {decision['reason']}")

    elif decision['status'] == 'requires_modification':
        print(f"Modification required: {decision['required_changes']}")
        # Modify action and resubmit
        modified_action = apply_modifications(action, decision['required_changes'])
        return execute_with_authorization(modified_action)

    else:
        raise TimeoutError("Authorization decision timeout")
```

### Step 5.4: Batch Agent Actions

```python
# Submit multiple related actions
actions = [
    AgentAction(
        agent_id="financial-advisor-agent-001",
        action_type="data_access",
        resource="customer_profile",
        resource_id="CUST-12345",
        action_details={"operation": "read"}
    ),
    AgentAction(
        agent_id="financial-advisor-agent-001",
        action_type="data_access",
        resource="transaction_history",
        resource_id="CUST-12345",
        action_details={"operation": "read", "date_range": "90d"}
    ),
    AgentAction(
        agent_id="financial-advisor-agent-001",
        action_type="recommendation",
        resource="investment_advice",
        action_details={
            "type": "portfolio_rebalance",
            "risk_tolerance": "moderate"
        }
    )
]

# Submit batch
batch_response = client.submit_batch(actions)
print(f"Batch ID: {batch_response['batch_id']}")
print(f"Actions submitted: {len(batch_response['actions'])}")

# Wait for all decisions
batch_result = client.wait_for_batch(
    batch_response['batch_id'],
    timeout=120
)

for result in batch_result['results']:
    print(f"Action {result['action_id']}: {result['decision']}")
```

---

## Phase 6: Multi-Tenant Isolation Verification

### Step 6.1: Create Second Organization for Testing

```bash
# As platform admin, create a second test organization
curl -X POST https://pilot.owkai.app/api/platform-admin/organizations \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Beta Testing Corp",
    "slug": "beta-testing",
    "email_domains": ["beta-testing.com"]
  }'
```

### Step 6.2: Verify Data Isolation

**Test 1: API Key Isolation**
```python
# Organization A's API key should not access Organization B's data

# Acme Financial's API key
acme_client = OWKAIClient(api_key="owkai_live_acme...")

# Try to access Beta Testing's data (should fail)
try:
    # This should return only Acme's actions, never Beta's
    actions = acme_client.list_actions()

    for action in actions:
        assert action['organization_id'] == 5, "Data leak detected!"

    print("Data isolation verified - only own organization's data returned")

except Exception as e:
    print(f"Error: {e}")
```

**Test 2: User Session Isolation**
```bash
# Login as Acme user
curl -X POST https://pilot.owkai.app/api/auth/cognito-session \
  -H "Content-Type: application/json" \
  -d '{"accessToken": "...", "idToken": "...", "refreshToken": "..."}' \
  -c acme_cookies.txt

# Try to access Beta Testing's data
curl -X GET "https://pilot.owkai.app/api/agent-activity?organization_id=6" \
  -b acme_cookies.txt

# Expected: Only returns Acme's data (org_id=5), ignores the query param
```

**Test 3: Cross-Organization Policy Access**
```bash
# Acme user should not see Beta's policies
curl -X GET https://pilot.owkai.app/api/governance/policies \
  -b acme_cookies.txt

# Should return only Acme's policies
# Any policy with organization_id != 5 indicates a data leak
```

### Step 6.3: Audit Log Isolation

```bash
# Verify audit logs are isolated
curl -X GET https://pilot.owkai.app/api/audit/logs \
  -b acme_cookies.txt

# All returned logs should have organization_id = 5
# Any other organization_id indicates a security breach
```

---

## Phase 7: Enterprise Policy Testing

### Step 7.1: Create Custom Policies

**As Org Admin:**

```bash
# Create a policy for high-risk financial operations
curl -X POST https://pilot.owkai.app/api/governance/policies \
  -H "Content-Type: application/json" \
  -b org_admin_cookies.txt \
  -d '{
    "name": "High-Risk Financial Operations",
    "description": "Requires manual approval for high-value transactions",
    "policy_type": "authorization",
    "conditions": {
      "action_type": ["transaction", "transfer", "withdrawal"],
      "risk_score": {"gte": 70},
      "amount": {"gte": 10000}
    },
    "actions": {
      "require_approval": true,
      "approver_roles": ["compliance_officer", "org_admin"],
      "notification": {
        "channels": ["email", "slack"],
        "urgency": "high"
      }
    },
    "enabled": true
  }'
```

### Step 7.2: Test Policy Enforcement

```python
# Submit action that should trigger the policy
high_risk_action = AgentAction(
    agent_id="trading-bot-001",
    action_type="transaction",
    resource="customer_account",
    resource_id="ACC-98765",
    action_details={
        "operation": "transfer",
        "amount": 50000,
        "destination": "external_account",
        "currency": "USD"
    },
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True
    }
)

response = client.submit_action(high_risk_action)

# Should trigger policy
assert response['status'] == 'pending_review'
assert response['risk_score'] >= 70
assert any(p['policy_name'] == 'High-Risk Financial Operations'
           for p in response['policy_matches'])

print("Policy correctly triggered for high-risk action")
```

### Step 7.3: Test Auto-Approval Policies

```python
# Create low-risk action that should auto-approve
low_risk_action = AgentAction(
    agent_id="chatbot-001",
    action_type="query",
    resource="faq_database",
    action_details={
        "operation": "search",
        "query": "What are your business hours?"
    },
    risk_indicators={
        "pii_involved": False,
        "financial_data": False
    }
)

response = client.submit_action(low_risk_action)

# Should auto-approve
assert response['decision'] == 'approved'
assert response['approval_type'] == 'automatic'
print("Low-risk action correctly auto-approved")
```

---

## Troubleshooting

### Common Issues

#### Issue: "Authentication required" Error
```
Error: [AUTH_001] Authentication required
```

**Solution:**
1. Check API key is valid and not expired
2. Verify using `X-API-Key` header:
```python
client = OWKAIClient(
    api_key="owkai_live_...",
    headers={"X-API-Key": "owkai_live_..."}  # SEC-033 fix
)
```

#### Issue: "Session expired" During MFA Operations
```
Error: Session expired. Please log in again.
```

**Solution:**
This occurs when using server JWT instead of Cognito token. The SEC-035 and SEC-037 fixes handle this by:
1. Accepting Cognito token in request body
2. Or via `X-Cognito-Token` header

#### Issue: NEW_PASSWORD_REQUIRED Shows MFA Screen
**Solution:**
This was fixed in SEC-030. Ensure frontend is updated to version with `NewPasswordRequired.jsx` component.

#### Issue: User Invitation Not Creating Cognito User
**Solution:**
This was fixed in SEC-034. Backend now calls `admin_create_user` on Cognito when inviting users.

#### Issue: API Key Prefix Mismatch
```
Warning: Key prefix doesn't match expected format
```

**Solution:**
SEC-038 confirmed this is cosmetic only. Keys are validated by hash, not prefix.

### Debug Mode

Enable debug logging:
```python
import logging

logging.basicConfig(level=logging.DEBUG)

client = OWKAIClient(
    api_key="owkai_live_...",
    debug=True
)
```

### Health Check Endpoints

```bash
# API Health
curl https://pilot.owkai.app/health

# Deployment Info
curl https://pilot.owkai.app/api/deployment-info

# Auth Status (with cookies)
curl https://pilot.owkai.app/api/auth/me -b cookies.txt
```

---

## Security Compliance Verification

### Checklist for Each Organization

- [ ] Cognito user pool provisioned with dedicated pool ID
- [ ] MFA configuration matches organization requirements
- [ ] Password policy enforced (12+ chars, complexity)
- [ ] API keys are SHA-256 hashed with salt
- [ ] All data queries filter by organization_id
- [ ] Audit logs capture all sensitive operations
- [ ] Session cookies are HttpOnly and Secure
- [ ] CSRF protection enabled
- [ ] Rate limiting active on authentication endpoints

### Compliance Standards Met

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| SOC 2 CC6.1 | Access Control | Multi-tenant isolation, RBAC |
| PCI-DSS 8.3 | MFA | TOTP-based MFA, configurable per org |
| HIPAA 164.312 | Audit Controls | Complete audit trail |
| NIST 800-63B | Authentication | AAL2 compliance with MFA |
| GDPR Art. 25 | Data Protection | Tenant isolation by design |

---

## Support

For enterprise support:
- Email: enterprise@owkai.app
- Slack: #owkai-enterprise-support
- Documentation: https://docs.owkai.app/enterprise

---

*Document Version: 2.0 | Last Updated: 2025-11-30 | Classification: Internal Use*
