# BYOK API Reference

## Base URL

```
https://api.ascend.owkai.app/api/v1/byok
```

## Authentication

All endpoints require authentication via:
- **Dashboard Users**: JWT token in `Authorization: Bearer <token>` header
- **API Keys**: `X-API-Key: <api_key>` header

## Endpoints

---

### Register Encryption Key

Register a customer-managed encryption key (CMK) for BYOK encryption.

**Endpoint:** `POST /api/v1/byok/keys`

**Prerequisites:**
1. Create a KMS key in your AWS account
2. Apply the key policy granting ASCEND access (see setup guide)
3. Key must be symmetric encryption (not asymmetric)

**Request Body:**
```json
{
  "cmk_arn": "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012",
  "cmk_alias": "ascend-encryption-key"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cmk_arn` | string | Yes | Full ARN of your KMS key |
| `cmk_alias` | string | No | Human-readable alias for the key |

**Response (201 Created):**
```json
{
  "organization_id": 42,
  "cmk_arn": "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012",
  "cmk_alias": "ascend-encryption-key",
  "status": "active",
  "status_reason": null,
  "last_validated_at": "2024-01-15T10:30:00Z",
  "last_rotation_at": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | Invalid CMK ARN format |
| 400 | Key validation failed (check key policy) |
| 401 | Authentication required |
| 409 | Organization already has a registered key |

**Example:**
```bash
curl -X POST "https://api.ascend.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cmk_arn": "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012",
    "cmk_alias": "ascend-key"
  }'
```

---

### Get Key Status

Retrieve the current status of your registered encryption key.

**Endpoint:** `GET /api/v1/byok/keys`

**Response (200 OK):**
```json
{
  "organization_id": 42,
  "cmk_arn": "arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012",
  "cmk_alias": "ascend-encryption-key",
  "status": "active",
  "status_reason": null,
  "last_validated_at": "2024-01-15T14:00:00Z",
  "last_rotation_at": "2024-01-10T08:00:00Z",
  "created_at": "2024-01-01T10:30:00Z"
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| `active` | Key is healthy and operational |
| `validating` | Key access is being verified |
| `error` | Key validation failed |
| `revoked` | Key access has been revoked |

**Response (204 No Content):**
Returned when no BYOK key is configured for the organization.

---

### Delete/Revoke Key

Remove the registered encryption key from ASCEND.

**Endpoint:** `DELETE /api/v1/byok/keys`

**Warning:** After deletion:
- Future data will use platform default encryption
- Previously encrypted data remains encrypted with the old DEK
- You should export data before deleting if migration is needed

**Response (200 OK):**
```json
{
  "message": "Encryption key removed successfully",
  "revoked_at": "2024-01-15T15:00:00Z"
}
```

---

### Check Key Health

Perform a health check on your registered CMK.

**Endpoint:** `GET /api/v1/byok/health`

**Response (200 OK) - BYOK Enabled:**
```json
{
  "byok_enabled": true,
  "status": "healthy",
  "cmk_accessible": true,
  "last_validated_at": "2024-01-15T14:00:00Z",
  "cmk_arn_prefix": "arn:aws:kms:us-east-2:123456******",
  "dek_version": 3
}
```

**Response (200 OK) - BYOK Not Enabled:**
```json
{
  "byok_enabled": false,
  "status": null,
  "cmk_accessible": null,
  "last_validated_at": null,
  "cmk_arn_prefix": null,
  "dek_version": null
}
```

**Health Status Values:**

| Status | Description |
|--------|-------------|
| `healthy` | CMK is accessible, all operations normal |
| `degraded` | CMK accessible but with warnings |
| `unhealthy` | CMK not accessible, operations blocked |

---

### Manual Key Rotation

Trigger a manual rotation of the Data Encryption Key (DEK).

**Endpoint:** `POST /api/v1/byok/keys/rotate`

**When to Use:**
- After rotating your CMK in AWS KMS
- As part of compliance key rotation schedule
- After a suspected key compromise

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Key rotation completed successfully",
  "new_dek_version": 4,
  "rotated_at": "2024-01-15T16:00:00Z"
}
```

**Note:** Automatic rotation detection runs every 15 minutes. Manual rotation is only needed for immediate rotation requirements.

---

### View Audit Log

Retrieve the BYOK audit log for your organization.

**Endpoint:** `GET /api/v1/byok/audit`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Max entries to return (1-500) |
| `offset` | int | 0 | Pagination offset |
| `operation` | string | null | Filter by operation type |

**Response (200 OK):**
```json
{
  "entries": [
    {
      "id": 1234,
      "operation": "encrypt",
      "success": true,
      "error_message": null,
      "created_at": "2024-01-15T14:30:00Z"
    },
    {
      "id": 1233,
      "operation": "dek_generated",
      "success": true,
      "error_message": null,
      "created_at": "2024-01-15T14:00:00Z"
    },
    {
      "id": 1232,
      "operation": "access_denied",
      "success": false,
      "error_message": "Key revoked by customer",
      "created_at": "2024-01-15T13:45:00Z"
    }
  ],
  "total_count": 156
}
```

**Operation Types:**

| Operation | Description |
|-----------|-------------|
| `key_registered` | CMK was registered |
| `key_revoked` | CMK was removed |
| `dek_generated` | New DEK was created |
| `encrypt` | Data was encrypted |
| `decrypt` | Data was decrypted |
| `access_denied` | CMK access was blocked |
| `health_check` | Health check performed |
| `rotation_detected` | CMK rotation detected |

---

## Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| `POST /keys` | 10/hour |
| `DELETE /keys` | 10/hour |
| `POST /keys/rotate` | 60/hour |
| `GET /keys` | 100/minute |
| `GET /health` | 100/minute |
| `GET /audit` | 100/minute |

---

## SDK Examples

### Python

```python
from ascend_sdk import AscendClient

client = AscendClient(api_key="your_api_key")

# Register CMK
result = client.byok.register_key(
    cmk_arn="arn:aws:kms:us-east-2:123456789012:key/...",
    cmk_alias="my-ascend-key"
)

# Check health
health = client.byok.health_check()
print(f"BYOK Status: {health.status}")

# View audit log
audit = client.byok.get_audit_log(limit=10)
for entry in audit.entries:
    print(f"{entry.operation}: {entry.success}")
```

### JavaScript/TypeScript

```typescript
import { AscendClient } from '@owkai/ascend-sdk';

const client = new AscendClient({ apiKey: 'your_api_key' });

// Register CMK
const result = await client.byok.registerKey({
  cmkArn: 'arn:aws:kms:us-east-2:123456789012:key/...',
  cmkAlias: 'my-ascend-key'
});

// Check health
const health = await client.byok.healthCheck();
console.log(`BYOK Status: ${health.status}`);
```

---

*Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP, NIST 800-53*
