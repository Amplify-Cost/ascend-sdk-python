---
sidebar_position: 2
title: SOC 2 Type II
description: SOC 2 Type II compliance controls and evidence
---

# SOC 2 Type II Compliance

Ascend is designed to meet SOC 2 Type II requirements across all five Trust Service Criteria.

## Trust Service Criteria Coverage

| Criteria | Status | Evidence |
|----------|--------|----------|
| Security (CC) | Compliant | Access controls, encryption, monitoring |
| Availability (A) | Compliant | 99.9% SLA, redundancy, DR |
| Processing Integrity (PI) | Compliant | Validation, audit trails |
| Confidentiality (C) | Compliant | Encryption, access controls |
| Privacy (P) | Compliant | Data handling, consent management |

---

## Common Criteria (CC) Controls

### CC6 - Logical and Physical Access Controls

#### CC6.1 - Logical Access Security

**Requirement:** The entity implements logical access security software, infrastructure, and architectures over protected information assets.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Authentication | JWT RS256 tokens with MFA | Auth logs, token validation |
| Authorization | Role-based access control (RBAC) | Policy engine, role mappings |
| Session Management | Secure session handling | Session timeout, invalidation |
| API Security | API key authentication | Key hashing, rotation policies |

**Code Reference:**
```python
# dependencies.py - Multi-tenant access control
async def get_organization_filter(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> int:
    """
    SOC 2 CC6.1: Returns organization_id for tenant isolation.
    All queries MUST use this for data segregation.
    """
    if current_user.organization_id is None:
        raise HTTPException(status_code=403, detail="User has no organization")
    return current_user.organization_id
```

**Audit Evidence:**
- Authentication event logs
- Failed login attempt tracking
- Session activity records
- API key usage logs

---

#### CC6.2 - Access Provisioning

**Requirement:** The entity restricts access to protected information assets.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| User Provisioning | Admin-controlled user creation | User creation audit logs |
| Role Assignment | Explicit role grants | Role assignment records |
| Access Review | Periodic access reviews | Review completion reports |
| Deprovisioning | Immediate access revocation | Deprovisioning timestamps |

**Agent Registration Controls:**
```json
{
  "agent_id": "customer-service-agent",
  "status": "draft",
  "requires_approval": true,
  "approved_by": "admin@company.com",
  "approved_at": "2025-01-15T10:30:00Z",
  "allowed_action_types": ["email_send", "ticket_create"],
  "blocked_resources": ["/admin/*", "/pii/*"]
}
```

---

#### CC6.3 - Access Removal

**Requirement:** The entity removes access when no longer required.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| User Deactivation | Immediate Cognito disable | Deactivation logs |
| Session Termination | Force logout on deactivation | Session invalidation records |
| API Key Revocation | Immediate key invalidation | Revocation timestamps |
| Agent Suspension | Immediate action blocking | Suspension audit trail |

---

### CC7 - System Operations

#### CC7.1 - Detection of Anomalies

**Requirement:** The entity detects anomalies and evaluates them for security events.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Anomaly Detection | ML-powered pattern analysis | Detection alerts |
| Threshold Monitoring | Configurable thresholds | Threshold breach logs |
| Real-time Alerting | Immediate notifications | Alert delivery records |
| Trend Analysis | Historical pattern comparison | Trend reports |

**Detection Capabilities:**
```json
{
  "anomaly_detection": {
    "enabled": true,
    "sensitivity": "high",
    "baseline_period_days": 14,
    "detection_types": [
      "volume_spike",
      "unusual_timing",
      "new_resource_access",
      "risk_score_deviation"
    ]
  }
}
```

---

#### CC7.2 - Monitoring System Components

**Requirement:** The entity monitors system components and the operation of those components for anomalies.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| System Health | CloudWatch monitoring | Health dashboards |
| Performance Metrics | Real-time metrics collection | Performance logs |
| Error Tracking | Centralized error logging | Error reports |
| Capacity Monitoring | Resource utilization tracking | Capacity alerts |

**Metrics Tracked:**
- CPU utilization
- Memory usage
- API response times
- Database connections
- Error rates
- Request throughput

---

## Availability (A) Controls

### A1.1 - Availability Commitments

**Requirement:** The entity maintains availability commitments.

**Ascend SLA:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime | 99.9% | Monthly calculation |
| RTO | 4 hours | Recovery time objective |
| RPO | 1 hour | Recovery point objective |
| Response Time | < 200ms | P95 API latency |

---

### A1.2 - Availability Monitoring

**Requirement:** The entity monitors availability.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Health Checks | Continuous endpoint monitoring | Health check logs |
| Alerting | PagerDuty integration | Alert records |
| Status Page | Public status dashboard | Status history |
| Incident Response | Documented runbooks | Incident reports |

---

## Processing Integrity (PI) Controls

### PI1.1 - Processing Accuracy

**Requirement:** The entity ensures processing integrity.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Input Validation | Server-side validation | Validation logs |
| Data Integrity | Checksums and hashes | Integrity verification |
| Transaction Logging | Complete audit trail | Transaction records |
| Error Handling | Graceful error management | Error logs |

**Unified Metrics Engine (SEC-066):**
```python
# Ensures consistent metric calculations across all endpoints
class UnifiedMetricsEngine:
    """
    SOC 2 PI-1: Single source of truth for all metrics.
    Prevents inconsistencies between dashboard components.
    """
    def calculate(self, period_hours: int) -> MetricSnapshot:
        # All metrics calculated from single query
        # Results cached and validated
        # Audit trail for every calculation
        pass
```

---

### PI1.2 - Processing Completeness

**Requirement:** The entity ensures complete processing.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Action Tracking | End-to-end action logging | Action records |
| Pipeline Verification | 7-step pipeline validation | Pipeline logs |
| Completion Confirmation | Status confirmation | Status records |
| Reconciliation | Periodic data reconciliation | Reconciliation reports |

---

## Confidentiality (C) Controls

### C1.1 - Confidential Information Protection

**Requirement:** The entity protects confidential information.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Encryption at Rest | AES-256-GCM | KMS configuration |
| Encryption in Transit | TLS 1.3 | Certificate records |
| Data Classification | Automatic classification | Classification tags |
| Access Logging | All access logged | Access logs |

---

### C1.2 - Confidential Information Disposal

**Requirement:** The entity disposes of confidential information.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Data Retention | Configurable retention periods | Retention policies |
| Secure Deletion | Cryptographic erasure | Deletion logs |
| Backup Purging | Automated backup expiration | Purge records |
| Audit Trail Retention | 7-year retention | Retention verification |

---

## Privacy (P) Controls

### P1.1 - Privacy Notice

**Requirement:** The entity provides notice regarding privacy practices.

**Ascend Implementation:**

| Control | Implementation | Evidence |
|---------|----------------|----------|
| Privacy Policy | Published privacy policy | Policy document |
| Data Collection Notice | Clear data usage disclosure | Notice records |
| Consent Management | Explicit consent collection | Consent logs |
| Policy Updates | Version-controlled updates | Update history |

---

## Audit Evidence Collection

### Continuous Evidence Generation

Ascend automatically generates audit evidence:

```json
{
  "evidence_type": "access_control",
  "timestamp": "2025-01-15T14:30:00Z",
  "control": "CC6.1",
  "event": {
    "type": "user_authentication",
    "user_id": "user@company.com",
    "method": "jwt_mfa",
    "result": "success",
    "ip_address": "10.0.1.50"
  },
  "attestation": {
    "generated_by": "ascend_audit_engine",
    "integrity_hash": "sha256:abc123..."
  }
}
```

### Evidence Export

```bash
# Export SOC 2 evidence package
curl -X POST "https://pilot.owkai.app/api/compliance/export/soc2" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "controls": ["CC6.1", "CC6.2", "CC7.1", "CC7.2"],
    "format": "pdf"
  }'
```

**Response:**
```json
{
  "export_id": "exp_20250115_soc2_a1b2c3d4",
  "status": "generating",
  "estimated_completion": "2025-01-15T14:35:00Z",
  "download_url": "https://pilot.owkai.app/api/compliance/exports/exp_20250115_soc2_a1b2c3d4"
}
```

---

## Control Mapping Reference

### Action Type to SOC 2 Control Mapping

| Action Type | Primary Control | Secondary Controls |
|-------------|-----------------|-------------------|
| database_read | CC6.1 | CC7.2, C1.1 |
| database_write | CC6.1 | PI1.1, AU-9 |
| database_delete | CC6.1 | CC7.1, CM-3 |
| file_read | CC6.1 | C1.1, AU-2 |
| file_write | CC6.1 | PI1.1, CC7.2 |
| user_create | CC6.2 | IA-4, AU-2 |
| user_delete | CC6.3 | AU-2, CC7.1 |
| config_change | CC7.2 | CM-3, AU-9 |
| data_export | C1.1 | CC6.1, SI-12 |
| api_call | CC6.1 | CC7.2, AU-2 |

---

## Auditor Resources

### Documentation Package

| Document | Description | Access |
|----------|-------------|--------|
| System Description | Architecture overview | On request |
| Control Matrix | Detailed control mappings | On request |
| Evidence Package | Generated audit evidence | API export |
| Penetration Test | Annual pentest results | On request |
| Vulnerability Scans | Continuous scan results | On request |

### Contact

For SOC 2 audit inquiries:
- Email: compliance@owkai.app
- Audit Coordinator: Available during audit periods

---

*SOC 2 Type II report available upon request with NDA.*
