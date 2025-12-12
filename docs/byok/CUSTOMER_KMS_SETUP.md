---
Document ID: ASCEND-BYOK-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 Type II, PCI-DSS 3.5, HIPAA 164.312, FedRAMP SC-12, NIST 800-53 SC-12/SC-13
SEC Ticket: BYOK-002
---

# BYOK Customer KMS Setup Guide

This guide explains how to configure your AWS KMS Customer Managed Key (CMK) for use with ASCEND's Bring Your Own Key (BYOK) feature.

## Overview

ASCEND's BYOK feature allows you to control the encryption keys used to protect your data at rest. With BYOK:

- **You own the key**: The CMK lives in your AWS account
- **You control access**: You can revoke ASCEND's access at any time
- **You see usage**: All key operations are logged in your CloudTrail
- **Data sovereignty**: Your encryption keys never leave your AWS account

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENVELOPE ENCRYPTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   YOUR AWS ACCOUNT                        ASCEND PLATFORM                   │
│   ────────────────                        ───────────────                   │
│                                                                             │
│   ┌─────────────────┐                    ┌─────────────────────────────┐   │
│   │  AWS KMS        │                    │  Data Encryption            │   │
│   │                 │                    │                             │   │
│   │  CMK (Customer  │◄─── Encrypt ──────►│  1. Generate random DEK     │   │
│   │   Managed Key)  │     DEK            │  2. Encrypt data with DEK   │   │
│   │                 │                    │  3. Encrypt DEK with CMK    │   │
│   │  - Never leaves │                    │  4. Store encrypted DEK     │   │
│   │    KMS          │                    │     + encrypted data        │   │
│   │  - You control  │                    │                             │   │
│   │    access       │                    │  DEK = Data Encryption Key  │   │
│   └─────────────────┘                    └─────────────────────────────┘   │
│                                                                             │
│   Your Controls:                          ASCEND Never Has:                 │
│   ✓ Key rotation policy                   ✗ Access to your CMK directly    │
│   ✓ Key access policy                     ✗ Ability to export keys         │
│   ✓ Key deletion                          ✗ Access after you revoke        │
│   ✓ CloudTrail audit                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- AWS account with KMS access
- IAM permissions to create KMS keys and policies
- ASCEND organization ID (found in Settings > Organization)

## Step 1: Create Your CMK

### Option A: AWS Console

1. Go to **AWS KMS** > **Customer managed keys**
2. Click **Create key**
3. Configure:
   - **Key type**: Symmetric
   - **Key usage**: Encrypt and decrypt
   - **Key material origin**: KMS (recommended)
4. Add alias: `alias/ascend-byok-{your-org-name}`
5. Complete the wizard (skip key administrators and users for now)

### Option B: AWS CLI

```bash
# Create the key
aws kms create-key \
  --description "ASCEND BYOK encryption key for {YOUR_ORG_NAME}" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT \
  --region us-east-2

# Note the KeyId from the response, then create an alias
aws kms create-alias \
  --alias-name alias/ascend-byok-{your-org-name} \
  --target-key-id {KEY_ID} \
  --region us-east-2
```

### Option C: Terraform

```hcl
resource "aws_kms_key" "ascend_byok" {
  description             = "ASCEND BYOK encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true  # Recommended

  tags = {
    Purpose = "ASCEND BYOK"
    Environment = "production"
  }
}

resource "aws_kms_alias" "ascend_byok" {
  name          = "alias/ascend-byok"
  target_key_id = aws_kms_key.ascend_byok.key_id
}
```

## Step 2: Configure Key Policy

Apply this key policy to grant ASCEND access to your CMK.

**IMPORTANT**: Replace `{YOUR_ORG_ID}` with your ASCEND organization ID.

### Key Policy JSON

```json
{
  "Version": "2012-10-17",
  "Id": "ascend-byok-policy",
  "Statement": [
    {
      "Sid": "EnableRootPermissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{YOUR_AWS_ACCOUNT_ID}:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "AllowASCENDEncryptionService",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::110948415588:role/ascend-byok-service"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:GenerateDataKeyWithoutPlaintext",
        "kms:DescribeKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:EncryptionContext:tenant_id": "{YOUR_ORG_ID}",
          "kms:EncryptionContext:service": "ascend"
        }
      }
    }
  ]
}
```

### Apply via AWS Console

1. Go to **AWS KMS** > **Customer managed keys**
2. Select your key
3. Go to **Key policy** tab
4. Click **Edit**
5. Replace with the policy above (updating placeholders)
6. Click **Save changes**

### Apply via AWS CLI

```bash
aws kms put-key-policy \
  --key-id {YOUR_KEY_ID} \
  --policy-name default \
  --policy file://ascend-byok-policy.json \
  --region us-east-2
```

## Step 3: Register Key with ASCEND

### Via Dashboard

1. Go to **Settings** > **Security** > **Encryption**
2. Click **Configure BYOK**
3. Enter your CMK ARN: `arn:aws:kms:us-east-2:{YOUR_ACCOUNT}:key/{KEY_ID}`
4. Click **Validate & Register**

### Via API

```bash
curl -X POST "https://pilot.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer {YOUR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "cmk_arn": "arn:aws:kms:us-east-2:{YOUR_ACCOUNT}:key/{KEY_ID}",
    "cmk_alias": "alias/ascend-byok"
  }'
```

### Expected Response

```json
{
  "organization_id": 123,
  "cmk_arn": "arn:aws:kms:us-east-2:***:key/***",
  "cmk_alias": "alias/ascend-byok",
  "status": "active",
  "status_reason": "Key validated successfully",
  "last_validated_at": "2025-12-11T10:30:00Z",
  "created_at": "2025-12-11T10:30:00Z"
}
```

## Step 4: Verify Key Access

ASCEND performs validation during registration and every 15 minutes thereafter.

### Check Status via API

```bash
curl -X GET "https://pilot.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

### Check Status via Health Endpoint

```bash
curl -X GET "https://pilot.owkai.app/api/v1/byok/health" \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

## Key Rotation

### Automatic Rotation (Recommended)

AWS KMS supports automatic annual key rotation. ASCEND automatically detects when your CMK is rotated and generates new DEKs encrypted with the new key material.

To enable automatic rotation:

```bash
aws kms enable-key-rotation --key-id {YOUR_KEY_ID} --region us-east-2
```

### Manual Rotation

You can also manually trigger key rotation via the ASCEND API:

```bash
curl -X POST "https://pilot.owkai.app/api/v1/byok/keys/rotate" \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

## Revoking Access

To immediately revoke ASCEND's access to your data:

### Option 1: Update Key Policy

Remove the `AllowASCENDEncryptionService` statement from your key policy:

```bash
aws kms put-key-policy \
  --key-id {YOUR_KEY_ID} \
  --policy-name default \
  --policy file://revoked-policy.json \
  --region us-east-2
```

### Option 2: Disable the Key

```bash
aws kms disable-key --key-id {YOUR_KEY_ID} --region us-east-2
```

### What Happens After Revocation

1. ASCEND detects access revocation within 15 minutes (health check)
2. Your BYOK status changes to `error`
3. Data encrypted with your CMK becomes unreadable
4. Platform operations continue for non-encrypted data
5. To restore access, update your key policy or re-enable the key

## Monitoring & Audit

### CloudTrail Events

All ASCEND key operations are logged in your CloudTrail:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com \
  --region us-east-2 \
  --query 'Events[?contains(CloudTrailEvent, `ascend`)].CloudTrailEvent'
```

### Key Operations Logged

| Operation | CloudTrail Event | Description |
|-----------|------------------|-------------|
| Generate DEK | `GenerateDataKey` | New data encryption key created |
| Encrypt DEK | `Encrypt` | DEK encrypted for storage |
| Decrypt DEK | `Decrypt` | DEK decrypted for use |
| Validation | `DescribeKey` | Health check validation |

### ASCEND Audit Log

View BYOK operations in ASCEND:

```bash
curl -X GET "https://pilot.owkai.app/api/v1/byok/audit" \
  -H "Authorization: Bearer {YOUR_TOKEN}"
```

## Troubleshooting

### "Unable to access the provided KMS key"

**Cause**: Key policy doesn't grant ASCEND access.

**Fix**: Verify the key policy includes the `AllowASCENDEncryptionService` statement with correct:
- ASCEND account ID: `110948415588`
- Role name: `ascend-byok-service`
- Encryption context conditions

### "Key validation failed"

**Cause**: ASCEND cannot perform required operations.

**Fix**: Ensure key policy grants these actions:
- `kms:Encrypt`
- `kms:Decrypt`
- `kms:GenerateDataKey`
- `kms:GenerateDataKeyWithoutPlaintext`
- `kms:DescribeKey`

### "Encryption context mismatch"

**Cause**: Wrong organization ID in key policy condition.

**Fix**: Update the `kms:EncryptionContext:tenant_id` value to match your ASCEND organization ID.

### "Key is in PENDING_DELETION state"

**Cause**: Key scheduled for deletion.

**Fix**: Cancel deletion if unintended:
```bash
aws kms cancel-key-deletion --key-id {YOUR_KEY_ID} --region us-east-2
aws kms enable-key --key-id {YOUR_KEY_ID} --region us-east-2
```

## Security Best Practices

1. **Enable automatic rotation**: Rotate keys annually at minimum
2. **Use key aliases**: Makes rotation seamless
3. **Restrict key administrators**: Limit who can modify key policy
4. **Enable CloudTrail**: Monitor all key usage
5. **Use multiple keys per environment**: Separate dev/staging/prod
6. **Document key owners**: Ensure business continuity
7. **Test revocation**: Verify you can revoke access when needed

## Compliance Notes

### SOC 2 Type II
- BYOK satisfies CC6.1 (Encryption of sensitive data)
- Customer controls key lifecycle

### PCI-DSS
- BYOK satisfies Requirement 3.5 (Key management procedures)
- Customer owns key management

### HIPAA
- BYOK satisfies §164.312(a)(2)(iv) (Encryption of ePHI)
- Customer controls ePHI encryption

### FedRAMP
- BYOK satisfies SC-12 (Cryptographic key management)
- Customer-managed keys in customer AWS account

## Support

For BYOK-related issues:

- **Email**: support@ascendowkai.com
- **Subject prefix**: `[BYOK]`
- **Include**: Your organization ID and CMK ARN (masked)

---

*This guide is maintained by the Ascend Engineering Team.*
