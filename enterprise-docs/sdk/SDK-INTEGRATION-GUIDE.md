# ASCEND SDK Integration Guide

**Document Version:** 1.1
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-12-11
**Author:** ASCEND Engineering Team

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Actions API v1 Reference](#actions-api-v1-reference)
4. [Risk Scoring & Thresholds](#risk-scoring--thresholds)
5. [AI Rule Manager Integration](#ai-rule-manager-integration)
6. [Boto3 Governance Wrapper](#boto3-governance-wrapper)
7. [Real-Time Kill-Switch (SEC-103)](#real-time-kill-switch-sec-103)
8. [Agent Control Notifications (SEC-106/107)](#agent-control-notifications-sec-106107)
9. [Agent Suspension API (SEC-115)](#agent-suspension-api-sec-115)
10. [Error Handling](#error-handling)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The ASCEND SDK provides AI governance capabilities for enterprise applications. This guide covers the Actions API v1 endpoints used by SDK integrations to submit actions for governance review.

### Key Features

| Feature | Description |
|---------|-------------|
| Action Submission | Submit actions for governance evaluation |
| Risk Scoring | Automatic risk classification (0-100) |
| Alert Generation | Alerts triggered for high-risk actions (risk >= 70) |
| ML Suggestions | AI-powered rule recommendations (3+ similar alerts) |
| Multi-tenant | Organization-scoped data isolation |

---

## Authentication

### API Key Authentication

SDK integrations use API key authentication via the `X-API-Key` header.

```bash
# Required header for all SDK requests
X-API-Key: owkai_xxx_your_api_key_here
```

### Environment Variable Configuration

```bash
# Set API key as environment variable (recommended)
export ASCEND_API_KEY="owkai_xxx_your_api_key_here"

# Optional: Override base URL (default: https://pilot.owkai.app)
export ASCEND_BASE_URL="https://pilot.owkai.app"
```

### API Key Format

| Prefix | Role | Use Case |
|--------|------|----------|
| `owkai_admin_*` | Organization Admin | Full governance access |
| `owkai_user_*` | Standard User | Limited to own organization |
| `owkai_super_admin_*` | Platform Admin | Cross-organization access |

---

## Actions API v1 Reference

### Base URL

```
https://pilot.owkai.app/api/v1/actions
```

### Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/actions/submit` | Submit action for governance | X-API-Key |
| GET | `/api/v1/actions` | List actions | X-API-Key |
| GET | `/api/v1/actions/{id}` | Get action details | X-API-Key |
| GET | `/api/v1/actions/{id}/status` | Poll status (SDK optimized) | X-API-Key |
| POST | `/api/v1/actions/{id}/approve` | Approve action | X-API-Key |
| POST | `/api/v1/actions/{id}/reject` | Reject action | X-API-Key |

---

### POST /api/v1/actions/submit

**Description:** Submit an action for governance evaluation through the complete pipeline.

**Request Headers:**
```bash
X-API-Key: owkai_xxx_your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "action_type": "string (required)",
  "tool_name": "string (required)",
  "description": "string (required)",
  "parameters": {},
  "agent_id": "string (optional)",
  "risk_score": 0
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action_type` | string | Yes | Action identifier (e.g., `iam:DeleteUser`, `s3:DeleteBucket`) |
| `tool_name` | string | Yes | Tool/service name (e.g., `aws_iam`, `aws_s3`) |
| `description` | string | Yes | Human-readable description of the action |
| `parameters` | object | No | Action-specific parameters |
| `agent_id` | string | No | Identifier for the AI agent |
| `risk_score` | integer | No | Pre-computed risk score (0-100), or computed by server |

**Response 200 (Success):**
```json
{
  "id": 923,
  "action_id": 923,
  "status": "pending_approval",
  "risk_score": 71.0,
  "risk_level": "high",
  "alert_triggered": true,
  "alert_id": 717,
  "requires_approval": true,
  "message": "Action processed through complete governance pipeline"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique action identifier |
| `action_id` | integer | Same as `id` (for compatibility) |
| `status` | string | `pending_approval`, `approved`, `denied` |
| `risk_score` | float | Computed risk score (0-100) |
| `risk_level` | string | `low`, `medium`, `high`, `critical` |
| `alert_triggered` | boolean | Whether an alert was generated |
| `alert_id` | integer | Alert ID if triggered (null otherwise) |
| `requires_approval` | boolean | Whether manual approval is required |
| `message` | string | Human-readable status message |

**Example Request:**
```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/submit" \
  -H "X-API-Key: owkai_admin_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "s3.delete_bucket",
    "tool_name": "aws_s3",
    "description": "Delete production backup bucket",
    "parameters": {
      "Bucket": "production-backups-2024"
    },
    "agent_id": "boto3-agent-abc123"
  }'
```

---

### GET /api/v1/actions

**Description:** List actions for the authenticated organization.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter by status: `pending_approval`, `approved`, `denied` |
| `limit` | integer | 50 | Maximum results (1-100) |
| `offset` | integer | 0 | Pagination offset |

**Example:**
```bash
curl -X GET "https://pilot.owkai.app/api/v1/actions?status=pending_approval&limit=10" \
  -H "X-API-Key: owkai_admin_your_key_here"
```

**Response:**
```json
{
  "actions": [
    {
      "id": 923,
      "action_type": "s3.delete_bucket",
      "status": "pending_approval",
      "risk_score": 85.0,
      "created_at": "2025-12-10T15:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### GET /api/v1/actions/{id}/status

**Description:** Poll action status (optimized for SDK polling).

**Example:**
```bash
curl -X GET "https://pilot.owkai.app/api/v1/actions/923/status" \
  -H "X-API-Key: owkai_admin_your_key_here"
```

**Response:**
```json
{
  "id": 923,
  "status": "approved",
  "risk_score": 71.0,
  "approved_by": "admin@company.com",
  "approved_at": "2025-12-10T15:35:00Z"
}
```

---

## Risk Scoring & Thresholds

### Risk Level Mapping

| Risk Score | Risk Level | Alert Generated | Auto-Approve Eligible |
|------------|------------|-----------------|----------------------|
| 0-29 | Low | No | Yes (configurable) |
| 30-69 | Medium | No | Configurable |
| 70-84 | High | **Yes** | No |
| 85-100 | Critical | **Yes** | No |

### Alert Threshold

Actions with `risk_score >= 70` automatically trigger alerts in the Alert Management system.

**SEC-110 Implementation:**
```python
# routes/actions_v1_routes.py:492
if action.risk_score >= 70:  # SEC-110: Align with HIGH risk tier
    alert = Alert(
        alert_type="High Risk Agent Action",
        severity="critical" if action.risk_score >= 85 else "high",
        ...
    )
```

---

## AI Rule Manager Integration

### ML Suggestion Requirements

The AI Rule Manager generates rule suggestions when:

1. **Alert Threshold:** 3+ alerts of the same type within 30 days
2. **No Existing Rule:** Alert type doesn't have a matching smart rule
3. **Organization Scope:** Suggestions are tenant-isolated

**SEC-114 Implementation:**
```sql
-- routes/smart_rules_routes.py:1295
HAVING COUNT(*) >= 3  -- SEC-114: Lowered for pilot phase
```

### Suggestions Endpoint

```bash
GET /api/smart-rules/suggestions
Authorization: Bearer <JWT_TOKEN>
```

**Note:** This endpoint requires JWT authentication (dashboard user), not API key.

---

## Boto3 Governance Wrapper

### Installation

```bash
pip install ascend-boto3
```

### Quick Start

```python
from ascend_boto3 import enable_governance
import boto3

# Enable governance (patches boto3 globally)
enable_governance(
    api_key="owkai_admin_your_key_here",  # Or use ASCEND_API_KEY env var
    base_url="https://pilot.owkai.app"
)

# Use boto3 as normal - governance is automatic
s3 = boto3.client('s3')
s3.list_buckets()        # Low risk - auto-approved
s3.delete_bucket(...)    # High risk - requires governance approval
```

### Configuration Options

```python
enable_governance(
    api_key="...",
    base_url="https://pilot.owkai.app",
    agent_id="my-agent-001",
    agent_name="Production Data Agent",
    auto_approve_low_risk=True,      # Auto-approve risk < 45
    auto_approve_medium_risk=False,  # Require review for 45-69
    bypass_services={"cloudwatch"},  # Skip governance for these
    dry_run=False                    # Log only, don't enforce
)
```

### Risk Classification

The wrapper classifies AWS operations by risk:

| Operation Pattern | Risk Level | Score Range |
|-------------------|------------|-------------|
| `list_*`, `get_*`, `describe_*` | Low | 0-44 |
| `put_*`, `create_*` | Medium | 45-69 |
| `delete_*`, `terminate_*` | High | 70-84 |
| `delete_bucket`, `delete_stack` | Critical | 85-100 |

---

## Real-Time Kill-Switch (SEC-103)

The ASCEND SDK includes real-time kill-switch capability via SNS/SQS messaging. This allows administrators to immediately block agent operations when security incidents occur.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────────┐
│ Admin Dashboard │───▶│ SNS Topic               │───▶│ SQS Queue           │
│ Emergency Stop  │    │ ascend-agent-control    │    │ org-{id} specific   │
└─────────────────┘    └─────────────────────────┘    └─────────────────────┘
                                                              │
                                                              ▼
                                                      ┌─────────────────────┐
                                                      │ SDK Agent           │
                                                      │ AgentControlClient  │
                                                      │ Polls every 5s      │
                                                      └─────────────────────┘
```

**Latency:** < 1 second from command issue to agent stop

### AgentControlClient Usage

```python
from ascend_boto3.control import AgentControlClient, create_control_client

# Create control client for your organization
control = create_control_client(
    organization_id=34,           # Your org ID
    agent_id="my-boto3-agent",    # Unique agent identifier
    region="us-east-2"
)

# Start background polling (non-blocking)
control.start_polling()

# Check if agent is blocked before operations
if control.is_blocked:
    print(f"Agent blocked: {control.block_reason}")
    # Handle graceful shutdown
else:
    # Proceed with normal operations
    pass

# Alternative: Raise exception if blocked
control.assert_not_blocked()  # Raises RuntimeError if blocked

# Stop polling on shutdown
control.stop_polling()
```

### Command Types

| Command | Description | Effect |
|---------|-------------|--------|
| `BLOCK` | Immediately stop agent | Sets `is_blocked=True` |
| `UNBLOCK` | Resume agent operations | Sets `is_blocked=False` |
| `SUSPEND` | Temporary pause | Treated as BLOCK |
| `QUARANTINE` | Security isolation | Treated as BLOCK |
| `RESUME` | Resume from suspend | Treated as UNBLOCK |

### Callbacks for Custom Handling

```python
def on_blocked(command):
    """Called when BLOCK command received."""
    print(f"Agent blocked! Reason: {command.get('reason')}")
    # Gracefully stop current operations
    # Save state if needed

def on_unblocked(command):
    """Called when UNBLOCK command received."""
    print(f"Agent unblocked! Resuming operations...")

control = create_control_client(
    organization_id=34,
    agent_id="my-agent",
    on_block=on_blocked,
    on_unblock=on_unblocked
)
```

### Integration with Governance Wrapper

```python
from ascend_boto3 import enable_governance
from ascend_boto3.control import create_control_client

# Enable governance
enable_governance(api_key="owkai_admin_xxx")

# Enable kill-switch polling
control = create_control_client(organization_id=34, agent_id="my-agent")
control.start_polling()

# Before each operation, check block status
def safe_operation(func, *args, **kwargs):
    control.assert_not_blocked()  # Raises if blocked
    return func(*args, **kwargs)

# Use in your agent
s3 = boto3.client('s3')
safe_operation(s3.delete_bucket, Bucket='my-bucket')
```

### Compliance

| Standard | Control | Implementation |
|----------|---------|----------------|
| SOC 2 CC6.2 | Access Revocation | Real-time BLOCK via SNS |
| NIST IR-4 | Incident Handling | Emergency suspension capability |
| HIPAA 164.308(a)(6) | Security Procedures | Immediate response to incidents |

---

## Agent Control Notifications (SEC-106/107)

When kill-switch commands are issued, notifications are automatically sent to configured channels.

### Agent Control Event Types

| Event Type | Priority | Description |
|------------|----------|-------------|
| `agent.blocked` | URGENT | Agent blocked via kill-switch |
| `agent.unblocked` | HIGH | Agent unblocked and resumed |
| `agent.suspended` | URGENT | Agent suspended (temporary) |
| `agent.quarantined` | URGENT | Agent isolated for security |

### Notification Channels

| Channel | Configuration | Delivery |
|---------|--------------|----------|
| Slack | Webhook URL in dashboard | Real-time |
| Microsoft Teams | Webhook URL in dashboard | Real-time |
| Webhook | Custom HTTP endpoint | Real-time |
| Email | User email settings | Near real-time |

### Notification Message Format

**Slack/Teams Example:**
```
🛑 AGENT BLOCKED: boto3-agent-001

Agent 'Production Data Agent' has been blocked via emergency kill-switch.

**Reason:** Suspicious activity detected
**Blocked by:** admin@company.com
**Command ID:** cmd-abc-123-def

Compliance: SOC 2 CC6.2 | NIST IR-4
```

### Subscribe to Agent Events

Configure notification preferences in the ASCEND Dashboard:

1. Navigate to **Settings** → **Notifications**
2. Select channels (Slack, Teams, Webhook)
3. Enable **Agent Control Events** category
4. Choose priority threshold (Recommended: HIGH and above)

### Webhook Payload

```json
{
  "event_type": "agent.blocked",
  "priority": "urgent",
  "timestamp": "2025-12-11T01:30:00Z",
  "data": {
    "agent_id": "boto3-agent-001",
    "agent_display_name": "Production Data Agent",
    "command_id": "cmd-abc-123-def",
    "reason": "Suspicious activity detected",
    "blocked_by": "admin@company.com",
    "organization_id": 34
  }
}
```

---

## Agent Suspension API (SEC-115)

ASCEND provides two levels of agent suspension with different severity and effects.

### Two-Tier Suspension Architecture

| Endpoint | Type | SNS | Notifications | Use Case |
|----------|------|-----|---------------|----------|
| `/suspend` | Soft Pause | ❌ No | ❌ No | Routine maintenance, temporary pause |
| `/emergency-suspend` | Kill-Switch | ✅ Yes | ✅ Yes | Security incidents, policy violations |

### POST /api/registry/agents/{id}/suspend

**Description:** Soft suspension - updates database status only.

**Request:**
```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/my-agent-001/suspend?reason=Routine+maintenance" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response:**
```json
{
  "success": true,
  "message": "Agent suspended: my-agent-001",
  "agent": {
    "id": 42,
    "agent_id": "my-agent-001",
    "status": "suspended"
  },
  "reason": "Routine maintenance"
}
```

### POST /api/registry/agents/{id}/emergency-suspend

**Description:** Emergency kill-switch - suspends agent AND publishes BLOCK command via SNS.

**Request:**
```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/my-agent-001/emergency-suspend" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Suspicious activity detected - immediate termination required"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Explanation for emergency suspension (min 10 chars) |

**Response:**
```json
{
  "success": true,
  "agent_id": "my-agent-001",
  "status": "suspended",
  "reason": "Suspicious activity detected - immediate termination required",
  "suspended_by": "admin@company.com",
  "suspended_at": "2025-12-11T01:30:00Z",
  "alert": "EMERGENCY SUSPENSION - All stakeholders notified",
  "compliance": "SEC-068 / SEC-103 / SEC-107 / SOC 2 CC6.2 / NIST IR-4",
  "kill_switch": {
    "command_id": "cmd-abc-123-def",
    "sns_message_id": "msg-xyz-789",
    "status": "delivered",
    "note": "BLOCK command sent to agent via SNS/SQS"
  },
  "notifications": {
    "status": "dispatched",
    "event_type": "agent.blocked",
    "note": "SEC-107: Async notification sent to subscribed channels"
  }
}
```

### POST /api/registry/agents/{id}/activate

**Description:** Reactivate a suspended agent.

**Request:**
```bash
curl -X POST "https://pilot.owkai.app/api/registry/agents/my-agent-001/activate" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Issue resolved, resuming operations"}'
```

### When to Use Each

| Scenario | Use | Reason |
|----------|-----|--------|
| Scheduled maintenance | `/suspend` | No urgency, planned downtime |
| Agent behaving unexpectedly | `/emergency-suspend` | Need immediate stop |
| Security incident | `/emergency-suspend` | Must notify stakeholders |
| Policy violation detected | `/emergency-suspend` | Compliance requirement |
| Temporary pause for debugging | `/suspend` | No security concern |

### Compliance

| Standard | Control | Implementation |
|----------|---------|----------------|
| SOC 2 CC6.2 | Logical Access Controls | Emergency suspension with audit |
| NIST IR-4 | Incident Handling | Real-time response capability |
| HIPAA 164.308(a)(6) | Security Incident Procedures | Notification + audit trail |

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "AUTH_FAILED",
  "timestamp": "2025-12-10T15:30:00Z"
}
```

### Common Error Codes

| HTTP Code | Error | Cause | Resolution |
|-----------|-------|-------|------------|
| 401 | Authentication required | Missing or invalid API key | Verify `X-API-Key` header |
| 403 | Permission denied | Key lacks required permissions | Use appropriate key role |
| 404 | Not found | Invalid action ID or endpoint | Check endpoint path |
| 422 | Validation error | Invalid request body | Review request schema |
| 429 | Rate limited | Too many requests | Implement backoff |

---

## Troubleshooting

### API Key Authentication Fails (401)

```bash
# Verify key is set
echo $ASCEND_API_KEY

# Test authentication
curl -X GET "https://pilot.owkai.app/api/v1/actions?limit=1" \
  -H "X-API-Key: $ASCEND_API_KEY"
```

### No ML Suggestions Appearing

Verify you have 3+ alerts of the same type in the last 30 days:
- Check Alert Management dashboard
- Ensure alerts are for the same `alert_type`
- ML suggestions require JWT auth (dashboard), not API key

### Actions Not Appearing in Dashboard

1. Confirm action was submitted successfully (check response `id`)
2. Verify organization ID matches your dashboard login
3. Check filter settings (status, date range)

---

## Compliance

All SDK integrations maintain enterprise compliance:

| Standard | Control | Implementation |
|----------|---------|----------------|
| SOC 2 CC6.1 | Access Control | API key authentication, RBAC |
| HIPAA 164.312(a)(1) | Access Control | Organization-scoped isolation |
| NIST 800-53 AC-3 | Access Enforcement | Multi-tenant RLS policies |

---

**Document maintained by ASCEND Engineering Team**
