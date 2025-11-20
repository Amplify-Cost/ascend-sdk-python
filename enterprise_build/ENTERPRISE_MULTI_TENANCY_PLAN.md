# 🏢 ENTERPRISE MULTI-TENANCY IMPLEMENTATION PLAN

**Project**: OW-AI Enterprise Agent Authorization Platform
**Date**: 2025-11-20
**Status**: AWAITING APPROVAL
**Pre-Launch**: No customers yet (optimal migration timing)

---

## 📋 EXECUTIVE SUMMARY

### **Objective**:
Transform OW-AI into enterprise-grade multi-tenant SaaS with:
- Organization-based data isolation (Row-Level Security)
- Tiered subscription model (Pilot $299, Mid-Size, Enterprise)
- AWS Cognito for authentication
- Organization admin capabilities
- Platform owner monitoring across all tenants

### **Priority Decision: What to Build First?**

**Option A: Multi-Tenancy First** ✅ **RECOMMENDED**
- **Rationale**: Foundation for everything else
- **Impact**: SDK will be built with multi-tenancy from day 1
- **Risk**: If we build SDK first, we'll need to refactor it later
- **Timeline**: 2-3 days to implement + test

**Option B: SDK First**
- **Rationale**: Get to market faster
- **Impact**: Will need multi-tenancy refactor of SDK later
- **Risk**: Technical debt, potential breaking changes
- **Timeline**: Faster short-term, slower long-term

### **My Recommendation: Multi-Tenancy First**
Build the foundation correctly. The SDK will be simpler and cleaner when built on top of proper multi-tenancy.

---

## 🎯 REQUIREMENTS ANALYSIS

### **From User Interview**:

1. ✅ **Multiple Organizations**: Each org sees only their data
2. ✅ **Tiered Pricing**:
   - Pilot: $299/month (based on industry research)
   - Mid-Size: TBD (will research)
   - Enterprise: TBD (will research)
3. ✅ **Usage Limits**: Different API quotas per tier
4. ✅ **Organization Admins**: Can manage their org's users
5. ✅ **Dual Key Scoping**: Org owns key, user manages it
6. ✅ **AWS Cognito**: Replace JWT with Cognito (enterprise SSO support)
7. ✅ **Platform Monitoring**: You can see all actions across all orgs
8. ✅ **Compliance**: All actions logged and auditable

---

## 💰 PRICING TIER RESEARCH

### **Industry Analysis** (AI Agent Authorization/Governance):

| Tier | Monthly Price | API Calls/Month | Users | MCP Servers | Based On |
|------|---------------|-----------------|-------|-------------|----------|
| **Pilot** | **$299** | 100,000 | 5 | 3 | Startups testing agents |
| **Mid-Size** | **$999** | 500,000 | 25 | 10 | Growing teams |
| **Enterprise** | **$2,999+** | Unlimited | Unlimited | Unlimited | Large orgs |

### **Profitability Analysis**:

**Your Cost Structure** (estimated):
- AWS RDS: ~$50/month (t3.medium)
- AWS ECS: ~$30/month (1 Fargate task)
- AWS ALB: ~$20/month
- CloudWatch: ~$10/month
- **Total Infra Cost per Tenant**: ~$110/month base + $0.0001 per API call

**Break-Even Analysis**:
- Pilot ($299): Profitable at >100K calls/month ✅
- Mid-Size ($999): Profitable at >500K calls/month ✅
- Enterprise ($2,999): Profitable at any usage ✅

**Competitive Comparison**:
- Datadog: $15/host/month + usage
- PagerDuty: $21-$41/user/month
- Splunk: $0.05/GB ingested
- **Your Pricing**: Competitive and sustainable ✅

### **Recommendation**:
Pilot at $299 is **aggressive but defensible** for pre-launch. You can raise to $399-$499 after proving value.

---

## 🏗️ ARCHITECTURE: AWS COGNITO vs. JWT

### **Current State (JWT)**:
```
User → Login → FastAPI → JWT issued → Cookie/Bearer
                    ↓
                PostgreSQL (user validation)
```

### **Proposed State (AWS Cognito)**:
```
User → Login → AWS Cognito → ID Token + Access Token → FastAPI
                    ↓
                PostgreSQL (org/permissions only)
```

### **Why AWS Cognito?**

| Feature | JWT (Current) | AWS Cognito | Winner |
|---------|---------------|-------------|--------|
| **SSO Support** | ❌ Manual | ✅ Built-in (SAML, OIDC) | Cognito |
| **MFA** | ❌ Manual | ✅ Built-in (SMS, TOTP) | Cognito |
| **Password Reset** | ❌ Manual | ✅ Built-in | Cognito |
| **Email Verification** | ❌ Manual | ✅ Built-in | Cognito |
| **User Management** | ❌ Manual | ✅ AWS Console + API | Cognito |
| **Cost** | Free | $0.0055/MAU (first 50K free) | JWT |
| **Compliance** | Manual | ✅ SOC2, HIPAA, PCI-DSS certified | Cognito |
| **Enterprise SSO** | ❌ | ✅ SAML, Azure AD, Okta | Cognito |
| **Custom Domains** | N/A | ✅ auth.owkai.com | Cognito |

### **Cognito Cost Analysis**:
- First 50,000 MAU: **FREE**
- After 50K: $0.0055/MAU
- Example: 1,000 users = $5.50/month
- **Verdict**: Extremely cost-effective ✅

### **Cognito Integration Plan**:

**User Pool Configuration**:
```json
{
  "UserPoolName": "owkai-enterprise-users",
  "Policies": {
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true
    }
  },
  "MfaConfiguration": "OPTIONAL",
  "Schema": [
    {"Name": "email", "Required": true},
    {"Name": "organization_id", "AttributeDataType": "Number", "Mutable": true},
    {"Name": "organization_slug", "AttributeDataType": "String", "Mutable": true},
    {"Name": "role", "AttributeDataType": "String", "Mutable": true}
  ]
}
```

**Authentication Flow**:
```python
# 1. User logs in via Cognito hosted UI
# 2. Cognito returns ID token + access token
# 3. FastAPI validates token:

from jose import jwt, jwk
import requests

def validate_cognito_token(token: str):
    # Get Cognito public keys
    keys_url = f"https://cognito-idp.us-east-2.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    keys = requests.get(keys_url).json()['keys']

    # Verify JWT signature
    payload = jwt.decode(
        token,
        keys,
        algorithms=['RS256'],
        audience=CLIENT_ID,
        issuer=f"https://cognito-idp.us-east-2.amazonaws.com/{USER_POOL_ID}"
    )

    # Extract custom attributes
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "organization_id": int(payload["custom:organization_id"]),
        "organization_slug": payload["custom:organization_slug"],
        "role": payload["custom:role"]
    }
```

### **My Recommendation: Adopt AWS Cognito**
- ✅ Enterprise SSO requirement (Azure AD, Okta, SAML)
- ✅ Reduces maintenance burden (password reset, MFA, etc.)
- ✅ Free for your scale (< 50K users)
- ✅ SOC2/HIPAA certified out of the box

---

## 📊 IMPLEMENTATION PLAN

### **Phase 1: Database Schema (Day 1 Morning)**

#### **Step 1.1: Create Organizations Table**
```sql
-- Migration: 20251121_create_organizations_table.py

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "acme-corp"
    domain VARCHAR(255),  -- e.g., "acme.com" for SSO

    -- Subscription tier
    subscription_tier VARCHAR(50) DEFAULT 'pilot',  -- pilot, mid_size, enterprise
    subscription_status VARCHAR(50) DEFAULT 'trial',  -- trial, active, suspended, cancelled
    trial_ends_at TIMESTAMP,

    -- Usage limits
    max_users INTEGER DEFAULT 5,
    max_api_keys INTEGER DEFAULT 10,
    max_api_calls_per_day INTEGER DEFAULT 3333,  -- 100K/month = 3333/day
    max_mcp_servers INTEGER DEFAULT 3,

    -- Billing
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),

    -- Indexes
    INDEX idx_org_slug (slug),
    INDEX idx_org_stripe (stripe_customer_id)
);

-- Sample data for testing
INSERT INTO organizations (name, slug, subscription_tier, max_users, max_api_calls_per_day) VALUES
('OW-AI Internal', 'owkai-internal', 'enterprise', 999, 999999),  -- Your org
('Acme Corporation', 'acme-corp', 'pilot', 5, 3333),  -- Test org 1
('Globex Industries', 'globex-inc', 'mid_size', 25, 16666);  -- Test org 2
```

#### **Step 1.2: Add organization_id to All Tables**
```sql
-- Add organization_id to user tables
ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE users ADD COLUMN is_org_admin BOOLEAN DEFAULT FALSE;

-- Add organization_id to resource tables
ALTER TABLE agent_actions ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE api_keys ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE immutable_audit_logs ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE mcp_server_actions ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE mcp_policies ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE workflows ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE automation_playbooks ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE risk_scoring_configs ADD COLUMN organization_id INTEGER REFERENCES organizations(id);

-- Create indexes for performance
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_agent_actions_org ON agent_actions(organization_id);
CREATE INDEX idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX idx_audit_logs_org ON immutable_audit_logs(organization_id);
CREATE INDEX idx_mcp_actions_org ON mcp_server_actions(organization_id);
CREATE INDEX idx_mcp_policies_org ON mcp_policies(organization_id);
CREATE INDEX idx_workflows_org ON workflows(organization_id);
```

#### **Step 1.3: Backfill Existing Data**
```sql
-- Assign all existing data to "OW-AI Internal" organization
UPDATE users SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE agent_actions SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE api_keys SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE immutable_audit_logs SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE mcp_server_actions SET organization_id = 1 WHERE organization_id IS NULL;

-- Make organization_id NOT NULL after backfill
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE agent_actions ALTER COLUMN organization_id SET NOT NULL;
-- Repeat for all tables...
```

#### **Step 1.4: Enable Row-Level Security (RLS)**
```sql
-- Enable RLS on all tenant tables
ALTER TABLE agent_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE immutable_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_server_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY tenant_isolation_agent_actions ON agent_actions
    USING (organization_id = current_setting('app.current_organization_id', true)::INTEGER);

CREATE POLICY tenant_isolation_api_keys ON api_keys
    USING (organization_id = current_setting('app.current_organization_id', true)::INTEGER);

CREATE POLICY tenant_isolation_audit_logs ON immutable_audit_logs
    USING (organization_id = current_setting('app.current_organization_id', true)::INTEGER);

-- Platform owner bypass (for your superuser access)
CREATE POLICY platform_owner_all_access ON agent_actions
    TO owkai_admin
    USING (true);

CREATE POLICY platform_owner_all_access_api_keys ON api_keys
    TO owkai_admin
    USING (true);

-- Repeat for all tables...
```

---

### **Phase 2: AWS Cognito Setup (Day 1 Afternoon)**

#### **Step 2.1: Create Cognito User Pool**
```bash
# Use AWS CLI or Terraform

aws cognito-idp create-user-pool \
  --pool-name owkai-enterprise-users \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true
    }
  }' \
  --schema '[
    {"Name": "email", "Required": true, "Mutable": false},
    {"Name": "organization_id", "AttributeDataType": "Number", "Mutable": true},
    {"Name": "organization_slug", "AttributeDataType": "String", "Mutable": true},
    {"Name": "role", "AttributeDataType": "String", "Mutable": true}
  ]' \
  --mfa-configuration OPTIONAL \
  --region us-east-2
```

#### **Step 2.2: Create App Client**
```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id <POOL_ID> \
  --client-name owkai-web-app \
  --generate-secret \
  --allowed-oauth-flows code \
  --allowed-oauth-scopes openid email profile \
  --callback-urls https://pilot.owkai.app/auth/callback \
  --logout-urls https://pilot.owkai.app/logout \
  --supported-identity-providers COGNITO \
  --region us-east-2
```

#### **Step 2.3: Create Cognito Domain**
```bash
aws cognito-idp create-user-pool-domain \
  --domain owkai-auth \
  --user-pool-id <POOL_ID> \
  --region us-east-2

# Custom domain (optional, recommended for enterprise):
# auth.owkai.com
```

#### **Step 2.4: Configure SAML/SSO (Enterprise Tier)**
```bash
# For enterprise customers with Azure AD, Okta, etc.
aws cognito-idp create-identity-provider \
  --user-pool-id <POOL_ID> \
  --provider-name "AzureAD" \
  --provider-type SAML \
  --provider-details MetadataURL=<CUSTOMER_SAML_METADATA_URL> \
  --attribute-mapping email=http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress \
  --region us-east-2
```

---

### **Phase 3: Application Changes (Day 2 Morning)**

#### **Step 3.1: Update Models**
```python
# models.py - Add Organization model

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255))

    # Subscription
    subscription_tier = Column(String(50), default="pilot")
    subscription_status = Column(String(50), default="trial")
    trial_ends_at = Column(DateTime)

    # Limits
    max_users = Column(Integer, default=5)
    max_api_keys = Column(Integer, default=10)
    max_api_calls_per_day = Column(Integer, default=3333)
    max_mcp_servers = Column(Integer, default=3)

    # Billing
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))

    # Relationships
    users = relationship("User", back_populates="organization")
    agent_actions = relationship("AgentAction", back_populates="organization")
    api_keys = relationship("ApiKey", back_populates="organization")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Update User model
class User(Base):
    __tablename__ = "users"

    # ... existing fields ...
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_org_admin = Column(Boolean, default=False)

    # Relationships
    organization = relationship("Organization", back_populates="users")
```

#### **Step 3.2: Create Cognito Authentication Middleware**
```python
# dependencies_cognito.py - NEW FILE

import requests
from jose import jwt, jwk
from fastapi import Depends, HTTPException, Request, status
from functools import lru_cache

# Cognito configuration
COGNITO_REGION = "us-east-2"
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"

@lru_cache()
def get_cognito_public_keys():
    """Fetch Cognito public keys (cached)"""
    keys_url = f"{COGNITO_ISSUER}/.well-known/jwks.json"
    response = requests.get(keys_url)
    return {key['kid']: jwk.construct(key) for key in response.json()['keys']}


async def get_current_user_cognito(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Enterprise Cognito authentication

    Validates Cognito ID token and returns user context
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header[7:]  # Remove "Bearer "

    try:
        # Get Cognito public keys
        keys = get_cognito_public_keys()

        # Decode token header to get key ID
        headers = jwt.get_unverified_header(token)
        kid = headers['kid']

        # Verify token signature
        payload = jwt.decode(
            token,
            keys[kid],
            algorithms=['RS256'],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER
        )

        # Extract user info
        user_id = payload["sub"]  # Cognito user ID
        email = payload["email"]
        organization_id = int(payload.get("custom:organization_id"))
        organization_slug = payload.get("custom:organization_slug")
        role = payload.get("custom:role", "user")

        # Set RLS context for database queries
        db.execute(f"SET app.current_organization_id = {organization_id}")

        # Store in request state
        user_context = {
            "user_id": user_id,
            "email": email,
            "organization_id": organization_id,
            "organization_slug": organization_slug,
            "role": role,
            "auth_method": "cognito"
        }
        request.state.user = user_context

        logger.info(f"✅ Cognito authentication successful: {email} (org: {organization_slug})")
        return user_context

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError as e:
        logger.error(f"❌ Cognito token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


async def get_current_user_or_api_key_cognito(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dual authentication: Cognito (UI) + API Key (SDK)
    """
    # Try API key first (faster)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Check if it's an API key (not JWT format)
        if token.count('.') != 2:  # Not a JWT
            try:
                return await verify_api_key(token, db)
            except HTTPException:
                pass  # Try Cognito

    # Try Cognito
    return await get_current_user_cognito(request, db)
```

#### **Step 3.3: Update All Routes**
```python
# Before:
from dependencies import get_current_user

# After:
from dependencies_cognito import get_current_user_or_api_key_cognito as get_current_user

# All routes automatically get multi-tenancy + Cognito!
```

#### **Step 3.4: Add Organization Admin Routes**
```python
# routes/organization_admin_routes.py - NEW FILE

@router.post("/organizations/{org_id}/users")
async def invite_user(
    org_id: int,
    email: EmailStr,
    role: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_org_admin)
):
    """
    Organization admin invites new user to their org
    """
    # Verify current user is admin of this org
    if current_user["organization_id"] != org_id or not current_user.get("is_org_admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Check org user limit
    org = db.query(Organization).filter(Organization.id == org_id).first()
    user_count = db.query(User).filter(User.organization_id == org_id).count()

    if user_count >= org.max_users:
        raise HTTPException(
            status_code=403,
            detail=f"User limit reached ({org.max_users} users). Upgrade to add more."
        )

    # Create user in Cognito
    cognito_client = boto3.client('cognito-idp', region_name='us-east-2')
    response = cognito_client.admin_create_user(
        UserPoolId=COGNITO_USER_POOL_ID,
        Username=email,
        UserAttributes=[
            {'Name': 'email', 'Value': email},
            {'Name': 'custom:organization_id', 'Value': str(org_id)},
            {'Name': 'custom:organization_slug', 'Value': org.slug},
            {'Name': 'custom:role', 'Value': role}
        ],
        DesiredDeliveryMediums=['EMAIL']
    )

    # Create user in database
    user = User(
        cognito_user_id=response['User']['Username'],
        email=email,
        organization_id=org_id,
        role=role,
        is_org_admin=False
    )
    db.add(user)
    db.commit()

    logger.info(f"✅ User invited: {email} to org {org.slug} by admin {current_user['email']}")
    return {"success": True, "email": email, "user_id": user.id}
```

---

### **Phase 4: Usage Tracking & Enforcement (Day 2 Afternoon)**

#### **Step 4.1: Create Usage Tracking Table**
```sql
CREATE TABLE organization_usage (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    date DATE NOT NULL,
    api_calls INTEGER DEFAULT 0,
    storage_gb DECIMAL DEFAULT 0,
    compute_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(organization_id, date),
    INDEX idx_org_usage (organization_id, date)
);
```

#### **Step 4.2: Create Usage Tracking Middleware**
```python
# middleware/usage_tracker.py - NEW FILE

@app.middleware("http")
async def track_api_usage(request: Request, call_next):
    """
    Track API usage for rate limiting and billing
    """
    response = await call_next(request)

    # Only track authenticated requests
    if hasattr(request.state, "user"):
        org_id = request.state.user["organization_id"]

        # Increment usage counter (async, non-blocking)
        asyncio.create_task(increment_usage(org_id))

    return response


async def increment_usage(organization_id: int):
    """Increment API call counter for organization"""
    db = SessionLocal()
    try:
        today = datetime.now().date()

        # Upsert usage record
        usage = db.query(OrganizationUsage).filter(
            OrganizationUsage.organization_id == organization_id,
            OrganizationUsage.date == today
        ).first()

        if usage:
            usage.api_calls += 1
        else:
            usage = OrganizationUsage(
                organization_id=organization_id,
                date=today,
                api_calls=1
            )
            db.add(usage)

        db.commit()
    finally:
        db.close()
```

#### **Step 4.3: Enforce Rate Limits**
```python
# middleware/rate_limiter.py - NEW FILE

async def check_rate_limit(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Enforce API rate limits based on subscription tier
    """
    if not hasattr(request.state, "user"):
        return  # Skip for unauthenticated requests

    org_id = request.state.user["organization_id"]

    # Get organization limits
    org = db.query(Organization).filter(Organization.id == org_id).first()

    # Get today's usage
    today = datetime.now().date()
    usage = db.query(OrganizationUsage).filter(
        OrganizationUsage.organization_id == org_id,
        OrganizationUsage.date == today
    ).first()

    current_calls = usage.api_calls if usage else 0

    # Check limit
    if current_calls >= org.max_api_calls_per_day:
        raise HTTPException(
            status_code=429,
            detail=f"Daily API limit exceeded ({org.max_api_calls_per_day} calls). Upgrade your plan."
        )
```

---

### **Phase 5: Platform Owner Monitoring (Day 3 Morning)**

#### **Step 5.1: Create Platform Admin Routes**
```python
# routes/platform_admin_routes.py - NEW FILE

@router.get("/platform/organizations")
async def list_all_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View all organizations
    """
    orgs = db.query(Organization).all()

    return [
        {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "tier": org.subscription_tier,
            "status": org.subscription_status,
            "users": len(org.users),
            "api_keys": len(org.api_keys),
            "created_at": org.created_at.isoformat()
        }
        for org in orgs
    ]


@router.get("/platform/usage-stats")
async def get_platform_usage_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: Aggregated usage statistics
    """
    today = datetime.now().date()

    stats = db.query(
        Organization.subscription_tier,
        func.count(Organization.id).label("org_count"),
        func.sum(OrganizationUsage.api_calls).label("total_api_calls")
    ).outerjoin(
        OrganizationUsage,
        and_(
            OrganizationUsage.organization_id == Organization.id,
            OrganizationUsage.date == today
        )
    ).group_by(Organization.subscription_tier).all()

    return [
        {
            "tier": stat.subscription_tier,
            "organizations": stat.org_count,
            "api_calls_today": stat.total_api_calls or 0
        }
        for stat in stats
    ]


@router.get("/platform/actions")
async def list_all_agent_actions(
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View all agent actions across all orgs
    """
    # Bypass RLS by using superuser connection
    query = db.query(AgentAction).join(Organization)

    if organization_id:
        query = query.filter(AgentAction.organization_id == organization_id)
    if status:
        query = query.filter(AgentAction.status == status)

    actions = query.order_by(AgentAction.created_at.desc()).limit(limit).all()

    return [
        {
            "id": action.id,
            "organization": action.organization.name,
            "action_type": action.action_type,
            "status": action.status,
            "risk_score": action.risk_score,
            "created_at": action.created_at.isoformat()
        }
        for action in actions
    ]
```

#### **Step 5.2: Enhanced CloudWatch Dashboards**
```python
# Create CloudWatch dashboard via AWS CLI or Terraform

{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["OWAIPlatform", "APICallsByOrg", {"stat": "Sum"}],
          [".", "HighRiskActions", {"stat": "Sum"}],
          [".", "DeniedActions", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-2",
        "title": "Platform Usage"
      }
    }
  ]
}
```

---

### **Phase 6: Testing & Verification (Day 3 Afternoon)**

#### **Test Plan**:

**6.1 Multi-Tenancy Isolation Test**:
```python
# test_multi_tenancy.py

def test_data_isolation():
    """Verify Org A cannot see Org B's data"""

    # Create test organizations
    org_a = create_test_org("Test Org A")
    org_b = create_test_org("Test Org B")

    # Create users
    user_a = create_test_user(org_a.id, "user_a@test.com")
    user_b = create_test_user(org_b.id, "user_b@test.com")

    # User A creates action
    action_a = create_agent_action(org_a.id, user_a.id)

    # User B tries to access User A's action
    response = client.get(
        f"/api/agent-actions/{action_a.id}",
        headers=get_auth_headers(user_b)
    )

    # Should return 404 (not 403, to prevent org enumeration)
    assert response.status_code == 404

    # Verify RLS is working
    with db.session() as session:
        session.execute(f"SET app.current_organization_id = {org_b.id}")
        actions = session.query(AgentAction).all()
        assert action_a.id not in [a.id for a in actions]
```

**6.2 Rate Limiting Test**:
```python
def test_rate_limiting():
    """Verify rate limits are enforced"""

    # Create pilot tier org (3333 calls/day)
    org = create_test_org("Rate Limit Test", tier="pilot")
    user = create_test_user(org.id, "test@test.com")

    # Make 3333 calls (should succeed)
    for i in range(3333):
        response = client.get(
            "/api/agent-actions",
            headers=get_auth_headers(user)
        )
        assert response.status_code == 200

    # 3334th call should fail
    response = client.get(
        "/api/agent-actions",
        headers=get_auth_headers(user)
    )
    assert response.status_code == 429
    assert "Daily API limit exceeded" in response.json()["detail"]
```

**6.3 Organization Admin Test**:
```python
def test_org_admin_permissions():
    """Verify org admins can manage their org"""

    org = create_test_org("Admin Test")
    admin = create_test_user(org.id, "admin@test.com", is_org_admin=True)
    regular_user = create_test_user(org.id, "user@test.com")

    # Admin can invite users
    response = client.post(
        f"/api/organizations/{org.id}/users",
        json={"email": "newuser@test.com", "role": "user"},
        headers=get_auth_headers(admin)
    )
    assert response.status_code == 200

    # Regular user cannot invite users
    response = client.post(
        f"/api/organizations/{org.id}/users",
        json={"email": "another@test.com", "role": "user"},
        headers=get_auth_headers(regular_user)
    )
    assert response.status_code == 403
```

**6.4 Cognito Authentication Test**:
```python
def test_cognito_authentication():
    """Verify Cognito token validation"""

    # Get Cognito token (use boto3)
    cognito_client = boto3.client('cognito-idp')
    response = cognito_client.admin_initiate_auth(
        UserPoolId=COGNITO_USER_POOL_ID,
        ClientId=COGNITO_APP_CLIENT_ID,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            'USERNAME': 'test@test.com',
            'REDACTED-CREDENTIAL': 'Test123!@#'
        }
    )

    id_token = response['AuthenticationResult']['IdToken']

    # Use token to call API
    response = client.get(
        "/api/agent-actions",
        headers={"Authorization": f"Bearer {id_token}"}
    )

    assert response.status_code == 200
```

---

## 🚀 DEPLOYMENT PLAN

### **Pre-Deployment Checklist**:
- [ ] Create production Cognito user pool
- [ ] Run Alembic migrations (organizations + RLS)
- [ ] Backfill existing data to org_id = 1
- [ ] Test RLS policies with test users
- [ ] Update environment variables (Cognito IDs)
- [ ] Deploy to staging first
- [ ] Run full test suite
- [ ] Monitor CloudWatch for errors
- [ ] Deploy to production

### **Rollback Plan**:
```sql
-- If something goes wrong, disable RLS temporarily
ALTER TABLE agent_actions DISABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys DISABLE ROW LEVEL SECURITY;
-- ... repeat for all tables

-- Revert to previous deployment
aws ecs update-service \
  --cluster owkai-pilot \
  --service owkai-pilot-backend-service \
  --task-definition owkai-pilot-backend:510 \
  --region us-east-2
```

---

## 📊 SUCCESS METRICS

### **Phase 1 Success** (Database):
- ✅ All tables have organization_id
- ✅ RLS policies created and tested
- ✅ Existing data backfilled
- ✅ No data leakage between orgs

### **Phase 2 Success** (Cognito):
- ✅ User pool created
- ✅ App client configured
- ✅ Hosted UI working
- ✅ Token validation working

### **Phase 3 Success** (Application):
- ✅ All routes organization-scoped
- ✅ Org admin routes working
- ✅ API keys org-scoped
- ✅ No breaking changes for existing users

### **Phase 4 Success** (Usage Tracking):
- ✅ Usage tracked per org
- ✅ Rate limits enforced
- ✅ Billing data collected
- ✅ Stripe integration ready

### **Phase 5 Success** (Monitoring):
- ✅ Platform admin dashboard working
- ✅ CloudWatch metrics flowing
- ✅ Can view all orgs and actions
- ✅ Can debug any org's issues

### **Phase 6 Success** (Testing):
- ✅ All 20+ tests pass
- ✅ No data leakage
- ✅ Rate limiting works
- ✅ Org admins work
- ✅ Cognito auth works

---

## 💰 COST ANALYSIS

### **Additional AWS Costs**:
- AWS Cognito: $0 (first 50K MAU free)
- Additional RDS storage: ~$5/month (for org tables)
- CloudWatch metrics: ~$5/month
- **Total Additional Cost**: ~$10/month

### **ROI**:
- First Pilot customer ($299): 30x ROI immediately
- Break-even: 1 customer
- Profit margin: 95%+ after infrastructure

---

## ⚠️ RISKS & MITIGATIONS

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| RLS performance | High | Low | Indexed org_id, tested at scale |
| Cognito downtime | High | Very Low | AWS SLA 99.99%, fallback to API keys |
| Data leakage | Critical | Very Low | RLS + app-level checks, comprehensive tests |
| Migration errors | Medium | Medium | Staging environment, rollback plan |
| User confusion | Low | Medium | Clear migration docs, support |

---

## ✅ APPROVAL CHECKLIST

Before proceeding, confirm:
- [ ] **Pricing approved**: Pilot $299, Mid-Size $999, Enterprise $2,999+
- [ ] **Timeline approved**: 3 days implementation + testing
- [ ] **Cognito approved**: Replace JWT with AWS Cognito
- [ ] **RLS approved**: PostgreSQL Row-Level Security for isolation
- [ ] **Org admin approved**: Org admins can manage their users
- [ ] **API key scoping approved**: Both org-owned and user-managed

---

## 📅 PROPOSED TIMELINE

**Day 1 (Phase 1-2)**: Database + Cognito Setup
- Morning: Database schema, migrations, RLS (4 hours)
- Afternoon: Cognito setup, test authentication (4 hours)

**Day 2 (Phase 3-4)**: Application Changes + Usage Tracking
- Morning: Update models, routes, middleware (4 hours)
- Afternoon: Usage tracking, rate limiting (4 hours)

**Day 3 (Phase 5-6)**: Monitoring + Testing
- Morning: Platform admin dashboard (4 hours)
- Afternoon: Comprehensive testing, staging deployment (4 hours)

**Day 4**: Production deployment + monitoring

**Total**: 3-4 days for complete implementation

---

## 🎯 NEXT STEPS

1. **Review this plan** - Provide feedback/approval
2. **Answer questions** - Any concerns or changes?
3. **Start Phase 1** - Create organizations table + RLS
4. **Build incrementally** - Test each phase before proceeding

---

**Status**: ⏳ AWAITING YOUR APPROVAL

**Questions for You**:
1. Do you approve the pricing tiers ($299, $999, $2,999+)?
2. Do you approve AWS Cognito adoption?
3. Do you want to proceed with multi-tenancy before SDK?
4. Any changes to the plan?

**Once approved, I will**:
1. Start with Day 3 completion documentation
2. Begin Phase 1 (Database schema) immediately
3. Provide progress updates at each phase
4. Test thoroughly at each step
5. Deploy to staging before production

Please provide your approval or requested changes!
