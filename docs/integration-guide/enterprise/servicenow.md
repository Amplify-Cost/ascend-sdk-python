---
Document ID: ASCEND-ENT-009
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# ServiceNow Integration

Integrate Ascend with ServiceNow to automatically create incidents and manage tickets from governance events.

## Overview

The ServiceNow integration enables:

- Automatic incident creation for policy violations
- Ticket synchronization
- Change request workflows
- CMDB integration

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/servicenow/connections` | POST | Create connection |
| `/servicenow/connections` | GET | List connections |
| `/servicenow/connections/{id}` | GET | Get connection |
| `/servicenow/connections/{id}` | PUT | Update connection |
| `/servicenow/connections/{id}` | DELETE | Delete connection |
| `/servicenow/test` | POST | Test connection |
| `/servicenow/sync` | POST | Sync with ServiceNow |
| `/servicenow/tickets` | POST | Create ticket |
| `/servicenow/tickets` | GET | List tickets |
| `/servicenow/tickets/{id}` | GET | Get ticket |
| `/servicenow/tickets/{id}` | PUT | Update ticket |
| `/servicenow/metrics` | GET | Get metrics |

## Configuration

### Create Connection

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/connections \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production ServiceNow",
    "instance_url": "https://company.service-now.com",
    "auth_type": "basic",
    "username": "ascend_integration",
    "password": "your-password",
    "auto_create_incidents": true,
    "default_assignment_group": "Security Operations",
    "incident_severity_mapping": {
      "critical": 1,
      "high": 2,
      "medium": 3,
      "low": 4
    }
  }'
```

### OAuth Authentication

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/connections \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Production ServiceNow",
    "instance_url": "https://company.service-now.com",
    "auth_type": "oauth",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "auto_create_incidents": true
  }'
```

### Test Connection

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/test \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "connection_id": "conn_123"
  }'
```

## Automatic Incident Creation

### Enable Auto-Creation

```json
{
  "auto_create_incidents": true,
  "trigger_events": [
    "action.blocked",
    "policy.violation",
    "high_risk_alert"
  ],
  "min_risk_score": 70
}
```

### Incident Template

```json
{
  "incident_template": {
    "category": "Security",
    "subcategory": "AI Governance",
    "impact": "{{risk_level}}",
    "urgency": "{{risk_level}}",
    "short_description": "Ascend: {{event_type}} - {{agent_id}}",
    "description": "{{full_description}}",
    "assignment_group": "Security Operations",
    "caller_id": "ascend_integration"
  }
}
```

## Manual Ticket Creation

### Create Incident

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/tickets \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "connection_id": "conn_123",
    "type": "incident",
    "short_description": "High-risk action blocked",
    "description": "Agent customer-service-agent attempted database_query on customer_database. Risk score: 85.",
    "category": "Security",
    "priority": 2,
    "assignment_group": "Security Operations",
    "ascend_action_id": "act_xyz789"
  }'
```

### Create Change Request

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/tickets \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "connection_id": "conn_123",
    "type": "change_request",
    "short_description": "Policy update: Data Access Policy",
    "description": "Update governance policy to allow new agent access.",
    "category": "Policy Change",
    "risk": "low",
    "change_type": "normal"
  }'
```

## Ticket Synchronization

### Sync Status

```bash
curl -X POST https://pilot.owkai.app/api/servicenow/sync \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "connection_id": "conn_123",
    "direction": "bidirectional"
  }'
```

### Webhook for Updates

Configure ServiceNow to send updates back to Ascend:

```
Business Rule: After Update on Incident
Condition: current.correlation_id.startsWith('ascend_')
Script:
  var gr = new GlideHTTPRequest('https://pilot.owkai.app/api/webhooks/servicenow');
  gr.addHeader('X-ServiceNow-Webhook', 'your-webhook-secret');
  gr.post(JSON.stringify({
    sys_id: current.sys_id,
    number: current.number,
    state: current.state,
    resolution_code: current.close_code
  }));
```

## Severity Mapping

| Ascend Risk Level | ServiceNow Impact | ServiceNow Urgency | Priority |
|-------------------|-------------------|-------------------|----------|
| Critical (90-100) | 1 - High | 1 - High | 1 |
| High (70-89) | 2 - Medium | 2 - Medium | 2 |
| Medium (40-69) | 2 - Medium | 3 - Low | 3 |
| Low (0-39) | 3 - Low | 3 - Low | 4 |

## Listing Tickets

```bash
curl https://pilot.owkai.app/api/servicenow/tickets \
  -b cookies.txt
```

**Response:**

```json
{
  "tickets": [
    {
      "id": "ticket_123",
      "servicenow_number": "INC0012345",
      "servicenow_sys_id": "abc123def456",
      "type": "incident",
      "short_description": "High-risk action blocked",
      "state": "In Progress",
      "priority": 2,
      "ascend_action_id": "act_xyz789",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T12:30:00Z"
    }
  ]
}
```

## Metrics

```bash
curl https://pilot.owkai.app/api/servicenow/metrics \
  -b cookies.txt
```

**Response:**

```json
{
  "total_tickets": 156,
  "open_tickets": 12,
  "avg_resolution_time_hours": 4.2,
  "tickets_by_type": {
    "incident": 142,
    "change_request": 14
  },
  "tickets_by_priority": {
    "1": 8,
    "2": 45,
    "3": 78,
    "4": 25
  }
}
```

## CMDB Integration

### Link Agents to CIs

```json
{
  "cmdb_mapping": {
    "agent_to_ci": true,
    "ci_class": "cmdb_ci_appl",
    "attributes": {
      "name": "{{agent_id}}",
      "category": "AI Agent",
      "subcategory": "Governance Monitored"
    }
  }
}
```

## Best Practices

1. **Use service accounts** - Create dedicated ServiceNow account
2. **Map severity correctly** - Align risk levels with business impact
3. **Enable bidirectional sync** - Keep Ascend updated on ticket status
4. **Set appropriate triggers** - Don't create incidents for low-risk events
5. **Document workflows** - Maintain runbooks for incident response

## Troubleshooting

### Connection Failed

- Verify instance URL
- Check credentials
- Ensure service account has appropriate roles

### Tickets Not Creating

- Check auto_create_incidents is enabled
- Verify trigger_events includes expected events
- Review min_risk_score threshold

### Sync Issues

- Check network connectivity
- Verify API rate limits
- Review ServiceNow logs

## Next Steps

- [SIEM Integration](/enterprise/siem) - Security event monitoring
- [Slack/Teams](/enterprise/slack-teams) - Notifications
- [Compliance](/enterprise/compliance) - Compliance reporting
