---
sidebar_position: 5
title: MITRE ATT&CK
description: Threat framework mapping and detection
---

# MITRE ATT&CK Framework

Ascend maps all agent actions to the MITRE ATT&CK framework for comprehensive threat detection and security analysis.

## Framework Coverage

| Category | Coverage | Tactics | Techniques |
|----------|----------|---------|------------|
| Enterprise | Full | 14 tactics | 200+ techniques |
| Cloud | Full | AWS, Azure, GCP | Platform-specific |
| ICS | Partial | Industrial controls | Core techniques |

---

## Tactic Coverage

### Enterprise Tactics

| ID | Tactic | Description | Ascend Coverage |
|----|--------|-------------|-----------------|
| TA0001 | Initial Access | Gain entry to network | Monitoring |
| TA0002 | Execution | Run malicious code | Full detection |
| TA0003 | Persistence | Maintain foothold | Full detection |
| TA0004 | Privilege Escalation | Gain higher permissions | Full detection |
| TA0005 | Defense Evasion | Avoid detection | Full detection |
| TA0006 | Credential Access | Steal credentials | Full detection |
| TA0007 | Discovery | Learn about environment | Full detection |
| TA0008 | Lateral Movement | Move through network | Full detection |
| TA0009 | Collection | Gather target data | Full detection |
| TA0010 | Exfiltration | Steal data | Full detection |
| TA0011 | Command and Control | Communicate with compromised systems | Full detection |
| TA0040 | Impact | Manipulate, interrupt, or destroy | Full detection |

---

## Action-to-Tactic Mapping

### TA0002 - Execution

Agent actions that could indicate code execution:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| code_execute | T1059 | Critical | Immediate alert |
| shell_execute | T1059.004 | Critical | Immediate alert |
| script_run | T1059.001 | High | Alert + approval |
| command_execute | T1059 | High | Alert + approval |

**Detection Configuration:**
```json
{
  "action_type": "code_execute",
  "mitre_mapping": {
    "tactic": "TA0002",
    "tactic_name": "Execution",
    "technique": "T1059",
    "technique_name": "Command and Scripting Interpreter",
    "detection_priority": "critical",
    "auto_block": true,
    "alert_immediate": true
  }
}
```

---

### TA0003 - Persistence

Agent actions that could establish persistence:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| user_create | T1136 | High | Alert + approval |
| service_create | T1543 | Critical | Immediate alert |
| scheduled_task | T1053 | High | Alert + approval |
| config_modify | T1098 | High | Alert + approval |

**Persistence Detection:**
```python
# From enrichment.py - Persistence mappings
MITRE_MAPPINGS = {
    "user_create": {
        "mitre_tactic": "TA0003",
        "mitre_tactic_name": "Persistence",
        "mitre_technique": "T1136",
        "mitre_technique_name": "Create Account"
    },
    "service_install": {
        "mitre_tactic": "TA0003",
        "mitre_tactic_name": "Persistence",
        "mitre_technique": "T1543",
        "mitre_technique_name": "Create or Modify System Process"
    }
}
```

---

### TA0004 - Privilege Escalation

Agent actions that could escalate privileges:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| privilege_escalation | T1078 | Critical | Immediate alert |
| role_assign | T1098 | High | Alert + approval |
| permission_grant | T1098.001 | High | Alert + approval |
| sudo_execute | T1548 | Critical | Immediate alert |

**Escalation Alert:**
```json
{
  "alert": {
    "type": "privilege_escalation_attempt",
    "severity": "critical",
    "agent_id": "customer-service-agent",
    "action_type": "role_assign",
    "mitre": {
      "tactic": "TA0004",
      "technique": "T1098",
      "sub_technique": "T1098.001"
    },
    "recommendation": "Verify legitimate business need for elevated access"
  }
}
```

---

### TA0005 - Defense Evasion

Agent actions that could evade detection:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| log_delete | T1562.002 | Critical | Immediate alert |
| audit_disable | T1562.001 | Critical | Immediate alert |
| process_hide | T1564 | Critical | Immediate alert |
| indicator_remove | T1070 | Critical | Immediate alert |

**Evasion Detection:**
```python
# From enrichment.py - Defense Evasion mappings
MITRE_MAPPINGS = {
    "log_delete": {
        "mitre_tactic": "TA0005",
        "mitre_tactic_name": "Defense Evasion",
        "mitre_technique": "T1562",
        "mitre_technique_name": "Impair Defenses"
    },
    "audit_disable": {
        "mitre_tactic": "TA0005",
        "mitre_tactic_name": "Defense Evasion",
        "mitre_technique": "T1562.001",
        "mitre_technique_name": "Disable or Modify Tools"
    }
}
```

---

### TA0006 - Credential Access

Agent actions that could access credentials:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| credential_access | T1003 | Critical | Immediate alert |
| credential_dump | T1003 | Critical | Immediate alert |
| password_spray | T1110.003 | Critical | Immediate alert |
| keylog_capture | T1056 | Critical | Immediate alert |

**Credential Detection:**
```python
# From enrichment.py - Credential Access mappings
MITRE_MAPPINGS = {
    "credential_access": {
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1003",
        "mitre_technique_name": "OS Credential Dumping"
    },
    "credential_read": {
        "mitre_tactic": "TA0006",
        "mitre_tactic_name": "Credential Access",
        "mitre_technique": "T1552",
        "mitre_technique_name": "Unsecured Credentials"
    }
}
```

---

### TA0007 - Discovery

Agent actions that could discover system information:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| network_scan | T1046 | Medium | Alert |
| system_discovery | T1082 | Medium | Alert |
| account_discovery | T1087 | Medium | Alert |
| permission_discovery | T1069 | Medium | Alert |

---

### TA0009 - Collection

Agent actions that could collect data:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| data_collection | T1005 | High | Alert + approval |
| screen_capture | T1113 | High | Alert + approval |
| clipboard_capture | T1115 | High | Alert + approval |
| archive_data | T1560 | High | Alert + approval |

**Collection Detection:**
```python
# From enrichment.py - Collection mappings
MITRE_MAPPINGS = {
    "data_collection": {
        "mitre_tactic": "TA0009",
        "mitre_tactic_name": "Collection",
        "mitre_technique": "T1005",
        "mitre_technique_name": "Data from Local System"
    },
    "database_read": {
        "mitre_tactic": "TA0009",
        "mitre_tactic_name": "Collection",
        "mitre_technique": "T1005",
        "mitre_technique_name": "Data from Local System"
    }
}
```

---

### TA0010 - Exfiltration

Agent actions that could exfiltrate data:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| data_export | T1041 | Critical | Immediate alert |
| data_exfiltration | T1041 | Critical | Immediate alert |
| bulk_transfer | T1048 | Critical | Immediate alert |
| cloud_upload | T1567 | High | Alert + approval |

**Exfiltration Detection:**
```python
# From enrichment.py - Exfiltration mappings
MITRE_MAPPINGS = {
    "data_export": {
        "mitre_tactic": "TA0010",
        "mitre_tactic_name": "Exfiltration",
        "mitre_technique": "T1041",
        "mitre_technique_name": "Exfiltration Over C2 Channel"
    },
    "data_exfiltration": {
        "mitre_tactic": "TA0010",
        "mitre_tactic_name": "Exfiltration",
        "mitre_technique": "T1041",
        "mitre_technique_name": "Exfiltration Over C2 Channel"
    }
}
```

---

### TA0011 - Command and Control

Agent actions that could establish C2:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| external_connection | T1071 | High | Alert |
| remote_access | T1219 | High | Alert + approval |
| proxy_setup | T1090 | High | Alert + approval |
| dns_tunnel | T1071.004 | Critical | Immediate alert |

**C2 Detection:**
```python
# From enrichment.py - C2 mappings
MITRE_MAPPINGS = {
    "external_connection": {
        "mitre_tactic": "TA0011",
        "mitre_tactic_name": "Command and Control",
        "mitre_technique": "T1071",
        "mitre_technique_name": "Application Layer Protocol"
    }
}
```

---

### TA0040 - Impact

Agent actions that could cause impact:

| Action Type | Technique | Risk Level | Detection |
|-------------|-----------|------------|-----------|
| data_destroy | T1485 | Critical | Immediate alert |
| service_stop | T1489 | Critical | Immediate alert |
| data_encrypt | T1486 | Critical | Immediate alert |
| data_wipe | T1561 | Critical | Immediate alert |

**Impact Detection:**
```python
# From enrichment.py - Impact mappings
MITRE_MAPPINGS = {
    "data_destroy": {
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1485",
        "mitre_technique_name": "Data Destruction"
    },
    "service_stop": {
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1489",
        "mitre_technique_name": "Service Stop"
    },
    "data_modify": {
        "mitre_tactic": "TA0040",
        "mitre_tactic_name": "Impact",
        "mitre_technique": "T1565",
        "mitre_technique_name": "Data Manipulation"
    }
}
```

---

## Complete Technique Reference

### Critical Techniques (Auto-Block)

| ID | Name | Actions | Response |
|----|------|---------|----------|
| T1003 | OS Credential Dumping | credential_access, credential_dump | Block + alert |
| T1059 | Command and Scripting Interpreter | code_execute, shell_execute | Block + alert |
| T1485 | Data Destruction | data_destroy, data_wipe | Block + alert |
| T1486 | Data Encrypted for Impact | data_encrypt | Block + alert |
| T1489 | Service Stop | service_stop | Block + alert |
| T1562 | Impair Defenses | log_delete, audit_disable | Block + alert |

### High-Risk Techniques (Alert + Approval)

| ID | Name | Actions | Response |
|----|------|---------|----------|
| T1005 | Data from Local System | data_collection, database_read | Alert + approval |
| T1041 | Exfiltration Over C2 | data_export, data_exfiltration | Alert + approval |
| T1078 | Valid Accounts | privilege_escalation | Alert + approval |
| T1098 | Account Manipulation | user_create, role_assign | Alert + approval |
| T1136 | Create Account | user_create | Alert + approval |
| T1552 | Unsecured Credentials | credential_read | Alert + approval |
| T1565 | Data Manipulation | data_modify | Alert + approval |

### Medium-Risk Techniques (Monitor)

| ID | Name | Actions | Response |
|----|------|---------|----------|
| T1046 | Network Service Discovery | network_scan | Monitor + log |
| T1071 | Application Layer Protocol | external_connection | Monitor + log |
| T1082 | System Information Discovery | system_discovery | Monitor + log |
| T1087 | Account Discovery | account_discovery | Monitor + log |

---

## Detection Rules

### Smart Rule Integration

Create MITRE-aligned smart rules:

```bash
# Create MITRE-based detection rule
curl -X POST "https://pilot.owkai.app/api/smart-rules/generate-from-nl" \
  -H "Cookie: access_token=your_session_cookie" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "Block any credential access attempts and alert security team",
    "context": "mitre_attack"
  }'
```

**Generated Rule:**
```json
{
  "condition": "mitre_technique IN ('T1003', 'T1552', 'T1110') OR action_type LIKE 'credential%'",
  "action": "block_and_alert",
  "risk_level": "critical",
  "mitre_alignment": {
    "tactic": "TA0006",
    "techniques": ["T1003", "T1552", "T1110"]
  }
}
```

---

## Threat Hunting

### Hunt Queries

Query for specific MITRE techniques:

```bash
# Hunt for credential access attempts
curl "https://pilot.owkai.app/api/analytics/trends?mitre_technique=T1003" \
  -H "X-API-Key: your_api_key"

# Hunt for exfiltration attempts
curl "https://pilot.owkai.app/api/analytics/trends?mitre_tactic=TA0010" \
  -H "X-API-Key: your_api_key"
```

### Response:

```json
{
  "hunt_results": {
    "mitre_tactic": "TA0006",
    "mitre_technique": "T1003",
    "total_matches": 3,
    "time_period": "24h",
    "events": [
      {
        "timestamp": "2025-01-15T10:30:00Z",
        "agent_id": "data-agent",
        "action_type": "credential_access",
        "status": "blocked",
        "risk_score": 95
      }
    ],
    "recommendation": "Review agent permissions and investigate blocked attempts"
  }
}
```

---

## MITRE ATT&CK Navigator Export

Export detection coverage to ATT&CK Navigator:

```bash
# Export to Navigator format
curl "https://pilot.owkai.app/api/compliance/export/mitre-navigator" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
{
  "name": "Ascend Detection Coverage",
  "version": "4.5",
  "domain": "enterprise-attack",
  "techniques": [
    {"techniqueID": "T1003", "score": 100, "color": "#ff0000", "comment": "Full detection"},
    {"techniqueID": "T1059", "score": 100, "color": "#ff0000", "comment": "Full detection"},
    {"techniqueID": "T1005", "score": 80, "color": "#ff6600", "comment": "Detection with approval"}
  ]
}
```

---

## Reporting

### MITRE Coverage Report

```bash
# Generate MITRE coverage report
curl -X POST "https://pilot.owkai.app/api/compliance/export/mitre" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "period_start": "2025-01-01",
    "period_end": "2025-01-31",
    "tactics": ["TA0006", "TA0010", "TA0040"],
    "format": "json"
  }'
```

### Report Contents

| Section | Description |
|---------|-------------|
| Coverage Matrix | Tactics and techniques covered |
| Detection Events | Events mapped to MITRE |
| Gap Analysis | Uncovered techniques |
| Recommendations | Coverage improvement suggestions |

---

*For MITRE ATT&CK integration questions, contact security@owkai.app*
