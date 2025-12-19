---
title: Ascend Enterprise Risk Scoring System
sidebar_position: 1
---

# Ascend Enterprise Risk Scoring System

| Field | Value |
|-------|-------|
| **Document ID** | ASCEND-HELP-007 |
| **Version** | 1.0.0 |
| **Last Updated** | December 19, 2025 |
| **Author** | Ascend Engineering Team |
| **Classification** | Enterprise Client Documentation |
| **Compliance** | SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4 |

**Document ID:** ASCEND-INT-002
**Version:** 2.0.0
**Classification:** Technical Reference
**Compliance:** SOC 2 CC3.2, NIST 800-30, PCI-DSS 6.1
**Publisher:** OW-kai Corporation

---

## Overview

The Ascend risk scoring system uses a multi-layer approach to calculate accurate, enterprise-grade risk scores for AI agent actions. This document explains each layer and how they combine.

---

## Risk Scoring Pipeline

```
                                    ┌─────────────────────────────────────┐
                                    │     Agent Action Submitted          │
                                    └─────────────┬───────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: FIRST-PASS ENRICHMENT                                               │
│  ─────────────────────────────────────────────────────────────────────────── │
│  • Action type classification                                                 │
│  • Tool name analysis                                                        │
│  • Initial NIST 800-53 mapping                                               │
│  • Initial MITRE ATT&CK mapping                                              │
│  • Base risk level determination (low/medium/high/critical)                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: CVSS ASSESSMENT                                                     │
│  ─────────────────────────────────────────────────────────────────────────── │
│  • CVSS 3.1 vector calculation                                               │
│  • Base score computation (0-10)                                             │
│  • Severity classification: None, Low, Medium, High, Critical                │
│  • Score normalization to 0-100 scale                                        │
│                                                                               │
│  CVSS Vector Components:                                                     │
│  • Attack Vector (AV): Network, Adjacent, Local, Physical                    │
│  • Attack Complexity (AC): Low, High                                         │
│  • Privileges Required (PR): None, Low, High                                 │
│  • User Interaction (UI): None, Required                                     │
│  • Scope (S): Unchanged, Changed                                             │
│  • Confidentiality Impact (C): None, Low, High                              │
│  • Integrity Impact (I): None, Low, High                                    │
│  • Availability Impact (A): None, Low, High                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: MITRE ATT&CK MAPPING                                               │
│  ─────────────────────────────────────────────────────────────────────────── │
│  • Tactic identification (14 tactics)                                        │
│  • Technique mapping (500+ techniques)                                       │
│  • Threat intelligence integration                                           │
│  • Attack pattern classification                                             │
│                                                                               │
│  Common Tactics:                                                             │
│  • TA0001 Initial Access    • TA0009 Collection                             │
│  • TA0002 Execution         • TA0010 Exfiltration                           │
│  • TA0003 Persistence       • TA0011 Command & Control                      │
│  • TA0004 Privilege Esc.    • TA0040 Impact                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: NIST 800-53 CONTROL MAPPING                                        │
│  ─────────────────────────────────────────────────────────────────────────── │
│  • Control family identification                                              │
│  • Specific control assignment                                               │
│  • Compliance recommendation generation                                       │
│                                                                               │
│  Control Families:                                                           │
│  • AC (Access Control)      • AU (Audit & Accountability)                   │
│  • IA (Identification)      • SC (System & Communications)                  │
│  • CM (Configuration)       • SI (System & Information Integrity)           │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: POLICY ENGINE EVALUATION                                           │
│  ─────────────────────────────────────────────────────────────────────────── │
│  • Organization-specific policy matching                                     │
│  • Natural language policy support                                           │
│  • Real-time evaluation (<200ms SLA)                                        │
│  • Decision: ALLOW, DENY, REQUIRE_APPROVAL                                  │
│  • Policy risk score (0-100)                                                │
│                                                                               │
│  Policy Types:                                                               │
│  • Allow policies (whitelist actions)                                        │
│  • Deny policies (blacklist actions)                                        │
│  • Approval policies (require human review)                                 │
│  • Conditional policies (time-based, user-based, context-based)            │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: HYBRID RISK CALCULATOR                                             │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                               │
│  Formula:                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Hybrid = (Environment × 35%) + (Data Sensitivity × 30%) +               ││
│  │          (CVSS × 25%) + (Operational Context × 10%) × Resource Mult.   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  Environment Factor (35%):                                                   │
│  • production = 100, staging = 60, development = 30, test = 10             │
│                                                                               │
│  Data Sensitivity Factor (30%):                                              │
│  • PII present = 90, PHI present = 95, PCI data = 100, Standard = 30      │
│                                                                               │
│  CVSS Factor (25%):                                                          │
│  • Direct mapping from CVSS score × 10                                      │
│                                                                               │
│  Operational Context (10%):                                                  │
│  • Business hours, user role, historical patterns                           │
│                                                                               │
│  Resource Multipliers:                                                       │
│  • Database: 1.3x    • Encryption: 1.5x                                    │
│  • Financial: 1.4x   • Admin: 1.5x                                         │
│  • Customer: 1.2x    • Production: 1.3x                                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7: RISK FUSION                                                        │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                               │
│  Final Score Formula:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Final Risk Score = (Policy Risk × 80%) + (Hybrid Risk × 20%)          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  Rationale:                                                                  │
│  • Policy risk is weighted 80% because organization policies are the        │
│    primary governance mechanism                                              │
│  • Hybrid risk contributes 20% to incorporate technical factors that        │
│    policies may not fully capture                                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  LAYER 8: SAFETY RULES (ALWAYS APPLIED)                                      │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                               │
│  Rule 1: CRITICAL CVSS Floor                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  IF CVSS_severity == "CRITICAL" THEN score = MAX(score, 85)            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  Rule 2: Policy DENY Override                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  IF policy_decision == "DENY" THEN score = 100                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
│  Rule 3: PII Production Floor                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  IF (contains_pii AND environment == "production") THEN                ││
│  │     score = MAX(score, 70)                                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
                                                  │
                                                  ▼
                                    ┌─────────────────────────────────────┐
                                    │     Final Risk Score (0-100)        │
                                    │     Risk Level Classification       │
                                    │     Approval Determination          │
                                    └─────────────────────────────────────┘
```

---

## Risk Level Thresholds

| Risk Score | Risk Level | Requires Approval | Auto-Action |
|------------|------------|-------------------|-------------|
| 0-44 | Low | No | Auto-approve |
| 45-69 | Medium | Configurable | Depends on policy |
| 70-84 | High | Yes | Requires review |
| 85-100 | Critical | Yes | Escalation required |

---

## Example Calculations

### Example 1: Low-Risk Database Read

**Input:**
```json
{
  "action_type": "database.read",
  "environment": "development",
  "contains_pii": false,
  "description": "Query user preferences"
}
```

**Calculation:**
```
Layer 1: Base risk level = "low"
Layer 2: CVSS score = 2.5 (Low severity)
Layer 5: Policy risk = 25 (no matching deny policies)
Layer 6: Hybrid = (30 × 0.35) + (30 × 0.30) + (25 × 0.25) + (20 × 0.10) = 27.75
Layer 7: Fusion = (25 × 0.8) + (27.75 × 0.2) = 25.55
Layer 8: No safety rules triggered

Final Score: 26 (Low risk, auto-approved)
```

### Example 2: High-Risk Financial Transfer

**Input:**
```json
{
  "action_type": "financial.transfer",
  "environment": "production",
  "contains_pii": true,
  "description": "Transfer $50,000 to vendor account"
}
```

**Calculation:**
```
Layer 1: Base risk level = "high"
Layer 2: CVSS score = 7.5 (High severity)
Layer 5: Policy risk = 80 (financial transfer policy match)
Layer 6: Hybrid = (100 × 0.35) + (90 × 0.30) + (75 × 0.25) + (50 × 0.10) × 1.4 = 91.0
Layer 7: Fusion = (80 × 0.8) + (91 × 0.2) = 82.2
Layer 8: Rule 3 triggered (PII in production) → MAX(82.2, 70) = 82.2

Final Score: 82 (High risk, requires approval)
```

### Example 3: Critical Policy Denied Action

**Input:**
```json
{
  "action_type": "database.delete",
  "environment": "production",
  "contains_pii": true,
  "description": "Delete all customer records from production"
}
```

**Calculation:**
```
Layer 1: Base risk level = "critical"
Layer 2: CVSS score = 9.8 (Critical severity)
Layer 5: Policy decision = DENY (production deletion policy)
Layer 6: Hybrid = 95.0
Layer 7: Fusion = (100 × 0.8) + (95 × 0.2) = 99.0
Layer 8: Rule 2 triggered (Policy DENY) → score = 100

Final Score: 100 (Critical, action blocked)
```

---

## Integration Response Example

```json
{
  "id": 12345,
  "risk_score": 82,
  "risk_level": "high",
  "requires_approval": true,
  "risk_assessment": {
    "policy_evaluated": true,
    "policy_risk": 80,
    "policy_decision": "PolicyDecision.require_approval",
    "hybrid_risk": 91,
    "hybrid_breakdown": {
      "environment_factor": 35.0,
      "data_sensitivity_factor": 27.0,
      "cvss_factor": 18.75,
      "operational_factor": 5.0,
      "resource_multiplier": 1.4,
      "pre_multiplier_score": 65.0
    },
    "hybrid_formula": "(100×35%)+(90×30%)+(75×25%)+(50×10%)×1.4",
    "fusion_applied": true,
    "fusion_formula": "(80 × 0.8) + (91 × 0.2)"
  },
  "compliance": {
    "nist_control": "AC-6",
    "mitre_tactic": "TA0040",
    "cvss_score": 7.5,
    "cvss_severity": "HIGH"
  }
}
```

---

## Customization Options

### Organization-Specific Risk Weights

Contact your Ascend administrator to customize:
- Environment weight percentages
- Data sensitivity thresholds
- Resource multiplier values
- Safety rule thresholds

### Policy-Based Overrides

Create policies to:
- Whitelist specific action types
- Blacklist high-risk operations
- Require approval for specific agents
- Apply time-based restrictions

---

## Compliance Mapping

| Framework | Controls Covered |
|-----------|------------------|
| SOC 2 | CC3.2, CC6.1, CC7.1, CC7.2 |
| NIST 800-53 | AC-2, AC-3, AC-6, AU-12, IR-4, IR-6, SI-3 |
| PCI-DSS | 6.1, 7.1, 8.3.1, 12.10 |
| HIPAA | 164.312(a), 164.312(b), 164.312(d) |
| GDPR | Article 32, Article 33 |

---

*Document Version: 2.0.0 | Last Updated: December 2025 | Compliance: SOC 2 CC3.2, NIST 800-30*
