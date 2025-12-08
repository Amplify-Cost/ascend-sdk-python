---
sidebar_position: 4
title: Agents API
description: Register and manage AI agents
---

# Agents API

Register, configure, and manage AI agents with enterprise-grade governance controls including rate limits, budget controls, and anomaly detection.

**Base URL:** `https://pilot.owkai.app/api/registry`

**Source:** `routes/agent_registry_routes.py`

**Compliance:** SOC 2 CC6.1/CC6.2/CC7.1, PCI-DSS 7.1/8.3, NIST AC-2/AC-3/SI-4

## Authentication

Most endpoints support dual authentication:
- **API Key:** `X-API-Key: owkai_admin_...` (SDK integration)
- **JWT Token:** `Authorization: Bearer <token>` (Admin UI)

Admin-only endpoints require JWT authentication.

## Agent Registration

### POST /agents

Register a new AI agent with the governance platform.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-service-agent",
    "display_name": "Customer Service Agent",
    "description": "Handles customer inquiries",
    "agent_type": "supervised",
    "default_risk_score": 50,
    "auto_approve_below": 30,
    "max_risk_threshold": 80,
    "allowed_action_types": ["email_send", "ticket_create"],
    "alert_on_high_risk": true
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | Yes | Unique identifier (3-64 chars) |
| `display_name` | string | Yes | Human-readable name |
| `description` | string | No | Agent description |
| `agent_type` | string | No | `autonomous`, `supervised`, `advisory`, `mcp_server` |
| `default_risk_score` | integer | No | Default risk (0-100, default: 50) |
| `auto_approve_below` | integer | No | Auto-approve threshold (default: 30) |
| `max_risk_threshold` | integer | No | Max risk threshold (default: 80) |
| `requires_mfa_above` | integer | No | MFA requirement threshold (default: 70) |
| `allowed_action_types` | array | No | Permitted action types |
| `allowed_resources` | array | No | Permitted resources |
| `blocked_resources` | array | No | Blocked resources |
| `alert_on_high_risk` | boolean | No | Send alerts for high risk (default: true) |
| `alert_recipients` | array | No | Email recipients for alerts |
| `webhook_url` | string | No | Webhook for notifications |
| `tags` | array | No | Categorization tags |
| `metadata` | object | No | Custom metadata |

**Response:**

```json
{
  "success": true,
  "created": true,
  "agent": {
    "id": 42,
    "agent_id": "customer-service-agent",
    "display_name": "Customer Service Agent",
    "status": "draft",
    "version": "1.0.0",
    "agent_type": "supervised",
    "created_at": "2025-01-15T10:00:00Z",
    "organization_id": 4
  },
  "message": "Agent registered: customer-service-agent",
  "next_steps": [
    "Configure policies using POST /api/registry/agents/{id}/policies",
    "Activate agent using POST /api/registry/agents/{id}/activate",
    "Submit actions using POST /api/sdk/agent-action"
  ]
}
```

---

### GET /agents

List all registered agents.

**Request:**

```bash
curl "https://pilot.owkai.app/api/registry/agents?status_filter=active&limit=20" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status_filter` | string | Filter by status: `draft`, `active`, `suspended` |
| `type_filter` | string | Filter by agent type |
| `limit` | integer | Max items (default: 100, max: 500) |
| `offset` | integer | Skip count |

---

### GET /agents/{agent_id}

Get detailed agent information.

**Response includes:**
- Risk configuration
- Capabilities
- MCP integration settings
- Notification settings
- Audit trail

---

### PUT /agents/{agent_id}

Update agent configuration (JWT required).

---

### DELETE /agents/{agent_id}

Delete an agent (admin only, JWT required).

---

## Agent Lifecycle

### POST /agents/{agent_id}/activate

Activate an agent for production use (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/customer-service-agent/activate" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response:**

```json
{
  "success": true,
  "message": "Agent activated: customer-service-agent",
  "agent": {
    "id": 42,
    "agent_id": "customer-service-agent",
    "status": "active",
    "approved_at": "2025-01-15T10:30:00Z",
    "approved_by": "admin@company.com"
  }
}
```

---

### POST /agents/{agent_id}/suspend

Suspend an agent (admin only).

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/customer-service-agent/suspend?reason=Security%20review" \
  -H "Cookie: access_token=your_session_cookie"
```

---

## Version Management

### GET /agents/{agent_id}/versions

List all versions of an agent.

---

### POST /agents/{agent_id}/rollback

Rollback to a previous version (admin only).

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/customer-service-agent/rollback?target_version=1.0.0" \
  -H "Cookie: access_token=your_session_cookie"
```

---

## Policy Management

### POST /agents/{agent_id}/policies

Add a policy to an agent.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/customer-service-agent/policies" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Block PII Access",
    "policy_description": "Prevent access to PII data",
    "is_active": true,
    "priority": 10,
    "conditions": {
      "data_classification": "pii"
    },
    "policy_action": "block"
  }'
```

---

### GET /agents/{agent_id}/policies

List policies for an agent.

---

### POST /agents/{agent_id}/evaluate

Test policy evaluation for a proposed action.

---

## Autonomous Agent Governance (SEC-068)

### PUT /agents/{agent_id}/rate-limits

Configure rate limits.

```bash
curl -X PUT "https://pilot.owkai.app/api/registry/agents/autonomous-agent/rate-limits" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "max_actions_per_minute": 10,
    "max_actions_per_hour": 100,
    "max_actions_per_day": 500
  }'
```

---

### PUT /agents/{agent_id}/budget

Configure budget limits.

```bash
curl -X PUT "https://pilot.owkai.app/api/registry/agents/autonomous-agent/budget" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "max_daily_budget_usd": 1000,
    "budget_alert_threshold_percent": 80,
    "auto_suspend_on_exceeded": true
  }'
```

---

### PUT /agents/{agent_id}/time-window

Configure time-based restrictions.

```bash
curl -X PUT "https://pilot.owkai.app/api/registry/agents/autonomous-agent/time-window" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "start_time": "09:00",
    "end_time": "17:00",
    "timezone": "America/New_York",
    "allowed_days": [1, 2, 3, 4, 5]
  }'
```

---

### PUT /agents/{agent_id}/data-classifications

Configure data access restrictions.

---

### PUT /agents/{agent_id}/auto-suspend

Configure auto-suspension triggers.

---

### PUT /agents/{agent_id}/escalation

Configure escalation paths (CR-003).

---

### GET /agents/{agent_id}/usage

Get usage statistics.

**Response:**

```json
{
  "agent_id": "autonomous-agent",
  "rate_limits": {
    "per_minute": {"limit": 10, "current": 3, "remaining": 7},
    "per_hour": {"limit": 100, "current": 45, "remaining": 55},
    "per_day": {"limit": 500, "current": 200, "remaining": 300}
  },
  "budget": {
    "max_daily_usd": 1000,
    "current_spend_usd": 450.50,
    "remaining_usd": 549.50,
    "alert_sent": false
  },
  "anomaly_detection": {
    "enabled": true,
    "count_24h": 0
  }
}
```

---

### GET /agents/{agent_id}/anomalies

Get anomaly detection status.

---

### POST /agents/{agent_id}/emergency-suspend

Emergency kill switch (admin only).

```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/autonomous-agent/emergency-suspend" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Detected unusual behavior pattern"}'
```

---

### POST /agents/{agent_id}/set-baselines

Set baseline metrics for anomaly detection.

---

## MCP Server Management

### POST /mcp-servers

Register an MCP server.

---

### GET /mcp-servers

List MCP servers.

---

### GET /mcp-servers/{server_name}

Get MCP server details.

---

### PUT /mcp-servers/{server_name}

Update MCP server.

---

### DELETE /mcp-servers/{server_name}

Delete MCP server (admin only).

---

### POST /mcp-servers/{server_name}/activate

Activate MCP server (admin only).

---

### POST /mcp-servers/{server_name}/deactivate

Deactivate MCP server (admin only).

---

## Agent Types

| Type | Description | Default Thresholds |
|------|-------------|-------------------|
| `supervised` | Human oversight required | auto: 30, max: 80 |
| `autonomous` | Operates independently | auto: 20, max: 60 |
| `advisory` | Recommendations only | auto: 50, max: 90 |
| `mcp_server` | MCP protocol server | auto: 30, max: 80 |

---

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Agent does not exist |
| 500 | Internal Server Error |

---

*Source: [agent_registry_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/agent_registry_routes.py)*
