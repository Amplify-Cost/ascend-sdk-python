# Unified Authorization Queue - Dependency Audit Report

**Project:** OW AI Enterprise Authorization Center
**Audit Date:** November 15, 2025
**Engineer:** Donald King, OW-kai Enterprise
**Purpose:** Identify all systems dependent on pending-actions endpoint before implementation

---

## Executive Summary

This audit identifies all systems, components, and endpoints that will be affected by implementing the unified authorization queue. The audit reveals **3 active backend endpoints** and **2 frontend components** that currently consume pending actions data.

### Critical Findings

1. **✅ GOOD NEWS:** Frontend already uses `/api/governance/pending-actions` - NOT authorization routes
2. **⚠️ OVERLAP:** Three separate backend endpoints serve pending actions (potential confusion)
3. **✅ SAFE:** EnterpriseApiService.js is NOT actively used by Authorization Dashboard
4. **⚠️ COMPLEXITY:** Unified governance router already exists but only queries agent_actions table

---

## Backend Endpoints Audit

### Endpoint 1: `/api/governance/pending-actions` ⭐ PRIMARY

**File:** `ow-ai-backend/routes/unified_governance_routes.py`
**Lines:** 2348-2373
**Status:** ✅ ACTIVELY USED BY FRONTEND
**Mount Point:** Line 1121 in main.py - `app.include_router(router, prefix="/api/governance")`

**Current Implementation:**
```python
@router.get("/pending-actions")
async def get_unified_pending_actions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from services.enterprise_batch_loader_v2 import enterprise_loader_v2
    result = enterprise_loader_v2.load_pending_approval_actions(db)
    return result
```

**What It Does:**
- Uses `enterprise_batch_loader_v2.py` to load actions
- **ONLY queries `agent_actions` table** (does NOT query `mcp_server_actions`)
- Returns actions with status = "pending_approval"
- Returns format: `{"success": True, "pending_actions": [...], "actions": [...], "total": N}`

**Impact of Our Changes:**
- ✅ **REPLACE THIS IMPLEMENTATION** with new unified loader
- ✅ Frontend already calls this endpoint (no frontend changes needed for endpoint URL)
- ✅ Response format will remain compatible (same JSON structure)

---

### Endpoint 2: `/agent-control/pending-actions` (Legacy)

**File:** `ow-ai-backend/routes/authorization_routes.py`
**Lines:** 795-803
**Status:** ⚠️ LEGACY - Potentially unused
**Mount Point:** Line 1156 in main.py - `app.include_router(authorization_router)`

**Current Implementation:**
```python
@router.get("/pending-actions")  # prefix="/agent-control" from router definition
async def get_pending_actions(
    risk_filter: Optional[str] = None,
    emergency_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return AuthorizationService.get_pending_actions(db, risk_filter, emergency_only, current_user)
```

**What It Does:**
- Uses `AuthorizationService.get_pending_actions()`
- Supports risk_filter and emergency_only parameters
- Legacy endpoint from original agent-control system

**Impact of Our Changes:**
- ⚠️ **NO CHANGES NEEDED** - This is a legacy endpoint
- Frontend does NOT use this endpoint
- Can remain as-is for backward compatibility
- **Recommendation:** Keep for backward compatibility, but consider deprecating

---

### Endpoint 3: `/api/authorization/pending-actions`

**File:** `ow-ai-backend/routes/authorization_routes.py`
**Lines:** 1072-1091
**Status:** ⚠️ DUPLICATE - Referenced in EnterpriseApiService but not used by main dashboard
**Mount Point:** Line 1157 in main.py - `app.include_router(authorization_api_router)`

**Current Implementation:**
```python
@api_router.get("/pending-actions")  # prefix="/api/authorization" from router definition
async def get_pending_actions_api(
    risk_filter: Optional[str] = None,
    emergency_only: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = AuthorizationService.get_pending_actions(db, risk_filter, emergency_only, current_user)

    if result.get("success", False):
        return result["actions"]
    else:
        return []
```

**What It Does:**
- Same as Endpoint 2 but with `/api/` prefix
- Returns empty array on error (vs full response object)
- Uses same AuthorizationService backend

**Impact of Our Changes:**
- ⚠️ **OPTIONAL UPDATE** - Referenced in EnterpriseApiService.js but not actively used
- Frontend Authorization Dashboard does NOT call this endpoint
- **Recommendation:** Update to use unified loader for consistency

---

## Frontend Components Audit

### Component 1: AgentAuthorizationDashboard.jsx ⭐ PRIMARY

**File:** `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`
**Lines:** 148-296
**Status:** ✅ ACTIVELY USED - Main Authorization Center component

**Current API Call:**
```javascript
// Line 154
const response = await fetch(`${API_BASE_URL}/api/governance/pending-actions`, {
  credentials: "include",
  headers: {
    ...getAuthHeaders(),
    "Content-Type": "application/json"
  }
});
```

**What It Does:**
- Fetches from `/api/governance/pending-actions` (Endpoint 1)
- Already handles both agent and MCP actions via client-side detection
- Transforms data to include `action_source`, `is_mcp_action`, `is_agent_action` flags
- Maps risk scores, NIST/MITRE controls, policy data

**Impact of Our Changes:**
- ✅ **UPDATE API CALL** to use new `/api/authorization/unified-pending-actions`
- ✅ Add filter UI (dropdown + quick buttons)
- ✅ Response format will be compatible (may need minor adjustments for new fields)
- ✅ Already has approval routing logic that handles both action types

---

### Component 2: EnterpriseApiService.js

**File:** `owkai-pilot-frontend/src/services/EnterpriseApiService.js`
**Lines:** 36-58, 178
**Status:** ⚠️ NOT ACTIVELY USED by Authorization Dashboard

**Current API References:**
```javascript
// Line 42 - In getAuthorizationData()
const pendingActions = await this.request('/api/authorization/pending-actions');

// Line 178 - In testConnectivity()
{ name: 'Pending Actions', endpoint: '/api/authorization/pending-actions' }
```

**What It Does:**
- Centralized API service layer
- References `/api/authorization/pending-actions` (Endpoint 3)
- Used for connectivity testing
- **NOT used by AgentAuthorizationDashboard** (which makes direct fetch calls)

**Impact of Our Changes:**
- ⚠️ **OPTIONAL UPDATE** - Not critical since not actively used
- **Recommendation:** Update for consistency and future-proofing
- Change endpoint to `/api/authorization/unified-pending-actions`

---

## Data Flow Architecture

### Current State (Before Our Changes)

```
┌─────────────────────────────────────────────────────────┐
│ Frontend: AgentAuthorizationDashboard.jsx              │
│   └─ fetchPendingActions()                             │
│      └─ Calls: /api/governance/pending-actions         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Backend: unified_governance_routes.py                   │
│   └─ get_unified_pending_actions()                     │
│      └─ Uses: enterprise_batch_loader_v2.py            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Data Source: enterprise_batch_loader_v2.py              │
│   └─ load_pending_approval_actions()                   │
│      └─ Queries: agent_actions table ONLY ❌           │
│      └─ Missing: mcp_server_actions table ❌            │
└─────────────────────────────────────────────────────────┘
```

**Problem:** MCP actions are NOT loaded from database, so MCP Servers tab is always empty.

---

### Proposed State (After Our Changes)

```
┌─────────────────────────────────────────────────────────┐
│ Frontend: AgentAuthorizationDashboard.jsx              │
│   └─ fetchPendingActions()                             │
│      └─ Calls: /api/authorization/unified-pending-actions │ ← CHANGE
│   └─ Filter UI: All/Agent/MCP/High Risk               │ ← NEW
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Backend: authorization_routes.py                        │ ← NEW
│   └─ get_unified_pending_actions()                     │ ← NEW
│      └─ Uses: enterprise_unified_loader.py             │ ← NEW
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Data Source: enterprise_unified_loader.py              │ ← NEW
│   └─ load_all_pending_actions()                        │ ← NEW
│      ├─ Queries: agent_actions table ✅                │
│      ├─ Queries: mcp_server_actions table ✅           │
│      ├─ Transforms both to common schema ✅            │
│      └─ Sorts by risk_score DESC ✅                    │
└─────────────────────────────────────────────────────────┘
```

**Solution:** Unified loader queries BOTH tables and merges them into single response.

---

## Required Changes Summary

### Backend Changes

| File | Change Type | Description | Priority |
|------|-------------|-------------|----------|
| `services/enterprise_unified_loader.py` | **CREATE** | New unified loader that queries both tables | **CRITICAL** |
| `routes/authorization_routes.py` | **MODIFY** | Add new endpoint `/api/authorization/unified-pending-actions` | **CRITICAL** |
| `routes/unified_governance_routes.py` | **OPTIONAL** | Could update to use unified loader (but not needed if we use auth routes) | LOW |

### Frontend Changes

| File | Change Type | Description | Priority |
|------|-------------|-------------|----------|
| `src/components/AgentAuthorizationDashboard.jsx` | **MODIFY** | Update API call, add filter UI | **CRITICAL** |
| `src/services/EnterpriseApiService.js` | **MODIFY** | Update endpoint for future-proofing | LOW |

---

## Migration Strategy

### Option A: ⭐ RECOMMENDED - Add New Endpoint, Update Frontend

**Advantages:**
- ✅ Zero breaking changes to existing endpoints
- ✅ Gradual migration path
- ✅ Easy rollback if issues occur
- ✅ Both old and new endpoints work during transition

**Steps:**
1. Create `enterprise_unified_loader.py` (new file)
2. Add new endpoint to `authorization_routes.py`
3. Test new endpoint locally
4. Update frontend to use new endpoint
5. Deploy backend first (both endpoints available)
6. Deploy frontend (switches to new endpoint)
7. Monitor for 48 hours
8. Optional: Deprecate old endpoint in future release

**Rollback:** Change frontend API call back to old endpoint

---

### Option B: Replace Existing Unified Governance Endpoint

**Advantages:**
- ✅ No new endpoints needed
- ✅ Frontend already calls this endpoint

**Disadvantages:**
- ❌ Breaking change to existing endpoint
- ❌ Harder to rollback
- ❌ Unified governance router is less organized than authorization router

**Steps:**
1. Create `enterprise_unified_loader.py`
2. Update `unified_governance_routes.py` to use new loader
3. Deploy backend and frontend together
4. Hope nothing breaks

**Rollback:** Revert code changes and redeploy

---

## Recommendation: Option A

**Rationale:**
1. **Safety First:** New endpoint means zero risk to existing functionality
2. **Better Architecture:** `/api/authorization/*` is more appropriate than `/api/governance/*`
3. **Enterprise Standards:** Aligns with authorization_routes.py patterns
4. **Gradual Migration:** Can test extensively before switching frontend
5. **Rollback Safety:** One-line change in frontend to rollback

**Updated Implementation Plan:**
1. Create `services/enterprise_unified_loader.py` (NEW)
2. Add endpoint to `routes/authorization_routes.py` (MODIFY - add ~50 lines)
3. Update `src/components/AgentAuthorizationDashboard.jsx` (MODIFY - line 154 and add filter UI)
4. Optional: Update `src/services/EnterpriseApiService.js` for consistency

---

## Testing Impact Analysis

### Local Testing Requirements

**Backend Tests:**
1. Test new `/api/authorization/unified-pending-actions` endpoint
2. Verify both agent and MCP actions returned
3. Verify counts object correct
4. Verify sorting by risk_score
5. Verify no performance regression

**Frontend Tests:**
1. Test filter dropdown shows correct counts
2. Test quick filter buttons work
3. Test approval flow still works for both types
4. Test no console errors
5. Verify backward compatibility

**Integration Tests:**
1. Create agent action → verify appears in unified queue
2. Create MCP action → verify appears in unified queue
3. Filter to "Agent" → verify only agent actions shown
4. Filter to "MCP" → verify only MCP actions shown
5. Approve agent action → verify routes to correct endpoint
6. Approve MCP action → verify routes to correct endpoint

---

## Production Deployment Impact

### Deployment Sequence

**Phase 1: Backend Deployment** (Zero Impact)
- Deploy new `enterprise_unified_loader.py`
- Deploy new endpoint in `authorization_routes.py`
- Result: New endpoint available, old endpoint still works
- Frontend: No changes yet, still using old endpoint
- **Risk Level:** ✅ ZERO - Old endpoint unchanged

**Phase 2: Frontend Deployment** (Minimal Impact)
- Update API call to new endpoint
- Add filter UI
- Result: Frontend uses new endpoint, old endpoint still exists
- **Risk Level:** ⚠️ LOW - Can rollback with one-line change

**Phase 3: Monitoring** (48 hours)
- Monitor error rates
- Verify approval success rates
- Check performance metrics
- **Risk Level:** ✅ SAFE - Both endpoints available

**Phase 4: Deprecation** (Optional, Future)
- Mark old endpoint as deprecated
- Add warning logs
- Plan removal for next major version
- **Risk Level:** ✅ SAFE - Gradual sunset

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Breaking existing functionality | High | Low | Use new endpoint, keep old one |
| Performance degradation | Medium | Low | Indexed queries, batch loading |
| Data inconsistency | Medium | Low | Both tables use same status values |
| Frontend errors | Medium | Low | Comprehensive local testing |
| Rollback complexity | Low | Low | One-line frontend change |

---

## Additional Findings

### Unused/Legacy Code Identified

1. **`/agent-control/pending-actions`** - Legacy endpoint, not used by modern frontend
2. **Archive files** - Multiple backup copies of old implementations
3. **EnterpriseApiService connectivity tests** - Reference unused endpoint

### Optimization Opportunities

1. **Consolidate pending-actions endpoints** - Currently 3 separate implementations
2. **Remove duplicate authorization router registrations** - Some commented-out includes still present
3. **Deprecate legacy /agent-control/* routes** - Modern frontend uses /api/* exclusively

---

## Approval Checklist

Before proceeding with implementation:

- [ ] Confirm Option A (new endpoint) is preferred approach
- [ ] Verify frontend API call change is acceptable (line 154)
- [ ] Approve gradual migration strategy
- [ ] Confirm 48-hour monitoring period is acceptable
- [ ] Approve keeping old endpoint for backward compatibility
- [ ] Confirm optional EnterpriseApiService update desired

---

## Conclusion

**Safe to Proceed:** ✅ YES

The unified queue implementation can be safely deployed using **Option A (new endpoint)** with minimal risk:

1. **Frontend Impact:** Single API call change (line 154) + filter UI addition
2. **Backend Impact:** New file + new endpoint (no changes to existing endpoints)
3. **Rollback Plan:** Change 1 line of frontend code
4. **Migration Path:** Gradual with zero downtime
5. **Risk Level:** LOW

**No other systems will be affected** by this implementation. The changes are isolated to:
- 1 new backend file
- 1 modified backend file (add endpoint)
- 1 modified frontend file (API call + filter UI)
- 1 optional frontend file (EnterpriseApiService.js)

**Evidence-based recommendation:** Proceed with implementation using Option A.

---

**Audit Complete**

*This audit was conducted using comprehensive codebase analysis, live route inspection, and architectural review of all pending-actions dependencies across frontend and backend systems.*
