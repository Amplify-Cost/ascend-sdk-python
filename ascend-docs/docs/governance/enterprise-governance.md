---
sidebar_position: 1
title: Enterprise Governance Architecture
description: Complete guide to Ascend's enterprise AI governance features for circuit breakers, anomaly detection, and policy management
---

# Enterprise Governance Architecture

Ascend provides banking-level governance for AI agents and MCP servers. This guide covers the enterprise features that enable organizations to maintain full control over autonomous AI systems.

## Overview

Ascend's governance architecture is built on four pillars:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASCEND ENTERPRISE GOVERNANCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Circuit Breaker │  │ Anomaly Detection│  │ Policy Resolver  │          │
│  │                  │  │                  │  │                  │          │
│  │  Auto-disable    │  │  Z-score based   │  │  Priority-based  │          │
│  │  failing servers │  │  behavior alerts │  │  conflict detect │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           └─────────────────────┼─────────────────────┘                     │
│                                 │                                           │
│                      ┌──────────▼──────────┐                               │
│                      │  Session Lifecycle  │                               │
│                      │  Auto-expiration    │                               │
│                      │  Renewal tracking   │                               │
│                      └─────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Circuit Breaker Pattern

The circuit breaker automatically detects and isolates failing MCP servers to prevent cascade failures across your AI infrastructure.

### States

| State | Description | Request Behavior |
|-------|-------------|------------------|
| **CLOSED** | Normal operation | Requests pass through |
| **OPEN** | Failures exceeded threshold | Requests blocked immediately |
| **HALF_OPEN** | Recovery testing | Limited probe requests allowed |

### State Transitions

```
┌─────────┐  failure_threshold  ┌─────────┐  timeout  ┌───────────┐
│ CLOSED  │ ─────────────────→  │  OPEN   │ ────────→ │ HALF_OPEN │
│(healthy)│                     │(blocked)│           │ (testing) │
└────┬────┘ ←───────────────────└─────────┘ ←──────── └─────┬─────┘
     │         recovery                       failure        │
     └───────────────────────────────────────────────────────┘
                             success
```

### Configuration

Configure circuit breaker thresholds per MCP server via the [Ascend Dashboard](https://pilot.owkai.app) or API:

```json
{
    "server_id": "mcp-production-001",
    "circuit_failure_threshold": 5,
    "circuit_recovery_timeout_seconds": 300,
    "circuit_required_successes": 2
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/governance/circuits` | GET | Get all circuit states |
| `/api/governance/circuits/{server_id}` | GET | Get specific circuit status |
| `/api/governance/circuits/{server_id}/reset` | POST | Force close circuit (admin) |
| `/api/governance/circuits/{server_id}/trip` | POST | Force open circuit (emergency) |

[Learn more about SDK integration →](/sdk/governance-integration)

---

## Anomaly Detection

Real-time statistical analysis of agent behavior to detect unusual patterns that may indicate security threats or misconfigurations.

### Algorithm

Ascend uses Z-score based anomaly detection:

```
z = (current_value - baseline_mean) / standard_deviation

If |z| > threshold → ANOMALY DETECTED
```

### Monitored Metrics

| Metric | Description | Typical Baseline |
|--------|-------------|------------------|
| **Actions/Hour** | Request frequency | Varies by agent |
| **Error Rate** | Failed action percentage | < 5% |
| **Risk Score** | Average risk of actions | Varies by policy |

### Severity Levels

| Z-Score Range | Severity | Action |
|---------------|----------|--------|
| 2.0 - 3.0 | LOW | Log only |
| 3.0 - 4.0 | MEDIUM | Alert sent |
| 4.0 - 5.0 | HIGH | Escalation triggered |
| > 5.0 | CRITICAL | Auto-suspension (if enabled) |

### Configuration

```json
{
    "agent_id": "agent-001",
    "anomaly_detection_enabled": true,
    "anomaly_sensitivity": 2.0,
    "anomaly_auto_suspend": false,
    "anomaly_escalation_threshold": 3,
    "baseline_window_hours": 168
}
```

[Configure anomaly detection in the Dashboard →](https://pilot.owkai.app)

---

## Policy Conflict Resolution

Automatically detects and resolves conflicts between overlapping governance policies.

### Conflict Types

| Type | Description | Severity |
|------|-------------|----------|
| **PRIORITY_TIE** | Same priority on overlapping scope | HIGH |
| **EFFECT_CONTRADICTION** | ALLOW vs DENY on same resource | CRITICAL |
| **RESOURCE_OVERLAP** | Ambiguous resource patterns | MEDIUM |

### Resolution Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `MOST_RESTRICTIVE` | DENY always wins | Security-first (default) |
| `MOST_PERMISSIVE` | ALLOW wins unless explicit DENY | Availability-first |
| `HIGHEST_PRIORITY` | Lower number = higher priority | Explicit ordering |
| `FIRST_MATCH` | First matching policy wins | Cedar-style evaluation |

### Best Practice: Priority Assignment

```
1-99:    System policies (reserved)
100-199: Security policies
200-299: Compliance policies
300-399: Business policies
400+:    Custom policies
```

---

## Session Lifecycle Management

Automatic management of MCP sessions with configurable expiration and renewal.

### Session States

| Status | Description |
|--------|-------------|
| `ACTIVE` | Session is operational |
| `EXPIRED` | Past expiration time |
| `TERMINATED` | Manually ended |

### Auto-Renewal

Sessions can be configured for automatic renewal:

```json
{
    "session_id": "sess-abc123",
    "auto_renewal_enabled": true,
    "max_renewals": 5,
    "renewal_count": 2
}
```

### Cleanup Schedule

| Job | Frequency | Purpose |
|-----|-----------|---------|
| Session Cleanup | Every 15 minutes | Mark expired sessions |
| Renewal Check | Every 5 minutes | Renew eligible sessions |
| Old Session Delete | Weekly (Sunday 3 AM UTC) | Data minimization |

### Recommended Session Duration

| Agent Type | Recommended Duration |
|------------|---------------------|
| Autonomous | 1 hour max |
| Supervised | 8 hours |
| Advisory | 24 hours |

---

## Compliance Mapping

| Feature | SOC 2 | PCI-DSS | NIST | GDPR |
|---------|-------|---------|------|------|
| Circuit Breaker | CC7.1 | 6.5.5 | SI-4 | — |
| Anomaly Detection | CC7.1 | 10.6 | SI-4 | — |
| Policy Resolver | CC6.1 | 7.1 | AC-3 | — |
| Session Cleanup | CC6.1 | — | IA-4 | Art. 5 |

[Learn more about Ascend compliance →](/security/compliance)

---

## SIEM Integration

### Datadog

```yaml
# Metrics exported to Datadog
ascend.circuit_breaker.state
ascend.circuit_breaker.failure_count
ascend.anomaly.detection_count
ascend.session.active_count
ascend.policy.conflict_count
```

### Splunk

```
# Splunk CIM compatible events
index=ascend sourcetype=circuit_breaker
| stats count by server_id, state

index=ascend sourcetype=anomaly_detection
| where severity="critical"
```

[Configure SIEM integration →](/enterprise/siem)

---

## Monitoring & Alerts

### Recommended Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Circuit Open | Any MCP server circuit opens | HIGH |
| Anomaly Streak | 3+ consecutive anomalies | HIGH |
| Policy Conflict | Critical conflict detected | CRITICAL |
| Session Spike | 50% increase in active sessions | MEDIUM |

---

## Next Steps

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>SDK Integration</h3>
      </div>
      <div className="card__body">
        <p>Learn how to integrate governance features into your agents.</p>
      </div>
      <div className="card__footer">
        <a className="button button--primary button--block" href="/sdk/governance-integration">View SDK Guide</a>
      </div>
    </div>
  </div>
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>SIEM Integration</h3>
      </div>
      <div className="card__body">
        <p>Export governance events to Splunk, Datadog, or Elastic.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/enterprise/siem">Configure SIEM</a>
      </div>
    </div>
  </div>
</div>

## Get Help

- **Documentation**: You're here!
- **Dashboard**: [pilot.owkai.app](https://pilot.owkai.app)
- **Support**: [support@ascendowkai.com](mailto:support@ascendowkai.com)
- **Status**: [status.ascendowkai.com](https://status.ascendowkai.com)
