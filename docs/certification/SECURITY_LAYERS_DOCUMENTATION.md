# ASCEND Security Layers Documentation

**Document Version:** 1.0.0
**Last Updated:** December 22, 2024
**Classification:** Enterprise Confidential

---

## Overview

The ASCEND AI Governance Platform implements a **12-layer defense-in-depth security architecture**. Each layer operates on a **FAIL SECURE** principle, meaning any failure defaults to DENY access rather than allowing potentially unauthorized operations.

---

## Layer 1: Rate Limiting

### Purpose
Protect against denial-of-service attacks and resource exhaustion through intelligent rate limiting at multiple levels.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Service | `agent_rate_limiter.py` | `/services/agent_rate_limiter.py` |
| Models | `models_rate_limits.py` | `/models_rate_limits.py` |
| Config | `OrgRateLimitConfig` | Database table |

### Configuration Levels

| Level | Scope | Default Limits |
|-------|-------|----------------|
| Organization | Tenant-wide | 1000/min, 50000/hr, 500000/day |
| Agent | Per-agent | Configurable per agent |
| IP | Authentication endpoints | 5/min for login |

### Fail-Secure Behavior
```python
# If Redis is unavailable, DENY all requests
if not redis_available:
    raise RateLimitExceeded("Service temporarily unavailable")
```

### Compliance Mapping
- SOC 2 A1.1 (Availability Controls)
- NIST 800-53 SC-5 (Denial of Service Protection)

---

## Layer 2: Prompt Security

### Purpose
Detect and prevent LLM prompt injection attacks, jailbreak attempts, and malicious prompt engineering.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Service | `prompt_security_service.py` | `/services/prompt_security_service.py` |
| Models | `models_prompt_security.py` | `/models_prompt_security.py` |
| Patterns | `GlobalPromptPattern` | Database table |

### Detection Categories

| Category | Pattern IDs | Severity |
|----------|------------|----------|
| Direct Injection | PROMPT-001, PROMPT-002 | CRITICAL |
| Jailbreak | PROMPT-004, PROMPT-008 | CRITICAL |
| Role Manipulation | PROMPT-003, PROMPT-009 | HIGH |
| Encoding Attacks | PROMPT-005, PROMPT-012 | HIGH |
| Data Exfiltration | PROMPT-014, PROMPT-019 | HIGH |
| Chain Attacks | PROMPT-020 | CRITICAL |

### Multi-Signal Configuration (VAL-FIX-001)

```python
# Reduce false positives through multi-signal requirement
multi_signal_required = True        # Require 2+ patterns for HIGH risk
single_pattern_max_risk = 70        # Cap single matches at MEDIUM
business_context_filter = True      # Filter business terminology
critical_patterns_always_block = True  # Critical patterns bypass
```

### Fail-Secure Behavior
```python
# If detector fails, BLOCK the request
if detection_error:
    return BlockDecision(reason="Security scanner unavailable")
```

### Compliance Mapping
- OWASP LLM Top 10 (LLM01 Prompt Injection)
- CWE-77 (Command Injection)

---

## Layer 3: Code Analysis

### Purpose
Detect malicious code patterns, SQL injection, command injection, and secrets exposure in agent-generated code.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Service | `code_analysis_service.py` | `/services/code_analysis_service.py` |
| Models | `models_code_analysis.py` | `/models_code_analysis.py` |
| Patterns | `GlobalCodePattern` | Database table |

### Detection Categories

| Category | CWE Mapping | Examples |
|----------|-------------|----------|
| SQL Injection | CWE-89 | UNION SELECT, DROP TABLE |
| Command Injection | CWE-78 | Shell metacharacters, backticks |
| Credential Exposure | CWE-200 | API keys, passwords in code |
| Data Destruction | CWE-400 | DROP, DELETE, TRUNCATE |
| Remote Code Execution | CWE-94 | eval(), exec(), system() |

### Fail-Secure Behavior
```python
# If analyzer fails, BLOCK the code execution
if analyzer_error:
    return BlockDecision(reason="Code analyzer unavailable")
```

### Compliance Mapping
- PCI-DSS 6.5 (Secure Development)
- NIST 800-53 SI-10 (Information Input Validation)

---

## Layer 4: Action Governance

### Purpose
Evaluate all agent actions through a comprehensive risk assessment pipeline using CVSS v3.1 scoring and policy evaluation.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| CVSS Mapper | `cvss_auto_mapper.py` | `/services/cvss_auto_mapper.py` |
| Policy Engine | `policy_engine.py` | `/policy_engine.py` |
| Risk Calculator | `enterprise_risk_calculator_v2.py` | `/services/enterprise_risk_calculator_v2.py` |

### CVSS Auto-Mapping

| Action Type | Base Score | Severity |
|-------------|------------|----------|
| database_read | 3.5 | LOW |
| database_write | 5.3 | MEDIUM |
| database_delete | 7.5 | HIGH |
| database_drop | 9.9 | CRITICAL |
| Unknown | 7.5 | HIGH (fail-secure) |

### Policy Decisions

| Decision | HTTP Code | Behavior |
|----------|-----------|----------|
| ALLOW | 200 | Proceed with action |
| DENY | 403 | Block immediately |
| REQUIRE_APPROVAL | 202 | Route to workflow |
| ESCALATE | 202 | Notify and require approval |

### Fail-Secure Behavior
```python
# Unknown action types default to HIGH risk
if action_type not in known_types:
    return CvssMetrics(base_score=7.5, severity="HIGH")
```

### Compliance Mapping
- CVSS v3.1 Specification
- NIST 800-30 (Risk Assessment)

---

## Layer 5: JWT Authentication

### Purpose
Secure authentication using RS256-signed JSON Web Tokens with comprehensive claim validation.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Manager | `jwt_manager.py` | `/jwt_manager.py` |
| Security | `jwt_security.py` | `/security/jwt_security.py` |
| Validation | `dependencies.py` | `/dependencies.py` |

### Token Structure

```json
{
  "iss": "https://api.ow-ai.com",
  "aud": ["ow-ai-platform", "ow-ai-api"],
  "sub": "<user_id>",
  "exp": "<expiration>",
  "jti": "<session_id>",
  "role": "<admin|analyst|viewer>",
  "tenant_id": "<organization_id>",
  "permissions": ["read", "write", "approve"]
}
```

### Validation Rules

| Rule | Enforcement | Failure Action |
|------|-------------|----------------|
| Signature | RS256 required | Reject (401) |
| Expiration | exp < now | Reject (401) |
| Issuer | Must match config | Reject (401) |
| Audience | Must be in allowed list | Reject (401) |
| Algorithm | Only RS256 | Reject (401) |

### Fail-Secure Behavior
```python
# Signature verification is ALWAYS required
signature_verification = True  # Cannot be disabled

# Algorithm confusion attacks blocked
blocked_algorithms = ["none", "None", "NONE", ""]
```

### Compliance Mapping
- NIST 800-63B (Authentication)
- OWASP ASVS V3.5 (Token Management)

---

## Layer 6: API Key Validation

### Purpose
Provide secure API authentication for programmatic access with constant-time comparison to prevent timing attacks.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Auth | `dependencies_api_keys.py` | `/dependencies_api_keys.py` |
| Models | `models_api_keys.py` | `/models_api_keys.py` |
| Storage | SHA-256 hash + salt | Database |

### Key Format
```
Key: owkai_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (64+ chars)
Prefix: First 32 characters (for lookup)
Hash: SHA-256 of full key + salt
```

### Validation Process

1. Extract key from `Authorization: Bearer` or `X-API-Key` header
2. Validate format (minimum 16 characters)
3. Extract prefix for database lookup
4. Retrieve hashed key from database
5. **Constant-time comparison** (prevents timing attacks)
6. Check expiration and revocation status
7. Log usage for audit

### Fail-Secure Behavior
```python
# Constant-time comparison prevents timing attacks
from hmac import compare_digest
if not compare_digest(provided_hash, stored_hash):
    raise AuthenticationError("Invalid API key")
```

### Compliance Mapping
- SOC 2 CC6.1 (Logical Access)
- PCI-DSS 8.1 (User Authentication)

---

## Layer 7: RBAC (Role-Based Access Control)

### Purpose
Enforce least-privilege access with a 6-level hierarchy and separation of duties requirements.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Manager | `rbac_manager.py` | `/rbac_manager.py` |
| Dependencies | `dependencies_rbac.py` | `/dependencies_rbac.py` |

### Access Levels

| Level | Name | Permissions |
|-------|------|-------------|
| 0 | RESTRICTED | None (suspended users) |
| 1 | BASIC | Dashboard view only |
| 2 | POWER | Analytics + alerts |
| 3 | MANAGER | Authorization capabilities |
| 4 | ADMIN | Full system access |
| 5 | EXECUTIVE | All + reporting |

### Separation of Duties

| Action | Required Approvers | Constraints |
|--------|-------------------|-------------|
| High-Risk (≥70) | 2 approvers | ADMIN + EXECUTIVE |
| Critical (≥90) | 2 approvers | Both EXECUTIVE, different departments |
| User Role Change | 2 approvers | MANAGER + ADMIN |
| Emergency Override | 2 EXECUTIVE | Requires justification |

### Fail-Secure Behavior
```python
# Default-deny permission model
def has_permission(user, permission):
    if permission not in user.permissions:
        return False  # Deny by default
    return True
```

### Compliance Mapping
- SOC 2 CC6.1 (Logical Access)
- NIST 800-53 AC-5 (Separation of Duties)

---

## Layer 8: BYOK Encryption

### Purpose
Enable customer-managed encryption keys (BYOK/CMK) with envelope encryption for data at rest.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Service | `byok_service.py` | `/services/encryption/byok_service.py` |
| Health | `byok_health.py` | `/services/encryption/byok_health.py` |
| KMS | AWS KMS | Customer AWS account |

### Encryption Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ENVELOPE ENCRYPTION                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Customer CMK (in customer's AWS account)                   │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  DEK (Data Encryption Key)                          │    │
│  │  - Generated per encryption operation               │    │
│  │  - Encrypted by CMK                                 │    │
│  │  - Stored with encrypted data                       │    │
│  └─────────────────────────────────────────────────────┘    │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Encrypted Data (AES-256-GCM)                       │    │
│  │  - Authenticated encryption                         │    │
│  │  - Tamper-evident                                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fail-Secure Behavior
```python
# If CMK is unavailable, BLOCK all operations
if cmk_access_denied:
    raise EncryptionError("Customer key unavailable - blocking operation")
    # NO fallback to unencrypted storage
```

### Compliance Mapping
- SOC 2 CC6.2 (Cryptographic Key Management)
- PCI-DSS 3.5 (Protect Cryptographic Keys)
- HIPAA 164.312(a)(2)(i) (Encryption)

---

## Layer 9: Audit Logging

### Purpose
Maintain immutable, hash-chained audit logs that comply with WORM (Write-Once-Read-Many) requirements for legal and compliance purposes.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Service | `immutable_audit_service.py` | `/services/immutable_audit_service.py` |
| Models | `models_audit.py` | `/models_audit.py` |
| Storage | PostgreSQL | `immutable_audit_logs` table |

### Audit Log Structure

```python
ImmutableAuditLog:
  id: UUID
  sequence_number: Integer (unique, auto-increment)
  timestamp: DateTime
  event_type: USER_ACTION | SYSTEM_EVENT | POLICY_VIOLATION
  actor_id: String
  resource_type: AGENT | TOOL | DATA | POLICY
  resource_id: String
  action: CREATE | READ | UPDATE | DELETE | EXECUTE
  outcome: SUCCESS | FAILURE | PENDING | DENIED
  event_data: JSON
  risk_level: LOW | MEDIUM | HIGH | CRITICAL
  compliance_tags: [SOX, HIPAA, PCI, GDPR]
  content_hash: SHA-256
  previous_hash: SHA-256 (chain link)
  chain_hash: SHA-256 (integrity)
  legal_hold: Boolean
  retention_until: DateTime
```

### Hash Chaining

```
Entry N-1                    Entry N                      Entry N+1
┌─────────────┐             ┌─────────────┐             ┌─────────────┐
│ content_hash│────────────▶│previous_hash│────────────▶│previous_hash│
│   (SHA-256) │             │ content_hash│             │ content_hash│
└─────────────┘             └─────────────┘             └─────────────┘
                                   │
                                   ▼
                            chain_hash = SHA-256(content_hash + previous_hash)
```

### Fail-Secure Behavior
```python
# If audit write fails, BLOCK the operation
try:
    audit_service.log(event)
except AuditWriteError:
    raise OperationBlocked("Audit logging unavailable")
```

### Compliance Mapping
- SOC 2 CC7.2 (System Monitoring)
- PCI-DSS 10.1 (Audit Trail Implementation)
- HIPAA 164.312(b) (Audit Controls)

---

## Layer 10: Input Validation

### Purpose
Validate and sanitize all input to prevent injection attacks and ensure data integrity.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Schemas | Pydantic | `/schemas.py`, route files |
| SQL | SQLAlchemy ORM | Parameterized queries |
| Sanitization | bleach | HTML/XSS sanitization |

### Validation Rules

| Input Type | Validation |
|------------|------------|
| Email | RFC 5322 format |
| Organization ID | Integer, FK constraint |
| Risk Score | Integer 0-100 |
| Pattern Values | Regex validation |
| JSON | Schema validation |

### SQL Injection Prevention

```python
# CORRECT: Parameterized queries
db.query(User).filter(User.email == email).first()

# NEVER: String concatenation
# db.execute(f"SELECT * FROM users WHERE email = '{email}'")  # DANGEROUS
```

### Fail-Secure Behavior
```python
# Invalid input rejected with 400 Bad Request
try:
    validated_data = schema.validate(input_data)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### Compliance Mapping
- OWASP Top 10 A1 (Injection)
- PCI-DSS 6.5.1 (Injection Flaws)

---

## Layer 11: Secrets Management

### Purpose
Securely store and retrieve sensitive configuration data using AWS Secrets Manager with environment variable fallback.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Config | `config.py` | `/config.py` |
| AWS | Secrets Manager | AWS us-east-2 |
| Local | Environment variables | `.env` (dev only) |

### Secret Loading Priority

```python
1. AWS Secrets Manager (production)
   └─ Fetch from AWS with caching

2. Environment Variables (development fallback)
   └─ LOCAL development only

3. Development Defaults (development only)
   └─ Ephemeral keys, change on restart
```

### Secret Validation

```python
# Production requirements
if ENVIRONMENT == "production":
    if len(SECRET_KEY) < 32:
        raise ConfigurationError("SECRET_KEY must be 32+ characters")

    if "dev-" in SECRET_KEY or "test-" in SECRET_KEY:
        raise ConfigurationError("Insecure secret detected")
```

### Fail-Secure Behavior
```python
# If secrets unavailable in production, FAIL startup
try:
    secrets = secrets_manager.get_secret()
except SecretsError:
    if ENVIRONMENT == "production":
        raise StartupError("Cannot start without secrets")
    else:
        use_development_defaults()
```

### Compliance Mapping
- SOC 2 CC6.1 (Logical Access)
- PCI-DSS 3.5 (Key Protection)

---

## Layer 12: Security Headers

### Purpose
Apply security headers to all HTTP responses to prevent common web vulnerabilities.

### Implementation

| Component | Technology | Location |
|-----------|------------|----------|
| Headers | `headers.py` | `/security/headers.py` |
| Middleware | FastAPI | `/main.py` |

### Headers Applied

| Header | Value | Purpose |
|--------|-------|---------|
| X-Frame-Options | DENY | Prevent clickjacking |
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-XSS-Protection | 1; mode=block | XSS filter (legacy) |
| Content-Security-Policy | default-src 'none' | Strict CSP |
| Strict-Transport-Security | max-age=63072000 | Force HTTPS (2 years) |
| Referrer-Policy | strict-origin-when-cross-origin | Limit referrer leakage |
| Permissions-Policy | (disabled features) | Disable browser features |
| Cache-Control | no-store, private | Prevent caching |

### CORS Configuration

```python
# Production origins (allowlist)
ALLOWED_ORIGINS = [
    "https://pilot.owkai.app",
    "https://app.owkai.app"
]

# Development origins
if ENVIRONMENT == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://localhost:5173"
    ])
```

### Compliance Mapping
- OWASP Top 10 A01 (Broken Access Control)
- PCI-DSS 6.5.10 (Cross-Site Scripting)

---

## Summary: Fail-Secure Matrix

| Layer | Component | Failure Mode | Default Action |
|-------|-----------|--------------|----------------|
| 1 | Rate Limiting | Redis unavailable | DENY |
| 2 | Prompt Security | Detector failure | BLOCK |
| 3 | Code Analysis | Analyzer error | BLOCK |
| 4 | Action Governance | Evaluator error | DENY |
| 5 | JWT Authentication | Invalid token | DENY (401) |
| 6 | API Key Validation | Validation failure | DENY (401) |
| 7 | RBAC | Permission check fails | DENY (403) |
| 8 | BYOK Encryption | CMK unavailable | FAIL (block operation) |
| 9 | Audit Logging | Write fails | BLOCK operation |
| 10 | Input Validation | Malformed input | REJECT (400) |
| 11 | Secrets Management | Fetch fails | FAIL startup (prod) |
| 12 | Security Headers | N/A | Always applied |

---

*Document ID: ASCEND-SEC-2024-001*
