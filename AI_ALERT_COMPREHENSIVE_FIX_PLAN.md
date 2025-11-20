# 🏢 AI Alert Management - Comprehensive Enterprise Fix Plan

**Date**: 2025-11-19
**Status**: READY FOR APPROVAL
**Engineer**: Donald King (OW-kai Enterprise)
**Priority**: CRITICAL

---

## 📋 EXECUTIVE SUMMARY

**Critical Issues Found**:
1. ✅ Frontend OVERWRITES AI-generated recommendations with hardcoded strings
2. ✅ Counter shows 0 (alerts array likely empty or filtered incorrectly)
3. ✅ Agent names not displaying (deployment or data issue)
4. ✅ EVERY action creates 2 duplicate alerts (database bug)
5. ✅ "Standalone" status confusing (should show approval status)

**Impact**: User sees generic "Immediate investigation required" instead of intelligent NIST/MITRE-based recommendations

---

## 🔍 EVIDENCE OF ISSUES

### **SMOKING GUN #1: Hardcoded Recommendations Override**

**File**: `AIAlertManagementSystem.jsx:200`
```javascript
const enrichedAlerts = data.map(alert => ({
  ...alert,
  correlation_id: null,
  threat_category: getRandomThreatCategory(),  // ❌ RANDOM!
  recommended_action: getRecommendedAction(alert.severity),  // ❌ HARDCODED!
  time_since: getTimeSince(alert.timestamp)
}));
```

**Function** (line 386):
```javascript
const getRecommendedAction = (severity) => {
  const actions = {
    "high": "Immediate investigation required",  // ❌ HARDCODED
    "medium": "Review within 4 hours",           // ❌ HARDCODED
    "low": "Monitor and analyze trends"          // ❌ HARDCODED
  };
  return actions[severity] || "Standard monitoring";
};
```

**What Database Has**:
```
"Restrict admin privileges for database_write operations related to processing customer
refunds to only authorized personnel. Implement multi-factor authentication and audit
logs to comply with NIST AU-9, reducing the risk of unauthorized or malicious activities."
```

**What User Sees**:
```
"Immediate investigation required"  // ❌ WORTHLESS!
```

---

### **SMOKING GUN #2: Random Threat Categories**

**Function** (line 381):
```javascript
const getRandomThreatCategory = () => {
  const categories = ["Malware", "Phishing", "DDoS", "APT", "Insider Threat", "Data Exfiltration"];
  return categories[Math.floor(Math.random() * categories.length)];  // ❌ RANDOM!
};
```

**Problem**: Same alert shows different threat category on each refresh!

---

### **SMOKING GUN #3: Duplicate Alerts**

**Database Evidence**:
```sql
SELECT action_id, COUNT(*) FROM alerts
WHERE agent_action_id IN (SELECT id FROM agent_actions WHERE status = 'pending')
GROUP BY action_id;
```

**Result**: EVERY action has exactly 2 alerts!
```
action_631: 2 alerts
action_630: 2 alerts
action_629: 2 alerts
action_628: 2 alerts
...
```

**Likely Cause**: Alert creation triggered twice (event handler bug or retry logic)

---

### **SMOKING GUN #4: Counter Shows 0**

**User Report**: "logged in and saw 0 agents alerts in the counter"

**Database Reality**:
```sql
SELECT COUNT(*) FROM alerts WHERE status = 'new';
-- Result: 24 alerts
```

**Possible Causes**:
1. API not returning data
2. Frontend `alerts` array empty
3. Filter logic broken

---

### **SMOKING GUN #5: Confusing Status**

**Current Display** (line 749):
```javascript
{alert.correlation_id ? '🔗 Correlated' : '⚪ Standalone'}
```

**Problems**:
- "Standalone" doesn't mean anything to users
- Should show approval status (pending/approved/rejected)
- correlation_id is always null (line 198), so ALWAYS shows "Standalone"

---

## 💡 ENTERPRISE SOLUTION

### **Phase 1: Remove Hardcoded Data Overrides** (CRITICAL - 5 minutes)

**File**: `owkai-pilot-frontend/src/components/AIAlertManagementSystem.jsx`

#### **Fix #1: Stop Overwriting Recommendations** (Line 196-202)

**BEFORE**:
```javascript
const enrichedAlerts = data.map(alert => ({
  ...alert,
  correlation_id: null,
  threat_category: getRandomThreatCategory(),  // ❌ DELETE
  recommended_action: getRecommendedAction(alert.severity),  // ❌ DELETE
  time_since: getTimeSince(alert.timestamp)
}));
```

**AFTER**:
```javascript
const enrichedAlerts = data.map(alert => ({
  ...alert,
  // 🏢 ENTERPRISE FIX (2025-11-19): Use REAL data from database
  // threat_category comes from MITRE tactic (already in API response)
  // recommended_action comes from AI engine (already in API response)
  time_since: getTimeSince(alert.timestamp)
}));
```

#### **Fix #2: Delete Hardcoded Functions** (Lines 381-393)

**DELETE ENTIRELY**:
```javascript
const getRandomThreatCategory = () => { ... };  // ❌ DELETE ALL
const getRecommendedAction = (severity) => { ... };  // ❌ DELETE ALL
```

#### **Fix #3: Use Real Fields in UI** (Line 743-746)

**BEFORE**:
```javascript
<span className="font-medium">Threat Category:</span> {alert.threat_category}
<span className="font-medium">Recommended Action:</span> {alert.recommended_action}
```

**AFTER**:
```javascript
{/* 🏢 Use REAL MITRE tactic instead of random category */}
<span className="font-medium">MITRE Tactic:</span> {alert.mitre_tactic || 'Not Classified'}

{/* 🏢 Use REAL AI recommendation from database */}
<span className="font-medium">Recommended Action:</span> {alert.recommendation || 'Under review'}
```

**Why This Works**:
- Backend already returns `mitre_tactic` from agent_actions table
- Backend already returns `recommendation` from agent_actions table
- Just need to USE the fields instead of overwriting them!

---

### **Phase 2: Fix Duplicate Alerts** (HIGH - 15 minutes)

**Problem**: Every action creates 2 alerts

**Investigation Steps**:
1. Find alert creation code
2. Check for duplicate event handlers
3. Check for retry logic

**Files to Check**:
- `routes/agent_routes.py` - Agent action creation
- `services/*.py` - Alert creation service
- Event handlers/webhooks

**Likely Fix**:
Add idempotency check before creating alert:
```python
# Before creating alert
existing_alert = db.query(Alert).filter(
    Alert.agent_action_id == action_id,
    Alert.alert_type == "High Risk Agent Action"
).first()

if existing_alert:
    logger.warning(f"Alert already exists for action {action_id}, skipping creation")
    return existing_alert

# Create alert only if doesn't exist
alert = Alert(
    agent_action_id=action_id,
    ...
)
```

---

### **Phase 3: Fix Counter Display** (MEDIUM - 10 minutes)

**Issue**: Counter shows 0 instead of 24 active alerts

**Debugging Steps**:
1. Check what API returns: `curl https://pilot.owkai.app/api/alerts`
2. Check browser console: `console.log("Alerts:", alerts)`
3. Check filter logic: `console.log("Filtered:", filteredAlerts)`

**Possible Fixes**:

**Option A**: API not being called
```javascript
useEffect(() => {
  fetchAlerts();  // Make sure this is called on mount
}, []);
```

**Option B**: Status mismatch
```javascript
// Current filter
alerts.filter(a => a.status === "new" || !a.status)

// If API returns different status, adjust:
alerts.filter(a => !a.status || a.status === "new" || a.status === "pending")
```

**Option C**: Alerts array empty
```javascript
// Add defensive check
{(alerts && alerts.length > 0) ? (
  alerts.filter(a => a.status === "new").length
) : 0}
```

---

### **Phase 4: Fix Status Display** (LOW - 5 minutes)

**File**: `AIAlertManagementSystem.jsx:749`

**BEFORE**:
```javascript
<span className="font-medium">Status:</span>
{alert.correlation_id ? '🔗 Correlated' : '⚪ Standalone'}
```

**AFTER - Option 1** (Show approval status):
```javascript
<span className="font-medium">Approval Status:</span>
{alert.status === 'new' ? '⏳ Pending Review' :
 alert.status === 'acknowledged' ? '✅ Acknowledged' :
 alert.status === 'escalated' ? '🚨 Escalated' :
 '⚪ ' + (alert.status || 'New')}
```

**AFTER - Option 2** (Remove correlation entirely):
```javascript
{/* Correlation feature not used, remove from UI */}
```

---

### **Phase 5: Fix Agent/MCP Name Display** (MEDIUM - 10 minutes)

**Issue**: Names not showing despite backend fix

**Debugging**:
1. Check Task Definition 500 is actually running
2. Check API response includes `agent_name` field
3. Check frontend receives field

**Test**:
```bash
TOKEN="<your-token>"
curl -s "https://pilot.owkai.app/api/alerts" -H "Authorization: Bearer $TOKEN" | jq '.[0] | {id, agent_name, mcp_server_name}'
```

**Expected**:
```json
{
  "id": 510,
  "agent_name": "payment-processor-agent",
  "mcp_server_name": null
}
```

**If Missing**:
- Backend not deployed correctly
- Regex not matching message format
- API endpoint returning old data

**Fix**: Verify deployment, re-deploy if needed

---

## 🎯 IMPLEMENTATION PRIORITY

### **CRITICAL - DO FIRST** (5 minutes):
1. Remove `getRecommendedAction()` override (line 200)
2. Remove `getRandomThreatCategory()` override (line 199)
3. Delete both functions (lines 381-393)
4. Update UI to use `alert.recommendation` and `alert.mitre_tactic`

**Impact**: User immediately sees REAL AI recommendations instead of garbage

### **HIGH - DO TODAY** (25 minutes):
5. Fix duplicate alert creation bug (add idempotency check)
6. Debug counter showing 0 (check API response)
7. Verify agent_name deployment (check Task Def 500)

### **MEDIUM - DO THIS WEEK** (5 minutes):
8. Fix "Standalone" status display (show approval status instead)

---

## 📊 EXPECTED RESULTS AFTER FIX

### **Before**:
```
Threat Category: DDoS (random, changes on refresh)
Recommended Action: Immediate investigation required
Status: ⚪ Standalone
Agent: <not shown>
```

### **After**:
```
MITRE Tactic: Impact
Recommended Action: Implement strict access controls limiting admin privileges for
  database_read actions related to financial transactions, in alignment with NIST
  control AU-9. Regularly monitor and audit admin activities...
Approval Status: ⏳ Pending Review
Agent: 🤖 payment-processor-agent
```

---

## 🔧 DEPLOYMENT STRATEGY

### **Frontend-Only Fixes** (Phases 1, 4, 5):
1. Edit `AIAlertManagementSystem.jsx`
2. Commit to main branch
3. Railway auto-deploys
4. Hard refresh browser (Ctrl+Shift+R)

**Time**: 5 minutes

### **Backend Fix** (Phase 2 - Duplicate Alerts):
1. Find alert creation code
2. Add idempotency check
3. Commit to master branch
4. GitHub Actions deploys to ECS
5. Wait for Task Definition 501

**Time**: 20 minutes

### **Debugging** (Phase 3 - Counter):
1. Check browser console
2. Check network tab
3. Apply specific fix based on findings

**Time**: 10 minutes

---

## 🚀 RISK ASSESSMENT

### **Phase 1** (Remove hardcoded overrides):
- **Risk**: ZERO (removing bad code)
- **Impact**: CRITICAL (fixes main user complaint)
- **Rollback**: Revert commit

### **Phase 2** (Fix duplicate alerts):
- **Risk**: LOW (additive check only)
- **Impact**: HIGH (reduces database clutter)
- **Rollback**: Remove idempotency check

### **Phase 3** (Debug counter):
- **Risk**: DEPENDS (TBD after investigation)
- **Impact**: HIGH (user sees correct counts)
- **Rollback**: DEPENDS

### **Phase 4** (Fix status display):
- **Risk**: ZERO (UI-only change)
- **Impact**: MEDIUM (better UX)
- **Rollback**: Revert commit

---

## 📝 SUCCESS CRITERIA

✅ **Recommendations Fixed**:
- Alert cards show full AI-generated recommendations (200+ characters)
- No more "Immediate investigation required" generic text

✅ **Threat Categories Fixed**:
- Shows real MITRE tactic (Impact, Execution, etc.)
- No more random categories changing on refresh

✅ **Counter Fixed**:
- Shows correct count of active alerts (24, not 0)

✅ **Agent Names Fixed**:
- Purple badges showing "🤖 Agent: payment-processor-agent"

✅ **Duplicate Alerts Fixed**:
- Each action has exactly 1 alert (not 2)

✅ **Status Fixed**:
- Shows approval status (not correlation status)

---

## 🎯 RECOMMENDATION

**Approve Phase 1 immediately** (5 minutes):
- Zero risk
- Critical impact
- Fixes main user complaint
- No deployment needed (frontend only)

**Approve Phase 2 after investigation** (20 minutes):
- Low risk
- High impact
- Requires finding alert creation code first

**Approve Phases 3-4 as needed** (15 minutes):
- Medium priority
- Can be done after Phase 1

---

**Status**: AWAITING APPROVAL ⏳
**Recommendation**: START WITH PHASE 1 NOW
