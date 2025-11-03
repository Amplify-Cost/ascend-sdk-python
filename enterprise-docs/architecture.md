# OW-AI System Architecture (VERIFIED)

**Last Updated:** October 23, 2025  
**Verification Date:** 2025-10-23

*This documentation is automatically generated from your actual codebase.*

## System Overview

OW-AI is deployed as a containerized application with the following verified components:
```
┌─────────────────────────────────────────────────────────┐
│                    OW-AI Platform                        │
├─────────────────────────────────────────────────────────┤
│  Frontend (React)          Backend (FastAPI)             │
│  ├─ React 19.1.0           ├─ Python 3.11                │
│  ├─ Vite 6.4.1             ├─ FastAPI 0.115+             │
│  └─ Dashboard UI           └─ RESTful API                │
│                            ↓                             │
│                    ┌───────────────┐                    │
│                    │  PostgreSQL   │                    │
│                    │   (AWS RDS)   │                    │
│                    └───────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Verified Backend Architecture

### Authentication
**Type:** cookie-based JWT

Your application uses cookies for authentication, not Authorization headers. This means:
- JWT tokens are sent via httpOnly cookies
- Browser automatically includes credentials
- More secure against XSS attacks

### API Route Modules (29 modules)
- `__init___routes.py` -   Init   endpoints
- `admin_routes.py` - Admin endpoints
- `agent_routes.py` - Agent endpoints
- `alert_routes.py` - Alert endpoints
- `alert_summary_routes.py` - Alert Summary endpoints
- `analytics_routes.py` - Analytics endpoints
- `audit_routes.py` - Audit endpoints
- `auth_routes.py` - Auth endpoints
- `auth_routes.py` - Auth endpoints
- `authorization_routes.py` - Authorization endpoints
- `authorization_api_adapter_routes.py` - Authorization Api Adapter endpoints
- `automation_orchestration_routes.py` - Automation Orchestration endpoints
- `data_rights_routes.py` - Data Rights endpoints
- `enrichment_routes.py` - Enrichment endpoints
- `enterprise_secrets_routes.py` - Enterprise Secrets endpoints
- `enterprise_user_management_routes.py` - Enterprise User Management endpoints
- `log_routes.py` - Log endpoints
- `main_routes.py` - Main endpoints
- `mcp_enterprise_secure_routes.py` - Mcp Enterprise Secure endpoints
- `mcp_governance_routes.py` - Mcp Governance endpoints
- `mcp_governance_adapter_routes.py` - Mcp Governance Adapter endpoints
- `rule_routes.py` - Rule endpoints
- `siem_integration_routes.py` - Siem Integration endpoints
- `siem_simple_routes.py` - Siem Simple endpoints
- `smart_alerts_routes.py` - Smart Alerts endpoints
- `smart_rules_routes.py` - Smart Rules endpoints
- `sso_routes.py` - Sso endpoints
- `support_routes.py` - Support endpoints
- `unified_governance_routes.py` - Unified Governance endpoints

### Service Layer (24 services)
- `action_service.py` - Action business logic
- `action_taxonomy_service.py` - Action Taxonomy business logic
- `alert_service.py` - Alert business logic
- `approver_selector_service.py` - Approver Selector business logic
- `assessment_service.py` - Assessment business logic
- `cedar_enforcement_service.py` - Cedar Enforcement business logic
- `condition_engine_service.py` - Condition Engine business logic
- `cvss_auto_mapper_service.py` - Cvss Auto Mapper business logic
- `cvss_calculator_service.py` - Cvss Calculator business logic
- `data_rights_service.py` - Data Rights business logic
- `enterprise_batch_loader_service.py` - Enterprise Batch Loader business logic
- `enterprise_batch_loader_v2_service.py` - Enterprise Batch Loader V2 business logic
- `enterprise_policy_templates_service.py` - Enterprise Policy Templates business logic
- `immutable_audit_service.py` - Immutable Audit business logic
- `mcp_governance_service.py` - Mcp Governance business logic
- `mitre_mapper_service.py` - Mitre Mapper business logic
- `nist_mapper_service.py` - Nist Mapper business logic
- `orchestration_service.py` - Orchestration business logic
- `pending_actions_service.py` - Pending Actions business logic
- `security_bridge_service.py` - Security Bridge business logic
- `sla_monitor_service.py` - Sla Monitor business logic
- `workflow_service.py` - Workflow business logic
- `workflow_approver_service.py` - Workflow Approver business logic
- `workflow_bridge_service.py` - Workflow Bridge business logic

### Database Schema (18 tables)

Your application uses the following database tables:

- **agent_actions**
- **alerts**
- **audit_logs**
- **automation_playbooks**
- **enterprise_policies**
- **integration_endpoints**
- **log_audit_trails**
- **logs**
- **pending_agent_actions**
- **playbook_executions**
- **rule_feedbacks**
- **rules**
- **smart_rules**
- **system_configurations**
- **users**
- **workflow_executions**
- **workflow_steps**
- **workflows**

### Technology Stack (Verified from package.json and requirements.txt)

**Backend:**
- FastAPI 0.115+
- SQLAlchemy 2.0+
- Pydantic 2.5+
- Alembic (migrations)
- JWT authentication
- PostgreSQL driver

**Frontend:**
- React 19.1.0
- Vite 6.4.1
- Axios (HTTP client)
- Chart.js (analytics)

**Deployment:**
- Docker containers
- AWS ECS (Fargate)
- AWS RDS (PostgreSQL)
- AWS Secrets Manager
- GitHub Actions CI/CD

## Production URL

Your application is deployed at: **https://pilot.owkai.app**

## Authentication Flow (ACTUAL)

Since you use cookie-based authentication, here's the real flow:
```
1. User submits login credentials
   POST /auth/login

2. Backend validates credentials
   - Checks database
   - Verifies password hash

3. Backend creates JWT token
   - Signs with RSA-256
   - Includes user info (email, role)

4. Backend sets httpOnly cookie
   Set-Cookie: access_token=eyJ...; HttpOnly; Secure

5. Browser stores cookie automatically
   - Browser manages the cookie
   - No JavaScript access (XSS protection)

6. All subsequent requests include cookie
   GET /api/smart-rules
   Cookie: access_token=eyJ...

7. Backend reads from cookie
   - Extracts token from request.cookies
   - Validates JWT signature
   - Attaches user to request

NO Authorization headers needed!
```

## Data Flow

### Action Evaluation Flow (Verified)
```
1. Frontend: User/Agent initiates action
   ↓
2. POST /agent-control/actions (or /api/authorization/actions)
   ↓
3. OrchestrationService.evaluate_and_act()
   ├─ AssessmentService.assess_action() → Risk score
   ├─ Check smart_rules table → Match rules
   ├─ AlertService.create_alert() → If high risk
   └─ WorkflowService.create_execution() → If approval needed
   ↓
4. Decision: block / require_approval / notify / allow
   ↓
5. Update action status in database
   ↓
6. Return response to frontend
```

## File Structure (Verified)
```
ow-ai-backend/
├── main.py                 # FastAPI app entry point
├── models.py               # SQLAlchemy models
├── security.py             # JWT & password handling
├── dependencies.py         # Auth dependencies
├── routes/                 # API endpoints
│   ├── __init___routes.py
│   ├── admin_routes.py
│   ├── agent_routes.py
│   ├── alert_routes.py
│   ├── alert_summary_routes.py
│   ├── analytics_routes.py
│   ├── audit_routes.py
│   ├── auth_routes.py
│   ├── auth_routes.py
│   ├── authorization_routes.py
│   ├── authorization_api_adapter_routes.py
│   ├── automation_orchestration_routes.py
│   ├── data_rights_routes.py
│   ├── enrichment_routes.py
│   ├── enterprise_secrets_routes.py
│   ├── enterprise_user_management_routes.py
│   ├── log_routes.py
│   ├── main_routes.py
│   ├── mcp_enterprise_secure_routes.py
│   ├── mcp_governance_routes.py
│   ├── mcp_governance_adapter_routes.py
│   ├── rule_routes.py
│   ├── siem_integration_routes.py
│   ├── siem_simple_routes.py
│   ├── smart_alerts_routes.py
│   ├── smart_rules_routes.py
│   ├── sso_routes.py
│   ├── support_routes.py
│   ├── unified_governance_routes.py
├── services/               # Business logic
│   ├── action_service.py
│   ├── action_taxonomy_service.py
│   ├── alert_service.py
│   ├── approver_selector_service.py
│   ├── assessment_service.py
│   ├── cedar_enforcement_service.py
│   ├── condition_engine_service.py
│   ├── cvss_auto_mapper_service.py
│   ├── cvss_calculator_service.py
│   ├── data_rights_service.py
│   ├── enterprise_batch_loader_service.py
│   ├── enterprise_batch_loader_v2_service.py
│   ├── enterprise_policy_templates_service.py
│   ├── immutable_audit_service.py
│   ├── mcp_governance_service.py
│   ├── mitre_mapper_service.py
│   ├── nist_mapper_service.py
│   ├── orchestration_service.py
│   ├── pending_actions_service.py
│   ├── security_bridge_service.py
│   ├── sla_monitor_service.py
│   ├── workflow_service.py
│   ├── workflow_approver_service.py
│   ├── workflow_bridge_service.py
├── schemas/                # Pydantic models
├── alembic/                # Database migrations
├── Dockerfile              # Container definition
└── startup.sh              # Entry point script

owkai-pilot-frontend/
├── src/
│   ├── components/         # React components
│   ├── utils/              # Utilities (fetchWithAuth)
│   └── main.jsx            # App entry point
├── Dockerfile
└── package.json
```

## Deployment Architecture (AWS)
```
AWS Cloud
├── ECS Cluster
│   ├── Frontend Service
│   │   ├── Task Definition (Fargate)
│   │   ├── Container: owkai-pilot-frontend
│   │   └── Port: 3000 → 80
│   └── Backend Service
│       ├── Task Definition (Fargate)
│       ├── Container: owkai-pilot-backend
│       └── Port: 8000
├── Application Load Balancer
│   ├── Target: Frontend (pilot.owkai.app)
│   └── Target: Backend (pilot.owkai.app/api/*)
├── RDS PostgreSQL
│   ├── Instance: db.t3.micro (or larger)
│   └── Multi-AZ: Enabled
└── Secrets Manager
    ├── DATABASE_URL
    ├── JWT_SECRET
    └── Other secrets
```

---

**Note:** This documentation is generated from your actual code at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
