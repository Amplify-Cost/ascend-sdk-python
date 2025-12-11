---
Document ID: ASCEND-ENT-005
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# System Diagnostics

Enterprise-grade health monitoring with Splunk/Datadog-compatible audit trails, real-time component analysis, and automated remediation suggestions.

## Overview

The System Diagnostics module provides comprehensive platform health monitoring aligned with industry leaders:

| Pattern | Industry Leader | Ascend Implementation |
|---------|-----------------|----------------------|
| Common Information Model | Splunk CIM | Standardized event format |
| Metrics Registry | Datadog Metrics | Centralized metric definitions |
| Distributed Tracing | Wiz.io | Correlation IDs for request tracking |
| Audit Trail | SOC 2 AU-6 | Immutable diagnostic logs |

### Compliance

| Standard | Requirement | Implementation |
|----------|-------------|----------------|
| SOC 2 CC7.2 | Security Monitoring | Real-time health checks |
| PCI-DSS 10.2 | Audit Trail Requirements | Immutable `diagnostic_audit_logs` table |
| HIPAA 164.312 | Audit Controls | SIEM-compatible export formats |
| NIST AU-6 | Audit Review & Analysis | Correlation ID tracking |

## API Endpoints

All endpoints are rate-limited and require authentication.

### Full Health Check

```http
GET /api/diagnostics/health
```

**Rate Limit:** 10 requests/minute

**Response:**
```json
{
  "status": "healthy",
  "health_score": 98.5,
  "severity": "INFO",
  "components": {
    "api": {"status": "healthy", "score": 100},
    "database": {"status": "healthy", "score": 98},
    "integrations": {"status": "healthy", "score": 95},
    "security": {"status": "healthy", "score": 100}
  },
  "timestamp": "2025-12-04T14:30:52Z",
  "correlation_id": "diag_4_20251204_143052_a1b2c3d4"
}
```

### API Health

```http
GET /api/diagnostics/api
```

**Rate Limit:** 20 requests/minute

Tests endpoint responsiveness, rate limiter status, and authentication system.

### Database Health

```http
GET /api/diagnostics/database
```

**Rate Limit:** 20 requests/minute

Checks database connectivity, query performance, and connection pool utilization.

### Integration Health

```http
GET /api/diagnostics/integrations
```

**Rate Limit:** 20 requests/minute

Verifies SIEM connectivity, webhook endpoints, and notification channels.

### Diagnostic History

```http
GET /api/diagnostics/history?limit=50
```

**Rate Limit:** 30 requests/minute

Returns historical diagnostic records for trend analysis.

### SIEM Export

```http
POST /api/diagnostics/export
```

**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "format": "splunk_cim",
  "start_date": "2025-12-01",
  "end_date": "2025-12-04"
}
```

**Supported Formats:**
- `splunk_cim` - Splunk Common Information Model
- `datadog_metrics` - Datadog metrics format
- `wiz_json` - Wiz.io JSON format

## Health Score Calculation

The composite health score uses a weighted formula:

```
Health Score = (API × 0.30) + (Database × 0.40) + (Integrations × 0.20) + (Security × 0.10)
```

| Component | Weight | Description |
|-----------|--------|-------------|
| API | 30% | Endpoint responsiveness, rate limiter status |
| Database | 40% | Query latency, connection pool utilization |
| Integrations | 20% | SIEM connectivity, webhook health |
| Security | 10% | Authentication status, certificate validity |

### Severity Classification

| Severity | Health Score | Splunk Level |
|----------|-------------|--------------|
| INFO | ≥ 90 | informational |
| WARNING | ≥ 80, < 90 | warning |
| ERROR | ≥ 60, < 80 | error |
| CRITICAL | < 60 | critical |

## Correlation IDs

Every diagnostic operation generates a traceable correlation ID:

**Format:** `diag_{org_id}_{YYYYMMDD}_{HHMMSS}_{uuid4_short}`

**Example:** `diag_4_20251204_143052_a1b2c3d4`

Use correlation IDs to trace diagnostic events across:
- Application logs
- SIEM systems
- Support tickets
- Audit reports

## Database Schema

### diagnostic_audit_logs

Immutable audit trail for all diagnostic operations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `correlation_id` | String(64) | Unique tracing identifier |
| `organization_id` | Integer | Multi-tenant isolation (FK) |
| `diagnostic_type` | String(50) | `api_health`, `database_status`, `integration_test`, `full_diagnostic`, `security_scan` |
| `status` | String(20) | `success`, `warning`, `failure`, `critical`, `timeout` |
| `health_score` | Float | Composite score 0-100 |
| `severity` | String(20) | `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `EMERGENCY` |
| `results` | JSONB | Full diagnostic results with component breakdown |
| `component_details` | JSONB | Individual component statuses |
| `remediation_suggestions` | JSONB | Actionable remediation steps |
| `initiated_by` | Integer | User ID who triggered diagnostic (FK) |
| `duration_ms` | Integer | Execution duration in milliseconds |
| `siem_export_format` | String(30) | `splunk_cim`, `datadog_metrics`, `wiz_json`, `generic_syslog` |
| `siem_exported_at` | DateTime | When record was exported to SIEM |
| `request_context` | JSONB | Source IP, user agent, request ID |
| `created_at` | DateTime | Immutable creation timestamp |

**Indexes:**
- `ix_diagnostic_audit_org_created` - Organization + timestamp queries
- `ix_diagnostic_audit_correlation` - Correlation ID lookups
- `ix_diagnostic_audit_severity` - Severity-based filtering

### diagnostic_thresholds

Organization-specific alerting thresholds.

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `api_response_time_warning_ms` | Integer | 500 | Warning threshold for API latency |
| `api_response_time_critical_ms` | Integer | 2000 | Critical threshold for API latency |
| `api_error_rate_warning_pct` | Float | 1.0% | Warning threshold for error rate |
| `api_error_rate_critical_pct` | Float | 5.0% | Critical threshold for error rate |
| `db_query_time_warning_ms` | Integer | 100 | Warning threshold for DB queries |
| `db_query_time_critical_ms` | Integer | 500 | Critical threshold for DB queries |
| `db_connection_pool_warning_pct` | Float | 70% | Warning for pool utilization |
| `db_connection_pool_critical_pct` | Float | 90% | Critical for pool utilization |
| `health_score_warning` | Float | 80.0 | Warning threshold for health score |
| `health_score_critical` | Float | 60.0 | Critical threshold for health score |
| `auto_alert_on_critical` | Boolean | true | Automatic alerting on critical status |
| `alert_cooldown_minutes` | Integer | 15 | Cooldown between alerts |

## SIEM Integration

### Splunk Common Information Model

Export diagnostic records in Splunk CIM format:

```json
{
  "event_id": "diag_4_20251204_143052_a1b2c3d4",
  "timestamp": "2025-12-04T14:30:52Z",
  "source": "owkai_diagnostics",
  "sourcetype": "owkai:diagnostic:full_diagnostic",
  "severity": "info",
  "status": "success",
  "health_score": 98.5,
  "organization_id": 4,
  "duration_ms": 245,
  "component_count": 4,
  "remediation_count": 0,
  "details": { ... }
}
```

**Splunk Query Example:**
```spl
index=ascend sourcetype="owkai:diagnostic:*"
| where health_score < 80
| stats count by organization_id, severity
```

### Datadog Metrics

Export as Datadog-compatible metric points:

```json
[
  {
    "metric": "owkai.diagnostics.health_score",
    "type": "gauge",
    "points": [[1701701452, 98.5]],
    "tags": ["org_id:4", "diagnostic_type:full_diagnostic", "status:success", "severity:info"]
  },
  {
    "metric": "owkai.diagnostics.duration_ms",
    "type": "gauge",
    "points": [[1701701452, 245]],
    "tags": ["org_id:4", "diagnostic_type:full_diagnostic", "status:success", "severity:info"]
  },
  {
    "metric": "owkai.diagnostics.execution",
    "type": "count",
    "points": [[1701701452, 1]],
    "tags": ["org_id:4", "diagnostic_type:full_diagnostic", "status:success", "severity:info"]
  }
]
```

**Datadog Dashboard Query:**
```
avg:owkai.diagnostics.health_score{*} by {org_id}
```

### Wiz.io JSON

Export for Wiz.io security posture management:

```json
{
  "event_id": "diag_4_20251204_143052_a1b2c3d4",
  "platform": "ascend",
  "resource_type": "diagnostic_check",
  "severity": "INFO",
  "health_score": 98.5,
  "findings": [],
  "remediation": []
}
```

## UI Integration

Access System Diagnostics from the Admin Console:

**Navigation:** Admin Console > Admin Tools > System Diagnostics

### Dashboard Features

1. **Run Diagnostic** - Execute full health check with audit logging
2. **Health History** - View historical health scores and trends
3. **Export to SIEM** - Download records in Splunk/Datadog/Wiz format
4. **Threshold Configuration** - Customize alerting thresholds per organization

### Component Status Display

| Status | Color | Description |
|--------|-------|-------------|
| Healthy | Green | Score ≥ 90, all systems operational |
| Degraded | Yellow | Score ≥ 80, minor issues detected |
| Unhealthy | Orange | Score ≥ 60, significant issues |
| Critical | Red | Score < 60, immediate attention required |

## Best Practices

### Monitoring Recommendations

1. **Schedule Regular Checks** - Run diagnostics hourly for proactive monitoring
2. **Set Appropriate Thresholds** - Configure thresholds based on your SLA requirements
3. **Enable SIEM Export** - Forward diagnostic logs to your SIEM for centralized monitoring
4. **Review Remediation Suggestions** - Act on AI-generated remediation suggestions promptly

### Alert Configuration

```json
{
  "api_response_time_warning_ms": 500,
  "api_response_time_critical_ms": 2000,
  "health_score_warning": 80.0,
  "health_score_critical": 60.0,
  "auto_alert_on_critical": true,
  "alert_cooldown_minutes": 15
}
```

### Correlation ID Usage

1. Include correlation ID in support tickets
2. Use for cross-system log correlation in your SIEM
3. Reference in incident response documentation
4. Store in audit reports for compliance

## Troubleshooting

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| 429 Too Many Requests | Rate limit exceeded | Wait for cooldown, check rate limits |
| Health Score Fluctuation | Database connection pool saturation | Review pool configuration |
| SIEM Export Timeout | Large date range | Reduce export range, use pagination |
| Missing Correlation ID | Legacy diagnostic records | Upgrade to latest API version |

### Debug Mode

Enable detailed logging for troubleshooting:

```python
# Log diagnostic execution details
logger.setLevel(logging.DEBUG)
```

## Next Steps

- [SIEM Integration](/enterprise/siem) - Configure SIEM forwarding
- [Splunk Setup](/enterprise/splunk) - Splunk-specific configuration
- [Compliance](/enterprise/compliance) - Compliance documentation
- [Analytics](/enterprise/analytics) - Platform analytics
