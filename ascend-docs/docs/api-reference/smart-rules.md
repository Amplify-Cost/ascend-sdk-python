---
sidebar_position: 5
title: Smart Rules API
description: Create and manage AI-powered security rules
---

# Smart Rules API

Create, manage, and optimize AI-powered security rules with A/B testing, ML suggestions, and natural language generation.

**Base URL:** `https://pilot.owkai.app/api/smart-rules`

**Source:** `routes/smart_rules_routes.py`

**Compliance:** SOC 2 CC6.1, NIST AC-3/SI-4, PCI-DSS 7.1

## Authentication

All endpoints require JWT authentication via session cookie or API key.

Admin-only endpoints (marked) require elevated permissions.

---

## Rule Management

### GET /

List all smart rules for the organization.

**Request:**

```bash
curl "https://pilot.owkai.app/api/smart-rules" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
[
  {
    "id": 42,
    "agent_id": "security-agent",
    "action_type": "smart_rule",
    "description": "Block access to PII data outside business hours",
    "condition": "data_classification == 'pii' AND time_context == 'after_hours'",
    "action": "block_and_alert",
    "risk_level": "high",
    "recommendation": "Review rule effectiveness weekly",
    "justification": "Prevents unauthorized PII access",
    "created_at": "2025-01-15T10:00:00Z",
    "name": "PII After-Hours Block",
    "performance_score": 94.5,
    "triggers_last_24h": 12,
    "false_positives": 1,
    "effectiveness_rating": "high",
    "last_triggered": "2025-01-15T14:30:00Z",
    "has_execution_history": true
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `performance_score` | float | Accuracy percentage (null if no data) |
| `triggers_last_24h` | integer | Trigger count in last 24 hours |
| `false_positives` | integer | False positive count |
| `effectiveness_rating` | string | `high`, `medium`, `low`, or null |
| `has_execution_history` | boolean | Whether rule has been triggered |

---

### POST /

Create a smart rule manually (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Suspicious File Access",
    "condition": "action_type == \"file_read\" AND file_path LIKE \"/etc/%\"",
    "action": "block_and_alert",
    "risk_level": "high",
    "description": "Block access to system configuration files",
    "justification": "Prevents unauthorized system file access"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Rule name |
| `condition` | string | Yes | Condition expression |
| `action` | string | No | Action to take (default: alert) |
| `risk_level` | string | No | `low`, `medium`, `high`, `critical` |
| `description` | string | Yes | Rule description |
| `justification` | string | No | Why rule is needed |
| `agent_id` | string | No | Associated agent ID |
| `action_type` | string | No | Rule type |
| `recommendation` | string | No | Recommended action when triggered |

**Valid Actions:**

- `alert`
- `block`
- `block_and_alert`
- `quarantine`
- `monitor`
- `escalate`
- `quarantine_and_investigate`
- `monitor_and_escalate`

---

### DELETE /{rule_id}

Delete a smart rule (admin only).

**Request:**

```bash
curl -X DELETE "https://pilot.owkai.app/api/smart-rules/42" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response:**

```json
{
  "message": "Enterprise smart rule deleted successfully",
  "audit_info": {
    "rule_id": 42,
    "rule_condition": "data_classification == 'pii'",
    "deleted_by": "admin@company.com",
    "deletion_timestamp": "2025-01-15T10:00:00Z",
    "impact_assessment": "Rule deactivated - monitoring for security gaps"
  },
  "recommendation": "Monitor security metrics for 24 hours to ensure no coverage gaps"
}
```

---

## AI Rule Generation

### POST /generate

Generate a smart rule using AI (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/generate" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "security-agent",
    "action_type": "suspicious_activity",
    "description": "Detect and block unauthorized database exports"
  }'
```

**Response:**

```json
{
  "agent_id": "security-agent",
  "action_type": "suspicious_activity",
  "description": "Detect and block unauthorized database exports",
  "condition": "action_type == 'database_export' AND data_size_mb > 100",
  "action": "block_and_alert",
  "risk_level": "high",
  "recommendation": "Review export requests through approval workflow",
  "justification": "Prevents large-scale data exfiltration"
}
```

---

### POST /generate-from-nl

Generate a rule from natural language description (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/generate-from-nl" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "Block any agent from sending emails with attachments larger than 10MB during non-business hours",
    "context": "enterprise_security"
  }'
```

**Response:**

```json
{
  "id": 43,
  "condition": "(action_type == 'email_send' AND attachment_size_mb > 10) AND time_context NOT IN ('business_hours')",
  "action": "block_and_alert",
  "justification": "Enterprise AI-generated rule to prevent large file exfiltration",
  "risk_level": "high",
  "performance_score": 85,
  "triggers_last_24h": 0,
  "false_positives": 0,
  "created_at": "2025-01-15T10:00:00Z",
  "natural_language_source": "Block any agent from sending emails with attachments larger than 10MB during non-business hours",
  "enterprise_features": {
    "compliance_impact": "PCI-DSS 7.1, HIPAA 164.312",
    "business_impact": "Low operational impact",
    "false_positive_likelihood": "5%",
    "ai_confidence": 85
  }
}
```

---

## Rule Analytics

### GET /analytics

Get rule performance analytics for the organization (SEC-082).

**Request:**

```bash
curl "https://pilot.owkai.app/api/smart-rules/analytics" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
{
  "total_rules": 15,
  "active_rules": 15,
  "avg_performance_score": 88.5,
  "total_triggers_24h": 247,
  "false_positive_rate": 4.2,
  "top_performing_rules": [
    {
      "id": 42,
      "name": "PII Access Monitor",
      "score": 96,
      "category": "high"
    }
  ],
  "performance_trends": {
    "accuracy_improvement": "+12%",
    "response_time_improvement": "-25%",
    "false_positive_reduction": "-35%"
  },
  "ml_insights": {
    "pattern_recognition_accuracy": 88,
    "events_analyzed": 15420,
    "new_patterns_identified": 7,
    "prediction_confidence": 88
  },
  "enterprise_metrics": {
    "cost_savings_monthly": "$45,000",
    "incidents_prevented": 23,
    "automation_rate": "78%",
    "compliance_score": "94%"
  }
}
```

---

### GET /suggestions

Get ML-powered rule suggestions based on pattern analysis.

**Request:**

```bash
curl "https://pilot.owkai.app/api/smart-rules/suggestions" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
[
  {
    "id": 1,
    "suggested_rule": "Automated response for Unauthorized Access alerts",
    "confidence": 87,
    "reasoning": "Pattern analysis identified 145 occurrences in last 30 days. 65% escalation rate indicates high threat level requiring immediate attention.",
    "potential_impact": "Could automate 130 alerts/month, saving ~11 analyst hours ($825 value).",
    "data_points": 145,
    "category": "unauthorized_access",
    "priority": "high",
    "implementation_complexity": "medium",
    "estimated_false_positives": "8%",
    "business_impact": "high"
  }
]
```

---

## Rule Optimization

### POST /optimize/{rule_id}

Analyze and optimize rule performance (admin only, SEC-089).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/optimize/42" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response (with data):**

```json
{
  "rule_id": 42,
  "status": "analysis_complete",
  "original_performance": 87.5,
  "optimized_performance": null,
  "data_points_analyzed": 156,
  "analysis_period_days": 30,
  "current_metrics": {
    "total_triggers_30d": 156,
    "false_positives_30d": 12,
    "false_positive_rate": "7.7%",
    "avg_detection_time_ms": 45.2
  },
  "optimization_available": true,
  "optimization_techniques": [
    "Machine learning threshold tuning",
    "Behavioral pattern recognition",
    "Threat intelligence integration",
    "Context-aware analysis"
  ],
  "message": "Optimization recommendations available"
}
```

**Response (insufficient data):**

```json
{
  "rule_id": 42,
  "status": "insufficient_data",
  "original_performance": null,
  "data_points_analyzed": 3,
  "analysis_period_days": 30,
  "optimization_available": false,
  "message": "Insufficient data - rule needs more execution history for optimization analysis"
}
```

---

## A/B Testing

### GET /ab-tests

List all A/B tests for the organization.

**Request:**

```bash
curl "https://pilot.owkai.app/api/smart-rules/ab-tests" \
  -H "X-API-Key: your_api_key"
```

**Response:**

```json
[
  {
    "id": 1,
    "test_id": "550e8400-e29b-41d4-a716-446655440000",
    "test_name": "A/B Test: PII Access Monitor",
    "description": "Testing optimizations for: Block PII access outside hours",
    "rule_id": 42,
    "variant_a": "data_classification == 'pii' AND time_context == 'after_hours'",
    "variant_b": "(data_classification == 'pii' AND time_context == 'after_hours') AND user_risk_score < 'high'",
    "variant_a_performance": 75,
    "variant_b_performance": 82,
    "confidence_level": 88,
    "status": "running",
    "progress_percentage": 65,
    "winner": null,
    "statistical_significance": "medium",
    "improvement": "+9.3% projected",
    "sample_size": 1950,
    "traffic_split": 50,
    "duration_hours": 168,
    "enterprise_insights": {
      "cost_savings": "$3,500/month projected",
      "false_positive_reduction": "7.0% reduction",
      "efficiency_gain": "+3 hours/week",
      "recommendation": "Collecting more data (65% complete) - Strong indicators emerging"
    },
    "created_by": "admin@company.com",
    "created_at": "2025-01-10T10:00:00Z"
  }
]
```

---

### POST /ab-test

Create an A/B test for a rule (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/ab-test?rule_id=42" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "traffic_split": 50,
    "test_duration_hours": 168
  }'
```

**Response:**

```json
{
  "success": true,
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "rule_id": 42,
  "variant_a_rule_id": 43,
  "variant_b_rule_id": 44,
  "message": "A/B test created successfully! Check A/B Testing tab to monitor results.",
  "test_name": "A/B Test: PII Access Monitor",
  "enterprise_metadata": {
    "created_by": "admin@company.com",
    "organization_id": 4,
    "audit_trail_id": "660e8400-e29b-41d4-a716-446655440001"
  }
}
```

---

### GET /ab-test/{test_id}

Get A/B test details and results.

**Request:**

```bash
curl "https://pilot.owkai.app/api/smart-rules/ab-test/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key"
```

---

### POST /ab-test/{test_id}/stop

Stop a running A/B test.

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/ab-test/550e8400-e29b-41d4-a716-446655440000/stop" \
  -H "Cookie: access_token=your_session_cookie"
```

---

### POST /ab-test/{test_id}/deploy

Deploy the winning variant from an A/B test (admin only).

**Request:**

```bash
curl -X POST "https://pilot.owkai.app/api/smart-rules/ab-test/550e8400-e29b-41d4-a716-446655440000/deploy" \
  -H "Cookie: access_token=your_session_cookie"
```

**Response:**

```json
{
  "success": true,
  "message": "Winner deployed successfully! Variant B is now active.",
  "test_id": "550e8400-e29b-41d4-a716-446655440000",
  "winner": "variant_b",
  "base_rule_id": 42,
  "base_rule_name": "PII Access Monitor",
  "winning_condition": "(data_classification == 'pii' AND time_context == 'after_hours') AND user_risk_score < 'high'",
  "winning_performance": "82%",
  "improvement": "+7.0%"
}
```

---

## Error Responses

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid rule parameters |
| 401 | Unauthorized - Missing authentication |
| 403 | Forbidden - Admin access required |
| 404 | Not Found - Rule does not exist |
| 500 | Internal Server Error |

---

*Source: [smart_rules_routes.py](https://github.com/owkai/ow-ai-backend/blob/main/routes/smart_rules_routes.py)*
