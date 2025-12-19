---
title: API Overview
sidebar_position: 1
---

# API Overview

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-API-001 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

The Ascend Platform REST API provides programmatic access to enterprise-grade agent governance, policy management, compliance automation, and real-time security orchestration. Built with banking-level security and multi-tenant isolation, our API powers mission-critical workflows for Fortune 500 companies.

## Base URLs

```
Production:  https://pilot.owkai.app
Sandbox:     https://sandbox-pilot.owkai.app
```

## Enterprise Security Architecture

### Authentication Methods

Ascend supports three authentication methods, each designed for specific use cases with industry-leading security standards:

| Method | Use Case | Security Standard | Token Lifetime |
|--------|----------|-------------------|----------------|
| **Cookie Sessions** | Web applications, dashboards | HttpOnly, Secure, SameSite=Strict | 24 hours (configurable) |
| **AWS Cognito JWT** | Enterprise SSO, mobile apps | RS256 signature, JWKS validation | 1 hour (auto-refresh) |
| **API Keys** | Server-to-server, SDKs, automation | SHA-256 hashing with salt, HMAC signing | Custom expiration |

#### Quick Start: Cookie Authentication

```bash
# 1. Login to get session cookie
curl -X POST https://pilot.owkai.app/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@company.com", "password": "SecurePass123!"}' \
  -c cookies.txt

# 2. Use cookie in subsequent requests
curl https://pilot.owkai.app/api/v1/actions \
  -b cookies.txt
```

#### Quick Start: API Key Authentication

```bash
# 1. Generate API key (requires existing session)
curl -X POST https://pilot.owkai.app/api/keys/generate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production SDK",
    "description": "Production environment API key",
    "expires_in_days": 90
  }'

# 2. Use API key (returned only once - store securely)
curl https://pilot.owkai.app/api/v1/actions/submit \
  -H "X-API-Key: owkai_live_xxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "database_query",
    "target_resource": "users",
    "agent_id": "agent-001"
  }'
```

[Complete Authentication Guide →](/sdk/rest/authentication)

### Multi-Tenant Isolation

**CRITICAL:** All API endpoints enforce organization-level data isolation. Users can ONLY access data belonging to their organization. This is enforced at the database query level using the `get_organization_filter()` dependency:

```python
# Every database query is automatically filtered
db.query(Model).filter(Model.organization_id == org_id)
```

**Security Guarantees:**
- Cross-tenant data access is impossible at the API layer
- Organization ID extracted from authenticated user token
- No manual organization selection - prevents privilege escalation
- Compliance: SOC 2 CC6.1, PCI-DSS 7.1, HIPAA 164.312(a)

---

## Core API Endpoints

### Authentication & Authorization

**Prefix:** `/api/auth`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/token` | POST | Login with email/password | No |
| `/api/auth/me` | GET | Get current user profile | Yes |
| `/api/auth/refresh-token` | POST | Refresh session token | Yes |
| `/api/auth/logout` | POST | Logout (invalidates all tokens) | Yes |
| `/api/auth/csrf` | GET | Get CSRF token for state-changing requests | Yes |
| `/api/auth/change-password` | POST | Change current user password | Yes |
| `/api/auth/forgot-password` | POST | Request password reset email | No |
| `/api/auth/confirm-reset-password` | POST | Complete password reset with code | No |
| `/api/auth/cognito-session` | POST | Create session from Cognito tokens | No |
| `/api/auth/mfa-status` | GET | Check MFA enrollment status | Yes |
| `/api/auth/mfa/setup-totp` | POST | Generate TOTP secret and QR code | Yes |
| `/api/auth/mfa/verify-totp` | POST | Verify TOTP code to complete enrollment | Yes |
| `/api/auth/mfa/disable` | POST | Disable MFA for current user | Yes |
| `/api/auth/revoke-tokens` | POST | Revoke all user tokens (self) | Yes |
| `/api/auth/admin/revoke-user-tokens/{user_id}` | POST | Admin: Revoke user tokens | Admin |
| `/api/auth/admin/revoke-organization-tokens/{org_id}` | POST | Platform Admin: Revoke org tokens | Platform Admin |

**Source:** `routes/auth.py`

---

### Agent Actions & Governance

**Prefix:** `/api/v1/actions`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/v1/actions/submit` | POST | Submit agent action for governance evaluation | Yes (Cookie/Cognito/API Key) |
| `/api/v1/actions` | GET | List agent actions for organization | Yes |
| `/api/v1/actions/{action_id}` | GET | Get action details | Yes |
| `/api/v1/actions/{action_id}/status` | GET | Get action status | Yes |
| `/api/v1/actions/{action_id}/approve` | POST | Approve pending action | Yes |
| `/api/v1/actions/{action_id}/reject` | POST | Reject pending action | Yes |
| `/api/v1/actions/{action_id}/false-positive` | POST | Mark as false positive (retrains ML) | Yes |
| `/api/audit-trail` | GET | Complete audit trail with filters | Yes |
| `/api/models` | GET | List available AI models | Yes |
| `/api/support/submit` | POST | Submit support ticket | Yes |
| `/api/v1/actions/upload-json` | POST | Bulk upload actions from JSON | Yes |

**Example: Submit Agent Action**

```bash
curl -X POST https://pilot.owkai.app/api/v1/actions/submit \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "action_type": "database_query",
    "target_resource": "users",
    "agent_id": "agent-prod-001",
    "risk_category": "data_access",
    "justification": "Fetch user data for analytics dashboard",
    "metadata": {
      "query": "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY",
      "database": "production_db"
    }
  }'
```

**Response:**

```json
{
  "id": 12345,
  "action_id": "act_abc123xyz",
  "status": "pending_approval",
  "risk_score": 72,
  "requires_approval": true,
  "policy_evaluation": {
    "matched_policies": ["POL-001: Production DB Access"],
    "decision": "deny_pending_approval",
    "risk_level": "high"
  },
  "created_at": "2025-12-04T10:30:00Z"
}
```

**Source:** `routes/agent_routes.py`

---

### Authorization & Approvals

**Prefix:** `/api/authorization`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/authorization/pending-actions` | GET | List pending approval requests | Yes |
| `/api/authorization/authorize/{action_id}` | POST | Approve/reject action | Admin |
| `/api/authorization/authorize-with-audit/{action_id}` | POST | Approve with audit trail | Admin |
| `/api/authorization/dashboard` | GET | Approval dashboard metrics | Yes |
| `/api/authorization/execution-history` | GET | Action execution history | Yes |
| `/api/authorization/policies/create-from-natural-language` | POST | Create policy from natural language | Admin |
| `/api/authorization/policies/{policy_id}/deploy` | POST | Deploy policy version | Admin |
| `/api/authorization/policies/{policy_id}/rollback/{version_id}` | POST | Rollback policy to version | Admin |
| `/api/authorization/mcp-discovery/scan-network` | POST | Discover MCP servers on network | Admin |
| `/api/authorization/mcp-discovery/server-status` | GET | MCP server health status | Yes |
| `/api/authorization/mcp-discovery/health-monitor` | GET | Real-time health monitoring | Yes |
| `/api/authorization/debug/policies` | GET | Debug policy evaluation | Admin |

**Source:** `routes/authorization_routes.py`

---

### Automation Playbooks & Workflows

**Prefix:** `/api/authorization/automation`, `/api/authorization/orchestration`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/authorization/automation/playbooks` | GET | List automation playbooks | Yes |
| `/api/authorization/automation/playbooks` | POST | Create playbook | Admin |
| `/api/authorization/automation/playbook/{playbook_id}/toggle` | POST | Enable/disable playbook | Admin |
| `/api/authorization/automation/execute-playbook` | POST | Execute playbook | Yes |
| `/api/authorization/automation/playbooks/{playbook_id}/test` | POST | Test playbook in dry-run mode | Admin |
| `/api/authorization/automation/playbook-templates` | GET | List playbook templates | Yes |
| `/api/authorization/automation/playbook/{playbook_id}` | DELETE | Delete playbook | Admin |
| `/api/authorization/automation/playbook/{playbook_id}/restore` | POST | Restore deleted playbook | Admin |
| `/api/authorization/automation/playbooks/deleted` | GET | List deleted playbooks | Admin |
| `/api/authorization/automation/playbook/{playbook_id}/permanent` | DELETE | Permanently delete playbook | Admin |
| `/api/authorization/automation/playbooks/{playbook_id}/versions` | GET | List playbook versions | Yes |
| `/api/authorization/automation/playbooks/{playbook_id}/versions` | POST | Create new version | Admin |
| `/api/authorization/automation/playbooks/{playbook_id}/rollback` | POST | Rollback to version | Admin |
| `/api/authorization/automation/playbooks/{playbook_id}/analytics` | GET | Playbook analytics | Yes |
| `/api/authorization/automation/playbooks/{playbook_id}/performance` | GET | Performance metrics | Yes |
| `/api/authorization/automation/playbooks/clone` | POST | Clone playbook | Admin |
| `/api/authorization/orchestration/active-workflows` | GET | List active workflows | Yes |
| `/api/authorization/workflows/create` | POST | Create workflow | Admin |
| `/api/authorization/workflows` | GET | List workflows | Yes |
| `/api/authorization/workflow-config` | GET | Get workflow configuration | Admin |
| `/api/authorization/workflow-config` | POST | Update workflow configuration | Admin |
| `/api/authorization/orchestration/execute/{workflow_id}` | POST | Execute workflow | Yes |
| `/api/authorization/automation/activity-feed` | GET | Automation activity feed | Yes |

**Source:** `routes/automation_orchestration_routes.py`, `routes/playbook_deletion_routes.py`, `routes/playbook_versioning_routes.py`, `routes/enterprise_workflow_config_routes.py`

---

### Unified Governance & Policies

**Prefix:** `/api` (various governance endpoints)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/unified/action` | POST | Submit unified governance action | Yes |
| `/api/unified-stats` | GET | Unified governance statistics | Yes |
| `/api/unified-actions` | GET | List unified actions | Yes |
| `/api/unified/actions` | GET | Alternative unified actions endpoint | Yes |
| `/api/policies` | GET | List all policies | Yes |
| `/api/create-policy` | POST | Create new policy | Admin |
| `/api/policies/{policy_id}` | PUT | Update policy | Admin |
| `/api/policies/{policy_id}` | DELETE | Delete policy | Admin |
| `/api/policies/{policy_id}/check-conflicts` | POST | Check for policy conflicts | Admin |
| `/api/policies/conflicts/analyze` | GET | Analyze all policy conflicts | Admin |
| `/api/policies/export` | GET | Export policies | Admin |
| `/api/policies/import` | POST | Import policies | Admin |
| `/api/policies/import/template` | GET | Get import template | Admin |
| `/api/policies/backup` | POST | Backup policies | Admin |
| `/api/policies/bulk-update-status` | POST | Bulk update policy status | Admin |
| `/api/policies/bulk-delete` | POST | Bulk delete policies | Admin |
| `/api/policies/bulk-update-priority` | POST | Bulk update policy priority | Admin |
| `/api/policies/templates` | GET | List policy templates | Yes |
| `/api/policies/from-template` | POST | Create policy from template | Admin |
| `/api/policies/dashboard/pending-approvals` | GET | Pending approvals dashboard | Yes |
| `/api/health` | GET | Governance health check | Yes |
| `/api/admin/unified-report` | GET | Admin unified governance report | Admin |

**Source:** `routes/unified_governance_routes.py`

---

### MCP (Model Context Protocol) Governance

**Prefix:** `/api/mcp`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/mcp/evaluate` | POST | Evaluate MCP action against policies | Yes |
| `/api/mcp/execute` | POST | Execute approved MCP action | Yes |
| `/api/mcp/servers/register` | POST | Register MCP server | Admin |
| `/api/mcp/servers` | GET | List registered MCP servers | Yes |
| `/api/mcp/actions/pending` | GET | List pending MCP actions | Yes |
| `/api/mcp/actions/{action_id}/approve` | POST | Approve MCP action | Admin |
| `/api/mcp/actions/all` | GET | List all MCP actions | Yes |
| `/api/mcp/policies` | POST | Create MCP policy | Admin |
| `/api/mcp/policies` | GET | List MCP policies | Yes |
| `/api/mcp/analytics/dashboard` | GET | MCP analytics dashboard | Yes |
| `/api/mcp/health` | GET | MCP system health | Yes |
| `/api/mcp/test/evaluate` | POST | Test MCP policy evaluation | Admin |
| `/api/mcp/actions/assess-risk-enterprise` | POST | Enterprise risk assessment | Yes |
| `/api/mcp/actions` | GET | List MCP actions | Yes |
| `/api/mcp/actions/ingest` | POST | Ingest MCP actions | Yes |

**Source:** `routes/mcp_governance_routes.py`, `routes/mcp_enterprise_secure.py`, `routes/mcp_governance_adapter.py`

---

### Agent Registry & Health

**Prefix:** `/api/registry`, `/api/agents/health`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/registry/agents` | POST | Register new agent | Admin |
| `/api/registry/agents` | GET | List registered agents | Yes |
| `/api/registry/agents/{agent_id}` | GET | Get agent details | Yes |
| `/api/registry/agents/{agent_id}` | PUT | Update agent | Admin |
| `/api/registry/agents/{agent_id}` | DELETE | Delete agent | Admin |
| `/api/registry/agents/{agent_id}/activate` | POST | Activate agent | Admin |
| `/api/registry/agents/{agent_id}/suspend` | POST | Suspend agent | Admin |
| `/api/registry/agents/{agent_id}/emergency-suspend` | POST | Emergency suspend agent | Admin |
| `/api/registry/agents/{agent_id}/versions` | GET | List agent versions | Yes |
| `/api/registry/agents/{agent_id}/rollback` | POST | Rollback to version | Admin |
| `/api/registry/agents/{agent_id}/policies` | POST | Attach policy to agent | Admin |
| `/api/registry/agents/{agent_id}/policies` | GET | List agent policies | Yes |
| `/api/registry/agents/{agent_id}/evaluate` | POST | Evaluate agent behavior | Admin |
| `/api/registry/agents/{agent_id}/usage` | GET | Agent usage statistics | Yes |
| `/api/registry/agents/{agent_id}/anomalies` | GET | Detect agent anomalies | Yes |
| `/api/registry/agents/{agent_id}/rate-limits` | PUT | Update rate limits | Admin |
| `/api/registry/agents/{agent_id}/budget` | PUT | Update cost budget | Admin |
| `/api/registry/agents/{agent_id}/time-window` | PUT | Update time window limits | Admin |
| `/api/registry/agents/{agent_id}/escalation` | PUT | Update escalation config | Admin |
| `/api/registry/agents/{agent_id}/auto-suspend` | PUT | Configure auto-suspend | Admin |
| `/api/registry/agents/{agent_id}/data-classifications` | PUT | Set data classifications | Admin |
| `/api/registry/agents/{agent_id}/set-baselines` | POST | Set performance baselines | Admin |
| `/api/registry/mcp-servers` | POST | Register MCP server | Admin |
| `/api/registry/mcp-servers` | GET | List MCP servers | Yes |
| `/api/registry/mcp-servers/{server_name}` | GET | Get MCP server details | Yes |
| `/api/registry/mcp-servers/{server_name}` | PUT | Update MCP server | Admin |
| `/api/registry/mcp-servers/{server_name}` | DELETE | Delete MCP server | Admin |
| `/api/registry/mcp-servers/{server_name}/activate` | POST | Activate MCP server | Admin |
| `/api/registry/mcp-servers/{server_name}/deactivate` | POST | Deactivate MCP server | Admin |
| `/api/agents/health/heartbeat` | POST | Submit agent heartbeat | Yes |
| `/api/agents/health/heartbeat/batch` | POST | Submit batch heartbeats | Yes |
| `/api/agents/health/summary` | GET | Health summary for all agents | Yes |
| `/api/agents/health/{agent_id}` | GET | Health status for agent | Yes |
| `/api/agents/health/{agent_id}/interval` | PUT | Update heartbeat interval | Admin |
| `/api/agents/health/check` | POST | Force health check | Admin |
| `/api/agents/health/public/status` | GET | Public health status (no auth) | No |

**Source:** `routes/agent_registry_routes.py`, `routes/agent_health_routes.py`

---

### API Key Management

**Prefix:** `/api/keys`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/keys/generate` | POST | Generate new API key | Admin |
| `/api/keys/list` | GET | List API keys for organization | Admin |
| `/api/keys/{key_id}/revoke` | DELETE | Revoke API key | Admin |
| `/api/keys/{key_id}/usage` | GET | Get API key usage statistics | Admin |

**Example: Generate API Key**

```bash
curl -X POST https://pilot.owkai.app/api/keys/generate \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production SDK",
    "description": "API key for production environment",
    "expires_in_days": 90,
    "rate_limit": {
      "max_requests": 5000,
      "window_seconds": 3600
    }
  }'
```

**Response (Secret shown ONCE - store securely):**

```json
{
  "success": true,
  "api_key": "owkai_admin_tUsL1234567890abcdef",
  "key_id": 42,
  "key_prefix": "owkai_admin_tUsL",
  "name": "Production SDK",
  "expires_at": "2026-03-04T10:30:00Z",
  "created_at": "2025-12-04T10:30:00Z",
  "warning": "⚠️ Save this key now - you will NOT see it again!"
}
```

**Source:** `routes/api_key_routes.py`

---

### Alerts & Insights

**Prefix:** `/api` (alert endpoints)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/alerts` | GET | List alerts for organization | Yes |
| `/api/alerts/count` | GET | Get alert count | Yes |
| `/api/alerts/{alert_id}` | PATCH | Update alert (acknowledge/resolve) | Yes |
| `/api/alerts/create-test-data` | POST | Create test alerts (dev only) | Admin |
| `/api/alerts/summary` | POST | Generate alert summary | Yes |
| `/api/alerts/summary-text` | POST | Generate text-based summary | Yes |
| `/api/active` | GET | List active alerts | Yes |
| `/api/{alert_id}/acknowledge` | POST | Acknowledge alert | Yes |
| `/api/{alert_id}/resolve` | POST | Resolve alert | Yes |
| `/api/{alert_id}/escalate` | POST | Escalate alert | Admin |

**Source:** `routes/alert_routes.py`, `routes/alert_summary.py`, `routes/smart_alerts.py`

---

### Analytics & Insights

**Prefix:** `/api` (analytics endpoints)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/analytics/trends` | GET | Alert trends over time | Yes |
| `/api/analytics/realtime/metrics` | GET | Real-time metrics | Yes |
| `/api/analytics/predictive/trends` | GET | Predictive analytics | Yes |
| `/api/analytics/executive/dashboard` | GET | Executive dashboard | Admin |
| `/api/analytics/performance` | GET | Performance analytics | Yes |
| `/api/analytics/performance/system` | GET | System performance metrics | Yes |
| `/api/analytics/debug` | GET | Debug analytics data | Admin |

**WebSocket:**
```
wss://pilot.owkai.app/analytics/ws/realtime/{user_email}
```

**Source:** `routes/analytics_routes.py`

---

### Executive Briefs

**Prefix:** `/api/executive-briefs`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/executive-briefs/latest` | GET | Get latest executive brief | Admin |
| `/api/executive-briefs/{brief_id}` | GET | Get specific brief | Admin |
| `/api/executive-briefs/generate` | POST | Generate new brief | Admin |
| `/api/executive-briefs/regenerate` | POST | Force regenerate brief | Admin |
| `/api/executive-briefs/cooldown` | GET | Check cooldown status | Admin |
| `/api/executive-briefs/history` | GET | Brief generation history | Admin |

**Source:** `routes/executive_brief_routes.py`

---

### Rules & Smart Rules

**Prefix:** `/api` (rule endpoints)

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/rules` | GET | List rules | Yes |
| `/api/rules` | POST | Create rule | Admin |
| `/api/rules/{rule_id}` | DELETE | Delete rule | Admin |
| `/api/rules/seed` | POST | Seed default rules | Admin |
| `/api/rules/generate-smart-rule` | POST | Generate smart rule with AI | Admin |
| `/api/feedback/{rule_id}` | GET | Get rule feedback | Yes |
| `/api/feedback/{rule_id}` | POST | Submit rule feedback | Yes |
| `/api/smart-rules/analytics` | GET | Smart rule analytics | Yes |
| `/api/smart-rules/ab-tests` | GET | List A/B tests | Yes |
| `/api/smart-rules/ab-test` | POST | Create A/B test | Admin |
| `/api/smart-rules/ab-test/{test_id}` | GET | Get A/B test details | Yes |
| `/api/smart-rules/ab-test/{test_id}/stop` | POST | Stop A/B test | Admin |
| `/api/smart-rules/ab-test/{test_id}/deploy` | POST | Deploy winning variant | Admin |
| `/api/smart-rules/ab-test/{test_id}` | DELETE | Delete A/B test | Admin |
| `/api/smart-rules/suggestions` | GET | Get rule suggestions | Yes |
| `/api/smart-rules/generate-from-nl` | POST | Generate rule from natural language | Admin |
| `/api/smart-rules/optimize/{rule_id}` | POST | Optimize rule with ML | Admin |
| `/api/smart-rules/{rule_id}` | DELETE | Delete smart rule | Admin |
| `/api/smart-rules/generate` | POST | Generate smart rule | Admin |
| `/api/smart-rules/seed` | POST | Seed default smart rules | Admin |

**Source:** `routes/rule_routes.py`, `routes/smart_rules_routes.py`

---

### Compliance & Audit

**Prefix:** `/api/compliance-export`, `/api/audit`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/compliance-export/frameworks` | GET | List compliance frameworks | Admin |
| `/api/compliance-export/frameworks/{framework}` | GET | Get framework details | Admin |
| `/api/compliance-export/exports` | POST | Create export job | Admin |
| `/api/compliance-export/exports` | GET | List export jobs | Admin |
| `/api/compliance-export/exports/{job_id}` | GET | Get export job status | Admin |
| `/api/compliance-export/exports/{job_id}/download` | GET | Download export | Admin |
| `/api/compliance-export/exports/{job_id}/downloads` | GET | List downloads for job | Admin |
| `/api/compliance-export/exports/{job_id}/verify` | POST | Verify export integrity | Admin |
| `/api/compliance-export/schedules` | POST | Create export schedule | Admin |
| `/api/compliance-export/schedules` | GET | List schedules | Admin |
| `/api/compliance-export/schedules/{schedule_id}` | GET | Get schedule details | Admin |
| `/api/compliance-export/schedules/{schedule_id}` | PUT | Update schedule | Admin |
| `/api/compliance-export/schedules/{schedule_id}` | DELETE | Delete schedule | Admin |
| `/api/compliance-export/quick-export/{framework}/{report_type}` | POST | Quick export | Admin |
| `/api/compliance-export/metrics` | GET | Compliance metrics | Admin |
| `/api/audit/health` | GET | Audit system health | Admin |
| `/api/audit/log` | POST | Submit audit log entry | Yes |
| `/api/audit/logs` | GET | Query audit logs | Admin |
| `/api/audit/verify-integrity` | POST | Verify audit log integrity | Admin |
| `/api/audit/export/csv` | GET | Export audit logs as CSV | Admin |
| `/api/audit/export/pdf` | GET | Export audit logs as PDF | Admin |

**Supported Compliance Frameworks:**
- SOC 2 Type II
- PCI-DSS
- HIPAA
- GDPR
- SOX
- ISO 27001
- NIST 800-53
- CCPA

**Source:** `routes/compliance_export_routes.py`, `routes/audit_routes.py`

---

### Data Rights (GDPR/CCPA)

**Prefix:** `/api/data-rights`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/data-rights/access/request` | POST | Request data access (GDPR Art. 15) | Yes |
| `/api/data-rights/access/{request_id}/data` | GET | Download data access request | Yes |
| `/api/data-rights/erasure/request` | POST | Request data erasure (GDPR Art. 17) | Yes |
| `/api/data-rights/erasure/{request_id}/execute` | POST | Execute erasure request | Admin |
| `/api/data-rights/portability/request` | POST | Request data portability (GDPR Art. 20) | Yes |
| `/api/data-rights/consent/record` | POST | Record consent | Yes |
| `/api/data-rights/lineage/record` | POST | Record data lineage | Yes |
| `/api/data-rights/lineage/subject/{subject_identifier}` | GET | Get data lineage | Admin |
| `/api/data-rights/compliance/report` | GET | Compliance report | Admin |
| `/api/data-rights/requests` | GET | List data rights requests | Admin |
| `/api/data-rights/requests/{request_id}` | GET | Get request details | Yes |
| `/api/data-rights/health` | GET | Data rights system health | Admin |

**Source:** `routes/data_rights_routes.py`

---

### Enterprise Integrations

**Prefix:** `/api/integrations`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/integrations/types` | GET | List integration types | Yes |
| `/api/integrations/templates` | GET | List integration templates | Yes |
| `/api/integrations/status` | GET | Integration status | Yes |
| `/api/integrations/{integration_id}` | GET | Get integration details | Yes |
| `/api/integrations/{integration_id}` | PUT | Update integration | Admin |
| `/api/integrations/{integration_id}` | DELETE | Delete integration | Admin |
| `/api/integrations/health/summary` | GET | Health summary for all integrations | Yes |
| `/api/integrations/{integration_id}/health-check` | POST | Run health check | Admin |
| `/api/integrations/{integration_id}/health-history` | GET | Health check history | Yes |
| `/api/integrations/data-flows` | POST | Create data flow | Admin |
| `/api/integrations/data-flows/from-template` | POST | Create from template | Admin |
| `/api/integrations/data-flows` | GET | List data flows | Yes |
| `/api/integrations/data-flows/{data_flow_id}/execute` | POST | Execute data flow | Admin |
| `/api/integrations/events` | GET | List integration events | Yes |
| `/api/integrations/events/correlate` | POST | Correlate events | Admin |
| `/api/integrations/dashboard` | GET | Integration dashboard | Yes |
| `/api/integrations/metrics` | GET | Integration metrics | Yes |
| `/api/integrations/bulk` | POST | Bulk create integrations | Admin |
| `/api/integrations/test` | POST | Test integration | Admin |

**Integration Wizard:**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/integrations/wizard/types` | GET | List integration types | Yes |
| `/api/integrations/wizard/types/{type_id}` | GET | Get type details | Yes |
| `/api/integrations/wizard/code-snippets/{type_id}` | GET | Get code snippets | Yes |
| `/api/integrations/wizard/checklist/{type_id}` | GET | Get setup checklist | Yes |
| `/api/integrations/wizard/quick-start` | GET | Quick start guide | Yes |
| `/api/integrations/wizard/validate-config` | POST | Validate configuration | Admin |

**Source:** `routes/integration_suite_routes.py`, `routes/integration_wizard_routes.py`

---

### SIEM Integration

**Prefix:** `/api/siem-integration`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/siem-integration/status` | GET | SIEM integration status | Admin |
| `/api/siem-integration/configure` | POST | Configure SIEM connection | Admin |
| `/api/siem-integration/test-connection` | POST | Test SIEM connection | Admin |
| `/api/siem-integration/send-event` | POST | Send event to SIEM | Yes |
| `/api/siem-integration/forward-authorization/{action_id}` | POST | Forward authorization event | Yes |
| `/api/siem-integration/threat-intelligence` | POST | Send threat intelligence | Yes |
| `/api/siem-integration/query-events` | GET | Query SIEM events | Admin |
| `/api/siem-integration/metrics` | GET | SIEM integration metrics | Admin |
| `/api/siem-integration/bulk-forward` | POST | Bulk forward events | Admin |
| `/api/siem-integration/health` | GET | SIEM health check | Admin |

**Supported SIEM Platforms:**
- Splunk
- Datadog
- Wiz
- QRadar
- ArcSight
- LogRhythm

**Simplified SIEM API:**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/enterprise/siem/configure` | POST | Configure SIEM | Admin |
| `/api/enterprise/siem/test-connection` | POST | Test connection | Admin |
| `/api/enterprise/siem/status` | GET | Connection status | Admin |
| `/api/enterprise/siem/send-test-event` | POST | Send test event | Admin |
| `/api/enterprise/siem/supported-integrations` | GET | List supported platforms | Yes |
| `/api/enterprise/siem/disconnect` | DELETE | Disconnect SIEM | Admin |

**Source:** `routes/siem_integration.py`, `routes/siem_simple.py`

---

### ServiceNow Integration

**Prefix:** `/api/servicenow`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/servicenow/connections` | POST | Create ServiceNow connection | Admin |
| `/api/servicenow/connections` | GET | List connections | Admin |
| `/api/servicenow/connections/{connection_id}` | GET | Get connection details | Admin |
| `/api/servicenow/connections/{connection_id}` | PUT | Update connection | Admin |
| `/api/servicenow/connections/{connection_id}` | DELETE | Delete connection | Admin |
| `/api/servicenow/connections/{connection_id}/test` | POST | Test connection | Admin |
| `/api/servicenow/tickets` | POST | Create ServiceNow ticket | Yes |
| `/api/servicenow/tickets` | GET | List tickets | Yes |
| `/api/servicenow/tickets/{ticket_id}` | GET | Get ticket details | Yes |
| `/api/servicenow/tickets/{ticket_id}` | PUT | Update ticket | Admin |
| `/api/servicenow/tickets/{ticket_id}/retry` | POST | Retry failed ticket creation | Admin |
| `/api/servicenow/event-mappings` | GET | List event mappings | Admin |
| `/api/servicenow/metrics` | GET | ServiceNow metrics | Admin |
| `/api/servicenow/sync-logs` | GET | Sync logs | Admin |

**Source:** `routes/servicenow_routes.py`

---

### Webhooks

**Prefix:** `/api/webhooks`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/webhooks/events` | GET | List available webhook event types | Yes |
| `/api/webhooks` | POST | Create webhook subscription | Admin |
| `/api/webhooks` | GET | List subscriptions | Admin |
| `/api/webhooks/{subscription_id}` | GET | Get subscription details | Admin |
| `/api/webhooks/{subscription_id}` | PUT | Update subscription | Admin |
| `/api/webhooks/{subscription_id}` | DELETE | Delete subscription | Admin |
| `/api/webhooks/{subscription_id}/rotate-secret` | POST | Rotate webhook secret | Admin |
| `/api/webhooks/{subscription_id}/test` | POST | Send test webhook | Admin |
| `/api/webhooks/{subscription_id}/deliveries` | GET | List deliveries for subscription | Admin |
| `/api/webhooks/dlq/entries` | GET | List dead letter queue entries | Admin |
| `/api/webhooks/dlq/{dlq_id}/resolve` | POST | Resolve DLQ entry | Admin |
| `/api/webhooks/dlq/{dlq_id}/retry` | POST | Retry DLQ entry | Admin |
| `/api/webhooks/metrics` | GET | Webhook metrics | Admin |

**Supported Webhook Events:**
- `action.submitted`
- `action.approved`
- `action.rejected`
- `action.executed`
- `action.failed`
- `policy.created`
- `policy.updated`
- `policy.deleted`
- `policy.violated`
- `alert.triggered`
- `alert.resolved`
- `alert.escalated`
- `risk.threshold_exceeded`
- `risk.score_changed`
- `compliance.report_ready`
- `compliance.violation`
- `user.login`
- `user.logout`
- `user.mfa_enabled`
- `system.health_alert`

[Complete Webhook Documentation →](/sdk/rest/webhooks)

**Source:** `routes/webhook_routes.py`

---

### Notifications

**Prefix:** `/api/notifications`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/notifications/events` | GET | List notification events | Yes |
| `/api/notifications/channels` | POST | Create notification channel | Admin |
| `/api/notifications/channels` | GET | List channels | Admin |
| `/api/notifications/channels/{channel_id}` | GET | Get channel details | Admin |
| `/api/notifications/channels/{channel_id}` | PUT | Update channel | Admin |
| `/api/notifications/channels/{channel_id}` | DELETE | Delete channel | Admin |
| `/api/notifications/channels/{channel_id}/test` | POST | Test channel | Admin |
| `/api/notifications/channels/{channel_id}/pause` | POST | Pause channel | Admin |
| `/api/notifications/channels/{channel_id}/resume` | POST | Resume channel | Admin |
| `/api/notifications/channels/{channel_id}/deliveries` | GET | List deliveries | Admin |
| `/api/notifications/deliveries` | GET | List all deliveries | Admin |
| `/api/notifications/metrics` | GET | Notification metrics | Admin |
| `/api/notifications/send` | POST | Send notification | Admin |

**Supported Channels:**
- Email
- SMS
- Slack
- Microsoft Teams
- Webhook

**Source:** `routes/notification_routes.py`

---

### Risk Configuration

**Prefix:** `/api/risk-scoring`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/risk-scoring/config` | GET | Get current risk configuration | Admin |
| `/api/risk-scoring/config/history` | GET | Configuration history | Admin |
| `/api/risk-scoring/config` | POST | Create risk configuration | Admin |
| `/api/risk-scoring/config/{config_id}/activate` | PUT | Activate configuration | Admin |
| `/api/risk-scoring/config/validate` | POST | Validate configuration | Admin |
| `/api/risk-scoring/config/rollback-to-default` | POST | Rollback to default config | Admin |

**Source:** `routes/risk_scoring_config_routes.py`

---

### User Management

**Prefix:** `/api/admin`, `/api/enterprise-users`

#### Admin Console Users:

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/admin/organization` | GET | Get organization details | Admin |
| `/api/admin/organization` | PATCH | Update organization | Admin |
| `/api/admin/users` | GET | List users | Admin |
| `/api/admin/users/invite` | POST | Invite user | Admin |
| `/api/admin/users/{user_id}/role` | PATCH | Update user role | Admin |
| `/api/admin/users/{user_id}` | DELETE | Delete user | Admin |
| `/api/admin/users/{user_id}/suspend` | PATCH | Suspend/unsuspend user | Admin |
| `/api/admin/users/{user_id}/profile` | PATCH | Update user profile | Admin |
| `/api/admin/users/{user_id}/reset-password` | POST | Reset user password | Admin |
| `/api/admin/users/{user_id}/force-logout` | POST | Force user logout | Admin |
| `/api/admin/users/{user_id}/activity` | GET | User activity log | Admin |
| `/api/admin/users/bulk-operation` | POST | Bulk user operations | Admin |
| `/api/admin/rbac/levels` | GET | List RBAC levels | Admin |
| `/api/admin/rbac/users` | GET | List users with RBAC | Admin |
| `/api/admin/users/{user_id}/access-level` | PATCH | Update access level | Admin |

#### Enterprise User Management:

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/enterprise-users/users` | GET | List users | Admin |
| `/api/enterprise-users/users` | POST | Create user | Admin |
| `/api/enterprise-users/users/{user_id}` | PUT | Update user | Admin |
| `/api/enterprise-users/users/{user_id}` | DELETE | Delete user | Admin |
| `/api/enterprise-users/users/{user_id}/reset-password` | POST | Reset password | Admin |
| `/api/enterprise-users/users/{user_id}/unlock` | POST | Unlock account | Admin |
| `/api/enterprise-users/roles` | GET | List roles | Admin |
| `/api/enterprise-users/roles` | POST | Create role | Admin |
| `/api/enterprise-users/roles/{role_id}` | PUT | Update role | Admin |
| `/api/enterprise-users/audit-logs` | GET | User audit logs | Admin |
| `/api/enterprise-users/analytics` | GET | User analytics | Admin |

**Source:** `routes/admin_console_routes.py`, `routes/enterprise_user_management_routes.py`, `routes/admin_routes.py`

---

### Secret Rotation

**Prefix:** `/api/secrets`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/secrets/status` | GET | Rotation status for all secrets | Admin |
| `/api/secrets/rotate` | POST | Rotate specific secret | Admin |
| `/api/secrets/rotate-all` | POST | Rotate all secrets | Admin |
| `/api/secrets/schedule` | POST | Schedule rotation | Admin |
| `/api/secrets/schedules` | GET | List rotation schedules | Admin |
| `/api/secrets/schedule/{secret_name}` | DELETE | Delete schedule | Admin |
| `/api/secrets/compliance-report` | GET | Compliance report | Admin |
| `/api/secrets/audit-trail` | GET | Rotation audit trail | Admin |
| `/api/secrets/rotation-history` | GET | Rotation history | Admin |
| `/api/secrets/emergency-rotation` | POST | Emergency rotation | Admin |
| `/api/secrets/validate-secrets` | POST | Validate secrets | Admin |
| `/api/secrets/health` | GET | Secret rotation system health | Admin |

**Source:** `routes/enterprise_secrets_routes.py`

---

### Retention Policies

**Prefix:** `/api/retention`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/retention/health` | GET | Retention system health | Admin |
| `/api/retention/statistics` | GET | Retention statistics | Admin |
| `/api/retention/backfill` | POST | Backfill retention metadata | Admin |
| `/api/retention/expired` | GET | List expired items | Admin |
| `/api/retention/cleanup` | POST | Run cleanup job | Admin |
| `/api/retention/legal-hold` | POST | Apply legal hold | Admin |
| `/api/retention/legal-hold/release` | POST | Release legal hold | Admin |
| `/api/retention/job-status` | GET | Cleanup job status | Admin |
| `/api/retention/trigger-manual-cleanup` | POST | Trigger manual cleanup | Admin |

**Source:** `routes/retention_routes.py`

---

### Organization Administration

**Prefix:** `/api/organizations`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/organizations/{org_id}/users` | POST | Create user in organization | Admin |
| `/api/organizations/{org_id}/users` | GET | List users in organization | Admin |
| `/api/organizations/{org_id}/users/{user_id}` | DELETE | Delete user | Admin |
| `/api/organizations/{org_id}/users/{user_id}/role` | PATCH | Update user role | Admin |
| `/api/organizations/{org_id}/subscription-info` | GET | Get subscription info | Admin |
| `/api/organizations/users` | POST | Create user (current org) | Admin |
| `/api/organizations/users` | GET | List users (current org) | Admin |
| `/api/organizations/users/{user_id}` | DELETE | Delete user (current org) | Admin |
| `/api/organizations/users/{user_id}/role` | PATCH | Update role (current org) | Admin |
| `/api/organizations/subscription-info` | GET | Get subscription (current org) | Admin |

**Source:** `routes/organization_admin_routes.py`

---

### Platform Administration

**Prefix:** `/api/platform`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/platform/organizations` | GET | List all organizations | Platform Admin |
| `/api/platform/organizations` | POST | Create organization | Platform Admin |
| `/api/platform/organizations/{org_id}` | GET | Get organization details | Platform Admin |
| `/api/platform/usage-stats` | GET | Platform usage statistics | Platform Admin |
| `/api/platform/actions` | GET | All actions across platform | Platform Admin |
| `/api/platform/high-risk-actions` | GET | High-risk actions | Platform Admin |
| `/api/platform/auth-audit-log` | GET | Authentication audit log | Platform Admin |
| `/api/platform/brute-force-attempts` | GET | Brute force attempts | Platform Admin |
| `/api/platform/active-tokens` | GET | Active authentication tokens | Platform Admin |

**Source:** `routes/platform_admin_routes.py`

---

### Self-Service Signup

**Prefix:** `/api/signup`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/signup/request` | POST | Request organization signup | No |
| `/api/signup/verify-email` | POST | Verify email address | No |
| `/api/signup/resend-verification` | POST | Resend verification email | No |
| `/api/signup/status/{signup_id}` | GET | Check signup status | No |

**Source:** `routes/signup_routes.py`

---

### AWS Cognito Pool Management

**Prefix:** `/api/cognito`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/cognito/pool-config/by-slug/{organization_slug}` | GET | Get pool config by slug | Admin |
| `/api/cognito/pool-config/by-id/{organization_id}` | GET | Get pool config by org ID | Admin |
| `/api/cognito/pool-config/by-email/{email}` | GET | Get pool config by email | No |
| `/api/cognito/pool-status/{organization_slug}` | GET | Get pool status | Admin |
| `/api/cognito/organizations` | GET | List organizations with pools | Admin |
| `/api/cognito/health` | GET | Cognito integration health | Admin |

**Source:** `routes/cognito_pool_routes.py`

---

### SDK & Agent Integration

**Prefix:** `/api/sdk`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/sdk/agent/register` | POST | Register agent with SDK | API Key |
| `/api/sdk/action/{action_id}/completed` | POST | Mark action completed | API Key |
| `/api/sdk/action/{action_id}/failed` | POST | Mark action failed | API Key |
| `/api/sdk/approval/{approval_id}` | GET | Check approval status | API Key |
| `/api/sdk/webhooks/configure` | POST | Configure SDK webhooks | API Key |
| `/api/sdk/health` | GET | SDK health check | API Key |

**Source:** `routes/sdk_routes.py`

---

### Diagnostics & Health

**Prefix:** `/api/diagnostics`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/diagnostics/health` | GET | Overall system health | Admin |
| `/api/diagnostics/api` | GET | API health check | Admin |
| `/api/diagnostics/database` | GET | Database health check | Admin |
| `/api/diagnostics/integrations` | GET | Integration health check | Admin |
| `/api/diagnostics/history` | GET | Diagnostic history | Admin |
| `/api/diagnostics/export` | POST | Export diagnostics | Admin |

**Source:** `routes/diagnostics_routes.py`

---

### Documentation

**Prefix:** `/api/docs`

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/docs/integration` | GET | Integration documentation | Yes |
| `/api/docs/integration/readme` | GET | README documentation | Yes |
| `/api/docs/integration/risk-scoring` | GET | Risk scoring guide | Yes |
| `/api/docs/integration/api-reference` | GET | API reference | Yes |
| `/api/docs/integration/sdk-guide` | GET | SDK guide | Yes |
| `/api/docs/integration/architecture` | GET | Architecture documentation | Yes |
| `/api/docs/integration/agent-registry` | GET | Agent registry docs | Yes |
| `/api/docs/integration/agent-governance` | GET | Agent governance docs | Yes |
| `/api/docs/integration/governance-controls` | GET | Governance controls docs | Yes |
| `/api/docs/integration/{doc_name}` | GET | Get specific document | Yes |
| `/api/docs/quick-start` | GET | Quick start guide | Yes |
| `/api/docs/action-types` | GET | List action types | Yes |

**Source:** `routes/docs_routes.py`

---

### System Health & Info

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | System health check | No |
| `/api/deployment-info` | GET | Deployment information (commit SHA, build date) | No |
| `/api/models` | GET | List available AI models | Yes |
| `/api/logs` | GET | System logs | Admin |
| `/api/security-findings` | GET | Security findings | Admin |

**Source:** `routes/main_routes.py`, `main.py`

---

## Rate Limits & Quotas

### Default Rate Limits

| Auth Method | Requests/Minute | Requests/Hour | Requests/Day |
|-------------|-----------------|---------------|--------------|
| Cookie Session | 100 | 6,000 | 100,000 |
| Cognito JWT | 100 | 6,000 | 100,000 |
| API Key (default) | 1,000 | 60,000 | 1,000,000 |
| API Key (custom) | Configurable | Configurable | Configurable |

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1733308800
X-RateLimit-Retry-After: 45
```

### Brute Force Protection

| Protection Type | Threshold | Window | Lockout Duration |
|-----------------|-----------|--------|------------------|
| IP-based login attempts | 5 failures | 15 minutes | 15 minutes |
| Email-based login attempts | 10 failures | 15 minutes | Exponential (up to 24 hours) |
| API key brute force | 20 failures | 5 minutes | 1 hour |
| Password reset attempts | 5 requests | 1 hour | 1 hour |

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message",
  "error_code": "ERR_CODE",
  "request_id": "req_abc123xyz",
  "timestamp": "2025-12-04T10:30:00Z",
  "path": "/api/v1/actions"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| **200** | OK | Request successful |
| **201** | Created | Resource created successfully |
| **204** | No Content | Request successful, no content to return |
| **400** | Bad Request | Invalid request parameters |
| **401** | Unauthorized | Missing or invalid authentication |
| **403** | Forbidden | Insufficient permissions or cross-tenant access attempt |
| **404** | Not Found | Resource not found or not accessible |
| **409** | Conflict | Resource conflict (e.g., duplicate) |
| **422** | Unprocessable Entity | Validation error |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server error |
| **503** | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Insufficient permissions |
| `AUTH_004` | MFA required |
| `AUTH_005` | Account locked |
| `TENANT_001` | Cross-tenant access denied |
| `RATE_001` | Rate limit exceeded |
| `POLICY_001` | Policy violation |
| `VALIDATION_001` | Invalid input |

---

## Security Best Practices

### 1. Authentication

- **Web Apps:** Use cookie-based sessions with CSRF protection
- **Mobile Apps:** Use AWS Cognito JWT with secure token storage
- **Server-to-Server:** Use API keys with minimal required permissions
- **All Environments:** Enable MFA for admin accounts

### 2. API Key Security

- Store API keys in environment variables or secure vaults (AWS Secrets Manager, HashiCorp Vault)
- Never commit API keys to version control
- Rotate API keys every 90 days (or per your security policy)
- Use separate API keys for dev/staging/production
- Revoke API keys immediately if compromised

### 3. Request Security

- Always use HTTPS (TLS 1.3)
- Include CSRF token for state-changing requests (POST, PUT, DELETE, PATCH)
- Validate all input on client and server side
- Sanitize output to prevent XSS
- Use parameterized queries to prevent SQL injection

### 4. Data Security

- Never include sensitive data in URLs (use request body)
- Encrypt sensitive data at rest and in transit
- Implement proper access controls (RBAC)
- Audit all data access and modifications
- Follow principle of least privilege

### 5. Monitoring & Logging

- Monitor API usage for anomalies
- Set up alerts for unusual activity
- Review audit logs regularly
- Track API key usage
- Implement automated security scanning

---

## Compliance & Governance

### Regulatory Compliance

Ascend Platform API is compliant with:

- **SOC 2 Type II** - Security, availability, confidentiality
- **PCI-DSS** - Payment card industry data security
- **HIPAA** - Healthcare information privacy
- **GDPR** - EU data protection and privacy
- **SOX** - Financial reporting integrity
- **ISO 27001** - Information security management
- **NIST 800-53** - Federal information security controls
- **CCPA** - California consumer privacy

### Data Residency

- **US Region:** us-east-2 (Ohio)
- **EU Region:** eu-west-1 (Ireland) - Coming Soon
- **APAC Region:** ap-southeast-1 (Singapore) - Coming Soon

### Audit Trail

All API requests are logged with:
- Timestamp
- User/API key identity
- Organization ID
- IP address
- Request method and endpoint
- Request/response payloads (configurable)
- Response status code
- Processing duration

Audit logs are immutable and retained per your compliance requirements (default: 7 years).

---

## Webhook Events

Subscribe to real-time events via webhooks. See [Webhook Documentation](/sdk/rest/webhooks) for complete details.

**Available Events:**

| Category | Events |
|----------|--------|
| **Agent Actions** | action.submitted, action.approved, action.rejected, action.executed, action.failed |
| **Policies** | policy.created, policy.updated, policy.deleted, policy.violated |
| **Alerts** | alert.triggered, alert.resolved, alert.escalated |
| **Risk** | risk.threshold_exceeded, risk.score_changed |
| **Compliance** | compliance.report_ready, compliance.violation |
| **Users** | user.login, user.logout, user.mfa_enabled |
| **System** | system.health_alert |

---

## API Versioning

The Ascend API uses URL-based versioning:

```
Current Version: v1 (implicit in all /api/* endpoints)
Future Versions: /api/v2/* (when available)
```

**Versioning Policy:**
- Current version supported for minimum 24 months after new version release
- Breaking changes require new version
- Deprecation notices given 6 months in advance
- Security patches backported to all supported versions

---

## Support & Resources

### Documentation

- [Authentication Guide](/sdk/rest/authentication)
- [Endpoint Reference](/sdk/rest/endpoints)
- [Webhook Guide](/sdk/rest/webhooks)
- [Python SDK](/sdk/python/installation)
- [Node.js SDK](/sdk/nodejs/installation)

### API Status

- **Status Page:** [status.ascendowkai.com](https://status.ascendowkai.com)
- **Incident History:** [status.ascendowkai.com/history](https://status.ascendowkai.com/history)
- **Subscribe to Updates:** Email, SMS, Slack, Webhook

### Support Channels

- **Email:** [support@ascendowkai.com](mailto:support@ascendowkai.com)
- **Enterprise Support:** [enterprise@ascendowkai.com](mailto:enterprise@ascendowkai.com)
- **Security Issues:** [security@ascendowkai.com](mailto:security@ascendowkai.com)
- **GitHub Issues:** [github.com/ascend-platform/issues](https://github.com/ascend-platform/issues)

### SLA Guarantees

| Plan | Uptime SLA | Support Response Time |
|------|------------|----------------------|
| **Enterprise** | 99.99% | < 1 hour (24/7) |
| **Professional** | 99.9% | < 4 hours (business hours) |
| **Standard** | 99.5% | < 24 hours (business hours) |

---

## API Change Log

### 2025-12-04 (Current)
- SEC-081: Documentation rewrite with verified endpoints only
- 484 endpoints across 51 route modules documented
- Added comprehensive security, compliance, and best practices sections

### 2025-12-03
- SEC-066: Unified Metrics Architecture implementation
- Added Executive Brief endpoints
- Added Metric Audit Trail endpoints

### 2025-11-30
- SEC-025: Multi-tenant email system
- Agent Registry endpoints
- Agent Health endpoints

### 2025-11-28
- Enterprise Webhook System (HMAC-SHA256 signed webhooks)
- ServiceNow Integration
- Notification Channels
- Compliance Export System

### 2025-11-26
- SEC-007: Multi-tenant data isolation (CRITICAL)
- Organization filter dependency across all endpoints
- Banking-level security implementation

---

**Document Information:**
- **Document ID:** SEC-081-API-OVERVIEW
- **Version:** 2.0.0
- **Last Updated:** 2025-12-04
- **Verification:** All endpoints verified from source code (routes/*.py)
- **Compliance:** SOC 2, PCI-DSS, HIPAA, GDPR, SOX
