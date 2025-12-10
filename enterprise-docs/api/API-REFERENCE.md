# OW-AI Platform - API Reference

## Table of Contents
1. [Base URLs & Environment](#base-urls--environment)
2. [Authentication](#authentication)
3. [Actions API v1 (SDK)](#actions-api-v1-sdk)
4. [Authorization Center APIs](#authorization-center-apis)
5. [Alert Management APIs](#alert-management-apis)
6. [Smart Rules Engine APIs](#smart-rules-engine-apis)
7. [Enterprise User Management APIs](#enterprise-user-management-apis)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

## Base URLs & Environment

### Production Environment
- **Base URL:** https://pilot.owkai.app
- **API Version:** v1
- **Documentation:** https://pilot.owkai.app/docs

### Staging Environment
- **Base URL:** https://staging.owkai.app
- **API Version:** v1
- **Documentation:** https://staging.owkai.app/docs

### Development Environment
- **Base URL:** http://localhost:8000
- **API Version:** v1
- **Documentation:** http://localhost:8000/docs

## Authentication

All API requests (except authentication endpoints) require authentication using JWT Bearer tokens.

### Authentication Methods
1. **Bearer Token:** Include JWT token in Authorization header
2. **Cookie Authentication:** For browser-based applications (automatic)

### Token Format
```bash
Authorization: Bearer <JWT_TOKEN>
```

### Token Lifecycle
- **Access Token Expiry:** 30 minutes
- **Refresh Token Expiry:** 7 days
- **Automatic Refresh:** Handled by client libraries

---

## Authentication Endpoints

### POST /auth/token
**Description:** Authenticate user and receive JWT access and refresh tokens

**Request Body:**
```json
{
  "email": "admin@owkai.com",
  "password": "SecurePassword123!"
}
```

**Response 200 (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3IiwiZW1haWwiOiJhZG1pbkBvd2thaS5jb20iLCJyb2xlIjoiYWRtaW4iLCJ1c2VyX2lkIjo3LCJleHAiOjE3NjAyNDQ3NTcsImlhdCI6MTc2MDI0Mjk1NywidHlwZSI6ImFjY2VzcyIsImlzcyI6Im93LWFpLWVudGVycHJpc2UiLCJhdWQiOiJvdy1haS1wbGF0Zm9ybSIsImp0aSI6ImFjY2Vzcy03LTE3NjAyNDI5NTcifQ.H64dVK0a7S92-42EuwxsT3wnLTxphunSINBwTeyKFaE",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3IiwiZW1haWwiOiJhZG1pbkBvd2thaS5jb20iLCJyb2xlIjoiYWRtaW4iLCJ1c2VyX2lkIjo3LCJleHAiOjE3NjA4NDc3NTcsImlhdCI6MTc2MDI0Mjk1NywidHlwZSI6InJlZnJlc2giLCJpc3MiOiJvdy1haS1lbnRlcnByaXNlIiwiYXVkIjoib3ctYWktcGxhdGZvcm0iLCJqdGkiOiJyZWZyZXNoLTctMTc2MDI0Mjk1NyJ9.l2voTAcdT5PD1YTm_AYXfG9quLiuCSdJmwLsl-NNQo8",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "email": "admin@owkai.com",
    "role": "admin",
    "user_id": 7
  },
  "auth_mode": "token"
}
```

**Response 401 (Invalid Credentials):**
```json
{
  "detail": "Invalid email or password"
}
```

**Example:**
```bash
curl -X POST https://pilot.owkai.app/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@owkai.com","password":"SecurePassword123!"}'
```

### GET /auth/me
**Description:** Get current authenticated user profile information

**Authentication:** Required

**Response 200:**
```json
{
  "user_id": 7,
  "email": "admin@owkai.com",
  "role": "admin",
  "auth_source": "bearer",
  "auth_mode": "enterprise",
  "enterprise_validated": true
}
```

**Example:**
```bash
curl -X GET https://pilot.owkai.app/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /auth/refresh-token
**Description:** Refresh expired access token using refresh token

**Authentication:** Refresh token required

**Response 200:**
```json
{
  "access_token": "new_access_token_here",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/logout
**Description:** Logout and invalidate current session

**Authentication:** Required

**Response 200:**
```json
{
  "message": "Successfully logged out",
  "cleared_tokens": true
}
```

---

## Actions API v1 (SDK)

The Actions API v1 provides SDK integration endpoints for submitting actions to the governance pipeline. These endpoints use API key authentication instead of JWT tokens.

### Authentication

SDK endpoints use the `X-API-Key` header for authentication:

```bash
X-API-Key: owkai_xxx_your_api_key_here
```

### POST /api/v1/actions/submit

**Description:** Submit an action for governance evaluation through the complete pipeline.

**Authentication:** API Key (X-API-Key header)

**Request Body:**
```json
{
  "action_type": "s3.delete_bucket",
  "tool_name": "aws_s3",
  "description": "Delete production backup bucket",
  "parameters": {
    "Bucket": "production-backups-2024"
  },
  "agent_id": "boto3-agent-abc123"
}
```

**Response 200 (Success):**
```json
{
  "id": 923,
  "action_id": 923,
  "status": "pending_approval",
  "risk_score": 71.0,
  "risk_level": "high",
  "alert_triggered": true,
  "alert_id": 717,
  "requires_approval": true,
  "message": "Action processed through complete governance pipeline"
}
```

**Example:**
```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/submit" \
  -H "X-API-Key: owkai_admin_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "s3.delete_bucket", "tool_name": "aws_s3", "description": "Delete bucket"}'
```

### GET /api/v1/actions

**Description:** List actions for the authenticated organization.

**Authentication:** API Key (X-API-Key header)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | all | Filter: `pending_approval`, `approved`, `denied` |
| limit | integer | 50 | Maximum results (1-100) |

**Response 200:**
```json
{
  "actions": [
    {
      "id": 923,
      "action_type": "s3.delete_bucket",
      "status": "pending_approval",
      "risk_score": 85.0,
      "created_at": "2025-12-10T15:30:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/actions/{id}/status

**Description:** Poll action status (optimized for SDK polling).

**Authentication:** API Key (X-API-Key header)

**Response 200:**
```json
{
  "id": 923,
  "status": "approved",
  "risk_score": 71.0,
  "approved_by": "admin@company.com",
  "approved_at": "2025-12-10T15:35:00Z"
}
```

### Risk Score Thresholds

| Risk Score | Risk Level | Alert Generated |
|------------|------------|-----------------|
| 0-29 | Low | No |
| 30-69 | Medium | No |
| 70-84 | High | **Yes** |
| 85-100 | Critical | **Yes** |

**Note:** Actions with `risk_score >= 70` automatically trigger alerts in the Alert Management system.

---

## Authorization Center APIs

The Authorization Center provides real-time policy evaluation, approval workflows, and enterprise governance capabilities.

### GET /api/authorization/dashboard
**Description:** Get comprehensive approval dashboard with KPIs and metrics

**Authentication:** Required
**Permissions:** Any authenticated user

**Response 200:**
```json
{
  "summary": {
    "total_pending": 5,
    "total_approved": 147,
    "total_executed": 134,
    "total_rejected": 23,
    "approval_rate": 86.5,
    "execution_rate": 91.2
  },
  "enterprise_kpis": {
    "high_risk_pending": 2,
    "today_actions": 12,
    "sla_compliance": 96.8,
    "security_posture_score": 87.4,
    "compliance_score": 94.2,
    "threat_detection_accuracy": 91.7
  },
  "recent_activity": [
    {
      "id": 1001,
      "action_type": "file_access",
      "status": "approved",
      "timestamp": "2025-10-12T10:30:00Z",
      "risk_level": "medium",
      "agent_id": "ai-agent-001",
      "description": "Read configuration files",
      "enterprise_priority": "normal"
    }
  ],
  "user_context": {
    "role": "admin",
    "permissions": ["approve", "reject", "view_all"],
    "access_level": "elevated",
    "enterprise_privileges": true
  },
  "user_info": {
    "approval_level": 5,
    "is_emergency_approver": true,
    "max_risk_approval": 100,
    "role": "admin",
    "email": "admin@company.com"
  },
  "system_status": {
    "siem_integration": "operational",
    "threat_intelligence": "active",
    "automation_engine": "running",
    "compliance_monitoring": "enabled"
  },
  "last_updated": "2025-10-12T11:30:00Z"
}
```

**Example:**
```bash
curl -X GET https://pilot.owkai.app/api/authorization/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GET /api/authorization/pending-actions
**Description:** Get all pending actions requiring approval with filtering capabilities

**Authentication:** Required
**Permissions:** Approver role or higher

**Query Parameters:**
- `risk_level` (optional): Filter by risk level (low, medium, high, critical)
- `agent_id` (optional): Filter by specific agent ID
- `limit` (optional): Limit number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response 200:**
```json
{
  "actions": [
    {
      "id": 1003,
      "agent_id": "ai-agent-002",
      "action_type": "api_call",
      "description": "Call external payment processing API",
      "risk_level": "high",
      "risk_score": 85,
      "status": "pending",
      "created_at": "2025-10-12T12:00:00Z",
      "extra_data": {
        "endpoint": "https://api.payments.com/process",
        "method": "POST",
        "data_sensitivity": "high"
      },
      "approval_requirements": {
        "minimum_role": "security_analyst",
        "requires_dual_approval": true,
        "max_approval_time_hours": 4
      }
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

**Example:**
```bash
curl -X GET "https://pilot.owkai.app/api/authorization/pending-actions?risk_level=high&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### POST /api/authorization/authorize/{action_id}
**Description:** Authorize a specific action with comprehensive audit trail

**Authentication:** Required
**Permissions:** Approver role or higher
**CSRF Protection:** Required for web requests

**Path Parameters:**
- `action_id` (integer): ID of the action to authorize

**Request Body:**
```json
{
  "decision": "approve",
  "comment": "Approved after security review",
  "conditions": {
    "time_limit_hours": 2,
    "monitoring_required": true,
    "additional_logging": true
  }
}
```

**Response 200 (Success):**
```json
{
  "success": true,
  "action_id": 1003,
  "decision": "approved",
  "approved_by": "security_analyst@company.com",
  "approved_at": "2025-10-12T12:30:00Z",
  "execution_status": "authorized",
  "audit_trail": {
    "audit_id": "audit_20251012_123000_1003",
    "compliance_flags": ["SOX", "PCI-DSS"],
    "risk_assessment": {
      "original_score": 85,
      "mitigated_score": 45,
      "mitigation_factors": ["time_limit", "monitoring"]
    }
  },
  "next_steps": [
    "Action authorized for execution",
    "Monitoring enabled for 2 hours",
    "Results will be logged for audit"
  ]
}
```

**Response 400 (Invalid Decision):**
```json
{
  "detail": "Invalid decision. Must be 'approve' or 'reject'"
}
```

**Response 404 (Action Not Found):**
```json
{
  "detail": "Action not found or already processed"
}
```

**Example:**
```bash
curl -X POST https://pilot.owkai.app/api/authorization/authorize/1003 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve",
    "comment": "Approved after security review",
    "conditions": {"time_limit_hours": 2}
  }'
```

### GET /api/authorization/execution-history
**Description:** Get comprehensive execution history with enterprise metadata

**Authentication:** Required
**Permissions:** Any authenticated user

**Query Parameters:**
- `start_date` (optional): Filter from date (ISO 8601 format)
- `end_date` (optional): Filter to date (ISO 8601 format)
- `status` (optional): Filter by execution status
- `limit` (optional): Limit results (default: 50, max: 100)

**Response 200:**
```json
{
  "executions": [
    {
      "id": 1001,
      "action_id": 998,
      "agent_id": "ai-agent-001",
      "action_type": "file_access",
      "status": "completed",
      "approved_by": "admin@company.com",
      "executed_at": "2025-10-12T10:45:00Z",
      "execution_time_ms": 1250,
      "results": {
        "success": true,
        "files_accessed": 5,
        "data_processed": "124KB"
      },
      "compliance_data": {
        "nist_controls": ["AC-3", "AU-2"],
        "sox_compliance": true,
        "audit_log_id": "audit_20251012_104500_998"
      }
    }
  ],
  "summary": {
    "total_executions": 134,
    "success_rate": 97.8,
    "avg_execution_time_ms": 1180,
    "compliance_rate": 100.0
  }
}
```

### POST /api/authorization/policies/evaluate-realtime
**Description:** Real-time policy evaluation for authorization decisions

**Authentication:** Required
**Permissions:** Any authenticated user

**Request Body:**
```json
{
  "action_type": "file_access",
  "resource": "/secure/customer_data.db",
  "namespace": "database",
  "environment": "production",
  "user_context": {
    "user_id": "user123",
    "user_email": "analyst@company.com",
    "user_role": "security_analyst"
  },
  "additional_context": {
    "ip_address": "10.0.1.100",
    "time_of_day": "business_hours",
    "data_classification": "confidential"
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "evaluation_id": "eval_20251012_125500",
  "decision": "require_approval",
  "risk_score": {
    "total_score": 75,
    "risk_level": "HIGH",
    "category_scores": {
      "data_sensitivity": 85,
      "user_privilege": 60,
      "time_context": 70,
      "environmental": 80
    }
  },
  "policy_matches": [
    {
      "policy_id": "pol_sensitive_data_access",
      "policy_name": "Sensitive Data Access Control",
      "effect": "require_approval",
      "conditions_met": ["high_data_sensitivity", "production_environment"]
    }
  ],
  "approval_requirements": {
    "minimum_role": "security_analyst",
    "dual_approval_required": true,
    "max_approval_time_hours": 2
  },
  "evaluation_time_ms": 142,
  "cached": false
}
```

### GET /api/authorization/workflow-config
**Description:** Get current workflow configuration for approval workflows

**Authentication:** Required

**Response 200:**
```json
{
  "workflows": {
    "risk_90_100": {
      "name": "Critical Risk (90-100)",
      "approval_levels": 3,
      "approvers": ["security@company.com", "senior@company.com", "executive@company.com"],
      "timeout_hours": 2,
      "emergency_override": true,
      "escalation_minutes": 30
    },
    "risk_70_89": {
      "name": "High Risk (70-89)",
      "approval_levels": 2,
      "approvers": ["security@company.com", "senior@company.com"],
      "timeout_hours": 4,
      "emergency_override": false,
      "escalation_minutes": 60
    },
    "risk_50_69": {
      "name": "Medium Risk (50-69)",
      "approval_levels": 2,
      "approvers": ["security@company.com", "security2@company.com"],
      "timeout_hours": 8,
      "emergency_override": false,
      "escalation_minutes": 120
    },
    "risk_0_49": {
      "name": "Low Risk (0-49)",
      "approval_levels": 1,
      "approvers": ["security@company.com"],
      "timeout_hours": 24,
      "emergency_override": false,
      "escalation_minutes": 480
    }
  },
  "last_modified": "2025-10-12T14:00:00Z",
  "modified_by": "system",
  "total_workflows": 4,
  "emergency_override_enabled": true
}
```

### POST /api/authorization/workflow-config
**Description:** Update workflow configuration

**Authentication:** Required
**Permissions:** Admin role

**Request Body:**
```json
{
  "workflow_id": "risk_90_100",
  "config": {
    "approval_levels": 3,
    "timeout_hours": 1,
    "emergency_override": true
  }
}
```

**Response 200:**
```json
{
  "success": true,
  "updated_workflow": "risk_90_100",
  "changes_applied": 2,
  "effective_immediately": true
}
```

---

## Alert Management APIs

The Alert Management System provides real-time threat detection, alert correlation, and automated response capabilities.

### GET /api/alerts
**Description:** Get all alerts with filtering and pagination

**Authentication:** Required
**Permissions:** Any authenticated user

**Query Parameters:**
- `severity` (optional): Filter by severity (low, medium, high, critical)
- `status` (optional): Filter by status (new, acknowledged, resolved)
- `limit` (optional): Limit results (default: 50, max: 100)
- `start_date` (optional): Filter from date
- `end_date` (optional): Filter to date

**Response 200:**
```json
[
  {
    "id": 3001,
    "alert_type": "High Risk Agent Action",
    "severity": "high",
    "message": "Multiple failed login attempts detected",
    "timestamp": "2025-10-12T04:24:38.693457",
    "agent_id": "unknown-agent",
    "action_type": "authentication",
    "status": "new",
    "metadata": {
      "source_ip": "192.168.1.100",
      "attempt_count": 5,
      "time_window": "5 minutes"
    },
    "correlation_id": "corr_20251012_042438"
  }
]
```

**Example:**
```bash
curl -X GET "https://pilot.owkai.app/api/alerts?severity=high&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### GET /api/alerts/active
**Description:** Get all currently active alerts with real-time statistics

**Authentication:** Required

**Response 200:**
```json
{
  "alerts": [
    {
      "id": 3002,
      "alert_type": "Threat Detection",
      "severity": "critical",
      "message": "Potential data exfiltration detected",
      "timestamp": "2025-10-12T13:15:00Z",
      "agent_id": "ai-agent-003",
      "status": "active",
      "escalation_level": 2,
      "assigned_to": "security_team@company.com"
    }
  ],
  "statistics": {
    "total_active": 3,
    "by_severity": {
      "critical": 1,
      "high": 2,
      "medium": 0,
      "low": 0
    }
  },
  "last_updated": "2025-10-12T13:20:00Z"
}
```

### POST /api/alerts/{alert_id}/acknowledge
**Description:** Acknowledge an alert and add acknowledgment details

**Authentication:** Required
**Permissions:** Security Analyst role or higher
**CSRF Protection:** Required

**Path Parameters:**
- `alert_id` (integer): ID of the alert to acknowledge

**Request Body:**
```json
{
  "comment": "Acknowledged - investigating potential false positive",
  "estimated_resolution_time": "2 hours",
  "assigned_to": "security_analyst@company.com"
}
```

**Response 200:**
```json
{
  "success": true,
  "alert_id": 3001,
  "status": "acknowledged",
  "acknowledged_by": "security_analyst@company.com",
  "acknowledged_at": "2025-10-12T13:25:00Z",
  "comment": "Acknowledged - investigating potential false positive",
  "audit_trail": {
    "action": "alert_acknowledged",
    "user": "security_analyst@company.com",
    "timestamp": "2025-10-12T13:25:00Z",
    "compliance_logged": true
  }
}
```

### POST /api/alerts/{alert_id}/escalate
**Description:** Escalate alert to higher security level or different team

**Authentication:** Required
**Permissions:** Security Analyst role or higher
**CSRF Protection:** Required

**Request Body:**
```json
{
  "escalation_level": "high",
  "reason": "Potential security breach requires immediate attention",
  "escalate_to": "security_manager@company.com",
  "urgency": "immediate"
}
```

**Response 200:**
```json
{
  "success": true,
  "alert_id": 3001,
  "escalation_level": "high",
  "escalated_by": "security_analyst@company.com",
  "escalated_to": "security_manager@company.com",
  "escalated_at": "2025-10-12T13:30:00Z",
  "notification_sent": true,
  "sla_updated": {
    "new_response_time_minutes": 15,
    "new_resolution_time_hours": 1
  }
}
```

### POST /api/alerts/{alert_id}/resolve
**Description:** Mark alert as resolved with resolution details

**Authentication:** Required
**Permissions:** Security Analyst role or higher

**Request Body:**
```json
{
  "resolution": "False positive - legitimate user activity",
  "resolution_type": "false_positive",
  "actions_taken": [
    "Reviewed user activity logs",
    "Confirmed legitimate business access",
    "Updated detection rules"
  ],
  "prevent_recurrence": "Updated whitelist for user's IP range"
}
```

**Response 200:**
```json
{
  "success": true,
  "alert_id": 3001,
  "status": "resolved",
  "resolved_by": "security_analyst@company.com",
  "resolved_at": "2025-10-12T14:00:00Z",
  "resolution_time_minutes": 95,
  "compliance_documentation": {
    "incident_report_id": "INC_20251012_001",
    "stored_location": "s3://compliance-docs/incidents/2025/10/",
    "retention_period_years": 7
  }
}
```

### GET /api/alerts/ai-insights
**Description:** Get AI-powered alert insights and recommendations

**Authentication:** Required

**Response 200:**
```json
{
  "threat_summary": {
    "total_threats": 15,
    "critical_threats": 3,
    "automated_responses": 6,
    "false_positive_rate": 12.5,
    "avg_response_time": "4.2 minutes"
  },
  "predictive_analysis": {
    "risk_score": 75,
    "trend_direction": "increasing",
    "predicted_incidents": 2,
    "confidence_level": 87
  },
  "patterns_detected": [
    {
      "pattern_type": "Geographic Anomaly",
      "occurrences": 8,
      "severity": "medium"
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "recommendation": "Implement stricter rate limiting",
      "reason": "Detected unusual API access patterns"
    }
  ]
}
```

### GET /api/alerts/threat-intelligence
**Description:** Get real-time threat intelligence data

**Authentication:** Required

**Response 200:**
```json
{
  "active_threats": 12,
  "threat_level": "elevated",
  "recent_threats": [
    {
      "threat_type": "Brute Force Attack",
      "severity": "high",
      "first_detected": "2025-10-12T14:00:00Z",
      "affected_systems": 3
    }
  ],
  "mitigation_status": "active"
}
```

### GET /api/alerts/performance-metrics
**Description:** Get alert system performance metrics and AI effectiveness

**Authentication:** Required

**Response 200:**
```json
{
  "detection_accuracy": 94.5,
  "response_time_avg": "3.8 minutes",
  "false_positive_rate": 5.2,
  "ai_confidence": 89,
  "alerts_processed_24h": 247,
  "automated_resolution_rate": 42.3
}
```

---

## Smart Rules Engine APIs

The Smart Rules Engine provides AI-powered rule creation, optimization, and performance analytics.

### GET /api/smart-rules
**Description:** List all smart rules with performance analytics

**Authentication:** Required

**Response 200:**
```json
[
  {
    "id": 12,
    "agent_id": "enterprise-ai-generated",
    "action_type": "natural_language_enterprise_rule",
    "description": "Block API calls from suspicious geographic locations",
    "condition": "smart_analysis('geographic_anomaly') AND threat_detected",
    "action": "block_and_alert",
    "enabled": true,
    "created_at": "2025-10-12T10:00:00Z",
    "performance_metrics": {
      "trigger_count_24h": 15,
      "false_positive_rate": 2.1,
      "effectiveness_score": 94
    }
  }
]
```

### POST /api/smart-rules/generate-from-nl
**Description:** Generate smart rule from natural language description using AI

**Authentication:** Required
**Permissions:** Security Analyst role or higher

**Request Body:**
```json
{
  "description": "Alert me when any user accesses more than 100 files in 5 minutes",
  "severity": "high",
  "enabled": true,
  "context": {
    "department": "engineering",
    "environment": "production"
  }
}
```

**Response 200:**
```json
{
  "id": 13,
  "condition": "smart_analysis('Alert me when any user accesses more than 100 file') AND threat_detected",
  "action": "monitor_and_alert",
  "justification": "Enterprise-grade intelligent rule created from natural language: 'Alert me when any user accesses more than 100 file'. This rule implements advanced threat detection with smart analysis.",
  "confidence_score": 87,
  "generated_at": "2025-10-12T13:45:00Z",
  "ai_model_version": "gpt-4-enterprise",
  "estimated_performance": {
    "expected_false_positive_rate": 3.2,
    "expected_effectiveness": 91
  }
}
```

### GET /api/smart-rules/analytics
**Description:** Get comprehensive rule performance analytics

**Authentication:** Required

**Response 200:**
```json
{
  "total_rules": 6,
  "active_rules": 6,
  "avg_performance_score": 88.2,
  "total_triggers_24h": 170,
  "false_positive_rate": 4.5,
  "top_performing_rules": [
    {
      "id": 1,
      "name": "Data Exfiltration Block",
      "score": 94,
      "category": "data_protection"
    }
  ],
  "recommendations": [
    {
      "rule_id": 3,
      "recommendation": "Consider adjusting threshold from 50 to 75 for better accuracy",
      "confidence": 85
    }
  ],
  "performance_trends": {
    "7_day_average_score": 87.1,
    "improvement_percentage": 12.3
  }
}
```

### POST /api/smart-rules/optimize/{rule_id}
**Description:** Use AI to optimize rule performance and reduce false positives

**Authentication:** Required
**Permissions:** Admin role

**Path Parameters:**
- `rule_id` (integer): ID of the rule to optimize

**Response 200:**
```json
{
  "success": true,
  "rule_id": 12,
  "optimization_results": {
    "original_performance": 87,
    "optimized_performance": 94,
    "improvement_percentage": 8.0,
    "changes_made": [
      "Adjusted threshold from 5 to 7 failed attempts",
      "Added time window clustering",
      "Enhanced geographic correlation"
    ]
  },
  "ai_analysis": {
    "confidence": 92,
    "model_version": "optimization-v2.1",
    "training_data_points": 10000
  }
}
```

### GET /api/smart-rules/suggestions
**Description:** Get AI-powered rule suggestions based on system analysis

**Authentication:** Required

**Response 200:**
```json
[
  {
    "id": 1,
    "suggested_rule": "Block API calls from new geographic regions during off-hours",
    "confidence": 89,
    "reasoning": "ML pattern analysis shows 94% of off-hours geo-anomalies correlate with malicious activity",
    "category": "geographic_anomaly",
    "estimated_impact": "15-20% reduction in security incidents",
    "implementation_complexity": "low"
  }
]
```

---

## Enterprise User Management APIs

### GET /api/enterprise-users/users
**Description:** Get all enterprise users with role and permission information

**Authentication:** Required
**Permissions:** Admin role

**Response 200:**
```json
{
  "users": [
    {
      "id": 7,
      "email": "admin@owkai.com",
      "first_name": "System",
      "last_name": "Administrator",
      "department": "Engineering",
      "role": "admin",
      "is_active": true,
      "created_at": "2025-10-12T04:20:21Z",
      "last_login": "2025-10-12T13:45:00Z",
      "permissions": [
        "user_management",
        "policy_creation",
        "alert_management",
        "system_administration"
      ]
    }
  ],
  "pagination": {
    "total": 15,
    "page": 1,
    "per_page": 50
  }
}
```

### POST /api/enterprise-users/users
**Description:** Create new enterprise user

**Authentication:** Required
**Permissions:** Admin role

**Request Body:**
```json
{
  "email": "new_analyst@company.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "security_analyst",
  "department": "Security",
  "password": "TempPassword123!",
  "force_password_change": true
}
```

**Response 201:**
```json
{
  "id": 15,
  "email": "new_analyst@company.com",
  "role": "security_analyst",
  "created_at": "2025-10-12T14:00:00Z",
  "activation_required": true,
  "activation_link": "https://pilot.owkai.app/activate?token=abc123..."
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message description",
  "error_code": "AUTH_001",
  "timestamp": "2025-10-12T14:00:00Z",
  "request_id": "req_20251012_140000_123"
}
```

### Common HTTP Status Codes

**400 Bad Request**
- Invalid request format
- Missing required fields
- Invalid parameter values

**401 Unauthorized**
- Missing or invalid authentication
- Expired tokens
- Invalid credentials

**403 Forbidden**
- Insufficient permissions
- RBAC access denied
- CSRF token validation failed

**404 Not Found**
- Resource not found
- Invalid endpoint
- Deleted or non-existent ID

**429 Too Many Requests**
- Rate limit exceeded
- API quota exceeded

**500 Internal Server Error**
- Unexpected server error
- Database connection issues
- Third-party service failures

## Rate Limiting

### Default Limits
- **Authenticated Users:** 100 requests per minute
- **Admin Users:** 200 requests per minute
- **Burst Allowance:** 150% of rate limit for 30 seconds

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

### Rate Limit Response (429)
```json
{
  "detail": "Rate limit exceeded",
  "limit": 100,
  "reset_time": "2025-10-12T14:01:00Z",
  "retry_after_seconds": 60
}
```

## SDK & Client Libraries

### Python SDK
```python
from owkai_client import OWKAIClient

client = OWKAIClient(
    base_url="https://pilot.owkai.app",
    api_key="your_api_key"
)

# Authenticate
auth_response = client.auth.login("admin@company.com", "password")

# Get alerts
alerts = client.alerts.list(severity="high")

# Authorize action
result = client.authorization.approve_action(
    action_id=1003,
    comment="Approved after review"
)
```

### JavaScript SDK
```javascript
import { OWKAIClient } from '@owkai/client';

const client = new OWKAIClient({
  baseURL: 'https://pilot.owkai.app',
  apiKey: 'your_api_key'
});

// Authenticate
const authResponse = await client.auth.login({
  email: 'admin@company.com',
  password: 'password'
});

// Get dashboard data
const dashboard = await client.authorization.getDashboard();

// Create smart rule
const rule = await client.smartRules.createFromNL({
  description: 'Block suspicious file access patterns'
});
```

---

This API reference provides comprehensive documentation for integrating with the OW-AI Platform. For additional support or questions, contact our enterprise support team.