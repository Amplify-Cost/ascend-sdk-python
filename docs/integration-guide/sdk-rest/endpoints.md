---
title: REST API Endpoints
sidebar_position: 1
---

# REST API Endpoints

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-SDK-017 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Complete reference for Ascend REST API endpoints.

## Base URL

```
https://pilot.owkai.app
```

## Actions

### Submit Action

Submit an agent action for governance review.

```http
POST /api/v1/actions/submit
```

**Request Body:**

```json
{
  "agent_id": "customer-service-agent",
  "action_type": "data_access",
  "description": "Retrieve customer profile",
  "resource": "customer_database.profiles",
  "parameters": {
    "customer_id": "cust_12345",
    "fields": ["name", "email"]
  },
  "metadata": {
    "ticket_id": "TICKET-789"
  }
}
```

**Response:**

```json
{
  "action_id": "act_7f8g9h0i",
  "status": "approved",
  "risk_score": 25,
  "risk_level": "low",
  "decision": {
    "outcome": "approved",
    "reason": "Low risk action",
    "decided_by": "auto_approve",
    "decided_at": "2025-01-15T10:30:00Z"
  },
  "policies_evaluated": [
    {
      "policy_id": "pol_data_access",
      "result": "allow"
    }
  ],
  "audit_trail": {
    "audit_id": "aud_xyz789",
    "evaluation_time_ms": 45
  }
}
```

---

### Get Action

Get action details.

```http
GET /api/v1/actions/{action_id}
```

**Response:**

```json
{
  "action_id": "act_7f8g9h0i",
  "agent_id": "customer-service-agent",
  "action_type": "data_access",
  "resource": "customer_database.profiles",
  "status": "approved",
  "risk_score": 25,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Action Status

Get current action status.

```http
GET /api/v1/actions/{action_id}/status
```

**Response:**

```json
{
  "action_id": "act_7f8g9h0i",
  "status": "approved",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### List Actions

List actions with filters.

```http
GET /api/v1/actions?agent_id=my-agent&status=approved&limit=50
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Filter by agent |
| `status` | string | Filter by status |
| `action_type` | string | Filter by type |
| `start_date` | string | Start date (ISO 8601) |
| `end_date` | string | End date (ISO 8601) |
| `limit` | integer | Max results (default 50) |
| `offset` | integer | Pagination offset |

---

### Cancel Action

Cancel a pending action.

```http
POST /api/v1/actions/{action_id}/cancel
```

**Request Body:**

```json
{
  "reason": "User requested cancellation"
}
```

---

## Agents

### Register Agent

```http
POST /api/registry/agents
```

**Request Body:**

```json
{
  "agent_id": "my-agent",
  "name": "My AI Agent",
  "description": "Agent for customer service",
  "capabilities": ["data_access", "query"]
}
```

---

### Get Agent

```http
GET /api/registry/agents/{agent_id}
```

---

### List Agents

```http
GET /api/registry/agents?status=active&limit=50
```

---

### Update Agent

```http
PUT /api/registry/agents/{agent_id}
```

---

### Deactivate Agent

```http
POST /api/registry/agents/{agent_id}/deactivate
```

---

## Policies

### Create Policy

```http
POST /api/governance/policies
```

**Request Body:**

```json
{
  "name": "PII Access Policy",
  "description": "Require approval for PII access",
  "conditions": {
    "resource_tags": ["pii"],
    "action_types": ["read", "update"]
  },
  "action": "require_approval",
  "workflow_id": "wf_abc123",
  "priority": 100
}
```

---

### Get Policy

```http
GET /api/governance/policies/{policy_id}
```

---

### List Policies

```http
GET /api/governance/policies
```

---

### Update Policy

```http
PUT /api/governance/policies/{policy_id}
```

---

### Delete Policy

```http
DELETE /api/governance/policies/{policy_id}
```

---

## Workflows

### Create Workflow

```http
POST /api/governance/workflows
```

**Request Body:**

```json
{
  "name": "Manager Approval",
  "type": "single_approval",
  "approvers": [
    {"role": "manager"}
  ],
  "timeout_seconds": 3600
}
```

---

### Get Workflow

```http
GET /api/governance/workflows/{workflow_id}
```

---

### List Workflows

```http
GET /api/governance/workflows
```

---

## Audit

### List Audit Logs

```http
GET /api/audit/logs?event_types=action.blocked&start_date=2025-01-01&limit=100
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `event_types` | string | Comma-separated event types |
| `start_date` | string | Start date |
| `end_date` | string | End date |
| `actor_type` | string | Filter by actor type |
| `limit` | integer | Max results |
| `offset` | integer | Pagination offset |

---

### Get Audit Log

```http
GET /api/audit/logs/{log_id}
```

---

### Export Audit Logs

```http
POST /api/audit/export
```

**Request Body:**

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "format": "json"
}
```

---

## Risk

### Evaluate Risk

```http
POST /api/risk/evaluate
```

**Request Body:**

```json
{
  "agent_id": "my-agent",
  "action_type": "data_access",
  "resource": "database"
}
```

**Response:**

```json
{
  "score": 45,
  "level": "medium",
  "factors": {
    "action_type": {"weight": 0.25, "contribution": 3.75},
    "resource_sensitivity": {"weight": 0.30, "contribution": 22.5}
  }
}
```

---

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Server Error |

## Next Steps

- [Webhooks](/sdk/rest/webhooks) - Event notifications
- [Authentication](/sdk/rest/authentication) - Auth methods
