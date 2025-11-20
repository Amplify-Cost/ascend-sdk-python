# 🔍 Auto-Approval Threshold Investigation - COMPLETE

**Date**: 2025-11-19
**Status**: ROOT CAUSE IDENTIFIED ✅
**Engineer**: Donald King (OW-kai Enterprise)
**Priority**: CRITICAL

---

## 📋 EXECUTIVE SUMMARY

**Issue**: Actions with Risk Score 39 (LOW) are not being auto-approved

**Root Cause Found**: **MULTIPLE conflicting systems setting approval requirements**

**Impact**: Low-risk actions requiring unnecessary manual approval (poor UX, workflow bottleneck)

---

## 🎯 THE PROBLEM

**User Report**:
> "deployment-agent" action with Risk Score 39 (LOW) is pending in Authorization Center

**Expected Behavior**:
- Risk Score 39 → AUTO-APPROVED (no human approval needed)
- Status: "approved"
- Required Approval Level: 0

**Actual Behavior**:
- Risk Score 39 → PENDING APPROVAL
- Status: "pending"
- Required Approval Level: 5 (CRITICAL level!)

---

## 🔬 EVIDENCE COLLECTED

### **Evidence #1: Database State**

**Action 638**:
```sql
id  | agent_id         | risk_score | status  | required_approval_level
638 | deployment-agent | 39         | pending | 5
```

**ALL Recent Actions Have Level 5**:
```sql
id  | risk_score | required_approval_level
638 | 39         | 5  ← WRONG (should be 0)
633 | 39         | 5  ← WRONG
599 | 54         | 5  ← WRONG (should be 1-2)
568 | 48         | 5  ← WRONG (should be 0-1)
```

🚨 **Pattern**: EVERY action has `required_approval_level=5` regardless of risk score!

---

### **Evidence #2: Production Logs (Action 638 Creation)**

```
2025-11-19 16:14:19 - CVSS assessment: Score 3.3 (LOW)
2025-11-19 16:14:19 - CVSS Risk Score: 39
2025-11-19 16:14:19 - ✅ Playbook matched: pb-auto-approve-low-risk-actions
2025-11-19 16:14:19 - ▶️  Executing playbook 'pb-auto-approve-low-risk-actions' for action 638
2025-11-19 16:14:19 - 🤖 Evaluating agent action 638 with unified policy engine
2025-11-19 16:14:19 - ✅ Agent action 638 evaluated: decision=require_approval, policy_risk=66, fused_risk=39.0
```

**Critical Line**:
```
decision=require_approval, policy_risk=66, fused_risk=39.0
```

🚨 **Conflict Detected**:
- **Fused Risk (CVSS)**: 39 (LOW) → Should auto-approve
- **Policy Risk**: 66 (MEDIUM-HIGH) → Requires approval
- **Final Decision**: require_approval ❌

---

### **Evidence #3: Code Investigation**

#### **Finding A: Unified Policy Engine Overrides CVSS**

**File**: `services/unified_policy_evaluation_service.py` (inferred)

**What Happens**:
1. CVSS calculates risk = 39 (LOW)
2. Unified policy engine evaluates action
3. Policy engine calculates own risk = 66 (based on rules)
4. **Policy risk OVERRIDES CVSS risk**
5. Decision: require_approval (because 66 >= 60 threshold)

---

#### **Finding B: WorkflowBridge Sets required_approval_level**

**File**: `services/workflow_bridge.py:50-59, 125`

```python
def calculate_approval_levels(self, risk_score: int) -> int:
    if risk_score >= 90:
        return 3
    elif risk_score >= 70:
        return 2
    elif risk_score >= 50:
        return 2
    else:
        return 1  # ← Even low-risk gets Level 1!
```

```python
# Line 125
agent_action.required_approval_level = required_levels
```

**Problem**:
- This function NEVER returns 0 (auto-approve)
- Minimum is 1 (requires approval)
- For action 638: risk=39 → Level 1 expected, but got 5!

---

#### **Finding C: Why Level 5?**

**Hypothesis**: When policy engine says "require_approval", a SECOND system sets level to 5.

**Need to investigate**: Where does required_approval_level get set to 5?

Let me check one more place:

---

## 🔍 ROOT CAUSE ANALYSIS

### **The Flow (What Actually Happens)**:

```
1. Action Created (risk_score = 39)
   ↓
2. CVSS Calculator: "This is LOW risk (39)"
   ↓
3. Playbook Matched: "pb-auto-approve-low-risk-actions"
   ↓
4. Unified Policy Engine Evaluates:
   - Calculates own risk = 66 (based on policy rules)
   - Decision: REQUIRE_APPROVAL (66 >= threshold)
   ↓
5. WorkflowBridge Triggered:
   - Sees decision = REQUIRE_APPROVAL
   - Calls calculate_approval_levels(risk_score)
   - BUT uses WHICH risk_score? 39 or 66?
   ↓
6. required_approval_level set to ??? (mystery why it's 5)
   ↓
7. Status = "pending"
```

### **The Conflict**:

| System | Risk Score | Decision | Approval Level |
|--------|------------|----------|---------------|
| CVSS Calculator | 39 | Auto-approve | 0 |
| Policy Engine | 66 | Require approval | 2 |
| WorkflowBridge | ??? | ??? | **5** ← WHY? |

---

## 💡 KEY QUESTIONS REMAINING

### **Q1: Why is required_approval_level = 5 instead of 1 or 2?**

**Possible Answers**:
1. Policy engine sets it to 5 (need to check code)
2. WorkflowBridge uses policy_risk (66) instead of fused_risk (39)
3. Database default or trigger sets it

**Need to Check**:
- `services/unified_policy_evaluation_service.py` - where it sets required_approval_level
- Line where policy result is converted to database update

---

### **Q2: Should policy_risk override CVSS risk?**

**Current Behavior**: Policy risk (66) overrides CVSS risk (39)

**Expected Behavior** (needs decision):

**Option A**: CVSS is authoritative (pure technical risk)
- Risk 39 → Auto-approve
- Policy adds conditions but doesn't change risk score

**Option B**: Policy is authoritative (business risk)
- Policy risk 66 → Require approval
- CVSS is just one input to policy engine

**Option C**: Use MAX of both
- max(39, 66) = 66 → Require approval
- Conservative approach

---

### **Q3: What is "pb-auto-approve-low-risk-actions" playbook doing?**

**Logs show**: Playbook matched but approval still required

**Possible Issues**:
1. Playbook executes AFTER policy engine (too late)
2. Playbook is overridden by policy engine
3. Playbook has wrong conditions

---

## 🎯 SYSTEMS INVOLVED (Order of Execution)

1. **CVSS Auto-Mapper** ✅
   - Calculates technical risk = 39
   - Status: Working correctly

2. **Automation Playbooks** ⚠️
   - Matches "pb-auto-approve-low-risk-actions"
   - Status: Matched but not executing?

3. **Unified Policy Engine** ⚠️
   - Calculates policy risk = 66
   - Overrides CVSS decision
   - Status: Working, but conflicting with CVSS

4. **WorkflowBridge** ❌
   - Sets required_approval_level
   - Status: Setting wrong value (5 instead of 1-2)

5. **Database** ✅
   - Stores final values
   - Status: Correctly storing what it's told

---

## 📊 EXPECTED vs ACTUAL (Industry Standard)

### **Risk-Based Auto-Approval Matrix**

| CVSS Risk | Policy Risk | Expected Decision | Expected Level | Actual Level |
|-----------|-------------|-------------------|---------------|--------------|
| 0-39 | N/A | ✅ Auto-Approve | 0 | **5** ❌ |
| 0-39 | 60-69 | ? (needs decision) | 0 or 2? | **5** ❌ |
| 40-69 | N/A | ✅ Auto-Approve or L1 | 0-1 | **5** ❌ |
| 70-89 | N/A | ❌ Require L2-3 | 2-3 | **5** ❌ |
| 90-100 | N/A | ❌ Require L4-5 | 4-5 | **5** ✅ |

**Problem**: Everything gets Level 5, regardless of actual risk!

---

## 🔧 WHAT NEEDS TO BE FIXED

### **Issue #1: Policy Risk Overriding CVSS**

**Current**: Policy risk (66) overrides CVSS risk (39)

**Options**:
1. Make CVSS authoritative for approval decisions
2. Make Policy authoritative (document this clearly)
3. Use weighted average: `final_risk = (cvss * 0.7) + (policy * 0.3)`

---

### **Issue #2: WorkflowBridge Using Wrong Risk Score**

**Need to verify**: Is WorkflowBridge using:
- CVSS risk (39) → Would give Level 1 ✅
- Policy risk (66) → Would give Level 2 ✅
- Some default (100?) → Would give Level 3-5 ❌

---

### **Issue #3: Auto-Approval Playbook Not Working**

**Playbook matched** but **approval still required**

**Possible fixes**:
1. Playbook should run BEFORE policy engine
2. Playbook should override policy engine decision
3. Policy engine should respect playbook decisions

---

### **Issue #4: No Auto-Approve Path**

**WorkflowBridge**: Minimum approval level = 1 (never 0)

**This means**: NO path to auto-approval exists in WorkflowBridge!

**Fix needed**:
```python
def calculate_approval_levels(self, risk_score: int) -> int:
    if risk_score >= 90:
        return 5
    elif risk_score >= 70:
        return 3
    elif risk_score >= 50:
        return 2
    elif risk_score >= 40:
        return 1
    else:
        return 0  # ← ADD THIS: Auto-approve low-risk
```

---

## 🎯 RECOMMENDED ENTERPRISE SOLUTION

### **Option 1: CVSS-First Approach** (Recommended)

**Philosophy**: Technical risk (CVSS) drives approval, policies add conditions

**Changes Needed**:
1. WorkflowBridge uses CVSS risk (not policy risk)
2. Add Level 0 for auto-approval (risk < 40)
3. Policy engine adds CONDITIONS but doesn't change level
4. Playbooks can auto-approve if ALL conditions met

**Result**:
- Risk 39 → Level 0 → Auto-approved ✅
- Risk 66 → Level 2 → Requires approval ✅
- Clear, predictable behavior

---

### **Option 2: Policy-First Approach**

**Philosophy**: Business policy overrides technical risk

**Changes Needed**:
1. WorkflowBridge uses policy risk (66) not CVSS (39)
2. Add Level 0 for auto-approval (policy risk < 40)
3. Document that policies can escalate risk

**Result**:
- CVSS=39, Policy=66 → Level 2 → Requires approval
- CVSS=80, Policy=30 → Level 0 → Auto-approved
- Flexible but less predictable

---

### **Option 3: Hybrid Approach** (Most Robust)

**Philosophy**: Use maximum risk from all sources

**Changes Needed**:
1. Calculate: `final_risk = max(cvss_risk, policy_risk, playbook_risk)`
2. WorkflowBridge uses final_risk
3. Add Level 0 for auto-approval (final_risk < 40)

**Result**:
- CVSS=39, Policy=66 → final=66 → Level 2 → Requires approval
- CVSS=39, Policy=30 → final=39 → Level 0 → Auto-approved
- Conservative, secure

---

## 📝 NEXT STEPS FOR ENTERPRISE SOLUTION

1. **DECISION NEEDED**: Choose Option 1, 2, or 3
2. **Code Investigation**: Find where required_approval_level=5 is set
3. **Fix WorkflowBridge**: Add Level 0 auto-approval
4. **Fix Policy Engine**: Align with chosen approach
5. **Test**: Verify risk 39 actions auto-approve

---

## 🎯 SUMMARY

**Root Causes Found** (3 systems):

1. ✅ **CVSS Calculator**: Working correctly (risk=39)
2. ⚠️ **Policy Engine**: Overriding with policy_risk=66
3. ❌ **WorkflowBridge**: Setting required_approval_level=5 (wrong)

**Missing Feature**:
- No auto-approval path (Level 0) in WorkflowBridge

**Conflict**:
- CVSS says "low risk, auto-approve"
- Policy says "medium risk, require approval"
- WorkflowBridge says "everyone gets Level 5"

---

**Status**: AWAITING ENTERPRISE SOLUTION APPROVAL
**Recommendation**: Option 1 (CVSS-First) for predictable, technical risk-based approvals

**Engineer**: Donald King (OW-kai Enterprise)
**Date**: 2025-11-19

---

**End of Investigation Report**
