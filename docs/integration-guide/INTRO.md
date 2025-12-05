# Welcome to Ascend

Ascend is the enterprise AI governance platform that provides comprehensive oversight, control, and compliance for your AI agents.

## What is Ascend?

Ascend acts as a governance layer between your AI agents and the systems they interact with. Every agent action is:

- **Evaluated** against risk scoring algorithms
- **Checked** against your organization's policies
- **Routed** through approval workflows when needed
- **Logged** for complete audit trails

## Platform Capabilities

### Enterprise-Grade Security

- SOC 2 Type II compliant architecture
- HIPAA compliant data handling
- GDPR compliant with data rights APIs
- PCI-DSS compliant for financial data
- Multi-tenant data isolation with organization_id filtering

### Complete Visibility

- Real-time monitoring of all AI actions (484 API endpoints)
- Risk scoring for every operation (0-100 scale)
- Comprehensive audit logging with SIEM integration
- Anomaly detection service
- System diagnostics with health monitoring

### Flexible Control

- Customizable policies with condition engine
- Configurable approval workflows
- Role-based access control with Cognito integration
- Enterprise webhooks and notifications

## Quick Links

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Getting Started</h3>
      </div>
      <div className="card__body">
        <p>Get up and running with Ascend in 5 minutes.</p>
      </div>
      <div className="card__footer">
        <a className="button button--primary button--block" href="/getting-started/quick-start">Quick Start Guide</a>
      </div>
    </div>
  </div>
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Core Concepts</h3>
      </div>
      <div className="card__body">
        <p>Understand how Ascend works under the hood.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/core-concepts/how-ascend-works">Learn More</a>
      </div>
    </div>
  </div>
</div>

<div className="row">
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>REST API</h3>
      </div>
      <div className="card__body">
        <p>Complete REST API with 484 endpoints.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/api/overview">API Reference</a>
      </div>
    </div>
  </div>
  <div className="col col--6">
    <div className="card margin-bottom--lg">
      <div className="card__header">
        <h3>Integrations</h3>
      </div>
      <div className="card__body">
        <p>Connect with LangChain, MCP, and custom agents.</p>
      </div>
      <div className="card__footer">
        <a className="button button--secondary button--block" href="/integrations/overview">Browse Integrations</a>
      </div>
    </div>
  </div>
</div>

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR AI AGENTS                                │
│   LangChain • MCP Server • Custom Agents • Claude Code          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   REST API Call   │
                    │   (API Key Auth)  │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                      ASCEND PLATFORM                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Risk Engine │  │Policy Engine│  │  Workflows  │              │
│  │ (61 services)│  │(conditions) │  │ (approvals) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Audit Logs  │  │   SIEM      │  │ Diagnostics │              │
│  │ (immutable) │  │(Splunk/DD)  │  │  (health)   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   YOUR SYSTEMS    │
                    │   Databases, APIs │
                    └───────────────────┘
```

## Key Features

### Risk Scoring

Every action is assigned a risk score (0-100) based on:

- Action type and sensitivity
- Resource classification
- Historical patterns
- Context analysis
- Agent trust level

**Source:** `services/enterprise_risk_calculator.py`, `services/enterprise_risk_calculator_v2.py`

[Learn about Risk Scoring](/core-concepts/risk-scoring)

### Policy Engine

Define governance rules with flexible conditions:

```python
# Example policy structure from unified_governance_routes.py
{
    "name": "Restrict PII Access",
    "conditions": {
        "resource_type": "customer_data",
        "contains_pii": True
    },
    "action": "require_approval",
    "approvers": ["data-protection-team"]
}
```

**Source:** `services/condition_engine.py`, `services/unified_policy_evaluation_service.py`

[Learn about Policies](/core-concepts/how-ascend-works)

### Approval Workflows

Configure human-in-the-loop approvals:

- Single approval
- Multi-level escalation
- Workflow configuration per organization
- Time-based routing with SLA monitoring

**Source:** `services/workflow_service.py`, `services/workflow_approver_service.py`, `services/sla_monitor.py`

[Learn about Workflows](/core-concepts/approval-workflows)

### Audit Logging

Complete, immutable audit trails:

- Every action logged to `audit_logs` table
- Organization-level isolation
- SIEM integration (Splunk CIM, Datadog)
- Compliance report exports (CSV, PDF)

**Source:** `services/immutable_audit_service.py`, `routes/audit_routes.py`

[Learn about Audit Logging](/core-concepts/audit-logging)

## Backend Services (61 Total)

| Category | Services | Description |
|----------|----------|-------------|
| Risk & Scoring | `enterprise_risk_calculator.py`, `cvss_calculator.py` | Risk scoring algorithms |
| Policy | `condition_engine.py`, `policy_conflict_resolver.py` | Policy evaluation |
| Workflow | `workflow_service.py`, `sla_monitor.py` | Approval workflows |
| Security | `anomaly_detection_service.py`, `circuit_breaker_service.py` | Security controls |
| Integration | `servicenow_service.py`, `webhook_service.py` | External integrations |
| Compliance | `data_rights_service.py`, `compliance_export_service.py` | GDPR/compliance |

## Route Modules (51 Total)

| Module | Prefix | Description |
|--------|--------|-------------|
| `authorization_routes.py` | `/api/authorization` | Agent action submission |
| `agent_routes.py` | `/api/agent-*` | Agent activity |
| `diagnostics_routes.py` | `/api/diagnostics` | System health |
| `webhook_routes.py` | `/api/webhooks` | Enterprise webhooks |
| `siem_integration.py` | `/api/siem-integration` | SIEM connectivity |
| `servicenow_routes.py` | `/api/servicenow` | ServiceNow integration |
| `data_rights_routes.py` | `/api/data-rights` | GDPR data rights |
| `compliance_export_routes.py` | `/api/compliance-export` | Compliance reports |

## Enterprise Features

- **SSO/SAML**: Enterprise identity integration via AWS Cognito
- **SIEM Integration**: Splunk CIM, Datadog metrics export
- **Multi-Tenancy**: Complete data isolation with `organization_id`
- **Compliance**: SOC 2, HIPAA, GDPR, PCI-DSS aligned

[Learn about Enterprise](/enterprise/overview)

## Get Help

- **Documentation**: You're here!
- **API Reference**: Available at your deployment URL `/docs`
- **Support**: Contact your account team

## Ready to Start?

<a className="button button--primary button--lg" href="/getting-started/quick-start">
  Get Started in 5 Minutes
</a>
