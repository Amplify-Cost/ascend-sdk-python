---
sidebar_position: 4
title: Troubleshooting
description: Common BYOK issues and solutions
---

# BYOK Troubleshooting

Common issues and solutions for BYOK/CMK encryption.

## Quick Diagnostics

Run these commands to quickly diagnose BYOK issues:

```bash
# Check BYOK health
curl https://pilot.owkai.app/api/v1/byok/health \
  -H "Authorization: Bearer $ASCEND_TOKEN"

# Check key status
curl https://pilot.owkai.app/api/v1/byok/keys \
  -H "Authorization: Bearer $ASCEND_TOKEN"

# Check waiver status
curl https://pilot.owkai.app/api/v1/byok/legal-waiver/status \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

---

## Common Issues

### Key Registration Failed

**Symptom:** `POST /api/v1/byok/keys` returns error

#### Error: "Invalid ARN format"

**Cause:** Key ARN doesn't match expected format

**Solution:**
1. Verify ARN format: `arn:aws:kms:REGION:ACCOUNT:key/KEY_ID`
2. Check for typos in region or account ID
3. Ensure you're using the key ARN, not alias ARN

```bash
# Get correct ARN
aws kms describe-key --key-id alias/ascend-byok-key \
  --query 'KeyMetadata.Arn' --output text
```

#### Error: "Cannot access CMK"

**Cause:** ASCEND doesn't have permission to use your key

**Solution:**
1. Verify key policy includes ASCEND's IAM role
2. Check the cross-account access statement

```bash
# Check key policy
aws kms get-key-policy --key-id alias/ascend-byok-key --policy-name default

# Required statement:
{
  "Sid": "Allow ASCEND",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::123456789012:role/ascend-byok-service"
  },
  "Action": [
    "kms:Encrypt",
    "kms:Decrypt",
    "kms:GenerateDataKey",
    "kms:DescribeKey"
  ],
  "Resource": "*"
}
```

#### Error: "Organization already has BYOK key"

**Cause:** A key is already registered for your organization

**Solution:**
1. Check existing key: `GET /api/v1/byok/keys`
2. Delete existing key first: `DELETE /api/v1/byok/keys`
3. Then register new key

---

### Health Check Failing

**Symptom:** `/api/v1/byok/health` returns `unhealthy`

#### Error: "CMK inaccessible"

**Possible Causes:**
1. Key policy was modified
2. Key was disabled
3. Key was scheduled for deletion
4. AWS KMS service issue

**Solutions:**

1. **Check key status in AWS:**
   ```bash
   aws kms describe-key --key-id alias/ascend-byok-key
   # Look for "KeyState": "Enabled"
   ```

2. **Verify key policy:**
   ```bash
   aws kms get-key-policy --key-id alias/ascend-byok-key --policy-name default
   ```

3. **Check AWS KMS service health:**
   - Visit [AWS Service Health Dashboard](https://status.aws.amazon.com/)

4. **Cancel deletion if scheduled:**
   ```bash
   aws kms cancel-key-deletion --key-id YOUR_KEY_ID
   aws kms enable-key --key-id YOUR_KEY_ID
   ```

#### Error: "DEK invalid"

**Cause:** Data Encryption Key is corrupted or missing

**Solution:**
1. Trigger DEK rotation:
   ```bash
   curl -X POST https://pilot.owkai.app/api/v1/byok/keys/rotate \
     -H "Authorization: Bearer $ASCEND_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"rotation_type": "dek", "reason": "DEK recovery"}'
   ```

2. If rotation fails, contact ASCEND support

---

### Encryption/Decryption Errors

**Symptom:** Operations failing with encryption errors

#### Error: "KMS ThrottlingException"

**Cause:** Too many requests to AWS KMS

**Solution:**
1. AWS KMS has request quotas per second
2. Contact AWS to increase quotas
3. Or contact ASCEND to enable request batching

```bash
# Check current quotas
aws service-quotas get-service-quota \
  --service-code kms \
  --quota-code L-6E65D7BB
```

#### Error: "IncorrectKeyException"

**Cause:** Trying to decrypt with wrong key

**Solution:**
1. This usually means data was encrypted with a different key
2. Check if you changed BYOK keys recently
3. Contact ASCEND support for data migration assistance

---

### Waiver Issues

**Symptom:** BYOK won't activate after key registration

#### Error: "Waiver not acknowledged"

**Cause:** Legal waiver hasn't been acknowledged

**Solution:**
1. Get the waiver:
   ```bash
   curl https://pilot.owkai.app/api/v1/byok/legal-waiver \
     -H "Authorization: Bearer $ASCEND_TOKEN"
   ```

2. Acknowledge the waiver:
   ```bash
   curl -X POST https://pilot.owkai.app/api/v1/byok/legal-waiver/acknowledge \
     -H "Authorization: Bearer $ASCEND_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "acknowledged": true,
       "acknowledged_by": "your-email@company.com"
     }'
   ```

#### Error: "Requires reacknowledgment"

**Cause:** Waiver version has been updated

**Solution:**
1. Check current waiver version
2. Re-acknowledge with updated terms

---

### Performance Issues

**Symptom:** Slow encryption/decryption operations

#### High Latency

**Possible Causes:**
1. Network latency to AWS KMS
2. KMS throttling
3. Large data volumes

**Solutions:**

1. **Check baseline latency:**
   ```bash
   curl https://pilot.owkai.app/api/v1/byok/health \
     -H "Authorization: Bearer $ASCEND_TOKEN" | jq '.latency_ms'
   ```

2. **Expected latency:**
   - Normal: 30-50ms per operation
   - High: 100-200ms (investigate)
   - Critical: >500ms (urgent)

3. **Optimization options:**
   - Enable caching (contact ASCEND)
   - Increase KMS quotas
   - Consider regional key placement

---

## Emergency Procedures

### CMK Accidentally Disabled

```bash
# Re-enable the key immediately
aws kms enable-key --key-id YOUR_KEY_ID

# Verify it's enabled
aws kms describe-key --key-id YOUR_KEY_ID --query 'KeyMetadata.KeyState'
```

### CMK Scheduled for Deletion

:::danger
If your CMK is deleted, data encrypted with it will be **permanently lost**.
:::

```bash
# Cancel deletion immediately
aws kms cancel-key-deletion --key-id YOUR_KEY_ID

# Re-enable the key
aws kms enable-key --key-id YOUR_KEY_ID

# Verify recovery
curl https://pilot.owkai.app/api/v1/byok/health \
  -H "Authorization: Bearer $ASCEND_TOKEN"
```

### Key Policy Accidentally Removed

```bash
# Re-apply the key policy with ASCEND access
aws kms put-key-policy \
  --key-id YOUR_KEY_ID \
  --policy-name default \
  --policy file://key-policy.json
```

---

## Monitoring & Alerts

### Recommended CloudWatch Alarms

Set up these alarms in AWS CloudWatch for your KMS key:

```bash
# Create alarm for key access failures
aws cloudwatch put-metric-alarm \
  --alarm-name "ASCEND-BYOK-AccessDenied" \
  --metric-name "AccessDenied" \
  --namespace "AWS/KMS" \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:REGION:ACCOUNT:your-alert-topic \
  --dimensions Name=KeyId,Value=YOUR_KEY_ID
```

### Recommended ASCEND Alerts

Configure these in your ASCEND dashboard:

| Alert | Condition | Severity |
|-------|-----------|----------|
| CMK Inaccessible | Health check fails | Critical |
| High Latency | >200ms for 5 minutes | Warning |
| Encryption Failures | >10 in 5 minutes | High |
| Key Rotation Needed | >90 days since rotation | Medium |

---

## Getting Help

### Before Contacting Support

Gather this information:

1. **BYOK Health Output:**
   ```bash
   curl https://pilot.owkai.app/api/v1/byok/health \
     -H "Authorization: Bearer $ASCEND_TOKEN"
   ```

2. **Key Status:**
   ```bash
   aws kms describe-key --key-id YOUR_KEY_ID
   ```

3. **Recent Audit Logs:**
   ```bash
   curl "https://pilot.owkai.app/api/v1/byok/audit?limit=50" \
     -H "Authorization: Bearer $ASCEND_TOKEN"
   ```

4. **AWS CloudTrail Events:**
   ```bash
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=ResourceName,AttributeValue=YOUR_KEY_ARN \
     --max-results 50
   ```

### Contact Information

| Issue Type | Contact |
|------------|---------|
| Configuration help | support@owkai.app |
| Security concerns | security@owkai.app |
| Emergency (data at risk) | Enterprise support hotline |

---

## FAQ

**Q: Can I use a key from a different AWS region?**

A: Yes, cross-region keys are supported. Latency may be higher.

**Q: Can I use AWS KMS multi-region keys?**

A: Yes, multi-region keys are supported for disaster recovery scenarios.

**Q: What happens if my AWS account is suspended?**

A: ASCEND will lose access to your CMK, and data operations will fail. Contact ASCEND support immediately.

**Q: Can I have multiple BYOK keys?**

A: Currently, one key per organization. Multi-key support is on the roadmap.

**Q: How do I migrate to a new CMK?**

A: Contact ASCEND support for assisted migration. Do not delete the old key until migration is complete.

## Next Steps

- [Setup Guide](./setup-guide) — Step-by-step setup instructions
- [API Reference](./api-reference) — Complete API documentation
- [BYOK Overview](./) — Return to overview
