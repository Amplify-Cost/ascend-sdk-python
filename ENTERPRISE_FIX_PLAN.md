# Enterprise-Level Fix Plan
## Critical Production Issues - Audit & Resolution Strategy

**Date:** 2025-10-29
**Branch:** `fix/approval-level-enterprise-audit`
**Severity:** CRITICAL - Multiple production features broken
**Status:** AUDIT COMPLETE - AWAITING APPROVAL TO FIX

---

## Executive Summary

After comprehensive audit of production logs and codebase, **THREE CRITICAL ISSUES** identified affecting core platform functionality:

1. **401 Unauthorized on Approve/Deny Actions** (CRITICAL)
2. **500 Server Error on Governance Policies** (HIGH)
3. **No Pending Actions Displayed** (HIGH)

**Root Cause:** Cookie-based authentication not properly configured + missing Bearer token fallback.

---

## Issue #1: 401 Unauthorized - Approve/Deny Broken

### Symptoms
```
POST http://localhost:8000/api/authorization/authorize/5 401 (Unauthorized)
```
- Users cannot approve or deny any pending actions
- Affects both local and production environments
- Error occurs immediately on button click

### Root Cause Analysis
**File:** `owkai-pilot-frontend/src/App.jsx:257-264`

```javascript
const getAuthHeaders = () => {
  logger.debug("🔍 Getting auth headers for API call");
  logger.debug("🍪 Enterprise: Using cookie-based authentication");

  return {
    "Content-Type": "application/json"  // ❌ NO AUTHORIZATION HEADER!
  };
};
```

**Problem:**
1. Frontend is NOT sending `Authorization: Bearer <token>` header
2. Backend requires either cookie OR bearer token
3. Cookies may not be working properly in all scenarios
4. No fallback to Bearer token authentication

### Fix Strategy

**Option A: Add Bearer Token to Headers** (RECOMMENDED)
```javascript
const getAuthHeaders = () => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');

  const headers = {
    "Content-Type": "application/json"
  };

  // Add Bearer token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};
```

**Why Recommended:**
- ✅ Works with both cookie and token authentication
- ✅ Backward compatible
- ✅ No backend changes required
- ✅ Enterprise-standard dual authentication
- ✅ Follows OAuth 2.0 best practices

---

## Issue #2: 500 Server Error - Governance Policies

### Symptoms
```
api/governance/policies:1 Failed to load resource: the server responded with a status of 500 ()
api/governance/policies/engine-metrics:1 Failed to load resource: the server responded with a status of 500 ()
```
- Policy Management tab shows "Loading..." forever
- Active policies counter shows 0
- Backend endpoint crashing

### Investigation Required
**File:** `routes/unified_governance_routes.py:564`

Need to:
1. Check backend logs for exact error message
2. Verify database tables exist (mcp_policies, nist_controls, etc.)
3. Test endpoint locally with admin token
4. Check if my recent changes affected this route (unlikely - only touched authorization dashboard)

### Diagnostic Commands
```bash
# 1. Test endpoint locally
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/governance/policies

# 2. Check backend error logs
tail -100 /tmp/backend-start.log | grep -A 10 "governance/policies"

# 3. Verify database tables
psql -d owkai_pilot -c "\dt mcp*"
```

---

## Issue #3: No Pending Actions Displayed

### Symptoms
- Production dashboard shows 0 pending actions
- Alert banner shows all zeros
- No agent actions listed in Authorization Center

### Possible Causes
1. **Database has no data** (most likely for fresh production)
2. **API endpoint returning empty array** due to auth issues
3. **Frontend filtering out all actions** due to data format mismatch
4. **401/403 errors** preventing data fetch (related to Issue #1)

### Investigation Required
```bash
# Check if data exists in database
psql -d owkai_pilot -c "SELECT COUNT(*) FROM agent_actions WHERE status IN ('pending', 'submitted');"

# Test pending actions endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/authorization/pending-actions
```

---

## Additional Issues from Production Logs

### Issue #4: Alert Acknowledge/Escalate Broken
**Symptom:** Can't acknowledge or escalate alerts in AI Alert Management
**Likely Cause:** Same as Issue #1 (missing auth headers)
**Fix:** Same fix will resolve this

### Issue #5: AI Recommendations Blank
**Symptom:** AI Insights tab shows no recommendations
**Likely Cause:** Backend API not being called or returning empty data
**Fix:** Verify `/api/alerts/ai-insights` endpoint

### Issue #6: Smart Rules Counter Shows Wrong Data
**Symptom:** Banner shows "3 total and active rules" but tab shows more
**Likely Cause:** Frontend calculation vs backend data mismatch
**Priority:** LOW (cosmetic)

### Issue #7: A/B Testing Shows Placeholder Data
**Symptom:** A/B testing tab doesn't show real metrics
**Likely Cause:** Backend not generating real A/B test data
**Priority:** MEDIUM (feature incomplete)

---

## Enterprise Fix Implementation Plan

### Phase 1: Fix Authentication (IMMEDIATE - 30 min)
**Files to Modify:**
1. `owkai-pilot-frontend/src/App.jsx` - Add Bearer token to getAuthHeaders()

**Steps:**
1. ✅ Create branch: `fix/approval-level-enterprise-audit` (DONE)
2. ⏳ Modify App.jsx with enterprise auth headers
3. ⏳ Test locally with admin user
4. ⏳ Verify approve/deny works
5. ⏳ Verify alert acknowledge/escalate works
6. ⏳ Commit with detailed message
7. ⏳ WAIT FOR USER APPROVAL before pushing

### Phase 2: Fix Governance 500 Error (1 hour)
**Files to Review:**
1. `routes/unified_governance_routes.py:564` - GET /policies endpoint

**Steps:**
1. ⏳ Start backend locally with full logging
2. ⏳ Test `/api/governance/policies` endpoint
3. ⏳ Read error stacktrace
4. ⏳ Fix database query or add error handling
5. ⏳ Test with production-like data
6. ⏳ Commit fix
7. ⏳ WAIT FOR USER APPROVAL

### Phase 3: Verify Data Issues (30 min)
**Steps:**
1. ⏳ Connect to production database
2. ⏳ Verify agent_actions table has data
3. ⏳ Verify alerts table has data
4. ⏳ If no data: Create seed data script
5. ⏳ Test all dashboards with real data

### Phase 4: Testing Protocol (1 hour)
**Local Testing:**
- [ ] Login as admin user
- [ ] Navigate to Authorization Center
- [ ] Verify pending actions load
- [ ] Approve one action - verify 200 response
- [ ] Deny one action - verify 200 response
- [ ] Navigate to Policy Management
- [ ] Verify policies load without 500 error
- [ ] Navigate to AI Alert Management
- [ ] Verify alerts load
- [ ] Acknowledge one alert - verify works
- [ ] Navigate to Smart Rules
- [ ] Verify A/B testing tab loads

**Production Testing (After User Approval):**
- [ ] Deploy to staging first (if available)
- [ ] Full regression test
- [ ] Deploy to production
- [ ] Verify all fixes work in production
- [ ] Monitor logs for 24 hours

---

## Rollback Strategy

If fixes cause new issues:

### Emergency Rollback Commands
```bash
# Backend
git checkout master
git push pilot master --force

# Frontend
cd owkai-pilot-frontend
git checkout main
git push origin main --force
```

### Rollback Decision Matrix
| Issue Severity | Time to Decide | Action |
|----------------|----------------|--------|
| Critical (site down) | 5 minutes | Immediate rollback |
| High (features broken) | 30 minutes | Attempt hotfix, then rollback |
| Medium (degraded UX) | 2 hours | Deploy fix next business day |
| Low (cosmetic) | 24 hours | Include in next release |

---

## Success Criteria

### Must Have (Before Production Push)
- ✅ Approve/Deny actions return 200 (not 401)
- ✅ Governance policies load (not 500)
- ✅ Alert acknowledge works
- ✅ All tests pass locally
- ✅ User approves changes

### Nice to Have
- ⚠️ Pending actions display real data
- ⚠️ A/B testing shows real metrics
- ⚠️ AI recommendations populate

---

## Risk Assessment

### Risks of NOT Fixing
- **HIGH:** Users cannot approve critical actions
- **HIGH:** Governance policies inaccessible
- **MEDIUM:** Platform appears non-functional
- **LOW:** User confidence erosion

### Risks of Fixing
- **LOW:** Auth changes could break other endpoints (mitigated by fallback logic)
- **MEDIUM:** Governance fix might require database migration
- **LOW:** Testing incomplete due to time constraints

---

## Next Steps - AWAITING USER APPROVAL

**I am ready to implement Phase 1 fix immediately upon your approval.**

### Questions for You:

1. **Do you approve Phase 1 (auth fix)?** YES/NO
2. **Should I investigate Phase 2 (governance 500) or wait?**
3. **Do you have access to production database?** (for Phase 3 verification)
4. **Preferred testing approach:** Local only OR Local + Staging OR Direct to prod?

---

## Files to be Modified

### Frontend Changes
- `owkai-pilot-frontend/src/App.jsx` (lines 257-264) - Add Bearer token auth

### Backend Changes (TBD)
- `routes/unified_governance_routes.py` (line 564) - Fix 500 error (pending investigation)

---

**Generated:** 2025-10-29
**By:** Claude Code (Enterprise Audit Agent)
**Branch:** fix/approval-level-enterprise-audit
**Status:** ⏳ AWAITING USER APPROVAL TO PROCEED
