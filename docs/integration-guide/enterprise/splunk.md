# Splunk Integration

Integrate Ascend with Splunk for comprehensive security event monitoring and analysis.

## Overview

Send Ascend governance events to Splunk via HTTP Event Collector (HEC) for:

- Real-time security monitoring
- Custom dashboards
- Alert correlation
- Compliance reporting

## Configuration

### 1. Create Splunk HEC Token

1. In Splunk, navigate to **Settings** → **Data Inputs** → **HTTP Event Collector**
2. Click **New Token**
3. Configure:
   - Name: `Ascend Governance`
   - Source type: `ascend:audit`
   - Index: `ascend_security` (or your preferred index)
4. Copy the token

### 2. Configure Ascend

```bash
curl -X POST https://pilot.owkai.app/api/siem/configure \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "splunk",
    "config": {
      "hec_url": "https://splunk.company.com:8088",
      "hec_token": "your-hec-token",
      "index": "ascend_security",
      "sourcetype": "ascend:audit",
      "source": "ascend_governance",
      "verify_ssl": true
    },
    "events": ["*"],
    "include_metadata": true
  }'
```

### 3. Test Connection

```bash
curl -X POST https://pilot.owkai.app/api/siem/test-connection \
  -b cookies.txt
```

## Event Format

### Standard Event

```json
{
  "time": 1705320000,
  "host": "pilot.owkai.app/api",
  "source": "ascend_governance",
  "sourcetype": "ascend:audit",
  "index": "ascend_security",
  "event": {
    "event_type": "action.blocked",
    "timestamp": "2025-01-15T10:00:00Z",
    "organization": {
      "id": 123,
      "name": "Acme Corp"
    },
    "user": {
      "id": 456,
      "email": "user@acmecorp.com"
    },
    "agent": {
      "id": "customer-service-agent",
      "type": "automation"
    },
    "action": {
      "id": "act_xyz789",
      "type": "database_query",
      "resource": "customer_database",
      "description": "SELECT * FROM customers"
    },
    "risk": {
      "score": 85,
      "level": "critical",
      "factors": ["sensitive_data", "bulk_access"]
    },
    "decision": {
      "outcome": "blocked",
      "reason": "Risk threshold exceeded",
      "policy_id": "pol_123",
      "policy_name": "Data Protection"
    }
  }
}
```

## Splunk Searches

### High-Risk Actions

```spl
index=ascend_security sourcetype="ascend:audit"
| where 'event.risk.score' >= 80
| stats count by 'event.agent.id', 'event.risk.level'
| sort -count
```

### Authentication Events

```spl
index=ascend_security sourcetype="ascend:audit"
  event_type IN ("auth.failed", "auth.mfa_failed", "user.locked")
| timechart span=1h count by event_type
```

### Policy Violations by Organization

```spl
index=ascend_security sourcetype="ascend:audit"
  event_type="policy.violation"
| stats count by 'event.organization.name', 'event.decision.policy_name'
| sort -count
```

### Agent Activity Timeline

```spl
index=ascend_security sourcetype="ascend:audit"
| timechart span=5m count by 'event.agent.id'
```

### Blocked Actions Report

```spl
index=ascend_security sourcetype="ascend:audit"
  'event.decision.outcome'="blocked"
| table _time, 'event.agent.id', 'event.action.type',
        'event.action.resource', 'event.risk.score', 'event.decision.reason'
```

## Splunk Dashboards

### Import Dashboard

```bash
# Download Ascend dashboard
curl -O https://pilot.owkai.app/api/static/splunk/ascend_dashboard.xml

# Import to Splunk
# Settings → Dashboards → Create from XML
```

### Dashboard Panels

1. **Risk Score Distribution** - Histogram of action risk scores
2. **Actions by Status** - Approved/Rejected/Blocked pie chart
3. **Top Agents** - Most active agents
4. **Policy Violations** - Violations over time
5. **Authentication Events** - Login/logout/failures

## Splunk Alerts

### High-Risk Action Alert

```spl
index=ascend_security sourcetype="ascend:audit"
  'event.risk.score' >= 90
| stats count by 'event.agent.id'
| where count >= 3
```

Alert settings:
- Trigger: Number of results > 0
- Throttle: 15 minutes
- Action: Send to Slack/Email

### Multiple Failed Logins

```spl
index=ascend_security sourcetype="ascend:audit"
  event_type="auth.failed"
| stats count by 'event.user.email'
| where count >= 5
```

### Anomalous Agent Behavior

```spl
index=ascend_security sourcetype="ascend:audit"
| stats count as actions by 'event.agent.id'
| eventstats avg(actions) as avg_actions, stdev(actions) as stdev_actions
| where actions > (avg_actions + 2*stdev_actions)
```

## Field Extractions

### Create Field Extractions

```spl
# Props.conf
[ascend:audit]
SHOULD_LINEMERGE = false
TIME_FORMAT = %Y-%m-%dT%H:%M:%S
TIME_PREFIX = "timestamp":"
KV_MODE = json
```

### Common Fields

| Field | Description |
|-------|-------------|
| `event.event_type` | Event type (action.blocked, etc.) |
| `event.risk.score` | Risk score (0-100) |
| `event.risk.level` | Risk level (low/medium/high/critical) |
| `event.agent.id` | Agent identifier |
| `event.organization.name` | Organization name |
| `event.decision.outcome` | Decision (approved/rejected/blocked) |

## Troubleshooting

### Events Not Appearing

1. Verify HEC token is valid
2. Check index exists and has capacity
3. Test HEC directly:
   ```bash
   curl -k https://splunk:8088/services/collector \
     -H "Authorization: Splunk your-token" \
     -d '{"event": "test"}'
   ```

### Parsing Issues

1. Check sourcetype configuration
2. Verify JSON is valid
3. Review props.conf settings

### Latency

1. Check network connectivity
2. Review Splunk indexer queue
3. Consider increasing batch size

## Best Practices

1. **Use dedicated index** - Separate Ascend events from other data
2. **Set retention** - Configure appropriate retention for compliance
3. **Create saved searches** - Pre-build common queries
4. **Enable alerts** - Set up proactive monitoring
5. **Document dashboards** - Maintain dashboard documentation

## Next Steps

- [SIEM Integration](/enterprise/siem) - General SIEM setup
- [Compliance](/enterprise/compliance) - Compliance reporting
- [Audit Logging](/core-concepts/audit-logging) - Audit trail details
