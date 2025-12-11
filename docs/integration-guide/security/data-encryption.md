---
Document ID: ASCEND-SEC-004
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Data Encryption

Ascend implements comprehensive encryption to protect data at rest and in transit, based on industry-standard practices and verified backend implementations.

## Encryption Overview

| Layer | Method | Implementation Source |
|-------|--------|----------------------|
| Data at Rest | AWS RDS PostgreSQL encryption | RDS storage-level encryption |
| Data in Transit | TLS 1.3 | HTTPS (port 443) |
| Passwords | bcrypt (cost 12) | `models.py`, `dependencies.py` |
| API Keys | PBKDF2-HMAC-SHA256 | `api_key_routes.py` (100,000 iterations) |

## Data in Transit

### TLS Configuration

All API communications use TLS:

```
Protocol: TLS 1.3 (minimum TLS 1.2)
Port: 443 (HTTPS only)
Certificate: Issued by trusted CA
HSTS: Enforced by infrastructure
```

**Implementation**: AWS infrastructure enforces TLS termination at load balancer.

### Certificate Verification

SDK clients enforce certificate verification:

```python
# Python SDK (enforced by default)
import requests

response = requests.get(
    "https://pilot.owkai.app/api/health",
    verify=True  # Certificate verification enabled
)

# DON'T: Never disable in production
# verify=False  # Security violation
```

## Data at Rest

### Database Encryption

PostgreSQL database uses AWS RDS encryption:

| Data Type | Storage | Encryption |
|-----------|---------|------------|
| User records | RDS PostgreSQL | AES-256 (RDS level) |
| Action history | RDS PostgreSQL | AES-256 (RDS level) |
| Audit logs | RDS PostgreSQL | AES-256 (RDS level) |
| Organization data | RDS PostgreSQL | AES-256 (RDS level) |

**Source**: AWS RDS encrypted storage volumes

### Field-Level Encryption

Sensitive fields receive additional application-level encryption:

#### Password Hashing

```python
# From models.py User model
password = Column(String)  # Stored as bcrypt hash

# Bcrypt with cost factor 12 (2^12 iterations)
# Industry standard for password hashing
# Resistant to brute-force attacks
```

**Source**: `/ow-ai-backend/models.py` (line 33)

#### API Key Hashing

```python
# From API key implementation
# Key generation (conceptual)
import secrets
import hashlib

# Generate cryptographically secure key
raw_key = secrets.token_bytes(32)
key_string = f"owkai_live_{secrets.token_urlsafe(32)}"

# Hash for storage (PBKDF2-HMAC-SHA256, 100,000 iterations)
salt = secrets.token_bytes(16)
key_hash = hashlib.pbkdf2_hmac('sha256', key_string.encode(), salt, 100000)

# Only hash and metadata stored
{
    "key_prefix": "owkai_xxxx",    # First 4 chars
    "key_suffix": "xxxx",           # Last 4 chars
    "key_hash": key_hash,           # PBKDF2-HMAC-SHA256
    "salt": salt,                   # Random per key
    "organization_id": 123          # Tenant isolation
}
```

**Source**: `/ow-ai-backend/routes/api_key_routes.py` (SEC-018)

## Multi-Tenant Data Isolation

### Row-Level Security

Every database query is filtered by `organization_id`:

```python
# From dependencies.py (SEC-007)
async def get_organization_filter(
    current_user: User = Depends(get_current_user)
) -> int:
    """
    ENTERPRISE: Returns organization_id for current user.
    All database queries MUST use this for tenant isolation.
    """
    if current_user.organization_id is None:
        raise HTTPException(403, "User has no organization")
    return current_user.organization_id

# Usage in routes
@router.get("/api/data")
async def get_data(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    # All queries automatically filtered by org_id
    return db.query(Model).filter(
        Model.organization_id == org_id
    ).all()
```

**Source**: `/ow-ai-backend/dependencies.py` (lines 118-149)

### Isolated Tables

| Table | Organization Column | Index | NOT NULL |
|-------|---------------------|-------|----------|
| users | `organization_id` | ✅ Yes | ✅ Yes |
| alerts | `organization_id` | ✅ Yes | ✅ Yes |
| agent_actions | `organization_id` | ✅ Yes | ✅ Yes |
| smart_rules | `organization_id` | ✅ Yes | ❌ Nullable |
| api_keys | `organization_id` | ✅ Yes | ✅ Yes |

**Source**: `/ow-ai-backend/models.py` (User: line 57, Alert: line 111, AgentAction: line 162, SmartRule: line 271)

## Session Security

### Cookie-Based JWT

```python
# From dependencies.py
SESSION_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "owai_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Cookie attributes (security/cookies.py)
{
    "httponly": True,        # Prevent XSS access
    "secure": True,          # HTTPS only
    "samesite": "Lax",       # CSRF protection
    "path": "/",
    "max_age": 3600          # 1 hour expiration
}
```

**Features**:
- HttpOnly flag prevents JavaScript access (XSS protection)
- Secure flag enforces HTTPS-only transmission
- SameSite=Lax prevents CSRF attacks
- Token versioning for force logout capability

**Source**: `/ow-ai-backend/dependencies.py`, `/ow-ai-backend/security/cookies.py`

### Session Revocation

```python
# From models.py User model (SEC-046)
class User(Base):
    # Token versioning for force logout
    token_version = Column(Integer, default=0, nullable=False)
    last_logout = Column(DateTime, nullable=True)
    last_active_at = Column(DateTime, nullable=True)

# Force logout (increment version)
user.token_version += 1  # Invalidates all existing sessions
db.commit()
```

**Source**: `/ow-ai-backend/models.py` (lines 78-80)

## Key Management

### API Key Lifecycle

1. **Generation**: Cryptographically secure random generation (256-bit)
2. **Storage**: PBKDF2-HMAC-SHA256 hash with per-key salt (100,000 iterations)
3. **Validation**: Constant-time comparison to prevent timing attacks
4. **Rotation**: Manual key rotation via API (automatic expiration optional)
5. **Revocation**: Immediate key deletion from database

### Key Rotation

```bash
# Generate new API key
curl -X POST https://pilot.owkai.app/api/keys/generate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production Agent Key",
    "scopes": ["agent:read", "agent:write"]
  }'

# Revoke old API key
curl -X DELETE https://pilot.owkai.app/api/keys/{key_id} \
  -b cookies.txt
```

**Source**: `/ow-ai-backend/routes/api_key_routes.py`

## Audit Log Integrity

### Immutable Audit Trails

Audit logs use immutable storage patterns:

```python
# From data_rights_routes.py
await audit_service.log_event(
    event_type="DATA_ACCESS_REQUEST",
    actor_id=current_user.email,
    resource_type="DATA_SUBJECT",
    resource_id=subject_email,
    action="REQUEST_SUBMITTED",
    event_data={...},
    risk_level="MEDIUM",
    compliance_tags=["GDPR", "CCPA", "DATA_ACCESS"],
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

**Features**:
- Append-only storage (no updates/deletes)
- Cryptographic integrity (service implementation)
- Compliance tagging (GDPR, CCPA, SOC 2)
- IP address and user agent tracking

**Source**: `/ow-ai-backend/routes/data_rights_routes.py` (lines 151-167)

## Encryption in SDK

### Python SDK

```python
from ascend_sdk import AscendClient

# All communications automatically encrypted with TLS
client = AscendClient(
    api_key="owkai_your_key",
    verify_ssl=True  # Default: True (DO NOT DISABLE)
)

# API calls use HTTPS by default
decision = await client.evaluate_action(
    action_type="database.query",
    resource="production_db"
)
```

### Environment Variables

```bash
# DO: Use environment variables
export ASCEND_API_KEY="owkai_live_xxxxx"

# DO: Use secure secret management
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets

# DON'T: Hardcode keys
# api_key = "owkai_live_xxxxx"  # NEVER DO THIS

# DON'T: Commit keys to git
# .env files should be in .gitignore
```

## Compliance

### Encryption Standards

| Standard | Requirement | Ascend Implementation |
|----------|-------------|----------------------|
| SOC 2 Type II | Data encryption | ✅ RDS encryption, bcrypt, TLS 1.3 |
| HIPAA | PHI encryption at rest/transit | ✅ RDS encryption, HTTPS only |
| PCI-DSS | Cardholder data encryption | ✅ Field-level hashing, TLS |
| GDPR | Personal data protection | ✅ Multi-tenant isolation, encryption |

### Algorithm Standards

| Use Case | Algorithm | Key Size | Compliance |
|----------|-----------|----------|------------|
| Database | AES-256 | 256-bit | FIPS 140-2 |
| Passwords | bcrypt | Cost 12 | OWASP |
| API Keys | PBKDF2-HMAC-SHA256 | 256-bit | NIST |
| Transport | TLS 1.3 | 2048-bit RSA | PCI-DSS |

## Best Practices

### 1. Never Disable Certificate Verification

```python
# GOOD: Default behavior
client = AscendClient(api_key="...", verify_ssl=True)

# BAD: Security violation
client = AscendClient(api_key="...", verify_ssl=False)  # NEVER
```

### 2. Use Strong API Keys

```python
# GOOD: Secure key generation
api_key = os.environ.get("ASCEND_API_KEY")

# BAD: Weak or exposed keys
api_key = "test123"  # NEVER use weak keys
```

### 3. Rotate Keys Regularly

```python
# Recommended key rotation schedule:
# - Production keys: Every 90 days
# - Development keys: Every 180 days
# - Compromised keys: Immediate revocation
```

### 4. Log Security Events

```python
# DO: Log authentication attempts
logger.info(f"API key auth success: {key_prefix}")

# DON'T: Log sensitive data
# logger.info(f"API key: {full_key}")  # NEVER log full keys
```

## Troubleshooting

### Certificate Verification Errors

```bash
# Verify TLS certificate
openssl s_client -connect pilot.owkai.app:443 -showcerts

# Expected output:
# subject=CN=pilot.owkai.app
# issuer=CN=Amazon (or your CA)
# Verification: OK
```

### Key Authentication Failures

Common issues:
1. **Expired key**: Check key expiration date
2. **Wrong environment**: Verify using correct key (test vs. production)
3. **Revoked key**: Check if key was manually revoked
4. **Organization mismatch**: Ensure key belongs to correct organization

## Implementation References

All encryption features are implemented in:

| Feature | Backend File | Line Reference |
|---------|-------------|----------------|
| Password Hashing | `models.py` | Line 33 (User.password) |
| API Key Hashing | `api_key_routes.py` | SEC-018 implementation |
| Session Cookies | `dependencies.py` | Lines 118-150 |
| Multi-Tenant Isolation | `dependencies.py` | SEC-007 (lines 118-176) |
| Token Versioning | `models.py` | Line 78 (User.token_version) |
| Audit Logging | `data_rights_routes.py` | Lines 97-167 |

## Next Steps

- [Security Overview](/security/overview) - Complete security architecture
- [Compliance](/security/compliance) - Compliance frameworks and certifications
- [API Authentication](/sdk/rest/authentication) - API key management guide
