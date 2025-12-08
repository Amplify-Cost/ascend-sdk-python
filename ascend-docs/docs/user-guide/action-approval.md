---
sidebar_position: 3
title: Action Approval
description: Review and approve pending agent actions
---

# Action Approval

The Action Approval dashboard enables human-in-the-loop oversight for AI agent actions, providing approval workflows, policy enforcement, and automation playbooks.

## Overview

When an agent action exceeds risk thresholds or triggers a policy, it enters the approval queue for human review.

**Source**: `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Pending** | Actions awaiting approval |
| **Workflows** | Approval workflow configuration |
| **Policies** | Governance policies |
| **Automation** | Automation playbooks |
| **Execution** | Execution history |

## Pending Actions Queue

### Queue Filters

| Filter | Options |
|--------|---------|
| **Source** | All, Agent, MCP, High Risk |
| **Status** | Pending, Approved, Rejected |
| **Risk Level** | Low, Medium, High, Critical |

### Action Card Information

Each pending action displays:

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 database_write                              Risk: 75/100 │
├─────────────────────────────────────────────────────────────┤
│ Agent: financial-advisor-001                                │
│ Resource: production_db.customers                           │
│ Description: Update customer profile                        │
├─────────────────────────────────────────────────────────────┤
│ NIST: AC-3     MITRE: T1003     CVSS: 6.5                  │
├─────────────────────────────────────────────────────────────┤
│ [✓ Approve]  [✗ Deny]  [📋 Details]                        │
└─────────────────────────────────────────────────────────────┘
```

## Approval Actions

### Approve Action

1. Review action details and risk score
2. Click **Approve**
3. Add optional comment
4. Confirm approval

**Audit Trail**: Records approver, timestamp, and justification.

### Deny Action

1. Review action details
2. Click **Deny**
3. Provide reason (required)
4. Confirm denial

**Agent Notification**: Agent receives denial reason via webhook.

### Emergency Override

For time-sensitive situations:

1. Click **Emergency Override**
2. Provide detailed justification (required)
3. Select override type:
   - **Expedited Approval**: Skip additional approvers
   - **Risk Acknowledgment**: Approve despite high risk

**Security Alert**: Emergency overrides trigger security team notification.

## Approval Workflows

Configure multi-level approval chains:

### Workflow Structure

```javascript
{
  "name": "High-Value Transaction Approval",
  "description": "Multi-level approval for transactions over $10,000",
  "steps": [
    { "level": 1, "role": "team_lead", "timeout_hours": 4 },
    { "level": 2, "role": "manager", "timeout_hours": 8 },
    { "level": 3, "role": "director", "timeout_hours": 24 }
  ],
  "triggers": [
    { "field": "risk_score", "operator": ">=", "value": 70 },
    { "field": "action_type", "operator": "in", "value": ["funds_transfer"] }
  ],
  "approvers": ["team-leads", "finance-managers"]
}
```

### Workflow Triggers

| Trigger | Description | Example |
|---------|-------------|---------|
| `risk_score` | Risk threshold | `>= 70` |
| `action_type` | Specific actions | `database_delete` |
| `resource` | Resource patterns | `*.pii` |
| `agent_id` | Specific agents | `autonomous-*` |

## Automation Playbooks

Automate routine approval decisions:

### Playbook Configuration

```javascript
{
  "id": "auto-approve-low-risk",
  "name": "Auto-Approve Low Risk Reads",
  "status": "active",
  "risk_level": "low",
  "approval_required": false,
  "trigger_conditions": {
    "risk_score": { "min": 0, "max": 30 },
    "action_type": ["database_read", "api_read"],
    "environment": ["development", "staging"],
    "business_hours": true
  },
  "actions": [
    { "type": "auto_approve", "delay_seconds": 0 },
    { "type": "log", "message": "Auto-approved low-risk read" }
  ]
}
```

### Playbook Features

| Feature | Description |
|---------|-------------|
| **Template Library** | Pre-built playbook templates |
| **Dry-Run Testing** | Test playbooks before activation |
| **Version History** | Track playbook changes |
| **Analytics Dashboard** | Monitor playbook performance |

### Playbook Actions

| Action Type | Description |
|-------------|-------------|
| `auto_approve` | Automatically approve |
| `auto_deny` | Automatically deny |
| `escalate` | Send to next approval level |
| `notify` | Send notification |
| `log` | Add audit log entry |
| `webhook` | Call external webhook |

## Policy Enforcement

The Enhanced Policy Tab provides governance policy management:

### Policy Structure

```javascript
{
  "policy_name": "Block PII Access After Hours",
  "description": "Deny PII access outside business hours",
  "effect": "DENY",
  "conditions": {
    "resource_type": "pii",
    "time": { "outside": "09:00-17:00" }
  },
  "priority": 100
}
```

### Policy Decision Badge

Actions display policy evaluation results:

| Badge | Meaning |
|-------|---------|
| ✅ **ALLOW** | Policy permits action |
| ❌ **DENY** | Policy blocks action |
| ⏳ **REQUIRE_APPROVAL** | Needs human review |
| ⚠️ **CONFLICT** | Multiple policies conflict |

## Execution History

Track all approval decisions:

| Field | Description |
|-------|-------------|
| Action ID | Unique action identifier |
| Decision | Approved/Denied/Auto-approved |
| Approver | Who made the decision |
| Timestamp | When decision was made |
| Duration | Time from submission to decision |
| Playbook | Automation playbook used (if any) |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/authorization/pending` | GET | Get pending actions |
| `/api/authorization/approve/{id}` | POST | Approve action |
| `/api/authorization/deny/{id}` | POST | Deny action |
| `/api/authorization/workflows` | GET | List workflows |
| `/api/automation/playbooks` | GET | List playbooks |

**Source**: `ow-ai-backend/routes/authorization_routes.py`

## Best Practices

1. **Set SLAs**: Configure approval timeouts to prevent queue buildup
2. **Use playbooks**: Automate repetitive low-risk approvals
3. **Review denials**: Monitor denial patterns to improve policies
4. **Escalate promptly**: Don't let critical actions wait
5. **Document decisions**: Always add context to approvals/denials

## Troubleshooting

### Queue not refreshing

**Solution**: Check WebSocket connection; refresh page if needed.

### Playbook not triggering

**Solution**: Verify trigger conditions match action attributes exactly.

### Approval timeout

**Solution**: Check email notifications; escalate to backup approver.

---

*Source: [AgentAuthorizationDashboard.jsx](https://github.com/owkai/owkai-pilot-frontend/blob/main/src/components/AgentAuthorizationDashboard.jsx), [authorization_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/authorization_routes.py)*
