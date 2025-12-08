---
sidebar_position: 2
title: Risk Levels
description: Risk scoring and threshold configuration
---

# Risk Levels Reference

Ascend uses a comprehensive risk scoring system that combines CVSS 3.1 scoring with contextual analysis for accurate risk assessment.

## Risk Level Overview

| Level | Score Range | CVSS Range | Color | Response |
|-------|-------------|------------|-------|----------|
| Low | 0 - 39 | 0.1 - 3.9 | Green | Auto-approve |
| Medium | 40 - 69 | 4.0 - 6.9 | Yellow | Monitor |
| High | 70 - 89 | 7.0 - 8.9 | Orange | Alert + Review |
| Critical | 90 - 100 | 9.0 - 10.0 | Red | Block + Alert |

---

## Risk Score Calculation

### Formula

```
Risk Score = (CVSS Base × 10) + Context Modifiers + Agent Modifiers

Maximum: 100
Minimum: 0
```

### CVSS 3.1 Base Score

The foundation of risk scoring is CVSS 3.1:

| Metric | Values | Impact |
|--------|--------|--------|
| Attack Vector (AV) | Network, Adjacent, Local, Physical | Reach of attack |
| Attack Complexity (AC) | Low, High | Difficulty to exploit |
| Privileges Required (PR) | None, Low, High | Access needed |
| User Interaction (UI) | None, Required | Human involvement |
| Scope (S) | Unchanged, Changed | Impact boundaries |
| Confidentiality (C) | None, Low, High | Data exposure |
| Integrity (I) | None, Low, High | Data modification |
| Availability (A) | None, Low, High | Service disruption |

### CVSS Score Ranges

| Severity | Score | Example Actions |
|----------|-------|-----------------|
| None | 0.0 | No impact actions |
| Low | 0.1 - 3.9 | database_read, api_call |
| Medium | 4.0 - 6.9 | database_write, email_send |
| High | 7.0 - 8.9 | data_export, phi_access |
| Critical | 9.0 - 10.0 | credential_access, shell_execute |

---

## Context Modifiers

Context modifiers adjust risk based on operational factors:

### Time-Based Modifiers

| Context | Modifier | Description |
|---------|----------|-------------|
| Business Hours | +0 | Standard operating hours |
| After Hours | +10 | Outside 9am-5pm |
| Weekend | +10 | Saturday/Sunday |
| Holiday | +15 | Company holidays |

### Data Sensitivity Modifiers

| Data Type | Modifier | Description |
|-----------|----------|-------------|
| Public | +0 | Non-sensitive data |
| Internal | +5 | Internal use only |
| Confidential | +10 | Business sensitive |
| PII | +15 | Personal information |
| PHI | +20 | Health information |
| PCI | +20 | Payment card data |

### Target Modifiers

| Target | Modifier | Description |
|--------|----------|-------------|
| Internal System | +0 | Organization systems |
| External API | +10 | Third-party services |
| Production DB | +10 | Production database |
| Admin System | +15 | Administrative systems |

### Volume Modifiers

| Volume | Modifier | Description |
|--------|----------|-------------|
| Single Record | +0 | One record affected |
| Batch (10-100) | +5 | Multiple records |
| Bulk (100-1000) | +10 | Large batch |
| Mass (1000+) | +15 | Mass operation |

---

## Agent Type Modifiers

Different agent types have different risk profiles:

### Agent Type Thresholds

| Agent Type | Auto-Approve Below | Max Risk | MFA Above | Description |
|------------|-------------------|----------|-----------|-------------|
| Supervised | 30 | 80 | 70 | Human oversight |
| Autonomous | 20 | 60 | 50 | Independent operation |
| Advisory | 50 | 90 | 80 | Recommendations only |
| MCP Server | 30 | 80 | 70 | MCP protocol |

### Agent Risk Calculation

```json
{
  "agent_id": "customer-service-agent",
  "agent_type": "supervised",
  "risk_config": {
    "auto_approve_below": 30,
    "max_risk_threshold": 80,
    "requires_mfa_above": 70,
    "default_risk_score": 50
  },
  "thresholds_applied": {
    "base_cvss": 5.0,
    "context_modifier": 15,
    "final_risk_score": 65,
    "risk_level": "medium",
    "decision": "requires_review"
  }
}
```

---

## Threshold Configuration

### Organization-Level Configuration

```bash
# Configure organization risk thresholds
curl -X PUT "https://pilot.owkai.app/api/authorization/thresholds" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_approve_threshold": 30,
    "review_threshold": 50,
    "alert_threshold": 70,
    "block_threshold": 90,
    "mfa_threshold": 70
  }'
```

### Agent-Level Configuration

```bash
# Configure agent-specific thresholds
curl -X PUT "https://pilot.owkai.app/api/registry/agents/my-agent/thresholds" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_approve_below": 25,
    "max_risk_threshold": 70,
    "requires_mfa_above": 60
  }'
```

---

## Decision Logic

### Status Determination (SEC-106)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Action Submitted                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐                                            │
│  │ Policy Denies?  │──Yes──► DENIED                             │
│  └────────┬────────┘                                            │
│           │ No                                                   │
│           ▼                                                      │
│  ┌─────────────────────────┐                                    │
│  │ Risk < auto_approve?    │──Yes──► APPROVED (auto)            │
│  └────────┬────────────────┘                                    │
│           │ No                                                   │
│           ▼                                                      │
│  ┌─────────────────────────┐                                    │
│  │ Risk >= max_threshold?  │──Yes──► PENDING_APPROVAL           │
│  └────────┬────────────────┘                                    │
│           │ No                                                   │
│           ▼                                                      │
│  ┌─────────────────────────┐                                    │
│  │ Policy requires approval?│──Yes──► PENDING_APPROVAL          │
│  └────────┬────────────────┘                                    │
│           │ No                                                   │
│           ▼                                                      │
│       APPROVED                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Response by Risk Level

| Risk Level | Auto-Approve | Alert | Human Review | Block |
|------------|--------------|-------|--------------|-------|
| Low | Yes | No | No | No |
| Medium | Conditional | Optional | Optional | No |
| High | No | Yes | Yes | No |
| Critical | No | Yes | Yes | Yes |

---

## Risk Scoring Examples

### Example 1: Low Risk Read

```json
{
  "action_type": "database_read",
  "cvss_base": 2.5,
  "context": {
    "time": "business_hours",
    "data_type": "internal",
    "target": "internal_system",
    "volume": "single_record"
  },
  "calculation": {
    "cvss_component": 25,
    "time_modifier": 0,
    "data_modifier": 5,
    "target_modifier": 0,
    "volume_modifier": 0,
    "total": 30
  },
  "result": {
    "risk_score": 30,
    "risk_level": "low",
    "status": "approved"
  }
}
```

### Example 2: High Risk Export

```json
{
  "action_type": "data_export",
  "cvss_base": 7.5,
  "context": {
    "time": "after_hours",
    "data_type": "pii",
    "target": "external_api",
    "volume": "bulk"
  },
  "calculation": {
    "cvss_component": 75,
    "time_modifier": 10,
    "data_modifier": 15,
    "target_modifier": 10,
    "volume_modifier": 10,
    "total": 100,
    "capped": 100
  },
  "result": {
    "risk_score": 100,
    "risk_level": "critical",
    "status": "pending_approval",
    "alert_triggered": true
  }
}
```

### Example 3: Medium Risk Write

```json
{
  "action_type": "database_write",
  "cvss_base": 5.0,
  "context": {
    "time": "business_hours",
    "data_type": "internal",
    "target": "production_db",
    "volume": "single_record"
  },
  "calculation": {
    "cvss_component": 50,
    "time_modifier": 0,
    "data_modifier": 5,
    "target_modifier": 10,
    "volume_modifier": 0,
    "total": 65
  },
  "result": {
    "risk_score": 65,
    "risk_level": "medium",
    "status": "approved"
  }
}
```

---

## Risk Trending

### Risk Metrics Over Time

```json
{
  "risk_trends": {
    "period": "30_days",
    "metrics": {
      "average_risk_score": 42.5,
      "high_risk_actions": 23,
      "critical_actions_blocked": 5,
      "auto_approved_percentage": 68.5
    },
    "trend": {
      "direction": "improving",
      "change": "-8.2%",
      "insight": "Risk profile improving due to policy refinements"
    }
  }
}
```

### Risk Distribution

| Range | Count | Percentage |
|-------|-------|------------|
| 0-19 | 1,245 | 35.2% |
| 20-39 | 1,178 | 33.3% |
| 40-59 | 687 | 19.4% |
| 60-79 | 312 | 8.8% |
| 80-100 | 118 | 3.3% |

---

## Custom Risk Profiles

### Create Custom Profile

```bash
# Create custom risk profile
curl -X POST "https://pilot.owkai.app/api/authorization/risk-profiles" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_name": "high_security",
    "description": "Strict risk profile for sensitive operations",
    "thresholds": {
      "auto_approve_below": 15,
      "review_threshold": 30,
      "alert_threshold": 50,
      "block_threshold": 75
    },
    "context_multipliers": {
      "after_hours": 1.5,
      "pii_data": 1.5,
      "external_target": 1.3
    }
  }'
```

### Apply Profile to Agent

```bash
# Apply risk profile to agent
curl -X PUT "https://pilot.owkai.app/api/registry/agents/my-agent/risk-profile" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "risk_profile": "high_security"
  }'
```

---

## Alert Thresholds

### Alert Configuration

| Threshold | Default | Description |
|-----------|---------|-------------|
| Info | 40 | Informational notification |
| Warning | 60 | Warning alert |
| Alert | 75 | Standard alert |
| Critical | 90 | Critical alert (immediate) |

### Alert Delivery

```json
{
  "alert_config": {
    "email_notifications": true,
    "slack_integration": true,
    "pagerduty_integration": false,
    "webhook_url": "https://hooks.example.com/alerts",
    "escalation_path": [
      {"threshold": 75, "notify": ["security-team@company.com"]},
      {"threshold": 90, "notify": ["ciso@company.com"], "pagerduty": true}
    ]
  }
}
```

---

*For risk configuration questions, contact support@owkai.app*
