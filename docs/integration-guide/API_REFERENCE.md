---
title: Ascend API Reference
sidebar_position: 1
---

# Ascend API Reference

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-HELP-003 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

**Document ID:** ASCEND-INT-003
**Version:** 2.0.0
**Classification:** Technical Reference
**Publisher:** OW-kai Corporation
**Base URL:** `https://your-domain.ascendowkai.com`

---

## Authentication

All API requests require authentication via API Key or JWT token.

### API Key Authentication
```
Authorization: Bearer ascend_<prefix>_<secret>
```

### JWT Authentication (Dashboard users)
```
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### POST /api/authorization/agent-action

Submit an agent action for governance evaluation.

**Authentication:** API Key or JWT

**Request Body:**
```json
{
  "agent_id": "string (required)",
  "action_type": "string (required)",
  "tool_name": "string (required)",
  "description": "string (required)",
  "target_system": "string (optional)",
  "environment": "string (optional, default: 'production')",
  "contains_pii": "boolean (optional, default: false)",
  "resource_type": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "id": 12345,
  "action_id": 12345,
  "agent_id": "finance-agent-001",
  "action_type": "database.read",
  "status": "approved",
  "risk_score": 35,
  "risk_level": "low",
  "requires_approval": false,
  "approved": true,
  "alert_generated": false,
  "alert_id": null,
  "poll_url": "/api/agent-action/status/12345",
  "enterprise_grade": true,
  "auth_api_integration": true,
  "compliance": {
    "nist_control": "AU-12",
    "nist_description": "Audit Generation",
    "mitre_tactic": "TA0009",
    "mitre_technique": "T1005",
    "recommendation": "Enable audit logging for this action type",
    "cvss_score": 3.5,
    "cvss_severity": "LOW",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N"
  },
  "risk_assessment": {
    "policy_evaluated": true,
    "policy_risk": 30,
    "policy_decision": "PolicyDecision.allow",
    "hybrid_risk": 35,
    "hybrid_breakdown": {
      "environment_factor": 35.0,
      "data_sensitivity_factor": 9.0,
      "cvss_factor": 8.75,
      "operational_factor": 2.0
    },
    "hybrid_formula": "(100×35%)+(30×30%)+(35×25%)+(20×10%)",
    "fusion_applied": true,
    "fusion_formula": "(30 × 0.8) + (35 × 0.2)"
  },
  "automation": {
    "playbook": {
      "matched": false
    },
    "workflow": {
      "workflow_triggered": false,
      "workflow_id": null,
      "alert_created": false
    }
  },
  "message": "Enterprise action processed - Risk: 35, Level: low"
}
```

**Error Responses:**

| Status | Description |
|--------|-------------|
| 401 | Authentication required |
| 403 | Access denied |
| 422 | Validation error (missing required fields) |
| 500 | Internal server error |

---

### POST /api/sdk/agent-action

SDK-optimized endpoint for agent action submission. Provides identical enterprise-grade risk scoring.

**Authentication:** API Key

**Request Body:**
```json
{
  "agent_id": "string (required)",
  "action_type": "string (required)",
  "tool_name": "string (required)",
  "description": "string (required)",
  "target_system": "string (optional)",
  "environment": "string (optional)",
  "contains_pii": "boolean (optional)",
  "resource": "string (optional)",
  "resource_type": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "id": 12345,
  "action_id": 12345,
  "agent_id": "finance-agent-001",
  "action_type": "database.read",
  "status": "approved",
  "risk_score": 35,
  "risk_level": "low",
  "requires_approval": false,
  "approved": true,
  "alert_generated": false,
  "alert_id": null,
  "poll_url": "/api/agent-action/status/12345",
  "enterprise_grade": true,
  "sdk_integration": true,
  "compliance": {
    "nist_control": "AU-12",
    "nist_description": "Audit Generation",
    "mitre_tactic": "TA0009",
    "mitre_technique": "T1005",
    "recommendation": "Enable audit logging",
    "cvss_score": 3.5,
    "cvss_severity": "LOW",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N"
  },
  "risk_assessment": {
    "policy_evaluated": true,
    "policy_risk": 30,
    "policy_decision": "PolicyDecision.allow",
    "hybrid_risk": 35,
    "fusion_applied": true,
    "fusion_formula": "(30 × 0.8) + (35 × 0.2)"
  },
  "automation": {
    "playbook": {"matched": false},
    "workflow": {"workflow_triggered": false}
  }
}
```

---

### GET /api/agent-action/status/{action_id}

Poll the status of a submitted action.

**Authentication:** API Key or JWT

**Path Parameters:**
- `action_id` (integer): The action ID from the submission response

**Response (200 OK):**
```json
{
  "id": 12345,
  "agent_id": "finance-agent-001",
  "action_type": "database.read",
  "status": "approved",
  "risk_score": 35,
  "risk_level": "low",
  "requires_approval": false,
  "approved": true,
  "reviewed_by": null,
  "reviewed_at": null,
  "created_at": "2025-12-03T12:00:00Z"
}
```

---

### POST /api/authorization/approve/{action_id}

Approve a pending action. Requires admin or security_manager role.

**Authentication:** JWT (Admin/Security Manager)

**Path Parameters:**
- `action_id` (integer): The action ID to approve

**Request Body:**
```json
{
  "approval_notes": "string (optional)"
}
```

**Response (200 OK):**
```json
{
  "id": 12345,
  "status": "approved",
  "approved": true,
  "reviewed_by": "admin@company.com",
  "reviewed_at": "2025-12-03T12:30:00Z",
  "message": "Action approved successfully"
}
```

---

### POST /api/authorization/deny/{action_id}

Deny a pending action. Requires admin or security_manager role.

**Authentication:** JWT (Admin/Security Manager)

**Path Parameters:**
- `action_id` (integer): The action ID to deny

**Request Body:**
```json
{
  "rejection_reason": "string (required)"
}
```

**Response (200 OK):**
```json
{
  "id": 12345,
  "status": "denied",
  "approved": false,
  "reviewed_by": "security@company.com",
  "reviewed_at": "2025-12-03T12:30:00Z",
  "rejection_reason": "Action violates security policy",
  "message": "Action denied"
}
```

---

### GET /api/agent-activity

Get recent agent activity for the organization.

**Authentication:** JWT

**Query Parameters:**
- `limit` (integer, optional): Number of records (default: 100, max: 1000)
- `offset` (integer, optional): Pagination offset
- `status` (string, optional): Filter by status
- `risk_level` (string, optional): Filter by risk level
- `agent_id` (string, optional): Filter by agent ID

**Response (200 OK):**
```json
{
  "total": 1234,
  "limit": 100,
  "offset": 0,
  "actions": [
    {
      "id": 12345,
      "agent_id": "finance-agent-001",
      "action_type": "database.read",
      "status": "approved",
      "risk_score": 35,
      "risk_level": "low",
      "created_at": "2025-12-03T12:00:00Z"
    }
  ]
}
```

---

### GET /api/alerts

Get active alerts for the organization.

**Authentication:** JWT

**Query Parameters:**
- `severity` (string, optional): Filter by severity (critical, high, medium, low)
- `status` (string, optional): Filter by status (new, acknowledged, resolved)
- `limit` (integer, optional): Number of records

**Response (200 OK):**
```json
{
  "total": 5,
  "alerts": [
    {
      "id": 100,
      "alert_type": "High Risk Agent Action",
      "severity": "high",
      "message": "Agent 'finance-agent' requesting high-risk action",
      "status": "new",
      "agent_action_id": 12345,
      "created_at": "2025-12-03T12:00:00Z"
    }
  ]
}
```

---

## Action Types Reference

### Database Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `database.read` | Read/query operations | Low |
| `database.write` | Insert/Update operations | Medium |
| `database.delete` | Delete operations | High |
| `database.schema_change` | DDL operations | Critical |
| `database.bulk_update` | Bulk modifications | High |
| `database.export` | Data export | High |

### File System Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `file.read` | File read access | Low |
| `file.write` | File write operations | Medium |
| `file.delete` | File deletion | High |
| `file.permission_change` | Permission modifications | High |
| `file.bulk_delete` | Bulk file deletion | Critical |

### Financial Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `financial.read` | Account queries | Medium |
| `financial.transfer` | Money transfers | High |
| `financial.bulk_transfer` | Bulk operations | Critical |
| `financial.modify_limits` | Limit changes | High |

### Security Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `security.authentication` | Auth events | Medium |
| `security.access_control` | Permission changes | High |
| `security.encryption_change` | Encryption modifications | Critical |
| `security.key_rotation` | Key management | High |

### Communication Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `email.send` | Email dispatch | Medium |
| `email.bulk_send` | Bulk email | High |
| `sms.send` | SMS dispatch | Medium |
| `notification.push` | Push notifications | Low |

### API Operations
| Action Type | Description | Base Risk |
|-------------|-------------|-----------|
| `api.external_call` | External API calls | Medium |
| `api.data_sync` | Data synchronization | Medium |
| `api.webhook` | Webhook dispatch | Low |

---

## Rate Limits

| Endpoint | Rate Limit | Burst |
|----------|------------|-------|
| POST /api/authorization/agent-action | 100/min | 150 |
| POST /api/sdk/agent-action | 100/min | 150 |
| GET /api/agent-action/status/* | 300/min | 500 |
| GET /api/alerts | 60/min | 100 |

---

## Webhooks (Enterprise)

Configure webhooks to receive real-time notifications:

### Event Types
- `action.submitted` - New action submitted
- `action.approved` - Action approved
- `action.denied` - Action denied
- `alert.triggered` - Alert generated
- `policy.violated` - Policy violation detected

### Webhook Payload
```json
{
  "id": "evt_abc123",
  "type": "action.submitted",
  "timestamp": "2025-12-03T12:00:00Z",
  "api_version": "2025-12-01",
  "organization_id": 1,
  "data": {
    "action_id": 12345,
    "agent_id": "finance-agent-001",
    "action_type": "database.read",
    "risk_score": 35,
    "risk_level": "low"
  }
}
```

### Signature Verification
```python
import hmac
import hashlib

def verify_webhook(payload, signature, timestamp, secret):
    message = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## SDK Support

Official Ascend SDKs available:
- **Python**: `pip install requests python-dotenv  # No SDK package - use REST API directly`
- **JavaScript/TypeScript**: `npm install @ascend/sdk`
- **Go**: `go get github.com/ascendowkai/sdk-go`

See [SDK Guide](./SDK_GUIDE.md) for usage examples.

---

*Document Version: 2.0.0 | Last Updated: December 2025*
