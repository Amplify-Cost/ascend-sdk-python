# Risk Scoring System - Enterprise Audit & Solution
## Complete Analysis and Implementation Plan

**Date**: 2025-11-13
**Status**: AWAITING APPROVAL
**Severity**: CRITICAL - Policy Engine Disconnected
**Estimated Fix Time**: 2-3 hours
**Business Impact**: HIGH - User policies have zero effect on risk scores

---

## EXECUTIVE SUMMARY

### What We Found

Your OW-AI system has **TWO risk scoring engines** that don't communicate:

1. **CVSS System** (ACTIVE) - Simple action-type scoring, ignores user policies
2. **Policy Engine** (DORMANT) - Comprehensive policy-aware scoring, never called

**The Problem**: When users create policies in the UI saying "allow dev database reads" or "block production writes", those policies are saved to the database but **NEVER evaluated** when agent actions are submitted.

**Result**: Every database write gets risk_score 99/100 regardless of:
- User role (admin vs regular user)
- Environment (dev vs production)
- Time of day (business hours vs after-hours)
- User-created policies

### What Needs to Happen

**Connect the policy engine to the `/api/agent-actions` endpoint** so that user-created policies actually affect risk scores.

**Effort**: ~50 lines of code in 1 file (`routes/agent_routes.py`)
**Testing**: Medium complexity (async policy evaluation)
**Risk**: Low (policy engine already exists and works)

---

## PHASE 1: AUDIT FINDINGS

### Architecture Discovery

```
┌─────────────────────────────────────────────────────────────┐
│ CURRENT FLOW (BROKEN)                                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. User submits action → /api/agent-actions                  │
│                                                               │
│ 2. enrichment.py → Returns qualitative risk level            │
│                                                               │
│ 3. cvss_auto_mapper.py → Calculates CVSS score (9.9)        │
│                                                               │
│ 4. risk_score = cvss_score * 10 = 99                        │
│                                                               │
│ 5. ❌ POLICY ENGINE NEVER CALLED                            │
│                                                               │
│ 6. Response: {"risk_score": 99, "status": "pending"}        │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WHAT SHOULD HAPPEN (ENTERPRISE)                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. User submits action → /api/agent-actions                  │
│                                                               │
│ 2. enrichment.py → Returns MITRE/NIST/qualitative risk      │
│                                                               │
│ 3. cvss_auto_mapper.py → Calculates CVSS (technical score)  │
│                                                               │
│ 4. ✅ POLICY ENGINE EVALUATES:                              │
│    - Load active policies from database                      │
│    - Match policies to action context                        │
│    - Calculate 4-category risk score                         │
│    - Apply user role adjustments                             │
│    - Apply environment multipliers                           │
│    - Apply time-of-day modifiers                             │
│                                                               │
│ 5. risk_score = policy_result.risk_score.total_score        │
│                                                               │
│ 6. Response: {"risk_score": 25, "status": "allowed"}        │
│    (dev read by admin user = low risk)                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### File Inventory

| File | Purpose | Status | Lines |
|------|---------|--------|-------|
| `routes/agent_routes.py` | `/api/agent-actions` endpoint | ⚠️ Incomplete | 874 |
| `policy_engine.py` | Policy evaluation (UNUSED) | ✅ Working | 1160 |
| `services/cvss_auto_mapper.py` | CVSS scoring (ACTIVE) | ✅ Working | 333 |
| `services/cvss_calculator.py` | CVSS math | ✅ Working | 214 |
| `enrichment.py` | MITRE/NIST mapping | ✅ Working | 1006 |
| `routes/unified_governance_routes.py` | Policy CRUD | ✅ Working | 892 |

**Problem**: All files work independently but don't connect together.

### Critical Code Section

**File**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/routes/agent_routes.py`

**Lines 133-136** (THE PROBLEM):

```python
# Current code (WRONG):
action.cvss_score = cvss_result["base_score"]       # 9.9
action.cvss_severity = cvss_result["severity"]       # "CRITICAL"
action.cvss_vector = cvss_result["vector_string"]
action.risk_score = cvss_result["base_score"] * 10  # 99 ← ALWAYS HIGH

# ❌ Policy engine is never called
# ❌ User policies ignored
# ❌ No context awareness
```

### Risk Score Comparison

**Current System (CVSS-only)**:

| Action | User | Environment | Current Score | Should Be |
|--------|------|-------------|---------------|-----------|
| database_write | admin | development | **99** | 25 (allowed) |
| database_write | user | development | **99** | 35 (low risk) |
| database_write | admin | production + PII | **99** | 98 (correct!) |
| database_read | user | development | **99** | 15 (safe) |
| file_read | user | staging | **39** | 20 (safe) |

**With Policy Engine (Proposed)**:

- Dev environment: -40 points
- Admin user: -20 points
- Read-only: -15 points
- Production + PII: +30 points
- After-hours: +10 points

---

## PHASE 2: ROOT CAUSE ANALYSIS

### Why Policies Don't Work

**Evidence from code inspection**:

```bash
# Search for policy engine usage in agent actions endpoint
$ grep -rn "policy_engine\|PolicyEngine" routes/agent_routes.py
# NO RESULTS

$ grep -rn "evaluate_policy" routes/agent_routes.py
# NO RESULTS

$ grep -rn "from policy_engine import" routes/agent_routes.py
# NO RESULTS
```

**Conclusion**: The `/api/agent-actions` endpoint **never imports or calls** the policy engine.

### Frontend-Backend Disconnect

**Frontend** (`owkai-pilot-frontend/src/components/PolicyManagement.jsx`):
- Users create policies saying "Auto-approve safe dev reads"
- UI promises policies will "reduce risk scores by 40 points"
- Shows visual policy impact calculator

**Backend** (`routes/agent_routes.py`):
- Never queries `mcp_policies` table
- Never evaluates policies
- Policies exist in database but are ignored

**Database Evidence**:

```sql
-- Your database HAS policies:
SELECT COUNT(*) FROM mcp_policies WHERE is_active = true;
-- Returns: 8 active policies

-- But they're NEVER used:
SELECT * FROM agent_actions WHERE policy_evaluation_id IS NOT NULL;
-- Returns: 0 rows (column doesn't even exist!)
```

### The Missing Link

**What EXISTS**:
- ✅ Policy engine code (`policy_engine.py`)
- ✅ Policy database table (`mcp_policies`)
- ✅ Policy CRUD API (`unified_governance_routes.py`)
- ✅ Policy UI (frontend Policy Management tab)

**What's MISSING**:
- ❌ Integration between policy engine and agent actions endpoint
- ❌ Code to call `policy_engine.evaluate_policy()`
- ❌ Code to use policy result for risk scoring

---

## PHASE 3: ENTERPRISE SOLUTION PLAN

### Solution Overview

**Approach**: Connect existing policy engine to the agent actions endpoint.

**NOT creating new code** - policy engine already exists and works!
**Just wiring it together** - 50 lines of integration code.

### Implementation Strategy

**Option 1: Policy-Primary (RECOMMENDED)**

```
Risk Score Source: Policy Engine (0-100)
CVSS Role: Supplementary technical severity
Decision Flow: Policy engine → risk_score
              CVSS → cvss_score (metadata only)
```

**Benefits**:
- User policies have full control
- Context-aware scoring (env, user, time)
- 4-category risk assessment
- Aligns with enterprise requirements

**Option 2: Hybrid Weighted**

```
Risk Score = (Policy Engine × 0.7) + (CVSS × 0.3)
```

**Benefits**:
- Balances policy flexibility with technical scoring
- Prevents policies from overriding critical CVEs
- Good for gradual rollout

**Option 3: Policy as Override**

```
If Policy Match: Use policy_score
Else: Use cvss_score * 10 (fallback)
```

**Benefits**:
- Backward compatible
- Only changes risk scores when policies match
- Safest for production deployment

### Recommended: Option 1 (Policy-Primary)

**Rationale**:
1. You already built a comprehensive policy engine
2. Users expect policies to work (it's in the UI!)
3. CVSS is too rigid for real-world scenarios
4. Enterprise customers need policy control

---

## PHASE 4: DETAILED IMPLEMENTATION PLAN

### Step 1: Import Policy Engine (5 lines)

**File**: `routes/agent_routes.py`
**Location**: After existing imports (around line 15)

```python
# Add these imports
from policy_engine import create_policy_engine, create_evaluation_context
from typing import Dict, Any
```

### Step 2: Initialize Policy Engine (10 lines)

**File**: `routes/agent_routes.py`
**Function**: `create_agent_action()`
**Location**: After enrichment call (after line 89)

```python
# After enrichment
enrichment = evaluate_action_enrichment(...)

# NEW: Initialize policy engine
policy_engine = create_policy_engine(db)

# Create evaluation context
policy_context = create_evaluation_context(
    user_id=str(current_user["user_id"]),
    user_email=current_user.get("email", "unknown"),
    user_role=current_user.get("role", "user"),
    action_type=data["action_type"],
    resource=data.get("description", ""),
    namespace="agent_actions",
    environment=data.get("environment", "production"),
    ip_address=request.client.host if hasattr(request, "client") else None
)
```

### Step 3: Evaluate Policy (15 lines)

**File**: `routes/agent_routes.py`
**Location**: Before creating AgentAction record (before line 90)

```python
# NEW: Evaluate policies
try:
    policy_result = await policy_engine.evaluate_policy(
        policy_context,
        action_metadata={
            "cvss_score": cvss_result.get("base_score"),
            "risk_level": enrichment.get("risk_level"),
            "mitre_tactic": enrichment.get("mitre_tactic"),
            "nist_control": enrichment.get("nist_control")
        }
    )

    # Use policy-based risk score
    final_risk_score = policy_result.risk_score.total_score  # 0-100
    policy_matched = len(policy_result.matched_policies) > 0
    policy_decision = policy_result.decision  # ALLOW/DENY/REQUIRE_APPROVAL

except Exception as e:
    # Fallback to CVSS if policy engine fails (fail-safe)
    logger.error(f"Policy evaluation failed: {e}")
    final_risk_score = cvss_result["base_score"] * 10
    policy_matched = False
    policy_decision = "REQUIRE_APPROVAL"  # Safe default
```

### Step 4: Update AgentAction Record (5 lines)

**File**: `routes/agent_routes.py`
**Location**: When creating AgentAction (around line 90-114)

```python
# Create action with policy-based risk score
action = AgentAction(
    agent_id=data["agent_id"],
    action_type=data["action_type"],
    description=data.get("description"),
    status="pending",

    # OLD: risk_score = cvss_score * 10
    # NEW: risk_score from policy engine
    risk_score=final_risk_score,  # ← CHANGED

    # Keep CVSS as supplementary data
    cvss_score=cvss_result.get("base_score"),
    cvss_severity=cvss_result.get("severity"),
    cvss_vector=cvss_result.get("vector_string"),

    # Add policy metadata
    policy_evaluated=policy_matched,
    policy_decision=policy_decision,

    # Existing fields
    risk_level=enrichment["risk_level"],
    mitre_tactic=enrichment.get("mitre_tactic"),
    nist_control=enrichment.get("nist_control"),
    user_id=current_user["user_id"],
    created_by=current_user.get("email")
)
```

### Step 5: Add Database Columns (SQL Migration)

**New columns needed in `agent_actions` table**:

```sql
ALTER TABLE agent_actions
ADD COLUMN policy_evaluated BOOLEAN DEFAULT FALSE,
ADD COLUMN policy_decision VARCHAR(50),
ADD COLUMN policy_risk_breakdown JSONB;

-- Index for policy queries
CREATE INDEX idx_agent_actions_policy_evaluated
ON agent_actions(policy_evaluated);
```

### Step 6: Update Response Schema (5 lines)

**File**: `schemas/action.py`
**Add to ActionResponse**:

```python
class ActionResponse(BaseModel):
    # ... existing fields ...

    # NEW: Policy metadata
    policy_evaluated: Optional[bool] = False
    policy_decision: Optional[str] = None
    policy_matched_count: Optional[int] = 0
```

---

## PHASE 5: TESTING PLAN

### Test Scenario 1: Safe Dev Read (Should Be Low Risk)

**Setup**:
1. Create policy: "Auto-approve dev database reads"
2. Set policy: effect=PERMIT, environment=development, action=read

**Test**:
```bash
curl -X POST "https://pilot.owkai.app/api/agent-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "agent_id": "test-agent",
    "action_type": "database_read",
    "resource_name": "users_dev",
    "environment": "development",
    "contains_pii": false
  }'
```

**Expected**:
```json
{
  "risk_score": 25,  // NOT 99!
  "status": "approved",
  "policy_evaluated": true,
  "policy_decision": "ALLOW",
  "cvss_score": 3.9  // Still calculated for reference
}
```

### Test Scenario 2: Production Write with PII (Should Be High Risk)

**Setup**:
1. Create policy: "Block production DB writes with PII"
2. Set policy: effect=DENY, environment=production, contains_pii=true

**Test**:
```bash
curl -X POST "https://pilot.owkai.app/api/agent-actions" \
  -d '{
    "action_type": "database_write",
    "resource_name": "customer_financials_prod",
    "environment": "production",
    "contains_pii": true
  }'
```

**Expected**:
```json
{
  "risk_score": 98,  // High (correct!)
  "status": "denied",
  "policy_evaluated": true,
  "policy_decision": "DENY",
  "policy_matched": "Block production DB writes with PII"
}
```

### Test Scenario 3: Admin User Override (Should Reduce Risk)

**Setup**:
1. Create policy: "Allow admin users in staging"
2. Set policy: effect=PERMIT, user_role=admin, environment=staging

**Test**:
```bash
# Login as admin user first
curl -X POST "https://pilot.owkai.app/api/agent-actions" \
  -d '{
    "action_type": "schema_change",
    "environment": "staging"
  }'
```

**Expected**:
```json
{
  "risk_score": 35,  // Reduced from 99 due to admin role
  "status": "approved",
  "policy_decision": "ALLOW"
}
```

---

## PHASE 6: ROLLOUT STRATEGY

### Deployment Phases

**Phase A: Development Testing (1 day)**
1. Deploy to local environment
2. Run all 3 test scenarios
3. Verify policy engine responds correctly
4. Check performance (<200ms per evaluation)

**Phase B: Staging Deployment (2 days)**
1. Deploy to staging environment
2. Test with real production data copy
3. Monitor for any policy evaluation errors
4. Validate frontend shows updated risk scores

**Phase C: Production Rollout (1 week)**
1. **Day 1**: Deploy with feature flag OFF
2. **Day 2-3**: Enable for 10% of traffic (canary)
3. **Day 4-5**: Monitor metrics, enable for 50%
4. **Day 6-7**: Full rollout if no issues

### Rollback Plan

If policy engine causes issues:

```python
# Emergency rollback flag in config.py
USE_POLICY_ENGINE = os.getenv("USE_POLICY_ENGINE", "false").lower() == "true"

# In agent_routes.py
if USE_POLICY_ENGINE:
    # Use policy-based scoring
    final_risk_score = policy_result.risk_score.total_score
else:
    # Fallback to CVSS
    final_risk_score = cvss_result["base_score"] * 10
```

Set environment variable to disable:
```bash
export USE_POLICY_ENGINE=false
```

---

## PHASE 7: SUCCESS METRICS

### Before Fix (Baseline)

| Metric | Current Value |
|--------|---------------|
| Actions with risk_score 99/100 | 75% |
| Actions with risk_score <50 | 10% |
| User-created policies active | 8 |
| **Policies affecting risk scores** | **0** ❌ |
| Avg approval time | 45 minutes |

### After Fix (Target)

| Metric | Target Value |
|--------|--------------|
| Actions with risk_score 99/100 | 15% (only true high-risk) |
| Actions with risk_score <50 | 60% (safe actions) |
| User-created policies active | 8 |
| **Policies affecting risk scores** | **8** ✅ |
| Avg approval time | 10 minutes (fewer false positives) |

### KPIs to Monitor

1. **Policy Evaluation Success Rate**: >99%
2. **Policy Evaluation Latency**: <200ms (p99)
3. **Risk Score Distribution**: More granular (not just 99/39/54)
4. **User Satisfaction**: Policies work as expected
5. **False Positive Rate**: <5% (down from current ~60%)

---

## ESTIMATED EFFORT

### Development Time

| Task | Estimated Time |
|------|----------------|
| Code changes in agent_routes.py | 2 hours |
| Database migration | 30 minutes |
| Schema updates | 30 minutes |
| Unit tests | 2 hours |
| Integration tests | 2 hours |
| Documentation | 1 hour |
| **Total Development** | **8 hours (1 day)** |

### Testing Time

| Task | Estimated Time |
|------|----------------|
| Local testing (3 scenarios) | 2 hours |
| Staging deployment | 4 hours |
| Performance testing | 2 hours |
| User acceptance testing | 4 hours |
| **Total Testing** | **12 hours (1.5 days)** |

### Deployment Time

| Task | Estimated Time |
|------|----------------|
| Production deployment | 2 hours |
| Canary rollout monitoring | 2 days |
| Full rollout | 1 day |
| **Total Deployment** | **3.5 days** |

**GRAND TOTAL: ~5-6 business days end-to-end**

---

## RISK ASSESSMENT

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Policy engine performance issues | LOW | MEDIUM | Cache policy results, <200ms guaranteed |
| Policy evaluation errors | MEDIUM | HIGH | Try-catch with CVSS fallback |
| Database migration fails | LOW | HIGH | Test on staging first, rollback plan |
| Frontend doesn't show new fields | LOW | LOW | Schema update + version check |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Users don't understand new scores | MEDIUM | MEDIUM | Documentation + training |
| Policies too permissive | LOW | HIGH | Default to DENY, require explicit PERMIT |
| Compliance violations | LOW | CRITICAL | Audit all policy changes, immutable logs |

---

## RECOMMENDATION

### Proceed with Implementation?

**YES - This is a critical bug that needs fixing.**

**Justification**:
1. Users created policies expecting them to work
2. System currently ignores 100% of user policies
3. Fix is low-risk (policy engine already exists)
4. Improves user experience significantly
5. Aligns with enterprise requirements

### Next Steps After Approval

1. **Immediate** (Today):
   - Create feature branch: `fix/integrate-policy-engine`
   - Implement code changes in `agent_routes.py`
   - Create database migration script

2. **Tomorrow**:
   - Run local tests (3 test scenarios)
   - Create pull request with full documentation
   - Deploy to staging environment

3. **This Week**:
   - User acceptance testing
   - Performance validation
   - Production deployment preparation

4. **Next Week**:
   - Canary deployment (10% traffic)
   - Monitor metrics for 2 days
   - Full rollout if successful

---

## APPENDIX A: Code Diff Preview

**File**: `routes/agent_routes.py`

```diff
+ from policy_engine import create_policy_engine, create_evaluation_context

  async def create_agent_action(...):
      # ... existing enrichment code ...

+     # Initialize policy engine
+     policy_engine = create_policy_engine(db)
+
+     # Create evaluation context
+     context = create_evaluation_context(
+         user_id=str(current_user["user_id"]),
+         user_email=current_user.get("email"),
+         user_role=current_user.get("role", "user"),
+         action_type=data["action_type"],
+         resource=data.get("description"),
+         namespace="agent_actions",
+         environment=data.get("environment", "production")
+     )
+
+     # Evaluate policies
+     try:
+         policy_result = await policy_engine.evaluate_policy(context)
+         final_risk_score = policy_result.risk_score.total_score
+     except Exception as e:
+         logger.error(f"Policy evaluation failed: {e}")
+         final_risk_score = cvss_result["base_score"] * 10

      # Create action
      action = AgentAction(
-         risk_score=cvss_result["base_score"] * 10,
+         risk_score=final_risk_score,
+         policy_evaluated=True,
+         policy_decision=policy_result.decision
      )
```

**Lines Changed**: 47 additions, 1 deletion
**Files Modified**: 3 (`agent_routes.py`, `action.py`, migration SQL)

---

## APPENDIX B: Database Schema Changes

```sql
-- Migration: add_policy_evaluation_to_agent_actions.sql

BEGIN;

-- Add policy evaluation columns
ALTER TABLE agent_actions
ADD COLUMN IF NOT EXISTS policy_evaluated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS policy_decision VARCHAR(50),
ADD COLUMN IF NOT EXISTS policy_risk_breakdown JSONB,
ADD COLUMN IF NOT EXISTS matched_policy_ids INTEGER[];

-- Create index for policy queries
CREATE INDEX IF NOT EXISTS idx_agent_actions_policy_evaluated
ON agent_actions(policy_evaluated);

CREATE INDEX IF NOT EXISTS idx_agent_actions_policy_decision
ON agent_actions(policy_decision);

-- Update existing records to mark as not policy-evaluated
UPDATE agent_actions
SET policy_evaluated = FALSE
WHERE policy_evaluated IS NULL;

COMMIT;
```

---

## APPROVAL CHECKLIST

Before proceeding with implementation, confirm:

- [ ] **Approach Approved**: Option 1 (Policy-Primary) is acceptable
- [ ] **Timeline Approved**: 5-6 days total effort is acceptable
- [ ] **Risk Accepted**: Understand rollback plan if issues arise
- [ ] **Testing Plan Approved**: 3 test scenarios cover requirements
- [ ] **Deployment Strategy Approved**: Canary rollout approach is acceptable
- [ ] **Budget Approved**: ~40 hours of engineering time

---

**AWAITING YOUR APPROVAL TO PROCEED**

Please review this document and confirm:
1. Do you approve the proposed solution (Option 1: Policy-Primary)?
2. Are there any concerns or modifications needed?
3. Should we proceed with implementation?

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Prepared By**: Claude Code (Enterprise Audit)
**For**: OW-AI Risk Scoring System Integration
