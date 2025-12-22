# ASCEND System Architecture Map

**Document Version:** 1.0.0
**Last Updated:** December 22, 2024
**Classification:** Enterprise Confidential

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASCEND AI GOVERNANCE PLATFORM                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │   Web Dashboard  │    │     REST API     │    │    SDK Clients   │       │
│  │  (React + Vite)  │    │    (FastAPI)     │    │ (Python/Node.js) │       │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘       │
│           │                       │                       │                  │
│           └───────────────────────┼───────────────────────┘                  │
│                                   │                                          │
│  ┌────────────────────────────────▼─────────────────────────────────────┐   │
│  │                      API GATEWAY LAYER                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │Kong Plugin  │  │Envoy ext_   │  │ Lambda Auth │  │  MCP Server │  │   │
│  │  │ (Lua)       │  │authz (Go)   │  │  (Python)   │  │(TypeScript) │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │                                          │
│  ┌────────────────────────────────▼─────────────────────────────────────┐   │
│  │                      CORE SERVICES LAYER                              │   │
│  │                                                                        │   │
│  │  ┌───────────────────────────────────────────────────────────────┐   │   │
│  │  │                  7-STEP GOVERNANCE PIPELINE                    │   │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │   │
│  │  │  │Enrich- │→│ CVSS   │→│Policy  │→│Smart   │→│Alert   │       │   │   │
│  │  │  │ment    │ │Scoring │ │Engine  │ │Rules   │ │Gen     │       │   │   │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │   │   │
│  │  │                                              ↓                 │   │   │
│  │  │  ┌────────┐ ┌────────┐                    ┌────────┐           │   │   │
│  │  │  │Workflow│→│Audit   │←───────────────────│Immut.  │           │   │   │
│  │  │  │Router  │ │Logger  │                    │Log     │           │   │   │
│  │  │  └────────┘ └────────┘                    └────────┘           │   │   │
│  │  └───────────────────────────────────────────────────────────────┘   │   │
│  │                                                                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │Auth      │ │Rate      │ │Prompt    │ │Code      │ │BYOK      │    │   │
│  │  │Service   │ │Limiter   │ │Security  │ │Analysis  │ │Encryption│    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  │                                                                        │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │   │
│  │  │Billing   │ │Metering  │ │Notif-    │ │Webhook   │ │Agent     │    │   │
│  │  │Service   │ │Service   │ │ication   │ │Service   │ │Registry  │    │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │   │
│  └────────────────────────────────┬─────────────────────────────────────┘   │
│                                   │                                          │
│  ┌────────────────────────────────▼─────────────────────────────────────┐   │
│  │                        DATA LAYER                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │  PostgreSQL  │  │    Redis     │  │  AWS KMS     │                │   │
│  │  │  (Primary)   │  │   (Cache)    │  │  (BYOK)      │                │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      EXTERNAL INTEGRATIONS                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │   │
│  │  │AWS      │ │Stripe   │ │Slack/   │ │SIEM     │ │Service- │         │   │
│  │  │Cognito  │ │Billing  │ │Teams    │ │Systems  │ │Now      │         │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Details

### 2.1 Frontend Layer

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| Web Dashboard | React 19.1.0 + Vite | 3000 | User interface |
| Auth Context | React Context | - | Authentication state |
| Theme Context | React Context | - | Dark/light mode |

**Key Components:**
- `CognitoLogin.jsx` - Multi-pool authentication
- `Dashboard.jsx` - Executive overview
- `AgentAuthorizationDashboard.jsx` - Approval queue
- `VisualPolicyBuilder.jsx` - Policy creation
- `BillingDashboard.jsx` - Subscription management

### 2.2 API Layer

| Component | Technology | Port | Purpose |
|-----------|------------|------|---------|
| FastAPI Server | Python 3.11 | 8000 | REST API |
| Uvicorn | ASGI Server | 8000 | Production server |
| Alembic | Migrations | - | Database versioning |

**Route Categories:**
- `/auth/*` - Authentication (6 routes)
- `/api/v1/actions/*` - Action governance (8 routes)
- `/api/analytics/*` - Analytics (5 routes)
- `/api/billing/*` - Billing (3 routes)
- `/api/admin/*` - Administration (8 routes)

### 2.3 Gateway Layer

| Gateway | Protocol | Language | Integration Point |
|---------|----------|----------|-------------------|
| Kong Plugin | HTTP | Lua | API Gateway |
| Envoy ext_authz | gRPC | Go | Service Mesh |
| Lambda Authorizer | HTTP | Python | AWS API Gateway |
| MCP Server | stdio/HTTP | TypeScript | Claude/LLM |

### 2.4 Service Layer

**Core Services (77 total):**

| Category | Services | Key Examples |
|----------|----------|--------------|
| Authentication | 8 | `token_service`, `multi_pool_jwt_validator` |
| Security | 12 | `prompt_security_service`, `agent_rate_limiter` |
| Governance | 10 | `policy_engine`, `unified_policy_evaluation_service` |
| Risk | 5 | `cvss_auto_mapper`, `enterprise_risk_calculator_v2` |
| Notifications | 4 | `notification_service`, `webhook_signer` |
| Billing | 3 | `metering_service`, `spend_control_service` |

### 2.5 Data Layer

| Database | Purpose | Technology |
|----------|---------|------------|
| PostgreSQL | Primary data store | RDS (Multi-AZ) |
| Redis | Cache & rate limiting | ElastiCache |
| AWS KMS | Key management | BYOK support |

**Key Tables (80+):**
- `organizations` - Multi-tenant anchor
- `users` - Per-org email uniqueness
- `agent_actions` - Core governance entity
- `immutable_audit_logs` - WORM compliance
- `usage_events` - Billing metering

---

## 3. Security Architecture

### 3.1 12-Layer Defense Model

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 12: Security Headers (X-Frame-Options, CSP, HSTS)        │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 11: Secrets Management (AWS Secrets Manager)             │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 10: Input Validation (Pydantic + Sanitization)           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 9: Audit Logging (Hash-Chained WORM)                     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 8: BYOK Encryption (AES-256-GCM + Customer CMK)          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 7: RBAC (6-Level Hierarchy + Separation of Duties)       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 6: API Key Validation (SHA-256 + Constant-Time)          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5: JWT Authentication (RS256 + Claim Validation)         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: Action Governance (CVSS + Policy Engine)              │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: Code Analysis (Pattern Detection + CWE Mapping)       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Prompt Security (Injection Detection + LLM Chain)     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: Rate Limiting (Redis Sliding Window + Per-Agent)      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Authentication Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Client  │────▶│  Cognito │────▶│  Backend │────▶│ Database │
│          │     │  Pool    │     │  JWT Val │     │  Lookup  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  1. Login      │                │                │
     │  ──────────▶   │                │                │
     │                │                │                │
     │  2. MFA        │                │                │
     │  ◀──────────   │                │                │
     │                │                │                │
     │  3. Tokens     │                │                │
     │  ◀──────────   │                │                │
     │                │                │                │
     │  4. API Call   │                │                │
     │  ───────────────────────────▶   │                │
     │                │                │                │
     │                │  5. Validate   │                │
     │                │  ──────────▶   │                │
     │                │                │                │
     │                │  6. User Data  │                │
     │                │  ◀──────────   │                │
     │                │                │                │
     │  7. Response   │                │                │
     │  ◀───────────────────────────   │                │
```

### 3.3 Action Governance Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Agent   │────▶│ Gateway  │────▶│ Backend  │────▶│ Response │
│  (SDK)   │     │ (Kong/   │     │ Pipeline │     │          │
│          │     │  Envoy)  │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │
     │  1. Submit     │                │                │
     │  ──────────▶   │                │                │
     │                │                │                │
     │                │  2. Pre-Check  │                │
     │                │  ──────────▶   │                │
     │                │                │                │
     │                │  3. 7-Step Pipeline             │
     │                │  ┌────────────────────────┐     │
     │                │  │ Enrich → CVSS → Policy │     │
     │                │  │ → Rules → Alert →      │     │
     │                │  │ Workflow → Audit       │     │
     │                │  └────────────────────────┘     │
     │                │                │                │
     │                │  4. Decision   │                │
     │                │  ◀──────────   │                │
     │                │                │                │
     │  5. Result     │                │                │
     │  ◀──────────   │                │                │
```

---

## 4. Data Flow Diagrams

### 4.1 Multi-Tenant Data Isolation

```
┌─────────────────────────────────────────────────────────────┐
│                     REQUEST PROCESSING                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐       │
│  │  Request   │────▶│  JWT       │────▶│  Extract   │       │
│  │  Arrives   │     │  Decode    │     │  org_id    │       │
│  └────────────┘     └────────────┘     └────────────┘       │
│                                              │               │
│                                              ▼               │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐       │
│  │  Response  │◀────│  Execute   │◀────│  Set RLS   │       │
│  │  (Filtered)│     │  Query     │     │  Context   │       │
│  └────────────┘     └────────────┘     └────────────┘       │
│                                                              │
│  SQL: SELECT * FROM agent_actions                            │
│        WHERE organization_id = :org_id  ← Auto-injected     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Billing Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     BILLING PIPELINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐       │
│  │  API Call  │────▶│  Metering  │────▶│  Redis     │       │
│  │  (Action)  │     │  Service   │     │  Counter   │       │
│  └────────────┘     └────────────┘     └────────────┘       │
│                                              │               │
│                                              ▼               │
│  ┌────────────┐     ┌────────────┐     ┌────────────┐       │
│  │  Stripe    │◀────│  Aggregate │◀────│  Batch     │       │
│  │  Invoice   │     │  to DB     │     │  Flush     │       │
│  └────────────┘     └────────────┘     └────────────┘       │
│                                                              │
│  Event Types:                                                │
│  - ACTION_EVALUATION                                         │
│  - MCP_SERVER_HOUR                                           │
│  - USER_SEAT                                                 │
│  - API_CALL                                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Deployment Architecture

### 5.1 AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS REGION (us-east-2)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │                    VPC (10.100.0.0/16)             │     │
│  │  ┌──────────────────┐  ┌──────────────────┐        │     │
│  │  │  Public Subnet 1 │  │  Public Subnet 2 │        │     │
│  │  │  (10.100.1.0/24) │  │  (10.100.2.0/24) │        │     │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │        │     │
│  │  │  │    ALB     │  │  │  │    ALB     │  │        │     │
│  │  │  └────────────┘  │  │  └────────────┘  │        │     │
│  │  └──────────────────┘  └──────────────────┘        │     │
│  │                                                     │     │
│  │  ┌──────────────────┐  ┌──────────────────┐        │     │
│  │  │  Private Sub 1   │  │  Private Sub 2   │        │     │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │        │     │
│  │  │  │ECS Fargate │  │  │  │ECS Fargate │  │        │     │
│  │  │  │ (Backend)  │  │  │  │ (Frontend) │  │        │     │
│  │  │  └────────────┘  │  │  └────────────┘  │        │     │
│  │  │  ┌────────────┐  │  │  ┌────────────┐  │        │     │
│  │  │  │    RDS     │  │  │  │ElastiCache │  │        │     │
│  │  │  │(PostgreSQL)│  │  │  │  (Redis)   │  │        │     │
│  │  │  └────────────┘  │  │  └────────────┘  │        │     │
│  │  └──────────────────┘  └──────────────────┘        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Cognito   │  │    KMS     │  │  Secrets   │             │
│  │  (Auth)    │  │   (BYOK)   │  │  Manager   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │    ECR     │  │    SNS     │  │    SQS     │             │
│  │ (Registry) │  │  (Events)  │  │  (Queues)  │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  KUBERNETES CLUSTER                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              ascend-system namespace               │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │     │
│  │  │ Backend  │  │ Backend  │  │ Backend  │         │     │
│  │  │ Pod #1   │  │ Pod #2   │  │ Pod #3   │         │     │
│  │  └──────────┘  └──────────┘  └──────────┘         │     │
│  │       ↑            ↑            ↑                  │     │
│  │       └────────────┼────────────┘                  │     │
│  │              ┌─────┴─────┐                         │     │
│  │              │  Service  │                         │     │
│  │              │(ClusterIP)│                         │     │
│  │              └───────────┘                         │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              ascend-authz namespace                │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │     │
│  │  │  Authz   │  │  Authz   │  │  Authz   │         │     │
│  │  │ Pod #1   │  │ Pod #2   │  │ Pod #3   │         │     │
│  │  │(ext_authz│  │(ext_authz│  │(ext_authz│         │     │
│  │  └──────────┘  └──────────┘  └──────────┘         │     │
│  │       ↑            ↑            ↑                  │     │
│  │       └────────────┼────────────┘                  │     │
│  │              ┌─────┴─────┐                         │     │
│  │              │  Service  │                         │     │
│  │              │  (gRPC)   │                         │     │
│  │              └───────────┘                         │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Resources:                                                  │
│  - Deployment (3 replicas, HPA 3-10)                        │
│  - Service (ClusterIP + gRPC)                               │
│  - HPA (70% CPU, 80% Memory)                                │
│  - PDB (minAvailable: 2)                                    │
│  - Secret (API keys, certificates)                          │
│  - ConfigMap (configuration)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Integration Points

### 6.1 External Service Integrations

| Service | Protocol | Purpose | Status |
|---------|----------|---------|--------|
| AWS Cognito | HTTPS | Authentication | Production |
| AWS KMS | HTTPS | Key management | Production |
| AWS Secrets Manager | HTTPS | Secrets storage | Production |
| AWS SNS | HTTPS | Event publishing | Production |
| AWS SQS | HTTPS | Message queuing | Production |
| Stripe | HTTPS | Billing | Production |
| Slack | HTTPS | Notifications | Production |
| Microsoft Teams | HTTPS | Notifications | Production |
| ServiceNow | HTTPS | ITSM integration | Available |
| Splunk | HTTPS | SIEM | Available |

### 6.2 SDK Integration Points

| SDK | Endpoint | Authentication |
|-----|----------|----------------|
| Python SDK | `/api/v1/actions` | API Key + Bearer |
| boto3 Wrapper | `/api/v1/actions` | API Key + Bearer |
| LangChain | `/api/v1/actions` | API Key + Bearer |
| MCP Server | `/api/v1/mcp/*` | API Key |

---

## 7. Monitoring & Observability

### 7.1 Metrics Collection

| Source | Metrics | Storage |
|--------|---------|---------|
| Backend | Request latency, error rates | CloudWatch |
| Database | Connections, query times | CloudWatch RDS |
| Cache | Hit rate, memory usage | CloudWatch ElastiCache |
| Gateway | Decision latency, cache hits | Custom metrics |

### 7.2 Logging Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Backend    │────▶│  CloudWatch  │────▶│    SIEM      │
│   Logs       │     │    Logs      │     │  (Optional)  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Immutable  │
                     │  Audit Logs  │
                     │   (DB WORM)  │
                     └──────────────┘
```

---

*Document ID: ASCEND-ARCH-2024-001*
