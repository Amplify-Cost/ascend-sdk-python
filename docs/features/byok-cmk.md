# BYOK/CMK Encryption Feature Guide

## Overview

Bring Your Own Key (BYOK) / Customer Managed Keys (CMK) enables enterprise customers to maintain complete control over their encryption keys while using ASCEND's AI governance platform.

With BYOK, your sensitive data is encrypted using keys stored in **your AWS account**, ensuring:
- **Data Sovereignty**: You control who can access your encryption keys
- **Regulatory Compliance**: Meet requirements for key management (PCI-DSS, HIPAA, FedRAMP)
- **Revocation Control**: Instantly block ASCEND's access to your data by revoking key permissions

## How It Works

ASCEND uses **envelope encryption** with your Customer Managed Key (CMK):

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENVELOPE ENCRYPTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │  Your CMK        │    │  Data Encryption │                   │
│  │  (AWS KMS)       │───►│  Key (DEK)       │                   │
│  │  In YOUR account │    │  256-bit AES     │                   │
│  └──────────────────┘    └────────┬─────────┘                   │
│                                   │                              │
│                                   ▼                              │
│                          ┌──────────────────┐                   │
│                          │  Your Sensitive  │                   │
│                          │  Data            │                   │
│                          │  (Encrypted)     │                   │
│                          └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

1. **CMK (Customer Managed Key)**: Created and managed in your AWS KMS account
2. **DEK (Data Encryption Key)**: Generated using your CMK, stored encrypted
3. **Your Data**: Encrypted with the DEK using AES-256-GCM

## Key Benefits

### Data Sovereignty
Your CMK never leaves your AWS account. ASCEND only has permission to use the key for encryption/decryption operations - never to export or copy it.

### Instant Revocation
Revoke ASCEND's access at any time by updating your KMS key policy. This immediately blocks all data access (by design).

### Audit Trail
- All key operations are logged in AWS CloudTrail (in your account)
- All ASCEND encryption operations are logged in our audit system
- Complete visibility into who accessed what and when

### Compliance
BYOK helps meet requirements for:
- **PCI-DSS 3.5-3.6**: Cryptographic key management
- **HIPAA 164.312(a)(2)(iv)**: Encryption of PHI
- **SOC 2 CC6.1**: Encryption of data at rest
- **FedRAMP**: FIPS 140-2 validated encryption
- **NIST 800-53 SC-12**: Cryptographic key establishment

## FAIL SECURE Design

**CRITICAL**: BYOK is designed to FAIL SECURE. This means:

| Scenario | Behavior |
|----------|----------|
| CMK access revoked | All data access BLOCKED |
| CMK deleted | Data permanently inaccessible |
| Key policy modified | Operations may be blocked |
| KMS unavailable | Operations temporarily blocked |

This is intentional - your data is protected even if something goes wrong.

## Limitations and Risks

### Permanent Data Loss Risk
If you delete your CMK or permanently revoke access:
- **Your data becomes PERMANENTLY UNRECOVERABLE**
- OW-KAI Technologies cannot recover your data
- There is no "undo" for CMK deletion

### Operational Considerations
- KMS rate limits may affect high-volume operations
- Cross-region replication requires multi-region keys
- Key rotation requires DEK re-wrapping (handled automatically)

### Not Encrypted with BYOK
The following are NOT encrypted with your CMK:
- Metadata (timestamps, IDs, status flags)
- Aggregated analytics (counts, summaries)
- System logs (sanitized of sensitive data)

## Getting Started

See the [Customer KMS Setup Guide](/docs/byok/CUSTOMER_KMS_SETUP.md) for step-by-step setup instructions.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/byok/keys` | POST | Register your CMK |
| `/api/v1/byok/keys` | GET | Get current key status |
| `/api/v1/byok/keys` | DELETE | Revoke/remove key |
| `/api/v1/byok/keys/rotate` | POST | Trigger DEK rotation |
| `/api/v1/byok/health` | GET | Check key health |
| `/api/v1/byok/audit` | GET | View audit log |

See the [API Reference](/docs/api/byok-endpoints.md) for detailed documentation.

## Support

For BYOK-related issues:
1. Check the [Troubleshooting Guide](/docs/guides/byok-integration.md#troubleshooting)
2. Review your AWS CloudTrail logs
3. Contact support with your organization ID and error details

---

*Compliance: SOC 2, PCI-DSS, HIPAA, FedRAMP, NIST 800-53*
