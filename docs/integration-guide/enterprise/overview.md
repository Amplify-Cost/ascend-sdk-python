# Enterprise Overview

OW-kai provides enterprise-grade integrations for authentication, incident management, security monitoring, and compliance reporting. All integrations are built with multi-tenant isolation, full audit trails, and SOC 2 Type II compliant security controls.

## Integration Status

| Integration | Status | Protocol/Standard | Source File |
|------------|--------|-------------------|-------------|
| **Authentication** |
| Single Sign-On | Production | OIDC, SAML | `routes/sso_routes.py` |
| AWS Cognito | Production | OAuth 2.0 | `routes/auth.py` |
| **Incident Management** |
| ServiceNow | Production | REST API, OAuth 2.0 | `routes/servicenow_routes.py` |
| **Notifications** |
| Slack | Production | Webhooks | `routes/notification_routes.py` |
| Microsoft Teams | Production | Webhooks | `routes/notification_routes.py` |
| Webhooks | Production | HTTP/S, HMAC-SHA256 | `routes/webhook_routes.py` |
| **Security Monitoring** |
| SIEM Integration | Production | Splunk HEC, Generic | `routes/siem_integration.py` |
| Splunk CIM Export | Production | Common Information Model | `models_diagnostics.py` |
| Datadog Metrics | Production | Metrics API | `models_diagnostics.py` |
| **Compliance** |
| Compliance Exports | Production | SOX, PCI-DSS, HIPAA, GDPR | `routes/compliance_export_routes.py` |
| **Analytics** |
| Real-time Analytics | Production | WebSocket, REST | `routes/analytics_routes.py` |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     OW-kai Enterprise Platform                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    IDENTITY LAYER                                 │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                            │  │
│  │  │  Okta   │  │  Azure  │  │  Google │                            │  │
│  │  │  OIDC   │  │   AD    │  │ Workspace│                            │  │
│  │  └────┬────┘  └────┬────┘  └────┬────┘                            │  │
│  │       └───────────┬┴───────────┬┘                                  │  │
│  │              ┌────▼────────────▼────┐                              │  │
│  │              │   SSO Router Layer   │ (routes/sso_routes.py)       │  │
│  │              └──────────┬───────────┘                              │  │
│  └─────────────────────────┼──────────────────────────────────────────┘  │
│                            │                                              │
│  ┌─────────────────────────▼──────────────────────────────────────────┐  │
│  │              Multi-Tenant Core Services                             │  │
│  │  - Organization Isolation (dependencies.py::get_organization_filter)│  │
│  │  - Credential Encryption (AES-256)                                  │  │
│  │  - Audit Logging (immutable trails)                                 │  │
│  └─────────────────────────┬──────────────────────────────────────────┘  │
│                            │                                              │
│  ┌─────────────────────────▼──────────────────────────────────────────┐  │
│  │                   ENTERPRISE INTEGRATIONS                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │  │ ServiceNow  │  │    SIEM     │  │ Slack/Teams │                 │  │
│  │  │ (OAuth2)    │  │  (Splunk)   │  │ (Webhooks)  │                 │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │  │
│  │  ┌─────────────┐  ┌─────────────┐                                   │  │
│  │  │ Compliance  │  │  Analytics  │                                   │  │
│  │  │  (Export)   │  │ (WebSocket) │                                   │  │
│  │  └─────────────┘  └─────────────┘                                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Security & Compliance

### Compliance Standards

| Standard | Status | Implementation |
|----------|--------|----------------|
| SOC 2 Type II | Compliant | Multi-tenant isolation, audit trails |
| HIPAA | Compliant | Data encryption, access controls |
| PCI-DSS | Compliant | Secure API endpoints, token management |
| GDPR | Compliant | Data isolation, right to deletion |
| SOX | Compliant | Immutable audit logs, segregation of duties |

**Note**: Changed from "Certified" to "Compliant" per SEC-081 requirements.

### Data Security

- **Encryption at Rest**: AES-256
- **Encryption in Transit**: TLS 1.2+
- **Key Management**: Environment-based encryption keys
- **Data Isolation**: Multi-tenant with organization-level filtering
- **Audit Trails**: Immutable logs for all operations

## Quick Start

### 1. Authentication (SSO)

Enable single sign-on with your identity provider:

```bash
GET /api/auth/sso/providers
# Returns: Okta, Azure AD, Google Workspace

POST /api/auth/sso/login/{provider}
```

Source: `routes/sso_routes.py` (lines 38-66, 67-112)

### 2. ServiceNow Integration

Create a ServiceNow connection:

```bash
POST /api/servicenow/connections
{
  "name": "Production ServiceNow",
  "instance_url": "https://company.service-now.com",
  "auth_type": "oauth2",
  "username": "service_account",
  "password": "encrypted"
}
```

Source: `routes/servicenow_routes.py` (lines 45-109)

### 3. SIEM Integration

Configure Splunk HTTP Event Collector:

```bash
POST /api/siem-integration/configure
{
  "siem_type": "splunk",
  "host": "splunk.company.com",
  "port": 8088,
  "api_token": "your-hec-token"
}
```

Source: `routes/siem_integration.py` (lines 81-136)

### 4. Notifications (Slack/Teams)

Create a notification channel:

```bash
POST /api/notifications/channels
{
  "name": "Security Alerts",
  "channel_type": "slack",
  "webhook_url": "https://hooks.slack.com/...",
  "subscribed_events": ["alert.critical", "action.escalated"]
}
```

Source: `routes/notification_routes.py` (lines 105-189)

## Data Export Formats

### Splunk CIM

Export diagnostics to Splunk Common Information Model:

```python
# From models_diagnostics.py (lines 170-190)
DiagnosticAuditLog.to_splunk_cim() → {
  "event_id": "diag_4_20251204_143052_a1b2c3d4",
  "timestamp": "2025-12-04T14:30:52Z",
  "source": "owkai_diagnostics",
  "sourcetype": "owkai:diagnostic:api_health",
  "severity": "info",
  "health_score": 98.5
}
```

### Datadog Metrics

Export metrics to Datadog monitoring:

```python
# From models_diagnostics.py (lines 192-226)
DiagnosticAuditLog.to_datadog_metrics() → [
  {
    "metric": "owkai.diagnostics.health_score",
    "type": "gauge",
    "points": [[timestamp, 98.5]],
    "tags": ["org_id:4", "status:healthy"]
  }
]
```

## API Rate Limits

| Integration | Default Limit | Configurable | Source |
|------------|---------------|--------------|--------|
| ServiceNow | 100 req/min | Yes | `services/servicenow_service.py` |
| Webhooks | 100 events/min | Yes | `routes/webhook_routes.py` |
| Notifications | 60 events/min | Yes | `routes/notification_routes.py` |
| SIEM | Unlimited | N/A | `routes/siem_integration.py` |
| Analytics | 10 req/sec | Fixed | `routes/analytics_routes.py` |

## Health Monitoring

All integrations expose health check endpoints:

```bash
GET /api/servicenow/metrics         # ServiceNow stats (routes/servicenow_routes.py:692)
GET /api/siem-integration/status    # SIEM connection (routes/siem_integration.py:45)
GET /api/webhooks/metrics            # Webhook delivery (routes/webhook_routes.py:616)
GET /api/notifications/metrics       # Notification rates (routes/notification_routes.py:710)
```

## Compliance Exports

Generate compliance reports for auditors:

```bash
POST /api/compliance-export/exports
{
  "framework": "sox",
  "report_type": "audit_log",
  "export_format": "json",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

Supported frameworks: SOX, PCI-DSS, HIPAA, GDPR, SOC2, NIST, ISO 27001

Source: `routes/compliance_export_routes.py` (lines 91-157)

## Next Steps

1. **Authentication**: [Configure SSO](./sso.md) with OIDC or SAML
2. **Incident Management**: [Set up ServiceNow](./servicenow.md) for automatic ticket creation
3. **Security Monitoring**: [Integrate Splunk](./splunk.md) for real-time event streaming
4. **Notifications**: [Configure Slack/Teams](./slack-teams.md) for alert delivery
5. **Compliance**: [Enable compliance exports](./compliance.md) for audit readiness

## Support

For integration assistance:
- Technical documentation in each integration guide
- Source code references included for transparency
- Compliance framework mappings for regulatory alignment
