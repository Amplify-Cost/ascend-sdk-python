---
sidebar_position: 7
title: MCP Governance API
description: Govern Model Context Protocol servers
---

# MCP Governance API

Evaluate, approve, and monitor Model Context Protocol (MCP) server actions with enterprise-grade governance controls.

**Base URL:** `https://pilot.owkai.app/api/mcp-governance`

**Source:** `routes/mcp_governance_routes.py`

**Compliance:** SOC 2 CC6.1/CC7.1, NIST AC-3/AU-6, PCI-DSS 7.1/10.2

## Overview

The MCP Governance API provides complete lifecycle management for MCP server actions, using the same enterprise risk assessment and approval workflows as agent actions.

**Enterprise Features:**
- Real-time risk assessment (0-100 scale)
- Policy-based decision making
- Multi-level approval workflows
- Immutable audit logging
- Fail-closed security (deny by default)

---

## Authentication

All endpoints require authentication. MCP evaluation endpoints accept both API keys and JWT tokens.

---

## Action Evaluation

### POST /evaluate

Evaluate an MCP server action and return governance decision.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/evaluate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "filesystem-server",
    "namespace": "filesystem",
    "verb": "write_file",
    "resource": "/data/reports/quarterly.csv",
    "parameters": {"content": "Q4 Report Data"},
    "session_id": "session-123",
    "client_id": "claude-desktop"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | string | Yes | MCP server identifier |
| `namespace` | string | Yes | MCP namespace (filesystem, database, etc.) |
| `verb` | string | Yes | Action verb (read_file, write_file, etc.) |
| `resource` | string | Yes | Target resource path/identifier |
| `parameters` | object | No | Action parameters |
| `session_id` | string | Yes | MCP session identifier |
| `client_id` | string | Yes | MCP client identifier |
| `request_id` | string | No | Unique request ID (auto-generated) |

**Response:**

```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "decision": "EVALUATE",
  "status": "PENDING_APPROVAL",
  "risk_score": 65,
  "risk_level": "MEDIUM",
  "requires_approval": true,
  "approval_level": 2,
  "reason": "Write operation to sensitive data directory requires approval",
  "estimated_review_time_minutes": 15
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `action_id` | string | Unique action identifier |
| `decision` | string | `ALLOW`, `DENY`, or `EVALUATE` |
| `status` | string | `AUTO_APPROVED`, `PENDING_APPROVAL`, `DENIED`, `FAILED` |
| `risk_score` | integer | Risk score (0-100) |
| `risk_level` | string | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `requires_approval` | boolean | Whether human approval is needed |
| `approval_level` | integer | Required approval level (1-5) |
| `estimated_review_time_minutes` | integer | Estimated time to review |

**Decision Logic:**

| Risk Score | Decision | Status |
|------------|----------|--------|
| 0-30 | ALLOW | AUTO_APPROVED |
| 31-70 | EVALUATE | PENDING_APPROVAL |
| 71-100 | DENY | DENIED (high risk) |
| Error | DENY | FAILED (fail-closed) |

---

### POST /execute

Execute an approved MCP action.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/execute?action_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**

```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "execution_result": "SUCCESS",
  "execution_duration_ms": 150,
  "execution_output": "MCP action executed: write_file on /data/reports/quarterly.csv",
  "error_message": null
}
```

**Requirements:**
- Action must be `APPROVED` or `AUTO_APPROVED`
- Action must belong to user's organization

---

## Server Management

### POST /servers/register

Register a new MCP server for governance.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/servers/register" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "filesystem-server",
    "server_name": "File System MCP Server",
    "server_description": "Provides file system access to AI agents",
    "endpoint_url": "stdio://filesystem-server",
    "capabilities": {
      "read_file": true,
      "write_file": true,
      "list_directory": true
    },
    "trust_level": "restricted"
  }'
```

**Trust Levels:**

| Level | Description | Default Behavior |
|-------|-------------|------------------|
| `trusted` | Low risk, auto-approve most actions | Auto-approve score < 50 |
| `restricted` | Medium risk, require approval | Require approval for all writes |
| `sandbox` | High risk, deny by default | Deny unless explicitly approved |

**Response:**

```json
{
  "server_id": "filesystem-server",
  "status": "registered",
  "trust_level": "restricted",
  "requires_approval": true
}
```

---

### GET /servers

List all registered MCP servers.

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/servers?active_only=true" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "total": 3,
  "servers": [
    {
      "server_id": "filesystem-server",
      "server_name": "File System MCP Server",
      "trust_level": "restricted",
      "is_active": true,
      "total_actions": 1247,
      "failed_actions": 12,
      "last_seen": "2025-01-15T14:30:00Z",
      "capabilities": {
        "read_file": true,
        "write_file": true,
        "list_directory": true
      }
    }
  ]
}
```

---

## Approval Workflows

### GET /actions/pending

Get MCP actions pending approval (for Authorization Center).

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/actions/pending?limit=50&risk_level=HIGH" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response:**

```json
{
  "total": 7,
  "limit": 50,
  "actions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "action_type": "mcp_server_action",
      "created_at": "2025-01-15T14:25:00Z",
      "server_id": "filesystem-server",
      "server_name": "File System MCP Server",
      "namespace": "filesystem",
      "verb": "write_file",
      "resource": "/data/reports/quarterly.csv",
      "user_email": "analyst@company.com",
      "user_role": "analyst",
      "risk_score": 65,
      "risk_level": "MEDIUM",
      "risk_factors": ["write_operation", "sensitive_path"],
      "approval_level": 2,
      "policy_reason": "Write to data directory requires L2 approval",
      "status": "PENDING_APPROVAL",
      "session_id": "session-123",
      "environment": "production",
      "compliance_tags": ["SOC2", "PCI-DSS"]
    }
  ]
}
```

---

### POST /actions/{action_id}/approve

Approve or deny a pending MCP action.

**Request (Approve):**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/actions/550e8400-e29b-41d4-a716-446655440000/approve" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "550e8400-e29b-41d4-a716-446655440000",
    "approval_decision": "APPROVE",
    "approval_reason": "Verified quarterly report generation is authorized",
    "conditions": {"expires_in_hours": 24}
  }'
```

**Request (Deny):**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/actions/550e8400-e29b-41d4-a716-446655440000/approve" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "550e8400-e29b-41d4-a716-446655440000",
    "approval_decision": "DENY",
    "approval_reason": "Unauthorized access to sensitive directory"
  }'
```

**Response:**

```json
{
  "action_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "APPROVED",
  "approved_by": "admin@company.com",
  "approved_at": "2025-01-15T14:35:00Z"
}
```

---

## Policy Management

### POST /policies

Create an MCP governance policy.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/policies" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Block Sensitive File Writes",
    "policy_description": "Prevent writes to configuration and credential files",
    "server_patterns": ["*"],
    "namespace_patterns": ["filesystem"],
    "verb_patterns": ["write_file", "delete_file"],
    "resource_patterns": ["/etc/*", "*.env", "*credentials*"],
    "risk_threshold": 90,
    "action": "DENY",
    "required_approval_level": 5,
    "compliance_framework": "PCI-DSS"
  }'
```

**Response:**

```json
{
  "policy_id": "660e8400-e29b-41d4-a716-446655440000",
  "policy_name": "Block Sensitive File Writes",
  "status": "created",
  "is_active": true
}
```

---

### GET /policies

List MCP governance policies.

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/policies?active_only=true" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "total": 5,
  "policies": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "policy_name": "Block Sensitive File Writes",
      "policy_description": "Prevent writes to configuration and credential files",
      "action": "DENY",
      "risk_threshold": 90,
      "required_approval_level": 5,
      "is_active": true,
      "priority": 100,
      "execution_count": 47,
      "created_by": "admin@company.com",
      "created_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

---

## Analytics Dashboard

### GET /analytics/dashboard

Get MCP governance analytics.

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/analytics/dashboard?time_range_hours=24" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "time_range_hours": 24,
  "generated_at": "2025-01-15T14:30:00Z",
  "summary": {
    "total_actions": 1247,
    "pending_approvals": 7,
    "auto_approved": 1150,
    "denied": 45
  },
  "status_distribution": [
    {"status": "AUTO_APPROVED", "count": 1150},
    {"status": "APPROVED", "count": 45},
    {"status": "PENDING_APPROVAL", "count": 7},
    {"status": "DENIED", "count": 45}
  ],
  "risk_distribution": [
    {"risk_level": "LOW", "count": 980},
    {"risk_level": "MEDIUM", "count": 220},
    {"risk_level": "HIGH", "count": 42},
    {"risk_level": "CRITICAL", "count": 5}
  ],
  "server_activity": [
    {
      "server_id": "filesystem-server",
      "server_name": "File System MCP Server",
      "total_actions": 847,
      "avg_risk_score": 28.5
    },
    {
      "server_id": "database-server",
      "server_name": "Database MCP Server",
      "total_actions": 400,
      "avg_risk_score": 45.2
    }
  ],
  "high_risk_actions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "server_id": "database-server",
      "namespace": "database",
      "verb": "execute_query",
      "risk_score": 85,
      "status": "DENIED",
      "created_at": "2025-01-15T12:00:00Z"
    }
  ]
}
```

---

## Unified Actions View

### GET /actions/all

Get unified view of all AI actions (agents + MCP servers).

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/actions/all?limit=50&action_type_filter=all" \
  -H "X-API-Key: your_api_key"
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default: 50) |
| `status_filter` | string | Filter by status |
| `risk_level_filter` | string | Filter by risk level |
| `action_type_filter` | string | `agent`, `mcp`, or `all` |

**Response:**

```json
{
  "total": 25,
  "limit": 50,
  "filters": {
    "status": null,
    "risk_level": null,
    "action_type": "all"
  },
  "actions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "action_type": "mcp_server_action",
      "created_at": "2025-01-15T14:25:00Z",
      "title": "File System MCP Server: write_file",
      "description": "filesystem - /data/reports/quarterly.csv",
      "server_id": "filesystem-server",
      "risk_score": 65,
      "risk_level": "MEDIUM",
      "status": "PENDING_APPROVAL"
    },
    {
      "id": "1547",
      "action_type": "agent_action",
      "created_at": "2025-01-15T14:20:00Z",
      "title": "Agent customer-service-agent: email_send",
      "description": "Send welcome email to customer",
      "agent_id": "customer-service-agent",
      "risk_score": 35,
      "risk_level": "low",
      "status": "approved"
    }
  ]
}
```

---

## Health Check

### GET /health

Check MCP governance system health.

**Request:**

```bash
curl "https://pilot.owkai.app/api/mcp-governance/health" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "status": "healthy",
  "mcp_governance_system": "operational",
  "timestamp": "2025-01-15T14:30:00Z",
  "database_connected": true,
  "statistics": {
    "total_servers": 3,
    "active_servers": 3,
    "total_actions": 15420,
    "pending_actions": 7,
    "active_policies": 5,
    "recent_actions_24h": 1247
  },
  "features": [
    "mcp_action_evaluation",
    "risk_assessment",
    "approval_workflows",
    "policy_engine",
    "audit_integration",
    "unified_dashboard",
    "real_time_monitoring"
  ],
  "enterprise_ready": true,
  "ai_governance_complete": true
}
```

---

## WebSocket Real-Time Updates

### WS /ws/realtime

WebSocket for real-time MCP governance updates.

**Connection:**

```javascript
const ws = new WebSocket('wss://pilot.owkai.app/api/mcp-governance/ws/realtime');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('MCP update:', data);
};
```

**Update Message (every 5 seconds):**

```json
{
  "type": "mcp_governance_update",
  "timestamp": "2025-01-15T14:30:05Z",
  "pending_actions": 7,
  "high_risk_actions": 2,
  "system_status": "operational"
}
```

---

## Test Endpoint

### POST /test/evaluate

Simple test endpoint for MCP evaluation (development).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/mcp-governance/test/evaluate?server_id=test-server&namespace=filesystem&verb=read_file&resource=/tmp/test.txt" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "test_result": "success",
  "evaluation": {
    "action_id": "770e8400-e29b-41d4-a716-446655440000",
    "decision": "ALLOW",
    "status": "AUTO_APPROVED",
    "risk_score": 15,
    "risk_level": "LOW"
  }
}
```

---

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing authentication |
| 403 | Forbidden - Action not approved |
| 404 | Not Found - Action or server not found |
| 409 | Conflict - Server already registered |
| 500 | Internal Server Error |
| 503 | Service Unavailable - System unhealthy |

---

*Source: [mcp_governance_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/mcp_governance_routes.py)*
