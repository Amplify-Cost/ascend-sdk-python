---
sidebar_position: 3
title: Actions API
description: Submit and manage agent actions
---

# Actions API

Submit agent actions for governance evaluation through the complete 7-step pipeline including risk assessment, CVSS scoring, policy evaluation, and approval workflows.

**Base URL:** `https://pilot.owkai.app/api/v1/actions`

**Source:** `routes/actions_v1_routes.py`

**Compliance:** SOC 2 Type II, HIPAA, PCI-DSS, GDPR, SOX

## Authentication

All endpoints support dual authentication:
- **API Key:** `X-API-Key: owkai_admin_...` (SDK integration)
- **JWT Token:** `Authorization: Bearer <token>` (Admin UI)

## Endpoints

### POST /submit

Submit an agent action for governance evaluation through the complete pipeline.

**Governance Pipeline:**
1. Risk Assessment (NIST/MITRE enrichment)
2. CVSS Calculation (quantitative scoring)
3. Policy Evaluation (governance policies)
4. Smart Rules Check (custom rules)
5. Alert Generation (high-risk actions)
6. Workflow Routing (approval workflows)
7. Audit Logging (immutable trail)

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/submit" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-service-agent",
    "action_type": "email_send",
    "description": "Send welcome email to new customer",
    "tool_name": "email_service"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | Yes | Unique agent identifier |
| `action_type` | string | Yes | Type of action being performed |
| `description` | string | Yes | Human-readable action description |
| `tool_name` | string | Yes | Tool/service being used |
| `target_system` | string | No | Target system affected |
| `nist_control` | string | No | Override NIST control mapping |
| `mitre_tactic` | string | No | Override MITRE tactic mapping |

**Response:**

```json
{
  "id": 1547,
  "action_id": 1547,
  "status": "approved",
  "risk_score": 35.0,
  "risk_level": "low",
  "cvss_score": 3.5,
  "cvss_severity": "low",
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N",
  "requires_approval": false,
  "alert_triggered": false,
  "alert_id": null,
  "workflow_id": null,
  "policy_decision": "allow",
  "matched_policies": 0,
  "matched_smart_rules": 0,
  "correlation_id": "action_20250115_103045_a1b2c3d4",
  "processing_time_ms": 145,
  "action_type": "email_send",
  "nist_control": "AC-3",
  "nist_description": "Access Enforcement",
  "mitre_tactic": "TA0002",
  "mitre_technique": "T1566",
  "thresholds": {
    "auto_approve_below": 30,
    "max_risk_threshold": 80,
    "agent_type": "supervised",
    "is_registered": true
  },
  "message": "Action processed through complete governance pipeline - Status: approved"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Action ID |
| `status` | string | `approved`, `pending_approval`, or `denied` |
| `risk_score` | float | Risk score (0-100) |
| `risk_level` | string | `low`, `medium`, `high`, `critical` |
| `cvss_score` | float | CVSS base score (0-10) |
| `cvss_severity` | string | CVSS severity rating |
| `requires_approval` | boolean | Whether human approval is needed |
| `alert_triggered` | boolean | Whether an alert was created |
| `correlation_id` | string | Request tracing ID |
| `processing_time_ms` | integer | Pipeline processing time |

**Status Determination Logic (SEC-106):**

| Condition | Result |
|-----------|--------|
| Policy denies | `denied` |
| Risk &lt; auto_approve_below | `approved` (auto) |
| Risk &gt;= max_risk_threshold | `pending_approval` |
| Policy or smart rules require approval | `pending_approval` |
| Otherwise | `approved` |

---

### GET /

List agent actions for the organization.

**Request:**

```bash
curl "https://pilot.owkai.app/api/v1/actions?limit=20&offset=0&status_filter=pending_approval" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Max items (max: 1000) |
| `offset` | integer | 0 | Skip count |
| `status_filter` | string | null | Filter by status |

**Response:**

```json
[
  {
    "id": 1547,
    "agent_id": "customer-service-agent",
    "action_type": "email_send",
    "description": "Send welcome email",
    "status": "approved",
    "risk_score": 35.0,
    "risk_level": "low",
    "cvss_score": 3.5,
    "cvss_severity": "low",
    "timestamp": "2025-01-15T10:30:45Z",
    "tool_name": "email_service",
    "target_system": "smtp.company.com"
  }
]
```

---

### GET /{action_id}

Get detailed information for a specific action.

**Request:**

```bash
curl "https://pilot.owkai.app/api/v1/actions/1547" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "id": 1547,
  "agent_id": "customer-service-agent",
  "action_type": "email_send",
  "description": "Send welcome email",
  "tool_name": "email_service",
  "status": "approved",
  "risk_score": 35.0,
  "risk_level": "low",
  "cvss_score": 3.5,
  "cvss_severity": "low",
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N",
  "nist_control": "AC-3",
  "nist_description": "Access Enforcement",
  "mitre_tactic": "TA0002",
  "mitre_technique": "T1566",
  "recommendation": "Ensure proper authorization before sending",
  "target_system": "smtp.company.com",
  "timestamp": "2025-01-15T10:30:45Z",
  "user_id": 15,
  "organization_id": 4,
  "alert": null
}
```

---

### GET /{action_id}/status

Poll for action decision status (optimized for SDK polling).

**Request:**

```bash
curl "https://pilot.owkai.app/api/v1/actions/1547/status" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "action_id": 1547,
  "status": "approved",
  "risk_score": 35.0,
  "timestamp": "2025-01-15T10:30:45Z",
  "decision_ready": true
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `action_id` | integer | Action ID |
| `status` | string | Current status |
| `risk_score` | float | Risk score |
| `decision_ready` | boolean | true if approved or denied |

**SDK Polling Pattern:**

```python
import time

def wait_for_decision(action_id, max_wait=300):
    start = time.time()
    while time.time() - start < max_wait:
        response = api.get_action_status(action_id)
        if response["decision_ready"]:
            return response["status"]
        time.sleep(5)  # Poll every 5 seconds
    return "timeout"
```

---

### POST /{action_id}/approve

Approve a pending action (admin only, JWT required).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/1547/approve" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "X-CSRF-Token: your_csrf_token"
```

**Response:**

```json
{
  "action_id": 1547,
  "status": "approved",
  "approved_by": 15,
  "approved_at": "2025-01-15T11:00:00Z",
  "correlation_id": "action_20250115_110000_e5f6g7h8"
}
```

**Requirements:**
- JWT authentication (no API keys)
- Action must be in `pending_approval` status
- User must have approval permissions

---

### POST /{action_id}/reject

Reject a pending action (admin only, JWT required).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/1547/reject" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "X-CSRF-Token: your_csrf_token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Exceeds authorized scope"}'
```

**Request Body (optional):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Rejection reason |

**Response:**

```json
{
  "action_id": 1547,
  "status": "denied",
  "rejected_by": 15,
  "rejected_at": "2025-01-15T11:05:00Z",
  "reason": "Exceeds authorized scope",
  "correlation_id": "action_20250115_110500_i9j0k1l2"
}
```

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid status transition |
| 401 | Unauthorized - Missing/invalid authentication |
| 404 | Not Found - Action does not exist |
| 422 | Validation Error - Missing required fields |
| 500 | Internal Server Error |

**Example Error:**

```json
{
  "detail": "Missing required fields: agent_id, action_type"
}
```

## Risk Thresholds

Actions are evaluated against configurable thresholds:

| Threshold | Default | Description |
|-----------|---------|-------------|
| `auto_approve_below` | 30 | Auto-approve below this score |
| `max_risk_threshold` | 80 | Require approval above this score |
| `requires_mfa_above` | 70 | Require MFA above this score |

Autonomous agents have stricter defaults:

| Setting | Supervised | Autonomous |
|---------|------------|------------|
| Auto-approve | &lt;30 | &lt;20 |
| Max risk | 80 | 60 |

## CVSS Scoring

Actions receive CVSS 3.1 base scores:

| Severity | Score Range |
|----------|-------------|
| None | 0.0 |
| Low | 0.1 - 3.9 |
| Medium | 4.0 - 6.9 |
| High | 7.0 - 8.9 |
| Critical | 9.0 - 10.0 |

## NIST/MITRE Enrichment

Actions are automatically mapped to:

| Framework | Example |
|-----------|---------|
| NIST Controls | AC-3 (Access Enforcement) |
| MITRE Tactics | TA0002 (Execution) |
| MITRE Techniques | T1566 (Phishing) |

---

*Source: [actions_v1_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/actions_v1_routes.py)*
