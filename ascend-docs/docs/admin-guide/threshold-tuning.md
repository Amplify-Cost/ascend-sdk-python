---
sidebar_position: 5
title: Threshold Tuning
description: Configure risk thresholds and agent governance controls
---

# Threshold Tuning

Fine-tune risk thresholds, rate limits, budget controls, and autonomous agent governance for optimal security and operational efficiency.

## Overview

Threshold configuration allows organizations to balance security requirements with operational efficiency by adjusting when actions require approval, when to auto-approve, and when to block.

**Source**: `ow-ai-backend/models_agent_registry.py` (SEC-068)

**Compliance**: SOC 2 CC6.1/CC6.2/CC7.1, NIST AC-3/SI-4, PCI-DSS 7.1

## Risk Thresholds

### Core Threshold Settings

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `default_risk_score` | 50 | 0-100 | Base risk for new actions |
| `auto_approve_below` | 30 | 0-100 | Auto-approve threshold |
| `max_risk_threshold` | 80 | 0-100 | Maximum allowed risk |
| `requires_mfa_above` | 70 | 0-100 | MFA requirement trigger |

### Threshold Flow

```
┌───────────────────────────────────────────────────────────────┐
│                   Risk Score Evaluation                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Risk Score < auto_approve_below (30)                         │
│  └── ✅ AUTO-APPROVE                                          │
│                                                               │
│  Risk Score >= auto_approve_below AND < requires_mfa_above    │
│  └── ⏳ REQUIRE APPROVAL                                      │
│                                                               │
│  Risk Score >= requires_mfa_above (70)                        │
│  └── 🔐 REQUIRE MFA + APPROVAL                               │
│                                                               │
│  Risk Score > max_risk_threshold (80)                         │
│  └── ❌ BLOCK                                                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## Autonomous Agent Thresholds (SEC-068)

### Stricter Defaults for Autonomous Agents

| Setting | Supervised | Autonomous |
|---------|------------|------------|
| `auto_approve_below` | 30 | 20 |
| `max_risk_threshold` | 80 | 60 |
| `require_dual_approval` | false | configurable |

### Autonomous-Specific Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `autonomous_auto_approve_below` | 20 | Lower auto-approve threshold |
| `autonomous_max_risk_threshold` | 60 | Lower maximum risk |
| `autonomous_require_dual_approval` | false | Two approvers required |

## Rate Limiting (SEC-068)

### Rate Limit Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_actions_per_minute` | null | Per-minute limit (null = unlimited) |
| `max_actions_per_hour` | null | Per-hour limit |
| `max_actions_per_day` | null | Per-day limit |

### Example Configuration

```json
{
  "agent_id": "customer-service-agent",
  "max_actions_per_minute": 10,
  "max_actions_per_hour": 100,
  "max_actions_per_day": 500
}
```

### Rate Limit Tracking

| Column | Description |
|--------|-------------|
| `current_minute_count` | Actions in current minute |
| `current_hour_count` | Actions in current hour |
| `current_day_count` | Actions in current day |
| `rate_limit_window_start` | Window tracking timestamp |

## Budget Controls (SEC-068)

### Budget Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `max_daily_budget_usd` | null | Daily spending limit |
| `budget_alert_threshold_percent` | 80 | Alert at percentage |
| `auto_suspend_on_budget_exceeded` | true | Auto-suspend toggle |

### Budget Tracking

| Column | Description |
|--------|-------------|
| `current_daily_spend_usd` | Today's spend |
| `budget_reset_at` | Next reset timestamp |
| `budget_alert_sent` | Alert status flag |

### Budget Flow

```
Daily Budget: $1,000

├── Spend < $800 (80%)
│   └── Normal operation
│
├── Spend >= $800
│   └── Alert sent to admin
│
└── Spend >= $1,000
    └── Auto-suspend agent (if enabled)
```

## Time Window Restrictions (SEC-068)

### Time-Based Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `time_window_enabled` | false | Enable restrictions |
| `time_window_start` | null | Start time (HH:MM) |
| `time_window_end` | null | End time (HH:MM) |
| `time_window_timezone` | UTC | Timezone |
| `time_window_days` | [] | Allowed days (0=Sun, 1=Mon...) |

### Example: Business Hours Only

```json
{
  "time_window_enabled": true,
  "time_window_start": "09:00",
  "time_window_end": "17:00",
  "time_window_timezone": "America/New_York",
  "time_window_days": [1, 2, 3, 4, 5]
}
```

## Data Classification Restrictions (SEC-068)

### Classification Levels

| Classification | Description | Risk Level |
|----------------|-------------|------------|
| `public` | Publicly available | Low |
| `internal` | Internal use only | Low |
| `confidential` | Business sensitive | Medium |
| `pii` | Personal data | High |
| `phi` | Health data | High |
| `pci` | Payment data | Critical |
| `financial` | Financial data | High |
| `secret` | Top secret | Critical |

### Configuration

```json
{
  "allowed_data_classifications": ["public", "internal"],
  "blocked_data_classifications": ["pii", "financial", "secret"]
}
```

## Auto-Suspension Triggers (SEC-068)

### Suspension Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_suspend_enabled` | false | Enable auto-suspend |
| `auto_suspend_on_error_rate` | null | Error rate trigger (0.10 = 10%) |
| `auto_suspend_on_offline_minutes` | null | Offline duration trigger |
| `auto_suspend_on_budget_exceeded` | true | Budget trigger |
| `auto_suspend_on_rate_exceeded` | false | Rate limit trigger |

### Suspension Tracking

| Column | Description |
|--------|-------------|
| `auto_suspended_at` | When suspended |
| `auto_suspend_reason` | Why suspended |

## Anomaly Detection (SEC-068)

### Anomaly Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `anomaly_detection_enabled` | true | Enable detection |
| `anomaly_threshold_percent` | 50.0 | Deviation threshold |

### Baseline Metrics

| Metric | Description |
|--------|-------------|
| `baseline_actions_per_hour` | Normal action rate |
| `baseline_error_rate` | Normal error rate |
| `baseline_avg_risk_score` | Normal risk score |

### Anomaly Tracking

| Column | Description |
|--------|-------------|
| `last_anomaly_check` | Last check timestamp |
| `last_anomaly_detected` | Last anomaly timestamp |
| `anomaly_count_24h` | 24-hour anomaly count |

## Escalation Paths (CR-003)

### Autonomous Escalation

| Setting | Description |
|---------|-------------|
| `autonomous_escalation_webhook_url` | Webhook for high-risk alerts |
| `autonomous_escalation_email` | Fallback email |
| `autonomous_allow_queued_approval` | Queue for human review |

### Example Configuration

```json
{
  "autonomous_escalation_webhook_url": "https://hooks.slack.com/...",
  "autonomous_escalation_email": "security@company.com",
  "autonomous_allow_queued_approval": true
}
```

## Concurrent Action Limits (SEC-068)

| Setting | Default | Description |
|---------|---------|-------------|
| `max_concurrent_actions` | null | Concurrent limit |
| `current_concurrent_actions` | 0 | Current count |
| `max_session_duration_minutes` | null | Session timeout |

## Tuning Recommendations

### Conservative (High Security)

```json
{
  "auto_approve_below": 15,
  "max_risk_threshold": 60,
  "requires_mfa_above": 50,
  "auto_suspend_enabled": true,
  "anomaly_detection_enabled": true,
  "anomaly_threshold_percent": 30.0
}
```

### Balanced (Standard Operations)

```json
{
  "auto_approve_below": 30,
  "max_risk_threshold": 80,
  "requires_mfa_above": 70,
  "auto_suspend_enabled": false,
  "anomaly_detection_enabled": true,
  "anomaly_threshold_percent": 50.0
}
```

### Permissive (High Throughput)

```json
{
  "auto_approve_below": 50,
  "max_risk_threshold": 90,
  "requires_mfa_above": 85,
  "auto_suspend_enabled": false,
  "anomaly_detection_enabled": false
}
```

## Best Practices

1. **Start conservative**: Begin with strict thresholds, relax gradually
2. **Monitor false positives**: High block rates indicate thresholds too strict
3. **Enable anomaly detection**: Catch unusual patterns early
4. **Set budget limits**: Always configure budget controls
5. **Document changes**: Track threshold modifications in change log
6. **Review regularly**: Audit thresholds quarterly

## Troubleshooting

### Too many actions blocked

**Cause**: `max_risk_threshold` too low.

**Solution**: Gradually increase threshold; monitor for legitimate blocks.

### Too many approval requests

**Cause**: `auto_approve_below` too low.

**Solution**: Analyze approved requests; increase threshold for low-risk patterns.

### Agent frequently suspended

**Cause**: Auto-suspend triggers too sensitive.

**Solution**: Increase `auto_suspend_on_error_rate` or disable non-critical triggers.

---

*Source: [models_agent_registry.py](https://github.com/owkai/ow-ai-backend/blob/main/models_agent_registry.py)*
