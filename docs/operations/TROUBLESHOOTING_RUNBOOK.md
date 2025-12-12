---
Document ID: ASCEND-OPS-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Internal Operations
Last Updated: December 2025
Compliance: SOC 2 CC7.4/CC7.5, NIST 800-53 IR-4/IR-6
SEC Ticket: SEC-101
---

# ASCEND Platform Troubleshooting Runbook

Enterprise-grade incident response and troubleshooting procedures for the ASCEND AI Governance Platform.

---

## Table of Contents

- [1. Quick Reference](#1-quick-reference)
  - [1.1 Configuration Variables](#11-configuration-variables)
  - [1.2 Emergency Contacts](#12-emergency-contacts)
  - [1.3 Escalation Matrix](#13-escalation-matrix)
  - [1.4 Critical Commands Cheat Sheet](#14-critical-commands-cheat-sheet)
  - [1.5 Log Locations](#15-log-locations)
  - [1.6 CloudWatch Dashboards](#16-cloudwatch-dashboards)
- [2. Incident Categories](#2-incident-categories)
  - [2.1 Authentication Failures](#21-authentication-failures)
  - [2.2 Authorization Failures](#22-authorization-failures)
  - [2.3 SDK/Agent Connectivity](#23-sdkagent-connectivity)
  - [2.4 Kill-Switch Failures](#24-kill-switch-failures)
  - [2.5 Workflow/Action Processing](#25-workflowaction-processing)
  - [2.6 Database Connectivity](#26-database-connectivity)
  - [2.7 Performance Degradation](#27-performance-degradation)
  - [2.8 Notification Failures](#28-notification-failures)
- [3. AWS Service Troubleshooting](#3-aws-service-troubleshooting)
- [4. Multi-Tenant Isolation Verification](#4-multi-tenant-isolation-verification)
- [5. Compliance & Audit](#5-compliance--audit)
- [6. Appendix](#6-appendix)

---

## 1. Quick Reference

### 1.1 Configuration Variables

Replace these placeholders with actual values from your environment:

| Variable | Description | Example |
|----------|-------------|---------|
| `{ACCOUNT_ID}` | AWS Account ID | `110948415588` |
| `{REGION}` | AWS Region | `us-east-2` |
| `{CLUSTER_NAME}` | ECS Cluster Name | `owkai-pilot-cluster` |
| `{SERVICE_NAME}` | ECS Service Name | `owkai-pilot-backend` |
| `{DB_INSTANCE}` | RDS Instance ID | `owkai-pilot-db` |
| `{DB_HOST}` | RDS Endpoint | `owkai-pilot-db.xxx.{REGION}.rds.amazonaws.com` |
| `{LOG_GROUP}` | CloudWatch Log Group | `/ecs/owkai-pilot-backend` |
| `{COGNITO_POOL_ID}` | Cognito User Pool ID | `{REGION}_xxxxxxxx` |
| `{SNS_TOPIC_ARN}` | Agent Control SNS Topic | `arn:aws:sns:{REGION}:{ACCOUNT_ID}:ascend-agent-control` |
| `{ORG_ID}` | Organization ID (tenant) | `1`, `34`, etc. |
| `{API_KEY}` | API Key (masked in logs) | `owkai_***` |

### 1.2 Emergency Contacts

| Role | Contact | Method | Availability |
|------|---------|--------|--------------|
| Platform Owner | Greg (CEO) | Slack DM / Phone | 24/7 for SEV-1 |
| On-Call Engineer | TBD | PagerDuty (future) | Business hours |

> **Note:** For pilot phase, all escalations go directly to Greg. Future expansion will add on-call rotation.

### 1.3 Escalation Matrix

| Severity | Definition | Response Time | Escalation | Example Incidents |
|----------|------------|---------------|------------|-------------------|
| **SEV-1** | Platform down OR security breach | 15 min | Greg immediately | RDS down, cross-tenant leak, RLS function failure |
| **SEV-2** | Major feature broken, multiple customers | 1 hr | Greg within 1 hr | Kill-switch failing, SDK auth broken |
| **SEV-3** | Single customer issue, workaround exists | 4 hrs | Greg next business day | One customer login issue |
| **SEV-4** | Minor issue, no customer impact | 24 hrs | Normal backlog | Documentation typo |

### 1.4 Critical Commands Cheat Sheet

```bash
# === HEALTH CHECK ===
curl -s https://pilot.owkai.app/api/health | jq .

# === ECS SERVICE STATUS ===
aws ecs describe-services \
  --cluster {CLUSTER_NAME} \
  --services {SERVICE_NAME} \
  --region {REGION} \
  --query 'services[0].{running:runningCount,desired:desiredCount,status:status}'

# === RECENT ERRORS (last hour) ===
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --filter-pattern "ERROR" \
  --start-time $(( $(date +%s) - 3600 ))000 \
  --region {REGION} \
  --query 'events[*].message' --output text | head -50

# === RDS STATUS ===
aws rds describe-db-instances \
  --db-instance-identifier {DB_INSTANCE} \
  --region {REGION} \
  --query 'DBInstances[0].{status:DBInstanceStatus,az:AvailabilityZone}'

# === FORCE ECS REDEPLOY ===
aws ecs update-service \
  --cluster {CLUSTER_NAME} \
  --service {SERVICE_NAME} \
  --force-new-deployment \
  --region {REGION}
```

### 1.5 Log Locations

| Component | CloudWatch Log Group | Retention |
|-----------|---------------------|-----------|
| FastAPI Backend | `/ecs/owkai-pilot-backend` | 30 days |
| Cognito | `/aws/cognito/userpools/{COGNITO_POOL_ID}` | 30 days |
| RDS PostgreSQL | `/aws/rds/instance/{DB_INSTANCE}/postgresql` | 7 days |
| ALB Access Logs | S3: `ascend-alb-logs-{ACCOUNT_ID}/` | 90 days |
| SNS Delivery | CloudWatch Metrics | N/A |
| SQS Metrics | CloudWatch Metrics | N/A |

### 1.6 CloudWatch Dashboards

| Dashboard | Purpose | URL |
|-----------|---------|-----|
| ASCEND-Platform-Health | Overall platform health | `https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=ASCEND-Platform-Health` |
| ASCEND-ECS-Metrics | Container CPU/Memory | `https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=ASCEND-ECS-Metrics` |
| ASCEND-RDS-Performance | Database performance | `https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=ASCEND-RDS-Performance` |
| ASCEND-API-Latency | API response times | `https://{REGION}.console.aws.amazon.com/cloudwatch/home?region={REGION}#dashboards:name=ASCEND-API-Latency` |

---

## 2. Incident Categories

### 2.1 Authentication Failures

#### Scenario 2.1.1: SDK Returns 401 Unauthorized

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Single tenant, all SDK operations blocked |
| **Data Risk** | None (access denied) |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 20 min without resolution |

**Symptoms:**
- Agent SDK receives HTTP 401 response
- Error message: "Invalid or missing API key"
- All agent actions failing for one organization

**Forensic Preservation (before remediation):**
```bash
# Capture current state
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --filter-pattern "401" \
  --start-time $(( $(date +%s) - 3600 ))000 \
  --region {REGION} \
  --query 'events[*].{time:timestamp,msg:message}' > /tmp/401_errors_$(date +%Y%m%d_%H%M%S).json
```

**Diagnostic Steps:**

1. **Verify API key format** (should start with `owkai_` prefix, 32+ chars)
   ```bash
   # Customer provides key - verify format only (never log full key)
   echo "Key starts with: $(echo '{API_KEY}' | cut -c1-10)..."
   ```

2. **Check key exists in database:**
   ```sql
   -- SEC-101: Always filter by organization_id for multi-tenant safety
   SELECT id, organization_id, status, created_at,
          LEFT(key_prefix, 10) || '***' as key_preview
   FROM api_keys
   WHERE organization_id = {ORG_ID}
     AND status = 'active'
   ORDER BY created_at DESC;
   ```

3. **Verify key not revoked:**
   ```sql
   SELECT id, status, revoked_at, revoked_reason
   FROM api_keys
   WHERE organization_id = {ORG_ID}
     AND key_prefix LIKE 'owkai_%'
   ORDER BY created_at DESC LIMIT 5;
   ```

4. **Test RLS lookup function:**
   ```sql
   -- Test auth function (use test key, not production)
   SELECT * FROM auth_lookup_api_key('{API_KEY}');
   ```

5. **Review backend logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name {LOG_GROUP} \
     --filter-pattern "auth" \
     --start-time $(( $(date +%s) - 1800 ))000 \
     --region {REGION} \
     --query 'events[*].message' --output text | grep -i "401\|invalid\|key"
   ```

**Remediation:**

| Root Cause | Fix |
|------------|-----|
| Key not found | Customer regenerates key in dashboard |
| Key revoked | Investigate reason, re-enable if appropriate |
| Key expired | Customer generates new key |
| Hash mismatch | Verify customer using correct key value |

**Fail-Secure Fallback:**
If primary fix fails within 20 min:
1. Verify RLS function is operational (see Scenario 2.1.5)
2. Check if issue is platform-wide or tenant-specific
3. Escalate to Greg if platform-wide

**Verification:**
```bash
# Test API with new/fixed key
curl -s -X GET "https://pilot.owkai.app/api/health" \
  -H "X-API-Key: {NEW_API_KEY}" | jq .
```

**Post-Incident Actions:**
- [ ] Log incident in `audit_logs` table
- [ ] Document root cause
- [ ] Update customer if their action required

---

#### Scenario 2.1.2: Dashboard Login Fails

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 (multiple users) / SEV-3 (single user) |
| **Blast Radius** | Single tenant, dashboard access only |
| **Data Risk** | None (access denied) |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 30 min without resolution |

**Symptoms:**
- User cannot login to dashboard
- Cognito error or redirect loop
- "User not found" or "Invalid credentials" error

**Diagnostic Steps:**

1. **Check Cognito user status:**
   ```bash
   aws cognito-idp admin-get-user \
     --user-pool-id {COGNITO_POOL_ID} \
     --username "{USER_EMAIL}" \
     --region {REGION}
   ```

2. **Verify user exists in database:**
   ```sql
   SELECT id, email, organization_id, is_suspended, cognito_sub
   FROM users
   WHERE email = '{USER_EMAIL}'
     AND organization_id = {ORG_ID};
   ```

3. **Check organization status:**
   ```sql
   SELECT id, name, status, is_active
   FROM organizations
   WHERE id = {ORG_ID};
   ```

4. **Review Cognito logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name "/aws/cognito/userpools/{COGNITO_POOL_ID}" \
     --filter-pattern "{USER_EMAIL}" \
     --start-time $(( $(date +%s) - 3600 ))000 \
     --region {REGION}
   ```

**Remediation:**

| Root Cause | Fix |
|------------|-----|
| `FORCE_CHANGE_PASSWORD` | User must reset password via forgot password flow |
| User disabled in Cognito | Re-enable: `aws cognito-idp admin-enable-user ...` |
| `is_suspended = true` | Investigate reason, update if appropriate |
| Organization inactive | Activate organization |
| Cognito/DB mismatch | Re-sync user: update `cognito_sub` in database |

**Fail-Secure Fallback:**
If fix fails within 30 min:
1. Verify Cognito service health in AWS status page
2. Check if issue affects all users or single user
3. For single user: create new account as workaround
4. Escalate to Greg if platform-wide

**Verification:**
- User successfully logs in
- Session cookie set correctly
- Dashboard loads without errors

---

#### Scenario 2.1.3: API Key Not Found in Database

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Single tenant |
| **Data Risk** | None |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 15 min |

**Symptoms:**
- SDK returns 401
- Key was previously working
- Customer claims key is correct

**Diagnostic Steps:**

1. **Search for key by prefix:**
   ```sql
   SELECT id, organization_id, status, key_prefix, created_at
   FROM api_keys
   WHERE key_prefix LIKE 'owkai_%'
     AND organization_id = {ORG_ID}
   ORDER BY created_at DESC;
   ```

2. **Check if key was deleted:**
   ```sql
   -- Check audit logs for key deletion
   SELECT * FROM audit_logs
   WHERE organization_id = {ORG_ID}
     AND action LIKE '%api_key%'
     AND timestamp > NOW() - INTERVAL '7 days'
   ORDER BY timestamp DESC;
   ```

**Remediation:**
- Key deleted: Customer regenerates in dashboard
- Key never existed: Customer generates new key
- Wrong organization: Verify customer using correct account

**Fail-Secure Fallback:**
Generate new key for customer via admin API if dashboard inaccessible.

---

#### Scenario 2.1.4: Cognito Token Expired/Invalid

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-3 |
| **Blast Radius** | Single user session |
| **Data Risk** | None |
| **Diagnostic Time** | 5 min |
| **Escalation Threshold** | 15 min |

**Symptoms:**
- Dashboard shows "Session expired"
- API returns 401 with "Token expired"
- Refresh token not working

**Diagnostic Steps:**

1. **Decode JWT to check expiry:**
   ```bash
   # Decode JWT payload (base64)
   echo "{JWT_TOKEN}" | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .
   ```

2. **Check token version:**
   ```sql
   SELECT id, email, token_version
   FROM users
   WHERE email = '{USER_EMAIL}'
     AND organization_id = {ORG_ID};
   ```

**Remediation:**
- Token expired: User re-authenticates (normal flow)
- Token version mismatch: User was force-logged-out, re-authenticate
- Refresh token expired: User must re-login

---

#### Scenario 2.1.5: auth_lookup_api_key() Function Failure (SEV-1)

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-1 |
| **Blast Radius** | ALL TENANTS - Complete SDK authentication failure |
| **Data Risk** | None (fail-secure: all access denied) |
| **Diagnostic Time** | 5 min |
| **Escalation Threshold** | 10 min - Escalate to Greg immediately |

**Symptoms:**
- ALL SDK requests returning 401
- Multiple tenants reporting auth failures simultaneously
- Backend logs show "function auth_lookup_api_key does not exist" or similar

**Forensic Preservation (MANDATORY before remediation):**
```bash
# Capture function state
PGPASSWORD='{DB_PASSWORD}' psql -h {DB_HOST} -U postgres -d owkai_pilot -c "
  SELECT proname, prosrc
  FROM pg_proc
  WHERE proname = 'auth_lookup_api_key';" > /tmp/rls_function_state_$(date +%Y%m%d_%H%M%S).txt

# Capture recent auth errors
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --filter-pattern "auth_lookup" \
  --start-time $(( $(date +%s) - 1800 ))000 \
  --region {REGION} > /tmp/auth_errors_$(date +%Y%m%d_%H%M%S).json
```

**Diagnostic Steps:**

1. **Verify function exists:**
   ```sql
   SELECT proname, proowner::regrole, prosecdef
   FROM pg_proc
   WHERE proname = 'auth_lookup_api_key';
   ```

2. **Test function directly:**
   ```sql
   -- Use a known-good test key
   SELECT * FROM auth_lookup_api_key('owkai_test_xxx');
   ```

3. **Check function permissions:**
   ```sql
   SELECT grantee, privilege_type
   FROM information_schema.routine_privileges
   WHERE routine_name = 'auth_lookup_api_key';
   ```

4. **Check for recent migrations:**
   ```sql
   SELECT version_num, description
   FROM alembic_version;

   -- Check migration history
   SELECT * FROM alembic_version_history
   ORDER BY timestamp DESC LIMIT 5;
   ```

**Remediation:**

| Root Cause | Fix |
|------------|-----|
| Function dropped | Re-run migration that creates function |
| Permissions revoked | Grant EXECUTE to application role |
| Function modified incorrectly | Restore from backup/migration |

**Emergency Restore (if function missing):**
```sql
-- SEC-101: Emergency RLS function restoration
-- Only run if function is confirmed missing
CREATE OR REPLACE FUNCTION auth_lookup_api_key(p_api_key TEXT)
RETURNS TABLE (
    id INTEGER,
    organization_id INTEGER,
    status TEXT
)
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    SELECT ak.id, ak.organization_id, ak.status::TEXT
    FROM api_keys ak
    WHERE ak.key_hash = encode(
        sha256((p_api_key || ak.salt)::bytea), 'hex'
    )
    AND ak.status = 'active'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION auth_lookup_api_key TO app_role;
```

**Fail-Secure Fallback:**
If function cannot be restored within 10 min:
1. **ESCALATE TO GREG IMMEDIATELY** - This is platform-wide outage
2. Consider emergency database restore from snapshot
3. Communicate to all customers via status page

**Verification:**
```bash
# Test SDK auth after fix
curl -s -X GET "https://pilot.owkai.app/api/health" \
  -H "X-API-Key: {TEST_API_KEY}" | jq .

# Verify multiple tenants can authenticate
for key in "{KEY_ORG_1}" "{KEY_ORG_2}"; do
  curl -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: $key" \
    "https://pilot.owkai.app/api/v1/actions"
  echo ""
done
```

**Post-Incident Actions:**
- [ ] Create incident report (SOC 2 CC7.5)
- [ ] Root cause analysis within 24 hours
- [ ] Implement monitoring for function health
- [ ] Review deployment procedures

---

### 2.2 Authorization Failures

#### Scenario 2.2.1: RLS Policy Blocking Legitimate Access

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Single tenant, specific data access |
| **Data Risk** | None (fail-secure) |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 25 min |

**Symptoms:**
- User can login but cannot see their data
- API returns empty results or 403
- "Permission denied" errors

**Diagnostic Steps:**

1. **Verify user's organization:**
   ```sql
   SELECT u.id, u.email, u.organization_id, o.name as org_name
   FROM users u
   JOIN organizations o ON u.organization_id = o.id
   WHERE u.email = '{USER_EMAIL}';
   ```

2. **Check data exists for organization:**
   ```sql
   -- Example: Check agent_actions
   SELECT COUNT(*) as action_count
   FROM agent_actions
   WHERE organization_id = {ORG_ID};
   ```

3. **Test RLS as user:**
   ```sql
   -- Set RLS context and test query
   SET app.current_organization_id = {ORG_ID};
   SELECT * FROM agent_actions LIMIT 5;
   ```

**Remediation:**
- Data belongs to different org: Data migration needed (careful!)
- RLS context not set: Fix application code setting context
- User in wrong org: Update user's organization_id

**Fail-Secure Fallback:**
Do NOT bypass RLS. If legitimate access blocked, fix the context-setting code.

---

#### Scenario 2.2.2: Cross-Tenant Data Leak Detected (SEV-1)

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-1 - CRITICAL SECURITY INCIDENT |
| **Blast Radius** | Multiple tenants, compliance violation |
| **Data Risk** | HIGH - Data exposed to unauthorized tenant |
| **Diagnostic Time** | Immediate containment, then investigation |
| **Escalation Threshold** | IMMEDIATE - Escalate to Greg NOW |

**Symptoms:**
- User sees data from another organization
- Audit log shows cross-org data access
- Customer reports seeing unfamiliar data

**IMMEDIATE CONTAINMENT (before diagnosis):**
```bash
# 1. Capture evidence FIRST
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --start-time $(( $(date +%s) - 7200 ))000 \
  --region {REGION} > /tmp/security_incident_$(date +%Y%m%d_%H%M%S).json

# 2. Consider taking service offline if leak is active
# ONLY with Greg's approval:
# aws ecs update-service --cluster {CLUSTER_NAME} --service {SERVICE_NAME} --desired-count 0
```

**Forensic Preservation (MANDATORY):**
```sql
-- Capture all queries from affected timeframe
SELECT * FROM audit_logs
WHERE timestamp > NOW() - INTERVAL '4 hours'
ORDER BY timestamp DESC;

-- Capture user session data
SELECT * FROM users WHERE id IN ({AFFECTED_USER_IDS});
```

**Diagnostic Steps:**

1. **Identify scope of leak:**
   ```sql
   -- Find queries that returned cross-org data
   SELECT user_id, organization_id, action, resource_id, timestamp
   FROM audit_logs
   WHERE timestamp > '{INCIDENT_START_TIME}'
     AND organization_id != (
       SELECT organization_id FROM users WHERE id = user_id
     )
   ORDER BY timestamp;
   ```

2. **Check RLS policies:**
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, qual
   FROM pg_policies
   WHERE tablename IN ('agent_actions', 'users', 'api_keys');
   ```

3. **Review recent deployments:**
   ```bash
   # Check recent ECS deployments
   aws ecs describe-services \
     --cluster {CLUSTER_NAME} \
     --services {SERVICE_NAME} \
     --region {REGION} \
     --query 'services[0].deployments'
   ```

**Remediation:**
1. Fix RLS policy or application code
2. Rotate any exposed credentials
3. Notify affected customers (legal/compliance requirement)
4. Full incident report within 24 hours

**Fail-Secure Fallback:**
If root cause unclear, keep service offline until RLS verified.

**Regulatory Notification Triggers:**
- GDPR: 72-hour notification if EU data
- SOC 2: Document in incident register
- HIPAA: If PHI involved, breach notification required

---

### 2.3 SDK/Agent Connectivity

#### Scenario 2.3.1: Connection Timeout to API

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-3 (single agent) / SEV-2 (multiple) |
| **Blast Radius** | Depends on scope |
| **Data Risk** | None |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 20 min |

**Symptoms:**
- SDK raises `ConnectionTimeout` or `ReadTimeout`
- Agent cannot submit actions
- Intermittent failures

**Diagnostic Steps:**

1. **Check API health:**
   ```bash
   curl -s -w "\nTime: %{time_total}s\n" https://pilot.owkai.app/api/health
   ```

2. **Check ALB health:**
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT_ID}:targetgroup/{TG_NAME}/{TG_ID} \
     --region {REGION}
   ```

3. **Check ECS task health:**
   ```bash
   aws ecs describe-services \
     --cluster {CLUSTER_NAME} \
     --services {SERVICE_NAME} \
     --region {REGION} \
     --query 'services[0].{running:runningCount,desired:desiredCount}'
   ```

**Remediation:**
- ECS unhealthy: Force new deployment
- ALB issues: Check target group configuration
- Network issues: Check security groups, NACLs

**Fail-Secure Fallback:**
If API unreachable, agent should queue actions locally (SDK v1.2+).

---

#### Scenario 2.3.2: SSL/TLS Certificate Validation Failure

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | All SDK connections |
| **Data Risk** | None (connections refused) |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 20 min |

**Symptoms:**
- SDK raises `SSLError` or `CertificateError`
- "Certificate verify failed"
- All HTTPS connections failing

**Diagnostic Steps:**

1. **Check certificate:**
   ```bash
   echo | openssl s_client -connect pilot.owkai.app:443 2>/dev/null | openssl x509 -noout -dates
   ```

2. **Check certificate chain:**
   ```bash
   curl -vI https://pilot.owkai.app 2>&1 | grep -i "SSL\|certificate"
   ```

**Remediation:**
- Certificate expired: Renew via ACM
- Wrong certificate: Update ALB listener
- Client clock wrong: Customer fixes their system time

---

### 2.4 Kill-Switch Failures

#### Scenario 2.4.1: Agent Not Stopping After BLOCK Command

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-1 |
| **Blast Radius** | Single agent, potential compliance violation |
| **Data Risk** | HIGH - Uncontrolled agent behavior |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 15 min - Escalate to Greg |

**Symptoms:**
- Admin triggered BLOCK in dashboard
- Agent continues operating
- No confirmation of stop received

**Forensic Preservation:**
```bash
# Capture kill-switch message flow
aws sns list-subscriptions-by-topic \
  --topic-arn {SNS_TOPIC_ARN} \
  --region {REGION} > /tmp/sns_subs_$(date +%Y%m%d_%H%M%S).json

aws sqs get-queue-attributes \
  --queue-url https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/org-{ORG_ID}-control \
  --attribute-names All \
  --region {REGION} > /tmp/sqs_state_$(date +%Y%m%d_%H%M%S).json
```

**Diagnostic Steps:**

1. **Verify block command was sent:**
   ```sql
   SELECT * FROM agent_control_commands
   WHERE organization_id = {ORG_ID}
     AND agent_id = '{AGENT_ID}'
   ORDER BY created_at DESC LIMIT 5;
   ```

2. **Check SNS publish:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/SNS \
     --metric-name NumberOfMessagesPublished \
     --dimensions Name=TopicName,Value=ascend-agent-control \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Sum \
     --region {REGION}
   ```

3. **Check SQS queue:**
   ```bash
   aws sqs get-queue-attributes \
     --queue-url https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/org-{ORG_ID}-control \
     --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible \
     --region {REGION}
   ```

4. **Check SDK version:**
   - Kill-switch requires SDK >= 1.1.0
   - Customer may be on older version

**Remediation:**

| Root Cause | Fix |
|------------|-----|
| SNS not publishing | Check IAM permissions, republish message |
| SQS not receiving | Check SNS subscription, recreate if needed |
| SDK not polling | Customer must upgrade SDK |
| SDK polling wrong queue | Verify organization ID in SDK config |

**Fail-Secure Fallback - EMERGENCY:**
```sql
-- Revoke agent's API key immediately
UPDATE api_keys
SET status = 'revoked',
    revoked_at = NOW(),
    revoked_reason = 'Emergency: Kill-switch failure - SEC-101'
WHERE organization_id = {ORG_ID}
  AND id = (
    SELECT api_key_id FROM registered_agents
    WHERE agent_id = '{AGENT_ID}' AND organization_id = {ORG_ID}
  );
```

**Verification:**
```bash
# Verify agent can no longer authenticate
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: {AGENT_API_KEY}" \
  "https://pilot.owkai.app/api/health"
# Should return 401
```

---

#### Scenario 2.4.2: SNS Message Not Published

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Kill-switch for affected org |
| **Data Risk** | Medium - Agent may continue |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 15 min |

**Diagnostic Steps:**

1. **Check ECS task role permissions:**
   ```bash
   aws iam get-role-policy \
     --role-name {ECS_TASK_ROLE} \
     --policy-name sns-publish-policy \
     --region {REGION}
   ```

2. **Check SNS topic exists:**
   ```bash
   aws sns get-topic-attributes \
     --topic-arn {SNS_TOPIC_ARN} \
     --region {REGION}
   ```

3. **Check backend logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name {LOG_GROUP} \
     --filter-pattern "SNS\|publish\|agent-control" \
     --start-time $(( $(date +%s) - 3600 ))000 \
     --region {REGION}
   ```

**Remediation:**
- Missing permissions: Update IAM policy
- Topic deleted: Recreate SNS topic and subscriptions
- Backend error: Fix code, redeploy

---

#### Scenario 2.4.3: SQS Queue Not Receiving Messages

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Single organization |
| **Data Risk** | Medium |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 15 min |

**Diagnostic Steps:**

1. **Verify subscription exists:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn {SNS_TOPIC_ARN} \
     --region {REGION} \
     --query "Subscriptions[?Endpoint=='arn:aws:sqs:{REGION}:{ACCOUNT_ID}:org-{ORG_ID}-control']"
   ```

2. **Check SQS permissions:**
   ```bash
   aws sqs get-queue-attributes \
     --queue-url https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/org-{ORG_ID}-control \
     --attribute-names Policy \
     --region {REGION}
   ```

**Remediation:**
- Missing subscription: Create SNS → SQS subscription
- Permission denied: Update SQS policy to allow SNS

---

### 2.5 Workflow/Action Processing

#### Scenario 2.5.1: Actions Stuck in pending_approval

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | Single tenant workflows |
| **Data Risk** | None |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 25 min |

**Symptoms:**
- Actions show `status = 'pending_approval'` for extended time
- No workflow execution created
- Approvers not seeing actions in dashboard

**Diagnostic Steps:**

1. **Check action exists:**
   ```sql
   SELECT id, agent_id, status, risk_score, created_at, updated_at
   FROM agent_actions
   WHERE organization_id = {ORG_ID}
     AND status = 'pending_approval'
   ORDER BY created_at DESC LIMIT 10;
   ```

2. **Check workflow execution:**
   ```sql
   SELECT we.id, we.workflow_id, we.status, we.created_at
   FROM workflow_executions we
   JOIN agent_actions aa ON we.action_id = aa.id
   WHERE aa.organization_id = {ORG_ID}
     AND aa.id = {ACTION_ID};
   ```

3. **Check agent thresholds:**
   ```sql
   SELECT agent_id, auto_approve_below, requires_approval_above, max_risk_threshold
   FROM registered_agents
   WHERE organization_id = {ORG_ID}
     AND agent_id = '{AGENT_ID}';
   ```

4. **Check backend logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name {LOG_GROUP} \
     --filter-pattern "workflow\|action\|{ACTION_ID}" \
     --start-time $(( $(date +%s) - 3600 ))000 \
     --region {REGION}
   ```

**Remediation:**
- Workflow not created: Check workflow service, restart if needed
- Threshold misconfigured: Adjust agent thresholds
- Processing error: Check logs, fix code, reprocess action

**Fail-Secure Fallback:**
Actions remain pending (safe state). Manual approval can unblock.

---

#### Scenario 2.5.2: Approval Notifications Not Sent

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-3 |
| **Blast Radius** | Single tenant |
| **Data Risk** | None |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 30 min |

**Symptoms:**
- Actions pending but approvers not notified
- Email/Slack notifications not arriving
- Workflow execution shows notification_sent = false

**Diagnostic Steps:**

1. **Check notification configuration:**
   ```sql
   SELECT * FROM notification_settings
   WHERE organization_id = {ORG_ID};
   ```

2. **Check SES delivery:**
   ```bash
   aws ses get-send-statistics --region {REGION}
   ```

3. **Check Slack webhook:**
   ```sql
   SELECT slack_webhook_url, slack_enabled
   FROM organizations
   WHERE id = {ORG_ID};
   ```

**Remediation:**
- SES bounces: Check email validity, SES reputation
- Slack webhook invalid: Customer updates webhook URL
- Notifications disabled: Enable in settings

---

### 2.6 Database Connectivity

#### Scenario 2.6.1: RDS Connection Refused

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-1 |
| **Blast Radius** | ALL TENANTS - Platform down |
| **Data Risk** | None (service unavailable) |
| **Diagnostic Time** | 5 min |
| **Escalation Threshold** | 10 min - Escalate to Greg |

**Symptoms:**
- All API calls return 500
- Backend logs show "connection refused" or timeout
- Health check failing

**Forensic Preservation:**
```bash
# Capture current state before remediation
aws rds describe-db-instances \
  --db-instance-identifier {DB_INSTANCE} \
  --region {REGION} > /tmp/rds_state_$(date +%Y%m%d_%H%M%S).json

aws rds describe-events \
  --source-identifier {DB_INSTANCE} \
  --source-type db-instance \
  --duration 60 \
  --region {REGION} > /tmp/rds_events_$(date +%Y%m%d_%H%M%S).json
```

**Diagnostic Steps:**

1. **Check RDS status:**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier {DB_INSTANCE} \
     --region {REGION} \
     --query 'DBInstances[0].{status:DBInstanceStatus,az:AvailabilityZone,multiAZ:MultiAZ}'
   ```

2. **Check RDS events:**
   ```bash
   aws rds describe-events \
     --source-identifier {DB_INSTANCE} \
     --source-type db-instance \
     --duration 60 \
     --region {REGION}
   ```

3. **Check security groups:**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier {DB_INSTANCE} \
     --region {REGION} \
     --query 'DBInstances[0].VpcSecurityGroups'
   ```

**Remediation:**

| Root Cause | Fix |
|------------|-----|
| RDS stopped | Start instance (takes 2-5 min) |
| Security group changed | Add ECS security group to RDS inbound |
| Multi-AZ failover | Wait for automatic recovery (~60s) |
| Storage full | Increase storage, enable autoscaling |
| Max connections | Increase `max_connections` parameter |

**Fail-Secure Fallback:**
Service remains unavailable (safe). No data at risk.

**Verification:**
```bash
# Test database connection
PGPASSWORD='{DB_PASSWORD}' psql -h {DB_HOST} -U postgres -d owkai_pilot -c "SELECT 1;"

# Test API health
curl -s https://pilot.owkai.app/api/health | jq .
```

---

#### Scenario 2.6.2: Connection Pool Exhausted

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | All tenants, intermittent |
| **Data Risk** | None |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 20 min |

**Symptoms:**
- Intermittent 500 errors
- "Too many connections" in logs
- Slow response times

**Diagnostic Steps:**

1. **Check current connections:**
   ```sql
   SELECT count(*) as total_connections,
          state,
          usename
   FROM pg_stat_activity
   GROUP BY state, usename
   ORDER BY total_connections DESC;
   ```

2. **Check max connections:**
   ```sql
   SHOW max_connections;
   ```

3. **Find connection leaks:**
   ```sql
   SELECT pid, usename, application_name, client_addr,
          state, query_start, NOW() - query_start as duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC;
   ```

**Remediation:**
- Increase pool size in application config
- Fix connection leaks in code
- Increase RDS `max_connections` parameter
- Add connection pooler (PgBouncer) if needed

---

### 2.7 Performance Degradation

#### Scenario 2.7.1: API Latency > 5 Seconds

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-2 |
| **Blast Radius** | All tenants |
| **Data Risk** | None |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 25 min |

**Symptoms:**
- Dashboard loading slowly
- SDK timeouts increasing
- Users complaining about performance

**Diagnostic Steps:**

1. **Check ECS metrics:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/ECS \
     --metric-name CPUUtilization \
     --dimensions Name=ClusterName,Value={CLUSTER_NAME} Name=ServiceName,Value={SERVICE_NAME} \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Average \
     --region {REGION}
   ```

2. **Check RDS performance:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/RDS \
     --metric-name CPUUtilization \
     --dimensions Name=DBInstanceIdentifier,Value={DB_INSTANCE} \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Average \
     --region {REGION}
   ```

3. **Find slow queries:**
   ```sql
   SELECT query, calls, mean_time, total_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

**Remediation:**
- High CPU: Scale ECS tasks, optimize code
- Slow queries: Add indexes, optimize queries
- Memory pressure: Increase task memory
- Network: Check ALB, VPC configuration

---

### 2.8 Notification Failures

#### Scenario 2.8.1: SES Emails Not Delivered

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-3 |
| **Blast Radius** | Email notifications only |
| **Data Risk** | None |
| **Diagnostic Time** | 15 min |
| **Escalation Threshold** | 30 min |

**Symptoms:**
- Approval notifications not arriving via email
- Password reset emails not received
- SES bounce notifications

**Diagnostic Steps:**

1. **Check SES sending stats:**
   ```bash
   aws ses get-send-statistics --region {REGION}
   ```

2. **Check SES reputation:**
   ```bash
   aws ses get-account --region {REGION}
   ```

3. **Check bounce/complaint rates:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/SES \
     --metric-name Bounce \
     --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 3600 \
     --statistics Sum \
     --region {REGION}
   ```

**Remediation:**
- High bounce rate: Clean email list, verify addresses
- Reputation issues: Review SES best practices
- Quota exceeded: Request limit increase

---

#### Scenario 2.8.2: Slack/Teams Webhook Failing

| Attribute | Value |
|-----------|-------|
| **Severity** | SEV-3 |
| **Blast Radius** | Single tenant notifications |
| **Data Risk** | None |
| **Diagnostic Time** | 10 min |
| **Escalation Threshold** | 20 min |

**Symptoms:**
- Slack/Teams notifications not appearing
- Webhook returns error in logs
- Customer reports missing alerts

**Diagnostic Steps:**

1. **Check webhook configuration:**
   ```sql
   SELECT slack_webhook_url, teams_webhook_url,
          slack_enabled, teams_enabled
   FROM organizations
   WHERE id = {ORG_ID};
   ```

2. **Test webhook:**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"text":"Test notification from ASCEND"}' \
     "{WEBHOOK_URL}"
   ```

3. **Check backend logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name {LOG_GROUP} \
     --filter-pattern "webhook\|slack\|teams" \
     --start-time $(( $(date +%s) - 3600 ))000 \
     --region {REGION}
   ```

**Remediation:**
- Invalid webhook: Customer regenerates in Slack/Teams
- Network error: Check outbound connectivity
- Rate limited: Reduce notification frequency

---

## 3. AWS Service Troubleshooting

### 3.1 ECS Fargate Health

```bash
# List running tasks
aws ecs list-tasks \
  --cluster {CLUSTER_NAME} \
  --service-name {SERVICE_NAME} \
  --region {REGION}

# Describe task
aws ecs describe-tasks \
  --cluster {CLUSTER_NAME} \
  --tasks {TASK_ARN} \
  --region {REGION}

# Force new deployment
aws ecs update-service \
  --cluster {CLUSTER_NAME} \
  --service {SERVICE_NAME} \
  --force-new-deployment \
  --region {REGION}

# View task logs
aws logs get-log-events \
  --log-group-name {LOG_GROUP} \
  --log-stream-name "ecs/{SERVICE_NAME}/{TASK_ID}" \
  --region {REGION}
```

### 3.2 RDS PostgreSQL

```bash
# Instance status
aws rds describe-db-instances \
  --db-instance-identifier {DB_INSTANCE} \
  --region {REGION}

# Recent events
aws rds describe-events \
  --source-identifier {DB_INSTANCE} \
  --source-type db-instance \
  --duration 1440 \
  --region {REGION}

# Reboot instance (if needed)
aws rds reboot-db-instance \
  --db-instance-identifier {DB_INSTANCE} \
  --region {REGION}
```

### 3.3 Cognito User Pools

```bash
# Get user
aws cognito-idp admin-get-user \
  --user-pool-id {COGNITO_POOL_ID} \
  --username "{EMAIL}" \
  --region {REGION}

# Disable user
aws cognito-idp admin-disable-user \
  --user-pool-id {COGNITO_POOL_ID} \
  --username "{EMAIL}" \
  --region {REGION}

# Enable user
aws cognito-idp admin-enable-user \
  --user-pool-id {COGNITO_POOL_ID} \
  --username "{EMAIL}" \
  --region {REGION}

# Reset password
aws cognito-idp admin-reset-user-password \
  --user-pool-id {COGNITO_POOL_ID} \
  --username "{EMAIL}" \
  --region {REGION}
```

### 3.4 SES Email

```bash
# Sending statistics
aws ses get-send-statistics --region {REGION}

# Account status
aws ses get-account --region {REGION}

# Send test email
aws ses send-email \
  --from "noreply@ascendowkai.com" \
  --to "{TEST_EMAIL}" \
  --subject "ASCEND Test Email" \
  --text "This is a test email from ASCEND troubleshooting." \
  --region {REGION}
```

### 3.5 SNS/SQS Kill-Switch Path

```bash
# List SNS subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn {SNS_TOPIC_ARN} \
  --region {REGION}

# Publish test message
aws sns publish \
  --topic-arn {SNS_TOPIC_ARN} \
  --message '{"type":"test","organization_id":{ORG_ID}}' \
  --region {REGION}

# Check SQS queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/org-{ORG_ID}-control \
  --attribute-names All \
  --region {REGION}

# Receive messages (for testing)
aws sqs receive-message \
  --queue-url https://sqs.{REGION}.amazonaws.com/{ACCOUNT_ID}/org-{ORG_ID}-control \
  --max-number-of-messages 1 \
  --region {REGION}
```

### 3.6 Secrets Manager

```bash
# List secrets
aws secretsmanager list-secrets --region {REGION}

# Get secret value
aws secretsmanager get-secret-value \
  --secret-id {SECRET_NAME} \
  --region {REGION}

# Rotate secret
aws secretsmanager rotate-secret \
  --secret-id {SECRET_NAME} \
  --region {REGION}
```

### 3.7 ALB/Target Groups

```bash
# Describe load balancer
aws elbv2 describe-load-balancers \
  --names {ALB_NAME} \
  --region {REGION}

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn {TARGET_GROUP_ARN} \
  --region {REGION}

# Check listener rules
aws elbv2 describe-rules \
  --listener-arn {LISTENER_ARN} \
  --region {REGION}
```

---

## 4. Multi-Tenant Isolation Verification

### 4.1 RLS Verification Queries

```sql
-- SEC-101: Verify RLS policies exist
SELECT schemaname, tablename, policyname, permissive, roles, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename;

-- Verify RLS is enabled on critical tables
SELECT relname, relrowsecurity, relforcerowsecurity
FROM pg_class
WHERE relname IN ('users', 'agent_actions', 'api_keys', 'organizations', 'registered_agents');

-- Test RLS context
SET app.current_organization_id = {ORG_ID};
SELECT current_setting('app.current_organization_id');
```

### 4.2 Cross-Tenant Leak Detection

```sql
-- SEC-101: Find any queries that may have leaked data
-- Run periodically as compliance check

-- Check if any user accessed data outside their org
SELECT al.user_id, u.organization_id as user_org,
       al.resource_organization_id as accessed_org,
       al.action, al.timestamp
FROM audit_logs al
JOIN users u ON al.user_id = u.id
WHERE al.resource_organization_id IS NOT NULL
  AND al.resource_organization_id != u.organization_id
  AND al.timestamp > NOW() - INTERVAL '24 hours';

-- Check agent_actions for org mismatches
SELECT aa.id, aa.organization_id, ra.organization_id as agent_org
FROM agent_actions aa
JOIN registered_agents ra ON aa.agent_id = ra.agent_id
WHERE aa.organization_id != ra.organization_id;
```

### 4.3 Tenant-Specific Log Filtering

```bash
# Filter logs for specific organization
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --filter-pattern "\"organization_id\":{ORG_ID}" \
  --start-time $(( $(date +%s) - 3600 ))000 \
  --region {REGION}

# Filter by user email domain (for tenant)
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --filter-pattern "\"@customer-domain.com\"" \
  --start-time $(( $(date +%s) - 3600 ))000 \
  --region {REGION}
```

---

## 5. Compliance & Audit

### 5.1 Evidence Collection Procedures

For any SEV-1 or SEV-2 incident, collect the following evidence **BEFORE** remediation:

```bash
# Create incident evidence directory
INCIDENT_ID="INC-$(date +%Y%m%d-%H%M%S)"
mkdir -p /tmp/${INCIDENT_ID}

# 1. Capture system state
aws ecs describe-services \
  --cluster {CLUSTER_NAME} \
  --services {SERVICE_NAME} \
  --region {REGION} > /tmp/${INCIDENT_ID}/ecs_state.json

aws rds describe-db-instances \
  --db-instance-identifier {DB_INSTANCE} \
  --region {REGION} > /tmp/${INCIDENT_ID}/rds_state.json

# 2. Capture relevant logs
aws logs filter-log-events \
  --log-group-name {LOG_GROUP} \
  --start-time $(( $(date +%s) - 7200 ))000 \
  --region {REGION} > /tmp/${INCIDENT_ID}/backend_logs.json

# 3. Capture database state (if applicable)
PGPASSWORD='{DB_PASSWORD}' psql -h {DB_HOST} -U postgres -d owkai_pilot -c "
  SELECT * FROM audit_logs
  WHERE timestamp > NOW() - INTERVAL '4 hours'
  ORDER BY timestamp DESC;" > /tmp/${INCIDENT_ID}/audit_logs.txt

# 4. Create evidence manifest
echo "Incident: ${INCIDENT_ID}" > /tmp/${INCIDENT_ID}/manifest.txt
echo "Collected: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /tmp/${INCIDENT_ID}/manifest.txt
echo "Collector: $(whoami)" >> /tmp/${INCIDENT_ID}/manifest.txt

# 5. Archive evidence
tar -czf /tmp/${INCIDENT_ID}.tar.gz -C /tmp ${INCIDENT_ID}
```

### 5.2 Incident Documentation Requirements

Every SEV-1 and SEV-2 incident requires:

1. **Incident Report** (within 24 hours):
   - Incident ID and severity
   - Timeline of events
   - Root cause analysis
   - Remediation steps taken
   - Evidence collected
   - Lessons learned

2. **Audit Log Entry**:
   ```sql
   INSERT INTO audit_logs (
     organization_id, user_id, action, resource_type,
     resource_id, details, timestamp
   ) VALUES (
     0, -- System/platform level
     NULL, -- Automated
     'security_incident',
     'platform',
     '{INCIDENT_ID}',
     '{"severity": "SEV-1", "type": "...", "resolution": "..."}',
     NOW()
   );
   ```

3. **SOC 2 Register Entry** (if applicable):
   - Document in security incident register
   - Track remediation completion
   - Schedule post-incident review

### 5.3 Regulatory Notification Triggers

| Regulation | Trigger | Notification Window | Contact |
|------------|---------|---------------------|---------|
| **GDPR** | Personal data breach affecting EU residents | 72 hours | DPO / Supervisory Authority |
| **HIPAA** | PHI breach (if applicable) | 60 days | HHS OCR |
| **SOC 2** | Control failure | Document in register | Auditor at next review |
| **Customer Contract** | SLA breach | Per contract | Customer success team |

### 5.4 Audit Log Preservation

```sql
-- SEC-101: Audit log retention policy
-- Logs must be retained for compliance periods:
-- - SOC 2: 1 year minimum
-- - GDPR: Duration of processing + 3 years
-- - HIPAA: 6 years

-- Never delete audit logs without archival
-- Archive procedure:
-- 1. Export to S3 (encrypted)
-- 2. Verify export integrity
-- 3. Update retention metadata
-- 4. Only then delete from database

-- Check audit log retention
SELECT
  DATE_TRUNC('month', timestamp) as month,
  COUNT(*) as log_count
FROM audit_logs
GROUP BY month
ORDER BY month DESC;
```

---

## 6. Appendix

### 6.1 Common Error Codes Reference

| HTTP Code | Meaning | Common Cause |
|-----------|---------|--------------|
| 400 | Bad Request | Invalid request payload |
| 401 | Unauthorized | Invalid/missing API key or token |
| 403 | Forbidden | RLS policy denial, insufficient permissions |
| 404 | Not Found | Resource doesn't exist or not accessible to tenant |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Application error, database issue |
| 502 | Bad Gateway | ALB cannot reach backend |
| 503 | Service Unavailable | ECS tasks unhealthy |
| 504 | Gateway Timeout | Backend timeout (>30s) |

### 6.2 Database Schema Quick Reference

```
organizations (id, name, status, settings)
    ├── users (id, email, organization_id, cognito_sub, is_org_admin)
    ├── api_keys (id, organization_id, key_hash, salt, status)
    ├── registered_agents (id, organization_id, agent_id, thresholds)
    ├── agent_actions (id, organization_id, agent_id, status, risk_score)
    ├── workflows (id, organization_id, name, steps)
    ├── workflow_executions (id, workflow_id, action_id, status)
    ├── smart_rules (id, organization_id, conditions, actions)
    └── audit_logs (id, organization_id, action, timestamp)
```

### 6.3 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | December 2025 | Ascend Engineering | Initial release (SEC-101) |

---

*This runbook is maintained by the Ascend Engineering Team. For updates or corrections, submit via the standard documentation process.*
