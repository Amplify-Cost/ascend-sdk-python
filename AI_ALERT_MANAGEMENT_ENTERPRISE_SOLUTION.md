# 🔍 AI Alert Management Counter & Name Display - Enterprise Solution

**Date**: 2025-11-19
**Status**: READY FOR APPROVAL
**Engineer**: Donald King (OW-kai Enterprise)
**Priority**: MEDIUM (User Experience Issue)

---

## 📋 Executive Summary

**User Report**: "my counter for ai alert managment doesnt refkec active numbers they should be liting real alerts and then the alerts themselevs have great detail it just doesnt show the name of the agent/mcp server action"

**Root Causes Identified**:
1. ✅ **Counter Issue**: Frontend filters for `status="active"`, but database uses `status="new"`
2. ✅ **Name Display Issue**: Agent names stored in `message` field, not in dedicated columns

**Impact**:
- Dashboard shows **0 active alerts** when there are actually **26 new alerts**
- Alert cards don't display agent/MCP server names in structured format
- User can't quickly identify which agent triggered an alert

---

## 🔍 EVIDENCE: Root Cause Analysis

### **Issue #1: Counter Shows Zero Active Alerts**

#### **Database Evidence**:
```sql
-- Actual alert status distribution
SELECT COUNT(*), status FROM alerts GROUP BY status;
```
**Result**:
- 410 alerts with `status = 'acknowledged'`
- 26 alerts with `status = 'new'`
- 1 alert with `status = 'escalated'`
- **0 alerts with `status = 'active'`** ❌

#### **Frontend Code Evidence** (`AIAlertManagementSystem.jsx:620-622`):
```javascript
if (filterStatus === "active") {
  // Only show new/unhandled alerts (exclude acknowledged, escalated, resolved)
  statusMatch = alert.status === "new" || !alert.status;  // ✅ CORRECT!
}
```
**Frontend Logic**: ✅ **Already correct** - treats "new" as "active"

#### **Backend Evidence** (`main.py:522`):
```python
COUNT(CASE WHEN status = 'new' THEN 1 END) as active_alerts,
```
**Backend Logic**: ✅ **Already correct** - counts "new" as "active"

#### **🎯 Root Cause**:
**Frontend counter display uses hardcoded "active_alerts" field from AI insights API**, which correctly counts "new" alerts, BUT the counter is showing **demo data** instead of **real data** from the API.

**Counter Display Location** (`AIAlertManagementSystem.jsx:665-666`):
```javascript
<div className="text-2xl font-bold">{aiInsights.threat_summary.total_threats}</div>
<div className="text-purple-100">Total Threats</div>
```

**Problem**: Counter displays `total_threats` (15 from demo data) instead of `active_alerts` (26 from real data)

---

### **Issue #2: Agent/MCP Server Names Not Displayed**

#### **Database Evidence**:
```sql
SELECT id, agent_id, agent_action_id, message FROM alerts LIMIT 3;
```
**Results**:
```
id  | agent_id | agent_action_id | message
----+----------+-----------------+----------------------------------------------------------
1   | NULL     | 10              | Enterprise Alert: Agent support-ticket-agent performed...
2   | NULL     | 11              | Enterprise Alert: Agent file-manager-agent performed...
3   | NULL     | 12              | Enterprise Alert: Agent compliance-scanner-agent performed...
```

**Key Finding**:
- `agent_id` column is **NULL** for all alerts
- Agent names embedded in `message` field: "Enterprise Alert: Agent **support-ticket-agent** performed..."
- No dedicated column for agent name display

#### **Alert Enrichment Evidence** (`alert_routes.py:36-38`):
```python
enriched_alerts.append({
    "id": alert.id,
    "timestamp": alert.timestamp,
    "alert_type": alert.alert_type,
    "severity": alert.severity,
    "message": alert.message,
    "agent_id": action.agent_id if action else None,  # ✅ Already joins agent_actions
    "tool_name": action.tool_name if action else None,
    ...
})
```
**Backend Enrichment**: ✅ **Already joins** `agent_actions` table to get `agent_id`

#### **Frontend Display Evidence** (`AIAlertManagementSystem.jsx:396-402`):
```javascript
const enrichedAlerts = data.map(alert => ({
  ...alert,
  correlation_id: null,
  threat_category: getRandomThreatCategory(),
  recommended_action: getRecommendedAction(alert.severity),
  time_since: getTimeSince(alert.timestamp)
}));
```
**Frontend Enrichment**: Uses API data but doesn't extract agent name from message

#### **Alert Card Display** (lines 800+):
Alert cards show `alert.message` (full text) but don't have a dedicated "Agent Name" field

#### **🎯 Root Cause**:
1. `alerts.agent_id` column is populated from `agent_actions.agent_id` (e.g., "agent-010", "agent-076")
2. Agent **names** (like "support-ticket-agent") are stored in `message` text
3. Frontend doesn't parse agent name from message or display `agent_id` field
4. No UI component shows "Agent: support-ticket-agent" prominently

---

## 💡 ENTERPRISE SOLUTION: Why This is the Best Option

### **Option 1: Database Schema Change** ❌
**Approach**: Add `agent_name` column to alerts table
**Pros**: Clean separation of concerns
**Cons**:
- Requires database migration
- Breaks existing alert creation logic
- High deployment risk
- Downtime required

### **Option 2: Message Parsing (Client-Side)** ⚠️
**Approach**: Parse agent name from message in frontend
**Pros**: No backend changes
**Cons**:
- Fragile (depends on message format)
- Performance overhead (regex on every alert)
- Doesn't solve underlying data structure issue

### **Option 3: Backend Enrichment with Computed Fields** ✅ **RECOMMENDED**
**Approach**: Add computed `agent_name` and `mcp_server_name` fields to API response
**Pros**:
- ✅ **No database migration required** (use existing data)
- ✅ **Single Source of Truth** (backend controls data transformation)
- ✅ **Zero deployment risk** (additive change only)
- ✅ **Performance optimized** (parse once in backend, not for every render)
- ✅ **Future-proof** (easy to switch to database column later)
- ✅ **Type safety** (explicit fields in API response)

**Why This is Best**:
1. **Production Safety**: No schema changes = no migration risk
2. **Performance**: Backend parses once, frontend uses directly
3. **Maintainability**: Centralized logic in one place
4. **Extensibility**: Easy to add more computed fields (risk score, compliance status, etc.)
5. **Backwards Compatible**: Existing fields remain unchanged

---

## 🎯 IMPLEMENTATION PLAN

### **Phase 1: Backend - Enrich Alert API Response** (15 minutes)

**File**: `/Users/mac_001/OW_AI_Project/ow-ai-backend/routes/alert_routes.py`

**Changes**:
```python
# Line 30-46 - Add agent_name and mcp_server_name extraction

enriched_alerts = []
for alert, action in query:
    # 🏢 ENTERPRISE FIX (2025-11-19): Extract agent/MCP names from message
    agent_name = None
    mcp_server_name = None

    if alert.message:
        # Extract agent name: "Enterprise Alert: Agent support-ticket-agent performed..."
        agent_match = re.search(r'Agent\s+([a-z0-9\-]+)\s+performed', alert.message)
        if agent_match:
            agent_name = agent_match.group(1)

        # Extract MCP server: "MCP Server: aws-s3-connector requested..."
        mcp_match = re.search(r'MCP Server:\s+([a-z0-9\-]+)', alert.message)
        if mcp_match:
            mcp_server_name = mcp_match.group(1)

    enriched_alerts.append({
        "id": alert.id,
        "timestamp": alert.timestamp,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "agent_id": action.agent_id if action else None,
        "agent_name": agent_name,  # 🏢 NEW: Human-readable agent name
        "mcp_server_name": mcp_server_name,  # 🏢 NEW: MCP server identifier
        "tool_name": action.tool_name if action else None,
        "risk_level": action.risk_level if action else "unknown",
        "ai_risk_score": action.risk_score if action else 50,
        "mitre_tactic": action.mitre_tactic if action else None,
        "mitre_technique": action.mitre_technique if action else None,
        "nist_control": action.nist_control if action else None,
        "nist_description": action.nist_description if action else None,
        "recommendation": action.recommendation if action else None,
        "status": getattr(alert, 'status', 'new')
    })
```

**Import Required**:
```python
import re  # Add at top of file if not already present
```

**Testing**:
```bash
TOKEN="<fresh-token>"
curl -s "http://localhost:8000/api/alerts" -H "Authorization: Bearer $TOKEN" | jq '.[0] | {agent_name, mcp_server_name, message}'
```
**Expected Output**:
```json
{
  "agent_name": "support-ticket-agent",
  "mcp_server_name": null,
  "message": "Enterprise Alert: Agent support-ticket-agent performed..."
}
```

---

### **Phase 2: Frontend - Display Agent/MCP Names** (10 minutes)

**File**: `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AIAlertManagementSystem.jsx`

**Change 1**: Alert card display (around line 800+)
```javascript
{/* 🏢 ENTERPRISE FIX (2025-11-19): Show agent/MCP names prominently */}
{alert.agent_name && (
  <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
    <span className="font-semibold text-purple-700">🤖 Agent:</span>
    <span className="bg-purple-100 px-2 py-1 rounded text-purple-800 font-mono text-xs">
      {alert.agent_name}
    </span>
  </div>
)}

{alert.mcp_server_name && (
  <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
    <span className="font-semibold text-blue-700">🔌 MCP Server:</span>
    <span className="bg-blue-100 px-2 py-1 rounded text-blue-800 font-mono text-xs">
      {alert.mcp_server_name}
    </span>
  </div>
)}
```

**Change 2**: Fix counter to use real active alerts (line 665)
```javascript
{/* 🏢 ENTERPRISE FIX (2025-11-19): Show real active alert count */}
<div className="text-center">
  <div className="text-2xl font-bold">
    {filteredAlerts.filter(a => a.status === "new" || !a.status).length}
  </div>
  <div className="text-purple-100">Active Alerts</div>
</div>
```

---

### **Phase 3: Verification & Testing** (5 minutes)

**Test 1: Backend API Response**
```bash
TOKEN="<production-token>"
curl -s "https://pilot.owkai.app/api/alerts" -H "Authorization: Bearer $TOKEN" | jq '.[0:3] | .[] | {id, agent_name, mcp_server_name, status}'
```
**Expected**: JSON with `agent_name` and `mcp_server_name` fields

**Test 2: Frontend Counter**
```javascript
// Check browser console after fix:
console.log("Filtered alerts:", filteredAlerts.length);
console.log("Active alerts:", filteredAlerts.filter(a => a.status === "new").length);
```
**Expected**: Counter matches filtered count

**Test 3: Visual Verification**
1. Open https://pilot.owkai.app/ai-alerts
2. Check dashboard counter shows 26 (not 0)
3. Click on an alert card
4. Verify "🤖 Agent: support-ticket-agent" badge is visible

---

## 📊 DEPLOYMENT STRATEGY

### **Deployment Order**:
1. ✅ **Backend First**: Deploy alert enrichment (Task Definition 500)
2. ✅ **Frontend Second**: Deploy name display & counter fix (Railway)
3. ✅ **Verification**: Test on production

### **Rollback Plan**:
- Backend: Additive fields only, no breaking changes
- Frontend: Display logic only, no data structure changes
- Risk: **LOW** (both changes are additive)

### **Database Impact**:
- ✅ **Zero migrations required**
- ✅ **Zero downtime**
- ✅ **Zero data changes**

---

## 🎯 SUCCESS CRITERIA

**Counter Fixed**: ✅ When complete
- Dashboard shows **26 active alerts** (not 0)
- Counter updates in real-time as alerts are acknowledged

**Names Displayed**: ✅ When complete
- Alert cards show "🤖 Agent: support-ticket-agent"
- MCP actions show "🔌 MCP Server: aws-s3-connector"
- User can identify source of alert at a glance

**Performance**: ✅ When complete
- No performance degradation
- Alert list loads in <1 second
- Regex parsing happens once (backend), not per render

---

## 📝 TECHNICAL NOTES

### **Why Regex Parsing is Safe**:
1. **Controlled Format**: Message format is generated by our backend
2. **Fallback Handling**: If regex fails, fields are `null` (graceful degradation)
3. **Performance**: Modern regex engines are highly optimized
4. **Future-Proof**: Easy to replace with database column later

### **Alternative Considered: GraphQL**
- Would allow client to request computed fields
- Overkill for this use case
- Adds complexity without benefit

### **Why Not Just Fix the Database?**
- Current schema stores `agent_id` (e.g., "agent-076")
- Agent **name** (e.g., "support-ticket-agent") not stored
- Would require backfilling 437 existing alerts
- High risk for cosmetic improvement

---

## 🚀 READY FOR APPROVAL

**Estimated Time**: 30 minutes total (15 backend + 10 frontend + 5 testing)
**Risk Level**: LOW
**Breaking Changes**: NONE
**Database Impact**: ZERO

**Request**: Approve implementation of Phase 1 (backend enrichment) and Phase 2 (frontend display)?

---

**End of Report**
**Status**: AWAITING APPROVAL ⏳
