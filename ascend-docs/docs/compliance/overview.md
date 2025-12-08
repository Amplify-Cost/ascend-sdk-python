---
sidebar_position: 1
title: Compliance Overview
description: Enterprise compliance framework and regulatory alignment
---

# Compliance Overview

Ascend provides comprehensive compliance controls aligned with major regulatory frameworks for enterprise AI governance.

## Supported Frameworks

| Framework | Coverage | Certification |
|-----------|----------|---------------|
| SOC 2 Type II | Full | Audit-ready |
| HIPAA | Full | BAA available |
| PCI-DSS | Full | Level 1 compliant |
| NIST 800-53 | Full | Rev 5 aligned |
| NIST CSF | Full | v2.0 aligned |
| GDPR | Full | EU compliant |
| SOX | Full | Section 404 |
| MITRE ATT&CK | Full | v14 mapped |

---

## Compliance Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASCEND COMPLIANCE LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SOC 2      │  │    HIPAA     │  │   PCI-DSS    │          │
│  │  Type II     │  │  Safeguards  │  │  Requirements│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Unified Control Framework                   │    │
│  │                                                          │    │
│  │  • Access Control (AC)    • Audit & Accountability (AU) │    │
│  │  • Configuration Mgmt (CM) • Identification & Auth (IA) │    │
│  │  • System & Comms (SC)    • System & Info Integrity (SI)│    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 Compliance Engine                        │    │
│  │                                                          │    │
│  │  Action → NIST Control → MITRE Technique → Risk Score   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Control Categories

### Access Control (AC)

Controls governing who can access what resources under what conditions.

| Control | Description | Implementation |
|---------|-------------|----------------|
| AC-2 | Account Management | User provisioning, role assignment |
| AC-3 | Access Enforcement | Policy-based authorization |
| AC-4 | Information Flow Enforcement | Data classification controls |
| AC-6 | Least Privilege | Minimal access permissions |

### Audit and Accountability (AU)

Controls ensuring comprehensive audit trails and accountability.

| Control | Description | Implementation |
|---------|-------------|----------------|
| AU-2 | Audit Events | Event logging configuration |
| AU-6 | Audit Review & Analysis | Log analysis and alerting |
| AU-7 | Audit Reduction | Log filtering and summarization |
| AU-9 | Protection of Audit Info | Immutable audit logs |

### Configuration Management (CM)

Controls for managing system configurations securely.

| Control | Description | Implementation |
|---------|-------------|----------------|
| CM-3 | Configuration Change Control | Change management workflows |
| CM-6 | Configuration Settings | Secure baseline configurations |
| CM-8 | Information System Inventory | Asset management |

### Identification and Authentication (IA)

Controls for identity verification and authentication.

| Control | Description | Implementation |
|---------|-------------|----------------|
| IA-2 | Identification & Authentication | User/agent authentication |
| IA-4 | Identifier Management | Unique identifier assignment |
| IA-5 | Authenticator Management | Credential lifecycle |

### System and Communications Protection (SC)

Controls protecting system boundaries and communications.

| Control | Description | Implementation |
|---------|-------------|----------------|
| SC-7 | Boundary Protection | Network segmentation |
| SC-8 | Transmission Confidentiality | TLS 1.3 encryption |
| SC-13 | Cryptographic Protection | AES-256 encryption |

### System and Information Integrity (SI)

Controls ensuring system and data integrity.

| Control | Description | Implementation |
|---------|-------------|----------------|
| SI-3 | Malicious Code Protection | Threat detection |
| SI-4 | System Monitoring | Real-time monitoring |
| SI-12 | Information Handling | Data lifecycle management |

---

## Automatic Compliance Mapping

Every agent action is automatically mapped to compliance controls:

```json
{
  "action_type": "database_write",
  "compliance_mapping": {
    "nist_control": "AC-3",
    "nist_family": "Access Control",
    "nist_description": "Access Enforcement",
    "mitre_tactic": "TA0003",
    "mitre_technique": "T1098",
    "soc2_control": "CC6.1",
    "pci_requirement": "7.1"
  }
}
```

### Mapping Coverage

| Action Category | NIST Controls | MITRE Tactics | SOC 2 |
|-----------------|---------------|---------------|-------|
| Read Operations | AC-3, AU-2 | TA0009 | CC6.1 |
| Write Operations | AC-3, AU-9 | TA0003 | CC6.1 |
| Delete Operations | AC-6, CM-3 | TA0040 | CC7.1 |
| Data Export | AC-4, SI-12 | TA0010 | CC6.1 |
| Authentication | IA-2, IA-5 | TA0006 | CC6.1 |
| System Changes | CM-3, SI-4 | TA0005 | CC7.2 |

---

## Compliance Reports

### Available Report Types

| Report | Frequency | Format | Purpose |
|--------|-----------|--------|---------|
| SOC 2 Evidence | On-demand | PDF/JSON | Auditor review |
| HIPAA Audit Trail | Daily | JSON | PHI access tracking |
| PCI-DSS Compliance | Monthly | PDF | Payment data compliance |
| NIST Control Status | Weekly | JSON | Control effectiveness |
| Risk Assessment | Real-time | Dashboard | Current risk posture |

### Generating Reports

```bash
# SOC 2 evidence export
curl "https://pilot.owkai.app/api/compliance/export/soc2" \
  -H "X-API-Key: your_api_key"

# HIPAA audit trail
curl "https://pilot.owkai.app/api/compliance/export/hipaa?days=30" \
  -H "X-API-Key: your_api_key"

# NIST control assessment
curl "https://pilot.owkai.app/api/compliance/export/nist" \
  -H "X-API-Key: your_api_key"
```

---

## Audit Trail Structure

Every action generates an immutable audit record:

```json
{
  "audit_id": "aud_20250115_143052_a1b2c3d4",
  "timestamp": "2025-01-15T14:30:52Z",
  "organization_id": 4,
  "user_id": 15,
  "agent_id": "customer-service-agent",
  "action": {
    "type": "database_write",
    "description": "Update customer record",
    "target": "customers.email",
    "risk_score": 45
  },
  "compliance": {
    "nist_control": "AC-3",
    "mitre_tactic": "TA0003",
    "soc2_control": "CC6.1",
    "pci_requirement": "7.1"
  },
  "decision": {
    "status": "approved",
    "method": "auto_approve",
    "reason": "Risk below threshold"
  },
  "context": {
    "ip_address": "10.0.1.50",
    "session_id": "sess_abc123",
    "correlation_id": "corr_xyz789"
  }
}
```

---

## Data Residency

Ascend supports configurable data residency for compliance:

| Region | Data Center | Compliance |
|--------|-------------|------------|
| US East | AWS us-east-2 | SOC 2, HIPAA, PCI-DSS |
| US West | AWS us-west-2 | SOC 2, HIPAA, PCI-DSS |
| EU | AWS eu-west-1 | GDPR, SOC 2 |
| UK | AWS eu-west-2 | UK GDPR, SOC 2 |

---

## Encryption Standards

### Data at Rest

| Data Type | Encryption | Key Management |
|-----------|------------|----------------|
| Database | AES-256-GCM | AWS KMS |
| Backups | AES-256-GCM | AWS KMS |
| Audit Logs | AES-256-GCM | AWS KMS |
| Config Files | AES-256-GCM | AWS KMS |

### Data in Transit

| Connection | Protocol | Certificate |
|------------|----------|-------------|
| API | TLS 1.3 | RSA-2048 |
| WebSocket | WSS/TLS 1.3 | RSA-2048 |
| Database | TLS 1.3 | RDS CA |
| Internal | mTLS | Internal CA |

---

## Compliance API

Access compliance data programmatically:

```bash
# Get compliance status
GET /api/compliance/status

# Get control mappings
GET /api/compliance/controls

# Export audit trail
GET /api/compliance/audit-trail?start=2025-01-01&end=2025-01-31

# Generate compliance report
POST /api/compliance/reports/generate
```

---

## Next Steps

- [SOC 2 Type II](./soc2) - Detailed SOC 2 control mappings
- [HIPAA](./hipaa) - Healthcare compliance requirements
- [NIST 800-53](./nist-800-53) - Federal security controls
- [MITRE ATT&CK](./mitre-attack) - Threat framework mapping

---

*For compliance questions or audit support, contact compliance@owkai.app*
