# Ascend Governance Controls Configuration Guide

**Document ID:** ASCEND-GOVERNANCE-CONTROLS-001
**Version:** 1.0.0
**Author:** Ascend Engineering Team
**Publisher:** OW-kai Technologies Inc.
**Classification:** Enterprise Client Documentation
**Last Updated:** December 2025
**Compliance:** SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4

---

## Overview

Governance Controls provide enterprise-grade safeguards for autonomous AI agents operating within your organization. These controls ensure that AI agents operate within defined boundaries, protecting your business from runaway costs, unauthorized data access, and operational disruptions.

This guide covers configuration of all governance controls available in the Ascend platform, with step-by-step instructions for each feature.

---

## Why Governance Controls Matter

When deploying autonomous AI agents in enterprise environments, organizations face several risks:

| Risk Category | Business Impact | Governance Solution |
|---------------|-----------------|---------------------|
| Runaway Operations | Agent executes thousands of unintended actions | Rate Limiting |
| Cost Overruns | Unexpected API/compute costs | Budget Controls |
| Compliance Violations | Operations outside approved hours | Time Window Enforcement |
| Data Breaches | Unauthorized access to sensitive data | Data Classification Controls |
| System Instability | Agent errors cascading through systems | Auto-Suspension Rules |
| Incident Response Delays | No notification of critical events | Escalation Configuration |

Ascend Governance Controls address each of these risks with configurable, auditable safeguards.

---

## Accessing Governance Controls

### Via the Ascend Dashboard

1. Navigate to **Agent Registry** in the sidebar
2. Select an agent from the list
3. Click the **Governance** tab
4. Configure controls as needed
5. Click **Save Configuration**

### Via API

All governance controls can be configured programmatically:

```bash
# Set rate limits for an agent
curl -X PATCH https://pilot.owkai.app/api/agent-registry/{agent_id}/governance \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "max_actions_per_minute": 100,
    "max_actions_per_hour": 1000,
    "max_actions_per_day": 10000
  }'
```

---

## Rate Limiting

### What It Does

Rate limiting prevents agents from executing too many actions within a given time window. This protects against:

- Infinite loops in agent logic
- Denial-of-service conditions
- Excessive API consumption
- Uncontrolled automation

### Configuration Options

| Setting | Description | Recommended Range |
|---------|-------------|-------------------|
| Actions per Minute | Maximum actions allowed per minute | 10-1000 |
| Actions per Hour | Maximum actions allowed per hour | 100-10000 |
| Actions per Day | Maximum actions allowed per day | 1000-100000 |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Rate Limits" section (marked with SOC 2 CC6.2 badge)

**Step 3:** Enter your desired limits:

```
Actions per Minute: 100
Actions per Hour: 1000
Actions per Day: 10000
```

**Step 4:** Click "Save Configuration"

### What Happens When Limits Are Exceeded

When an agent exceeds a rate limit:

1. The action request returns a `429 Too Many Requests` response
2. The response includes `retry_after` indicating when to retry
3. An alert is logged in the audit trail
4. If configured, auto-suspension triggers

### Example Response

```json
{
  "approved": false,
  "reason": "Rate limit exceeded: 100 actions per minute",
  "retry_after": 45,
  "rate_limit_status": {
    "minute": {"used": 100, "limit": 100, "resets_in": 45},
    "hour": {"used": 523, "limit": 1000, "resets_in": 1847},
    "day": {"used": 4521, "limit": 10000, "resets_in": 52341}
  }
}
```

### Compliance Mapping

- **SOC 2 CC6.2**: Logical access security measures
- **NIST SI-4**: Information system monitoring

---

## Budget Controls

### What It Does

Budget controls limit how much an agent can spend per day. This is critical for:

- Controlling cloud API costs
- Preventing financial impact from agent errors
- Meeting departmental budget constraints
- Cost allocation and chargeback

### Configuration Options

| Setting | Description | Example |
|---------|-------------|---------|
| Maximum Daily Budget (USD) | Hard spending limit per day | $1,000 |
| Alert Threshold (%) | Trigger alert at this % of budget | 80% |
| Auto-Suspend on Exceeded | Automatically disable agent at limit | Yes/No |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Budget Controls" section (marked with PCI-DSS 7.1 badge)

**Step 3:** Configure your budget limits:

```
Maximum Daily Budget: $1000.00
Alert Threshold: 80%
Auto-Suspend When Exceeded: ✓ Enabled
```

**Step 4:** Click "Save Configuration"

### Budget Tracking

The platform tracks costs based on:

- API calls to external LLM providers
- Compute resources consumed
- Data transfer volumes
- Custom cost attributions you define

### Alert Behavior

| Budget Used | Action |
|-------------|--------|
| 0-79% | Normal operation |
| 80% (threshold) | Alert sent to configured recipients |
| 90% | Warning alert sent |
| 100% | Agent suspended (if auto-suspend enabled) |

### Compliance Mapping

- **PCI-DSS 7.1**: Restrict access to need-to-know basis
- **SOC 2 A1.1**: Service availability commitments

---

## Time Window Enforcement

### What It Does

Time window enforcement restricts when agents can operate. Use cases include:

- Trading bots only during market hours
- Customer service bots during support hours
- Maintenance agents only during maintenance windows
- Compliance with labor regulations

### Configuration Options

| Setting | Description | Example |
|---------|-------------|---------|
| Enable Time Window | Turn restriction on/off | Yes/No |
| Start Time | When agent can start operating | 09:00 |
| End Time | When agent must stop operating | 17:00 |
| Timezone | Timezone for the window | America/New_York |
| Allowed Days | Days of the week | Mon, Tue, Wed, Thu, Fri |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Time Window Enforcement" section (marked with SOC 2 A1.1 badge)

**Step 3:** Enable and configure the time window:

```
Enable Time Window: ✓ On
Start Time: 09:00
End Time: 17:00
Timezone: America/New_York
Allowed Days: ☑ Mon ☑ Tue ☑ Wed ☑ Thu ☑ Fri ☐ Sat ☐ Sun
```

**Step 4:** Click "Save Configuration"

### Behavior Outside Time Windows

When an agent attempts to act outside its configured window:

1. The action is **blocked** (not queued)
2. Response includes `reason: "Outside operating hours"`
3. Next available window time is provided
4. Event is logged for audit purposes

### Example Response

```json
{
  "approved": false,
  "reason": "Outside operating hours",
  "time_window": {
    "current_time": "2025-12-04T22:30:00-05:00",
    "window_start": "09:00",
    "window_end": "17:00",
    "timezone": "America/New_York",
    "next_available": "2025-12-05T09:00:00-05:00"
  }
}
```

### Compliance Mapping

- **SOC 2 A1.1**: Service availability management
- **NIST AC-2(3)**: Automated account management

---

## Data Classification Controls

### What It Does

Data classification controls restrict what types of data an agent can access. This is essential for:

- HIPAA compliance (healthcare data)
- PCI-DSS compliance (payment card data)
- GDPR compliance (personal data)
- Internal data governance policies

### Classification Levels

Ascend supports the following data classification levels:

| Classification | Description | Example Data |
|----------------|-------------|--------------|
| `public` | Publicly available information | Marketing materials |
| `internal` | Internal company data | Internal memos |
| `confidential` | Sensitive business data | Financial forecasts |
| `pii` | Personal Identifiable Information | Customer names, emails |
| `financial` | Financial records | Account numbers, transactions |
| `healthcare` | Protected health information | Medical records |
| `secret` | Highly restricted data | Encryption keys |

### Configuration Options

| Setting | Description |
|---------|-------------|
| Allowed Classifications | Data types the agent CAN access |
| Blocked Classifications | Data types the agent CANNOT access (overrides allowed) |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Data Classification Controls" section (marked with HIPAA 164.312 badge)

**Step 3:** Configure allowed and blocked classifications:

```
Allowed Classifications:
  ☑ public
  ☑ internal
  ☐ confidential
  ☐ pii
  ☐ financial
  ☐ healthcare
  ☐ secret

Blocked Classifications:
  ☐ public
  ☐ internal
  ☐ confidential
  ☑ pii
  ☑ financial
  ☑ healthcare
  ☑ secret
```

**Step 4:** Click "Save Configuration"

### Classification Enforcement

When an agent attempts to access data:

1. Ascend checks the data's classification tag
2. If classification is in "blocked" list → **Deny**
3. If classification is NOT in "allowed" list → **Deny**
4. Otherwise → **Allow** (subject to other controls)

### Compliance Mapping

- **HIPAA 164.312**: Technical safeguards for PHI
- **PCI-DSS 3.4**: Protection of stored cardholder data
- **GDPR Art. 25**: Data protection by design

---

## Auto-Suspension Rules

### What It Does

Auto-suspension automatically disables agents when certain conditions are met. This provides:

- Automatic incident response
- Protection against cascading failures
- Compliance with operational policies
- Peace of mind for autonomous operations

### Suspension Triggers

| Trigger | Description | Example |
|---------|-------------|---------|
| Error Rate | Suspend if error rate exceeds threshold | >10% errors |
| Offline Duration | Suspend if no heartbeat for duration | 30 minutes |
| Budget Exceeded | Suspend when daily budget hit | $1000 spent |
| Rate Limit Exceeded | Suspend after repeated rate limit hits | 3x in 1 hour |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Auto-Suspension Rules" section (marked with NIST AC-2(3) badge)

**Step 3:** Enable and configure suspension triggers:

```
Enable Auto-Suspension: ✓ On

Triggers:
  ☑ Error Rate > 10%
  ☑ Offline > 30 minutes
  ☑ Budget Exceeded
  ☐ Rate Limit Exceeded
```

**Step 4:** Click "Save Configuration"

### Suspension Behavior

When an auto-suspension triggers:

1. Agent status immediately changes to **Suspended**
2. All pending actions are **blocked**
3. Audit log records the suspension with reason
4. Alert sent to configured recipients
5. Agent remains suspended until **manually reactivated**

### Reactivating a Suspended Agent

1. Navigate to **Agent Registry > [Agent Name]**
2. Review the suspension reason in the audit log
3. Address the root cause
4. Click **Reactivate Agent**
5. Enter reactivation notes (required for compliance)

### Compliance Mapping

- **SOC 2 CC6.2**: Logical access controls
- **NIST AC-2(3)**: Disable inactive accounts

---

## Escalation Configuration

### What It Does

Escalation ensures that blocked or high-risk actions don't go unnoticed. When an agent attempts a sensitive action, escalation can:

- Send real-time webhook notifications
- Email security/operations team
- Queue the action for human approval

### Escalation Options

| Option | Description | Use Case |
|--------|-------------|----------|
| Webhook URL | Real-time HTTP notification | SIEM integration, PagerDuty |
| Email Address | Email notification | Security team alerts |
| Queued Approval | Hold action for human review | Supervised autonomous agents |

### How to Configure

**Step 1:** Open the agent's Governance tab

**Step 2:** Locate the "Escalation Configuration" section (marked with enterprise badge)

**Step 3:** Configure escalation paths:

```
Escalation Webhook URL: https://your-siem.example.com/webhook/ascend
Escalation Email: security-team@yourcompany.com
Enable Queued Approval: ✓ On
```

**Step 4:** Click "Save Configuration"

### Webhook Payload

When escalation triggers, Ascend sends:

```json
{
  "event_type": "agent_action_escalated",
  "timestamp": "2025-12-04T14:32:00Z",
  "agent_id": "trading-bot-001",
  "action": {
    "action_type": "financial.transfer",
    "amount": 150000,
    "risk_score": 85
  },
  "reason": "High risk action requires approval",
  "action_id": "act_abc123",
  "approval_url": "https://pilot.owkai.app/approve/act_abc123"
}
```

### Queued Approval Flow

When queued approval is enabled:

1. High-risk action is **held** (not denied)
2. Notification sent via webhook/email
3. Approver reviews in Ascend dashboard
4. Approver clicks **Approve** or **Deny**
5. Agent receives the decision
6. Action proceeds or is blocked

### Compliance Mapping

- **SOC 2 CC6.1**: Access authorization
- **NIST AC-3**: Access enforcement

---

## Emergency Controls

### Emergency Kill Switch

For immediate agent suspension in critical situations:

**Step 1:** Navigate to **Agent Registry > [Agent Name]**

**Step 2:** Click the red **Emergency Suspend** button

**Step 3:** Enter a reason (required for audit trail):

```
Reason: Anomalous behavior detected - investigating security incident
```

**Step 4:** Confirm suspension

### What Happens

- Agent immediately stops all operations
- All pending actions are blocked
- Audit log records: timestamp, user, reason
- Agent status changes to **Emergency Suspended**
- Only administrators can reactivate

### Reactivation After Emergency

1. Investigate and resolve the incident
2. Document findings in your incident management system
3. Navigate to **Agent Registry > [Agent Name]**
4. Click **Reactivate Agent**
5. Enter detailed reactivation notes
6. Agent resumes normal operation

---

## Monitoring & Visibility

### Usage Dashboard

Each agent displays real-time metrics:

**Rate Limit Status:**
```
Minute: 45/100 (45% used) - Resets in 32s
Hour: 523/1000 (52% used) - Resets in 27m
Day: 4521/10000 (45% used) - Resets in 8h 42m
```

**Budget Status:**
```
Daily Budget: $1,000.00
Used Today: $342.17 (34%)
Alert Threshold: $800.00 (80%)
Status: ✓ Normal
```

**Health Status:**
```
Last Heartbeat: 2 minutes ago
Error Rate (24h): 1.2%
Status: ✓ Online
```

### Anomaly Detection

Ascend monitors agent behavior and alerts on anomalies:

| Metric | Baseline | Current | Status |
|--------|----------|---------|--------|
| Actions/Hour | 150 | 147 | Normal |
| Error Rate | 2% | 1.8% | Normal |
| Avg Risk Score | 35 | 34 | Normal |

When anomalies exceed thresholds, alerts are generated based on severity.

---

## API Reference

### Get Governance Configuration

```bash
GET /api/agent-registry/{agent_id}/governance

Response:
{
  "agent_id": "trading-bot-001",
  "rate_limits": {
    "max_actions_per_minute": 100,
    "max_actions_per_hour": 1000,
    "max_actions_per_day": 10000
  },
  "budget": {
    "max_daily_budget_usd": 1000,
    "alert_threshold_percent": 80,
    "auto_suspend_on_exceeded": true
  },
  "time_window": {
    "enabled": true,
    "start": "09:00",
    "end": "17:00",
    "timezone": "America/New_York",
    "days": [1, 2, 3, 4, 5]
  },
  "data_classifications": {
    "allowed": ["public", "internal"],
    "blocked": ["pii", "financial", "healthcare", "secret"]
  },
  "auto_suspension": {
    "enabled": true,
    "error_rate_threshold": 10,
    "offline_minutes_threshold": 30,
    "suspend_on_budget": true,
    "suspend_on_rate": false
  },
  "escalation": {
    "webhook_url": "https://siem.example.com/webhook",
    "email": "security@example.com",
    "queued_approval": true
  }
}
```

### Update Governance Configuration

```bash
PATCH /api/agent-registry/{agent_id}/governance
Content-Type: application/json

{
  "rate_limits": {
    "max_actions_per_minute": 200
  },
  "budget": {
    "max_daily_budget_usd": 2000
  }
}

Response:
{
  "success": true,
  "message": "Governance configuration updated",
  "agent_id": "trading-bot-001"
}
```

### Emergency Suspend

```bash
POST /api/agent-registry/{agent_id}/emergency-suspend
Content-Type: application/json

{
  "reason": "Security incident investigation"
}

Response:
{
  "success": true,
  "agent_id": "trading-bot-001",
  "status": "emergency_suspended",
  "suspended_at": "2025-12-04T14:32:00Z",
  "suspended_by": "admin@example.com"
}
```

---

## Best Practices

### For Initial Deployment

1. **Start Conservative**: Set strict limits initially, then relax based on observed behavior
2. **Enable All Monitoring**: Turn on anomaly detection from day one
3. **Configure Escalation**: Always have a notification path for blocked actions
4. **Document Baselines**: Record expected behavior patterns for comparison

### For Production Operations

1. **Review Weekly**: Check usage dashboards and anomaly alerts regularly
2. **Tune Thresholds**: Adjust limits based on actual usage patterns
3. **Test Escalation**: Periodically verify webhook/email notifications work
4. **Audit Trail Review**: Include governance events in compliance reviews

### For Compliance

1. **Map Controls to Requirements**: Document which controls satisfy which regulations
2. **Retain Audit Logs**: Keep governance event logs per retention policy
3. **Regular Assessments**: Include governance configuration in security reviews
4. **Evidence Collection**: Export governance configs for auditor review

---

## Troubleshooting

### Agent Not Respecting Rate Limits

1. Verify rate limits are configured (not null)
2. Check if agent is using cached authorization
3. Review audit logs for rate limit events
4. Ensure API key has correct permissions

### Budget Alerts Not Triggering

1. Verify alert threshold is set (default: 80%)
2. Check escalation email is configured
3. Verify webhook URL is accessible
4. Review notification service logs

### Time Window Not Enforcing

1. Verify time window is enabled
2. Check timezone configuration
3. Ensure allowed days are selected
4. Verify server time is synchronized

---

## Getting Help

**In-App Support:**
- Click **?** icon for contextual help
- Access documentation at **Settings > Documentation**

**Support Channels:**
- Documentation: https://docs.ascendowkai.com
- Status Page: https://status.ascendowkai.com
- Email: support@ascendowkai.com
- Enterprise Support: enterprise@ascendowkai.com

---

*Ascend Platform - Enterprise AI Agent Governance*
*© 2025 OW-kai Technologies Inc. All rights reserved.*
