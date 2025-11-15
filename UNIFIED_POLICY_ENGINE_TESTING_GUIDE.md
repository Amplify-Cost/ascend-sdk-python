# 🏢 UNIFIED POLICY ENGINE - Enterprise Testing Guide

**Version:** 1.0
**Task Definition:** 449 (Backend), 281 (Frontend)
**Deployment Date:** November 15, 2025
**Status:** ✅ PRODUCTION READY

---

## 📋 Executive Summary

This guide provides comprehensive testing procedures for the **Unified Policy Engine** (Option 1 Architecture). Both agent actions and MCP server actions are now evaluated using the same `EnterpriseRealTimePolicyEngine` for consistent, enterprise-grade governance.

### Key Fixes Deployed:

1. **Agent Action Endpoint** - Made `tool_name` optional with intelligent defaults
2. **API Schema** - Added policy evaluation fields to response (`policy_evaluated`, `policy_decision`, `policy_risk_score`, `risk_fusion_formula`)
3. **Backward Compatibility** - Zero breaking changes for existing integrations

---

## 🎯 Testing Objectives

### Primary Goals:
✅ Verify agent actions are evaluated by unified policy engine
✅ Verify MCP actions are evaluated by same policy engine
✅ Confirm policy decisions display correctly in frontend
✅ Validate 80/20 hybrid risk scoring for agents
✅ Validate 100% policy scoring for MCP actions
✅ Ensure no functionality regression

### Success Criteria:
- Agent action creation returns `policy_evaluated: true`
- Policy decisions are one of: ALLOW, DENY, REQUIRE_APPROVAL, ESCALATE, CONDITIONAL
- Policy risk scores are 0-100
- Risk fusion formulas show calculation transparency
- Frontend PolicyDecisionBadge displays correctly
- All existing features continue to work

---

## 🔐 Prerequisites

### 1. Authentication Token

```bash
# Get JWT token
curl -s -X POST "https://pilot.owkai.app/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@owkai.com&password=YOUR_REDACTED-CREDENTIAL" | python3 -m json.tool

# Save the token
export TOKEN="<paste_access_token_here>"
```

### 2. Verify Backend is Running

```bash
# Check ECS service health
aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service --region us-east-2 --query 'services[0].{Status:status,TaskDef:taskDefinition,Running:runningCount}' --output json

# Expected: Status=ACTIVE, TaskDef=449, Running=1
```

### 3. Verify Frontend is Accessible

```bash
curl -s "https://pilot.owkai.app/" | grep "<title>"

# Expected: <title>OW-AI Dashboard</title>
```

---

## 🧪 TEST SUITE 1: Agent Action with Unified Policy Engine

### Test 1.1: Create Low-Risk Agent Action (Should ALLOW)

```bash
curl -s -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-unified-policy-001",
    "action_type": "database_read",
    "description": "Reading test data from development database"
  }' | python3 -m json.tool
```

**Expected Response Fields:**
```json
{
  "id": <number>,
  "agent_id": "test-unified-policy-001",
  "action_type": "database_read",
  "tool_name": "inferred_database_read",  // ✅ Auto-generated
  "policy_evaluated": true,                // ✅ Unified engine evaluated
  "policy_decision": "ALLOW",              // ✅ Low risk = ALLOW
  "policy_risk_score": 20-40,              // ✅ Low policy risk
  "risk_fusion_formula": "hybrid_80_20_cvss_X_policy_Y_fused_Z",  // ✅ Shows calculation
  "risk_score": <float>,                   // ✅ Hybrid risk
  "status": "pending_approval"
}
```

**Validation Checklist:**
- [ ] `policy_evaluated` is `true`
- [ ] `policy_decision` is present (not null)
- [ ] `policy_risk_score` is between 0-100
- [ ] `risk_fusion_formula` contains "hybrid_80_20"
- [ ] `tool_name` was auto-generated as `inferred_database_read`
- [ ] Response returned in < 2 seconds

---

### Test 1.2: Create High-Risk Agent Action (Should REQUIRE_APPROVAL)

```bash
curl -s -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-unified-policy-002",
    "action_type": "database_delete",
    "description": "Deleting production database table with customer PII"
  }' | python3 -m json.tool
```

**Expected Response Fields:**
```json
{
  "id": <number>,
  "action_type": "database_delete",
  "policy_evaluated": true,
  "policy_decision": "REQUIRE_APPROVAL" or "DENY" or "ESCALATE",  // ✅ High risk decision
  "policy_risk_score": 70-100,             // ✅ High policy risk
  "risk_fusion_formula": "hybrid_80_20_cvss_X_policy_Y_fused_Z",
  "risk_score": 70-100,                    // ✅ High overall risk
  "status": "pending_approval"
}
```

**Validation Checklist:**
- [ ] `policy_evaluated` is `true`
- [ ] `policy_decision` is REQUIRE_APPROVAL, DENY, or ESCALATE
- [ ] `policy_risk_score` is >= 70
- [ ] `risk_score` is >= 70
- [ ] `status` is `pending_approval`

---

### Test 1.3: Create Action WITH Explicit tool_name (Backward Compatibility)

```bash
curl -s -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "legacy-integration-test",
    "action_type": "api_call",
    "description": "Calling external payment API",
    "tool_name": "stripe_payment_api"
  }' | python3 -m json.tool
```

**Expected Response Fields:**
```json
{
  "tool_name": "stripe_payment_api",       // ✅ Uses provided tool_name (not inferred)
  "policy_evaluated": true,
  "policy_decision": <string>,
  "policy_risk_score": <number>
}
```

**Validation Checklist:**
- [ ] `tool_name` is exactly "stripe_payment_api" (not inferred)
- [ ] Policy evaluation still occurred
- [ ] No errors or warnings

---

## 🧪 TEST SUITE 2: MCP Action with Unified Policy Engine

### Test 2.1: Verify MCP Governance Endpoint Path

```bash
# Test correct endpoint path
curl -s -X POST "https://pilot.owkai.app/api/governance/mcp-governance/evaluate-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "mcp-test-001",
    "namespace": "filesystem",
    "verb": "read_file",
    "resource": "/home/user/test.txt",
    "user_email": "admin@owkai.com",
    "user_role": "admin",
    "decision": "approved"
  }' | python3 -m json.tool
```

**Expected Response:**
```json
{
  "success": true,
  "policy_evaluation": {
    "evaluated": true,
    "decision": "ALLOW",
    "risk_score": 10-30,                   // ✅ Low risk read
    "category_scores": {
      "financial": <number>,
      "data_sensitivity": <number>,
      "security_impact": <number>,
      "compliance_risk": <number>
    },
    "matched_policies": [...]
  }
}
```

**Validation Checklist:**
- [ ] Endpoint returns 200 OK (not 404)
- [ ] `policy_evaluation.evaluated` is `true`
- [ ] `policy_evaluation.decision` is present
- [ ] `policy_evaluation.risk_score` is 0-100
- [ ] `category_scores` shows 4 categories

---

### Test 2.2: High-Risk MCP Action (File Write to System Path)

```bash
curl -s -X POST "https://pilot.owkai.app/api/governance/mcp-governance/evaluate-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action_id": "mcp-test-002",
    "namespace": "filesystem",
    "verb": "write_file",
    "resource": "/etc/passwd",
    "user_email": "admin@owkai.com",
    "user_role": "admin",
    "decision": "pending"
  }' | python3 -m json.tool
```

**Expected Response:**
```json
{
  "success": true,
  "policy_evaluation": {
    "evaluated": true,
    "decision": "DENY" or "REQUIRE_APPROVAL" or "ESCALATE",  // ✅ High risk
    "risk_score": 80-100,                  // ✅ Critical system file
    "matched_policies": [...]
  }
}
```

**Validation Checklist:**
- [ ] Policy decision is DENY, REQUIRE_APPROVAL, or ESCALATE
- [ ] Risk score is >= 80
- [ ] Evaluation completed successfully

---

## 🧪 TEST SUITE 3: Unified Queue Verification

### Test 3.1: Verify Both Action Types Appear in Queue

```bash
# Get all recent actions
curl -s "https://pilot.owkai.app/api/agent-activity" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Total actions: {len(data)}')
print(f'Actions with policy_evaluated=true: {sum(1 for a in data if a.get(\"policy_evaluated\"))}')
print(f'Sample policy decisions: {[a.get(\"policy_decision\") for a in data[:5] if a.get(\"policy_decision\")]}')
"
```

**Expected Output:**
```
Total actions: 50+
Actions with policy_evaluated=true: 20+
Sample policy decisions: ['ALLOW', 'REQUIRE_APPROVAL', 'DENY', ...]
```

**Validation Checklist:**
- [ ] Queue returns actions
- [ ] Some actions have `policy_evaluated=true`
- [ ] Policy decisions are properly formatted (not "PolicyDecision.ALLOW")

---

### Test 3.2: Filter by Policy Decision

```bash
# Get only actions requiring approval
curl -s "https://pilot.owkai.app/api/agent-activity?policy_decision=REQUIRE_APPROVAL" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Actions requiring approval: {len(data)}')
for action in data[:3]:
    print(f'  - ID {action[\"id\"]}: {action.get(\"policy_decision\")} (risk: {action.get(\"policy_risk_score\")})')
"
```

**Expected Output:**
```
Actions requiring approval: 10+
  - ID 318: REQUIRE_APPROVAL (risk: 66)
  - ID 317: REQUIRE_APPROVAL (risk: 66)
  - ID 316: REQUIRE_APPROVAL (risk: 66)
```

**Validation Checklist:**
- [ ] Filter returns only actions with specified decision
- [ ] Policy risk scores are present
- [ ] Response is fast (< 1 second)

---

## 🧪 TEST SUITE 4: Frontend UI Verification

### Test 4.1: PolicyDecisionBadge Display

**Manual Test Steps:**

1. **Open Browser:** https://pilot.owkai.app
2. **Login:** admin@owkai.com / [your password]
3. **Navigate:** Authorization Center → Activity Tab
4. **Create Test Action:**
   - Use the simulator or API to create a test action
   - Wait 2-3 seconds for page to refresh

**Expected UI Elements:**

```
┌─────────────────────────────────────────────────────┐
│ Action #319                                          │
│ ┌─────────┐ ┌─────────────┐ ┌──────────────────┐  │
│ │ RISK 75 │ │ ⏰ APPROVAL │ │ pending_approval │  │
│ └─────────┘ └─────────────┘ └──────────────────┘  │
│                                                      │
│ Description: Database write to production...        │
└─────────────────────────────────────────────────────┘
```

**Color-Coded Badges:**
- ✅ **ALLOW** - Green background, green text
- ❌ **DENY** - Red background, red text
- ⏰ **REQUIRE_APPROVAL** - Yellow background, yellow text
- ⬆️ **ESCALATE** - Orange background, orange text
- 🔀 **CONDITIONAL** - Blue background, blue text

**Validation Checklist:**
- [ ] PolicyDecisionBadge appears next to action status
- [ ] Badge shows correct icon and text
- [ ] Color coding matches decision type
- [ ] Both agent and MCP actions show policy badges
- [ ] No JavaScript errors in console

---

### Test 4.2: Policy Details Card (Expanded View)

**Manual Test Steps:**

1. Click on an action to expand details
2. Look for "Policy Evaluation Results" section

**Expected Display:**

```
┌─────────────────────────────────────────────────────┐
│ 🏢 Policy Evaluation Results         ⏰ APPROVAL   │
├─────────────────────────────────────────────────────┤
│ Policy Risk Score:                           66/100 │
│ Risk Fusion:              80% CVSS + 20% Policy     │
│ Evaluated By:      EnterpriseRealTimePolicyEngine   │
│ Action Source:                      🤖 Agent Action │
│                                                      │
│ ✅ Both agent and MCP actions use the same unified │
│    policy engine for consistent governance          │
└─────────────────────────────────────────────────────┘
```

**Validation Checklist:**
- [ ] Policy details card displays
- [ ] Risk score shows correctly
- [ ] Risk fusion formula is present
- [ ] Enterprise branding is visible
- [ ] Card layout is clean and professional

---

## 🧪 TEST SUITE 5: Database Verification

### Test 5.1: Verify Agent Actions Have Policy Data

```bash
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT
  id,
  agent_id,
  action_type,
  policy_evaluated,
  policy_decision,
  policy_risk_score,
  LEFT(risk_fusion_formula, 50) as formula_preview,
  created_at
FROM agent_actions
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND policy_evaluated = true
ORDER BY id DESC
LIMIT 5;
"
```

**Expected Output:**
```
 id  | agent_id              | action_type    | policy_evaluated | policy_decision    | policy_risk_score | formula_preview              | created_at
-----+-----------------------+----------------+------------------+--------------------+-------------------+------------------------------+------------
 320 | test-unified-policy-  | database_read  | t                | ALLOW              | 30                | hybrid_80_20_cvss_3.5_poli.. | 2025-11-15...
 319 | test-unified-policy-  | database_delete| t                | REQUIRE_APPROVAL   | 85                | hybrid_80_20_cvss_8.5_poli.. | 2025-11-15...
```

**Validation Checklist:**
- [ ] Recent actions exist (within last hour)
- [ ] `policy_evaluated` is `t` (true)
- [ ] `policy_decision` is not null
- [ ] `policy_risk_score` is 0-100
- [ ] `risk_fusion_formula` contains calculation details

---

### Test 5.2: Verify MCP Actions Have Policy Data

```bash
PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL' psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 \
  -U owkai_admin \
  -d owkai_pilot \
  -c "
SELECT
  id,
  namespace,
  verb,
  resource,
  policy_evaluated,
  policy_decision,
  policy_risk_score,
  created_at
FROM mcp_actions
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND policy_evaluated = true
ORDER BY id DESC
LIMIT 5;
"
```

**Expected Output:**
```
 id | namespace   | verb       | resource         | policy_evaluated | policy_decision    | policy_risk_score | created_at
----+-------------+------------+------------------+------------------+--------------------+-------------------+------------
 5  | filesystem  | write_file | /etc/passwd      | t                | DENY               | 95                | 2025-11-15...
 4  | filesystem  | read_file  | /home/user/test  | t                | ALLOW              | 20                | 2025-11-15...
```

**Validation Checklist:**
- [ ] MCP actions exist with policy evaluation
- [ ] Policy fields are populated
- [ ] High-risk actions have high policy risk scores
- [ ] Decisions match risk levels

---

## 🧪 TEST SUITE 6: Performance & Monitoring

### Test 6.1: Policy Evaluation Performance

```bash
# Check CloudWatch logs for evaluation time
aws logs tail /ecs/owkai-pilot-backend --since 10m --region us-east-2 --format short | grep "Policy evaluated" | tail -10
```

**Expected Log Entries:**
```
2025-11-15 21:50:15 ✅ Policy evaluated: Action 320 -> decision=ALLOW, policy_risk=30, time=125.32ms
2025-11-15 21:50:22 ✅ Policy evaluated: Action 321 -> decision=REQUIRE_APPROVAL, policy_risk=85, time=142.18ms
```

**Validation Checklist:**
- [ ] Evaluation time is < 200ms per action
- [ ] All evaluations complete successfully
- [ ] No timeout errors
- [ ] Policy decisions are logged

---

### Test 6.2: Error Rate Monitoring

```bash
# Check for errors in policy evaluation
aws logs tail /ecs/owkai-pilot-backend --since 10m --region us-east-2 --format short | grep -E "ERROR|CRITICAL|policy.*failed" | tail -20
```

**Expected:** No policy evaluation errors (other errors may exist from other services)

**Validation Checklist:**
- [ ] No "Policy evaluation failed" errors
- [ ] No "UnifiedPolicyEvaluationService" errors
- [ ] No timeout errors

---

## 📊 Test Results Summary Template

Use this template to document your test results:

```markdown
## Test Results - [Date]

### Environment:
- Backend Task Definition: 449
- Frontend Task Definition: 281
- Tester: [Your Name]
- Test Duration: [Start] - [End]

### Test Suite 1: Agent Actions
- Test 1.1 (Low Risk): ✅ PASS / ❌ FAIL
- Test 1.2 (High Risk): ✅ PASS / ❌ FAIL
- Test 1.3 (Backward Compat): ✅ PASS / ❌ FAIL

### Test Suite 2: MCP Actions
- Test 2.1 (Endpoint Path): ✅ PASS / ❌ FAIL
- Test 2.2 (High Risk): ✅ PASS / ❌ FAIL

### Test Suite 3: Unified Queue
- Test 3.1 (Both Types): ✅ PASS / ❌ FAIL
- Test 3.2 (Filtering): ✅ PASS / ❌ FAIL

### Test Suite 4: Frontend UI
- Test 4.1 (Badge Display): ✅ PASS / ❌ FAIL
- Test 4.2 (Details Card): ✅ PASS / ❌ FAIL

### Test Suite 5: Database
- Test 5.1 (Agent Data): ✅ PASS / ❌ FAIL
- Test 5.2 (MCP Data): ✅ PASS / ❌ FAIL

### Test Suite 6: Performance
- Test 6.1 (Eval Time): ✅ PASS / ❌ FAIL
- Test 6.2 (Error Rate): ✅ PASS / ❌ FAIL

### Overall Result: ✅ PASS / ⚠️ PARTIAL / ❌ FAIL

### Issues Found:
1. [Issue description]
2. [Issue description]

### Recommendations:
1. [Recommendation]
2. [Recommendation]
```

---

## 🚨 Troubleshooting

### Issue 1: "Missing required fields: tool_name"

**Cause:** Using old backend version (Task Def < 449)
**Solution:**
```bash
# Check task definition version
aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service --region us-east-2 --query 'services[0].taskDefinition'

# Expected: arn:aws:ecs:us-east-2:110948415588:task-definition/owkai-pilot-backend:449
```

---

### Issue 2: "404 Not Found" on MCP Endpoint

**Cause:** Wrong endpoint path
**Solution:** Use `/api/governance/mcp-governance/evaluate-action` (not `/api/mcp-governance/evaluate-action`)

---

### Issue 3: policy_decision Shows "PolicyDecision.ALLOW"

**Cause:** Backend not serializing enum to string
**Solution:** This should be fixed in Task Def 449. If issue persists, check logs for enum serialization errors.

---

### Issue 4: PolicyDecisionBadge Not Displaying

**Cause:** Frontend not updated or cache issue
**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R)
3. Verify frontend Task Def is 281

---

### Issue 5: No Actions Created in Last Hour

**Cause:** Tests not run yet or clock skew
**Solution:**
```bash
# Create test action first, then query
curl -s -X POST "https://pilot.owkai.app/api/agent-action" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"agent_id":"test","action_type":"test","description":"test"}'

# Wait 5 seconds, then query database again
```

---

## ✅ Sign-Off Checklist

### Before Production Approval:

- [ ] All Test Suite 1 tests pass (Agent Actions)
- [ ] All Test Suite 2 tests pass (MCP Actions)
- [ ] All Test Suite 3 tests pass (Unified Queue)
- [ ] All Test Suite 4 tests pass (Frontend UI)
- [ ] All Test Suite 5 tests pass (Database)
- [ ] All Test Suite 6 tests pass (Performance)
- [ ] No critical errors in logs
- [ ] Policy evaluation time < 200ms
- [ ] Zero breaking changes confirmed
- [ ] Documentation reviewed and accurate

### Approvals:

- **Technical Lead:** ________________ Date: _______
- **Security Review:** ________________ Date: _______
- **Product Owner:** ________________ Date: _______

---

## 📞 Support & Escalation

### For Technical Issues:
- Check CloudWatch logs: `/ecs/owkai-pilot-backend`
- Check ECS service health
- Review deployment logs in GitHub Actions

### For Policy Evaluation Issues:
- Check `UnifiedPolicyEvaluationService` logs
- Verify `EnterpriseRealTimePolicyEngine` is loaded
- Check `mcp_policies` table has active policies

### Escalation Path:
1. Review this testing guide
2. Check troubleshooting section
3. Review deployment documentation
4. Contact technical lead

---

**Document Version:** 1.0
**Last Updated:** November 15, 2025
**Next Review:** December 15, 2025

🏢 Enterprise Authorization Center - OW-kai Platform
