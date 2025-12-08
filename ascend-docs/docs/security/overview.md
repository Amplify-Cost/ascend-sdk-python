---
sidebar_position: 1
title: Security Overview
description: Security architecture and best practices for Ascend
---

# Security Overview

Ascend is built with banking-level security, designed to meet the strictest enterprise requirements for AI governance.

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      PERIMETER SECURITY                          │   │
│  │  • Rate Limiting (per API key)                                  │   │
│  │  • IP Allowlisting (Enterprise)                                 │   │
│  │  • TLS 1.3 required                                             │   │
│  │  • HTTPS only (443)                                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    AUTHENTICATION LAYER                          │   │
│  │  • API Key Authentication (SHA-256 with salt)                   │   │
│  │  • AWS Cognito Integration                                      │   │
│  │  • Session Management (cookie-based JWT)                        │   │
│  │  • CSRF Protection                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  │  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    AUTHORIZATION LAYER                           │   │
│  │  • Role-Based Access Control (RBAC)                             │   │
│  │  • Cedar-Style Policy Engine                                    │   │
│  │  • Policy Conflict Resolution                                   │   │
│  │  • Multi-Tenant Organization Isolation                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      DATA SECURITY                               │   │
│  │  • Encryption at Rest (RDS PostgreSQL encryption)               │   │
│  │  • Encryption in Transit (TLS 1.3)                              │   │
│  │  • Multi-Tenant Data Isolation (row-level)                      │   │
│  │  • Password Hashing (bcrypt)                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MONITORING & AUDIT                            │   │
│  │  • Anomaly Detection (Z-score based)                            │   │
│  │  • Circuit Breaker Pattern                                      │   │
│  │  • Immutable Audit Logs                                         │   │
│  │  • Real-time Health Monitoring                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Encryption

### Data at Rest

| Data Type | Encryption | Implementation |
|-----------|------------|----------------|
| Database | AWS RDS encryption | PostgreSQL storage encryption |
| Passwords | bcrypt (cost factor 12) | `dependencies.py`, `models.py` |
| API Keys | SHA-256 with salt | PBKDF2-HMAC-SHA256, 100,000 iterations |

**Source**: `/ow-ai-backend/models.py` (User model), `/ow-ai-backend/dependencies.py`

### Data in Transit

- **TLS 1.3** required for all API connections
- **HTTPS only** - Port 443, all HTTP redirected
- **Certificate verification** enforced in SDK

### API Key Security

API keys are never stored in plaintext:

```python
# From services implementation
{
    "key_prefix": "owkai_xxxx",      # First 4 chars only
    "key_suffix": "xxxx",             # Last 4 chars only
    "key_hash": "sha256:...",         # PBKDF2-HMAC-SHA256
    "salt": "base64:...",             # Random salt per key
    "organization_id": 123            # Multi-tenant isolation
}
```

**Source**: `/ow-ai-backend/routes/api_key_routes.py` (SEC-018)

## Authentication

### Session Management

```python
# Cookie-based JWT sessions (dependencies.py)
SESSION_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "owai_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Session security features:
- HttpOnly cookies (XSS protection)
- Secure flag (HTTPS only)
- SameSite=Lax (CSRF protection)
- Token versioning for force logout
```

**Source**: `/ow-ai-backend/dependencies.py`, `/ow-ai-backend/security/cookies.py`

### AWS Cognito Integration

- User pool per organization (multi-tenant isolation)
- Automatic user linking via email (SEC-014)
- MFA support (TOTP)
- Account lockout protection

**Source**: `/ow-ai-backend/dependencies_cognito.py`

## Access Control

### Role-Based Access Control (RBAC)

| Role | Column | Permissions |
|------|--------|-------------|
| Admin | `is_org_admin=true` | Full organization access |
| Manager | `approval_level>=2` | Approval permissions |
| User | `role='user'` | Standard access |
| Suspended | `is_suspended=true` | No access (SEC-046) |

**Source**: `/ow-ai-backend/models.py` (User model lines 49-87)

### Policy Enforcement

Cedar-style policy engine with:
- Natural language to structured policy compilation
- Multiple resolution strategies (MOST_RESTRICTIVE, MOST_PERMISSIVE, HIGHEST_PRIORITY, FIRST_MATCH)
- Semantic action taxonomy
- Policy conflict detection

**Source**: `/ow-ai-backend/services/cedar_enforcement_service.py`

### Policy Conflict Resolution

```python
# Conflict Types (policy_conflict_resolver.py)
PRIORITY_TIE          # Same priority on overlapping scope
EFFECT_CONTRADICTION  # ALLOW vs DENY on same resource
RESOURCE_OVERLAP      # Overlapping resource patterns
CONDITION_AMBIGUITY   # Ambiguous condition evaluation
```

**Source**: `/ow-ai-backend/services/policy_conflict_resolver.py` (lines 28-34)

## Multi-Tenant Security

### Organization Isolation

Every database query is filtered by `organization_id`:

```python
# Enterprise dependency (dependencies.py)
async def get_organization_filter(
    current_user: User = Depends(get_current_user)
) -> int:
    """
    ENTERPRISE: Returns organization_id for current user.
    All database queries MUST use this for tenant isolation.
    """
    return current_user.organization_id
```

**Source**: `/ow-ai-backend/dependencies.py` (SEC-007)

### Isolated Tables

| Table | Organization ID Column | Indexed |
|-------|------------------------|---------|
| users | `organization_id` | Yes (Foreign Key) |
| alerts | `organization_id` | Yes |
| agent_actions | `organization_id` | Yes |
| smart_rules | `organization_id` | Yes |
| api_keys | `organization_id` | Yes (NOT NULL) |

**Source**: `/ow-ai-backend/models.py` (lines 57, 111, 162, 271)

## Security Monitoring

### Anomaly Detection

Real-time Z-score based detection:

```python
# Z-score algorithm (anomaly_detection_service.py)
z = (current_value - baseline_mean) / standard_deviation

# Severity thresholds:
LOW      (z > 2.0)  # 1-2 std deviations
MEDIUM   (z > 2.0)  # 2-3 std deviations
HIGH     (z > 3.0)  # 3-4 std deviations
CRITICAL (z > 4.0)  # >4 std deviations (auto-suspend enabled)
```

**Monitored metrics**:
- Actions per hour (EMA/SMA)
- Error rate percentage
- Average risk score

**Source**: `/ow-ai-backend/services/anomaly_detection_service.py` (SEC-077, lines 44-522)

### Circuit Breaker Pattern

Prevents cascade failures in MCP servers:

```
CLOSED (healthy) ─failure_threshold→ OPEN (blocked) ─timeout→ HALF_OPEN (testing)
      ↑                                                               │
      └───────────────────────recovery_successful────────────────────┘
```

**Configuration**:
- `circuit_failure_threshold`: Failures before opening (default: 5)
- `circuit_recovery_timeout_seconds`: Time before retry (default: 300s)
- `circuit_required_successes`: Successes to close (default: 2)

**Source**: `/ow-ai-backend/services/circuit_breaker_service.py` (SEC-077, lines 30-456)

## Data Rights & Privacy

### GDPR Compliance

Comprehensive data subject rights implementation:

**Endpoints** (`data_rights_routes.py`):
- `POST /api/data-rights/access/request` - Right to Access (GDPR Article 15)
- `POST /api/data-rights/erasure/request` - Right to Erasure (GDPR Article 17)
- `POST /api/data-rights/portability/request` - Data Portability (GDPR Article 20)
- `POST /api/data-rights/consent/record` - Consent Management (GDPR Articles 6-7)
- `POST /api/data-rights/lineage/record` - Data Lineage Tracking

**Features**:
- 30-day response deadline tracking
- Verification workflow
- Cross-system data discovery
- Immutable audit logging

**Source**: `/ow-ai-backend/routes/data_rights_routes.py` (lines 1-940)

## Security Best Practices

### For API Keys

```python
# DO: Use environment variables
api_key = os.environ.get("ASCEND_API_KEY")

# DO: Rotate keys regularly
# Keys support automatic expiration

# DON'T: Hardcode keys
api_key = "owkai_live_xxxx"  # NEVER DO THIS

# DON'T: Log keys
logger.info(f"Using key: {api_key}")  # NEVER DO THIS
```

### For Multi-Tenant Applications

```python
# DO: Always filter by organization_id
from dependencies import get_organization_filter

@router.get("/api/data")
async def get_data(
    org_id: int = Depends(get_organization_filter),
    db: Session = Depends(get_db)
):
    return db.query(Model).filter(
        Model.organization_id == org_id
    ).all()

# DON'T: Query without organization filter
# This violates SEC-007 security requirements
```

### For Session Security

```python
# DO: Use CSRF protection
# CSRF tokens automatically validated in dependencies.py

# DO: Set token version for force logout
user.token_version += 1  # Invalidates all sessions

# DON'T: Disable CSRF validation
# Required for SOC 2 CC6.1 compliance
```

## Compliance

Ascend implements controls for:

- **SOC 2 Type II** - Processing integrity, confidentiality (see `/security/compliance`)
- **HIPAA** - PHI handling, audit trails (see `/security/compliance`)
- **GDPR** - Data subject rights, consent management (see `/security/compliance`)
- **PCI-DSS** - Secure authentication, audit logging (see `/security/compliance`)

## Reporting Security Issues

Report security vulnerabilities to:

**Email**: [security@ascendowkai.com](mailto:security@ascendowkai.com)

**Policy**: See [Responsible Disclosure](/security/responsible-disclosure)

## Implementation References

All security features documented here are implemented in the backend codebase:

| Feature | Backend Service | Status |
|---------|----------------|--------|
| Anomaly Detection | `services/anomaly_detection_service.py` | ✅ Implemented (SEC-077) |
| Circuit Breaker | `services/circuit_breaker_service.py` | ✅ Implemented (SEC-077) |
| Policy Resolver | `services/policy_conflict_resolver.py` | ✅ Implemented (SEC-077) |
| Policy Enforcement | `services/cedar_enforcement_service.py` | ✅ Implemented |
| Data Rights (GDPR) | `routes/data_rights_routes.py` | ✅ Implemented |
| Multi-Tenant Isolation | `dependencies.py` | ✅ Implemented (SEC-007) |
| API Key Auth | `routes/api_key_routes.py` | ✅ Implemented (SEC-018) |

## Next Steps

- [Data Encryption](/security/data-encryption) - Encryption implementation details
- [Compliance](/security/compliance) - Compliance framework mappings
- [Responsible Disclosure](/security/responsible-disclosure) - Report vulnerabilities
- [Enterprise Governance](/governance/enterprise-governance) - Policy and monitoring features
