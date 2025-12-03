# Ascend Enterprise Integration Guide

**Document ID:** ASCEND-INT-001
**Version:** 2.0.0
**Classification:** Customer Documentation
**Compliance:** SOC 2 Type II, PCI-DSS, HIPAA, GDPR
**Publisher:** OW-kai Corporation

---

## Overview

Welcome to the Ascend Enterprise AI Agent Governance Platform by OW-kai. This guide provides everything you need to integrate your AI agents with our enterprise-grade governance, risk assessment, and compliance system.

### Key Features

- **Enterprise Risk Scoring**: Multi-factor risk calculation using CVSS, policy evaluation, and hybrid scoring
- **Real-Time Policy Enforcement**: Sub-200ms policy evaluation with natural language support
- **Compliance Mapping**: Automatic NIST 800-53 and MITRE ATT&CK mapping for all actions
- **Multi-Tenant Isolation**: Banking-level data isolation between organizations
- **Automation Workflows**: Playbook-based auto-approval and orchestration

---

## Quick Start

### Step 1: Generate API Key

1. Log into the Ascend dashboard
2. Navigate to **Settings > API Keys**
3. Click **Generate New Key**
4. Copy and securely store your API key (format: `ascend_<prefix>_<secret>`)

### Step 2: Submit Your First Action

```bash
curl -X POST https://your-domain.ascendowkai.com/api/authorization/agent-action \
  -H "Authorization: Bearer ascend_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-001",
    "action_type": "database.read",
    "tool_name": "postgres_query",
    "description": "Querying user analytics data"
  }'
```

### Step 3: Check Response

```json
{
  "id": 12345,
  "action_id": 12345,
  "agent_id": "your-agent-001",
  "status": "approved",
  "risk_score": 35,
  "risk_level": "low",
  "requires_approval": false,
  "approved": true,
  "enterprise_grade": true,
  "compliance": {
    "nist_control": "AU-12",
    "mitre_tactic": "TA0009",
    "cvss_score": 3.5
  },
  "risk_assessment": {
    "policy_evaluated": true,
    "policy_risk": 30,
    "hybrid_risk": 35,
    "fusion_applied": true
  }
}
```

---

## Integration Endpoints

| Endpoint | Purpose | Authentication | Use Case |
|----------|---------|----------------|----------|
| `POST /api/authorization/agent-action` | Full enterprise pipeline | API Key or JWT | Production integrations |
| `POST /api/sdk/agent-action` | SDK-optimized endpoint | API Key | OW-kai SDK users |
| `GET /api/agent-action/status/{id}` | Poll action status | API Key or JWT | Async workflows |
| `POST /api/authorization/approve/{id}` | Approve pending action | JWT (Admin) | Manual approvals |

### Recommended Endpoint Selection

- **SDK Users**: Use `/api/sdk/agent-action` - optimized for Ascend SDK integration
- **Direct API Integration**: Use `/api/authorization/agent-action` - full enterprise features
- **Both endpoints now provide identical enterprise-grade risk scoring**

---

## Risk Scoring Architecture

Ascend uses a sophisticated multi-layer risk scoring system:

### 1. First-Pass Enrichment
- Action type analysis
- Tool name classification
- Target system evaluation

### 2. CVSS Assessment
- CVSS 3.1 vector calculation
- Severity classification (None, Low, Medium, High, Critical)
- Score normalization to 0-100 scale

### 3. Policy Engine Evaluation
- Natural language policy matching
- Organization-specific rules
- Real-time evaluation (<200ms)

### 4. Hybrid Risk Calculator
```
Hybrid Risk = (Environment × 35%) + (Data Sensitivity × 30%) +
              (CVSS × 25%) + (Operational Context × 10%) × Resource Multiplier
```

### 5. Risk Fusion (Final Score)
```
Final Risk Score = (Policy Risk × 80%) + (Hybrid Risk × 20%)
```

### Safety Rules (Always Applied)
1. **CRITICAL CVSS Floor**: If CVSS severity is CRITICAL, minimum score is 85
2. **Policy DENY Override**: If policy decision is DENY, score is set to 100
3. **PII Production Floor**: PII in production environment, minimum score is 70

---

## Response Fields Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique action identifier |
| `status` | string | Current status: `approved`, `pending`, `denied` |
| `risk_score` | integer | Final fused risk score (0-100) |
| `risk_level` | string | Risk classification: `low`, `medium`, `high`, `critical` |
| `requires_approval` | boolean | Whether manual approval is needed |
| `approved` | boolean | Current approval state |
| `compliance.nist_control` | string | Mapped NIST 800-53 control |
| `compliance.mitre_tactic` | string | Mapped MITRE ATT&CK tactic |
| `compliance.cvss_score` | float | CVSS base score (0-10) |
| `risk_assessment.policy_risk` | integer | Policy engine score |
| `risk_assessment.hybrid_risk` | integer | Multi-factor hybrid score |
| `risk_assessment.fusion_applied` | boolean | Whether fusion was used |
| `automation.playbook` | object | Playbook match results |
| `automation.workflow` | object | Workflow trigger results |

---

## Supported Action Types

### Database Operations
- `database.read` - Read queries (Low risk)
- `database.write` - Insert/Update operations (Medium risk)
- `database.delete` - Delete operations (High risk)
- `database.schema_change` - DDL operations (Critical risk)

### File System Operations
- `file.read` - File read access (Low risk)
- `file.write` - File write operations (Medium risk)
- `file.delete` - File deletion (High risk)
- `file.permission_change` - Permission modifications (High risk)

### Financial Operations
- `financial.read` - Account queries (Medium risk)
- `financial.transfer` - Money transfers (High risk)
- `financial.bulk_transfer` - Bulk operations (Critical risk)

### Security Operations
- `security.authentication` - Auth events (Medium risk)
- `security.access_control` - Permission changes (High risk)
- `security.encryption_change` - Encryption modifications (Critical risk)

### Communication Operations
- `email.send` - Email dispatch (Medium risk)
- `email.bulk_send` - Bulk email (High risk)
- `sms.send` - SMS dispatch (Medium risk)

---

## Authentication

### API Key Authentication
```bash
Authorization: Bearer ascend_your_api_key_here
```

### JWT Authentication (Dashboard Users)
```bash
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Key Security Best Practices
1. Never commit API keys to version control
2. Use environment variables for key storage
3. Rotate keys every 90 days
4. Use separate keys for development/production
5. Monitor key usage in the dashboard

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message description",
  "error_code": "ERR_CODE",
  "timestamp": "2025-12-03T00:00:00Z"
}
```

### Common Error Codes
| HTTP Status | Code | Description |
|-------------|------|-------------|
| 401 | `AUTH_REQUIRED` | Missing or invalid authentication |
| 403 | `ACCESS_DENIED` | Insufficient permissions |
| 422 | `VALIDATION_ERROR` | Invalid request payload |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server-side error |

---

## Rate Limits

| Tier | Requests/Minute | Burst |
|------|-----------------|-------|
| Standard | 100 | 150 |
| Enterprise | 1000 | 1500 |
| Unlimited | No limit | No limit |

---

## Support

- **Documentation**: https://docs.ascendowkai.com
- **Support Email**: support@ascendowkai.com
- **Status Page**: https://status.ascendowkai.com
- **API Reference**: /api/docs (Swagger UI)

---

## Next Steps

1. [Risk Scoring Deep Dive](./RISK_SCORING.md)
2. [API Reference](./API_REFERENCE.md)
3. [SDK Guide](./SDK_GUIDE.md)
4. [Architecture Overview](./ARCHITECTURE.md)

---

*Document Version: 2.0.0 | Last Updated: December 2025 | Compliance: SOC 2 CC6.1, PCI-DSS 7.1, NIST 800-53*
