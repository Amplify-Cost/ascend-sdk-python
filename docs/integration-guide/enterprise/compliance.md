# Compliance & Reporting

Ascend provides comprehensive compliance support for major regulatory frameworks with automated reporting and audit trail management.

## Supported Frameworks

| Framework | Status | Features |
|-----------|--------|----------|
| SOC 2 Type II | Compliant | Audit logs, access controls, encryption |
| HIPAA | Compliant | PHI protection, access logging, BAA available |
| GDPR | Compliant | Data subject rights, consent tracking, DPA available |
| PCI-DSS | Compliant | Cardholder data protection, encryption |
| SOX | Compliant | Financial controls, segregation of duties |

## Compliance API

### List Available Frameworks

```bash
curl https://pilot.owkai.app/api/compliance/frameworks \
  -b cookies.txt
```

**Response:**

```json
{
  "frameworks": [
    {
      "id": "soc2",
      "name": "SOC 2 Type II",
      "description": "Service Organization Control 2",
      "controls": 64,
      "enabled": true
    },
    {
      "id": "hipaa",
      "name": "HIPAA",
      "description": "Health Insurance Portability and Accountability Act",
      "controls": 42,
      "enabled": true
    },
    {
      "id": "gdpr",
      "name": "GDPR",
      "description": "General Data Protection Regulation",
      "controls": 38,
      "enabled": true
    },
    {
      "id": "pci_dss",
      "name": "PCI-DSS",
      "description": "Payment Card Industry Data Security Standard",
      "controls": 12,
      "enabled": true
    },
    {
      "id": "sox",
      "name": "SOX",
      "description": "Sarbanes-Oxley Act",
      "controls": 28,
      "enabled": true
    }
  ]
}
```

### Get Framework Details

```bash
curl https://pilot.owkai.app/api/compliance/frameworks/soc2 \
  -b cookies.txt
```

## Compliance Exports

### Create Export Job

```bash
curl -X POST https://pilot.owkai.app/api/compliance/exports \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "framework": "soc2",
    "report_type": "controls_assessment",
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-03-31"
    },
    "format": "pdf",
    "include_evidence": true
  }'
```

### Report Types

| Type | Description |
|------|-------------|
| `controls_assessment` | Control effectiveness assessment |
| `audit_log_summary` | Audit log activity summary |
| `access_review` | User access review report |
| `policy_compliance` | Policy compliance status |
| `incident_report` | Security incident summary |
| `risk_assessment` | Risk scoring analysis |

### Quick Export

```bash
curl -X POST https://pilot.owkai.app/api/compliance/quick-export/soc2/controls_assessment \
  -b cookies.txt
```

### Download Export

```bash
curl https://pilot.owkai.app/api/compliance/exports/job_123/download \
  -b cookies.txt \
  -o compliance_report.pdf
```

## Scheduled Reports

### Create Schedule

```bash
curl -X POST https://pilot.owkai.app/api/compliance/schedules \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Monthly SOC 2 Report",
    "framework": "soc2",
    "report_type": "controls_assessment",
    "schedule": "0 0 1 * *",
    "format": "pdf",
    "recipients": ["compliance@company.com", "audit@company.com"],
    "enabled": true
  }'
```

### Schedule Formats

| Schedule | Description |
|----------|-------------|
| `0 0 * * *` | Daily at midnight |
| `0 0 * * 1` | Weekly on Monday |
| `0 0 1 * *` | Monthly on 1st |
| `0 0 1 */3 *` | Quarterly |

## SOC 2 Controls

### Trust Service Criteria

| Category | Controls | Description |
|----------|----------|-------------|
| CC1 | Control Environment | Integrity, ethical values |
| CC2 | Communication | Information quality |
| CC3 | Risk Assessment | Risk identification |
| CC4 | Monitoring | Performance monitoring |
| CC5 | Control Activities | Policies and procedures |
| CC6 | Logical Access | Access controls |
| CC7 | System Operations | Change management |
| CC8 | Change Management | System changes |
| CC9 | Risk Mitigation | Business continuity |

### Ascend SOC 2 Evidence

| Control | Ascend Feature |
|---------|----------------|
| CC6.1 | Multi-tenant data isolation |
| CC6.2 | Role-based access control |
| CC6.3 | API key authentication |
| CC6.6 | Audit logging |
| CC7.1 | Automated deployment verification |
| CC7.2 | Security monitoring |

## HIPAA Controls

### Administrative Safeguards

| Control | Ascend Implementation |
|---------|----------------------|
| 164.308(a)(1) | Risk analysis and management |
| 164.308(a)(3) | Workforce security |
| 164.308(a)(4) | Access authorization |
| 164.308(a)(5) | Security awareness training |

### Technical Safeguards

| Control | Ascend Implementation |
|---------|----------------------|
| 164.312(a)(1) | Unique user identification |
| 164.312(b) | Audit controls |
| 164.312(c)(1) | Integrity controls |
| 164.312(d) | Authentication |
| 164.312(e)(1) | Transmission security |

## GDPR Compliance

### Data Subject Rights

Ascend provides APIs for handling data subject requests:

```bash
# Data Access Request
curl -X POST https://pilot.owkai.app/api/data-rights/access/request \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "subject_email": "user@example.com",
    "request_type": "access"
  }'

# Data Erasure Request
curl -X POST https://pilot.owkai.app/api/data-rights/erasure/request \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "subject_email": "user@example.com",
    "request_type": "erasure"
  }'

# Data Portability Request
curl -X POST https://pilot.owkai.app/api/data-rights/portability/request \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "subject_email": "user@example.com",
    "format": "json"
  }'
```

### Consent Management

```bash
curl -X POST https://pilot.owkai.app/api/data-rights/consent/record \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "subject_email": "user@example.com",
    "consent_type": "data_processing",
    "granted": true,
    "purpose": "AI governance monitoring"
  }'
```

## Compliance Metrics

```bash
curl https://pilot.owkai.app/api/compliance/metrics \
  -b cookies.txt
```

**Response:**

```json
{
  "overall_score": 94,
  "frameworks": {
    "soc2": {
      "score": 96,
      "controls_passed": 62,
      "controls_total": 64
    },
    "hipaa": {
      "score": 92,
      "controls_passed": 39,
      "controls_total": 42
    }
  },
  "recent_findings": 3,
  "open_remediation": 2
}
```

## Audit Trail

All compliance-related activities are logged:

```bash
curl https://pilot.owkai.app/api/audit/logs?category=compliance \
  -b cookies.txt
```

## Best Practices

1. **Regular exports** - Schedule weekly/monthly compliance reports
2. **Evidence collection** - Enable `include_evidence` for audits
3. **Access reviews** - Conduct quarterly user access reviews
4. **Policy updates** - Review policies after any compliance changes
5. **Training** - Document security awareness training

## Next Steps

- [Audit Logging](/core-concepts/audit-logging) - Detailed audit trail
- [Data Rights](/security/data-encryption) - Data protection
- [Security Overview](/security/overview) - Security architecture
