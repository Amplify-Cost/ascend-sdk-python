---
title: Ascend Platform Architecture
sidebar_position: 1
---

# Ascend Platform Architecture

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-HELP-004 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

**Document ID:** ASCEND-INT-005
**Version:** 2.0.0
**Classification:** Technical Reference
**Publisher:** OW-kai Corporation

---

## Overview

Ascend is an enterprise AI agent governance platform that provides real-time risk assessment, policy enforcement, and compliance management for AI agent actions. This document describes the platform architecture and integration patterns.

---

## High-Level Architecture

```
                                    ┌─────────────────────────────────────────────────────────────────┐
                                    │                     YOUR AI AGENTS                               │
                                    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
                                    │  │LangChain│  │ OpenAI  │  │ Claude  │  │ Custom  │            │
                                    │  │  Agent  │  │Functions│  │  Agent  │  │  Agent  │            │
                                    │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
                                    └───────┼────────────┼────────────┼────────────┼─────────────────┘
                                            │            │            │            │
                                            ▼            ▼            ▼            ▼
                                    ┌─────────────────────────────────────────────────────────────────┐
                                    │                    ASCEND SDK / API                              │
                                    │           ┌─────────────────────────────────┐                   │
                                    │           │  POST /api/authorization/agent-action              │
                                    │           │  POST /api/sdk/agent-action                        │
                                    │           └─────────────────────────────────┘                   │
                                    └───────────────────────────┬─────────────────────────────────────┘
                                                                │
                                                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         ASCEND PLATFORM                                                            │
│                                                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    RISK ASSESSMENT PIPELINE                                                  │  │
│  │                                                                                                              │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐              │  │
│  │  │  Enrichment  │──▶│    CVSS     │──▶│    MITRE    │──▶│    NIST     │──▶│   Policy    │              │  │
│  │  │   Engine     │   │  Calculator  │   │   Mapper    │   │   Mapper    │   │   Engine    │              │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘              │  │
│  │         │                  │                  │                  │                  │                      │  │
│  │         ▼                  ▼                  ▼                  ▼                  ▼                      │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐              │  │
│  │  │    Base      │   │    CVSS     │   │   ATT&CK    │   │   800-53    │   │   Policy    │              │  │
│  │  │  Risk Level  │   │    Score    │   │   Tactics   │   │  Controls   │   │    Risk     │              │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘              │  │
│  │                                                                                                              │  │
│  │                              ┌──────────────────────────────────────────┐                                   │  │
│  │                              │         HYBRID RISK CALCULATOR           │                                   │  │
│  │                              │  (Environment + Data + CVSS + Context)   │                                   │  │
│  │                              └──────────────────┬───────────────────────┘                                   │  │
│  │                                                 │                                                            │  │
│  │                              ┌──────────────────▼───────────────────────┐                                   │  │
│  │                              │            RISK FUSION                    │                                   │  │
│  │                              │   Final = (Policy×80%) + (Hybrid×20%)    │                                   │  │
│  │                              └──────────────────┬───────────────────────┘                                   │  │
│  │                                                 │                                                            │  │
│  │                              ┌──────────────────▼───────────────────────┐                                   │  │
│  │                              │            SAFETY RULES                   │                                   │  │
│  │                              │  • CRITICAL CVSS Floor (85)              │                                   │  │
│  │                              │  • Policy DENY Override (100)            │                                   │  │
│  │                              │  • PII Production Floor (70)             │                                   │  │
│  │                              └──────────────────────────────────────────┘                                   │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    AUTOMATION & ORCHESTRATION                                                │  │
│  │                                                                                                              │  │
│  │  ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐                  │  │
│  │  │   Playbook Engine    │        │  Workflow Orchestrator│        │   Alert Manager      │                  │  │
│  │  │  • Auto-approvals    │        │  • Approval workflows │        │  • Alert generation  │                  │  │
│  │  │  • Pattern matching  │        │  • Escalation chains  │        │  • Severity mapping  │                  │  │
│  │  │  • Time-based rules  │        │  • Notifications      │        │  • Audit logging     │                  │  │
│  │  └──────────────────────┘        └──────────────────────┘        └──────────────────────┘                  │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    DATA LAYER                                                                │  │
│  │                                                                                                              │  │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐              │  │
│  │  │  Agent Actions   │    │    Policies      │    │     Alerts       │    │   Audit Logs     │              │  │
│  │  │  (PostgreSQL)    │    │  (PostgreSQL)    │    │  (PostgreSQL)    │    │  (PostgreSQL)    │              │  │
│  │  └──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘              │  │
│  │                                                                                                              │  │
│  │                          ┌───────────────────────────────────────────┐                                      │  │
│  │                          │   MULTI-TENANT ISOLATION (organization_id)│                                      │  │
│  │                          │   Banking-level data separation            │                                      │  │
│  │                          └───────────────────────────────────────────┘                                      │  │
│  └────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                │
                                                                ▼
                                    ┌─────────────────────────────────────────────────────────────────┐
                                    │                    RESPONSE TO AGENT                             │
                                    │  {                                                               │
                                    │    "approved": true/false,                                      │
                                    │    "risk_score": 0-100,                                         │
                                    │    "compliance": {...},                                         │
                                    │    "risk_assessment": {...}                                     │
                                    │  }                                                               │
                                    └─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Enrichment Engine

The first-pass analysis of incoming actions:

- **Action Type Classification**: Maps action types to risk categories
- **Tool Analysis**: Evaluates tool-specific risks
- **Context Extraction**: Parses descriptions for keywords (PII, production, etc.)
- **Initial Risk Level**: Assigns base risk level (low/medium/high/critical)

### 2. CVSS Calculator

CVSS 3.1 scoring based on action characteristics:

- **Attack Vector**: Network-based AI agent actions = Network (AV:N)
- **Attack Complexity**: Automated vs manual = Low/High (AC:L/H)
- **Privileges Required**: Based on action type = None/Low/High (PR:N/L/H)
- **Impact Assessment**: CIA triad evaluation

### 3. MITRE ATT&CK Mapper

Maps actions to the MITRE ATT&CK framework:

- **Tactic Identification**: 14 top-level tactics (Initial Access, Execution, etc.)
- **Technique Mapping**: 500+ specific techniques
- **Sub-technique Resolution**: Granular attack pattern classification
- **Threat Intelligence**: Integration with threat feeds

### 4. NIST 800-53 Mapper

Maps actions to NIST security controls:

- **Control Families**: AC, AU, IA, SC, SI, CM, etc.
- **Specific Controls**: e.g., AC-2 (Account Management), AU-12 (Audit Generation)
- **Compliance Recommendations**: Actionable guidance

### 5. Policy Engine

Real-time policy evaluation (<200ms SLA):

- **Natural Language Policies**: Human-readable policy definitions
- **Organization-Specific Rules**: Custom policies per tenant
- **Policy Types**: Allow, Deny, Require Approval, Conditional
- **Decision Output**: ALLOW, DENY, REQUIRE_APPROVAL

### 6. Hybrid Risk Calculator

Multi-factor risk scoring:

```
Hybrid = (Environment × 35%) + (Data Sensitivity × 30%) +
         (CVSS × 25%) + (Operational Context × 10%) × Resource Multiplier
```

### 7. Risk Fusion

Combines policy and hybrid scores:

```
Final Score = (Policy Risk × 80%) + (Hybrid Risk × 20%)
```

### 8. Safety Rules

Hard rules that override calculated scores:

1. **CRITICAL CVSS Floor**: Score ≥ 85 if CVSS severity is CRITICAL
2. **Policy DENY Override**: Score = 100 if policy decision is DENY
3. **PII Production Floor**: Score ≥ 70 if PII detected in production

---

## Integration Patterns

### Pattern 1: Synchronous Evaluation

Best for: Low-risk actions, fast decisions needed

```
Agent → Ascend API → Risk Pipeline → Response → Agent proceeds/stops
```

### Pattern 2: Asynchronous with Polling

Best for: High-risk actions requiring approval

```
Agent → Ascend API → Pending → Agent polls → Approval received → Agent proceeds
```

### Pattern 3: Webhook-Based

Best for: Event-driven architectures

```
Agent → Ascend API → Pending → Approval event → Webhook to agent → Agent proceeds
```

---

## Data Flow

### Action Submission

1. Agent submits action via SDK/API
2. Request authenticated (API Key or JWT)
3. Organization identified for multi-tenant isolation
4. Action queued for processing

### Risk Assessment

1. Enrichment engine analyzes action
2. CVSS score calculated
3. MITRE/NIST mappings applied
4. Policy engine evaluates organization policies
5. Hybrid calculator runs
6. Risk fusion combines scores
7. Safety rules applied

### Decision Output

1. Final risk score determined
2. Approval requirement set
3. Alert generated (if high/critical)
4. Playbook matching checked
5. Workflow triggered (if needed)
6. Response returned to agent

---

## Security Architecture

### Authentication

- **API Keys**: SHA-256 hashed, salted, never stored plaintext
- **JWT Tokens**: RS256 signed, short expiration
- **Multi-Factor**: MFA enforced for admin access

### Multi-Tenant Isolation

- **Data Isolation**: All queries filtered by `organization_id`
- **Index Optimization**: Indexes on `organization_id` for performance
- **Cross-Tenant Prevention**: No cross-organization data access

### Encryption

- **In Transit**: TLS 1.3 required
- **At Rest**: AES-256 encryption
- **Key Management**: AWS KMS integration

### Audit Trail

- **All Actions Logged**: Every API call recorded
- **Immutable Logs**: Append-only audit trail
- **Retention**: Configurable per compliance requirements

---

## Performance Characteristics

| Metric | Target | Typical |
|--------|--------|---------|
| Policy Evaluation | <200ms | 50-100ms |
| Full Risk Pipeline | <500ms | 200-300ms |
| API Response Time | <1000ms | 300-500ms |
| Availability | 99.9% | 99.95% |

---

## Deployment Architecture

### Production Deployment

```
                    ┌─────────────────┐
                    │   CloudFront    │
                    │   (CDN/WAF)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Application     │
                    │ Load Balancer   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│  ECS Task 1   │   │  ECS Task 2   │   │  ECS Task N   │
│  (FastAPI)    │   │  (FastAPI)    │   │  (FastAPI)    │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   RDS PostgreSQL │
                    │   (Multi-AZ)    │
                    └─────────────────┘
```

### Components

- **CloudFront**: CDN and WAF protection
- **ALB**: Application load balancing with health checks
- **ECS Fargate**: Containerized application deployment
- **RDS PostgreSQL**: Managed database with Multi-AZ failover
- **Cognito**: Identity management and authentication

---

## Compliance Alignment

| Framework | Coverage |
|-----------|----------|
| SOC 2 Type II | CC1-CC9 |
| PCI-DSS | 6.1, 7.1, 8.3.1, 10.x, 12.10 |
| HIPAA | 164.312(a), (b), (d) |
| GDPR | Articles 25, 32, 33 |
| NIST 800-53 | AC, AU, IA, SC, SI families |

---

*Document Version: 2.0.0 | Last Updated: December 2025 | Publisher: OW-kai Corporation*
