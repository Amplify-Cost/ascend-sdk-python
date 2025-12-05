# Webhooks

Receive real-time notifications when events occur in Ascend.

## Overview

Webhooks allow your application to receive HTTP POST requests when specific events occur, enabling real-time integrations without polling.

## Configuring Webhooks

### Via Dashboard

1. Navigate to **Settings** → **Webhooks**
2. Click **Add Webhook**
3. Enter your endpoint URL
4. Select events to subscribe to
5. Copy and store the signing secret

### Via API

```bash
curl -X POST https://pilot.owkai.app/api/api/webhooks \
  -H "Authorization: Bearer ask_live_xxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/ascend",
    "events": ["action.approved", "action.blocked"],
    "secret": "whsec_your_secret"
  }'
```

## Webhook Payload

All webhooks follow this structure:

```json
{
  "id": "evt_abc123",
  "type": "action.approved",
  "created_at": "2025-01-15T10:30:00Z",
  "data": {
    "action_id": "act_xyz789",
    "agent_id": "my-agent",
    "status": "approved",
    "risk_score": 25
  }
}
```

## Event Types

### Action Events

| Event | Description |
|-------|-------------|
| `action.submitted` | Action submitted |
| `action.approved` | Action approved |
| `action.denied` | Action denied |
| `action.blocked` | Action blocked by policy |
| `action.escalated` | Action escalated |
| `action.timeout` | Approval timed out |

### Workflow Events

| Event | Description |
|-------|-------------|
| `workflow.started` | Workflow initiated |
| `workflow.completed` | Workflow finished |
| `workflow.escalated` | Workflow escalated |

### Security Events

| Event | Description |
|-------|-------------|
| `security.high_risk` | High risk action detected |
| `security.anomaly` | Anomaly detected |

## Verifying Signatures

Webhooks are signed using HMAC-SHA256. Always verify the signature.

### Node.js

```typescript
import crypto from 'crypto';

function verifyWebhook(payload: string, signature: string, secret: string): boolean {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');

    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(`sha256=${expected}`)
    );
}

// Express middleware
app.post('/webhooks/ascend', express.raw({ type: 'application/json' }), (req, res) => {
    const signature = req.headers['x-ascend-signature'];
    const payload = req.body.toString();

    if (!verifyWebhook(payload, signature, WEBHOOK_SECRET)) {
        return res.status(401).send('Invalid signature');
    }

    const event = JSON.parse(payload);
    console.log(`Event: ${event.type}`);

    res.status(200).send('OK');
});
```

### Python

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, f"sha256={expected}")

# Flask example
@app.route('/webhooks/ascend', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-Ascend-Signature')
    payload = request.get_data()

    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return 'Invalid signature', 401

    event = request.get_json()
    print(f"Event: {event['type']}")

    return 'OK', 200
```

## Headers

Each webhook request includes:

| Header | Description |
|--------|-------------|
| `X-Ascend-Signature` | HMAC-SHA256 signature |
| `X-Ascend-Event` | Event type |
| `X-Ascend-Delivery` | Unique delivery ID |
| `X-Ascend-Timestamp` | Unix timestamp |

## Retry Policy

Webhooks are retried on failure:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate |
| 2 | 1 minute |
| 3 | 5 minutes |
| 4 | 30 minutes |
| 5 | 2 hours |

After 5 failed attempts, the webhook is marked as failed.

## Best Practices

### 1. Respond Quickly

Return 200 within 30 seconds. Process async if needed:

```typescript
app.post('/webhooks/ascend', (req, res) => {
    // Acknowledge immediately
    res.status(200).send('OK');

    // Process async
    processWebhookAsync(req.body);
});
```

### 2. Handle Duplicates

Events may be delivered multiple times. Use `id` for deduplication:

```typescript
const processedEvents = new Set();

function handleEvent(event) {
    if (processedEvents.has(event.id)) {
        return; // Already processed
    }

    processedEvents.add(event.id);
    // Process event...
}
```

### 3. Verify Signatures

Always verify webhook signatures in production.

## Testing Webhooks

### Send Test Event

```bash
curl -X POST https://pilot.owkai.app/api/api/webhooks/{webhook_id}/test \
  -H "Authorization: Bearer ask_live_xxxx"
```

### Local Development

Use tools like ngrok for local testing:

```bash
ngrok http 3000
# Use the ngrok URL as your webhook endpoint
```

## Next Steps

- [API Endpoints](/sdk/rest/endpoints) - REST API reference
- [SIEM Integration](/enterprise/siem) - Send events to SIEM
