---
Document ID: ASCEND-START-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Authentication

OW-AI Authorization Center uses API key authentication for SDK and agent integrations.

## Authentication Method

**API Keys** are the primary authentication method for server-to-server communication and SDK usage.

| Method | Use Case | Header |
|--------|----------|--------|
| API Key | SDK, Agents, Automation | `Authorization: Bearer {api_key}` |
| Session Token | Web Dashboard | `Cookie: session_token` |

## Generating an API Key

### Via Dashboard (Recommended)

1. Log in to [OW-AI Dashboard](https://pilot.owkai.app)
2. Navigate to **Settings** → **API Keys**
3. Click **Generate New Key**
4. Provide a name (e.g., "Production Agent Key")
5. Copy the key immediately (shown only once)

**Endpoint:** `POST /api/keys/generate`
**Source:** `/ow-ai-backend/routes/api_key_routes.py:163-274`

### Via API (Programmatic)

```python
import requests

# Must authenticate with existing session or API key
headers = {
    "Authorization": f"Bearer {existing_key}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://pilot.owkai.app/api/keys/generate",
    headers=headers,
    json={
        "name": "Production Agent Key",
        "description": "API key for production agent fleet",
        "expires_in_days": 90
    }
)

key_data = response.json()
print(f"New API Key: {key_data['api_key']}")  # Save this immediately
print(f"Key Prefix: {key_data['key_prefix']}")
```

> **Important: Critical Security Notice**
> API keys are shown **only once** at generation time. The full key is never stored in plaintext on the server (SHA-256 hashed with salt). If you lose the key, you must generate a new one.

**Source:** `/ow-ai-backend/routes/api_key_routes.py:87-117` (cryptographic key generation)


## API Key Format

API keys use a role-based prefix for easy identification:

```
owkai_{role}_{random_token}
```

Examples:
- `owkai_admin_tUsLxYz123abcDEF...` (16+ characters prefix)
- `owkai_user_aB3dEfG789hijKLM...`

**Implementation:** `/ow-ai-backend/routes/api_key_routes.py:87-117`

The random token uses 256-bit cryptographic entropy via `secrets.token_urlsafe(32)`.

## Using API Keys

### Python

```python
import os
import requests

# Method 1: Environment variable (recommended)
api_key = os.getenv('OWKAI_API_KEY')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Method 2: Direct initialization
client = OWKAIClient(api_key="owkai_admin_xxxx")

# Submit action with authentication
response = requests.post(
    "https://pilot.owkai.app/api/v1/actions/submit",
    headers=headers,
    json={
        "agent_id": "my-agent",
        "action_type": "data_access",
        "description": "Access customer records",
        "tool_name": "database_query"
    }
)
```

### Node.js

```javascript
const axios = require('axios');

// Method 1: Environment variable (recommended)
const apiKey = process.env.OWKAI_API_KEY;
const headers = {
  'Authorization': `Bearer ${apiKey}`,
  'Content-Type': 'application/json'
};

// Submit action with authentication
const response = await axios.post(
  'https://pilot.owkai.app/api/v1/actions/submit',
  {
    agent_id: 'my-agent',
    action_type: 'data_access',
    description: 'Access customer records',
    tool_name: 'database_query'
  },
  { headers }
);
```

### cURL

```bash
# Set environment variable
export OWKAI_API_KEY="owkai_admin_xxxxxxxxxxxx"

# Submit action
curl -X POST https://pilot.owkai.app/api/v1/actions/submit \
  -H "Authorization: Bearer $OWKAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "action_type": "data_access",
    "description": "Access customer records",
    "tool_name": "database_query"
  }'
```

## Authentication Flow

### SDK Authentication

```
┌──────────┐                          ┌──────────────┐
│   SDK    │                          │   OW-AI API  │
└────┬─────┘                          └──────┬───────┘
     │                                       │
     │  1. POST /api/v1/actions/submit │
     │     Authorization: Bearer owkai_admin_xxx │
     │────────────────────────────────────────►│
     │                                       │
     │  2. Validate API key                │
     │     - Lookup key_hash in database   │
     │     - Verify not revoked            │
     │     - Check organization_id         │
     │                                  ◄──┤
     │                                       │
     │  3. Return authorization decision    │
     │◄────────────────────────────────────│
     │   { status: "approved", risk_score: 35 } │
```

**Authentication Implementation:**
- API Key Validation: `/ow-ai-backend/dependencies_api_keys.py`
- Dual Auth (JWT + API Key): `/ow-ai-backend/routes/authorization_routes.py:2206` (SEC-020)

## Managing API Keys

### List Keys

View all your API keys (masked for security):

**Endpoint:** `GET /api/keys/list`
**Source:** `/ow-ai-backend/routes/api_key_routes.py:280-336`

```python
response = requests.get(
    "https://pilot.owkai.app/api/keys/list",
    headers={"Authorization": f"Bearer {api_key}"}
)

keys = response.json()
for key in keys['keys']:
    print(f"Name: {key['name']}")
    print(f"Prefix: {key['key_prefix']}")  # Only first 16 chars shown
    print(f"Created: {key['created_at']}")
    print(f"Last Used: {key['last_used_at']}")
    print(f"Status: {'Active' if key['is_active'] else 'Revoked'}")
```

### Revoke Key

Immediately revoke an API key (soft delete with audit trail):

**Endpoint:** `DELETE /api/keys/{key_id}/revoke`
**Source:** `/ow-ai-backend/routes/api_key_routes.py:342-418`

```python
response = requests.delete(
    f"https://pilot.owkai.app/api/keys/{key_id}/revoke",
    headers={"Authorization": f"Bearer {api_key}"},
    params={"reason": "Key rotation - replacing with new key"}
)

if response.status_code == 200:
    print(f"Key revoked at: {response.json()['revoked_at']}")
```

### Key Usage Statistics

Monitor API key usage for security auditing:

**Endpoint:** `GET /api/keys/{key_id}/usage`
**Source:** `/ow-ai-backend/routes/api_key_routes.py:425-503`

```python
response = requests.get(
    f"https://pilot.owkai.app/api/keys/{key_id}/usage",
    headers={"Authorization": f"Bearer {api_key}"}
)

usage = response.json()
print(f"Total Requests: {usage['statistics']['total_requests']}")
print(f"Success Rate: {usage['statistics']['success_rate']}%")
print(f"Last Used: {usage['statistics']['last_used_at']}")

# Recent activity log
for activity in usage['recent_activity']:
    print(f"{activity['timestamp']}: {activity['method']} {activity['endpoint']} - {activity['status']}")
```

## Security Best Practices

### 1. Store Keys in Environment Variables

```bash
# .env file (never commit to git)
OWKAI_API_KEY=owkai_admin_xxxxxxxxxxxx
OWKAI_API_URL=https://pilot.owkai.app
```

```python
# Load in application
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OWKAI_API_KEY')
```

### 2. Rotate Keys Regularly

**Recommended:** Rotate keys every 90 days

```python
# Generate new key before revoking old one (zero-downtime rotation)
new_key_response = client.generate_api_key(
    name="Production Key v2",
    expires_in_days=90
)

# Update application with new key
update_production_config(new_key_response['api_key'])

# Wait for deployment to complete
wait_for_deployment()

# Revoke old key
client.revoke_api_key(old_key_id, reason="Scheduled key rotation")
```

### 3. Never Expose Keys in Client-Side Code

```javascript
// WRONG - Never do this
const apiKey = 'owkai_admin_xxxxxxxxxxxx';
fetch('https://pilot.owkai.app/api/v1/actions/submit', {
  headers: { 'Authorization': `Bearer ${apiKey}` }
});

// RIGHT - Use backend proxy
fetch('/api/my-backend-proxy', {
  method: 'POST',
  body: JSON.stringify(action)
});
```

### 4. Monitor Key Usage

Set up alerts for suspicious activity:

```python
def check_key_usage(key_id):
    usage = client.get_key_usage(key_id)

    # Alert on high error rate
    if usage['statistics']['success_rate'] < 90:
        send_alert(f"API key {key_id} has low success rate")

    # Alert on unusual activity spikes
    recent_requests = len(usage['recent_activity'])
    if recent_requests > 1000:  # Per hour
        send_alert(f"API key {key_id} showing unusual activity")
```

## Security Implementation

### Key Storage (Enterprise Grade)

**Source:** `/ow-ai-backend/routes/api_key_routes.py:87-117`

Keys are stored using SHA-256 hashing with per-key random salt:

```python
# Generation (never stored in plaintext)
raw_key = secrets.token_urlsafe(32)  # 256-bit entropy
full_key = f"owkai_{role}_{raw_key}"
salt = secrets.token_hex(16)
key_hash = hashlib.sha256((full_key + salt).encode()).hexdigest()

# Only key_hash and salt stored in database
# Full key shown ONCE at generation
```

### Multi-Tenant Isolation

**Source:** `/ow-ai-backend/routes/authorization_routes.py:2297-2306` (SEC-020)

All API keys are scoped to an organization:

```python
# Action submission automatically scopes to organization
action = AgentAction(
    agent_id=data["agent_id"],
    organization_id=org_id,  # From authenticated API key
    # ... other fields
)

# Users can ONLY access their organization's data
```

### Audit Trail

Every API key operation is logged to immutable audit log:

**Source:** `/ow-ai-backend/routes/api_key_routes.py:120-157`

```python
# Automatic audit logging
audit_log = ImmutableAuditLog(
    user_id=user_id,
    action="api_key_generated",
    resource_type="api_key",
    resource_id=key_id,
    outcome="success",
    metadata={
        "key_prefix": key_prefix,
        "key_name": key_name
    }
)
```

## Troubleshooting

### Invalid API Key

```
Error: HTTP 401 - Authentication required
```

**Solution:** Verify your API key is correct and hasn't been revoked. Check with `GET /api/keys/list`.

### Expired Key

```
Error: HTTP 403 - API key expired
```

**Solution:** Generate a new API key. Keys expire based on `expires_in_days` set during generation.

### Wrong Organization

```
Error: HTTP 404 - Action not found
```

**Solution:** Verify you're using the correct API key for your organization. API keys are organization-scoped.

### Rate Limited

```
Error: HTTP 429 - Rate limit exceeded
```

**Solution:** Check your rate limit configuration with `GET /api/keys/{key_id}/usage`. Default: 1000 requests/hour.

**Rate Limit Implementation:** `/ow-ai-backend/routes/api_key_routes.py:217-231`

## Compliance

API key management meets enterprise security standards:

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| **PCI-DSS 8.3.1** | Strong cryptography | SHA-256 with random salt |
| **HIPAA 164.312(d)** | Access controls | Organization-scoped keys |
| **SOC 2 CC6.1** | Audit trail | Immutable audit logs |
| **NIST 800-63B** | Key rotation | Configurable expiration |

**Source:** `/ow-ai-backend/routes/api_key_routes.py:1-10` (compliance documentation)

## Next Steps

- [First Agent Action](/getting-started/first-agent-action) - Submit your first action
- [Integration Examples](https://github.com/OW-AI/ow-ai-backend/tree/main/integration-examples) - Working code examples
- [API Reference](/api/overview) - Complete endpoint documentation
