# OW-AI Enterprise Customer Integration Guide

**Version:** 1.0
**Date:** 2025-10-30
**Audience:** Enterprise Customers, DevOps Teams, Security Engineers
**Classification:** PUBLIC - CUSTOMER-FACING

---

## Table of Contents

1. [Overview](#overview)
2. [Integration Patterns](#integration-patterns)
3. [Authentication](#authentication)
4. [Agent Action Submission](#agent-action-submission)
5. [MCP Server Governance](#mcp-server-governance)
6. [Webhooks and Real-Time Events](#webhooks-and-real-time-events)
7. [Code Examples](#code-examples)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

OW-AI provides enterprise-grade governance for AI agents and MCP (Model Context Protocol) servers. This guide explains how to integrate your AI agents with the OW-AI platform.

### What OW-AI Provides

- ✅ **Risk Assessment**: Automatic CVSS v3.1, MITRE ATT&CK, NIST 800-53 mapping
- ✅ **Policy Enforcement**: Cedar-style policy engine with auto-approval
- ✅ **Multi-Level Approvals**: 5 escalation levels based on risk scores
- ✅ **Real-Time Alerts**: Automatic alert creation for high-risk actions
- ✅ **Audit Trails**: Immutable compliance logging (SOX, HIPAA, PCI-DSS, GDPR)
- ✅ **Workflow Orchestration**: Automated response to risk events

---

## Integration Patterns

### Pattern 1: Direct API Integration (Recommended)
Your agent submits actions directly to OW-AI via REST API.

```
┌─────────────┐
│ Your Agent  │
└──────┬──────┘
       │ POST /api/agent-actions
       ▼
┌─────────────┐       ┌──────────────┐
│  OW-AI API  │──────▶│ Risk Engine  │
└─────────────┘       └──────────────┘
       │
       ▼
┌─────────────┐
│  Approval   │
│  Workflow   │
└─────────────┘
```

### Pattern 2: MCP Gateway Integration
Your MCP client routes through OW-AI's governance gateway.

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MCP Client  │──────▶│ OW-AI       │──────▶│ MCP Server  │
│             │       │ Gateway     │       │ (Protected) │
└─────────────┘       └─────────────┘       └─────────────┘
```

### Pattern 3: Webhook Integration
OW-AI sends webhooks to your systems for action events.

```
┌─────────────┐
│  OW-AI      │
└──────┬──────┘
       │ Webhook: action.approved
       ▼
┌─────────────┐
│ Your System │
└─────────────┘
```

---

## Authentication

### Option 1: JWT Bearer Token (Recommended for APIs)

**Step 1: Get Access Token**

```bash
POST https://pilot.owkai.app/auth/token
Content-Type: application/x-www-form-urlencoded

username=your-email@company.com&password=your-password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Step 2: Use Token in Requests**

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Option 2: API Key (Coming Soon)

```bash
X-API-Key: owai_sk_live_abc123xyz...
```

### Option 3: Session Cookies (Web UI Only)

Automatic when using the web interface.

---

## Agent Action Submission

### Endpoint

```
POST https://pilot.owkai.app/api/agent-actions
Content-Type: application/json
Authorization: Bearer {token}
```

### Request Body

```json
{
  "agent_id": "your-agent-unique-id",
  "action_type": "database_write",
  "description": "Update user preferences in production database",
  "tool_name": "psql",
  "risk_level": "high",
  "context": {
    "database": "production",
    "table": "user_preferences",
    "operation": "UPDATE"
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Unique identifier for your agent |
| `action_type` | string | Type of action (see [Action Types](#action-types)) |
| `description` | string | Human-readable description of the action |

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `tool_name` | string | Tool or service being used | `""` |
| `risk_level` | string | Manual risk classification (`low`, `medium`, `high`, `critical`) | `medium` |
| `context` | object | Additional context for risk assessment | `{}` |

**Note**: Even if you provide `risk_level`, OW-AI will recalculate it using CVSS assessment.

### Response

**Success (201 Created):**
```json
{
  "status": "success",
  "message": "✅ Enterprise agent action submitted successfully",
  "action_id": 123,
  "action_details": {
    "agent_id": "your-agent-unique-id",
    "action_type": "database_write",
    "risk_level": "high",
    "submitted_by": "admin@company.com",
    "timestamp": "2025-10-30T15:30:00Z"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "detail": "Missing required field: agent_id"
}
```

---

## Action Types

OW-AI recognizes the following action types for risk assessment:

### Database Operations
- `database_read` - Read from database
- `database_write` - Write to database
- `database_delete` - Delete from database
- `database_admin` - Administrative database operations

### File Operations
- `file_read` - Read files
- `file_write` - Write files
- `file_delete` - Delete files
- `file_execute` - Execute files

### Network Operations
- `api_call` - External API calls
- `network_request` - Network requests
- `data_exfiltration` - Data export/transfer

### Security Operations
- `credential_access` - Access credentials
- `privilege_escalation` - Escalate privileges
- `lateral_movement` - Move between systems

### Custom Actions
- `custom_action` - Custom/uncategorized action

---

## MCP Server Governance

### Endpoint

```
POST https://pilot.owkai.app/mcp/evaluate
Content-Type: application/json
Authorization: Bearer {token}
```

### Request Body

```json
{
  "server_id": "mcp-server-postgres",
  "namespace": "database",
  "verb": "write",
  "resource": "production.users",
  "parameters": {
    "query": "UPDATE users SET role = 'admin' WHERE id = 5",
    "database": "production"
  },
  "user_context": {
    "user_id": "user-123",
    "email": "developer@company.com",
    "role": "developer"
  },
  "session_context": {
    "session_id": "sess-abc123",
    "ip_address": "10.0.1.50"
  }
}
```

### Response

```json
{
  "decision": "REQUIRE_APPROVAL",
  "risk_score": 75,
  "policy_result": "REQUIRE_APPROVAL",
  "required_approvals": 3,
  "estimated_approval_time": 15,
  "reasons": [
    "High-risk database write operation",
    "Production environment access",
    "Administrative role modification"
  ],
  "mcp_action_id": 456
}
```

### Decision Types

| Decision | Description | Next Steps |
|----------|-------------|------------|
| `ALLOW` | Action approved automatically | Execute immediately |
| `DENY` | Action blocked by policy | Do not execute |
| `REQUIRE_APPROVAL` | Manual approval required | Wait for approval webhook |

---

## Webhooks and Real-Time Events

### Configure Webhook Endpoint

```bash
PUT https://pilot.owkai.app/api/webhooks
Content-Type: application/json
Authorization: Bearer {token}

{
  "url": "https://your-system.com/owai-webhook",
  "events": ["action.approved", "action.rejected", "alert.created"],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### action.approved
```json
{
  "event": "action.approved",
  "action_id": 123,
  "action_type": "database_write",
  "risk_score": 65,
  "approved_by": "security-team@company.com",
  "timestamp": "2025-10-30T15:35:00Z"
}
```

#### action.rejected
```json
{
  "event": "action.rejected",
  "action_id": 124,
  "action_type": "privilege_escalation",
  "risk_score": 95,
  "rejected_by": "ciso@company.com",
  "reason": "Violates security policy SP-001",
  "timestamp": "2025-10-30T15:36:00Z"
}
```

#### alert.created
```json
{
  "event": "alert.created",
  "alert_id": 789,
  "action_id": 125,
  "severity": "critical",
  "message": "High-risk action: data_exfiltration (ID: 125)",
  "timestamp": "2025-10-30T15:37:00Z"
}
```

### Verifying Webhook Signatures

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

---

## Code Examples

### Python SDK (Recommended)

```python
import requests
import os

class OWAIClient:
    def __init__(self, api_key=None, email=None, password=None):
        self.base_url = "https://pilot.owkai.app"
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
        elif email and password:
            self._authenticate(email, password)

    def _authenticate(self, email, password):
        """Get JWT token"""
        response = self.session.post(
            f"{self.base_url}/auth/token",
            data={"username": email, "password": password}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def submit_action(self, agent_id, action_type, description, **kwargs):
        """Submit agent action for governance"""
        payload = {
            "agent_id": agent_id,
            "action_type": action_type,
            "description": description,
            **kwargs
        }

        response = self.session.post(
            f"{self.base_url}/api/agent-actions",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def wait_for_approval(self, action_id, timeout=300):
        """Poll for action approval"""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.base_url}/api/agent-actions/{action_id}"
            )
            response.raise_for_status()
            action = response.json()

            if action["status"] == "approved":
                return True
            elif action["status"] == "rejected":
                return False

            time.sleep(5)  # Poll every 5 seconds

        raise TimeoutError(f"Action {action_id} approval timeout")

# Usage
client = OWAIClient(
    email="your-agent@company.com",
    password=os.getenv("OWAI_PASSWORD")
)

# Submit high-risk action
result = client.submit_action(
    agent_id="prod-agent-001",
    action_type="database_write",
    description="Update production user table",
    tool_name="psql",
    context={
        "database": "production",
        "table": "users",
        "operation": "UPDATE"
    }
)

print(f"Action submitted: {result['action_id']}")

# Wait for approval
if client.wait_for_approval(result['action_id']):
    print("✅ Action approved - executing...")
    # Execute your action here
else:
    print("❌ Action rejected - aborting...")
```

### JavaScript/TypeScript SDK

```typescript
import axios, { AxiosInstance } from 'axios';

interface ActionSubmission {
  agent_id: string;
  action_type: string;
  description: string;
  tool_name?: string;
  risk_level?: 'low' | 'medium' | 'high' | 'critical';
  context?: Record<string, any>;
}

class OWAIClient {
  private client: AxiosInstance;

  constructor(apiKey?: string, email?: string, password?: string) {
    this.client = axios.create({
      baseURL: 'https://pilot.owkai.app',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (apiKey) {
      this.client.defaults.headers.common['X-API-Key'] = apiKey;
    } else if (email && password) {
      this.authenticate(email, password);
    }
  }

  async authenticate(email: string, password: string): Promise<void> {
    const response = await this.client.post('/auth/token',
      new URLSearchParams({ username: email, password })
    );

    const token = response.data.access_token;
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  async submitAction(action: ActionSubmission): Promise<any> {
    const response = await this.client.post('/api/agent-actions', action);
    return response.data;
  }

  async waitForApproval(actionId: number, timeout: number = 300000): Promise<boolean> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      const response = await this.client.get(`/api/agent-actions/${actionId}`);
      const action = response.data;

      if (action.status === 'approved') {
        return true;
      } else if (action.status === 'rejected') {
        return false;
      }

      await new Promise(resolve => setTimeout(resolve, 5000));
    }

    throw new Error(`Action ${actionId} approval timeout`);
  }
}

// Usage
const client = new OWAIClient(
  undefined,
  'your-agent@company.com',
  process.env.OWAI_PASSWORD
);

const result = await client.submitAction({
  agent_id: 'prod-agent-001',
  action_type: 'database_write',
  description: 'Update production user table',
  tool_name: 'psql',
  context: {
    database: 'production',
    table: 'users',
    operation: 'UPDATE'
  }
});

console.log(`Action submitted: ${result.action_id}`);

if (await client.waitForApproval(result.action_id)) {
  console.log('✅ Action approved - executing...');
  // Execute your action
} else {
  console.log('❌ Action rejected - aborting...');
}
```

### cURL Examples

**Submit Action:**
```bash
#!/bin/bash

# Get token
TOKEN=$(curl -s -X POST "https://pilot.owkai.app/auth/token" \
  -d "username=admin@owkai.com&password=Admin123" \
  | jq -r '.access_token')

# Submit action
curl -X POST "https://pilot.owkai.app/api/agent-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-001",
    "action_type": "database_write",
    "description": "Test action submission",
    "tool_name": "psql"
  }'
```

---

## Security Best Practices

### 1. Credential Management

✅ **DO:**
- Store API keys in environment variables or secret managers
- Rotate credentials regularly (every 90 days)
- Use service accounts for automation

❌ **DON'T:**
- Hardcode credentials in source code
- Share credentials between environments
- Use personal accounts for automation

### 2. Network Security

✅ **DO:**
- Use HTTPS for all API calls
- Implement IP allowlisting where possible
- Use VPN or private networks for production

❌ **DON'T:**
- Send sensitive data in URL parameters
- Use HTTP (unencrypted) connections
- Expose internal network topology

### 3. Data Privacy

✅ **DO:**
- Minimize PII in action descriptions
- Use tokenization for sensitive data
- Implement data retention policies

❌ **DON'T:**
- Include passwords or API keys in action parameters
- Log sensitive customer data
- Store unnecessary personal information

### 4. Error Handling

✅ **DO:**
- Implement retry logic with exponential backoff
- Handle rate limiting (HTTP 429)
- Log errors for debugging

❌ **DON'T:**
- Expose detailed error messages to end users
- Retry indefinitely
- Ignore authentication errors

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failed (401)

**Symptoms:**
```json
{"detail": "Authentication required"}
```

**Solutions:**
- Verify token is not expired
- Check Authorization header format: `Bearer {token}`
- Ensure credentials are correct

#### 2. Missing Required Field (400)

**Symptoms:**
```json
{"detail": "Missing required field: agent_id"}
```

**Solutions:**
- Include all required fields: `agent_id`, `action_type`, `description`
- Check field names are spelled correctly
- Verify JSON syntax

#### 3. Action Stuck in Pending (No Response)

**Symptoms:**
- Action status remains `pending_approval` indefinitely

**Solutions:**
- Check if approvers are configured for your organization
- Verify workflow routing rules
- Contact support if no approvers available

#### 4. Webhook Not Received

**Symptoms:**
- No webhook events received

**Solutions:**
- Verify webhook URL is accessible from internet
- Check firewall rules allow OW-AI IPs
- Implement webhook signature verification
- Check webhook configuration in OW-AI dashboard

### Support

- **Documentation**: https://docs.owkai.app
- **Status Page**: https://status.owkai.app
- **Support Email**: support@owkai.app
- **Enterprise Support**: enterprise@owkai.app (24/7)

---

**End of Customer Integration Guide**
