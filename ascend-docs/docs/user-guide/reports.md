---
sidebar_position: 7
title: Reports
description: Executive briefs and compliance reporting
---

# Reports

Generate AI-powered executive briefs and compliance reports with automated scheduling and distribution.

## Overview

The Executive Brief system provides automated security summaries, threat analysis, and actionable recommendations for stakeholders.

**Source**: `ow-ai-backend/routes/executive_brief_routes.py` (SEC-065)

**Compliance**: SOC 2 AU-6, SOC 2 AU-7, NIST AU-6, PCI-DSS 10.6

## Executive Briefs

### Brief Contents

Each executive brief includes:

| Section | Description |
|---------|-------------|
| **Summary** | High-level threat overview |
| **Key Metrics** | Threats detected, prevented, cost savings |
| **Recommendations** | Prioritized action items |
| **Risk Assessment** | Overall security posture |
| **Distribution List** | Recipients |

### Brief Response Structure

```javascript
{
  "brief_id": "brief_20250115_a1b2c3",
  "generated_at": "2025-01-15T10:00:00Z",
  "generated_by": "admin@company.com",
  "expires_at": "2025-01-16T10:00:00Z",
  "time_period": "24h",
  "alert_count": 47,
  "high_priority_count": 12,
  "critical_count": 3,
  "summary": "Security posture remains strong with 47 alerts processed...",
  "key_metrics": {
    "threats_detected": 47,
    "threats_prevented": 44,
    "cost_savings": "$150,000",
    "system_accuracy": "93.6%"
  },
  "recommendations": [
    {
      "priority": "high",
      "action": "Review elevated database access patterns",
      "timeframe": "24 hours",
      "owner": "Security Team"
    }
  ],
  "risk_assessment": "MEDIUM",
  "generation_method": "ai_generated",
  "is_current": true,
  "version": 1
}
```

## Getting Latest Brief

Retrieve the current cached executive brief:

```bash
curl https://pilot.owkai.app/api/executive-briefs/latest \
  -H "Authorization: Bearer owkai_your_api_key"
```

**Performance**: &lt;100ms (indexed query)

### Behavior

1. Returns cached brief if valid
2. If no cached brief exists, generates new one
3. Records view in audit trail

## Regenerating Briefs

Force regeneration with fresh data:

```bash
curl -X POST https://pilot.owkai.app/api/executive-briefs/regenerate \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "time_period": "24h",
    "force": false
  }'
```

### Time Periods

| Period | Description |
|--------|-------------|
| `24h` | Last 24 hours |
| `7d` | Last 7 days |
| `30d` | Last 30 days |
| `90d` | Last 90 days |

### Rate Limiting

- **Cooldown**: 5 minutes between regenerations
- **Force**: Admin-only bypass for cooldown

## Checking Cooldown

Before regenerating, check if allowed:

```bash
curl https://pilot.owkai.app/api/executive-briefs/cooldown \
  -H "Authorization: Bearer owkai_your_api_key"
```

**Response:**

```json
{
  "can_regenerate": true,
  "seconds_remaining": 0,
  "message": "Regeneration available"
}
```

Or if rate limited:

```json
{
  "can_regenerate": false,
  "seconds_remaining": 180,
  "message": "Please wait 180 seconds before regenerating"
}
```

## Brief History

Retrieve historical briefs for audit purposes:

```bash
curl "https://pilot.owkai.app/api/executive-briefs/history?limit=10&offset=0" \
  -H "Authorization: Bearer owkai_your_api_key"
```

**Response:**

```json
{
  "briefs": [
    {
      "brief_id": "brief_20250115_a1b2c3",
      "generated_at": "2025-01-15T10:00:00Z",
      "time_period": "24h",
      "alert_count": 47,
      "is_current": true
    },
    {
      "brief_id": "brief_20250114_d4e5f6",
      "generated_at": "2025-01-14T10:00:00Z",
      "time_period": "24h",
      "alert_count": 52,
      "is_current": false
    }
  ],
  "total": 2,
  "limit": 10,
  "offset": 0
}
```

## Getting Specific Brief

Retrieve a brief by ID:

```bash
curl https://pilot.owkai.app/api/executive-briefs/{brief_id} \
  -H "Authorization: Bearer owkai_your_api_key"
```

Use for:
- Viewing historical briefs
- Sharing specific briefings
- Audit record access

## Key Metrics (SEC-066)

All briefs use the Unified Metrics Engine for consistent calculations:

### Threat Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| `threats_detected` | Total alerts in period | COUNT(alerts) |
| `threats_prevented` | Acknowledged alerts | COUNT(acknowledged) |
| `threats_pending` | Unacknowledged alerts | COUNT(pending) |

### Financial Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| `cost_savings` | Estimated savings | threats_prevented × $50,000 |

### Performance Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| `accuracy_rate` | Resolution rate | (acknowledged / total) × 100 |
| `false_positive_rate` | Dismissed alerts | (dismissed / total) × 100 |

## Recommendations

Briefs include prioritized recommendations:

### Recommendation Structure

```javascript
{
  "priority": "high",
  "action": "Review elevated database access patterns",
  "timeframe": "24 hours",
  "owner": "Security Team"
}
```

### Priority Levels

| Priority | Response Time | Description |
|----------|---------------|-------------|
| **Critical** | Immediate | Active threat requiring response |
| **High** | < 24 hours | Elevated risk needing attention |
| **Medium** | < 7 days | Should be addressed soon |
| **Low** | As scheduled | Monitor and review |

## Risk Assessment

Overall security posture evaluation:

| Level | Score Range | Description |
|-------|-------------|-------------|
| **Critical** | 80-100 | Immediate action required |
| **High** | 60-79 | Elevated risk |
| **Medium** | 40-59 | Moderate risk |
| **Low** | 0-39 | Acceptable risk |

## Brief Metadata

Each brief includes metadata for audit:

| Field | Description |
|-------|-------------|
| `organization_id` | Multi-tenant isolation |
| `has_activity` | Whether org has alerts |
| `llm_model` | AI model used |
| `generation_time_ms` | Generation duration |

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/executive-briefs/latest` | GET | Get latest brief |
| `/api/executive-briefs/regenerate` | POST | Regenerate brief |
| `/api/executive-briefs/cooldown` | GET | Check cooldown |
| `/api/executive-briefs/history` | GET | Get brief history |
| `/api/executive-briefs/{id}` | GET | Get specific brief |
| `/api/executive-briefs/generate` | POST | Legacy endpoint |

**Source**: `ow-ai-backend/routes/executive_brief_routes.py`

## Scheduled Reports

### Creating a Report Schedule

```bash
curl -X POST https://pilot.owkai.app/api/users/reports/scheduled \
  -H "Authorization: Bearer owkai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Executive Summary",
    "report_type": "executive_dashboard",
    "schedule": "0 9 * * 1",
    "format": "pdf",
    "recipients": ["exec@company.com"],
    "enabled": true
  }'
```

### Report Types

| Type | Description |
|------|-------------|
| `executive_dashboard` | High-level KPIs and trends |
| `risk_analysis` | Detailed risk breakdown |
| `compliance_summary` | Compliance scores and gaps |
| `agent_performance` | Per-agent metrics |
| `audit_summary` | Audit log summary |

### Schedule Format (Cron)

```
0 9 * * 1  = Every Monday at 9 AM
0 9 * * *  = Every day at 9 AM
0 9 1 * *  = First of month at 9 AM
```

## Best Practices

1. **Generate daily briefs**: Keep stakeholders informed
2. **Review recommendations**: Prioritize by urgency
3. **Track history**: Maintain audit compliance
4. **Distribute appropriately**: Use distribution list feature
5. **Monitor cost savings**: Demonstrate ROI

## Troubleshooting

### Brief generation failing

**Solution**: Check organization has alert data; empty state returns minimal brief.

### Rate limit errors (429)

**Solution**: Wait for cooldown period; check `/cooldown` endpoint.

### Metrics showing zero

**Solution**: Verify alerts exist in time period; check organization_id filtering.

### Brief not updating

**Solution**: Use `/regenerate` endpoint to force refresh.

---

*Source: [executive_brief_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/executive_brief_routes.py), [executive_brief_service.py](https://github.com/owkai/ow-ai-backend/blob/main/services/executive_brief_service.py)*
