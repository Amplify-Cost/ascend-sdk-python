---
title: SIEM Integration
sidebar_position: 1
---

# SIEM Integration

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-ENT-006 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

Forward Ascend security events and audit logs to your SIEM platform for centralized security monitoring and compliance.

## Supported SIEM Platforms

Query supported platforms via the API:

```bash
curl https://pilot.owkai.app/api/siem/supported-integrations \
  -b cookies.txt
```

| Platform | Integration Method | Status |
|----------|-------------------|--------|
| Splunk | HTTP Event Collector | Supported |
| Datadog | API Integration | Supported |
| Elastic/ELK | Webhook/Logstash | Supported |
| Azure Sentinel | Event Hub | Supported |
| AWS Security Hub | EventBridge | Supported |
| IBM QRadar | Syslog | Supported |
| Generic Webhook | HTTPS POST | Supported |
| Syslog | TCP/UDP | Supported |

## Quick Setup

### 1. Configure SIEM Connection

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
      "sourcetype": "ascend:audit"
    },
    "events": ["action.blocked", "auth.failed", "policy.violation"]
  }'
```

### 2. Test Connection

```bash
curl -X POST https://pilot.owkai.app/api/siem/test-connection \
  -b cookies.txt
```

### 3. Send Test Event

```bash
curl -X POST https://pilot.owkai.app/api/siem/send-test-event \
  -b cookies.txt
```

### 4. Check Status

```bash
curl https://pilot.owkai.app/api/siem/status \
  -b cookies.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/siem/configure` | POST | Configure SIEM connection |
| `/siem/test-connection` | POST | Test SIEM connectivity |
| `/siem/status` | GET | Get current SIEM status |
| `/siem/send-test-event` | POST | Send test event to SIEM |
| `/siem/supported-integrations` | GET | List supported SIEM platforms |
| `/siem/disconnect` | DELETE | Disconnect SIEM integration |

## Event Types

### Security Events (High Priority)

| Event | Severity | Description |
|-------|----------|-------------|
| `action.blocked` | High | Agent action blocked by policy |
| `action.high_risk` | High | High-risk action detected |
| `auth.failed` | Medium | Authentication failure |
| `auth.mfa_failed` | High | MFA verification failed |
| `anomaly.detected` | High | Behavioral anomaly detected |
| `policy.violation` | Medium | Policy rule triggered |
| `secret.rotated` | Info | Secret rotation occurred |
| `user.locked` | High | User account locked |

### Audit Events (Standard Priority)

| Event | Severity | Description |
|-------|----------|-------------|
| `action.submitted` | Info | Agent action submitted |
| `action.approved` | Info | Action approved |
| `action.rejected` | Info | Action rejected |
| `workflow.completed` | Info | Approval workflow completed |
| `user.login` | Info | User logged in |
| `user.logout` | Info | User logged out |
| `policy.created` | Info | Policy created |
| `policy.updated` | Info | Policy updated |

## Splunk Integration

### Configuration

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
      "source": "ascend_governance"
    },
    "events": ["*"],
    "include_metadata": true
  }'
```

### Event Format

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
    "organization_id": 123,
    "organization_name": "Acme Corp",
    "user_id": 456,
    "user_email": "user@acmecorp.com",
    "agent": {
      "agent_id": "customer-service-agent",
      "agent_type": "automation"
    },
    "action": {
      "action_id": "act_xyz789",
      "action_type": "database_query",
      "target_resource": "customer_database"
    },
    "risk": {
      "score": 85,
      "level": "critical",
      "factors": ["sensitive_data", "unusual_volume", "off_hours"]
    },
    "decision": {
      "outcome": "blocked",
      "reason": "Critical risk threshold exceeded",
      "policy_id": "pol_data_protection",
      "policy_name": "Data Protection Policy"
    }
  }
}
```

### Splunk Search Queries

```spl
# High-risk blocked actions
index=ascend_security sourcetype="ascend:audit" event_type="action.blocked" risk.score>=80
| stats count by agent.agent_id, risk.level
| sort -count

# Authentication failures by user
index=ascend_security sourcetype="ascend:audit" event_type="auth.failed"
| stats count by user_email
| where count > 5

# Actions by organization
index=ascend_security sourcetype="ascend:audit"
| timechart span=1h count by organization_name
```

## Datadog Integration

### Configuration

```bash
curl -X POST https://pilot.owkai.app/api/siem/configure \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "datadog",
    "config": {
      "api_key": "your-datadog-api-key",
      "site": "datadoghq.com",
      "service": "ascend-governance",
      "env": "production"
    },
    "events": ["*"],
    "tags": ["team:security", "product:ascend"]
  }'
```

### Datadog Log Format

```json
{
  "ddsource": "ascend",
  "ddtags": "env:production,service:ascend-governance,team:security",
  "hostname": "pilot.owkai.app/api",
  "service": "ascend-governance",
  "status": "warn",
  "message": "Agent action blocked: database_query on customer_database",
  "event_type": "action.blocked",
  "risk_score": 85,
  "organization_id": 123,
  "agent_id": "customer-service-agent"
}
```

## Elastic/ELK Integration

### Webhook Configuration

```bash
curl -X POST https://pilot.owkai.app/api/siem/configure \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "webhook",
    "config": {
      "url": "https://logstash.company.com:5044",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json",
        "X-Source": "ascend"
      }
    },
    "events": ["*"]
  }'
```

### Logstash Configuration

```ruby
input {
  http {
    port => 5044
    codec => json
  }
}

filter {
  if [source] == "ascend" {
    mutate {
      add_field => { "[@metadata][index]" => "ascend-events" }
    }

    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }

    # Map risk level to severity
    if [risk][score] >= 80 {
      mutate { add_field => { "severity" => "critical" } }
    } else if [risk][score] >= 60 {
      mutate { add_field => { "severity" => "high" } }
    } else if [risk][score] >= 40 {
      mutate { add_field => { "severity" => "medium" } }
    } else {
      mutate { add_field => { "severity" => "low" } }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index]}-%{+YYYY.MM.dd}"
  }
}
```

## Syslog Integration

### Configuration

```bash
curl -X POST https://pilot.owkai.app/api/siem/configure \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "type": "syslog",
    "config": {
      "host": "syslog.company.com",
      "port": 514,
      "protocol": "tcp",
      "format": "rfc5424",
      "facility": "local0"
    },
    "events": ["action.blocked", "auth.failed"]
  }'
```

### CEF Format

```
CEF:0|Ascend|AI Governance|1.0|action.blocked|Action Blocked|8|
src=customer-service-agent dst=customer_database act=database_query
risk=85 org=Acme Corp reason=Critical risk threshold exceeded
```

## Event Filtering

### Filter by Severity

```json
{
  "filters": {
    "min_severity": "medium",
    "events": ["action.*", "auth.*"]
  }
}
```

### Filter by Risk Score

```json
{
  "filters": {
    "risk_score": {
      "min": 60
    },
    "events": ["action.blocked", "action.high_risk"]
  }
}
```

### Filter by Event Pattern

```json
{
  "filters": {
    "events": ["action.blocked", "auth.*", "anomaly.*"],
    "exclude": ["user.login", "user.logout"]
  }
}
```

## Integration with Notifications

Combine SIEM with notification channels:

```bash
# Configure notification channel
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Security Team Slack",
    "type": "slack",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/xxx/yyy/zzz"
    }
  }'
```

## ServiceNow Integration

Create ServiceNow incidents from high-risk events:

```bash
# Configure ServiceNow connection
curl -X POST https://pilot.owkai.app/api/servicenow/connections \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "instance_url": "https://company.service-now.com",
    "username": "ascend_integration",
    "password": "your-password",
    "auto_create_incidents": true,
    "incident_severity_mapping": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 4
    }
  }'
```

## Webhook Events

Configure webhooks for custom integrations:

```bash
curl -X POST https://pilot.owkai.app/api/webhooks/subscriptions \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "url": "https://your-system.com/webhook",
    "events": ["action_approved", "action_rejected", "policy_change"],
    "secret": "your-webhook-secret"
  }'
```

### Webhook Payload

```json
{
  "event_type": "action_approved",
  "timestamp": "2025-01-15T10:00:00Z",
  "data": {
    "action_id": "act_xyz789",
    "action_type": "database_query",
    "approved_by": "admin@company.com",
    "organization_id": 123
  },
  "signature": "sha256=abc123..."
}
```

## Disconnecting SIEM

```bash
curl -X DELETE https://pilot.owkai.app/api/siem/disconnect \
  -b cookies.txt
```

## Troubleshooting

### Events Not Arriving

1. **Check connection status:**
   ```bash
   curl https://pilot.owkai.app/api/siem/status -b cookies.txt
   ```

2. **Test connectivity:**
   ```bash
   curl -X POST https://pilot.owkai.app/api/siem/test-connection -b cookies.txt
   ```

3. **Send test event:**
   ```bash
   curl -X POST https://pilot.owkai.app/api/siem/send-test-event -b cookies.txt
   ```

### Authentication Errors

- Verify SIEM credentials are correct
- Check token/API key hasn't expired
- Ensure IP allowlisting if applicable

### Missing Fields

- Enable `include_metadata: true` in configuration
- Verify event filters include required events
- Check field mapping in your SIEM

## Best Practices

1. **Start with high-priority events** - Begin with `action.blocked` and `auth.failed`
2. **Use appropriate retention** - SIEM logs may have different retention than Ascend audit logs
3. **Set up alerts** - Configure SIEM alerts for patterns like multiple blocked actions
4. **Test regularly** - Use test events to verify integration health
5. **Monitor delays** - Events should arrive within 60 seconds

## Next Steps

- [Compliance Export](/security/compliance) - Export compliance reports
- [Audit Logging](/core-concepts/audit-logging) - Audit trail details
- [Webhooks](/sdk/rest/webhooks) - Custom event subscriptions
