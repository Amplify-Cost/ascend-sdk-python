# 📋 PHASE 2 DEPLOYMENT PLAN - Enterprise Cognito Integration

**Date**: 2025-11-20
**Status**: 55% Complete - Database Ready, Code Implementation Pending
**Timeline**: 8-10 hours remaining (1-2 days)

---

## ✅ COMPLETED (55%)

### **1. AWS Cognito Infrastructure** ✅
- **User Pool**: `us-east-2_HPew14Rbn`
- **App Client**: `2t9sms0kmd85huog79fqpslc2u`
- **Domain**: `owkai-enterprise-auth.auth.us-east-2.amazoncognito.com`
- **Custom Attributes**: organization_id, organization_slug, role, is_org_admin
- **Password Policy**: Enterprise-grade (12+ chars, complexity requirements)

### **2. Database Migration** ✅
- **Migration ID**: `4b29c02bbab8_phase2_add_cognito_integration`
- **Tested Locally**: ✅ PASSED
- **New Tables**: 3 (login_attempts, auth_audit_log, cognito_tokens)
- **New Columns**: cognito_user_id, last_login_at, login_count
- **RLS Policies**: 6 new policies (tenant isolation + platform owner)
- **Ready for Production**: ✅ YES

### **3. Enterprise Security Documentation** ✅
- **10-Layer Security Design**: Documented in PHASE2_ENTERPRISE_SECURITY_AUDIT.md
- **OWASP Top 10**: All addressed
- **Compliance Paths**: SOC2, HIPAA, GDPR, PCI-DSS
- **Best Practices**: Defense in depth, zero trust, least privilege

### **4. Dependencies** ✅
- **python-jose[cryptography]**: JWT validation (RS256)
- **boto3**: AWS SDK for Cognito
- **requests**: JWKS fetching
- **bleach**: XSS protection
- **slowapi**: Rate limiting

---

## ⏳ REMAINING (45%)

### **Step 1: Enterprise Cognito Middleware** (2-3 hours)

**File**: `/ow-ai-backend/dependencies_cognito.py`

**Functions to Implement**:

```python
# 1. JWKS Caching (Performance + Security)
@lru_cache(maxsize=1)
def get_cognito_public_keys() -> dict:
    """
    Fetch and cache Cognito public keys for JWT validation
    - Caches keys to reduce latency
    - Auto-refreshes on signature validation failure
    """

# 2. JWT Token Validation (RS256)
def validate_cognito_token(token: str) -> dict:
    """
    Enterprise-grade JWT validation:
    1. Decode JWT header to get key ID (kid)
    2. Fetch matching public key from JWKS
    3. Verify RS256 signature
    4. Validate claims:
       - Issuer (iss): Cognito URL
       - Audience (aud): Our client ID
       - Expiration (exp): Not expired
       - Not-before (nbf): Valid timing
       - Token use (token_use): "id"
    5. Extract custom attributes
    6. Return validated payload

    Security: Prevents token tampering, replay attacks, expiration bypass
    """

# 3. Current User with RLS Context
async def get_current_user_cognito(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Complete authentication flow:
    1. Extract Bearer token from Authorization header
    2. Validate JWT signature and claims
    3. Verify organization exists in database
    4. Set PostgreSQL RLS context: SET app.current_organization_id = X
    5. Log authentication event to auth_audit_log
    6. Track token in cognito_tokens table
    7. Update user.last_login_at
    8. Return user context

    Defense in Depth: JWT validation + DB validation + RLS + Audit logging
    """

# 4. Dual Authentication (Cognito + API Keys)
async def get_current_user_or_api_key(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Support both authentication methods:
    - UI users: AWS Cognito (OAuth 2.0)
    - SDK users: API Keys (constant-time comparison)

    Flow:
    1. Check Authorization header
    2. If JWT format (3 parts): Use Cognito validation
    3. If API key format: Use API key validation
    4. Return unified user context
    """

# 5. Organization Admin Enforcement
async def require_org_admin(
    current_user: dict = Depends(get_current_user_cognito)
) -> dict:
    """
    Enforces organization admin permissions
    - Validates is_org_admin flag from Cognito custom attribute
    - Logs admin action attempts
    """

# 6. Platform Owner Enforcement
async def require_platform_owner(
    current_user: dict = Depends(get_current_user_cognito)
) -> dict:
    """
    Enforces platform owner (org_id = 1) access
    - Only OW-AI Internal organization
    - Only users with role = "platform_owner"
    - Logs all platform admin access
    """

# 7. Authentication Audit Logging
def log_auth_event(
    event_type: str,
    user_id: Optional[int],
    cognito_user_id: Optional[str],
    organization_id: Optional[int],
    success: bool,
    failure_reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Log every authentication event for compliance
    - Inserts into auth_audit_log table
    - Sends metric to CloudWatch
    - Enables security monitoring and alerting
    """

# 8. Brute Force Detection
async def check_login_attempts(
    email: str,
    ip_address: str,
    db: Session
) -> bool:
    """
    Prevent brute force attacks:
    - Count failed attempts in last 15 minutes
    - Block if > 5 failed attempts from same IP
    - Block if > 10 failed attempts for same email
    - Log all attempts to login_attempts table
    """

# 9. Token Revocation
async def revoke_token(
    token_jti: str,
    reason: str,
    db: Session
):
    """
    Immediate token revocation:
    - Marks token as revoked in cognito_tokens table
    - Adds to revocation blocklist
    - Prevents further use even if not expired
    """
```

**Security Features**:
- ✅ RS256 signature verification (asymmetric, secure)
- ✅ Complete claim validation (iss, aud, exp, nbf, token_use)
- ✅ Token revocation support
- ✅ Brute force detection
- ✅ Complete audit trail
- ✅ RLS context setting (database-enforced multi-tenancy)
- ✅ Constant-time API key comparison

---

### **Step 2: Organization Admin Routes** (2 hours)

**File**: `/ow-ai-backend/routes/organization_admin_routes.py`

**Endpoints**:

```python
@router.post("/organizations/{org_id}/users")
async def invite_user(
    org_id: int,
    email: EmailStr,
    role: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Organization admin invites new user

    Security:
    1. Validate current user is admin of THIS organization
    2. Check user limit for subscription tier
    3. Validate email format (Pydantic EmailStr)
    4. Sanitize role (only allowed values)
    5. Create user in AWS Cognito with custom attributes
    6. Create user in local database
    7. Log admin action
    8. Send invitation email via Cognito

    Input Validation:
    - Email: Pydantic EmailStr validator
    - Role: Must be in ['user', 'admin', 'manager']
    - Organization exists and current user is admin
    """

@router.get("/organizations/{org_id}/users")
async def list_org_users(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    List all users in organization
    - Enforced by RLS (automatic filtering)
    - Returns sanitized user data (no passwords)
    - Logs access for compliance
    """

@router.delete("/organizations/{org_id}/users/{user_id}")
async def remove_user(
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Remove user from organization

    Security:
    1. Verify user belongs to this organization
    2. Prevent self-deletion
    3. Disable user in Cognito
    4. Revoke all active tokens
    5. Soft delete in database (audit trail)
    6. Log admin action
    """

@router.patch("/organizations/{org_id}/users/{user_id}/role")
async def update_user_role(
    org_id: int,
    user_id: int,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Update user role

    Security:
    - Validate role (must be allowed value)
    - Update in Cognito custom attributes
    - Update in local database
    - Revoke existing tokens (force re-login with new role)
    - Log role change for compliance
    """
```

**Input Validation** (Enterprise):
```python
from pydantic import BaseModel, EmailStr, validator
import bleach

class InviteUserRequest(BaseModel):
    email: EmailStr  # Pydantic validates email format
    role: str
    first_name: Optional[str]
    last_name: Optional[str]

    @validator("role")
    def validate_role(cls, v):
        allowed_roles = ['user', 'admin', 'manager']
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v

    @validator("first_name", "last_name")
    def sanitize_name(cls, v):
        if v:
            # Strip HTML tags (XSS protection)
            return bleach.clean(v, tags=[], strip=True).strip()
        return v
```

---

### **Step 3: Platform Admin Routes** (2 hours)

**File**: `/ow-ai-backend/routes/platform_admin_routes.py`

**Endpoints**:

```python
@router.get("/platform/organizations")
async def list_all_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View ALL organizations (metadata only)

    Security:
    - Enforced by require_platform_owner (org_id = 1 only)
    - Returns metadata only (no encrypted data)
    - Logs all platform admin access
    - RLS allows SELECT but encrypted columns remain encrypted
    """

@router.get("/platform/usage-stats")
async def get_platform_usage_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: Aggregated usage statistics

    Returns:
    - API calls per organization (by tier)
    - Active users per organization
    - Storage usage per organization
    - Overage calculations
    """

@router.get("/platform/actions")
async def list_all_agent_actions(
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View agent actions across ALL organizations

    Security:
    - Metadata only (action type, status, risk score)
    - NO access to encrypted payloads
    - Filterable by organization
    - Logs all access for compliance
    """

@router.post("/platform/organizations")
async def create_organization(
    org_data: CreateOrganizationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: Create new organization

    Flow:
    1. Validate organization data (name, slug, tier)
    2. Create organization in database
    3. Create Cognito user pool group (optional)
    4. Create default admin user
    5. Initialize organization settings
    6. Log creation
    """
```

---

### **Step 4: Update Models** (30 minutes)

**File**: `/ow-ai-backend/models.py`

**Changes Needed**:

```python
# Add to User model
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...

    # NEW: Cognito integration
    cognito_user_id = Column(String(255), unique=True, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)

    # Relationships (already exists from Phase 1)
    organization = relationship("Organization", back_populates="users")


# NEW: LoginAttempt model
class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), index=True)
    user_agent = Column(String(500))
    success = Column(Boolean, default=False)
    failure_reason = Column(String(255))
    cognito_user_id = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    attempted_at = Column(DateTime, default=datetime.now, index=True)


# NEW: AuthAuditLog model
class AuthAuditLog(Base):
    __tablename__ = "auth_audit_log"

    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    cognito_user_id = Column(String(255))
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(255))
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.now, index=True)


# NEW: CognitoToken model
class CognitoToken(Base):
    __tablename__ = "cognito_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cognito_user_id = Column(String(255), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    token_jti = Column(String(255), unique=True, nullable=False)
    token_type = Column(String(50), nullable=False)
    issued_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False, index=True)
    revocation_reason = Column(String(255))
```

---

### **Step 5: Local Testing** (1 hour)

**Test Plan**:

1. **Token Validation Test**:
   - Create test Cognito user
   - Get ID token from Cognito
   - Validate token signature
   - Verify claim extraction
   - Test expired token rejection

2. **Multi-Tenancy Test**:
   - Create 2 test organizations
   - Create users in each org
   - Verify RLS isolation (org A can't see org B's data)
   - Test platform owner metadata access

3. **Organization Admin Test**:
   - Invite user to organization
   - Verify Cognito user created
   - Verify database record created
   - Test user limit enforcement

4. **Platform Admin Test**:
   - List all organizations
   - View cross-org statistics
   - Verify NO access to encrypted data

5. **Brute Force Test**:
   - Simulate 10 failed login attempts
   - Verify lockout after 5 attempts
   - Verify login_attempts table logging

---

### **Step 6: Production Deployment** (1 hour)

**Checklist**:

1. **Environment Variables**:
```bash
# Add to production .env
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_HPew14Rbn
COGNITO_APP_CLIENT_ID=2t9sms0kmd85huog79fqpslc2u
COGNITO_APP_CLIENT_SECRET=<from /tmp/cognito_client_secret.txt>
COGNITO_JWKS_URL=https://cognito-idp.us-east-2.amazonaws.com/us-east-2_HPew14Rbn/.well-known/jwks.json
```

2. **Database Migration**:
```bash
# Connect to production
export DATABASE_URL="postgresql://owkai_admin:${DB_REDACTED-CREDENTIAL}@owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com:5432/owkai_pilot"

# Create production backup
aws rds create-db-snapshot \
  --db-instance-identifier owkai-pilot-db \
  --db-snapshot-identifier "pre-phase2-cognito-$(date +%Y%m%d-%H%M%S)" \
  --region us-east-2

# Run migration
alembic upgrade head

# Validate
psql -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
     -U owkai_admin -d owkai_pilot \
     -c "SELECT COUNT(*) FROM login_attempts, auth_audit_log, cognito_tokens;"
```

3. **Deploy Backend**:
```bash
# Update ECS task definition with new environment variables
# Deploy via GitHub Actions or manual push
```

4. **Smoke Tests**:
   - ✅ Health check endpoint responds
   - ✅ Cognito login flow works
   - ✅ API key authentication still works (backward compatibility)
   - ✅ RLS policies enforce isolation
   - ✅ Audit logs are being written

---

## 📊 ESTIMATED TIMELINE

| Task | Estimated Time | Priority |
|------|----------------|----------|
| **Cognito Middleware** | 2-3 hours | 🔴 Critical |
| **Organization Admin Routes** | 2 hours | 🟠 High |
| **Platform Admin Routes** | 2 hours | 🟠 High |
| **Update Models** | 30 minutes | 🟠 High |
| **Local Testing** | 1 hour | 🟡 Medium |
| **Production Deployment** | 1 hour | 🟡 Medium |
| **Total** | **8-10 hours** | - |

**Completion Date** (if starting now): 1-2 days

---

## 🎯 SUCCESS CRITERIA

Phase 2 complete when:
- ✅ All middleware functions implemented with enterprise security
- ✅ Organization admin can invite/manage users via Cognito
- ✅ Platform admin can view all organizations (metadata only)
- ✅ Dual authentication working (Cognito + API keys)
- ✅ All 18 local tests passing
- ✅ Production migration successful
- ✅ Zero downtime deployment
- ✅ Evidence documented with screenshots/logs

---

## 🔐 SECURITY CHECKLIST

- ✅ JWT signature verification (RS256)
- ✅ Complete claim validation (iss, aud, exp, nbf, token_use)
- ✅ Token revocation support
- ✅ Brute force detection (5 failed attempts = lockout)
- ✅ Complete audit trail (every auth event logged)
- ✅ RLS enforcement (database-level)
- ✅ Input validation (Pydantic + bleach)
- ✅ Rate limiting (per-tier)
- ✅ Security headers (CORS, CSP, HSTS, etc.)
- ✅ Constant-time API key comparison

---

**Status**: Ready to proceed with Step 1 (Cognito Middleware Implementation)

**Next Action**: Create `/ow-ai-backend/dependencies_cognito.py` with enterprise-grade JWT validation

---
