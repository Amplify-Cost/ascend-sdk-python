---
sidebar_position: 4
title: Policy Configuration
description: Configure agent policies and governance rules
---

# Policy Configuration

Define fine-grained access control policies for AI agents with condition-based rules, escalation paths, and compliance enforcement.

## Overview

Agent policies enable organizations to enforce governance rules at the agent level, controlling what actions agents can perform and under what conditions.

**Source**: `ow-ai-backend/models_agent_registry.py`

**Compliance**: NIST AC-3, PCI-DSS 7.1, HIPAA 164.312(a)

## Policy Structure

### AgentPolicy Model

| Field | Type | Description |
|-------|------|-------------|
| `policy_name` | String | Human-readable name |
| `policy_description` | Text | Purpose description |
| `is_active` | Boolean | Enabled status |
| `priority` | Integer | Evaluation order (lower = higher) |
| `conditions` | JSONB | When policy applies |
| `policy_action` | String | What happens |
| `action_params` | JSONB | Action configuration |

### Policy Actions

| Action | Description | Use Case |
|--------|-------------|----------|
| `allow` | Permit the action | Low-risk operations |
| `block` | Deny the action | Prohibited operations |
| `require_approval` | Queue for human review | Medium-risk operations |
| `escalate` | Send to security team | High-risk operations |

## Creating Policies

### Example: Block High-Risk Transactions

```json
{
  "policy_name": "Block High-Risk Transactions",
  "policy_description": "Prevent autonomous agents from processing high-value transactions",
  "is_active": true,
  "priority": 10,
  "conditions": {
    "action_type": "transaction",
    "risk_above": 70,
    "agent_type": "autonomous"
  },
  "policy_action": "block",
  "action_params": {
    "notification": "security-team@company.com",
    "audit_level": "critical"
  }
}
```

### Example: Require Approval for PII Access

```json
{
  "policy_name": "PII Access Approval",
  "policy_description": "Require human approval for any PII data access",
  "is_active": true,
  "priority": 20,
  "conditions": {
    "resource_type": "pii",
    "action_type": ["read", "write", "delete"]
  },
  "policy_action": "require_approval",
  "action_params": {
    "approvers": ["compliance-team"],
    "timeout_hours": 24,
    "escalate_on_timeout": true
  }
}
```

### Example: Escalate Database Deletes

```json
{
  "policy_name": "Database Delete Escalation",
  "policy_description": "Escalate all database delete operations",
  "is_active": true,
  "priority": 5,
  "conditions": {
    "action_type": "database_delete"
  },
  "policy_action": "escalate",
  "action_params": {
    "escalate_to": "security-team",
    "notification_channel": "slack",
    "webhook_url": "https://hooks.slack.com/..."
  }
}
```

## Condition Syntax

### Available Condition Fields

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | string/array | Action type filter |
| `agent_type` | string | Agent classification |
| `risk_above` | integer | Minimum risk score |
| `risk_below` | integer | Maximum risk score |
| `resource_type` | string | Target resource type |
| `time_window` | object | Time-based restrictions |
| `data_classification` | string/array | Data sensitivity |

### Condition Operators

| Operator | Description | Example |
|----------|-------------|---------|
| Direct value | Exact match | `"action_type": "transaction"` |
| Array | Any match | `"action_type": ["read", "write"]` |
| Range | Numeric comparison | `"risk_above": 70` |
| Object | Complex condition | `"time_window": {"outside": "09:00-17:00"}` |

## Policy Priority

Policies evaluated in priority order (lower number = higher priority):

```
Priority 1:  Block Critical Actions
Priority 10: Require Dual Approval
Priority 20: Standard Approval
Priority 100: Default Allow
```

### Priority Guidelines

| Priority Range | Use Case |
|----------------|----------|
| 1-10 | Critical security blocks |
| 11-50 | High-priority restrictions |
| 51-100 | Standard governance |
| 101-500 | Organizational rules |
| 501+ | Default/fallback policies |

## Action Parameters

### Block Action Params

```json
{
  "notification": "security@company.com",
  "audit_level": "critical",
  "log_reason": true,
  "alert_on_repeated": true
}
```

### Require Approval Params

```json
{
  "approvers": ["team-leads", "security"],
  "timeout_hours": 24,
  "escalate_on_timeout": true,
  "require_justification": true,
  "min_approvers": 1
}
```

### Escalate Params

```json
{
  "escalate_to": "security-team",
  "notification_channel": "slack",
  "webhook_url": "https://...",
  "include_context": true,
  "severity": "high"
}
```

## Agent-Level Policies

### Per-Agent Configuration

Each registered agent can have specific policies:

```json
{
  "agent_id": "financial-advisor-001",
  "policies": [
    {
      "policy_name": "Transaction Limit",
      "conditions": {
        "action_type": "transaction",
        "amount_above": 10000
      },
      "policy_action": "require_approval"
    }
  ]
}
```

### Agent Policy Inheritance

1. Global organization policies (highest priority)
2. Agent-type policies
3. Agent-specific policies
4. Default allow (lowest priority)

## Compliance Mapping

### NIST AC-3 (Access Enforcement)

| Control | Implementation |
|---------|----------------|
| AC-3(1) | Role-based policy assignment |
| AC-3(2) | Dual authorization support |
| AC-3(3) | Mandatory access control |

### PCI-DSS 7.1 (Restrict Access)

| Requirement | Implementation |
|-------------|----------------|
| 7.1.1 | Policy-based access restrictions |
| 7.1.2 | Least privilege enforcement |
| 7.1.3 | Role-based permissions |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/governance/policies` | GET | List all policies |
| `/api/governance/policies` | POST | Create policy |
| `/api/governance/policies/{id}` | PUT | Update policy |
| `/api/governance/policies/{id}` | DELETE | Delete policy |
| `/api/governance/policies/evaluate` | POST | Test policy |

## Best Practices

1. **Start restrictive**: Begin with block/require_approval, relax as needed
2. **Use meaningful names**: Policy names should explain purpose
3. **Document conditions**: Add descriptions for complex conditions
4. **Test before deploy**: Use evaluate endpoint to test policies
5. **Regular review**: Audit policies quarterly for relevance
6. **Version policies**: Use policy_description for change notes

## Troubleshooting

### Policy not triggering

**Check**:
- Is policy `is_active: true`?
- Do conditions match the action?
- Is priority correct (not overridden)?

### Actions being blocked unexpectedly

**Solution**: Check higher-priority policies; use evaluate endpoint.

### Multiple policies conflicting

**Solution**: Review priority order; first matching policy wins.

---

*Source: [models_agent_registry.py](https://github.com/owkai/ow-ai-backend/blob/main/models_agent_registry.py)*
