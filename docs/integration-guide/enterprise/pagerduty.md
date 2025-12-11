---
Document ID: ASCEND-ENT-003
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# PagerDuty Integration

Integrate Ascend with PagerDuty to receive real-time alerts for critical governance events.

## Overview

The PagerDuty integration enables:

- Real-time incident alerting
- On-call escalation
- Alert correlation
- Runbook automation

## Configuration

### 1. Create PagerDuty Integration

1. In PagerDuty, go to **Services** → **Service Directory**
2. Select or create a service
3. Go to **Integrations** tab → **Add Integration**
4. Select **Events API v2**
5. Copy the Integration Key

### 2. Configure in Ascend

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "PagerDuty Security",
    "type": "pagerduty",
    "config": {
      "integration_key": "your-integration-key",
      "routing_key": "your-routing-key"
    },
    "events": [
      "action.blocked",
      "policy.violation",
      "auth.failed",
      "anomaly.detected"
    ],
    "severity_mapping": {
      "critical": "critical",
      "high": "error",
      "medium": "warning",
      "low": "info"
    }
  }'
```

## Event Format

### Trigger Event

```json
{
  "routing_key": "your-routing-key",
  "event_action": "trigger",
  "dedup_key": "ascend-act_xyz789",
  "payload": {
    "summary": "High-risk action blocked: database_query on customer_database",
    "severity": "critical",
    "source": "ascend-governance",
    "component": "customer-service-agent",
    "group": "Acme Corp",
    "class": "policy.violation",
    "custom_details": {
      "action_id": "act_xyz789",
      "agent_id": "customer-service-agent",
      "action_type": "database_query",
      "resource": "customer_database",
      "risk_score": 85,
      "risk_level": "critical",
      "policy_name": "Data Protection Policy",
      "organization": "Acme Corp"
    }
  },
  "links": [
    {
      "href": "https://pilot.owkai.app/actions/act_xyz789",
      "text": "View in Ascend"
    }
  ]
}
```

### Resolve Event

When an action is approved or resolved:

```json
{
  "routing_key": "your-routing-key",
  "event_action": "resolve",
  "dedup_key": "ascend-act_xyz789"
}
```

## Severity Mapping

| Ascend Risk | PagerDuty Severity | Description |
|-------------|-------------------|-------------|
| Critical (90-100) | `critical` | Pages immediately |
| High (70-89) | `error` | High urgency |
| Medium (40-69) | `warning` | Low urgency |
| Low (0-39) | `info` | Informational |

## Alert Routing

### Route by Risk Level

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "PagerDuty Critical Only",
    "type": "pagerduty",
    "config": {
      "integration_key": "critical-service-key"
    },
    "filters": {
      "min_risk_score": 90
    }
  }'
```

### Route by Event Type

```json
{
  "routing_rules": [
    {
      "events": ["auth.failed", "auth.mfa_failed"],
      "routing_key": "security-on-call"
    },
    {
      "events": ["action.blocked"],
      "routing_key": "governance-on-call"
    }
  ]
}
```

## Alert Correlation

### Deduplication

Ascend uses the action ID as the dedup key, preventing duplicate alerts:

```
dedup_key: ascend-{action_id}
```

### Alert Grouping

Configure in PagerDuty:
- **Intelligent grouping** - Let PagerDuty correlate
- **Content-based** - Group by agent_id or organization

## Runbook Automation

### Link Runbooks

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "PagerDuty with Runbooks",
    "type": "pagerduty",
    "config": {
      "integration_key": "your-key",
      "runbook_links": {
        "action.blocked": "https://wiki.company.com/runbooks/blocked-action",
        "policy.violation": "https://wiki.company.com/runbooks/policy-violation"
      }
    }
  }'
```

## Testing

### Send Test Alert

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/test \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "channel_id": "chan_pagerduty_123"
  }'
```

### Verify in PagerDuty

1. Check your service for the test incident
2. Verify severity and details
3. Acknowledge and resolve

## Best Practices

1. **Set appropriate thresholds** - Only page for critical events
2. **Use escalation policies** - Configure proper on-call rotation
3. **Add context** - Include links and details in alerts
4. **Configure maintenance windows** - Suppress during planned work
5. **Test regularly** - Verify integration is working

## Troubleshooting

### Alerts Not Triggering

- Verify integration key is correct
- Check event filters match your events
- Review PagerDuty service status

### Duplicate Alerts

- Verify dedup_key is consistent
- Check for multiple channel configurations
- Review event processing logs

### Missing Details

- Ensure `include_metadata` is enabled
- Check custom_details mapping
- Review event payload in PagerDuty

## Next Steps

- [Slack/Teams](/enterprise/slack-teams) - Additional notifications
- [SIEM Integration](/enterprise/siem) - Security monitoring
- [ServiceNow](/enterprise/servicenow) - Ticket management
