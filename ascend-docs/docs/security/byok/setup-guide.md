---
sidebar_position: 2
title: Setup Guide
description: Step-by-step BYOK/CMK setup instructions
---

# BYOK Setup Guide

> **Time Required:** 30 minutes | **Skill Level:** Security Admin

This guide walks you through setting up Bring Your Own Key (BYOK) encryption with your AWS KMS Customer Managed Key (CMK).

## Prerequisites

Before starting, ensure you have:

- [ ] AWS Account with administrative access
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] ASCEND Platform admin account
- [ ] ASCEND Enterprise subscription (BYOK is an enterprise feature)

## Step 1: Create Your CMK in AWS KMS

### Option A: AWS Console

1. Go to **AWS Console → KMS → Customer managed keys**
2. Click **Create key**
3. Select:
   - Key type: **Symmetric**
   - Key usage: **Encrypt and decrypt**
   - Advanced options: **KMS** (key material origin)
4. Add alias: `alias/ascend-byok-key`
5. Add description: `Customer managed key for ASCEND BYOK encryption`
6. Complete the wizard (key administrators and users will be configured in Step 2)

### Option B: AWS CLI

```bash
# Create the key
aws kms create-key \
  --description "Customer managed key for ASCEND BYOK encryption" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS \
  --tags TagKey=Purpose,TagValue=ASCEND-BYOK

# Create an alias for easier reference
KEY_ID=$(aws kms list-keys --query 'Keys[-1].KeyId' --output text)
aws kms create-alias \
  --alias-name alias/ascend-byok-key \
  --target-key-id $KEY_ID

# Verify the key
aws kms describe-key --key-id alias/ascend-byok-key
```

### Option C: Terraform

```hcl
resource "aws_kms_key" "ascend_byok" {
  description             = "Customer managed key for ASCEND BYOK encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Purpose = "ASCEND-BYOK"
    Environment = "production"
  }
}

resource "aws_kms_alias" "ascend_byok" {
  name          = "alias/ascend-byok-key"
  target_key_id = aws_kms_key.ascend_byok.key_id
}
```

## Step 2: Configure Key Policy

Your CMK needs a key policy that grants ASCEND cross-account access.

### Get ASCEND's AWS Account Information

Contact your ASCEND account representative or retrieve from the dashboard:

```
ASCEND AWS Account ID: 123456789012
ASCEND IAM Role: arn:aws:iam::123456789012:role/ascend-byok-service
```

### Update Key Policy

Add this statement to your key policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM policies",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow ASCEND to use this key for BYOK encryption",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/ascend-byok-service"
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
          "kms:ViaService": "secretsmanager.us-east-2.amazonaws.com"
        }
      }
    }
  ]
}
```

### Apply via AWS CLI

```bash
# Save policy to file
cat > key-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM policies",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow ASCEND to use this key",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/ascend-byok-service"
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:GenerateDataKeyWithoutPlaintext",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Apply the policy
aws kms put-key-policy \
  --key-id alias/ascend-byok-key \
  --policy-name default \
  --policy file://key-policy.json
```

## Step 3: Verify Key Access

Before registering with ASCEND, verify the key is accessible:

```bash
# Test encryption
echo "test" | aws kms encrypt \
  --key-id alias/ascend-byok-key \
  --plaintext fileb:///dev/stdin \
  --output text --query CiphertextBlob | base64 --decode > /tmp/encrypted

# Test decryption
aws kms decrypt \
  --ciphertext-blob fileb:///tmp/encrypted \
  --output text --query Plaintext | base64 --decode

# Should output: test
```

## Step 4: Get Your Key ARN

```bash
KEY_ARN=$(aws kms describe-key \
  --key-id alias/ascend-byok-key \
  --query 'KeyMetadata.Arn' \
  --output text)

echo "Your Key ARN: $KEY_ARN"
```

Save this ARN — you'll need it in the next step.

## Step 5: Register Key with ASCEND

### Using curl

```bash
# Get your ASCEND token
ASCEND_TOKEN="your-bearer-token"

# Register the key
curl -X POST https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key_arn": "arn:aws:kms:us-east-1:YOUR_ACCOUNT:key/YOUR_KEY_ID",
    "key_alias": "ascend-byok-key",
    "description": "Production BYOK encryption key"
  }'
```

### Expected Response

```json
{
  "status": "success",
  "message": "Customer managed key registered successfully",
  "key_id": "byok_abc123",
  "key_arn": "arn:aws:kms:us-east-1:YOUR_ACCOUNT:key/YOUR_KEY_ID",
  "registration_time": "2025-12-16T10:30:00Z",
  "requires_waiver_acknowledgment": true
}
```

## Step 6: Acknowledge Legal Waiver

BYOK requires acknowledgment of the legal waiver before activation.

### View the Waiver

```bash
curl https://pilot.owkai.app/api/v1/byok/legal-waiver \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Acknowledge the Waiver

```bash
curl -X POST https://pilot.owkai.app/api/v1/byok/legal-waiver/acknowledge \
  -H "Authorization: Bearer $ASCEND_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "acknowledged": true,
    "acknowledged_by": "security-admin@company.com",
    "acknowledged_terms": [
      "I understand that deleting my CMK will result in permanent data loss",
      "I understand that revoking ASCEND access will make data unreadable",
      "I accept responsibility for CMK availability and security"
    ]
  }'
```

## Step 7: Verify BYOK is Active

### Check Key Status

```bash
curl https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

Expected response:
```json
{
  "status": "active",
  "key_arn": "arn:aws:kms:us-east-1:YOUR_ACCOUNT:key/YOUR_KEY_ID",
  "key_alias": "ascend-byok-key",
  "registered_at": "2025-12-16T10:30:00Z",
  "waiver_acknowledged": true,
  "last_used": "2025-12-16T10:35:00Z"
}
```

### Check Health

```bash
curl https://pilot.owkai.app/api/v1/byok/health \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

Expected response:
```json
{
  "status": "healthy",
  "key_status": "active",
  "cmk_accessible": true,
  "last_encryption": "2025-12-16T10:35:00Z",
  "last_decryption": "2025-12-16T10:34:00Z"
}
```

## Step 8: Enable Key Rotation (Recommended)

Enable automatic key rotation in AWS KMS:

```bash
aws kms enable-key-rotation --key-id alias/ascend-byok-key

# Verify rotation is enabled
aws kms get-key-rotation-status --key-id alias/ascend-byok-key
```

## Step 9: Set Up CloudTrail Monitoring

Monitor all key usage in your AWS CloudTrail:

```bash
# Create CloudTrail for KMS events
aws cloudtrail create-trail \
  --name ascend-byok-audit \
  --s3-bucket-name your-cloudtrail-bucket \
  --include-global-service-events

# Enable KMS event logging
aws cloudtrail put-event-selectors \
  --trail-name ascend-byok-audit \
  --event-selectors '[{
    "ReadWriteType": "All",
    "IncludeManagementEvents": true,
    "DataResources": [{
      "Type": "AWS::KMS::Key",
      "Values": ["arn:aws:kms:us-east-1:YOUR_ACCOUNT:key/YOUR_KEY_ID"]
    }]
  }]'
```

## Verification Checklist

After setup, verify:

- [ ] CMK created in AWS KMS
- [ ] Key policy grants ASCEND cross-account access
- [ ] Key registered with ASCEND (`/api/v1/byok/keys` returns `active`)
- [ ] Legal waiver acknowledged
- [ ] Health check passes (`/api/v1/byok/health` returns `healthy`)
- [ ] Key rotation enabled in AWS KMS
- [ ] CloudTrail monitoring configured

## What Happens Next

Once BYOK is active:

1. **New data** is encrypted with DEKs wrapped by your CMK
2. **Existing data** will be re-encrypted on next access (gradual migration)
3. **All key operations** are logged in both ASCEND and your CloudTrail
4. **Key health** is monitored continuously

## Rollback Instructions

If you need to disable BYOK and return to ASCEND-managed encryption:

```bash
# Revoke BYOK key
curl -X DELETE https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

:::warning
Revoking BYOK will:
1. Migrate data back to ASCEND-managed encryption
2. Remove cross-account access to your CMK
3. Retain audit logs of the BYOK period
:::

## Next Steps

- [API Reference](./api-reference) — Complete API documentation
- [Troubleshooting](./troubleshooting) — Common issues and solutions
- [BYOK Overview](./) — Return to overview

## Support

For setup assistance:

- **Email**: security@owkai.app
- **Enterprise Support**: Contact your account representative
