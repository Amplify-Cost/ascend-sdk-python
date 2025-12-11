---
Document ID: ASCEND-ENT-004
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# Analytics & Reporting

Ascend provides comprehensive analytics for monitoring AI governance, risk trends, and compliance metrics.

## Overview

Access real-time and historical analytics through:

- REST API endpoints
- WebSocket real-time streaming
- Executive dashboards
- Scheduled reports

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analytics/trends` | GET | Alert trends analysis |
| `/analytics/realtime/metrics` | GET | Real-time metrics |
| `/analytics/predictive/trends` | GET | Predictive trends |
| `/analytics/executive/dashboard` | GET | Executive dashboard |
| `/analytics/performance` | GET | Performance analytics |
| `/analytics/performance/system` | GET | System performance |
| `WebSocket /analytics/ws/realtime/{user_email}` | WS | Real-time streaming |

## Alert Trends

```bash
curl https://pilot.owkai.app/api/analytics/trends \
  -b cookies.txt
```

**Response:**

```json
{
  "period": "30d",
  "total_actions": 15420,
  "approved": 14200,
  "rejected": 520,
  "blocked": 700,
  "trends": {
    "daily": [
      {"date": "2025-01-15", "approved": 485, "rejected": 18, "blocked": 22},
      {"date": "2025-01-16", "approved": 510, "rejected": 15, "blocked": 28}
    ]
  },
  "by_agent": [
    {"agent_id": "customer-service", "actions": 5200, "avg_risk": 35},
    {"agent_id": "data-analyzer", "actions": 4100, "avg_risk": 45}
  ],
  "by_action_type": [
    {"type": "database_query", "count": 8500, "blocked_rate": 0.03},
    {"type": "api_call", "count": 4200, "blocked_rate": 0.05}
  ]
}
```

## Real-Time Metrics

```bash
curl https://pilot.owkai.app/api/analytics/realtime/metrics \
  -b cookies.txt
```

**Response:**

```json
{
  "timestamp": "2025-01-15T10:00:00Z",
  "active_agents": 12,
  "actions_per_minute": 45,
  "pending_approvals": 8,
  "avg_response_time_ms": 125,
  "risk_distribution": {
    "low": 65,
    "medium": 25,
    "high": 8,
    "critical": 2
  },
  "recent_alerts": [
    {
      "id": "alert_123",
      "type": "high_risk_action",
      "agent_id": "data-analyzer",
      "risk_score": 82,
      "timestamp": "2025-01-15T09:58:00Z"
    }
  ]
}
```

## WebSocket Real-Time

### Connect to Stream

```javascript
const ws = new WebSocket(
  'wss://pilot.owkai.app/analytics/ws/realtime/user@company.com'
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

### Event Types

```json
{
  "type": "action_submitted",
  "data": {
    "action_id": "act_xyz789",
    "agent_id": "customer-service",
    "risk_score": 45
  }
}
```

```json
{
  "type": "metrics_update",
  "data": {
    "actions_per_minute": 48,
    "pending_approvals": 10
  }
}
```

## Executive Dashboard

```bash
curl https://pilot.owkai.app/api/analytics/executive/dashboard \
  -b cookies.txt
```

**Response:**

```json
{
  "summary": {
    "total_agents": 15,
    "total_actions_30d": 45200,
    "compliance_score": 94,
    "risk_trend": "decreasing"
  },
  "kpis": {
    "approval_rate": 0.92,
    "avg_approval_time_minutes": 8.5,
    "policy_violation_rate": 0.04,
    "blocked_action_rate": 0.03
  },
  "risk_summary": {
    "avg_risk_score": 38,
    "high_risk_actions": 152,
    "critical_incidents": 3
  },
  "top_risks": [
    {
      "category": "Data Access",
      "risk_level": "high",
      "count": 45,
      "trend": "increasing"
    }
  ],
  "compliance": {
    "soc2_score": 96,
    "hipaa_score": 92,
    "gdpr_score": 94
  }
}
```

## Predictive Trends

```bash
curl https://pilot.owkai.app/api/analytics/predictive/trends \
  -b cookies.txt
```

**Response:**

```json
{
  "forecast_period": "7d",
  "predictions": {
    "expected_actions": 3500,
    "expected_high_risk": 85,
    "risk_trend": "stable",
    "confidence": 0.87
  },
  "anomaly_detection": {
    "detected": false,
    "last_anomaly": "2025-01-10T14:30:00Z",
    "anomaly_type": "volume_spike"
  },
  "recommendations": [
    {
      "type": "policy_adjustment",
      "description": "Consider lowering threshold for database_write actions",
      "impact": "medium"
    }
  ]
}
```

## Performance Analytics

### Agent Performance

```bash
curl https://pilot.owkai.app/api/analytics/performance \
  -b cookies.txt
```

**Response:**

```json
{
  "agents": [
    {
      "agent_id": "customer-service",
      "total_actions": 5200,
      "approved_rate": 0.95,
      "avg_risk_score": 32,
      "avg_response_time_ms": 85,
      "policy_violations": 12
    }
  ],
  "overall": {
    "total_actions": 15420,
    "avg_processing_time_ms": 125,
    "p95_processing_time_ms": 280,
    "p99_processing_time_ms": 450
  }
}
```

### System Performance

```bash
curl https://pilot.owkai.app/api/analytics/performance/system \
  -b cookies.txt
```

**Response:**

```json
{
  "api_health": {
    "status": "healthy",
    "uptime_percent": 99.95,
    "avg_latency_ms": 85
  },
  "queue_metrics": {
    "pending_actions": 12,
    "avg_queue_time_ms": 150,
    "max_queue_depth_24h": 45
  },
  "database_metrics": {
    "query_time_avg_ms": 25,
    "connections_active": 8,
    "connections_available": 92
  }
}
```

## Scheduled Reports

### Create Report Schedule

```bash
curl -X POST https://pilot.owkai.app/api/users/reports/scheduled \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Weekly Executive Summary",
    "report_type": "executive_dashboard",
    "schedule": "0 9 * * 1",
    "format": "pdf",
    "recipients": ["exec@company.com", "security@company.com"],
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

## Custom Analytics

### Query Builder

```bash
curl -X POST https://pilot.owkai.app/api/analytics/query \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "metrics": ["action_count", "avg_risk_score", "approval_rate"],
    "dimensions": ["agent_id", "action_type"],
    "filters": {
      "date_range": {
        "start": "2025-01-01",
        "end": "2025-01-31"
      },
      "risk_score": {"gte": 50}
    },
    "group_by": ["agent_id"],
    "order_by": [{"field": "action_count", "direction": "desc"}],
    "limit": 10
  }'
```

## Data Export

### Export Analytics Data

```bash
curl -X POST https://pilot.owkai.app/api/analytics/export \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "report_type": "trends",
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-01-31"
    },
    "format": "csv"
  }' \
  -o analytics_export.csv
```

## Dashboard Integration

### Embed Dashboard

```html
<iframe
  src="https://pilot.owkai.app/embed/dashboard?token=xxx"
  width="100%"
  height="600"
></iframe>
```

### API for Custom Dashboards

Build custom dashboards using the analytics API:

```javascript
async function loadDashboard() {
  const [trends, realtime, executive] = await Promise.all([
    fetch('/analytics/trends').then(r => r.json()),
    fetch('/analytics/realtime/metrics').then(r => r.json()),
    fetch('/analytics/executive/dashboard').then(r => r.json())
  ]);

  renderCharts(trends, realtime, executive);
}
```

## Best Practices

1. **Use caching** - Cache analytics responses for performance
2. **Set appropriate ranges** - Limit date ranges for large datasets
3. **Monitor real-time sparingly** - Use WebSocket for live data
4. **Schedule reports** - Automate recurring reports
5. **Export for BI tools** - Use CSV export for external analysis

## Next Steps

- [Compliance](/enterprise/compliance) - Compliance reporting
- [Audit Logging](/core-concepts/audit-logging) - Audit trail
- [SIEM Integration](/enterprise/siem) - Security monitoring
