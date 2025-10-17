# OW-AI Platform - Enterprise Technical Documentation

Generated from production codebase

---

## 1. API Endpoints

**Total Endpoints:** 191


### Ab-Test Endpoints

- **POST** `/ab-test`

### Ab-Test Endpoints

- **GET** `/ab-test/{test_id}`

### Ab-Test Endpoints

- **DELETE** `/ab-test/{test_id}`

### Ab-Test Endpoints

- **GET** `/ab-test/{test_id}`

### Ab-Tests Endpoints

- **GET** `/ab-tests`

### Access Endpoints

- **POST** `/access/request`

### Access Endpoints

- **GET** `/access/{request_id}/data`

### Actions Endpoints

- **GET** `/actions/all`

### Actions Endpoints

- **GET** `/actions/pending`

### Actions Endpoints

- **POST** `/actions/{action_id}/approve`

### Admin Endpoints

- **GET** `/admin/unified-report`

### Admin Endpoints

- **GET** `/admin/users`

### Admin Endpoints

- **DELETE** `/admin/users/{user_id}`

### Agent-Action Endpoints

- **POST** `/agent-action`

### Agent-Action Endpoints

- **POST** `/agent-action/{action_id}/approve`

### Agent-Action Endpoints

- **POST** `/agent-action/{action_id}/false-positive`

### Agent-Action Endpoints

- **POST** `/agent-action/{action_id}/reject`

### Agent-Actions Endpoints

- **GET** `/agent-actions`

### Agent-Activity Endpoints

- **GET** `/agent-activity`

### Agent-Control Endpoints

- **POST** `/agent-control/authorize-with-audit/{action_id}`

### Agent-Control Endpoints

- **POST** `/agent-control/authorize/{action_id}`

### Agent-Control Endpoints

- **GET** `/agent-control/dashboard`

### Agent-Control Endpoints

- **GET** `/agent-control/debug/policies`

### Agent-Control Endpoints

- **GET** `/agent-control/execution-history`

### Agent-Control Endpoints

- **GET** `/agent-control/mcp-discovery/health-monitor`

### Agent-Control Endpoints

- **POST** `/agent-control/mcp-discovery/scan-network`

### Agent-Control Endpoints

- **GET** `/agent-control/mcp-discovery/server-status`

### Agent-Control Endpoints

- **GET** `/agent-control/pending-actions`

### Agent-Control Endpoints

- **POST** `/agent-control/policies/create-from-natural-language`

### Agent-Control Endpoints

- **POST** `/agent-control/policies/{policy_id}/deploy`

### Agent-Control Endpoints

- **POST** `/agent-control/policies/{policy_id}/rollback/{target_version_id}`

### Agent Endpoints

- **POST** `/agent/actions/pre-execute-check`

### Alerts Endpoints

- **GET** `/alerts`

### Alerts Endpoints

- **GET** `/alerts/active`

### Alerts Endpoints

- **GET** `/alerts/count`

### Alerts Endpoints

- **POST** `/alerts/create-test-data`

### Alerts Endpoints

- **POST** `/alerts/summary`

### Alerts Endpoints

- **POST** `/alerts/summary-text`

### Alerts Endpoints

- **POST** `/alerts/{alert_id}/acknowledge`

### Alerts Endpoints

- **POST** `/alerts/{alert_id}/resolve`

### Analytics Endpoints

- **GET** `/analytics`

### Analytics Endpoints

- **GET** `/analytics/dashboard`

### Analytics Endpoints

- **GET** `/analytics/trends`

### Api Endpoints

- **POST** `/api/authorization/automation/playbook/{playbook_id}/toggle`

### Api Endpoints

- **POST** `/api/authorization/automation/playbook/{playbook_id}/toggle`

### Api Endpoints

- **GET** `/api/authorization/automation/playbooks`

### Api Endpoints

- **GET** `/api/authorization/automation/playbooks`

### Api Endpoints

- **POST** `/api/authorization/execute/{action_id}`

### Api Endpoints

- **POST** `/api/authorization/execute/{action_id}`

### Api Endpoints

- **GET** `/api/authorization/mcp-governance/actions`

### Api Endpoints

- **POST** `/api/authorization/mcp-governance/evaluate-action`

### Api Endpoints

- **GET** `/api/authorization/orchestration/active-workflows`

### Api Endpoints

- **GET** `/api/authorization/orchestration/active-workflows`

### Api Endpoints

- **GET** `/api/enterprise-users/analytics`

### Api Endpoints

- **GET** `/api/enterprise-users/audit-logs`

### Api Endpoints

- **POST** `/api/enterprise-users/generate-report`

### Api Endpoints

- **POST** `/api/enterprise-users/reports/download/{report_id}`

### Api Endpoints

- **GET** `/api/enterprise-users/reports/library`

### Api Endpoints

- **GET** `/api/enterprise-users/reports/scheduled`

### Api Endpoints

- **GET** `/api/enterprise-users/roles`

### Api Endpoints

- **POST** `/api/enterprise-users/roles`

### Api Endpoints

- **GET** `/api/enterprise-users/users`

### Api Endpoints

- **POST** `/api/enterprise-users/users`

### Api Endpoints

- **PUT** `/api/enterprise-users/users/{user_id}`

### Api Endpoints

- **DELETE** `/api/enterprise-users/users/{user_id}`

### Api Endpoints

- **GET** `/api/mcp-governance/actions`

### Api Endpoints

- **POST** `/api/mcp-governance/evaluate-action`

### Api Endpoints

- **POST** `/api/siem-integration/bulk-forward`

### Api Endpoints

- **POST** `/api/siem-integration/configure`

### Api Endpoints

- **POST** `/api/siem-integration/forward-authorization/{action_id}`

### Api Endpoints

- **GET** `/api/siem-integration/health`

### Api Endpoints

- **GET** `/api/siem-integration/metrics`

### Api Endpoints

- **GET** `/api/siem-integration/query-events`

### Api Endpoints

- **POST** `/api/siem-integration/send-event`

### Api Endpoints

- **GET** `/api/siem-integration/status`

### Api Endpoints

- **POST** `/api/siem-integration/test-connection`

### Api Endpoints

- **POST** `/api/siem-integration/threat-intelligence`

### Audit-Trail Endpoints

- **GET** `/audit-trail`

### Audit Endpoints

- **GET** `/audit/health`

### Audit Endpoints

- **POST** `/audit/log`

### Audit Endpoints

- **GET** `/audit/logs`

### Audit Endpoints

- **POST** `/audit/verify-integrity`

### Auth Endpoints

- **GET** `/auth/diagnostic`

### Auth Endpoints

- **GET** `/auth/health`

### Auth Endpoints

- **POST** `/auth/logout`

### Auth Endpoints

- **GET** `/auth/me`

### Auth Endpoints

- **POST** `/auth/refresh-token`

### Auth Endpoints

- **GET** `/auth/sso/callback/{provider}`

### Auth Endpoints

- **GET** `/auth/sso/login/{provider}`

### Auth Endpoints

- **POST** `/auth/sso/logout`

### Auth Endpoints

- **GET** `/auth/sso/providers`

### Auth Endpoints

- **GET** `/auth/sso/user-profile`

### Auth Endpoints

- **POST** `/auth/token`

### Authorization Endpoints

- **GET** `/authorization/policies/engine-metrics`

### Authorization Endpoints

- **POST** `/authorization/policies/evaluate-realtime`

### Automation Endpoints

- **GET** `/automation/playbooks`

### Compliance Endpoints

- **GET** `/compliance/report`

### Consent Endpoints

- **POST** `/consent/record`

### Create-Policy Endpoints

- **POST** `/create-policy`

### Csrf Endpoints

- **GET** `/csrf`

### Dashboard Endpoints

- **GET** `/dashboard/pending-approvals`

### Debug Endpoints

- **GET** `/debug`

### Debug-Ab-Tests-Table Endpoints

- **GET** `/debug-ab-tests-table`

### Debug Endpoints

- **GET** `/debug/check-admin`

### Debug Endpoints

- **POST** `/debug/seed-test-data`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/audit-trail`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/compliance-report`

### Enterprise Endpoints

- **POST** `/enterprise/secrets/emergency-rotation`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/health`

### Enterprise Endpoints

- **POST** `/enterprise/secrets/rotate`

### Enterprise Endpoints

- **POST** `/enterprise/secrets/rotate-all`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/rotation-history`

### Enterprise Endpoints

- **POST** `/enterprise/secrets/schedule`

### Enterprise Endpoints

- **DELETE** `/enterprise/secrets/schedule/{secret_name}`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/schedules`

### Enterprise Endpoints

- **GET** `/enterprise/secrets/status`

### Enterprise Endpoints

- **POST** `/enterprise/secrets/validate-secrets`

### Enterprise Endpoints

- **POST** `/enterprise/siem/configure`

### Enterprise Endpoints

- **DELETE** `/enterprise/siem/disconnect`

### Enterprise Endpoints

- **POST** `/enterprise/siem/send-test-event`

### Enterprise Endpoints

- **GET** `/enterprise/siem/status`

### Enterprise Endpoints

- **GET** `/enterprise/siem/supported-integrations`

### Enterprise Endpoints

- **POST** `/enterprise/siem/test-connection`

### Erasure Endpoints

- **POST** `/erasure/request`

### Erasure Endpoints

- **POST** `/erasure/{request_id}/execute`

### Evaluate Endpoints

- **POST** `/evaluate`

### Execute Endpoints

- **POST** `/execute`

### Executive Endpoints

- **GET** `/executive/dashboard`

### Feedback Endpoints

- **GET** `/feedback/{rule_id}`

### Feedback Endpoints

- **POST** `/feedback/{rule_id}`

### Generate Endpoints

- **POST** `/generate`

### Generate-From-Nl Endpoints

- **POST** `/generate-from-nl`

### Generate-Smart-Rule Endpoints

- **POST** `/generate-smart-rule`

### Health Endpoints

- **GET** `/health`

### Health Endpoints

- **GET** `/health`

### Health Endpoints

- **GET** `/health`

### Lineage Endpoints

- **POST** `/lineage/record`

### Lineage Endpoints

- **GET** `/lineage/subject/{subject_identifier}`

### Logout Endpoints

- **POST** `/logout`

### Logs Endpoints

- **GET** `/logs`

### Logs Endpoints

- **GET** `/logs`

### Mcp-Governance Endpoints

- **POST** `/mcp-governance/evaluate-action`

### Mcp Endpoints

- **GET** `/mcp/actions`

### Mcp Endpoints

- **POST** `/mcp/actions/assess-risk-enterprise`

### Mcp Endpoints

- **POST** `/mcp/actions/ingest`

### Me Endpoints

- **GET** `/me`

### Optimize Endpoints

- **POST** `/optimize/{rule_id}`

### Orchestration Endpoints

- **GET** `/orchestration/active-workflows`

### Performance Endpoints

- **GET** `/performance/system`

### Policies Endpoints

- **POST** `/policies`

### Policies Endpoints

- **GET** `/policies`

### Policies Endpoints

- **GET** `/policies`

### Policies Endpoints

- **GET** `/policies/actions/types`

### Policies Endpoints

- **POST** `/policies/compile`

### Policies Endpoints

- **POST** `/policies/custom/build`

### Policies Endpoints

- **POST** `/policies/enforce`

### Policies Endpoints

- **GET** `/policies/enforcement-stats`

### Policies Endpoints

- **GET** `/policies/engine-metrics`

### Policies Endpoints

- **POST** `/policies/evaluate-realtime`

### Policies Endpoints

- **POST** `/policies/from-template`

### Policies Endpoints

- **GET** `/policies/resources/types`

### Policies Endpoints

- **GET** `/policies/templates`

### Policies Endpoints

- **GET** `/policies/templates/{template_id}`

### Policies Endpoints

- **PUT** `/policies/{policy_id}`

### Policies Endpoints

- **DELETE** `/policies/{policy_id}`

### Policies Endpoints

- **POST** `/policies/{policy_id}/deploy`

### Portability Endpoints

- **POST** `/portability/request`

### Predictive Endpoints

- **GET** `/predictive/trends`

### Realtime Endpoints

- **GET** `/realtime/metrics`

### Refresh-Token Endpoints

- **POST** `/refresh-token`

### Register Endpoints

- **POST** `/register`

### Requests Endpoints

- **GET** `/requests`

### Requests Endpoints

- **GET** `/requests/{request_id}`

### Rules Endpoints

- **GET** `/rules`

### Rules Endpoints

- **POST** `/rules`

### Rules Endpoints

- **POST** `/rules/seed`

### Rules Endpoints

- **DELETE** `/rules/{rule_id}`

### Security-Findings Endpoints

- **GET** `/security-findings`

### Seed Endpoints

- **POST** `/seed`

### Servers Endpoints

- **GET** `/servers`

### Servers Endpoints

- **POST** `/servers/register`

### Setup-Ab-Testing-Table Endpoints

- **POST** `/setup-ab-testing-table`

### Suggestions Endpoints

- **GET** `/suggestions`

### Support Endpoints

- **POST** `/support/issue`

### Test Endpoints

- **POST** `/test/evaluate`

### Token Endpoints

- **POST** `/token`

### Trends Endpoints

- **GET** `/trends`

### Unified-Actions Endpoints

- **GET** `/unified-actions`

### Unified-Stats Endpoints

- **GET** `/unified-stats`

### Workflows Endpoints

- **POST** `/workflows/{workflow_execution_id}/approve`

### {Rule_Id} Endpoints

- **DELETE** `/{rule_id}`

---

## 2. Service Layer

**Total Services:** 22

### WorkflowApproverService
*File:* `services/workflow_approver_service.py`

Assigns approvers to workflows based on risk and requirements

### MITREMapper
*File:* `services/mitre_mapper.py`

Maps agent actions to MITRE ATT&CK techniques based on observed behavior

### NISTMapper
*File:* `services/nist_mapper.py`

Maps agent actions to NIST SP 800-53 controls based on action characteristics

### SLAMonitor
*File:* `services/sla_monitor.py`

Monitors and enforces SLA deadlines using raw SQL

### CVSSAutoMapper
*File:* `services/cvss_auto_mapper.py`

Automatically maps agent actions to CVSS v3.1 metrics

### ImmutableAuditService
*File:* `services/immutable_audit_service.py`

Enterprise-grade immutable audit logging service

### ApproverSelector
*File:* `services/approver_selector.py`

Selects appropriate approvers based on:

### ConditionOperator
*File:* `services/condition_engine.py`

Supported operators for condition evaluation

### ConditionEngine
*File:* `services/condition_engine.py`

Enterprise condition evaluation engine

### CedarStylePolicy
*File:* `services/cedar_enforcement_service.py`

Cedar-style policy structure

### PolicyCompiler
*File:* `services/cedar_enforcement_service.py`

Compile natural language policies to Cedar-style structured rules

### EnforcementEngine
*File:* `services/cedar_enforcement_service.py`

High-performance policy evaluation engine

### SecurityEvent
*File:* `services/security_bridge_service.py`

Unified security event for both policy and smart rule systems

### SecurityBridge
*File:* `services/security_bridge_service.py`

Enterprise integration layer between policy enforcement and smart rules

### DataSubjectRightsService
*File:* `services/data_rights_service.py`

Enterprise GDPR/CCPA compliance service

### PolicyTemplate
*File:* `services/enterprise_policy_templates.py`

Structured policy template

### CustomPolicyBuilder
*File:* `services/enterprise_policy_templates.py`

Build custom policies with structured validation

### CVSSCalculator
*File:* `services/cvss_calculator.py`

CVSS v3.1 Base Score Calculator

### WorkflowBridgeError
*File:* `services/workflow_bridge.py`

Custom exception for workflow bridge errors

### WorkflowBridge
*File:* `services/workflow_bridge.py`

Enterprise workflow bridge connecting policy decisions to workflow execution.

### MCPGovernanceService
*File:* `services/mcp_governance_service.py`

Enterprise MCP Server Governance Service

### MCPGovernanceService
*File:* `services/mcp_governance_service.py`

Enterprise MCP Server Governance Service

---

## 3. Database Schema

**Total Tables:** 5

- `audit`
- `mcp_policies`
- `roles`
- `sessions`
- `users`
