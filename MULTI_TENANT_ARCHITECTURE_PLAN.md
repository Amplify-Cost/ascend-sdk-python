# OW-AI Enterprise Multi-Tenant Architecture Plan

**Document Version:** 1.0
**Classification:** INTERNAL - ARCHITECTURE
**Date:** 2025-11-25
**Author:** OW-AI Enterprise Engineering

---

## Executive Summary

This plan completes the multi-tenant authentication architecture to provide **true tenant isolation** with **banking-level security**. Each customer organization gets:

- Dedicated AWS Cognito User Pool (isolated authentication)
- Complete data isolation (organization_id filtering)
- Custom URL access (subdomain or path-based)
- Independent MFA and password policies

**Current State:** 95% complete - infrastructure exists
**Gap:** Frontend org detection and routing

---

## Architecture Overview

### Target State Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-TENANT LOGIN FLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: User Access                                                        │
│  ─────────────────────                                                      │
│                                                                             │
│  Option A: Subdomain       Option B: Path           Option C: Email         │
│  ───────────────────       ─────────────            ───────────────         │
│  acme.pilot.owkai.app  →   pilot.owkai.app/acme  →  User enters email       │
│         │                         │                        │                │
│         └─────────────────────────┴────────────────────────┘                │
│                                   │                                         │
│                                   ▼                                         │
│  STEP 2: Organization Detection                                             │
│  ──────────────────────────────                                             │
│                                                                             │
│  Frontend extracts org identifier:                                          │
│  • Subdomain: "acme" from acme.pilot.owkai.app                              │
│  • Path: "acme" from /acme/login                                            │
│  • Email: "acme.com" → lookup org by email domain                           │
│                                   │                                         │
│                                   ▼                                         │
│  STEP 3: Fetch Organization's Cognito Config                                │
│  ───────────────────────────────────────────                                │
│                                                                             │
│  GET /api/cognito/pool-config/by-slug/acme                                  │
│                                                                             │
│  Response:                                                                  │
│  {                                                                          │
│    "user_pool_id": "us-east-2_nxIgGAgxf",     ← Acme's dedicated pool       │
│    "app_client_id": "5gjc76r6cku8vuqr01641q5u53",                           │
│    "region": "us-east-2",                                                   │
│    "organization_id": 4,                                                    │
│    "organization_name": "Acme Corp",                                        │
│    "mfa_configuration": "OPTIONAL"                                          │
│  }                                                                          │
│                                   │                                         │
│                                   ▼                                         │
│  STEP 4: Authenticate Against Org's Cognito Pool                            │
│  ───────────────────────────────────────────────                            │
│                                                                             │
│  Frontend creates CognitoIdentityProvider with org's pool                   │
│  User credentials validated ONLY against Acme's pool                        │
│  Cognito returns JWT with issuer: .../us-east-2_nxIgGAgxf                   │
│                                   │                                         │
│                                   ▼                                         │
│  STEP 5: Exchange for Platform Session                                      │
│  ─────────────────────────────────────                                      │
│                                                                             │
│  POST /api/auth/cognito-session                                             │
│  Body: { cognito_token, organization_slug }                                 │
│                                                                             │
│  Backend:                                                                   │
│  1. Extract pool ID from JWT issuer                                         │
│  2. Verify JWT signature against org's Cognito JWKS                         │
│  3. Confirm pool matches organization record                                │
│  4. Create/update user with organization_id                                 │
│  5. Issue platform JWT with organization_id claim                           │
│  6. Set HttpOnly session cookie                                             │
│                                   │                                         │
│                                   ▼                                         │
│  STEP 6: Access Organization's Data                                         │
│  ─────────────────────────────────                                          │
│                                                                             │
│  All subsequent requests include organization_id                            │
│  Database queries filtered by organization_id                               │
│  User sees ONLY their organization's data                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Org Detection Endpoints

**File:** `/ow-ai-backend/routes/org_detection_routes.py`

```python
# New endpoints needed:

GET /api/organizations/detect
# Detects org from request context (subdomain, origin header)
# Returns: { slug, name, organization_id, login_url }

GET /api/organizations/by-email-domain/{domain}
# Maps email domain to organization
# Example: acme.com → Acme Corp
# Returns: { slug, name, organization_id }

GET /api/organizations/by-slug/{slug}/public-info
# Returns public info for login page branding
# Returns: { name, logo_url, login_message, mfa_required }
```

**Database Addition:**
```sql
-- Add email domain mapping to organizations
ALTER TABLE organizations ADD COLUMN email_domains TEXT[];
-- Example: ['acme.com', 'acme.net'] for Acme Corp
```

### Phase 2: Frontend Dynamic Routing

**File:** `/owkai-pilot-frontend/src/services/cognitoAuth.js`

Changes needed:
1. Remove hardcoded `DEFAULT_ORG_SLUG`
2. Add `detectOrganizationFromContext()` function
3. Support subdomain detection
4. Support path-based routing
5. Support email domain lookup

**File:** `/owkai-pilot-frontend/src/pages/LoginPage.jsx`

Changes needed:
1. Show organization name/logo on login page
2. Add "Not your organization?" link
3. Handle org not found gracefully

### Phase 3: URL Routing Strategy

**Option A: Subdomain-Based (Recommended for Enterprise)**
```
acme.pilot.owkai.app     → Acme Corp login
bigbank.pilot.owkai.app  → Big Bank login
pilot.owkai.app          → Org selector page
```

**Option B: Path-Based (Simpler DNS)**
```
pilot.owkai.app/org/acme      → Acme Corp login
pilot.owkai.app/org/bigbank   → Big Bank login
pilot.owkai.app/login         → Org selector page
```

**Recommendation:** Start with Path-Based (Phase 1), add Subdomain later (Phase 2)

---

## Security Controls

### Tenant Isolation Matrix

| Layer | Isolation Method | Verification |
|-------|------------------|--------------|
| Authentication | Dedicated Cognito Pool per org | Pool ID in JWT issuer |
| Authorization | organization_id in JWT claims | Middleware validation |
| Database | organization_id foreign key | Query-level filtering |
| API | organization_id in request context | Route guards |
| Audit | organization_id in all logs | Immutable audit trail |

### Banking-Level Security Features

| Feature | Implementation | Compliance |
|---------|----------------|------------|
| Pool Isolation | Each org has dedicated Cognito pool | SOC 2 Type II |
| MFA per Org | Configurable: OFF/OPTIONAL/ON | PCI-DSS 8.3 |
| Password Policy | Per-org NIST SP 800-63B settings | NIST 800-63B |
| Session Management | HttpOnly, Secure, SameSite cookies | OWASP Top 10 |
| JWT Validation | RS256 signature, issuer verification | OAuth 2.0 |
| Audit Trail | Complete action chain logging | SOX, GDPR |

---

## Implementation Order

### Step 1: Backend Changes (2-3 hours)
1. Create org_detection_routes.py
2. Add email_domains column to organizations
3. Register routes in main.py
4. Test endpoints

### Step 2: Frontend Changes (3-4 hours)
1. Update cognitoAuth.js with dynamic detection
2. Update LoginPage.jsx for org context
3. Add org selector component
4. Update routing in App.jsx

### Step 3: Integration Testing (1-2 hours)
1. Test Acme Corp login flow
2. Verify data isolation
3. Test MFA flow
4. Test error scenarios

### Step 4: Documentation (1 hour)
1. Update onboarding script
2. Document customer setup process
3. Create troubleshooting guide

---

## Test Scenarios

### Scenario 1: Path-Based Login
```
1. User navigates to: pilot.owkai.app/org/acme-corp
2. Frontend detects slug: "acme-corp"
3. Frontend fetches Acme's Cognito config
4. User logs in with admin@acmecorp.test
5. User sees only Acme Corp data
```

### Scenario 2: Email Domain Detection
```
1. User navigates to: pilot.owkai.app/login
2. User enters email: john@acme.com
3. Frontend calls: /api/organizations/by-email-domain/acme.com
4. Frontend redirects to: /org/acme-corp
5. User continues login flow
```

### Scenario 3: Direct URL Access
```
1. Customer bookmarks: pilot.owkai.app/org/acme-corp/dashboard
2. Not logged in → redirect to /org/acme-corp/login
3. After login → return to /org/acme-corp/dashboard
4. All URLs maintain org context
```

---

## Rollback Plan

If issues arise:
1. Set `VITE_MULTI_TENANT=false` in frontend
2. Frontend reverts to hardcoded `owkai-internal` slug
3. Existing users unaffected
4. New org users wait for fix

---

## Success Criteria

- [ ] Acme Corp user can login at `/org/acme-corp`
- [ ] Acme Corp user sees only their data
- [ ] Acme Corp user authenticates against their Cognito pool
- [ ] OW-AI internal users unaffected
- [ ] Error messages are user-friendly
- [ ] Audit trail captures organization context

---

## Approval

**Ready to implement?**

This plan provides true multi-tenant isolation with:
- Dedicated authentication per customer
- Complete data isolation
- Enterprise security standards
- Banking-level compliance

Estimated total time: 6-10 hours
