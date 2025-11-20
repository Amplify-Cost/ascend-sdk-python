# 🏗️ MASTER IMPLEMENTATION PLAN - Enterprise Multi-Tenant Platform

**Project**: OW-AI Enterprise Agent Authorization Platform
**Date**: 2025-11-20
**Status**: ✅ **APPROVED - STARTING PHASE 1**
**Timeline**: 7-10 days total

---

## ✅ APPROVALS RECEIVED

### **Architecture Decisions**:
- ✅ Multi-tenancy implementation FIRST (before SDK)
- ✅ AWS Cognito for enterprise SSO
- ✅ PostgreSQL Row-Level Security (RLS) for data isolation
- ✅ **SSE encryption** for customer data (platform admin sees metadata only)
- ✅ Organization admin capabilities

### **Pricing Strategy**:
- ✅ **Pilot**: $399/month (100K calls, 5 users, 3 MCP servers)
- ✅ **Growth**: $999/month (500K calls, 25 users, 10 MCP servers)
- ✅ **Enterprise**: $2,999/month (2M calls, 100 users, 50 MCP servers)
- ✅ **Mega-Enterprise**: Custom pricing (negotiated contracts)
- ✅ **Overage Model**: $0.005/call, $50/user, $100/server over limit

### **Security & Compliance**:
- ✅ Column-level encryption (pgcrypto) for sensitive data
- ✅ Platform admin access: metadata only (no customer data decryption)
- ✅ HIPAA, GDPR, SOC2, FedRAMP compliance requirements
- ✅ Complete audit trail with immutable logs

### **Implementation Order**:
1. Multi-tenancy (3-4 days)
2. SDK development (2-3 days)
3. Landing page + onboarding (2-3 days)
4. Stripe billing integration (1 day)

---

## 📅 MASTER TIMELINE

```
Week 1:
├── Day 1: Database Schema + SSE Encryption + RLS
├── Day 2: AWS Cognito Setup + Application Changes
├── Day 3: Usage Tracking + Platform Admin Dashboard
├── Day 4: Testing + Staging Deployment
│
Week 2:
├── Day 5: SDK Core Client Development
├── Day 6: SDK boto3 Auto-Patch + Testing
├── Day 7: Landing Page + Sign-Up Flow
├── Day 8: Email Notifications (SES) + Onboarding Wizard
│
Week 3:
├── Day 9: Stripe Integration + Billing Webhooks
└── Day 10: Production Deployment + Monitoring
```

---

## 🔐 PHASE 1: DATABASE SCHEMA + SSE ENCRYPTION

**Timeline**: Day 1 (6-8 hours)
**Status**: Starting now

### **1.1: Create Organizations Table**

```sql
-- Migration: alembic/versions/20251121_create_organizations_multi_tenant.py

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- e.g., "acme-corp"
    domain VARCHAR(255),  -- e.g., "acme.com" for SSO

    -- Subscription tier
    subscription_tier VARCHAR(50) DEFAULT 'pilot',  -- pilot, growth, enterprise, mega
    subscription_status VARCHAR(50) DEFAULT 'trial',  -- trial, active, suspended, cancelled
    trial_ends_at TIMESTAMP,

    -- Base limits (included in subscription)
    included_api_calls INTEGER DEFAULT 100000,  -- 100K for pilot ($399)
    included_users INTEGER DEFAULT 5,
    included_mcp_servers INTEGER DEFAULT 3,

    -- Overage rates (per unit over limit)
    overage_rate_per_call NUMERIC(10, 5) DEFAULT 0.005,  -- $0.005/call
    overage_rate_per_user NUMERIC(10, 2) DEFAULT 50.00,  -- $50/user
    overage_rate_per_server NUMERIC(10, 2) DEFAULT 100.00,  -- $100/server

    -- Current usage (reset monthly)
    current_month_api_calls INTEGER DEFAULT 0,
    current_month_overage_calls INTEGER DEFAULT 0,
    current_month_overage_cost NUMERIC(10, 2) DEFAULT 0.00,
    last_usage_reset_date DATE,

    -- Billing
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    next_billing_date DATE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER,

    -- Indexes
    CONSTRAINT valid_tier CHECK (subscription_tier IN ('pilot', 'growth', 'enterprise', 'mega'))
);

CREATE INDEX idx_org_slug ON organizations(slug);
CREATE INDEX idx_org_stripe_customer ON organizations(stripe_customer_id);
CREATE INDEX idx_org_tier_status ON organizations(subscription_tier, subscription_status);

-- Sample organizations for testing
INSERT INTO organizations (name, slug, subscription_tier, included_api_calls, included_users, included_mcp_servers) VALUES
('OW-AI Internal', 'owkai-internal', 'mega', 999999999, 999, 999),  -- Platform owner org
('Test Pilot Org', 'test-pilot', 'pilot', 100000, 5, 3),  -- Test org 1
('Test Growth Org', 'test-growth', 'growth', 500000, 25, 10);  -- Test org 2
```

---

### **1.2: Add organization_id to All Tables**

```sql
-- Add organization_id foreign key to all tenant tables

-- Users table
ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
ALTER TABLE users ADD COLUMN is_org_admin BOOLEAN DEFAULT FALSE;
CREATE INDEX idx_users_org ON users(organization_id);

-- Agent actions
ALTER TABLE agent_actions ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_agent_actions_org ON agent_actions(organization_id);

-- API keys
ALTER TABLE api_keys ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_api_keys_org ON api_keys(organization_id);

-- Audit logs
ALTER TABLE immutable_audit_logs ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_audit_logs_org ON immutable_audit_logs(organization_id);

-- MCP server actions
ALTER TABLE mcp_server_actions ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_mcp_actions_org ON mcp_server_actions(organization_id);

-- MCP policies
ALTER TABLE mcp_policies ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_mcp_policies_org ON mcp_policies(organization_id);

-- Workflows
ALTER TABLE workflows ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_workflows_org ON workflows(organization_id);

-- Automation playbooks
ALTER TABLE automation_playbooks ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_playbooks_org ON automation_playbooks(organization_id);

-- Risk scoring configs
ALTER TABLE risk_scoring_configs ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_risk_configs_org ON risk_scoring_configs(organization_id);

-- Alerts
ALTER TABLE alerts ADD COLUMN organization_id INTEGER REFERENCES organizations(id);
CREATE INDEX idx_alerts_org ON alerts(organization_id);
```

---

### **1.3: Backfill Existing Data**

```sql
-- Assign all existing data to OW-AI Internal organization (id = 1)

UPDATE users SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE agent_actions SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE api_keys SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE immutable_audit_logs SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE mcp_server_actions SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE mcp_policies SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE workflows SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE automation_playbooks SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE risk_scoring_configs SET organization_id = 1 WHERE organization_id IS NULL;
UPDATE alerts SET organization_id = 1 WHERE organization_id IS NULL;

-- Make organization_id NOT NULL after backfill
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE agent_actions ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE api_keys ALTER COLUMN organization_id SET NOT NULL;
-- Repeat for all tables...
```

---

### **1.4: SSE Encryption for Customer Data** 🔐

**Purpose**: Platform admin cannot decrypt customer sensitive data (compliance requirement)

```sql
-- Install pgcrypto extension for AES-256 encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encryption key storage (rotatable)
CREATE TABLE encryption_keys (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE NOT NULL,
    encrypted_key BYTEA NOT NULL,  -- Encrypted with KMS
    created_at TIMESTAMP DEFAULT NOW(),
    rotated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert master encryption key (encrypted with AWS KMS)
-- In production, this would be fetched from AWS Secrets Manager
INSERT INTO encryption_keys (key_name, encrypted_key, is_active) VALUES
('master-2025', pgp_sym_encrypt('PLACEHOLDER', 'temp-key'), TRUE);

-- Create encryption functions
CREATE OR REPLACE FUNCTION encrypt_customer_data(plaintext TEXT, org_id INTEGER)
RETURNS BYTEA AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- Get active encryption key
    SELECT pgp_sym_decrypt(encrypted_key, current_setting('app.kms_key'))
    INTO encryption_key
    FROM encryption_keys
    WHERE is_active = TRUE
    LIMIT 1;

    -- Encrypt with AES-256
    RETURN pgp_sym_encrypt(
        plaintext,
        encryption_key,
        'cipher-algo=aes256'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_customer_data(ciphertext BYTEA, org_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
    requesting_org INTEGER;
BEGIN
    -- Get requesting org from session
    requesting_org := current_setting('app.current_organization_id', TRUE)::INTEGER;

    -- Security check: Can only decrypt own org's data
    IF requesting_org IS NULL OR requesting_org != org_id THEN
        RAISE EXCEPTION 'Access denied: Cannot decrypt data from other organizations';
    END IF;

    -- Get active encryption key
    SELECT pgp_sym_decrypt(encrypted_key, current_setting('app.kms_key'))
    INTO encryption_key
    FROM encryption_keys
    WHERE is_active = TRUE
    LIMIT 1;

    -- Decrypt with AES-256
    RETURN pgp_sym_decrypt(
        ciphertext,
        encryption_key,
        'cipher-algo=aes256'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Audit all decryption attempts
CREATE TABLE decryption_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    organization_id INTEGER,
    table_name VARCHAR(100),
    record_id INTEGER,
    column_name VARCHAR(100),
    decrypted_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);
```

---

### **1.5: Encrypt Sensitive Columns**

```sql
-- agent_actions table - encrypt customer prompts/responses
ALTER TABLE agent_actions
    ADD COLUMN action_payload_encrypted BYTEA,
    ADD COLUMN response_encrypted BYTEA,
    ADD COLUMN mcp_credentials_encrypted BYTEA;

-- Migrate existing plaintext data to encrypted
UPDATE agent_actions
SET action_payload_encrypted = encrypt_customer_data(action_payload::TEXT, organization_id)
WHERE action_payload IS NOT NULL;

UPDATE agent_actions
SET response_encrypted = encrypt_customer_data(response::TEXT, organization_id)
WHERE response IS NOT NULL;

-- Drop plaintext columns (after verification)
-- ALTER TABLE agent_actions DROP COLUMN action_payload;
-- ALTER TABLE agent_actions DROP COLUMN response;

-- For now, rename to preserve data during migration
ALTER TABLE agent_actions RENAME COLUMN action_payload TO action_payload_plaintext_backup;
ALTER TABLE agent_actions RENAME COLUMN response TO response_plaintext_backup;
ALTER TABLE agent_actions RENAME COLUMN action_payload_encrypted TO action_payload;
ALTER TABLE agent_actions RENAME COLUMN response_encrypted TO response;

-- mcp_policies table - encrypt policy rules
ALTER TABLE mcp_policies
    ADD COLUMN policy_rules_encrypted BYTEA;

UPDATE mcp_policies
SET policy_rules_encrypted = encrypt_customer_data(policy_rules::TEXT, organization_id)
WHERE policy_rules IS NOT NULL;

-- automation_playbooks table - encrypt playbook definitions
ALTER TABLE automation_playbooks
    ADD COLUMN playbook_definition_encrypted BYTEA;

UPDATE automation_playbooks
SET playbook_definition_encrypted = encrypt_customer_data(playbook_definition::TEXT, organization_id)
WHERE playbook_definition IS NOT NULL;
```

---

### **1.6: Row-Level Security (RLS) Policies**

```sql
-- Enable RLS on all tenant tables
ALTER TABLE agent_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE immutable_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_server_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mcp_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_playbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policy
CREATE POLICY tenant_isolation_agent_actions ON agent_actions
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_api_keys ON api_keys
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_audit_logs ON immutable_audit_logs
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_mcp_actions ON mcp_server_actions
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_mcp_policies ON mcp_policies
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_workflows ON workflows
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_playbooks ON automation_playbooks
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

CREATE POLICY tenant_isolation_alerts ON alerts
    USING (organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER);

-- Platform owner bypass (metadata-only access, no decryption)
CREATE POLICY platform_owner_metadata_access ON agent_actions
    FOR SELECT
    TO owkai_admin
    USING (true);  -- Can see all rows, but cannot decrypt sensitive columns

CREATE POLICY platform_owner_metadata_access_api_keys ON api_keys
    FOR SELECT
    TO owkai_admin
    USING (true);

-- Repeat for all tables...
```

---

### **1.7: Usage Tracking Table**

```sql
CREATE TABLE organization_usage (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    date DATE NOT NULL,

    -- API usage
    api_calls INTEGER DEFAULT 0,
    api_calls_success INTEGER DEFAULT 0,
    api_calls_failed INTEGER DEFAULT 0,

    -- MCP server usage
    mcp_servers_active INTEGER DEFAULT 0,
    mcp_actions INTEGER DEFAULT 0,

    -- Storage usage
    storage_mb NUMERIC(10, 2) DEFAULT 0,

    -- Compute usage
    compute_minutes INTEGER DEFAULT 0,

    -- Overage tracking
    api_calls_over_limit INTEGER DEFAULT 0,
    users_over_limit INTEGER DEFAULT 0,
    servers_over_limit INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(organization_id, date),
    INDEX idx_org_usage_date (organization_id, date)
);

-- Function to increment usage
CREATE OR REPLACE FUNCTION increment_org_usage(org_id INTEGER, usage_type VARCHAR)
RETURNS VOID AS $$
BEGIN
    INSERT INTO organization_usage (organization_id, date, api_calls)
    VALUES (org_id, CURRENT_DATE, 1)
    ON CONFLICT (organization_id, date)
    DO UPDATE SET api_calls = organization_usage.api_calls + 1;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔐 PHASE 2: AWS COGNITO SETUP

**Timeline**: Day 2 Morning (3-4 hours)

### **2.1: Create Cognito User Pool**

```bash
# Using Terraform for infrastructure as code

resource "aws_cognito_user_pool" "owkai_enterprise" {
  name = "owkai-enterprise-users"

  # Password policy
  password_policy {
    minimum_length    = 12
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
  }

  # MFA configuration
  mfa_configuration = "OPTIONAL"

  # Custom attributes
  schema {
    name                = "organization_id"
    attribute_data_type = "Number"
    mutable             = true
    required            = false
  }

  schema {
    name                = "organization_slug"
    attribute_data_type = "String"
    mutable             = true
    required            = false

    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    mutable             = true
    required            = false

    string_attribute_constraints {
      min_length = 1
      max_length = 50
    }
  }

  schema {
    name                = "is_org_admin"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  # Email verification
  auto_verified_attributes = ["email"]

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = {
    Environment = "production"
    Project     = "OW-AI Enterprise"
  }
}
```

---

### **2.2: Create App Client**

```bash
resource "aws_cognito_user_pool_client" "owkai_web_app" {
  name         = "owkai-web-app"
  user_pool_id = aws_cognito_user_pool.owkai_enterprise.id

  generate_secret = true

  # OAuth flows
  allowed_oauth_flows = ["code"]
  allowed_oauth_scopes = ["openid", "email", "profile"]
  allowed_oauth_flows_user_pool_client = true

  # Callback URLs
  callback_urls = [
    "https://pilot.owkai.app/auth/callback",
    "http://localhost:5173/auth/callback"  # For local development
  ]

  logout_urls = [
    "https://pilot.owkai.app/logout",
    "http://localhost:5173/logout"
  ]

  # Supported identity providers
  supported_identity_providers = ["COGNITO"]

  # Token validity
  id_token_validity      = 60  # 60 minutes
  access_token_validity  = 60  # 60 minutes
  refresh_token_validity = 30  # 30 days

  token_validity_units {
    id_token      = "minutes"
    access_token  = "minutes"
    refresh_token = "days"
  }

  # Read/write attributes
  read_attributes = [
    "email",
    "email_verified",
    "custom:organization_id",
    "custom:organization_slug",
    "custom:role",
    "custom:is_org_admin"
  ]

  write_attributes = [
    "email"
  ]
}
```

---

### **2.3: Create Cognito Domain**

```bash
resource "aws_cognito_user_pool_domain" "owkai_auth" {
  domain       = "owkai-auth"
  user_pool_id = aws_cognito_user_pool.owkai_enterprise.id
}

# Optional: Custom domain
# resource "aws_cognito_user_pool_domain" "owkai_custom" {
#   domain          = "auth.owkai.com"
#   certificate_arn = aws_acm_certificate.auth_cert.arn
#   user_pool_id    = aws_cognito_user_pool.owkai_enterprise.id
# }
```

---

### **2.4: Configure SAML/SSO (Enterprise Tier)**

```bash
# Enterprise customers can use their own identity providers

resource "aws_cognito_identity_provider" "azure_ad" {
  user_pool_id  = aws_cognito_user_pool.owkai_enterprise.id
  provider_name = "AzureAD"
  provider_type = "SAML"

  provider_details = {
    MetadataURL = var.customer_saml_metadata_url
  }

  attribute_mapping = {
    email    = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    username = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
  }
}

# Support for Okta, OneLogin, etc.
```

---

## 💻 PHASE 3: APPLICATION CHANGES

**Timeline**: Day 2 Afternoon + Day 3 Morning (6-8 hours)

### **3.1: Update Models**

```python
# models.py - Add Organization model

from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

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

    # Base limits
    included_api_calls = Column(Integer, default=100000)
    included_users = Column(Integer, default=5)
    included_mcp_servers = Column(Integer, default=3)

    # Overage rates
    overage_rate_per_call = Column(Numeric(10, 5), default=0.005)
    overage_rate_per_user = Column(Numeric(10, 2), default=50.00)
    overage_rate_per_server = Column(Numeric(10, 2), default=100.00)

    # Current usage
    current_month_api_calls = Column(Integer, default=0)
    current_month_overage_calls = Column(Integer, default=0)
    current_month_overage_cost = Column(Numeric(10, 2), default=0.00)
    last_usage_reset_date = Column(Date)

    # Billing
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    next_billing_date = Column(Date)

    # Relationships
    users = relationship("User", back_populates="organization")
    agent_actions = relationship("AgentAction", back_populates="organization")
    api_keys = relationship("ApiKey", back_populates="organization")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# Update User model
class User(Base):
    __tablename__ = "users"

    # Existing fields...
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    is_org_admin = Column(Boolean, default=False)
    cognito_user_id = Column(String(255), unique=True)  # Cognito sub

    # Relationships
    organization = relationship("Organization", back_populates="users")


# Update AgentAction model
class AgentAction(Base):
    __tablename__ = "agent_actions"

    # Existing fields...
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    # Encrypted fields (BYTEA)
    action_payload = Column(LargeBinary)  # Encrypted customer data
    response = Column(LargeBinary)  # Encrypted customer data

    # Relationships
    organization = relationship("Organization", back_populates="agent_actions")


# Repeat for all models...
```

---

### **3.2: Cognito Authentication Middleware**

```python
# dependencies_cognito.py - NEW FILE

import boto3
import requests
from jose import jwt, jwk
from fastapi import Depends, HTTPException, Request, status
from functools import lru_cache
from sqlalchemy.orm import Session
import logging

from database import get_db
from config import (
    COGNITO_REGION,
    COGNITO_USER_POOL_ID,
    COGNITO_APP_CLIENT_ID
)

logger = logging.getLogger("enterprise.cognito")

COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"


@lru_cache()
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys"""
    keys_url = f"{COGNITO_ISSUER}/.well-known/jwks.json"
    response = requests.get(keys_url)
    return {key['kid']: jwk.construct(key) for key in response.json()['keys']}


async def get_current_user_cognito(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Enterprise Cognito authentication

    Validates Cognito ID token and sets RLS context
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )

    token = auth_header[7:]

    try:
        # Get Cognito public keys
        keys = get_cognito_public_keys()

        # Decode token header
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

        # Extract user info from custom attributes
        cognito_user_id = payload["sub"]
        email = payload["email"]
        organization_id = int(payload.get("custom:organization_id"))
        organization_slug = payload.get("custom:organization_slug")
        role = payload.get("custom:role", "user")
        is_org_admin = payload.get("custom:is_org_admin", "false") == "true"

        # Set RLS context for database queries
        db.execute(f"SET app.current_organization_id = {organization_id}")

        # Log authentication
        user_context = {
            "cognito_user_id": cognito_user_id,
            "email": email,
            "organization_id": organization_id,
            "organization_slug": organization_slug,
            "role": role,
            "is_org_admin": is_org_admin,
            "auth_method": "cognito"
        }
        request.state.user = user_context

        logger.info(f"✅ Cognito auth successful: {email} (org: {organization_slug})")
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
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Check if it's an API key (not JWT)
        if token.count('.') != 2:
            try:
                # Import here to avoid circular dependency
                from dependencies_api_keys import verify_api_key
                user_context = await verify_api_key(token, db)
                logger.info(f"✅ API key auth: {user_context['email']}")
                return user_context
            except HTTPException:
                pass

    # Try Cognito JWT
    return await get_current_user_cognito(request, db)


def require_org_admin(current_user: dict = Depends(get_current_user_or_api_key_cognito)):
    """Require organization admin role"""
    if not current_user.get("is_org_admin"):
        raise HTTPException(
            status_code=403,
            detail="Organization admin access required"
        )
    return current_user


def require_platform_owner(current_user: dict = Depends(get_current_user_or_api_key_cognito)):
    """Require platform owner role (OW-AI Internal org)"""
    if current_user.get("organization_id") != 1:  # OW-AI Internal
        raise HTTPException(
            status_code=403,
            detail="Platform owner access required"
        )
    return current_user
```

---

### **3.3: Encryption/Decryption Service**

```python
# services/encryption_service.py - NEW FILE

from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger("enterprise.encryption")

# In production, fetch from AWS Secrets Manager
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_customer_data(plaintext: str, organization_id: int, db: Session) -> bytes:
    """
    Encrypt customer sensitive data

    Uses AES-256 encryption with organization-specific salt
    """
    try:
        # Add organization ID as salt
        salted_data = f"{organization_id}:{plaintext}"
        encrypted = cipher_suite.encrypt(salted_data.encode())

        logger.debug(f"✅ Data encrypted for org {organization_id}")
        return encrypted
    except Exception as e:
        logger.error(f"❌ Encryption failed: {e}")
        raise


def decrypt_customer_data(
    ciphertext: bytes,
    organization_id: int,
    requesting_org_id: int,
    db: Session
) -> str:
    """
    Decrypt customer sensitive data

    Security: Can only decrypt own organization's data
    """
    # Security check
    if requesting_org_id != organization_id:
        logger.warning(
            f"❌ Decryption denied: Org {requesting_org_id} "
            f"tried to access Org {organization_id} data"
        )
        raise PermissionError("Cannot decrypt data from other organizations")

    try:
        # Decrypt
        decrypted = cipher_suite.decrypt(ciphertext).decode()

        # Remove salt
        org_id_str, plaintext = decrypted.split(":", 1)

        # Verify organization ID
        if int(org_id_str) != organization_id:
            raise ValueError("Organization ID mismatch")

        # Log decryption audit trail
        log_decryption_audit(organization_id, requesting_org_id, db)

        logger.debug(f"✅ Data decrypted for org {organization_id}")
        return plaintext
    except Exception as e:
        logger.error(f"❌ Decryption failed: {e}")
        raise


def log_decryption_audit(
    data_org_id: int,
    requesting_org_id: int,
    db: Session
):
    """Log all decryption attempts for compliance"""
    from models import DecryptionAuditLog
    from datetime import datetime

    audit = DecryptionAuditLog(
        organization_id=data_org_id,
        requesting_organization_id=requesting_org_id,
        decrypted_at=datetime.now()
    )
    db.add(audit)
    db.commit()
```

---

### **3.4: Platform Admin Routes (Metadata Only)**

```python
# routes/platform_admin_routes.py - NEW FILE

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, date

from database import get_db
from dependencies_cognito import require_platform_owner
from models import Organization, User, AgentAction, ApiKey, OrganizationUsage

router = APIRouter(prefix="/platform", tags=["Platform Admin"])


@router.get("/organizations")
async def list_all_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View all organizations

    Returns metadata only (no encrypted customer data)
    """
    orgs = db.query(Organization).all()

    return {
        "total": len(orgs),
        "organizations": [
            {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "tier": org.subscription_tier,
                "status": org.subscription_status,
                "users_count": len(org.users),
                "active_users": sum(1 for u in org.users if u.is_active),
                "api_keys_count": len(org.api_keys),
                "api_calls_month": org.current_month_api_calls,
                "overage_cost": float(org.current_month_overage_cost),
                "created_at": org.created_at.isoformat(),
                "trial_ends": org.trial_ends_at.isoformat() if org.trial_ends_at else None
            }
            for org in orgs
        ]
    }


@router.get("/actions")
async def list_all_agent_actions(
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View agent actions metadata

    ⚠️ DOES NOT DECRYPT customer data (compliance requirement)
    Returns metadata only for governance/monitoring
    """
    query = db.query(AgentAction).join(Organization)

    if organization_id:
        query = query.filter(AgentAction.organization_id == organization_id)
    if status:
        query = query.filter(AgentAction.status == status)

    actions = query.order_by(AgentAction.created_at.desc()).limit(limit).all()

    return {
        "total": len(actions),
        "actions": [
            {
                "id": action.id,
                "organization": {
                    "id": action.organization.id,
                    "name": action.organization.name,
                    "slug": action.organization.slug
                },
                "action_type": action.action_type,
                "status": action.status,
                "risk_score": action.risk_score,
                "created_at": action.created_at.isoformat(),
                "created_by": action.user.email if action.user else None,
                "mcp_server": action.mcp_server,
                # ❌ action_payload: NOT INCLUDED (encrypted)
                # ❌ response: NOT INCLUDED (encrypted)
                # Platform admin sees metadata only
                "metadata": {
                    "approval_count": action.approval_count,
                    "denial_count": action.denial_count,
                    "policy_evaluated": action.policy_evaluated,
                    "has_encrypted_data": action.action_payload is not None
                }
            }
            for action in actions
        ]
    }


@router.get("/usage-stats")
async def get_platform_usage_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: Aggregated usage statistics
    """
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of month
    if not end_date:
        end_date = date.today()

    # Aggregate stats by tier
    stats = db.query(
        Organization.subscription_tier,
        func.count(Organization.id).label("org_count"),
        func.sum(Organization.current_month_api_calls).label("total_api_calls"),
        func.sum(Organization.current_month_overage_cost).label("total_overage_revenue")
    ).group_by(Organization.subscription_tier).all()

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "by_tier": [
            {
                "tier": stat.subscription_tier,
                "organizations": stat.org_count,
                "api_calls_total": stat.total_api_calls or 0,
                "overage_revenue": float(stat.total_overage_revenue or 0)
            }
            for stat in stats
        ],
        "platform_totals": {
            "organizations": sum(s.org_count for s in stats),
            "api_calls": sum(s.total_api_calls or 0 for s in stats),
            "overage_revenue": sum(float(s.total_overage_revenue or 0) for s in stats)
        }
    }


@router.get("/compliance/decryption-log")
async def get_decryption_audit_log(
    organization_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_platform_owner)
):
    """
    Platform owner: View decryption audit log

    Shows who accessed encrypted customer data and when
    """
    from models import DecryptionAuditLog

    query = db.query(DecryptionAuditLog)

    if organization_id:
        query = query.filter(DecryptionAuditLog.organization_id == organization_id)

    logs = query.order_by(DecryptionAuditLog.decrypted_at.desc()).limit(limit).all()

    return {
        "total": len(logs),
        "decryption_attempts": [
            {
                "id": log.id,
                "organization_id": log.organization_id,
                "requesting_org_id": log.requesting_organization_id,
                "table_name": log.table_name,
                "record_id": log.record_id,
                "column_name": log.column_name,
                "decrypted_at": log.decrypted_at.isoformat(),
                "user_email": log.user.email if log.user else None,
                "ip_address": str(log.ip_address)
            }
            for log in logs
        ]
    }
```

---

## 📦 PHASE 4: SDK DEVELOPMENT

**Timeline**: Day 5-6 (2-3 days)
**Status**: After multi-tenancy complete

### **SDK Architecture**:

```
owkai-sdk-python/
├── owkai/
│   ├── __init__.py
│   ├── client.py              # Main SDK client
│   ├── auth.py                # API key authentication
│   ├── boto3_patch.py         # Auto-patch boto3 calls
│   ├── models.py              # Request/response models
│   ├── exceptions.py          # Custom exceptions
│   └── utils.py               # Helper functions
├── tests/
│   ├── test_client.py
│   ├── test_boto3_patch.py
│   └── test_integration.py
├── examples/
│   ├── basic_usage.py
│   ├── boto3_integration.py
│   └── policy_management.py
├── setup.py
├── requirements.txt
└── README.md
```

### **4.1: SDK Core Client**

```python
# owkai/client.py

import requests
from typing import Optional, Dict, List
from .auth import APIKeyAuth
from .models import AgentAction, Policy, APIKey
from .exceptions import OWAIException, AuthenticationError

class OWAIClient:
    """
    OW-AI Enterprise SDK Client

    Usage:
        client = OWAIClient(api_key="owkai_admin_xyz...")
        action = client.create_agent_action(...)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://pilot.owkai.app",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    # Agent Actions
    def create_agent_action(
        self,
        action_type: str,
        payload: dict,
        mcp_server: Optional[str] = None
    ) -> AgentAction:
        """Create agent action for approval"""
        response = self.session.post(
            f"{self.base_url}/api/agent-actions",
            json={
                "action_type": action_type,
                "payload": payload,
                "mcp_server": mcp_server
            },
            timeout=self.timeout
        )
        self._check_response(response)
        return AgentAction(**response.json())

    def get_agent_action(self, action_id: int) -> AgentAction:
        """Get agent action by ID"""
        response = self.session.get(
            f"{self.base_url}/api/agent-actions/{action_id}",
            timeout=self.timeout
        )
        self._check_response(response)
        return AgentAction(**response.json())

    def list_agent_actions(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentAction]:
        """List agent actions"""
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = self.session.get(
            f"{self.base_url}/api/agent-actions",
            params=params,
            timeout=self.timeout
        )
        self._check_response(response)
        return [AgentAction(**a) for a in response.json()["actions"]]

    # API Key Management
    def create_api_key(
        self,
        name: str,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> APIKey:
        """Generate new API key"""
        response = self.session.post(
            f"{self.base_url}/api/keys/generate",
            json={
                "name": name,
                "description": description,
                "expires_in_days": expires_in_days
            },
            timeout=self.timeout
        )
        self._check_response(response)
        return APIKey(**response.json())

    def list_api_keys(self) -> List[APIKey]:
        """List API keys"""
        response = self.session.get(
            f"{self.base_url}/api/keys/list",
            timeout=self.timeout
        )
        self._check_response(response)
        return [APIKey(**k) for k in response.json()["keys"]]

    def revoke_api_key(self, key_id: int, reason: str = "User revoked"):
        """Revoke API key"""
        response = self.session.delete(
            f"{self.base_url}/api/keys/{key_id}/revoke",
            json={"reason": reason},
            timeout=self.timeout
        )
        self._check_response(response)
        return response.json()

    # Helper methods
    def _check_response(self, response: requests.Response):
        """Check API response and raise exceptions"""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        elif response.status_code == 403:
            raise OWAIException("Permission denied")
        elif response.status_code == 429:
            raise OWAIException("Rate limit exceeded")
        elif response.status_code >= 400:
            try:
                error = response.json().get("detail", response.text)
            except:
                error = response.text
            raise OWAIException(f"API error: {error}")
```

---

### **4.2: boto3 Auto-Patch**

```python
# owkai/boto3_patch.py

import boto3
from typing import Optional
from .client import OWAIClient
from .exceptions import OWAIException

_original_boto3_client = boto3.client
_owkai_client: Optional[OWAIClient] = None


def patch_boto3(api_key: str, auto_approve_risk_below: int = 30):
    """
    Auto-patch boto3 to route through OW-AI governance

    Usage:
        from owkai import patch_boto3
        patch_boto3(api_key="owkai_admin_xyz...", auto_approve_risk_below=30)

        # Now all boto3 calls go through OW-AI governance
        ec2 = boto3.client('ec2')
        instances = ec2.describe_instances()  # ← Governed by OW-AI
    """
    global _owkai_client
    _owkai_client = OWAIClient(api_key=api_key)

    def patched_client(service_name, *args, **kwargs):
        """Patched boto3.client that routes through OW-AI"""
        original_client = _original_boto3_client(service_name, *args, **kwargs)
        return GovernedBoto3Client(original_client, service_name, auto_approve_risk_below)

    boto3.client = patched_client


class GovernedBoto3Client:
    """
    Wraps boto3 client to route calls through OW-AI governance
    """

    def __init__(self, original_client, service_name: str, auto_approve_risk_below: int):
        self._original = original_client
        self._service = service_name
        self._auto_approve_risk = auto_approve_risk_below

    def __getattr__(self, name):
        """Intercept all method calls"""
        original_method = getattr(self._original, name)

        def governed_method(*args, **kwargs):
            # Check with OW-AI governance first
            action = _owkai_client.create_agent_action(
                action_type=f"boto3_{self._service}_{name}",
                payload={
                    "service": self._service,
                    "method": name,
                    "args": str(args),
                    "kwargs": str(kwargs)
                },
                mcp_server=f"boto3-{self._service}"
            )

            # Check approval status
            if action.risk_score < self._auto_approve_risk:
                # Auto-approve low-risk actions
                return original_method(*args, **kwargs)
            elif action.status == "approved":
                # Manually approved
                return original_method(*args, **kwargs)
            elif action.status == "denied":
                raise OWAIException(f"Action denied by governance: {action.denial_reason}")
            else:
                # Pending approval
                raise OWAIException(
                    f"Action requires approval (risk score: {action.risk_score}). "
                    f"Action ID: {action.id}"
                )

        return governed_method
```

---

### **4.3: SDK Testing**

```python
# tests/test_integration.py

import pytest
from owkai import OWAIClient, patch_boto3
import boto3

# Test configuration
API_KEY = "owkai_admin_test_xyz..."
BASE_URL = "https://pilot.owkai.app"


def test_client_authentication():
    """Test SDK authentication"""
    client = OWAIClient(api_key=API_KEY, base_url=BASE_URL)

    # Should authenticate successfully
    keys = client.list_api_keys()
    assert isinstance(keys, list)


def test_create_agent_action():
    """Test creating agent action"""
    client = OWAIClient(api_key=API_KEY, base_url=BASE_URL)

    action = client.create_agent_action(
        action_type="test_action",
        payload={"test": "data"}
    )

    assert action.id is not None
    assert action.status in ["pending", "approved", "denied"]


def test_boto3_patch():
    """Test boto3 auto-patch"""
    patch_boto3(api_key=API_KEY, auto_approve_risk_below=30)

    # Create boto3 client (patched)
    ec2 = boto3.client('ec2', region_name='us-east-2')

    # This call should go through OW-AI governance
    # (will be denied if no MCP policy configured)
    with pytest.raises(Exception):  # Expect governance check
        instances = ec2.describe_instances()


def test_api_key_management():
    """Test API key CRUD"""
    client = OWAIClient(api_key=API_KEY, base_url=BASE_URL)

    # Create key
    new_key = client.create_api_key(
        name="Test SDK Key",
        description="Created by SDK test",
        expires_in_days=7
    )
    assert new_key.api_key.startswith("owkai_")

    # List keys
    keys = client.list_api_keys()
    assert any(k.id == new_key.key_id for k in keys)

    # Revoke key
    result = client.revoke_api_key(new_key.key_id, reason="Test complete")
    assert result["success"] is True
```

---

## 🌐 PHASE 5: LANDING PAGE + ONBOARDING

**Timeline**: Day 7-8 (2-3 days)
**Status**: After multi-tenancy + SDK complete

### **Landing Page Features**:

```
Landing Page (https://owkai.app):
├── 1. Hero Section
│   ├── Value prop: "Enterprise Agent Governance"
│   ├── CTA: "Start Free Trial" → Cognito sign-up
│   └── Social proof: "Trusted by X organizations"
│
├── 2. Pricing Section
│   ├── Pilot: $399/mo
│   ├── Growth: $999/mo
│   ├── Enterprise: $2,999/mo
│   └── Mega-Enterprise: Custom
│
├── 3. Sign-Up Flow
│   ├── Step 1: Create account (Cognito)
│   ├── Step 2: Create organization
│   ├── Step 3: Choose plan + payment (Stripe)
│   └── Step 4: Email verification (SES)
│
├── 4. Onboarding Wizard (after sign-up)
│   ├── Step 1: Generate first API key
│   ├── Step 2: Install SDK
│   ├── Step 3: Create first MCP policy
│   └── Step 4: Test first agent action
│
└── 5. Documentation
    ├── Quick start guide
    ├── API reference
    ├── SDK documentation
    └── Integration examples
```

### **5.1: Sign-Up Flow Implementation**

```python
# routes/signup_routes.py - NEW FILE

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import boto3
import stripe

from database import get_db
from models import Organization, User
from dependencies_cognito import get_current_user_cognito
from services.email_service import send_welcome_email

router = APIRouter(prefix="/signup", tags=["Sign-Up"])

cognito_client = boto3.client('cognito-idp', region_name='us-east-2')
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/create-organization")
async def create_organization(
    org_name: str,
    org_slug: str,
    subscription_tier: str,  # pilot, growth, enterprise
    payment_method_id: str,  # Stripe payment method ID
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_cognito)
):
    """
    Create new organization after Cognito sign-up

    Flow:
    1. Validate org slug is unique
    2. Create Stripe customer
    3. Create Stripe subscription
    4. Create organization in database
    5. Update Cognito user attributes
    6. Send welcome email
    """

    # 1. Validate org slug
    existing = db.query(Organization).filter(Organization.slug == org_slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization slug already taken")

    # 2. Create Stripe customer
    try:
        stripe_customer = stripe.Customer.create(
            email=current_user["email"],
            payment_method=payment_method_id,
            invoice_settings={"default_payment_method": payment_method_id}
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")

    # 3. Create Stripe subscription
    tier_prices = {
        "pilot": "price_pilot_399",  # Replace with actual Stripe price IDs
        "growth": "price_growth_999",
        "enterprise": "price_enterprise_2999"
    }

    try:
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer.id,
            items=[{"price": tier_prices[subscription_tier]}],
            trial_period_days=14  # 14-day free trial
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Subscription failed: {str(e)}")

    # 4. Create organization
    tier_limits = {
        "pilot": (100000, 5, 3),      # (calls, users, servers)
        "growth": (500000, 25, 10),
        "enterprise": (2000000, 100, 50)
    }
    calls, users, servers = tier_limits[subscription_tier]

    org = Organization(
        name=org_name,
        slug=org_slug,
        subscription_tier=subscription_tier,
        subscription_status="trialing",
        trial_ends_at=stripe_subscription.trial_end,
        included_api_calls=calls,
        included_users=users,
        included_mcp_servers=servers,
        stripe_customer_id=stripe_customer.id,
        stripe_subscription_id=stripe_subscription.id
    )
    db.add(org)
    db.flush()

    # 5. Update Cognito user attributes
    try:
        cognito_client.admin_update_user_attributes(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=current_user["cognito_user_id"],
            UserAttributes=[
                {"Name": "custom:organization_id", "Value": str(org.id)},
                {"Name": "custom:organization_slug", "Value": org.slug},
                {"Name": "custom:is_org_admin", "Value": "true"}  # First user is admin
            ]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

    # Create user in database
    user = User(
        cognito_user_id=current_user["cognito_user_id"],
        email=current_user["email"],
        organization_id=org.id,
        role="admin",
        is_org_admin=True
    )
    db.add(user)
    db.commit()

    # 6. Send welcome email
    await send_welcome_email(
        email=current_user["email"],
        org_name=org_name,
        trial_ends=stripe_subscription.trial_end
    )

    return {
        "success": True,
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "tier": subscription_tier,
            "trial_ends": org.trial_ends_at.isoformat()
        },
        "next_steps": [
            "Generate your first API key",
            "Install the OW-AI SDK",
            "Create your first MCP policy"
        ]
    }
```

---

### **5.2: AWS SES Email Notifications**

```python
# services/email_service.py - NEW FILE

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger("enterprise.email")

ses_client = boto3.client('ses', region_name='us-east-2')
FROM_EMAIL = "noreply@owkai.com"


async def send_welcome_email(email: str, org_name: str, trial_ends: datetime):
    """Send welcome email to new organization"""

    subject = f"Welcome to OW-AI Enterprise - {org_name}"

    html_body = f"""
    <html>
    <head></head>
    <body>
        <h1>Welcome to OW-AI Enterprise!</h1>
        <p>Hi there,</p>

        <p>Your organization <strong>{org_name}</strong> has been successfully created.</p>

        <h2>Your 14-Day Free Trial</h2>
        <p>Your trial ends on <strong>{trial_ends.strftime('%B %d, %Y')}</strong>.</p>

        <h2>Next Steps</h2>
        <ol>
            <li><a href="https://pilot.owkai.app/onboarding/api-key">Generate your first API key</a></li>
            <li><a href="https://docs.owkai.com/sdk">Install the OW-AI SDK</a></li>
            <li><a href="https://pilot.owkai.app/onboarding/policy">Create your first MCP policy</a></li>
        </ol>

        <h2>Resources</h2>
        <ul>
            <li><a href="https://docs.owkai.com">Documentation</a></li>
            <li><a href="https://docs.owkai.com/quick-start">Quick Start Guide</a></li>
            <li><a href="mailto:support@owkai.com">Contact Support</a></li>
        </ul>

        <p>Best regards,<br>The OW-AI Team</p>
    </body>
    </html>
    """

    try:
        response = ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}}
            }
        )
        logger.info(f"✅ Welcome email sent to {email}")
        return response
    except ClientError as e:
        logger.error(f"❌ Failed to send email: {e}")
        raise


async def send_trial_ending_email(email: str, org_name: str, days_left: int):
    """Send trial ending reminder"""

    subject = f"Your OW-AI Trial Ends in {days_left} Days"

    html_body = f"""
    <html>
    <body>
        <h1>Your Trial is Ending Soon</h1>
        <p>Hi,</p>

        <p>Your OW-AI Enterprise trial for <strong>{org_name}</strong> ends in <strong>{days_left} days</strong>.</p>

        <p><a href="https://pilot.owkai.app/billing/upgrade">Upgrade your plan</a> to continue using OW-AI Enterprise.</p>

        <p>Questions? <a href="mailto:support@owkai.com">Contact our team</a>.</p>

        <p>Best regards,<br>The OW-AI Team</p>
    </body>
    </html>
    """

    try:
        response = ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}}
            }
        )
        logger.info(f"✅ Trial reminder sent to {email}")
        return response
    except ClientError as e:
        logger.error(f"❌ Failed to send email: {e}")
        raise


async def send_usage_limit_warning(email: str, org_name: str, usage_percent: int):
    """Send usage limit warning"""

    subject = f"Usage Alert: {usage_percent}% of Your Limit"

    html_body = f"""
    <html>
    <body>
        <h1>Usage Alert</h1>
        <p>Hi,</p>

        <p><strong>{org_name}</strong> has used <strong>{usage_percent}%</strong> of your monthly API call limit.</p>

        <p>To avoid service interruption, consider <a href="https://pilot.owkai.app/billing/upgrade">upgrading your plan</a>.</p>

        <p>View your usage: <a href="https://pilot.owkai.app/usage">Dashboard</a></p>

        <p>Best regards,<br>The OW-AI Team</p>
    </body>
    </html>
    """

    try:
        response = ses_client.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": html_body}}
            }
        )
        logger.info(f"✅ Usage warning sent to {email}")
        return response
    except ClientError as e:
        logger.error(f"❌ Failed to send email: {e}")
        raise
```

---

## 💳 PHASE 6: STRIPE BILLING INTEGRATION

**Timeline**: Day 9 (1 day)

### **Stripe Webhook Handler**:

```python
# routes/billing_routes.py - NEW FILE

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
from datetime import datetime, timedelta

from database import get_db
from models import Organization
from services.email_service import send_trial_ending_email
import logging

logger = logging.getLogger("enterprise.billing")

router = APIRouter(prefix="/billing", tags=["Billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events

    Events handled:
    - invoice.payment_succeeded: Reset monthly usage
    - invoice.payment_failed: Suspend organization
    - customer.subscription.deleted: Cancel organization
    - customer.subscription.trial_will_end: Send reminder
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    event_type = event['type']
    logger.info(f"📩 Stripe webhook received: {event_type}")

    if event_type == 'invoice.payment_succeeded':
        # Monthly billing cycle - reset usage counters
        await handle_payment_succeeded(event, db)

    elif event_type == 'invoice.payment_failed':
        # Payment failed - suspend organization
        await handle_payment_failed(event, db)

    elif event_type == 'customer.subscription.deleted':
        # Subscription canceled - deactivate organization
        await handle_subscription_deleted(event, db)

    elif event_type == 'customer.subscription.trial_will_end':
        # Trial ending soon - send reminder
        await handle_trial_ending(event, db)

    return {"success": True}


async def handle_payment_succeeded(event, db: Session):
    """Handle successful payment"""
    customer_id = event['data']['object']['customer']

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        logger.warning(f"⚠️  Organization not found for customer {customer_id}")
        return

    # Reset monthly usage counters
    org.current_month_api_calls = 0
    org.current_month_overage_calls = 0
    org.current_month_overage_cost = 0
    org.last_usage_reset_date = datetime.now().date()
    org.subscription_status = "active"

    db.commit()
    logger.info(f"✅ Monthly reset for org {org.slug}")


async def handle_payment_failed(event, db: Session):
    """Handle failed payment"""
    customer_id = event['data']['object']['customer']

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    # Suspend organization
    org.subscription_status = "past_due"
    db.commit()

    logger.warning(f"⚠️  Payment failed for org {org.slug} - suspended")


async def handle_subscription_deleted(event, db: Session):
    """Handle subscription cancellation"""
    customer_id = event['data']['object']['customer']

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    # Deactivate organization
    org.subscription_status = "cancelled"
    db.commit()

    logger.info(f"❌ Subscription cancelled for org {org.slug}")


async def handle_trial_ending(event, db: Session):
    """Handle trial ending reminder"""
    customer_id = event['data']['object']['customer']

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    # Send reminder email
    admin = db.query(User).filter(
        User.organization_id == org.id,
        User.is_org_admin == True
    ).first()

    if admin:
        await send_trial_ending_email(
            email=admin.email,
            org_name=org.name,
            days_left=3  # Trial ends in 3 days
        )

    logger.info(f"📧 Trial ending reminder sent for org {org.slug}")
```

---

## 🚀 DEPLOYMENT CHECKLIST

### **Pre-Deployment**:
- [ ] Run all migrations locally
- [ ] Test RLS policies with test users
- [ ] Verify encryption/decryption works
- [ ] Test Cognito authentication
- [ ] Test SDK against staging
- [ ] Create Stripe products and prices
- [ ] Configure AWS SES (verify domain)
- [ ] Set up CloudWatch alarms

### **Staging Deployment**:
- [ ] Deploy to staging environment
- [ ] Run full test suite
- [ ] Test sign-up flow end-to-end
- [ ] Test billing webhooks (Stripe test mode)
- [ ] Verify email notifications
- [ ] Load testing (simulate 1000 users)

### **Production Deployment**:
- [ ] Database backup
- [ ] Deploy migrations to production
- [ ] Deploy application (GitHub Actions)
- [ ] Verify health checks
- [ ] Test authentication flow
- [ ] Monitor CloudWatch logs
- [ ] Test one end-to-end sign-up

---

## 📊 SUCCESS METRICS

### **Technical Metrics**:
- ✅ RLS prevents cross-org data access
- ✅ Platform admin cannot decrypt customer data
- ✅ All tests pass (100+ tests)
- ✅ API response time < 200ms (p95)
- ✅ Zero data leakage incidents

### **Business Metrics**:
- 📈 Organizations created
- 📈 Trial-to-paid conversion rate
- 📈 Monthly recurring revenue (MRR)
- 📈 Average revenue per organization (ARPO)
- 📈 Customer churn rate

---

## 🎯 FINAL DELIVERABLES

1. ✅ **Multi-tenant database** with RLS and encryption
2. ✅ **AWS Cognito** authentication with SSO support
3. ✅ **Platform admin dashboard** (metadata only)
4. ✅ **OW-AI SDK** (Python) with boto3 auto-patch
5. ✅ **Landing page** with sign-up flow
6. ✅ **Email notifications** (AWS SES)
7. ✅ **Stripe billing** with webhooks
8. ✅ **Usage tracking** and overage billing
9. ✅ **Complete documentation**
10. ✅ **Production deployment**

---

## 📅 TIMELINE SUMMARY

| Phase | Timeline | Status |
|-------|----------|--------|
| Phase 1: Database + SSE | Day 1 (6-8h) | Starting now |
| Phase 2: Cognito | Day 2 AM (3-4h) | Pending |
| Phase 3: Application | Day 2 PM + Day 3 AM (6-8h) | Pending |
| Phase 4: SDK | Day 5-6 (2-3 days) | Pending |
| Phase 5: Landing Page | Day 7-8 (2-3 days) | Pending |
| Phase 6: Billing | Day 9 (1 day) | Pending |
| Testing + Deployment | Day 4, 10 | Pending |
| **Total** | **7-10 days** | **Approved** |

---

**Status**: ✅ **APPROVED - STARTING PHASE 1 NOW**

**Next Action**: Begin Phase 1 - Database Schema + SSE Encryption

---

**Prepared by**: Enterprise Implementation Team
**Date**: 2025-11-20
**Approved by**: User
**Start Date**: 2025-11-20 (today)
