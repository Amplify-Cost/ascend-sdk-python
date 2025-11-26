# OW-AI Enterprise Action Blocking Architecture

**Document Version:** 1.0
**Classification:** INTERNAL - ENGINEERING
**Last Updated:** 2025-01-15
**Author:** OW-AI Enterprise Engineering

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Blocking Architecture Overview](#blocking-architecture-overview)
3. [Enforcement Levels](#enforcement-levels)
4. [Decision Flow](#decision-flow)
5. [Integration Points](#integration-points)
6. [Security Guarantees](#security-guarantees)

---

## Executive Summary

The OW-AI Enterprise Platform provides **real-time action blocking** for AI agents and MCP servers. This document describes the architectural mechanisms that ensure unauthorized actions are **prevented from execution**, not just logged.

### Key Principles

| Principle | Description |
|-----------|-------------|
| **Fail-Closed** | If governance check fails, action is blocked (not allowed) |
| **Synchronous Enforcement** | Blocking occurs in the execution path, not asynchronously |
| **Non-Bypassable** | Integration at execution layer prevents circumvention |
| **Audit Complete** | All decisions (allow/block) are immutably logged |

---

## Blocking Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT / MCP CLIENT                                │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    TOOL EXECUTION REQUEST                           │   │
│   │   Example: "DELETE FROM users WHERE last_login < '2024-01-01'"     │   │
│   └──────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OW-AI ENFORCEMENT LAYER                                │
│                    (Integrated at Execution Point)                          │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: INTERCEPT                                                  │   │
│   │  • Capture action details before execution                          │   │
│   │  • Extract: action_type, target, parameters, context                │   │
│   └──────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
│   ┌──────────────────────────────▼──────────────────────────────────────┐   │
│   │  STEP 2: EVALUATE (Synchronous API Call)                            │   │
│   │  • POST /api/authorization/agent-action                             │   │
│   │  • Response includes: risk_score, requires_approval, policy_result  │   │
│   └──────────────────────────────┬──────────────────────────────────────┘   │
│                                  │                                          │
│   ┌──────────────────────────────▼──────────────────────────────────────┐   │
│   │  STEP 3: ENFORCE DECISION                                           │   │
│   │                                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │   │
│   │  │   ALLOW     │  │    DENY     │  │    REQUIRE_APPROVAL         │  │   │
│   │  │             │  │             │  │                             │  │   │
│   │  │ Proceed to  │  │ BLOCK       │  │ BLOCK until approved        │  │   │
│   │  │ execution   │  │ immediately │  │ Poll for decision           │  │   │
│   │  │             │  │             │  │ Timeout = BLOCK             │  │   │
│   │  │ Return      │  │ Return      │  │                             │  │   │
│   │  │ result      │  │ error       │  │ Approved = proceed          │  │   │
│   │  │             │  │             │  │ Rejected = BLOCK + error    │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ACTUAL EXECUTION                                    │
│                    (Only reached if ALLOWED)                                │
│                                                                             │
│   • Database query executes                                                 │
│   • File operation completes                                                │
│   • API call is made                                                        │
│   • AWS resource is modified                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Enforcement Levels

OW-AI provides three enforcement levels based on integration depth:

### Level 1: Advisory (Logging Only)
```
┌─────────────────────────────────────────────────────────────────┐
│ ADVISORY MODE                                                   │
│                                                                 │
│ • Actions are logged and risk-assessed                          │
│ • NO blocking occurs                                            │
│ • Used for: Initial rollout, shadow mode, compliance auditing   │
│                                                                 │
│ Security: LOW (monitoring only)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Level 2: Cooperative (Agent-Enforced)
```
┌─────────────────────────────────────────────────────────────────┐
│ COOPERATIVE MODE                                                │
│                                                                 │
│ • Agent checks governance before execution                      │
│ • Agent is responsible for respecting decisions                 │
│ • Bypass possible if agent ignores response                     │
│ • Used for: Trusted internal agents, development                │
│                                                                 │
│ Security: MEDIUM (trust-based)                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Level 3: Mandatory (System-Enforced) ⭐ RECOMMENDED
```
┌─────────────────────────────────────────────────────────────────┐
│ MANDATORY MODE                                                  │
│                                                                 │
│ • Governance integrated INTO execution path                     │
│ • Action CANNOT proceed without approval                        │
│ • No bypass possible - enforcement is architectural             │
│ • Used for: Production, regulated environments, banking         │
│                                                                 │
│ Security: HIGH (non-bypassable)                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decision Flow

### Decision Types

| Decision | Code | Behavior | Agent Receives |
|----------|------|----------|----------------|
| **ALLOW** | `ALLOW` | Execute immediately | Success response |
| **DENY** | `DENY` | Block permanently | `GovernanceBlockedError` |
| **REQUIRE_APPROVAL** | `REQUIRE_APPROVAL` | Block until human decision | Waits, then success or `ActionRejectedError` |

### Decision Criteria

```
┌─────────────────────────────────────────────────────────────────┐
│                    RISK-BASED ROUTING                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Risk Score 0-29    →  AUTO-APPROVE (ALLOW)                     │
│  Risk Score 30-69   →  EVALUATE POLICY                          │
│  Risk Score 70-84   →  REQUIRE_APPROVAL (Level 1-2)             │
│  Risk Score 85-94   →  REQUIRE_APPROVAL (Level 3)               │
│  Risk Score 95-100  →  REQUIRE_APPROVAL (Executive) or DENY     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    POLICY-BASED ROUTING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Policy: "no-production-deletes"                                │
│  → Action: DELETE on production → DENY (immediate)              │
│                                                                 │
│  Policy: "require-approval-pii"                                 │
│  → Action: Access PII data → REQUIRE_APPROVAL                   │
│                                                                 │
│  Policy: "allow-read-staging"                                   │
│  → Action: SELECT on staging → ALLOW                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### 1. SDK Enforcement (Python)

```python
# Enforcement wrapper - action CANNOT bypass
from owkai.enforcement import EnforcedClient

client = EnforcedClient(
    api_key="...",
    enforcement_mode="mandatory",  # Cannot be disabled
    fail_closed=True               # Block on any error
)

# This is an ATOMIC operation:
# 1. Submit to OW-AI
# 2. Wait for decision
# 3. Execute only if approved
# 4. Return result or raise exception
result = client.execute_governed_action(
    action=lambda: db.execute("DELETE FROM users WHERE ..."),
    action_type="database_delete",
    description="...",
)
```

### 2. boto3 Enforcement (AWS)

```python
# Patches boto3 at import - all AWS calls governed
from owkai.enforcement import enable_mandatory_governance

enable_mandatory_governance(
    api_key="...",
    enforcement_mode="mandatory",
    fail_closed=True
)

# This S3 call CANNOT proceed without approval
s3 = boto3.client('s3')
s3.delete_bucket(Bucket='production')  # BLOCKS until approved
```

### 3. MCP Server Enforcement

```python
# MCP server with mandatory enforcement
from owkai.mcp import EnforcedMCPServer

server = EnforcedMCPServer(
    api_key="...",
    enforcement_mode="mandatory"
)

# Tool execution is BLOCKED until governance approves
@server.tool("query_database")
async def query_database(query: str):
    # This function only executes if governance allows
    return db.execute(query)
```

### 4. API Gateway Enforcement

```python
# FastAPI middleware - blocks before route handler
from owkai.middleware import MandatoryGovernanceMiddleware

app.add_middleware(
    MandatoryGovernanceMiddleware,
    api_key="...",
    enforcement_mode="mandatory",
    agent_header="X-Agent-ID"
)

# Route handler only executes if governance allows
@app.delete("/api/users/{id}")
def delete_user(id: int):
    # Governance already approved - safe to execute
    return db.delete_user(id)
```

---

## Security Guarantees

### What We Guarantee

| Guarantee | Description | Verification |
|-----------|-------------|--------------|
| **No Bypass** | Mandatory mode cannot be circumvented | Architectural enforcement |
| **Fail-Closed** | Errors result in block, not allow | Default configuration |
| **Audit Complete** | Every decision is logged | Immutable audit log |
| **Tamper-Proof** | Logs cannot be modified | Cryptographic signing |

### What We Cannot Guarantee

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| Network Failure | If OW-AI unreachable, decision defaults | Fail-closed blocks action |
| Agent Modification | Agent code could be changed | Code signing, integrity checks |
| System Compromise | Root access bypasses everything | Defense in depth |

---

## Next Documents

- [02_ERROR_RESPONSES.md](./02_ERROR_RESPONSES.md) - Complete error response specification
- [03_SDK_ENFORCEMENT.md](./03_SDK_ENFORCEMENT.md) - SDK enforcement implementation
- [04_MCP_ENFORCEMENT.md](./04_MCP_ENFORCEMENT.md) - MCP server enforcement implementation
- [05_INTEGRATION_GUIDE.md](./05_INTEGRATION_GUIDE.md) - Step-by-step integration guide

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | OW-AI Engineering | Initial release |
