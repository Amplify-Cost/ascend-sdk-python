---
title: Ascend Enterprise Integration Guide
sidebar_position: 1
---

# Ascend Enterprise Integration Guide

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-HELP-006 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

**Document ID:** ASCEND-INT-001
**Version:** 2.1.0
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
- **Agent Registry & Governance**: Full lifecycle management for autonomous AI agents (SEC-068)
- **Emergency Controls**: Kill switch, rate limits, budget caps, and time window restrictions

---

## Quick Start

### Step 1: Generate API Key

1. Log into the Ascend dashboard
2. Navigate to **Settings > API Keys**
3. Click **Generate New Key**
4. Copy and securely store your API key (format: `owkai_<role>_<secret>`)

### Step 2: Submit Your First Action

```bash
curl -X POST https://pilot.owkai.app/api/authorization/agent-action \
  -H "Authorization: Bearer owkai_your_api_key" \
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

## Agent Registration (SEC-068)

Before submitting actions, register your AI agent with the platform:

### Register an Agent

```bash
curl -X POST https://pilot.owkai.app/api/registry/agents \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "your-agent-001",
    "name": "Customer Service Bot",
    "description": "Handles customer inquiries and ticket routing",
    "agent_type": "autonomous",
    "version": "1.0.0",
    "capabilities": ["database.read", "email.send", "ticket.create"]
  }'
```

### Agent Types

| Type | Description | Risk Level | Approval Required |
|------|-------------|------------|-------------------|
| `supervised` | Human approval for high-risk actions | Medium | Yes (risk > 60) |
| `autonomous` | Operates independently with stricter controls | High | Configurable |
| `advisory` | Recommendations only, no execution | Low | No |
| `mcp_server` | Model Context Protocol server integration | Variable | Policy-based |

---

## Agent Governance Controls (SEC-068)

Configure comprehensive controls for autonomous AI agents:

### Rate Limits (SOC 2 CC6.2 / NIST SI-4)

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/rate-limits \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "max_actions_per_minute": 10,
    "max_actions_per_hour": 100,
    "max_actions_per_day": 1000,
    "auto_suspend_on_exceeded": true
  }'
```

### Budget Controls (PCI-DSS 7.1 / SOC 2 A1.1)

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/budget \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "max_daily_budget_usd": 100.00,
    "budget_alert_threshold_percent": 80,
    "auto_suspend_on_exceeded": true
  }'
```

### Time Window Restrictions (SOC 2 A1.1)

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/time-window \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "09:00",
    "end_time": "17:00",
    "timezone": "America/New_York",
    "allowed_days": [1, 2, 3, 4, 5]
  }'
```

### Data Classification Controls (HIPAA 164.312 / PCI-DSS 3.4 / GDPR)

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/data-classifications \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_classifications": ["public", "internal"],
    "blocked_classifications": ["pii", "financial", "secret"]
  }'
```

### Auto-Suspension Rules (NIST AC-2(3))

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/auto-suspend \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "on_error_rate": 0.10,
    "on_offline_minutes": 30,
    "on_budget_exceeded": true,
    "on_rate_exceeded": true
  }'
```

### Escalation & Webhooks (CR-003)

```bash
curl -X PUT https://pilot.owkai.app/api/registry/agents/{agent_id}/escalation \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "allow_queued_approval": true,
    "escalation_webhook_url": "https://your-app.com/webhooks/agent-escalation",
    "escalation_email": "security-team@your-company.com"
  }'
```

---

## Agent Monitoring

### Get Usage Statistics

```bash
curl -X GET https://pilot.owkai.app/api/registry/agents/{agent_id}/usage \
  -H "Authorization: Bearer ascend_your_api_key"
```

Response:
```json
{
  "actions_this_minute": 5,
  "actions_this_hour": 45,
  "actions_this_day": 320,
  "current_daily_spend_usd": 25.50,
  "health_status": "online",
  "last_heartbeat": "2025-12-03T10:30:00Z"
}
```

### Get Anomaly Detection Alerts

```bash
curl -X GET https://pilot.owkai.app/api/registry/agents/{agent_id}/anomalies \
  -H "Authorization: Bearer ascend_your_api_key"
```

### Set Baselines for Anomaly Detection

```bash
curl -X POST https://pilot.owkai.app/api/registry/agents/{agent_id}/set-baselines \
  -H "Authorization: Bearer ascend_your_api_key"
```

---

## Emergency Kill Switch (SOC 2 CC6.2 / NIST IR-4)

Immediately suspend an agent in case of security incident:

```bash
curl -X POST https://pilot.owkai.app/api/registry/agents/{agent_id}/emergency-suspend \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Detected unauthorized data access pattern - immediate investigation required"
  }'
```

**Effects:**
- Agent status immediately set to `suspended`
- All pending actions blocked
- Audit log entry created
- Webhook notification sent (if configured)
- Manual reactivation required via dashboard

---

## SDK Integration

### Python SDK

```bash
pip install requests python-dotenv  # No SDK package - use REST API directly
```

```python
from owkai_sdk import AscendClient, FailMode, Decision

client = AscendClient(api_key="owkai_your_api_key")

# Register agent
agent = client.register_agent(
    agent_id="my-agent-001",
    name="Customer Service Bot",
    agent_type="autonomous"
)

# Evaluate an action (handles risk scoring + approval flow)
result = client.evaluate_action(
    agent_id="my-agent-001",
    action_type="database.read",
    tool_name="postgres_query",
    description="Query customer records"
)

if result.approved:
    # Proceed with action
    pass
elif result.requires_approval:
    # Wait for manual approval or poll status
    status = client.poll_action_status(result.action_id, timeout=300)
else:
    # Action denied
    print(f"Denied: {result.denial_reason}")
```

### Node.js SDK

```bash
npm install @ascend/sdk
# or
yarn add @ascend/sdk
```

```typescript
import { AscendClient, FailMode, Decision } from '@ascend/sdk';

const client = new AscendClient({ apiKey: 'owkai_your_api_key' });

// Evaluate an action
const result = await client.evaluateAction({
  agentId: 'my-agent-001',
  actionType: 'database.read',
  toolName: 'postgres_query',
  description: 'Query customer records'
});

if (result.approved) {
  // Proceed with action
} else if (result.requiresApproval) {
  // Poll for approval
  const status = await client.pollActionStatus(result.actionId, { timeout: 300000 });
}
```

---

## Gateway Integrations (Zero-Code)

For infrastructure-level governance without application code changes, use our gateway integrations:

### Available Gateways

| Gateway | Best For | Deployment |
|---------|----------|------------|
| **[AWS Lambda Authorizer](./gateway/lambda-authorizer/)** | AWS API Gateway | CloudFormation/SAM |
| **[Kong Plugin](./gateway/kong-plugin/)** | Kong Gateway | LuaRocks |
| **[Envoy/Istio ext_authz](./gateway/envoy-istio/)** | Kubernetes/Service Mesh | Helm |

### When to Use Gateway Integration

- **Zero Application Changes**: Governance enforced at infrastructure layer
- **Uniform Policy Enforcement**: All traffic governed regardless of client
- **FAIL SECURE Design**: Requests blocked on any error (default behavior)
- **Existing Infrastructure**: Integrate with your current API gateway or service mesh

See the **[Gateway Integration Overview](./gateway/)** for detailed comparison and decision matrix.

---

## Integration Endpoints

### Action Submission

| Endpoint | Purpose | Authentication | Use Case |
|----------|---------|----------------|----------|
| `POST /api/authorization/agent-action` | Full enterprise pipeline | API Key or JWT | Production integrations |
| `POST /api/sdk/agent-action` | SDK-optimized endpoint | API Key | SDK users |
| `GET /api/agent-action/status/{id}` | Poll action status | API Key or JWT | Async workflows |
| `POST /api/authorization/approve/{id}` | Approve pending action | JWT (Admin) | Manual approvals |

### Agent Registry (SEC-068)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/registry/agents` | POST | Register new agent |
| `/api/registry/agents` | GET | List all agents |
| `/api/registry/agents/{id}` | GET | Get agent details |
| `/api/registry/agents/{id}` | PUT | Update agent |
| `/api/registry/agents/{id}` | DELETE | Delete agent |
| `/api/registry/agents/{id}/activate` | POST | Activate agent |
| `/api/registry/agents/{id}/suspend` | POST | Suspend agent |

### Agent Governance Controls (SEC-068)

| Endpoint | Method | Purpose | Compliance |
|----------|--------|---------|------------|
| `/api/registry/agents/{id}/rate-limits` | PUT | Configure rate limits | SOC 2 CC6.2 |
| `/api/registry/agents/{id}/budget` | PUT | Set budget controls | PCI-DSS 7.1 |
| `/api/registry/agents/{id}/time-window` | PUT | Set operating hours | SOC 2 A1.1 |
| `/api/registry/agents/{id}/data-classifications` | PUT | Data access controls | HIPAA 164.312 |
| `/api/registry/agents/{id}/auto-suspend` | PUT | Auto-suspension rules | NIST AC-2(3) |
| `/api/registry/agents/{id}/escalation` | PUT | Webhook/email config | CR-003 |
| `/api/registry/agents/{id}/usage` | GET | Usage statistics | SOC 2 CC6.2 |
| `/api/registry/agents/{id}/anomalies` | GET | Anomaly alerts | NIST SI-4 |
| `/api/registry/agents/{id}/emergency-suspend` | POST | Emergency kill switch | NIST IR-4 |
| `/api/registry/agents/{id}/set-baselines` | POST | Set anomaly baselines | NIST SI-4 |

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
Authorization: Bearer owkai_your_api_key_here
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

- **Documentation**: https://pilot.owkai.app/api/docs
- **Support Email**: support@ascendowkai.com
- **Status Page**: https://status.owkai.app
- **API Reference**: https://pilot.owkai.app/api/docs (Swagger UI)

---

## Next Steps

### Essential Reading

1. [Agent Registry - Technical Documentation](./AGENT_REGISTRY.md) - Complete technical guide for agent registration, governance controls, and API reference
2. [Agent Governance Guide](./AGENT_GOVERNANCE.md) - Business guide for governing autonomous AI agents
3. [SDK Integration Guide](./SDK_GUIDE.md) - Python and Node.js SDK usage with evaluate_action()
4. [API Reference](./API_REFERENCE.md) - Complete endpoint documentation

### Gateway Integrations (Zero-Code)

5. [Gateway Integration Overview](./gateway/) - Comparison and decision matrix for all gateways
6. [AWS Lambda Authorizer](./gateway/lambda-authorizer/) - API Gateway integration with CloudFormation
7. [Kong Gateway Plugin](./gateway/kong-plugin/) - Kong plugin with LuaRocks packaging
8. [Envoy/Istio ext_authz](./gateway/envoy-istio/) - Service mesh integration with Helm

### Advanced Topics

9. [Risk Scoring Deep Dive](./RISK_SCORING.md) - Multi-layer risk scoring architecture
10. [Architecture Overview](./ARCHITECTURE.md) - Platform components and data flow
11. [BYOK/CMK Encryption](/docs/byok/CUSTOMER_KMS_SETUP.md) - Bring Your Own Key encryption setup

---

*Document Version: 2.1.0 | Last Updated: December 2025 | Compliance: SOC 2 CC6.1, PCI-DSS 7.1, NIST 800-53, HIPAA, GDPR*
