# 🔍 MCP Endpoint Investigation Report

**Date**: 2025-11-18
**Engineer**: Donald King (OW-kai Enterprise)
**Issue**: Simulator creates MCP actions but shows `Decision: None` and all actions marked as `denied`

---

## 📋 Executive Summary

**Finding**: The `/api/governance/mcp-governance/evaluate-action` endpoint is designed for **approval workflows**, NOT for initial submission. This causes ALL MCP actions to be incorrectly marked as `denied` when the simulator doesn't provide a `decision` field.

**Impact**:
- ✅ **MCP actions ARE being created** (IDs 51-70 confirmed in database)
- ❌ **All marked as `status=denied`** instead of `status=pending`
- ❌ **Simulator shows `Decision: None`** because endpoint returns wrong response format
- ❌ **MCP actions DON'T appear in unified queue** because they're filtered by status

**Root Cause**: Wrong endpoint used + endpoint logic flaw

---

## 🔎 Investigation Evidence

### **Evidence 1: CloudWatch Logs Show MCP Actions Created**

```
2025-11-19 01:55:14 - INFO - 🔌 Evaluating MCP action None with unified policy engine
2025-11-19 01:55:14 - INFO - ✅ Created MCP action ID 51 with real data from request
2025-11-19 01:55:14 - INFO - 🔌 Evaluating MCP action 51 with unified policy engine
2025-11-19 01:55:14 - INFO - ✅ MCP action 51 evaluated: decision=require_approval, policy_risk=72, namespace=mcp, verb=s3_upload
2025-11-19 01:55:14 - INFO - ✅ MCP action 51 None - policy_decision=require_approval, risk=72
                                          ^^^^ THIS IS THE decision PARAMETER (None)
```

**Key Observation**: The log shows `"51 None"` - that `None` is the `decision` parameter value.

---

### **Evidence 2: Database Shows All MCP Actions as `denied`**

```sql
SELECT id, mcp_server_name, verb, status, policy_decision, risk_score
FROM mcp_server_actions
WHERE id BETWEEN 51 AND 70;
```

**Result**:
```
id | mcp_server_name     | verb          | status | policy_decision  | risk_score
---+---------------------+---------------+--------+------------------+-----------
51 | aws-mcp-server      | s3_upload     | denied | require_approval | 72
52 | filesystem-server   | write_file    | denied | require_approval | 72
53 | filesystem-server   | write_file    | denied | require_approval | 72
... (all 20 rows show status=denied)
```

**Key Finding**: ALL MCP actions have `status=denied` even though `policy_decision=require_approval` (which should mean `status=pending`).

---

### **Evidence 3: Endpoint Code Analysis**

**File**: `ow-ai-backend/routes/unified_governance_routes.py`
**Lines**: 799-972

```python
@router.post("/mcp-governance/evaluate-action")
async def evaluate_mcp_action(
    action_data: Dict[str, Any],
    ...
):
    # Line 819: Extract decision from request
    decision = action_data.get("decision")  # ❌ Simulator doesn't send this!

    # Line 843-876: Create MCP action if doesn't exist
    if not mcp_action:
        mcp_action = MCPServerAction(...)

    # Line 888: Evaluate with policy engine
    policy_result = await unified_service.evaluate_mcp_action(mcp_action, user_context)
    # ✅ This works! Returns policy_decision="require_approval", risk=72

    # Line 891: ❌ BUG - Sets status based on decision parameter, NOT policy result!
    mcp_action.status = "approved" if decision == "approved" else "denied"
    #                                   ^^^^^^^^ This is None from simulator
    #                                            So status becomes "denied"!

    # Line 944-967: Return response
    return {
        "success": True,
        "decision": decision,  # ❌ Returns None, not the policy decision!
        "action_id": mcp_action.id,
        ...
    }
```

**Critical Bugs Identified**:

1. **Bug #1** (Line 891): Status set from `decision` parameter instead of `policy_result.decision`
   ```python
   # Current (WRONG):
   mcp_action.status = "approved" if decision == "approved" else "denied"

   # Should be:
   mcp_action.status = "approved" if decision == "approved" else "pending"
   # OR better: Set status based on policy_result.decision
   ```

2. **Bug #2** (Line 946): Response returns `decision` parameter instead of policy decision
   ```python
   # Current (WRONG):
   return {"decision": decision}  # Returns None

   # Should be:
   return {"decision": policy_result.decision.value}  # Returns "require_approval"
   ```

---

### **Evidence 4: Two MCP Endpoints Exist**

**Endpoint 1**: `/api/governance/mcp-governance/evaluate-action`
**File**: `routes/unified_governance_routes.py` (lines 799-972)
**Status**: ✅ **ACTIVE** (registered in main.py)
**Purpose**: Approval/denial of existing MCP actions
**Expected Input**: `action_id` + `decision` ("approved" or "denied")
**Behavior**: Creates action if doesn't exist (test-friendly), but always marks as denied if decision=None

**Endpoint 2**: `/api/governance/mcp-governance/evaluate-action`
**File**: `routes/authorization_api_adapter.py` (lines 121-141)
**Status**: ❌ **INACTIVE** (NOT registered in main.py)
**Purpose**: Mock endpoint returning sample data
**Code**:
```python
@router.post("/mcp-governance/evaluate-action")
async def evaluate_mcp_action(action_data: dict, current_user = Depends(get_current_user)):
    """MCP governance endpoint that frontend expects"""
    return {
        "success": True,
        "actions": auth_data,
        "evaluated_action": {
            "id": "eval-001",
            "status": "evaluated",
            "risk_score": 45,
            "recommendation": "approve"
        }
    }
```

**Conclusion**: Only ONE endpoint is active (unified_governance_routes.py). The authorization_api_adapter.py version is **NOT being used**.

---

## 🎯 Root Cause Summary

### **Primary Issue**: Wrong Endpoint Being Used

The simulator calls `/api/governance/mcp-governance/evaluate-action`, which is designed for **approval workflows** (requires `decision` field), NOT for **initial submission**.

### **Secondary Issue**: Endpoint Logic Flaw

Even when auto-creating actions, the endpoint sets `status="denied"` when `decision=None` instead of `status="pending"`.

---

## 🔧 Why This Happens

**Step-by-Step Breakdown**:

1. **Simulator sends request** WITHOUT `decision` field:
   ```json
   {
     "mcp_server": "aws-mcp-server",
     "action_type": "s3_upload",
     "namespace": "mcp",
     "verb": "s3_upload",
     "resource": "{...}"
   }
   ```

2. **Endpoint extracts decision**:
   ```python
   decision = action_data.get("decision")  # Returns None
   ```

3. **Endpoint creates MCP action**:
   ```python
   mcp_action = MCPServerAction(...)  # ID=51
   ```

4. **Policy evaluation runs correctly**:
   ```python
   policy_result = await unified_service.evaluate_mcp_action(...)
   # Returns: decision="require_approval", risk_score=72
   ```

5. **❌ BUG: Status set from decision parameter, not policy result**:
   ```python
   mcp_action.status = "approved" if decision == "approved" else "denied"
   #                                   ^^^^ None != "approved", so status="denied"
   ```

6. **Database commit**:
   ```sql
   INSERT INTO mcp_server_actions (..., status='denied', policy_decision='require_approval', ...)
   ```

7. **Response sent to simulator**:
   ```json
   {
     "success": true,
     "decision": null,  // ❌ Should be "require_approval"
     "action_id": 51
   }
   ```

8. **Simulator logs**:
   ```
   🔧 MCP ACTION #51 | aws-mcp-server | Tool: s3_upload | MEDIUM | Decision: None
   ```

---

## 📊 Impact Analysis

### **What Works**:
- ✅ MCP actions ARE being created (20 actions created during test)
- ✅ Policy evaluation WORKS correctly (risk scores calculated)
- ✅ Audit logs ARE being created
- ✅ Risk assessment WORKS (risk_score=72, policy_risk_score=72)

### **What Doesn't Work**:
- ❌ Status always set to `denied` instead of `pending`
- ❌ MCP actions don't appear in unified queue (filtered by status=pending)
- ❌ Simulator shows `Decision: None` instead of actual decision
- ❌ Frontend dashboard won't show these actions (wrong status)

---

## 🏢 Enterprise Pattern Analysis

### **Expected Workflow** (Like Agent Actions):

1. **Initial Submission**: POST to `/api/governance/unified-actions`
   - Payload: Action data (no decision field)
   - Backend: Evaluates policies, sets status=pending/approved based on risk
   - Response: Returns policy decision

2. **Manual Approval** (if needed): POST to approval endpoint
   - Payload: action_id + decision
   - Backend: Updates status to approved/denied
   - Response: Confirms approval

### **Current MCP Workflow** (Broken):

1. **Simulator calls** `/api/governance/mcp-governance/evaluate-action`
   - Missing `decision` field
   - Endpoint treats as denial (decision != "approved")
   - Status set to `denied`
   - ❌ Breaks the flow

---

## 🔍 Is There a Redundant Endpoint?

**Answer**: NO, there is NOT a redundant endpoint in production.

**Findings**:
1. **Active Endpoint**: `unified_governance_routes.py` → `/api/governance/mcp-governance/evaluate-action`
   - Registered in main.py
   - Handles MCP governance
   - Has a logic bug but is NOT redundant

2. **Inactive Endpoint**: `authorization_api_adapter.py` → `/mcp-governance/evaluate-action`
   - NOT registered in main.py
   - Mock implementation
   - Never used in production
   - **Can be deleted** (code cleanup)

**Recommendation**: Delete `authorization_api_adapter.py` as it's unused legacy code.

---

## ✅ Correct Solution

### **Option 1: Use Unified Endpoint (Recommended)**

Change simulator to use `/api/governance/unified-actions`:

```python
# Simulator change:
response = requests.post(
    f"{self.base_url}/api/governance/unified-actions",  # ✅ Use this endpoint
    json={
        "action_source": "mcp",
        "mcp_server": mcp_config['server_name'],
        "action_type": mcp_config['tool'],
        "namespace": "mcp",
        "verb": mcp_config['tool'],
        "resource": json.dumps(mcp_config['args']),
        "context": {...}
    },
    headers=headers
)
```

**Benefits**:
- ✅ Same workflow as agent actions
- ✅ Proper status assignment (pending/approved based on risk)
- ✅ Returns correct decision in response
- ✅ Works with unified queue
- ✅ No backend changes needed

### **Option 2: Fix Existing Endpoint** (Not Recommended)

Fix `/mcp-governance/evaluate-action` to handle submission without decision:

```python
# Line 891 - Change from:
mcp_action.status = "approved" if decision == "approved" else "denied"

# To:
if decision:
    # Manual approval workflow
    mcp_action.status = "approved" if decision == "approved" else "denied"
else:
    # Initial submission workflow - set status based on policy
    if policy_result.decision.value == "approve":
        mcp_action.status = "approved"
    else:
        mcp_action.status = "pending"
```

**Drawbacks**:
- ❌ Makes one endpoint handle two workflows (confusing)
- ❌ Still non-standard compared to agent actions
- ❌ Requires backend deployment

---

## 🎯 Recommended Actions

1. **Immediate**: Update simulator to use `/api/governance/unified-actions` ✅
2. **Short-term**: Delete unused `authorization_api_adapter.py` (code cleanup)
3. **Medium-term**: Consider deprecating `/mcp-governance/evaluate-action` in favor of unified endpoint
4. **Long-term**: Standardize all action types (agent/MCP/playbook) on single unified endpoint

---

## 📝 Key Takeaways

1. **Not a redundant endpoint issue** - Only one endpoint is active
2. **Logic bug in endpoint** - Sets status from wrong variable
3. **Wrong endpoint being used** - Should use unified endpoint
4. **MCP actions ARE working** - Just marked with wrong status
5. **Easy fix** - Change simulator to use correct endpoint

---

**Report Prepared By**: OW-kai Enterprise Engineering
**Status**: INVESTIGATION COMPLETE ✅
**Next Step**: Implement Option 1 (use unified endpoint)
