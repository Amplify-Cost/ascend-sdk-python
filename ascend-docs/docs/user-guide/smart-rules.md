---
sidebar_position: 4
title: Smart Rules
description: Create and manage AI-powered governance rules
---

# Smart Rules

The Smart Rules Engine enables AI-assisted creation of governance rules using natural language, with built-in A/B testing and analytics.

## Overview

Create governance rules quickly using natural language descriptions, or build them manually with full control over conditions and actions.

**Source**: `owkai-pilot-frontend/src/components/SmartRuleGen.jsx`

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Rules** | View and manage existing rules |
| **Analytics** | Rule performance metrics |
| **A/B Testing** | Test rule variations |
| **Suggestions** | AI-generated rule recommendations |

## Creating Rules

### Method 1: Natural Language

1. Navigate to Smart Rules
2. Select **Natural Language** creation method
3. Describe your rule in plain English:

```
"Block all database write operations from autonomous agents
during non-business hours and alert the security team"
```

4. Click **Generate Rule**
5. Review the generated rule structure
6. Click **Accept** to create or **Modify** to adjust

### Method 2: Manual Creation

Create rules with full control:

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Rule name | `Block After-Hours PII Access` |
| `condition` | Rule condition | `action_type == 'pii_access' AND time NOT IN business_hours` |
| `action` | What to do | `alert`, `block`, `require_approval` |
| `risk_level` | Severity | `low`, `medium`, `high`, `critical` |
| `description` | Purpose | `Prevents PII access outside office hours` |
| `justification` | Business reason | `GDPR compliance requirement` |

### Rule Actions

| Action | Description |
|--------|-------------|
| `alert` | Generate alert, allow action |
| `block` | Deny action immediately |
| `require_approval` | Send to approval queue |
| `log` | Log only, no intervention |
| `escalate` | Send to security team |

## Rule Conditions

### Condition Syntax

```
field operator value [AND|OR condition]
```

### Available Fields

| Field | Description | Type |
|-------|-------------|------|
| `action_type` | Type of action | string |
| `risk_score` | Calculated risk | number (0-100) |
| `agent_id` | Agent identifier | string |
| `resource` | Target resource | string |
| `time` | Current time | time |
| `day` | Day of week | number (0-6) |
| `environment` | Deployment env | string |
| `user_role` | Actor role | string |

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equals | `action_type == 'database_write'` |
| `!=` | Not equals | `environment != 'production'` |
| `>`, `>=` | Greater than | `risk_score >= 70` |
| `<`, `<=` | Less than | `risk_score < 30` |
| `IN` | In list | `action_type IN ['read', 'query']` |
| `NOT IN` | Not in list | `agent_id NOT IN ['trusted-agent']` |
| `MATCHES` | Regex match | `resource MATCHES '*.pii.*'` |

### Example Rules

**Block High-Risk Deletes:**
```
name: "Block Critical Deletes"
condition: action_type == 'database_delete' AND risk_score >= 80
action: block
risk_level: critical
```

**Require Approval for PII:**
```
name: "PII Approval Required"
condition: resource MATCHES '*.pii.*' OR action_type == 'pii_access'
action: require_approval
risk_level: high
```

**Alert on Autonomous Agent Actions:**
```
name: "Monitor Autonomous Agents"
condition: agent_id MATCHES 'autonomous-*' AND risk_score >= 50
action: alert
risk_level: medium
```

## A/B Testing

Test rule variations to optimize governance:

### Creating an A/B Test

1. Navigate to **A/B Testing** tab
2. Click **Create Test**
3. Configure test:

```javascript
{
  "name": "Risk Threshold Test",
  "description": "Test optimal auto-approve threshold",
  "variant_a": {
    "condition": "risk_score < 25",
    "action": "auto_approve"
  },
  "variant_b": {
    "condition": "risk_score < 35",
    "action": "auto_approve"
  },
  "traffic_split": 50,  // 50% each variant
  "duration_days": 14,
  "success_metric": "false_positive_rate"
}
```

### Test Metrics

| Metric | Description |
|--------|-------------|
| **Trigger Rate** | How often each variant triggers |
| **False Positive Rate** | Incorrectly blocked actions |
| **False Negative Rate** | Incorrectly allowed actions |
| **User Override Rate** | Manual corrections needed |
| **Mean Time to Decision** | Average approval time |

## Rule Analytics

Track rule performance:

### Key Metrics (SEC-057)

| Metric | Description | Source |
|--------|-------------|--------|
| `pattern_recognition_accuracy` | ML model accuracy | Backend API |
| `events_analyzed` | Total events processed | Backend API |
| `threat_patterns_identified` | Detected patterns | Backend API |

### Rule Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Rule: Block After-Hours Access                              │
├─────────────────────────────────────────────────────────────┤
│ Triggers (24h):    47        Blocks:     12                 │
│ Alerts:            35        Approvals:   0                 │
├─────────────────────────────────────────────────────────────┤
│ Trend: ↗ 15% increase from last week                        │
└─────────────────────────────────────────────────────────────┘
```

## AI Suggestions

The system generates rule suggestions based on:

1. **Pattern Analysis**: Detects recurring action patterns
2. **Risk Trends**: Identifies emerging risk areas
3. **Policy Gaps**: Finds unprotected resource types
4. **Best Practices**: Industry-standard recommendations

### Reviewing Suggestions

1. Navigate to **Suggestions** tab
2. Review suggested rules
3. Click **Accept** to create rule
4. Click **Dismiss** to ignore
5. Click **Modify** to customize before creating

## Managing Rules

### Rule States

| State | Description |
|-------|-------------|
| **Active** | Rule is evaluating actions |
| **Inactive** | Rule is disabled |
| **Testing** | Rule in A/B test mode |
| **Draft** | Rule not yet activated |

### Rule Operations

| Action | Description |
|--------|-------------|
| **Edit** | Modify rule conditions |
| **Disable** | Temporarily deactivate |
| **Delete** | Remove rule permanently |
| **Clone** | Create copy for modification |
| **Export** | Download rule as JSON |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/smart-rules` | GET | List all rules |
| `/api/smart-rules` | POST | Create new rule |
| `/api/smart-rules/{id}` | PUT | Update rule |
| `/api/smart-rules/{id}` | DELETE | Delete rule |
| `/api/smart-rules/analytics` | GET | Rule analytics |
| `/api/smart-rules/ab-tests` | GET | A/B tests |
| `/api/smart-rules/suggestions` | GET | AI suggestions |

**Source**: `ow-ai-backend/routes/smart_rules_routes.py`

## Best Practices

1. **Start broad, refine narrow**: Begin with general rules, add specificity
2. **Use A/B testing**: Validate rule effectiveness before full deployment
3. **Review suggestions weekly**: AI catches patterns humans miss
4. **Document justifications**: Future auditors need context
5. **Monitor false positives**: High rates indicate overly strict rules

---

*Source: [SmartRuleGen.jsx](https://github.com/owkai/owkai-pilot-frontend/blob/main/src/components/SmartRuleGen.jsx), [smart_rules_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/smart_rules_routes.py)*
