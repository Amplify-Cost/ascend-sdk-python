---
sidebar_position: 6
title: Analytics API
description: Real-time analytics and executive dashboards
---

# Analytics API

Access real-time metrics, trend analysis, predictive analytics, and executive dashboards.

**Base URL:** `https://pilot.owkai.app/api/analytics`

**Source:** `routes/analytics_routes.py`

**Compliance:** SOC 2 CC6.1/CC7.2, NIST AU-6/AU-7, PCI-DSS 10.6

## Authentication

All endpoints require authentication via session cookie or API key.

Executive dashboard requires admin permissions.

---

## Trend Analytics

### GET /trends

Get trend data for agent activities and risk levels.

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/trends" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "high_risk_actions_by_day": [
    {"date": "2025-01-09", "count": 5},
    {"date": "2025-01-10", "count": 12},
    {"date": "2025-01-11", "count": 8}
  ],
  "top_agents": [
    {"agent": "customer-service-agent", "count": 245},
    {"agent": "data-analysis-agent", "count": 178}
  ],
  "top_tools": [
    {"tool": "email_service", "count": 312},
    {"tool": "database_query", "count": 187}
  ],
  "enriched_actions": [
    {
      "agent_id": "customer-service-agent",
      "action_type": "email_send",
      "risk_level": "medium",
      "mitre_tactic": "TA0002",
      "nist_control": "AC-3",
      "recommendation": "Verify recipient authorization",
      "tool_name": "email_service",
      "timestamp": "2025-01-15T14:30:00Z"
    }
  ],
  "pending_actions_count": 7
}
```

---

## Real-Time Metrics

### GET /realtime/metrics

Get real-time operational metrics with CloudWatch integration.

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/realtime/metrics" \
  -H "X-API-Key: your_api_key"
```

**Response (with CloudWatch):**

```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "real_time_overview": {
    "active_sessions": 12,
    "recent_high_risk_actions": 3,
    "active_agents": 8,
    "total_actions_last_hour": 47,
    "actions_last_24h": 1245,
    "status": {
      "has_data": true,
      "message": "Live data from production database",
      "data_age_minutes": 0
    }
  },
  "system_health": {
    "status": "live",
    "source": "cloudwatch",
    "cpu_usage": 34.5,
    "memory_usage": 62.8,
    "disk_usage": 45.2,
    "network_latency": 12.3,
    "api_response_time": 145.0,
    "timestamp": "2025-01-15T14:29:45Z",
    "metrics_age_seconds": 15
  },
  "performance_metrics": {
    "status": "live",
    "source": "cloudwatch_logs",
    "requests_per_second": 25.4,
    "avg_response_time": 145.0,
    "p95_response_time": 320.0,
    "error_rate": 0.002
  },
  "data_quality": {
    "source": "production_database",
    "timestamp": "2025-01-15T14:30:00Z",
    "has_historical_data": true,
    "has_recent_activity": true,
    "data_status": "live"
  },
  "meta": {
    "version": "1.0.0-phase2",
    "enterprise_grade": true,
    "mock_data": false,
    "real_data_sources": ["postgresql_rds", "aws_cloudwatch"],
    "phase": "2_of_3",
    "cloudwatch_enabled": true,
    "cloudwatch_status": "live"
  }
}
```

**Response (without CloudWatch):**

```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "real_time_overview": {
    "active_sessions": 12,
    "recent_high_risk_actions": 3,
    "active_agents": 8,
    "total_actions_last_hour": 47,
    "actions_last_24h": 1245
  },
  "system_health": {
    "status": "phase_2_planned",
    "message": "System health monitoring with AWS CloudWatch will be available in Phase 2",
    "available_metrics": ["CPU", "Memory", "Disk", "Network", "API Response Time"],
    "cloudwatch_enabled": false
  },
  "performance_metrics": {
    "status": "phase_2_planned",
    "message": "Performance tracking with CloudWatch Logs Insights will be available in Phase 2",
    "planned_metrics": ["Requests/sec", "Error rate", "Response time", "Cache hit rate"]
  }
}
```

---

## Predictive Analytics

### GET /predictive/trends

Get ML-powered predictive analytics and forecasting.

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/predictive/trends" \
  -H "X-API-Key: your_api_key"
```

**Response (active predictions):**

```json
{
  "status": "active",
  "prediction_quality": "high",
  "risk_forecast": [
    {
      "date": "2025-01-16",
      "predicted_high_risk_actions": 15,
      "confidence": 0.87,
      "trend": "increasing"
    },
    {
      "date": "2025-01-17",
      "predicted_high_risk_actions": 12,
      "confidence": 0.82,
      "trend": "stable"
    }
  ],
  "agent_workload_forecast": [
    {
      "agent_id": "customer-service-agent",
      "predicted_actions": 145,
      "confidence": 0.85,
      "recommendation": "Monitor capacity"
    }
  ],
  "anomalies": [
    {
      "type": "spike",
      "description": "Unusual activity spike detected for database-agent",
      "severity": "medium",
      "timestamp": "2025-01-15T10:00:00Z"
    }
  ],
  "risk_predictions": {
    "recommended_actions": [
      "Increase monitoring for customer-service-agent",
      "Review high-risk action patterns from last week"
    ]
  },
  "data_collection": {
    "days_collected": 21,
    "total_actions": 15420,
    "collection_progress": 100.0,
    "ready": true,
    "quality": "Excellent data for high quality predictions"
  },
  "meta": {
    "version": "1.0.0-phase3",
    "mock_data": false,
    "prediction_method": "ml_powered",
    "confidence_range": [0.75, 0.92],
    "phase": "3_of_3_active"
  },
  "timestamp": "2025-01-15T14:30:00Z"
}
```

**Response (collecting data):**

```json
{
  "status": "collecting_data",
  "message": "Collecting data for predictions. Minimum 4 days needed for pattern-based forecasting.",
  "data_collection": {
    "days_collected": 2,
    "minimum_required": 4,
    "optimal_required": 14,
    "total_actions": 245,
    "collection_progress": 50.0,
    "estimated_ready_date": "2025-01-17"
  },
  "planned_features": [
    {
      "feature": "Risk Trend Forecasting",
      "description": "Predict high-risk action patterns 7 days ahead",
      "accuracy_target": "85%+",
      "benefit": "Proactive threat mitigation"
    },
    {
      "feature": "Agent Workload Prediction",
      "description": "Forecast agent capacity and utilization",
      "accuracy_target": "80%+",
      "benefit": "Capacity planning and resource optimization"
    },
    {
      "feature": "Anomaly Detection",
      "description": "Identify unusual patterns and potential security threats",
      "accuracy_target": "90%+",
      "benefit": "Early warning system for security incidents"
    }
  ]
}
```

---

## Executive Dashboard

### GET /executive/dashboard

Get executive-level KPI dashboard (admin only).

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/executive/dashboard" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response:**

```json
{
  "report_date": "2025-01-15T14:30:00Z",
  "data_period": {
    "start_date": "2024-12-16T14:30:00Z",
    "end_date": "2025-01-15T14:30:00Z",
    "days": 30
  },
  "executive_summary": {
    "overall_health": "excellent",
    "key_achievements": [
      "Zero critical security incidents this month",
      "98.5% system reliability achieved",
      "82% workflow automation rate"
    ],
    "areas_of_focus": [
      "Continue monitoring system health and performance"
    ],
    "data_quality": "real_database_queries"
  },
  "executive_kpis": {
    "platform_health": {
      "score": 98.5,
      "trend": "stable",
      "status": "excellent",
      "total_actions": 4520,
      "success_rate": 98.5
    },
    "security_posture": {
      "score": 94.2,
      "trend": "improving",
      "critical_issues": 0,
      "high_risk_actions": 12,
      "medium_risk_actions": 45
    },
    "operational_efficiency": {
      "score": 82.0,
      "automation_rate": 0.82,
      "manual_interventions": 45,
      "pending_actions": 7
    },
    "compliance_status": {
      "score": 96.5,
      "violations": 2,
      "pending_reviews": 7,
      "compliance_actions": 234
    }
  },
  "business_metrics": {
    "user_growth": {
      "current_users": 125,
      "active_users": 98,
      "growth_rate": 0.15,
      "trend": "positive",
      "new_users_this_week": 8
    },
    "system_utilization": {
      "avg_actions_per_day": 150.7,
      "peak_day_actions": 312,
      "efficiency_score": 0.82,
      "total_actions_month": 4520
    }
  },
  "strategic_insights": [
    {
      "category": "security",
      "insight": "Strong security posture maintained (only 12 high-risk actions)",
      "action": "Continue current security protocols",
      "priority": "low",
      "data_source": "agent_actions_risk_analysis"
    },
    {
      "category": "efficiency",
      "insight": "Excellent automation rate (82%)",
      "action": "Maintain current automation strategies",
      "priority": "low",
      "data_source": "approval_workflow_metrics"
    }
  ],
  "next_review_date": "2025-01-22T14:30:00Z",
  "meta": {
    "version": "2.0.0",
    "mock_data": false,
    "real_data_sources": ["agent_actions", "users", "audit_logs"],
    "has_activity": true
  }
}
```

---

## System Performance

### GET /performance

Get system performance metrics with CloudWatch integration.

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/performance" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "system_metrics": {
    "cpu": {
      "current": 34.5,
      "average": 32.1,
      "status": "normal",
      "source": "cloudwatch"
    },
    "memory": {
      "current": 62.8,
      "available": 37.2,
      "status": "normal",
      "source": "cloudwatch"
    },
    "storage": {
      "used": 45.2,
      "available": 54.8,
      "status": "healthy",
      "source": "cloudwatch"
    }
  },
  "application_metrics": {
    "response_times": {
      "average": 145.0,
      "p95": 320.0,
      "target": 200.0,
      "status": "good",
      "source": "cloudwatch_logs"
    },
    "throughput": {
      "requests_per_second": 25.4,
      "source": "cloudwatch_logs"
    },
    "error_rates": {
      "current": 0.002,
      "target": 0.01,
      "status": "good",
      "source": "cloudwatch_logs"
    }
  },
  "database_metrics": {
    "connections": {
      "active": 12,
      "idle": 8,
      "total": 20,
      "max": 100,
      "utilization": 20.0,
      "status": "healthy",
      "source": "postgresql"
    },
    "query_performance": {
      "recent_queries": 47,
      "slow_queries_estimate": 0,
      "status": "optimal",
      "source": "agent_actions_table"
    }
  },
  "meta": {
    "version": "2.0.0",
    "mock_data": false,
    "cloudwatch_enabled": true,
    "data_sources": {
      "system_metrics": "cloudwatch",
      "application_metrics": "cloudwatch_logs",
      "database_metrics": "postgresql"
    }
  }
}
```

---

## Debug Endpoints

### GET /debug

Debug endpoint showing enriched actions (development).

**Request:**

```bash
curl "https://pilot.owkai.app/api/analytics/debug" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
[
  {
    "id": 1547,
    "agent_id": "customer-service-agent",
    "risk_level": "medium",
    "mitre_tactic": "TA0002",
    "nist_control": "AC-3",
    "recommendation": "Verify recipient authorization",
    "summary": "Email sent to external recipient"
  }
]
```

---

## WebSocket Real-Time Streaming

### WS /ws/realtime/{user_email}

WebSocket endpoint for real-time analytics streaming.

**Connection:**

```javascript
const ws = new WebSocket('wss://pilot.owkai.app/api/analytics/ws/realtime/user@company.com');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

**Message Types:**

**Connection Confirmation:**

```json
{
  "type": "connection",
  "status": "connected",
  "message": "Real-time analytics connected for user@company.com",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

**Metrics Update (every 10 seconds):**

```json
{
  "type": "metrics_update",
  "timestamp": "2025-01-15T14:30:10Z",
  "metrics": {
    "active_websocket_connections": 5,
    "recent_actions_last_hour": 47,
    "high_risk_actions_last_hour": 3,
    "active_agents_last_hour": 8
  },
  "system_metrics": {
    "status": "live",
    "cpu_usage": 34.5,
    "memory_usage": 62.8,
    "response_time": 145.0
  },
  "data_quality": {
    "source": "real_database",
    "mock_data": false,
    "has_activity": true
  }
}
```

---

## Error Responses

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Missing authentication |
| 403 | Forbidden - Admin access required |
| 500 | Internal Server Error |
| 503 | Service Unavailable - CloudWatch connection failed |

---

*Source: [analytics_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/analytics_routes.py)*
