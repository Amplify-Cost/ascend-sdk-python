# BYOK Integration Guide

## Prerequisites

Before integrating BYOK:

1. **AWS Account** with KMS permissions
2. **ASCEND Organization** with admin access
3. **IAM permissions** to create KMS keys and policies

## Step-by-Step Setup

### Step 1: Create Your KMS Key

Create a symmetric encryption key in your AWS account:

```bash
aws kms create-key \
  --description "ASCEND Platform Encryption Key" \
  --key-spec SYMMETRIC_DEFAULT \
  --key-usage ENCRYPT_DECRYPT \
  --tags TagKey=Purpose,TagValue=ASCEND-BYOK
```

Save the `KeyId` from the response.

### Step 2: Create Key Alias (Optional)

```bash
aws kms create-alias \
  --alias-name alias/ascend-byok \
  --target-key-id <your-key-id>
```

### Step 3: Apply Key Policy

Replace the default key policy with one that grants ASCEND access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow ASCEND Platform Access",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ASCEND_ACCOUNT_ID:role/ascend-byok-role"
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
          "kms:EncryptionContext:service": "ascend",
          "kms:EncryptionContext:tenant_id": "YOUR_ORG_ID"
        }
      }
    }
  ]
}
```

**Important:** Replace:
- `YOUR_ACCOUNT_ID` with your AWS account ID
- `ASCEND_ACCOUNT_ID` with the ASCEND platform account ID (provided during onboarding)
- `YOUR_ORG_ID` with your ASCEND organization ID

### Step 4: Register Key with ASCEND

Use the API or dashboard to register your CMK:

```bash
curl -X POST "https://api.ascend.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cmk_arn": "arn:aws:kms:us-east-2:YOUR_ACCOUNT:key/YOUR_KEY_ID",
    "cmk_alias": "ascend-byok"
  }'
```

### Step 5: Verify Integration

Check that BYOK is working:

```bash
curl -X GET "https://api.ascend.owkai.app/api/v1/byok/health" \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "byok_enabled": true,
  "status": "healthy",
  "cmk_accessible": true
}
```

## Key Rotation

### Automatic Rotation (Recommended)

Enable automatic rotation in AWS KMS:

```bash
aws kms enable-key-rotation --key-id <your-key-id>
```

ASCEND automatically detects CMK rotation and re-wraps DEKs within 15 minutes.

### Manual Rotation

If you need immediate rotation:

```bash
curl -X POST "https://api.ascend.owkai.app/api/v1/byok/keys/rotate" \
  -H "Authorization: Bearer $TOKEN"
```

## Troubleshooting

### Error: "Key validation failed"

**Cause:** ASCEND cannot access your CMK.

**Solution:**
1. Verify the key ARN is correct
2. Check the key policy includes ASCEND's principal
3. Ensure the encryption context conditions are correct
4. Verify the key is enabled in AWS KMS

```bash
aws kms describe-key --key-id <your-key-id>
```

### Error: "Access denied"

**Cause:** The key policy doesn't grant ASCEND sufficient permissions.

**Solution:**
1. Review the key policy statement for ASCEND
2. Ensure all required actions are allowed:
   - `kms:Encrypt`
   - `kms:Decrypt`
   - `kms:GenerateDataKey`
   - `kms:DescribeKey`

### Error: "Key status is revoked"

**Cause:** You revoked ASCEND's access to the CMK.

**Solution:**
1. If intentional: Data is blocked as designed
2. If unintentional: Update the key policy to restore access

### Error: "Organization already has a registered key"

**Cause:** A CMK is already registered for your organization.

**Solution:**
```bash
# Remove existing key first
curl -X DELETE "https://api.ascend.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer $TOKEN"

# Then register new key
curl -X POST "https://api.ascend.owkai.app/api/v1/byok/keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cmk_arn": "arn:aws:kms:..."}'
```

### Health Check Shows "unhealthy"

**Steps to diagnose:**

1. **Check AWS CloudTrail** for KMS access errors
2. **Verify key status** in AWS Console
3. **Check key policy** hasn't been modified
4. **Review ASCEND audit log**:
   ```bash
   curl -X GET "https://api.ascend.owkai.app/api/v1/byok/audit?limit=10" \
     -H "Authorization: Bearer $TOKEN"
   ```

## Best Practices

### Security

1. **Enable CloudTrail logging** for KMS events
2. **Use separate keys** for different environments (dev/staging/prod)
3. **Enable key rotation** (AWS rotates annually by default)
4. **Monitor CloudWatch alarms** for unusual KMS activity

### Operations

1. **Test in staging** before production deployment
2. **Document your key ARNs** and policies
3. **Create runbooks** for key rotation and emergency revocation
4. **Set up alerts** for BYOK health status changes

### Compliance

1. **Retain CloudTrail logs** per your compliance requirements
2. **Document key management procedures** for auditors
3. **Regular access reviews** of key policies
4. **Test disaster recovery** procedures annually

## Emergency Procedures

### Immediate Revocation

To immediately block ASCEND's access to your data:

```bash
# Option 1: Update key policy to remove ASCEND
aws kms put-key-policy \
  --key-id <your-key-id> \
  --policy-name default \
  --policy file://policy-without-ascend.json

# Option 2: Disable the key entirely
aws kms disable-key --key-id <your-key-id>
```

**Warning:** This immediately blocks all data access. Use only in emergencies.

### Restoring Access

To restore access after revocation:

1. Update key policy to include ASCEND principal
2. Enable the key if disabled
3. Wait for health check (up to 15 minutes) or trigger manually:
   ```bash
   curl -X GET "https://api.ascend.owkai.app/api/v1/byok/health" \
     -H "Authorization: Bearer $TOKEN"
   ```

---

*For additional support, contact support@owkai.app with your organization ID.*
