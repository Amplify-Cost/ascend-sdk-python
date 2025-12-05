# Compliance

Ascend aligns with major security and privacy frameworks for enterprise AI governance.

## Compliance Status

### SOC 2 Type II {#soc2}

**Status**: Compliant

SOC 2 compliance demonstrates our commitment to security, availability, processing integrity, confidentiality, and privacy.

**Scope**:
- AI governance platform
- Agent action management
- Audit logging systems
- Customer data handling

**Controls Implemented**:

| Control Category | Implementation | Backend Reference |
|-----------------|----------------|-------------------|
| Access Control | Multi-tenant isolation, RBAC | `dependencies.py` (SEC-007) |
| Audit Logging | Immutable audit trails | `data_rights_routes.py` |
| Change Management | Version control, deployment tracking | GitHub Actions |
| Incident Response | Anomaly detection, circuit breakers | `anomaly_detection_service.py` (SEC-077) |
| Data Encryption | TLS 1.3, bcrypt, RDS encryption | `models.py`, AWS RDS |

**Compliance Mapping**:
- **CC6.1**: Logical access controls (RBAC, organization isolation)
- **CC7.1**: System monitoring (anomaly detection, circuit breakers)
- **AU-6**: Audit review and analysis (immutable audit logs)
- **PI-1**: Processing integrity (unified metrics engine, SEC-066)

### HIPAA {#hipaa}

**Status**: Compliant

Health Insurance Portability and Accountability Act compliance for protected health information (PHI).

**Features**:
- Business Associate Agreement (BAA) available
- PHI handling controls via data rights APIs
- Comprehensive audit logging for healthcare data
- Row-level access controls per organization

**Technical Controls**:

| HIPAA Requirement | Implementation | Source |
|------------------|----------------|--------|
| 164.312(a)(1) - Access Control | Organization-level isolation | `dependencies.py` |
| 164.312(d) - Integrity | Immutable audit logs | `data_rights_routes.py` |
| 164.312(e) - Transmission Security | TLS 1.3 enforced | AWS Infrastructure |

**Requirements**:
- Enterprise plan required
- Signed BAA
- HIPAA-specific configuration

### PCI-DSS {#pci-dss}

**Status**: Compliant

Payment Card Industry Data Security Standard compliance.

**Controls**:

| Requirement | Implementation | Backend Reference |
|------------|----------------|-------------------|
| 7.1 - Access Control | RBAC, approval levels | `models.py` (User model) |
| 8.2.3 - Password Security | bcrypt cost 12 | `models.py` (line 33) |
| 8.3.1 - API Key Security | PBKDF2-HMAC-SHA256 | `api_key_routes.py` (SEC-018) |
| 10.2 - Audit Trail | Immutable event logging | `data_rights_routes.py` |
| 10.6 - Log Review | Anomaly detection | `anomaly_detection_service.py` (SEC-077) |

**Audit Requirements**:
- All authentication attempts logged
- All data access logged with organization ID
- All high-risk actions logged with risk scores

### GDPR {#gdpr}

**Status**: Compliant

General Data Protection Regulation compliance for EU data.

**Data Subject Rights Implementation**:

All GDPR rights are implemented via `/api/data-rights/*` endpoints:

| Right | GDPR Article | API Endpoint | Implementation |
|-------|-------------|--------------|----------------|
| Right to Access | Article 15 | `POST /api/data-rights/access/request` | Lines 105-194 |
| Right to Erasure | Article 17 | `POST /api/data-rights/erasure/request` | Lines 294-389 |
| Data Portability | Article 20 | `POST /api/data-rights/portability/request` | Lines 490-564 |
| Consent Management | Articles 6-7 | `POST /api/data-rights/consent/record` | Lines 570-642 |

**Source**: `/ow-ai-backend/routes/data_rights_routes.py`

**Features**:
- 30-day response deadline tracking (GDPR Article 12)
- Verification workflow for data subject requests
- Cross-system data discovery and retrieval
- Retention exception handling for legal obligations
- Immutable audit logging for all requests

**Data Lineage**:
```python
# Track data flow across systems
POST /api/data-rights/lineage/record
{
    "subject_identifier": "user@example.com",
    "data_type": "profile_data",
    "source_system": "auth_service",
    "destination_system": "analytics_db",
    "processing_purpose": "service_improvement",
    "legal_basis": "GDPR Article 6(1)(f)",
    "retention_period": "90_days"
}
```

**Source**: `/ow-ai-backend/routes/data_rights_routes.py` (lines 648-719)

### SOX

**Status**: Compliant

Sarbanes-Oxley Act compliance for financial controls.

**Features**:
- Immutable audit trails (no delete/update of audit records)
- Segregation of duties (role-based access control)
- Change management controls (deployment tracking)
- Access reviews (user management with suspension capability)

**Implementation**:

| SOX Control | Implementation | Backend Reference |
|------------|----------------|-------------------|
| Audit Trail | Append-only event logging | `data_rights_routes.py` |
| Segregation of Duties | RBAC with approval levels | `models.py` (User model) |
| Access Controls | Multi-tenant isolation | `dependencies.py` (SEC-007) |
| Change Management | Deployment info endpoint | `main.py` (SEC-010) |

## Compliance Reports

### Self-Service Reports

Generate compliance reports from the Dashboard or API:

**Available Reports**:
- Access audit report (all user authentication events)
- Action history report (all agent actions with risk scores)
- Policy compliance report (policy violations and approvals)
- GDPR compliance report (data subject request processing)

**API Endpoint**:
```bash
curl -X GET "https://pilot.owkai.app/api/data-rights/compliance/report?start_date=2025-01-01&end_date=2025-01-31&report_type=SUMMARY" \
  -b cookies.txt
```

**Response**:
```json
{
    "report_type": "SUMMARY",
    "period": {
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z"
    },
    "compliance_metrics": {
        "total_requests": 45,
        "average_response_time_hours": 18,
        "sla_compliance_rate": 98.5,
        "requests_by_type": {
            "ACCESS": 20,
            "ERASURE": 15,
            "PORTABILITY": 10
        }
    }
}
```

**Source**: `/ow-ai-backend/routes/data_rights_routes.py` (lines 764-807)

## Data Processing

### Multi-Tenant Data Isolation

**Implementation**: Every database query is automatically filtered by `organization_id`

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
```

**Tables with Isolation**:
- users
- alerts
- agent_actions
- smart_rules
- api_keys
- audit_logs

**Source**: `/ow-ai-backend/dependencies.py`, `/ow-ai-backend/models.py`

### Data Retention

| Data Type | Backend Storage | Configurable |
|-----------|-----------------|--------------|
| Audit Logs | PostgreSQL (encrypted) | Organization-level |
| Action History | PostgreSQL (encrypted) | Organization-level |
| Agent Data | PostgreSQL (encrypted) | Per-agent settings |
| User Sessions | JWT (1 hour expiration) | Fixed |

**GDPR Compliance**: Retention periods can be customized per organization to meet legal obligations while respecting data minimization principles.

## Regional Compliance

### United States
- SOC 2 Type II compliant
- HIPAA compliant (with BAA)
- SOX compliant (financial controls)

### European Union
- GDPR compliant (data subject rights APIs)
- EU data residency available (AWS eu-west-1, eu-central-1)
- Standard Contractual Clauses supported

### United Kingdom
- UK GDPR compliant
- International Data Transfer Agreement supported

## Security Questionnaires

### Common Security Questions

**Q: Where is data stored?**
A: Data is stored in AWS RDS PostgreSQL databases with encryption at rest. US customers use us-east-2 (Ohio), EU customers can choose EU-only regions.

**Q: Is data encrypted?**
A: Yes. TLS 1.3 in transit, AWS RDS encryption at rest, bcrypt for passwords, PBKDF2-HMAC-SHA256 for API keys.

**Q: How is multi-tenant isolation enforced?**
A: Row-level security via `organization_id` filtering on all database queries. Implemented in `dependencies.py` (SEC-007).

**Q: What audit capabilities exist?**
A: Immutable audit logs for all high-risk operations, GDPR-compliant data access tracking, anomaly detection with Z-score analysis.

**Q: Can you sign a BAA for HIPAA?**
A: Yes, for enterprise customers handling PHI. Contact your account manager.

## Compliance Automation

### Continuous Compliance Monitoring

Ascend provides built-in compliance monitoring:

**Anomaly Detection** (SEC-077):
```python
# From anomaly_detection_service.py
z = (current_value - baseline_mean) / standard_deviation

# Automatic alerts for:
# - Unusual action frequencies
# - Elevated error rates
# - Abnormal risk score patterns
# - Consecutive policy violations
```

**Circuit Breaker** (SEC-077):
```python
# From circuit_breaker_service.py
# Automatic isolation of failing MCP servers
# Prevents cascade failures
# SOC 2 CC7.1, NIST SI-4 compliance
```

**Policy Conflict Detection** (SEC-077):
```python
# From policy_conflict_resolver.py
# Detects:
# - Priority ties on overlapping scopes
# - Effect contradictions (ALLOW vs DENY)
# - Resource overlap ambiguities
# PCI-DSS 7.1, NIST AC-3 compliance
```

### Compliance Dashboard

View compliance status in real-time via:
- Dashboard: [pilot.owkai.app](https://pilot.owkai.app)
- API: `GET /api/data-rights/compliance/report`

**Metrics Available**:
- Policy adherence rate
- SLA compliance for data subject requests
- Audit trail completeness
- Access control effectiveness

## Implementation References

All compliance features are implemented in:

| Feature | Backend File | Compliance Standard |
|---------|-------------|-------------------|
| GDPR Data Rights | `data_rights_routes.py` | GDPR Articles 15, 17, 20 |
| Multi-Tenant Isolation | `dependencies.py` | SOC 2 CC6.1, PCI-DSS 7.1 |
| Anomaly Detection | `anomaly_detection_service.py` | SOC 2 CC7.1, NIST SI-4 |
| Circuit Breaker | `circuit_breaker_service.py` | SOC 2 CC7.1, PCI-DSS 6.5.5 |
| Policy Enforcement | `cedar_enforcement_service.py` | NIST AC-3, PCI-DSS 7.1 |
| Audit Logging | `data_rights_routes.py` | SOC 2 AU-6, PCI-DSS 10.2 |

## Next Steps

- [Security Overview](/security/overview) - Security architecture
- [Data Encryption](/security/data-encryption) - Encryption implementation details
- [Data Rights APIs](/sdk/rest/authentication) - GDPR compliance integration
