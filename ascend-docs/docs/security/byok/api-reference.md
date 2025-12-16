---
sidebar_position: 3
title: API Reference
description: BYOK/CMK API endpoint documentation
---

# BYOK API Reference

Complete API reference for BYOK/CMK encryption endpoints.

## Authentication

All BYOK endpoints require authentication via Bearer token:

```bash
-H "Authorization: Bearer $ASCEND_TOKEN"
```

## Base URL

```
https://pilot.owkai.app/api/v1/byok
```

---

## Register Encryption Key

Register your AWS KMS Customer Managed Key with ASCEND.

```
POST /api/v1/byok/keys
```

### Request Body

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `key_arn` | string | **Yes** | Full ARN of your AWS KMS key |
| `key_alias` | string | No | Friendly alias for the key |
| `description` | string | No | Description of the key's purpose |

### Example Request

```bash
curl -X POST https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
    "key_alias": "ascend-production-key",
    "description": "Production encryption key for ASCEND BYOK"
  }'
```

### Response

```json
{
  "status": "success",
  "message": "Customer managed key registered successfully",
  "key_id": "byok_abc123xyz",
  "key_arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
  "key_alias": "ascend-production-key",
  "registration_time": "2025-12-16T10:30:00Z",
  "requires_waiver_acknowledgment": true
}
```

### Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Invalid ARN format | Key ARN doesn't match expected format |
| 403 | Key access denied | ASCEND cannot access the key |
| 409 | Key already registered | Organization already has a BYOK key |

<!-- VALIDATED:
  Source: routes/byok_routes.py:152
  Function: register_encryption_key
  Status: ✅ VERIFIED
-->

---

## Get Key Status

Get the current status of your registered encryption key.

```
GET /api/v1/byok/keys
```

### Example Request

```bash
curl https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response

```json
{
  "status": "active",
  "key_id": "byok_abc123xyz",
  "key_arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
  "key_alias": "ascend-production-key",
  "registered_at": "2025-12-16T10:30:00Z",
  "registered_by": "admin@company.com",
  "waiver_acknowledged": true,
  "waiver_acknowledged_at": "2025-12-16T10:35:00Z",
  "last_used": "2025-12-16T11:00:00Z",
  "encryption_count": 1250,
  "decryption_count": 890
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `pending_waiver` | Key registered, waiting for waiver acknowledgment |
| `active` | Key is active and in use |
| `disabled` | Key temporarily disabled |
| `revoked` | Key access has been revoked |

<!-- VALIDATED:
  Source: routes/byok_routes.py:236
  Function: get_encryption_key_status
  Status: ✅ VERIFIED
-->

---

## Revoke Encryption Key

Remove your BYOK key and revert to ASCEND-managed encryption.

```
DELETE /api/v1/byok/keys
```

### Example Request

```bash
curl -X DELETE https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response

```json
{
  "status": "success",
  "message": "BYOK key revoked. Data migration to ASCEND-managed encryption initiated.",
  "revoked_at": "2025-12-16T12:00:00Z",
  "migration_status": "in_progress",
  "estimated_completion": "2025-12-16T12:30:00Z"
}
```

:::warning
Revoking the key will initiate data migration. During migration, some operations may have increased latency.
:::

<!-- VALIDATED:
  Source: routes/byok_routes.py:265
  Function: revoke_encryption_key
  Status: ✅ VERIFIED
-->

---

## Rotate Data Encryption Key

Trigger rotation of the Data Encryption Key (DEK) wrapped by your CMK.

```
POST /api/v1/byok/keys/rotate
```

### Request Body

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `rotation_type` | string | No | `dek` (default) or `full` |
| `reason` | string | No | Reason for rotation (for audit) |

### Example Request

```bash
curl -X POST https://pilot.owkai.app/api/v1/byok/keys/rotate \
  -H "Authorization: Bearer $ASCEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rotation_type": "dek",
    "reason": "Scheduled quarterly rotation"
  }'
```

### Response

```json
{
  "status": "success",
  "message": "DEK rotation initiated",
  "rotation_id": "rot_xyz789",
  "initiated_at": "2025-12-16T10:30:00Z",
  "estimated_completion": "2025-12-16T10:35:00Z",
  "previous_dek_id": "dek_old123",
  "new_dek_id": "dek_new456"
}
```

<!-- VALIDATED:
  Source: routes/byok_routes.py:384
  Function: rotate_encryption_key
  Status: ✅ VERIFIED
-->

---

## Health Check

Check the health status of your BYOK configuration.

```
GET /api/v1/byok/health
```

### Example Request

```bash
curl https://pilot.owkai.app/api/v1/byok/health \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response (Healthy)

```json
{
  "status": "healthy",
  "key_status": "active",
  "cmk_accessible": true,
  "last_encryption": "2025-12-16T10:30:00Z",
  "last_decryption": "2025-12-16T10:29:55Z",
  "latency_ms": {
    "encrypt": 45,
    "decrypt": 38
  },
  "checks": {
    "cmk_access": "pass",
    "dek_valid": "pass",
    "kms_connection": "pass"
  }
}
```

### Response (Unhealthy)

```json
{
  "status": "unhealthy",
  "key_status": "inaccessible",
  "cmk_accessible": false,
  "error": "KMS access denied - check key policy",
  "last_successful_operation": "2025-12-16T09:00:00Z",
  "checks": {
    "cmk_access": "fail",
    "dek_valid": "unknown",
    "kms_connection": "pass"
  }
}
```

<!-- VALIDATED:
  Source: routes/byok_routes.py:321
  Function: byok_health_check
  Status: ✅ VERIFIED
-->

---

## Get Audit Log

Retrieve BYOK operation audit log.

```
GET /api/v1/byok/audit
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 100 | Number of entries to return |
| `offset` | int | 0 | Pagination offset |
| `start_date` | string | — | Filter by start date (ISO 8601) |
| `end_date` | string | — | Filter by end date (ISO 8601) |
| `operation` | string | — | Filter by operation type |

### Example Request

```bash
curl "https://pilot.owkai.app/api/v1/byok/audit?limit=50&operation=encrypt" \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response

```json
{
  "entries": [
    {
      "id": "audit_123",
      "timestamp": "2025-12-16T10:30:00Z",
      "operation": "encrypt",
      "status": "success",
      "key_id": "byok_abc123",
      "user": "system",
      "ip_address": "10.0.0.1",
      "latency_ms": 45,
      "metadata": {
        "data_type": "agent_action",
        "record_id": "act_xyz789"
      }
    }
  ],
  "total": 1250,
  "limit": 50,
  "offset": 0
}
```

### Operation Types

| Operation | Description |
|-----------|-------------|
| `encrypt` | Data encryption operation |
| `decrypt` | Data decryption operation |
| `rotate` | DEK rotation |
| `register` | Key registration |
| `revoke` | Key revocation |
| `health_check` | Health check |

<!-- VALIDATED:
  Source: routes/byok_routes.py:526
  Function: get_byok_audit_log
  Status: ✅ VERIFIED
-->

---

## Get Legal Waiver

Retrieve the legal waiver text that must be acknowledged before BYOK activation.

```
GET /api/v1/byok/legal-waiver
```

### Example Request

```bash
curl https://pilot.owkai.app/api/v1/byok/legal-waiver \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response

```json
{
  "waiver_version": "1.0",
  "effective_date": "2025-01-01",
  "title": "BYOK/CMK Encryption Legal Waiver",
  "content": "By enabling Bring Your Own Key (BYOK) encryption...",
  "terms": [
    "I understand that deleting my CMK will result in permanent, unrecoverable data loss",
    "I understand that revoking ASCEND's access to my CMK will make data unreadable",
    "I accept full responsibility for the availability and security of my CMK",
    "I acknowledge that ASCEND cannot recover data if my CMK becomes inaccessible"
  ],
  "requires_acknowledgment": true
}
```

<!-- VALIDATED:
  Source: routes/byok_routes.py:579
  Function: get_legal_waiver
  Status: ✅ VERIFIED
-->

---

## Acknowledge Legal Waiver

Acknowledge the legal waiver to activate BYOK encryption.

```
POST /api/v1/byok/legal-waiver/acknowledge
```

### Request Body

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `acknowledged` | boolean | **Yes** | Must be `true` |
| `acknowledged_by` | string | **Yes** | Email of person acknowledging |
| `acknowledged_terms` | array | No | Specific terms acknowledged |

### Example Request

```bash
curl -X POST https://pilot.owkai.app/api/v1/byok/legal-waiver/acknowledge \
  -H "Authorization: Bearer $ASCEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "acknowledged": true,
    "acknowledged_by": "security-admin@company.com",
    "acknowledged_terms": [
      "I understand that deleting my CMK will result in permanent data loss",
      "I understand that revoking ASCEND access will make data unreadable",
      "I accept responsibility for CMK availability and security"
    ]
  }'
```

### Response

```json
{
  "status": "success",
  "message": "Legal waiver acknowledged. BYOK encryption is now active.",
  "acknowledged_at": "2025-12-16T10:35:00Z",
  "acknowledged_by": "security-admin@company.com",
  "waiver_version": "1.0",
  "byok_status": "active"
}
```

<!-- VALIDATED:
  Source: routes/byok_routes.py:607
  Function: acknowledge_legal_waiver
  Status: ✅ VERIFIED
-->

---

## Get Waiver Status

Check if the legal waiver has been acknowledged.

```
GET /api/v1/byok/legal-waiver/status
```

### Example Request

```bash
curl https://pilot.owkai.app/api/v1/byok/legal-waiver/status \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Response

```json
{
  "acknowledged": true,
  "acknowledged_at": "2025-12-16T10:35:00Z",
  "acknowledged_by": "security-admin@company.com",
  "waiver_version": "1.0",
  "current_waiver_version": "1.0",
  "requires_reacknowledgment": false
}
```

<!-- VALIDATED:
  Source: routes/byok_routes.py:700
  Function: get_legal_waiver_status
  Status: ✅ VERIFIED
-->

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `BYOK_001` | 400 | Invalid key ARN format |
| `BYOK_002` | 403 | Cannot access CMK - check key policy |
| `BYOK_003` | 409 | Organization already has BYOK key |
| `BYOK_004` | 400 | Waiver not acknowledged |
| `BYOK_005` | 404 | No BYOK key registered |
| `BYOK_006` | 503 | KMS service unavailable |
| `BYOK_007` | 500 | Encryption operation failed |
| `BYOK_008` | 500 | Decryption operation failed |

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| `POST /keys` | 5/hour |
| `GET /keys` | 100/minute |
| `DELETE /keys` | 1/hour |
| `POST /keys/rotate` | 10/hour |
| `GET /health` | 60/minute |
| `GET /audit` | 60/minute |

## Next Steps

- [Setup Guide](./setup-guide) — Step-by-step setup instructions
- [Troubleshooting](./troubleshooting) — Common issues and solutions
- [BYOK Overview](./) — Return to overview
