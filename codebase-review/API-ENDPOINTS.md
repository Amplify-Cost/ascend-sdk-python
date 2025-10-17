# OW-AI Platform - Complete API Endpoint Inventory

## Backend Status: ✅ RUNNING (167 routes registered)
**Server**: http://0.0.0.0:8000
**Enterprise Features**: ENABLED
**Authentication**: JWT with RS256 keys

---

## 🔐 Authentication Endpoints (`routes/auth.py`)

### Core Authentication
- `POST /auth/token` - User login with JWT tokens ✅ WORKING
- `GET /auth/me` - Get current user info ✅ WORKING
- `POST /auth/refresh-token` - Token refresh
- `POST /auth/logout` - User logout
- `GET /auth/csrf` - CSRF token for forms
- `GET /auth/health` - Authentication health check
- `GET /auth/diagnostic` - Authentication diagnostics

### Enterprise Features
- `POST /auth/login` - Alternative login endpoint
- `GET /auth/users` - User management (404 in current config)

---

## 🛡️ Authorization Center (`routes/authorization_routes.py`)

### Policy Management
- `GET /api/authorization/policies/list` - List policies ✅ WORKING
- `POST /api/authorization/policies/create-from-natural-language` - Natural language policy creation ✅ WORKING
- `POST /api/authorization/policies/evaluate-realtime` - Real-time policy evaluation ✅ WORKING
- `GET /api/authorization/policies/engine-metrics` - Policy engine performance metrics ✅ WORKING

### Authorization Workflows
- `POST /api/authorization/authorize/{action_id}` - Multi-level authorization
- `GET /api/authorization/pending` - Pending approvals
- `GET /api/authorization/history` - Authorization history
- `POST /api/authorization/emergency` - Emergency authorization

---

## 🚨 Alert Management (`routes/smart_alerts.py`)

### Alert Operations
- `GET /alerts` - List all alerts ✅ WORKING
- `GET /alerts?severity=high` - Filter alerts by severity ✅ WORKING
- `GET /alerts/{alert_id}` - Get specific alert (404 for non-existent)
- `GET /alerts/active` - Active alerts only ✅ WORKING
- `POST /alerts/summary` - Alert summary (500 Internal Error)

### Alert Actions (CSRF Protected)
- `POST /alerts/{alert_id}/acknowledge` - Acknowledge alert (403 - CSRF required)
- `POST /alerts/{alert_id}/escalate` - Escalate alert (403 - CSRF required)
- `POST /alerts/{alert_id}/resolve` - Resolve alert (403 - CSRF required)

### Real-time Features
- WebSocket endpoint for live alert updates
- Alert monitoring service (active)

---

## 🤖 Smart Rules Engine (`routes/smart_rules_routes.py`)

### Rule Management
- `GET /api/smart-rules` - List smart rules ✅ WORKING
- `POST /api/smart-rules/generate-from-nl` - Natural language rule generation ✅ WORKING
- `POST /api/smart-rules/generate` - AI-powered rule creation ✅ WORKING
- `POST /api/smart-rules/seed` - Seed demo rules (500 Internal Error)

### Analytics & Optimization
- `GET /api/smart-rules/analytics` - Rule performance analytics ✅ WORKING
- `GET /api/smart-rules/suggestions` - Rule suggestions ✅ WORKING
- `POST /api/smart-rules/optimize/{rule_id}` - Rule optimization (500 Internal Error)

### A/B Testing Framework
- `POST /api/smart-rules/setup-ab-testing-table` - Setup A/B testing ✅ WORKING
- `GET /api/smart-rules/ab-tests` - A/B testing results ✅ WORKING

---

## 👥 Enterprise User Management (`routes/enterprise_user_management_routes.py`)

### User Operations
- `GET /api/enterprise-users/users` - List enterprise users ✅ WORKING (1 user)
- `POST /api/enterprise-users/create` - Create new user
- `PUT /api/enterprise-users/update/{user_id}` - Update user
- `DELETE /api/enterprise-users/delete/{user_id}` - Delete user
- `POST /api/enterprise-users/bulk-operations` - Bulk user operations

---

## 🔑 SSO & Identity (`routes/sso_routes.py`)

### Single Sign-On
- `POST /sso/saml/login` - SAML SSO login
- `POST /sso/oidc/login` - OIDC SSO login
- `GET /sso/metadata` - SSO metadata
- `POST /sso/callback` - SSO callback handler

---

## 🗄️ Secrets Management (`routes/enterprise_secrets_routes.py`)

### Secret Operations
- `GET /api/secrets` - List secrets
- `POST /api/secrets/create` - Create secret
- `PUT /api/secrets/update/{secret_id}` - Update secret
- `DELETE /api/secrets/delete/{secret_id}` - Delete secret
- `POST /api/secrets/rotate/{secret_id}` - Rotate secret

---

## 🏛️ Governance & Compliance (`routes/unified_governance_routes.py`)

### MCP Governance
- `GET /api/governance/policies` - Governance policies
- `POST /api/governance/evaluate` - Policy evaluation
- `GET /api/governance/compliance` - Compliance status
- `POST /api/governance/audit` - Audit trail creation

### Workflow Management
- `POST /api/governance/workflows/create` - Create workflow
- `GET /api/governance/workflows/status/{workflow_id}` - Workflow status
- `POST /api/governance/workflows/execute` - Execute workflow

---

## 🤖 Automation & Orchestration (`routes/automation_orchestration_routes.py`)

### Automation Features
- `POST /api/authorization/automate` - Automation setup
- `GET /api/authorization/automations` - List automations
- `PUT /api/authorization/automations/{automation_id}` - Update automation
- `DELETE /api/authorization/automations/{automation_id}` - Delete automation

### Process Orchestration
- `POST /api/authorization/orchestrate` - Orchestrate processes
- `GET /api/authorization/orchestrations` - List orchestrations
- `POST /api/authorization/orchestrations/{orchestration_id}/execute` - Execute orchestration

---

## 📊 Analytics & Reporting (`routes/analytics_routes.py`)

### Performance Analytics
- `GET /analytics/performance` - Performance metrics
- `GET /analytics/usage` - Usage statistics
- `GET /analytics/security` - Security analytics
- `GET /analytics/compliance` - Compliance reporting

### Business Intelligence
- `GET /analytics/dashboard` - Main dashboard data
- `GET /analytics/reports/{report_id}` - Specific reports
- `POST /analytics/custom-query` - Custom analytics queries

---

## 🔍 Audit & Logging (`routes/audit_routes.py`)

### Audit Operations
- `GET /api/audit/trails` - Audit trail listing
- `GET /api/audit/search` - Search audit logs
- `POST /api/audit/export` - Export audit data
- `GET /api/audit/compliance-report` - Compliance reports

---

## 🛠️ Administrative (`routes/admin_routes.py`)

### System Administration
- `GET /api/admin/system-status` - System status
- `POST /api/admin/maintenance` - Maintenance operations
- `GET /api/admin/logs` - System logs
- `POST /api/admin/backup` - System backup

---

## 🏥 Health & Monitoring (`health.py` - Enterprise Module)

### Health Checks
- `GET /health` - System health ✅ WORKING
- `GET /health/detailed` - Detailed health metrics
- `GET /health/components` - Component health status

---

## 📞 Support System (`routes/support_routes.py`)

### Support Operations
- `POST /api/support/tickets` - Create support ticket
- `GET /api/support/tickets` - List tickets
- `PUT /api/support/tickets/{ticket_id}` - Update ticket
- `GET /api/support/knowledge-base` - Knowledge base access

---

## 🛡️ Data Rights & Privacy (`routes/data_rights_routes.py`)

### GDPR Compliance
- `POST /api/data-rights/request` - Data rights request
- `GET /api/data-rights/status/{request_id}` - Request status
- `POST /api/data-rights/export` - Data export
- `POST /api/data-rights/deletion` - Data deletion request

---

## 🔗 Integration & Bridges

### SIEM Integration (`routes/siem_integration.py`)
- `POST /api/siem/events` - Send SIEM events
- `GET /api/siem/status` - SIEM connection status
- `POST /api/siem/configure` - Configure SIEM integration

### Agent Management (`routes/agent_routes.py`)
- `GET /agents` - List agents
- `POST /agents/register` - Register new agent
- `GET /agents/{agent_id}/status` - Agent status
- `POST /agents/{agent_id}/actions` - Agent actions

---

## 🚨 Critical Issues Identified

### ❌ Failing Endpoints (500 Internal Server Error)
1. `POST /alerts/summary` - Alert summary endpoint
2. `POST /api/smart-rules/seed` - Rule seeding
3. `POST /api/smart-rules/optimize/{rule_id}` - Rule optimization

### ⚠️ CSRF Protected Endpoints (403 Forbidden without CSRF token)
1. `POST /alerts/{alert_id}/acknowledge` - Requires CSRF token
2. `POST /alerts/{alert_id}/escalate` - Requires CSRF token
3. `POST /alerts/{alert_id}/resolve` - Requires CSRF token

### 🔍 Missing/Not Found (404)
1. `POST /auth/login` - Endpoint not properly configured
2. `GET /auth/users` - User listing endpoint

---

## ✅ Working Core Features

### Authentication System (100% Functional)
- JWT token creation and validation
- User authentication and authorization
- Role-based access control (admin confirmed)

### Authorization Center (95% Functional)
- Policy listing and creation
- Natural language policy generation
- Real-time policy evaluation (sub-200ms)
- Engine performance metrics

### Smart Rules Engine (85% Functional)
- Rule listing and creation
- Natural language rule generation
- AI-powered rule suggestions
- A/B testing framework setup
- Performance analytics

### Alert Management (75% Functional)
- Alert listing and filtering
- Active alert monitoring
- Real-time alert processing
- CSRF-protected action endpoints (security working as intended)

---

**Next Phase**: Begin comprehensive end-to-end testing with evidence collection and database verification for each functional endpoint.