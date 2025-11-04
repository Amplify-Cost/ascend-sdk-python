# Authorization Center Analytics Audit - Test Plan & Execution
**Date:** 2025-11-04
**Auditor:** OW-KAI Engineer
**Objective:** Verify Analytics section uses ONLY real data from policy_evaluations table

---

## Test Scenarios

### Test 1: Analytics Endpoint Returns Real Database Data
**Endpoint:** `GET /api/governance/policies/engine-metrics`
**Expected:** Metrics come from `policy_evaluations` table, not random.randint()
**Success Criteria:**
- Same metrics returned on multiple calls (no randomness)
- Metrics match database query results
- Response includes actual policy evaluation counts

### Test 2: Policy Enforcement Logs to Database
**Endpoint:** `POST /api/governance/policies/enforce`
**Expected:** Each policy evaluation creates a record in `policy_evaluations`
**Success Criteria:**
- Row count increases after each enforcement
- Record contains correct decision, action, resource
- Evaluation time is measured and stored

### Test 3: Policy-Specific Effectiveness Metrics
**Endpoint:** `GET /api/governance/policies/engine-metrics` (per-policy data)
**Expected:** Individual policy statistics from database
**Success Criteria:**
- Evaluation counts per policy are accurate
- Success rate calculated from real denials/approvals
- Average response time from actual measurements

### Test 4: Frontend Analytics Display
**Component:** `PolicyAnalytics.jsx`
**Expected:** Frontend displays database-backed metrics
**Success Criteria:**
- Metrics refresh shows real-time data
- No random number generation in frontend
- Charts/graphs based on API response

---

## Pre-Test Database State

### Current Policy Evaluations Count
```sql
SELECT COUNT(*) FROM policy_evaluations;
-- Result: 7 evaluations
```

### Current Breakdown
```sql
SELECT
  decision,
  COUNT(*) as count
FROM policy_evaluations
GROUP BY decision;
-- ALLOW: 7
-- DENY: 0
-- REQUIRE_APPROVAL: 0
```

### Active Policies Count
```sql
SELECT COUNT(*) FROM enterprise_policies WHERE status = 'active';
-- Result: 0 policies
```

---

## Test Execution Log

### Test 1: Analytics Endpoint (Real Data Verification)

#### Step 1.1: Call endpoint twice and compare responses
**Command:**
```bash
curl -X GET "http://localhost:8000/api/governance/policies/engine-metrics" \
  -H "Authorization: Bearer $TOKEN" | jq '.metrics'
```

**Expected Behavior:**
- Both calls should return identical metrics
- No random variation between calls
- Metrics should match database counts (7 total evaluations, 7 allows, 0 denials)

#### Step 1.2: Verify metrics match database
**Database Query:**
```sql
SELECT
  COUNT(*) as total_evaluations,
  COUNT(CASE WHEN decision = 'DENY' THEN 1 END) as denials,
  COUNT(CASE WHEN decision = 'ALLOW' THEN 1 END) as allows,
  COUNT(CASE WHEN decision = 'REQUIRE_APPROVAL' THEN 1 END) as approvals
FROM policy_evaluations
WHERE evaluated_at >= NOW() - INTERVAL '24 hours';
```

**Expected Match:**
- API `total_evaluations` = Database `total_evaluations`
- API `denials` = Database `denials`
- API `approvals_required` = Database `approvals`

---

### Test 2: Policy Enforcement Logging

#### Step 2.1: Get baseline count
```sql
SELECT COUNT(*) FROM policy_evaluations;
-- Current: 7
```

#### Step 2.2: Create a test policy
```bash
curl -X POST "http://localhost:8000/api/governance/create-policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_name": "Test Financial Controls",
    "description": "Deny high-value transactions",
    "effect": "deny",
    "actions": ["database:write", "database:delete"],
    "resources": ["arn:aws:rds:prod/*"],
    "conditions": {"amount": {"gt": 10000}},
    "priority": 100
  }'
```

#### Step 2.3: Trigger policy enforcement
```bash
curl -X POST "http://localhost:8000/api/governance/policies/enforce" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "ai_agent:test_bot",
    "action_type": "database:write",
    "target": "arn:aws:rds:prod/transactions",
    "context": {"amount": 50000, "user": "admin@owkai.com"},
    "risk_score": 75
  }'
```

#### Step 2.4: Verify database logged the evaluation
```sql
SELECT COUNT(*) FROM policy_evaluations;
-- Expected: 8 (increased by 1)

SELECT
  id,
  principal,
  action,
  resource,
  decision,
  evaluation_time_ms,
  evaluated_at
FROM policy_evaluations
ORDER BY evaluated_at DESC
LIMIT 1;
-- Expected: New record with agent_id, action_type, decision
```

---

### Test 3: Policy-Specific Effectiveness

#### Step 3.1: Create multiple evaluations for a policy
```bash
# Enforce policy 3 times with different contexts
for i in {1..3}; do
  curl -X POST "http://localhost:8000/api/governance/policies/enforce" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"agent_id\": \"ai_agent:test_bot_$i\",
      \"action_type\": \"database:write\",
      \"target\": \"arn:aws:rds:prod/test_$i\",
      \"context\": {\"amount\": $((10000 + i * 1000))},
      \"risk_score\": 50
    }"
  sleep 1
done
```

#### Step 3.2: Query policy-specific metrics
```sql
SELECT
  policy_id,
  COUNT(*) as evaluations,
  COUNT(CASE WHEN decision = 'DENY' THEN 1 END) as denials,
  COUNT(CASE WHEN decision = 'ALLOW' THEN 1 END) as allows,
  AVG(evaluation_time_ms) as avg_time_ms
FROM policy_evaluations
WHERE policy_id IS NOT NULL
GROUP BY policy_id;
```

#### Step 3.3: Call analytics endpoint and verify per-policy data
```bash
curl -X GET "http://localhost:8000/api/governance/policies/engine-metrics" \
  -H "Authorization: Bearer $TOKEN" | jq '.metrics.policy_performance'
```

**Expected:**
- Policy performance array shows real evaluation counts
- Success rates calculated from actual denials/approvals
- Average response times from database measurements

---

## Success Criteria Summary

### ✅ PASS if:
1. **No Random Data:** Metrics are deterministic (same results on repeated calls)
2. **Database-Backed:** All metrics match database query results
3. **Real-Time Updates:** Metrics update immediately after new evaluations
4. **Audit Trail:** Every enforcement creates a database record
5. **Performance Tracking:** Evaluation times are measured and stored

### ❌ FAIL if:
1. Metrics change randomly between calls
2. Metrics don't match database counts
3. Policy enforcement doesn't log to database
4. Frontend shows hardcoded/static values
5. Any use of `random.randint()` in analytics code path

---

## Code Evidence Requirements

For each test, document:
1. **API Request:** Full curl command with headers
2. **API Response:** JSON response body
3. **Database Query:** SQL query and results
4. **Code Path:** File and line numbers executed
5. **Comparison:** Side-by-side API vs Database values

---

## Post-Test Analysis

### What to Verify:
- [ ] PolicyAnalyticsService is actually being called
- [ ] No fallback to random data generation
- [ ] Database queries are performant (indexed correctly)
- [ ] Error handling gracefully degrades (returns zeros, not crashes)
- [ ] Audit trail is immutable (no UPDATE/DELETE on evaluations)

### Known Gaps (Not Yet Implemented):
- Compliance mapping still uses hardcoded data
- Risk category breakdowns not yet database-backed
- Historical trend data needs time-series aggregation
- Policy effectiveness score calculation needs refinement

---

## Execution Instructions

1. Start backend: `cd ow-ai-backend && uvicorn main:app --reload`
2. Get auth token: `export TOKEN=$(curl -X POST "http://localhost:8000/login" -d '{"email":"admin@owkai.com","password":"admin"}' | jq -r .access_token)`
3. Run each test section in order
4. Document results in AUDIT_EXECUTION_RESULTS.md
5. Take screenshots of frontend analytics dashboard
6. Export database queries to CSV for evidence

---

**Prepared By:** OW-KAI Engineer Auditor
**Review Required:** Enterprise Security Team
**Deployment Gate:** All tests must pass before production deployment
