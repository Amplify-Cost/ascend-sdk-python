---
sidebar_position: 1
title: Action Types
description: Complete reference of supported action types
---

# Action Types Reference

Ascend supports 56+ enterprise action types with automatic CVSS scoring, NIST mapping, and MITRE ATT&CK alignment.

## Action Type Categories

| Category | Count | Risk Range | Description |
|----------|-------|------------|-------------|
| Read Operations | 5 | Low | Data retrieval actions |
| Write Operations | 4 | Medium | Data modification actions |
| Delete Operations | 3 | High | Data removal actions |
| Data Movement | 3 | High-Critical | Data transfer actions |
| Financial Services | 8 | High-Critical | Banking and trading actions |
| Healthcare/HIPAA | 5 | High-Critical | PHI access and modification |
| PII/GDPR | 4 | High | Personal data operations |
| System/Infrastructure | 6 | Critical | System-level actions |
| Communication | 3 | Medium | Messaging and notifications |
| HR/Employee Data | 4 | High | HR system operations |
| Legal/Contracts | 3 | High | Legal document operations |
| MCP Server Tools | 8 | High-Critical | MCP protocol actions |

---

## Read Operations (Low Risk)

Basic data retrieval operations with minimal security impact.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `database_read` | 2.5 | Low | AC-3 | TA0009 |
| `file_read` | 2.5 | Low | AC-3 | TA0009 |
| `api_read` | 2.5 | Low | AC-3 | TA0009 |
| `analytics_query` | 2.5 | Low | AC-3 | TA0009 |
| `api_call` | 3.0 | Low | AC-3 | TA0009 |

### CVSS Metrics (Read Operations)

```json
{
  "database_read": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "LOW",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
  }
}
```

---

## Write Operations (Medium Risk)

Data modification operations requiring standard access controls.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `database_write` | 5.0 | Medium | AC-3 | TA0003 |
| `file_write` | 5.0 | Medium | AC-3 | TA0003 |
| `api_write` | 5.0 | Medium | AC-3 | TA0003 |
| `record_update` | 4.5 | Medium | AC-3 | TA0003 |

### CVSS Metrics (Write Operations)

```json
{
  "database_write": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "LOW",
    "integrity_impact": "LOW",
    "availability_impact": "NONE"
  }
}
```

---

## Delete Operations (High Risk)

Data removal operations requiring elevated approval.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `database_delete` | 7.5 | High | AC-6 | TA0040 |
| `file_delete` | 7.5 | High | AC-6 | TA0040 |
| `record_delete` | 7.0 | High | AC-6 | TA0040 |

### CVSS Metrics (Delete Operations)

```json
{
  "database_delete": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "NONE",
    "integrity_impact": "HIGH",
    "availability_impact": "HIGH"
  }
}
```

---

## Data Movement (High-Critical Risk)

Data transfer operations with exfiltration detection.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `data_export` | 7.5 | High | SI-12 | TA0010 |
| `data_exfiltration` | 9.0 | Critical | AC-4 | TA0010 |
| `bulk_transfer` | 8.0 | High | SI-12 | TA0010 |

### CVSS Metrics (Data Movement)

```json
{
  "data_exfiltration": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "CHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
  }
}
```

---

## Financial Services (High-Critical Risk)

Banking and trading operations with strict compliance requirements.

| Action Type | CVSS | Risk Level | NIST Control | Compliance |
|-------------|------|------------|--------------|------------|
| `execute_trade` | 8.5 | Critical | AC-3, AU-2 | SOX, PCI-DSS |
| `funds_transfer` | 9.0 | Critical | AC-3, AU-2 | PCI-DSS |
| `payment_process` | 8.5 | Critical | AC-3 | PCI-DSS |
| `wire_transfer` | 9.0 | Critical | AC-3, AU-9 | SOX |
| `account_modify` | 7.5 | High | AC-3, CM-3 | SOX |
| `transaction_void` | 7.5 | High | AC-3, AU-9 | SOX |
| `credit_approval` | 8.0 | High | AC-3 | SOX |
| `limit_override` | 8.5 | Critical | AC-6 | SOX |

### CVSS Metrics (Financial)

```json
{
  "funds_transfer": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "HIGH",
    "user_interaction": "NONE",
    "scope": "CHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "HIGH",
    "availability_impact": "LOW"
  }
}
```

---

## Healthcare/HIPAA (High-Critical Risk)

Protected Health Information (PHI) operations.

| Action Type | CVSS | Risk Level | HIPAA Control | MITRE Tactic |
|-------------|------|------------|---------------|--------------|
| `phi_access` | 6.5 | High | 164.312(a)(1) | TA0009 |
| `phi_modify` | 8.1 | Critical | 164.312(c)(1) | TA0040 |
| `phi_export` | 8.5 | Critical | 164.312(e)(1) | TA0010 |
| `prescription_write` | 8.5 | Critical | 164.312(c)(1) | TA0003 |
| `diagnosis_modify` | 8.5 | Critical | 164.312(c)(1) | TA0040 |

### CVSS Metrics (Healthcare)

```json
{
  "phi_access": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "HIGH",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
  }
}
```

---

## PII/GDPR (High Risk)

Personal Identifiable Information operations.

| Action Type | CVSS | Risk Level | NIST Control | Compliance |
|-------------|------|------------|--------------|------------|
| `pii_access` | 6.5 | High | AC-3 | GDPR Art. 6 |
| `pii_modify` | 7.5 | High | AC-3, AU-9 | GDPR Art. 17 |
| `pii_delete` | 7.5 | High | SI-12 | GDPR Art. 17 |
| `consent_modify` | 6.5 | High | AC-3 | GDPR Art. 7 |

### CVSS Metrics (PII)

```json
{
  "pii_access": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "NONE",
    "availability_impact": "NONE"
  }
}
```

---

## System/Infrastructure (Critical Risk)

System-level operations requiring maximum security controls.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `system_modification` | 9.0 | Critical | CM-3 | TA0003 |
| `config_change` | 8.5 | Critical | CM-3 | TA0005 |
| `credential_access` | 9.0 | Critical | IA-5 | TA0006 |
| `privilege_escalation` | 9.5 | Critical | AC-6 | TA0004 |
| `service_restart` | 7.5 | High | CM-3 | TA0040 |
| `schema_change` | 8.5 | Critical | CM-3 | TA0003 |

### CVSS Metrics (System)

```json
{
  "privilege_escalation": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "CHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "HIGH",
    "availability_impact": "HIGH"
  }
}
```

---

## Communication (Medium Risk)

Messaging and notification operations.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `email_send` | 4.5 | Medium | AU-2 | TA0010 |
| `notification_send` | 3.5 | Low | AU-2 | TA0011 |
| `message_send` | 4.0 | Medium | AU-2 | TA0011 |

### CVSS Metrics (Communication)

```json
{
  "email_send": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "UNCHANGED",
    "confidentiality_impact": "LOW",
    "integrity_impact": "LOW",
    "availability_impact": "NONE"
  }
}
```

---

## HR/Employee Data (High Risk)

Human resources system operations.

| Action Type | CVSS | Risk Level | NIST Control | Compliance |
|-------------|------|------------|--------------|------------|
| `employee_record_access` | 6.5 | High | AC-3 | GDPR |
| `payroll_modify` | 8.0 | High | AC-3, AU-9 | SOX |
| `benefits_change` | 7.0 | High | AC-3 | ERISA |
| `termination_process` | 7.5 | High | AC-2 | SOX |

---

## Legal/Contracts (High Risk)

Legal document and contract operations.

| Action Type | CVSS | Risk Level | NIST Control | Compliance |
|-------------|------|------------|--------------|------------|
| `contract_sign` | 7.5 | High | AC-3, AU-9 | SOX |
| `contract_modify` | 7.5 | High | AC-3, CM-3 | SOX |
| `legal_hold` | 7.0 | High | AU-9 | eDiscovery |

---

## MCP Server Tools (High-Critical Risk)

Model Context Protocol (MCP) server operations.

| Action Type | CVSS | Risk Level | NIST Control | MITRE Tactic |
|-------------|------|------------|--------------|--------------|
| `execute_query` | 6.5 | High | AC-3 | TA0009 |
| `execute_command` | 9.0 | Critical | AC-3 | TA0002 |
| `shell_execute` | 9.5 | Critical | AC-3, CM-3 | TA0002 |
| `code_execute` | 9.5 | Critical | AC-3 | TA0002 |
| `file_system_access` | 7.0 | High | AC-3 | TA0009 |
| `network_request` | 6.5 | High | SC-7 | TA0011 |
| `process_spawn` | 8.5 | Critical | AC-3 | TA0002 |
| `memory_access` | 8.0 | High | AC-3 | TA0006 |

### CVSS Metrics (MCP Server)

```json
{
  "shell_execute": {
    "attack_vector": "NETWORK",
    "attack_complexity": "LOW",
    "privileges_required": "LOW",
    "user_interaction": "NONE",
    "scope": "CHANGED",
    "confidentiality_impact": "HIGH",
    "integrity_impact": "HIGH",
    "availability_impact": "HIGH"
  }
}
```

---

## Custom Action Types

Register custom action types for your organization:

```bash
# Register custom action type
curl -X POST "https://pilot.owkai.app/api/registry/action-types" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "custom_approval",
    "display_name": "Custom Approval Process",
    "category": "workflow",
    "default_risk_score": 45,
    "cvss_metrics": {
      "attack_vector": "NETWORK",
      "attack_complexity": "LOW",
      "privileges_required": "LOW",
      "confidentiality_impact": "LOW",
      "integrity_impact": "LOW",
      "availability_impact": "NONE"
    },
    "nist_control": "AC-3",
    "mitre_tactic": "TA0003"
  }'
```

---

## Action Type Submission

Submit an action with proper typing:

```bash
curl -X POST "https://pilot.owkai.app/api/v1/actions/submit" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-service-agent",
    "action_type": "database_write",
    "description": "Update customer email address",
    "tool_name": "postgresql",
    "target_system": "customers_db"
  }'
```

### Response with Automatic Enrichment

```json
{
  "id": 1547,
  "status": "approved",
  "risk_score": 45,
  "risk_level": "medium",
  "cvss_score": 5.0,
  "cvss_severity": "medium",
  "nist_control": "AC-3",
  "nist_description": "Access Enforcement",
  "mitre_tactic": "TA0003",
  "mitre_technique": "T1098"
}
```

---

## Risk Score Calculation

Risk scores are calculated from CVSS metrics:

```
Risk Score = CVSS Base Score × 10 + Context Modifiers

Context Modifiers:
- After hours: +10
- Sensitive data: +15
- External target: +10
- Bulk operation: +15
- First time action: +5
```

---

*For action type questions, contact support@owkai.app*
