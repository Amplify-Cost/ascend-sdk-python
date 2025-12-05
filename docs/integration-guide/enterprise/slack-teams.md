# Slack & Teams Integration

Integrate Ascend with Slack and Microsoft Teams to receive real-time notifications for approval requests, policy violations, and security alerts.

## Supported Platforms

| Platform | Features | Status |
|----------|----------|--------|
| Slack | Webhooks, Interactive Messages | Supported |
| Microsoft Teams | Webhooks, Adaptive Cards | Supported |

## Notification Types

| Event | Description | Default Channel |
|-------|-------------|-----------------|
| Approval Required | Action needs human approval | #approvals |
| Action Approved | Action was approved | #approvals |
| Action Rejected | Action was rejected | #approvals |
| Policy Violation | Policy rule triggered | #security-alerts |
| High Risk Alert | High-risk action detected | #security-alerts |
| System Alert | System health notification | #ops |

## Slack Configuration

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name: `Ascend Governance`
4. Select your workspace

### 2. Enable Incoming Webhooks

1. Navigate to **Incoming Webhooks**
2. Toggle **Activate Incoming Webhooks** to On
3. Click **Add New Webhook to Workspace**
4. Select the channel for notifications
5. Copy the Webhook URL

### 3. Configure in Ascend

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Security Team Slack",
    "type": "slack",
    "config": {
      "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXX"
    },
    "events": ["approval_required", "policy_violation", "high_risk_alert"]
  }'
```

### Slack Message Format

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Approval Required"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Agent:*\ncustomer-service-agent"},
        {"type": "mrkdwn", "text": "*Action:*\ndatabase_query"},
        {"type": "mrkdwn", "text": "*Resource:*\ncustomer_database"},
        {"type": "mrkdwn", "text": "*Risk Score:*\n75 (High)"}
      ]
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "Approve"},
          "style": "primary",
          "url": "https://pilot.owkai.app/approvals/act_xyz789"
        },
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "View Details"},
          "url": "https://pilot.owkai.app/actions/act_xyz789"
        }
      ]
    }
  ]
}
```

## Microsoft Teams Configuration

### 1. Create Incoming Webhook

1. Open Microsoft Teams
2. Navigate to the target channel
3. Click **...** → **Connectors**
4. Find **Incoming Webhook** and click **Configure**
5. Name: `Ascend Governance`
6. Upload icon (optional)
7. Click **Create** and copy the webhook URL

### 2. Configure in Ascend

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/channels \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Security Team Teams",
    "type": "teams",
    "config": {
      "webhook_url": "https://outlook.office.com/webhook/xxx/IncomingWebhook/yyy/zzz"
    },
    "events": ["approval_required", "policy_violation"]
  }'
```

### Teams Adaptive Card Format

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "text": "Approval Required",
            "weight": "bolder",
            "size": "large"
          },
          {
            "type": "FactSet",
            "facts": [
              {"title": "Agent", "value": "customer-service-agent"},
              {"title": "Action", "value": "database_query"},
              {"title": "Resource", "value": "customer_database"},
              {"title": "Risk Score", "value": "75 (High)"}
            ]
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "Approve",
            "url": "https://pilot.owkai.app/approvals/act_xyz789"
          },
          {
            "type": "Action.OpenUrl",
            "title": "View Details",
            "url": "https://pilot.owkai.app/actions/act_xyz789"
          }
        ]
      }
    }
  ]
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/channels` | POST | Create notification channel |
| `/api/notifications/channels` | GET | List channels |
| `/api/notifications/channels/{id}` | PUT | Update channel |
| `/api/notifications/channels/{id}` | DELETE | Delete channel |
| `/api/notifications/test/{id}` | POST | Send test notification |

## Event Configuration

### Configure Events per Channel

```bash
curl -X PUT https://pilot.owkai.app/api/api/notifications/channels/chan_123 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "events": [
      "approval_required",
      "action_approved",
      "action_rejected",
      "policy_violation",
      "high_risk_alert"
    ],
    "filters": {
      "min_risk_score": 60,
      "action_types": ["database_query", "api_call", "file_access"]
    }
  }'
```

### Event Filtering

| Filter | Description |
|--------|-------------|
| `min_risk_score` | Only notify for actions above threshold |
| `action_types` | Filter by specific action types |
| `agents` | Filter by specific agents |
| `severity` | Filter by severity level |

## Templates

### Custom Message Templates

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/templates \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "approval_required_custom",
    "type": "slack",
    "template": {
      "text": "Action requires approval: {{action_type}} on {{resource}}",
      "blocks": [...]
    }
  }'
```

## Testing

### Send Test Notification

```bash
curl -X POST https://pilot.owkai.app/api/api/notifications/test/chan_123 \
  -b cookies.txt
```

## Troubleshooting

### Notifications Not Arriving

1. Verify webhook URL is correct
2. Check channel permissions
3. Test webhook directly:
   ```bash
   curl -X POST "your-webhook-url" \
     -H "Content-Type: application/json" \
     -d '{"text": "Test from Ascend"}'
   ```

### Rate Limiting

- Slack: 1 message per second per webhook
- Teams: 4 messages per second per webhook

Ascend automatically queues and throttles messages to respect limits.

## Next Steps

- [SIEM Integration](/enterprise/siem) - Forward to SIEM
- [Approval Workflows](/core-concepts/approval-workflows) - Configure workflows
- [Webhooks](/sdk/rest/webhooks) - Custom integrations
