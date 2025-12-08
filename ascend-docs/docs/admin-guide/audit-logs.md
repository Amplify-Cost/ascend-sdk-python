---
sidebar_position: 7
title: Audit Logs
description: View and export immutable audit trails
---

# Audit Logs

Access immutable audit logs with hash-chaining, integrity verification, and compliance-ready exports.

## Overview

The immutable audit system provides cryptographically secured logging with WORM (Write Once Read Many) guarantees for compliance with financial regulations.

**Source**: `ow-ai-backend/routes/audit_routes.py`, `services/immutable_audit_service.py`

**Compliance**: SOX, HIPAA, PCI-DSS 10.2, SOC 2 AU-6, NIST AU-6/AU-7

## Audit Architecture

### Hash-Chaining

```
┌─────────────────────────────────────────────────────────────┐
│                   Hash Chain Structure                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Record 1          Record 2          Record 3               │
│  ┌────────┐        ┌────────┐        ┌────────┐            │
│  │content │───────▶│content │───────▶│content │            │
│  │hash    │        │hash    │        │hash    │            │
│  ├────────┤        ├────────┤        ├────────┤            │
│  │chain   │───────▶│previous│───────▶│previous│            │
│  │hash    │        │hash    │        │hash    │            │
│  └────────┘        └────────┘        └────────┘            │
│                                                              │
│  ANY modification breaks the chain and is detectable         │
└─────────────────────────────────────────────────────────────┘
```

### Security Features

| Feature | Implementation |
|---------|----------------|
| Content Hash | SHA-256 of record data |
| Chain Hash | SHA-256(content_hash + previous_chain_hash) |
| Immutability | Append-only, no updates or deletes |
| Integrity Check | Automated chain verification |

## Viewing Audit Logs

### List Audit Logs

```bash
curl "https://pilot.owkai.app/api/audit/logs?limit=100&offset=0" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "total": 1547,
  "limit": 100,
  "offset": 0,
  "logs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "sequence_number": 1547,
      "timestamp": "2025-01-15T14:30:00Z",
      "event_type": "agent_action_submitted",
      "actor_id": "user_123",
      "resource_type": "agent_action",
      "action": "create",
      "risk_level": "MEDIUM"
    }
  ]
}
```

### Audit Log Fields

| Field | Description |
|-------|-------------|
| `id` | UUID primary key |
| `sequence_number` | Sequential counter |
| `timestamp` | Event timestamp |
| `event_type` | Event classification |
| `actor_id` | Who performed action |
| `resource_type` | What was affected |
| `resource_id` | Specific resource ID |
| `action` | What was done |
| `outcome` | SUCCESS or FAILURE |
| `risk_level` | LOW, MEDIUM, HIGH, CRITICAL |
| `compliance_tags` | Applicable frameworks |

## Creating Audit Entries

### Log an Event

```bash
curl -X POST https://pilot.owkai.app/api/audit/log \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "data_access",
    "actor_id": "agent_financial_001",
    "resource_type": "customer_data",
    "resource_id": "cust_12345",
    "action": "read",
    "event_data": {
      "fields_accessed": ["name", "email"],
      "record_count": 1
    },
    "risk_level": "MEDIUM",
    "compliance_tags": ["GDPR", "PCI"]
  }'
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "sequence_number": 1548,
  "timestamp": "2025-01-15T14:31:00Z",
  "content_hash": "a1b2c3d4e5f6...",
  "status": "created"
}
```

## Integrity Verification

### Verify Chain Integrity

```bash
curl -X POST https://pilot.owkai.app/api/audit/verify-integrity \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Response:**

```json
{
  "id": "check_001",
  "check_time": "2025-01-15T14:35:00Z",
  "status": "VALID",
  "total_records": 1548,
  "check_duration_ms": 450,
  "records_per_second": 3440
}
```

### Verification Status

| Status | Description |
|--------|-------------|
| `VALID` | All hashes verified |
| `TAMPERED` | Content hash mismatch detected |
| `BROKEN` | Chain hash mismatch detected |

## Exporting Audit Logs

### Export to CSV

```bash
curl "https://pilot.owkai.app/api/audit/export/csv?\
start_date=2025-01-01T00:00:00Z&\
end_date=2025-01-31T23:59:59Z&\
event_type=agent_action_submitted" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -o audit_export.csv
```

### Export to PDF

```bash
curl "https://pilot.owkai.app/api/audit/export/pdf?\
start_date=2025-01-01T00:00:00Z&\
end_date=2025-01-31T23:59:59Z" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -o audit_report.pdf
```

### Export Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `start_date` | Start timestamp (ISO) | `2025-01-01T00:00:00Z` |
| `end_date` | End timestamp (ISO) | `2025-01-31T23:59:59Z` |
| `event_type` | Filter by event | `agent_action_submitted` |
| `actor_id` | Filter by actor | `user_123` |
| `resource_type` | Filter by resource | `customer_data` |

### CSV Columns

| Column | Description |
|--------|-------------|
| Sequence Number | Record sequence |
| Timestamp | Event time |
| Event Type | Classification |
| Actor ID | Who performed |
| Resource Type | What affected |
| Resource ID | Specific ID |
| Action | What done |
| Risk Level | Severity |
| Compliance Tags | Frameworks |
| Content Hash | Integrity hash |
| Chain Hash | Chain integrity |
| Retention Until | Retention date |
| Legal Hold | Hold status |
| IP Address | Source IP |

### PDF Report Contents

- Report metadata (generated date, user, record count)
- Hash chain integrity status
- Compliance framework badges
- Formatted data table
- Digital signature notice

## Retention Policies

### Compliance-Based Retention

| Framework | Retention Period |
|-----------|------------------|
| SOX | 7 years |
| HIPAA | 6 years |
| PCI-DSS | 1 year |
| GDPR | 6 years |
| CCPA | 3 years |
| FERPA | 5 years |
| Default | 7 years |

### Retention Calculation

Longest applicable period is used:

```python
retention_until = max(
    framework_retention for framework in compliance_tags
)
```

## Legal Hold

Audit records can be placed on legal hold:

| Field | Description |
|-------|-------------|
| `legal_hold` | Boolean hold status |
| `legal_hold_by` | Who applied hold |
| `legal_hold_reason` | Why held |

Records on legal hold:
- Cannot be deleted
- Retention period extended indefinitely
- Marked in exports

## Event Types

### System Events

| Event | Description |
|-------|-------------|
| `user_login` | User authentication |
| `user_logout` | User session end |
| `user_invited` | New user added |
| `user_removed` | User disabled |
| `user_role_updated` | Permission change |

### Agent Events

| Event | Description |
|-------|-------------|
| `agent_registered` | New agent added |
| `agent_action_submitted` | Action submitted |
| `agent_action_approved` | Action approved |
| `agent_action_denied` | Action denied |
| `agent_suspended` | Agent disabled |

### Security Events

| Event | Description |
|-------|-------------|
| `api_key_generated` | New key created |
| `api_key_revoked` | Key disabled |
| `mfa_enabled` | MFA activated |
| `mfa_disabled` | MFA removed |
| `policy_violation` | Rule triggered |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audit/health` | GET | Audit system health |
| `/api/audit/log` | POST | Create audit entry |
| `/api/audit/logs` | GET | List audit logs |
| `/api/audit/verify-integrity` | POST | Verify chain |
| `/api/audit/export/csv` | GET | Export CSV |
| `/api/audit/export/pdf` | GET | Export PDF |

**Source**: `ow-ai-backend/routes/audit_routes.py`

## Best Practices

1. **Regular verification**: Run integrity checks weekly
2. **Export backups**: Archive exports to cold storage
3. **Monitor anomalies**: Alert on unusual event patterns
4. **Apply legal holds**: Hold records for litigation
5. **Document retention**: Map frameworks to data types
6. **Review exports**: Verify export completeness

## Troubleshooting

### Integrity check shows BROKEN

**Cause**: Database corruption or manual modification.

**Action**:
1. Identify first broken sequence number
2. Investigate database logs
3. Contact support for remediation

### Export timeout

**Cause**: Large date range or high record count.

**Solution**: Use narrower date ranges; filter by event type.

### Missing audit entries

**Cause**: Service interruption during event.

**Solution**: Check application logs; events should be idempotent.

---

*Source: [audit_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/audit_routes.py), [immutable_audit_service.py](https://github.com/owkai/ow-ai-backend/blob/main/services/immutable_audit_service.py)*
