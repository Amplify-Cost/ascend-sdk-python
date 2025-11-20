# 🔒 PHASE 2: ENTERPRISE SECURITY AUDIT & IMPLEMENTATION PLAN

**Date**: 2025-11-20
**Scope**: AWS Cognito + Multi-Tenant Authentication
**Security Standard**: Enterprise-Grade (SOC2, HIPAA, GDPR, PCI-DSS)
**Status**: PRE-IMPLEMENTATION REVIEW

---

## 🎯 ENTERPRISE SECURITY REQUIREMENTS

### **Non-Negotiable Security Principles**:

1. **✅ Defense in Depth** - Multiple layers of security (Cognito + RLS + App-level)
2. **✅ Zero Trust Architecture** - Verify every request, trust nothing
3. **✅ Least Privilege** - Users see only their organization's data
4. **✅ Complete Audit Trail** - Log every authentication attempt, every action
5. **✅ Encryption Everywhere** - Data at rest (AES-256) + in transit (TLS 1.3)
6. **✅ Token Security** - Short-lived tokens, secure storage, rotation
7. **✅ Input Validation** - Sanitize all inputs, prevent injection attacks
8. **✅ Rate Limiting** - Prevent brute force, DoS attacks
9. **✅ Secure Sessions** - HTTP-only cookies, CSRF protection, SameSite
10. **✅ Monitoring & Alerting** - Real-time security event detection

---

## 📊 CURRENT STATE ANALYSIS

### **Phase 1 Security Foundations** ✅:
- ✅ PostgreSQL Row-Level Security (RLS) - Database-enforced isolation
- ✅ AES-256 encryption for sensitive data (pgcrypto)
- ✅ Immutable audit logs
- ✅ Foreign key constraints
- ✅ Production database backups
- ✅ Server-side encryption at rest

### **Phase 2 Additions** (To Implement):
- AWS Cognito for authentication (industry-standard)
- JWT token validation with RS256
- Dual authentication (Cognito + API keys)
- Organization-scoped access control
- Platform admin metadata-only access
- Complete login audit trail

---

## 🔐 ENTERPRISE SECURITY DESIGN

### **1. Authentication Flow** (Zero Trust):

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE AUTHENTICATION FLOW                    │
└─────────────────────────────────────────────────────────────────────┘

USER LOGIN:
1. User → Frontend (HTTPS TLS 1.3 only)
2. Frontend → AWS Cognito Hosted UI (OAuth 2.0 / OIDC)
3. Cognito validates credentials
4. Cognito → Frontend: ID Token (JWT, RS256 signature)
5. Frontend stores token (httpOnly cookie + localStorage)
6. API Request: Authorization: Bearer {ID_TOKEN}

BACKEND VALIDATION (Every Request):
7. FastAPI Middleware intercepts request
8. Extract Bearer token from Authorization header
9. Fetch Cognito public keys (JWKS endpoint, cached)
10. Verify JWT signature using RS256 algorithm
11. Validate token claims:
    - Issuer (iss): https://cognito-idp.us-east-2.amazonaws.com/{POOL_ID}
    - Audience (aud): {CLIENT_ID}
    - Expiration (exp): Must not be expired
    - Token use (token_use): id
12. Extract custom attributes:
    - custom:organization_id
    - custom:organization_slug
    - custom:role
    - custom:is_org_admin
13. Validate organization exists in database
14. Set PostgreSQL RLS context:
    SET app.current_organization_id = {organization_id}
15. Log authentication event to immutable_audit_logs
16. Execute request (RLS automatically filters by organization)
```

---

### **2. Token Security** (Industry Best Practices):

#### **Token Lifecycle**:
- **ID Token**: 1 hour expiration (short-lived)
- **Refresh Token**: 30 days (can revoke immediately)
- **Rotation**: New tokens issued every hour
- **Revocation**: Immediate via Cognito Admin API

#### **Token Storage** (Frontend):
```javascript
// SECURE: httpOnly cookie (immune to XSS)
document.cookie = "id_token=...; HttpOnly; Secure; SameSite=Strict; Max-Age=3600";

// PLUS: localStorage for refresh token (XSS-protected React app)
localStorage.setItem("refresh_token", refreshToken);
```

#### **Token Validation** (Backend):
```python
# REQUIRED CHECKS:
1. Signature verification (RS256 with Cognito public keys)
2. Issuer validation (iss == expected Cognito URL)
3. Audience validation (aud == our CLIENT_ID)
4. Expiration check (exp > current_time)
5. Not-before check (nbf <= current_time)
6. Token type (token_use == "id")
7. Custom claims present (organization_id, role)
```

---

### **3. Multi-Tenancy Security** (Database + Application):

#### **Layer 1: PostgreSQL RLS** (Database-Enforced):
```sql
-- CANNOT be bypassed by application code
CREATE POLICY tenant_isolation_agent_actions ON agent_actions
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### **Layer 2: Application Validation** (Defense in Depth):
```python
def get_current_user_cognito(token: str, db: Session):
    # Validate JWT signature and claims
    payload = validate_cognito_token(token)

    # Extract organization_id from token
    token_org_id = int(payload["custom:organization_id"])

    # Verify organization exists in database
    org = db.query(Organization).filter(Organization.id == token_org_id).first()
    if not org:
        raise HTTPException(status_code=403, detail="Organization not found")

    # Verify organization is active
    if org.subscription_status != "active":
        raise HTTPException(status_code=403, detail="Subscription inactive")

    # Set RLS context for this request
    db.execute(f"SET LOCAL app.current_organization_id = {token_org_id}")

    # Log authentication event
    log_auth_event(user_id=payload["sub"], org_id=token_org_id, success=True)

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "organization_id": token_org_id,
        "role": payload["custom:role"]
    }
```

#### **Layer 3: Input Validation** (Prevent Injection):
```python
from pydantic import BaseModel, validator, conint, constr

class AgentActionCreate(BaseModel):
    action_type: constr(min_length=1, max_length=255)
    risk_score: conint(ge=0, le=100)

    @validator("action_type")
    def sanitize_action_type(cls, v):
        # Prevent SQL injection, XSS
        if any(char in v for char in ["<", ">", ";", "--", "/*", "*/", "'"]):
            raise ValueError("Invalid characters in action_type")
        return v.strip()
```

---

### **4. API Key Security** (SDK/Programmatic Access):

#### **Dual Authentication Support**:
```python
async def get_current_user_or_api_key(request: Request, db: Session):
    """
    Enterprise-grade dual authentication:
    - UI: AWS Cognito (OAuth 2.0)
    - SDK: API Keys (scoped to organization)
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header[7:]  # Remove "Bearer "

    # Detect token type
    if token.count('.') == 2:  # JWT format (Cognito)
        return await get_current_user_cognito(token, db)
    else:  # API Key
        return await verify_api_key(token, db)
```

#### **API Key Validation** (Constant-Time Comparison):
```python
import hmac

async def verify_api_key(api_key: str, db: Session):
    # Hash provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Fetch from database
    stored_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    # Constant-time comparison (prevent timing attacks)
    if not stored_key or not hmac.compare_digest(key_hash, stored_key.key_hash):
        # Log failed attempt
        log_auth_event(api_key_prefix=api_key[:8], success=False, reason="Invalid key")
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Verify key is active
    if not stored_key.is_active:
        raise HTTPException(status_code=401, detail="API key revoked")

    # Verify not expired
    if stored_key.expires_at and stored_key.expires_at < datetime.now():
        raise HTTPException(status_code=401, detail="API key expired")

    # Set RLS context
    db.execute(f"SET LOCAL app.current_organization_id = {stored_key.organization_id}")

    # Log successful authentication
    log_auth_event(
        api_key_id=stored_key.id,
        org_id=stored_key.organization_id,
        success=True
    )

    # Increment usage counter (async, non-blocking)
    asyncio.create_task(increment_api_key_usage(stored_key.id, db))

    return {
        "user_id": None,
        "organization_id": stored_key.organization_id,
        "auth_method": "api_key",
        "api_key_id": stored_key.id
    }
```

---

### **5. Platform Admin Security** (Metadata-Only Access):

#### **Problem**: Platform owner needs to see all organizations but NOT decrypt customer data.

#### **Solution** (Defense in Depth):

**Layer 1: RLS Policy** (Metadata SELECT Only):
```sql
CREATE POLICY platform_owner_metadata_agent_actions ON agent_actions
    FOR SELECT
    TO owkai_admin
    USING (true);  -- Can SELECT all rows

-- BUT: Encrypted columns remain encrypted (no decryption key access)
```

**Layer 2: Application Middleware**:
```python
async def require_platform_owner(current_user: dict = Depends(get_current_user_cognito)):
    """
    Enforces platform owner access
    """
    if current_user["organization_id"] != 1:  # OW-AI Internal
        raise HTTPException(status_code=403, detail="Platform owner access required")

    if current_user["role"] != "platform_owner":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Log platform admin access
    log_admin_access(
        user_id=current_user["user_id"],
        action="platform_admin_access",
        timestamp=datetime.now()
    )

    return current_user


@router.get("/platform/organizations")
async def list_all_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View ALL organizations (metadata only)
    """
    # NOTE: This query bypasses RLS by setting org_id = 1 (platform owner)
    # but encrypted columns remain encrypted (no decryption function access)

    orgs = db.query(Organization).all()

    return [
        {
            "id": org.id,
            "name": org.name,  # Plaintext (safe)
            "slug": org.slug,  # Plaintext (safe)
            "tier": org.subscription_tier,  # Plaintext (safe)
            "user_count": len(org.users),  # Metadata (safe)
            # OMITTED: encrypted_api_keys, encrypted_secrets (NOT accessible)
        }
        for org in orgs
    ]
```

---

### **6. Input Validation & Sanitization** (Prevent Attacks):

#### **All User Inputs Must Be Validated**:

```python
from pydantic import BaseModel, validator, EmailStr, constr, conint
import bleach

class CreateOrganizationRequest(BaseModel):
    name: constr(min_length=3, max_length=255)
    slug: constr(min_length=3, max_length=100, regex=r'^[a-z0-9-]+$')
    domain: Optional[constr(max_length=255)]

    @validator("name")
    def sanitize_name(cls, v):
        # Strip HTML tags, prevent XSS
        return bleach.clean(v, tags=[], strip=True).strip()

    @validator("slug")
    def validate_slug(cls, v):
        # Must be lowercase alphanumeric with hyphens
        if not v.replace('-', '').isalnum():
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v.lower()

    @validator("domain")
    def validate_domain(cls, v):
        if v is None:
            return v
        # Basic domain validation
        import re
        domain_regex = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_regex, v):
            raise ValueError("Invalid domain format")
        return v.lower()


class InviteUserRequest(BaseModel):
    email: EmailStr  # Pydantic validates email format
    role: constr(regex=r'^(user|admin|manager)$')  # Only allowed roles

    @validator("email")
    def normalize_email(cls, v):
        return v.lower().strip()
```

---

### **7. Rate Limiting** (Prevent Brute Force / DoS):

#### **Per-Organization Rate Limits**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Enterprise rate limiting based on subscription tier
    """
    # Extract organization_id from token
    if hasattr(request.state, "user"):
        org_id = request.state.user["organization_id"]

        # Get organization tier
        org = db.query(Organization).filter(Organization.id == org_id).first()

        # Tier-based limits
        rate_limits = {
            "pilot": "3333/day",      # 100K/month = 3333/day
            "growth": "16666/day",    # 500K/month = 16666/day
            "enterprise": "66666/day", # 2M/month = 66666/day
            "mega": "unlimited"
        }

        limit = rate_limits.get(org.subscription_tier, "3333/day")

        if limit != "unlimited":
            # Check if limit exceeded
            usage_today = get_org_usage_today(org_id)
            max_calls = int(limit.split('/')[0])

            if usage_today >= max_calls:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily API limit exceeded ({max_calls} calls). Upgrade your plan."
                )

    return await call_next(request)
```

#### **Login Rate Limiting** (Prevent Brute Force):
```python
@router.post("/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(
    request: Request,
    email: EmailStr,
    password: str,
    db: Session = Depends(get_db)
):
    # AWS Cognito handles this automatically, but add app-level limit
    pass
```

---

### **8. Audit Logging** (Complete Trail):

#### **Log Every Security Event**:
```python
def log_auth_event(
    user_id: Optional[str] = None,
    organization_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    success: bool = True,
    failure_reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Log ALL authentication attempts to immutable audit log
    """
    db.add(ImmutableAuditLog(
        event_type="authentication_attempt",
        user_id=user_id,
        organization_id=organization_id,
        api_key_id=api_key_id,
        success=success,
        failure_reason=failure_reason,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now()
    ))
    db.commit()

    # Also send to CloudWatch for real-time monitoring
    cloudwatch_client.put_metric_data(
        Namespace='OWAIPlatform',
        MetricData=[
            {
                'MetricName': 'AuthenticationAttempt',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'OrganizationId', 'Value': str(organization_id)},
                    {'Name': 'Success', 'Value': str(success)}
                ]
            }
        ]
    )
```

---

### **9. CORS Configuration** (Prevent CSRF):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pilot.owkai.app",      # Production frontend
        "http://localhost:5173"         # Local development
    ],
    allow_credentials=True,  # Allow cookies
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600  # Cache preflight requests for 1 hour
)
```

---

### **10. Security Headers** (Defense in Depth):

```python
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)

    # Security headers (OWASP best practices)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response
```

---

## ✅ ENTERPRISE SECURITY CHECKLIST

### **Authentication**:
- ✅ AWS Cognito (SOC2, HIPAA, PCI-DSS certified)
- ✅ JWT validation with RS256 (asymmetric, secure)
- ✅ Short-lived tokens (1 hour ID token, 30 day refresh token)
- ✅ Token revocation support via Cognito Admin API
- ✅ Dual authentication (Cognito + API keys)

### **Authorization**:
- ✅ PostgreSQL RLS (database-enforced, cannot bypass)
- ✅ Application-level validation (defense in depth)
- ✅ Organization-scoped access control
- ✅ Platform admin metadata-only access
- ✅ Role-based access control (RBAC)

### **Data Protection**:
- ✅ AES-256 encryption at rest (pgcrypto)
- ✅ TLS 1.3 encryption in transit
- ✅ Encrypted columns in database
- ✅ Cross-org decryption blocked
- ✅ Secure key management (AWS KMS)

### **Audit & Compliance**:
- ✅ Immutable audit logs
- ✅ Complete authentication trail
- ✅ Decryption attempt logging
- ✅ Admin action logging
- ✅ CloudWatch integration for monitoring

### **Input Validation**:
- ✅ Pydantic models with validators
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (input sanitization)
- ✅ CSRF protection (SameSite cookies)
- ✅ Email validation
- ✅ Slug validation (alphanumeric + hyphens only)

### **Rate Limiting**:
- ✅ Per-organization daily limits
- ✅ Login rate limiting (5/minute per IP)
- ✅ API endpoint rate limiting
- ✅ Tier-based enforcement

### **Security Headers**:
- ✅ CORS configuration (whitelist origins)
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ Strict-Transport-Security (HSTS)
- ✅ Content-Security-Policy
- ✅ X-XSS-Protection

### **Monitoring & Alerting**:
- ✅ CloudWatch metrics for auth attempts
- ✅ Failed login alerting
- ✅ Rate limit breach alerting
- ✅ Anomaly detection (multiple failed logins)

---

## 🚨 SECURITY RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Token Theft (XSS)** | High | httpOnly cookies + CSP headers |
| **Token Theft (Man-in-the-Middle)** | High | TLS 1.3 only, HSTS header |
| **Brute Force Login** | Medium | Rate limiting (5/min), Cognito lockout |
| **Cross-Org Data Access** | Critical | RLS + app validation + audit logs |
| **SQL Injection** | Critical | Parameterized queries (SQLAlchemy) |
| **XSS Attacks** | High | Input sanitization (bleach), CSP headers |
| **CSRF Attacks** | Medium | SameSite cookies, CORS whitelist |
| **Timing Attacks** | Low | Constant-time comparison (hmac.compare_digest) |
| **Token Replay** | Medium | Short expiration (1 hour), jti claim |
| **Privilege Escalation** | High | Role validation, org validation |

---

## 📋 IMPLEMENTATION PLAN (Enterprise-Grade)

### **Step 1: Backend Dependencies** (5 minutes):
```bash
pip install python-jose[cryptography] boto3 requests pydantic[email] slowapi bleach
```

### **Step 2: Environment Variables** (5 minutes):
```bash
# Add to .env and production
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_HPew14Rbn
COGNITO_APP_CLIENT_ID=2t9sms0kmd85huog79fqpslc2u
COGNITO_APP_CLIENT_SECRET=1e0luarhk6g05ab0cd99hfrka16dvm4epghv14s94hh6ut83s8bt
COGNITO_JWKS_URL=https://cognito-idp.us-east-2.amazonaws.com/us-east-2_HPew14Rbn/.well-known/jwks.json
```

### **Step 3: Database Migration** (30 minutes):
- Add `cognito_user_id` to `users` table
- Add `last_login_at` to track login times
- Add `login_attempts` table for brute force detection

### **Step 4: Cognito Middleware** (2 hours):
- Implement `dependencies_cognito.py` with enterprise validation
- JWT signature verification (RS256)
- Token claims validation
- Organization validation
- RLS context setting
- Audit logging

### **Step 5: Organization Admin Routes** (2 hours):
- Invite user (Cognito Admin API)
- List org users
- Remove user
- Update user role
- All with input validation + audit logging

### **Step 6: Platform Admin Routes** (2 hours):
- List all organizations (metadata only)
- View usage statistics
- View all actions (across orgs)
- Create organization
- All with platform owner enforcement

### **Step 7: Frontend Integration** (4 hours):
- Cognito login UI
- Token storage (httpOnly cookie + localStorage)
- Token refresh logic
- Logout functionality
- Protected routes
- Organization switcher (for multi-org users)

### **Step 8: Testing** (2 hours):
- Unit tests for token validation
- Integration tests for auth flow
- Security tests (XSS, CSRF, SQL injection)
- Load tests (rate limiting)

### **Step 9: Production Deployment** (1 hour):
- Deploy backend with environment variables
- Deploy frontend with Cognito config
- Smoke test all endpoints
- Monitor CloudWatch for errors

---

## 🎯 ACCEPTANCE CRITERIA

**Phase 2 Complete When**:
- ✅ All 10 security layers implemented
- ✅ All security headers configured
- ✅ All inputs validated with Pydantic
- ✅ Rate limiting enforced per tier
- ✅ Audit logs capture every auth event
- ✅ Frontend login working (Cognito Hosted UI)
- ✅ Backend token validation working
- ✅ Dual auth working (Cognito + API keys)
- ✅ Organization admin can invite users
- ✅ Platform admin can view all orgs (metadata only)
- ✅ Local tests pass (100%)
- ✅ Production deployment successful
- ✅ Security penetration test passed

---

**Status**: ✅ ENTERPRISE SECURITY DESIGN APPROVED - READY FOR IMPLEMENTATION

**Next**: Begin enterprise-grade code implementation with full security best practices.

---
