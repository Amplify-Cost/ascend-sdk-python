# 🔍 AI Alert Management - Critical Issues Investigation

**Date**: 2025-11-19
**Status**: EVIDENCE GATHERED
**Priority**: HIGH

---

## 📋 USER REPORTS

### **Issue #1**: Counter Shows 0 Active Alerts
**User**: "logged in and saw 0 agents alerts in the counter"
**Expected**: Should show count of active alerts
**Actual**: Shows 0

### **Issue #2**: Agent/MCP Names Not Displaying
**User**: "i still dont see the name/id of the agent/mcp server who made the action"
**Expected**: Agent names visible in alert cards
**Actual**: Names not showing

### **Issue #3**: Hardcoded Recommendations
**User**: "recommended action appears to be demo or hardcoded data"
**Expected**: AI-generated recommendations based on NIST/MITRE
**Actual**: Generic hardcoded messages like "Immediate investigation required"

### **Issue #4**: Standalone Status Unclear
**User**: "status says standalone explain that feature"
**Expected**: User understands what "standalone" means
**Actual**: Confusing UI term

### **Issue #5**: Alert/Action Count Mismatch
**User**: "i see 5 pending actions in the authorization center... while i only see the same 4 alerts"
**Expected**: 1 alert per pending action
**Actual**: Missing alert for 1 action

### **Issue #6**: Duplicate NIST/MITRE Mappings
**User**: "all scores being 86 with one being 89 but they have the same nist mitre mappings"
**Expected**: Different actions have different controls
**Actual**: Multiple actions showing same AU-9 control

---

## 🔍 EVIDENCE GATHERED

### **Database State** (Production)

#### **Actions vs Alerts Count**:
```sql
-- Pending actions
SELECT COUNT(*) FROM agent_actions WHERE status = 'pending';
-- Result: 3 actions (IDs: 615, 616, 617 - OLD DATA)
-- Result: 3 actions (IDs: 618, 619, 620 - NEW DATA)

-- Alerts for these actions
SELECT COUNT(*) FROM alerts WHERE agent_action_id IN (615, 616, 617);
-- Result: 4 alerts (two alerts for action 616)
```

**FINDING #1**: Action 616 has **2 alerts** (ID 509 and 510)
- Alert 509: status='acknowledged'
- Alert 510: status='new'
- This is DUPLICATE alert creation bug

**FINDING #2**: Latest pending actions (618, 619, 620) have **NO alerts**
- Authorization Center shows 5 pending (3 old + 2 new that became pending recently)
- AI Alert Management shows only 4 alerts (from old actions)
- **Root Cause**: Alert creation is NOT automatic for all actions

#### **Alert Status Distribution**:
```sql
SELECT COUNT(*) as total, status FROM alerts GROUP BY status;
```
Result:
- **24 alerts**: status = 'new' (should show as "active")
- **416 alerts**: status = 'acknowledged'
- **1 alert**: status = 'escalated'

**FINDING #3**: 24 active alerts exist in database, but counter shows 0

#### **Agent Names in Alerts**:
```sql
SELECT id, message FROM alerts WHERE status = 'new' LIMIT 2;
```
Result:
```
ID 510: "Enterprise Alert: Agent payment-processor-agent performed high-risk action: database_read"
ID 508: "Enterprise Alert: Agent support-ticket-agent performed high-risk action: database_write"
```

**FINDING #4**: Agent names ARE in message text, regex should extract them

#### **Recommendations in Database**:
```sql
SELECT recommendation FROM agent_actions WHERE id = 615;
```
Result:
```
"Restrict admin privileges for database_write operations related to processing customer
refunds to only authorized personnel. Implement multi-factor authentication and audit
logs to comply with NIST AU-9, reducing the risk of unauthorized or malicious activities."
```

**FINDING #5**: Database HAS real AI-generated recommendations (not hardcoded)

---

## 🐛 ROOT CAUSES IDENTIFIED

### **Issue #1: Counter Shows 0**
**File**: `AIAlertManagementSystem.jsx:665`
**Code**:
```javascript
{alerts.filter(a => a.status === "new" || !a.status).length}
```

**Problem**: This code is CORRECT, so issue must be:
1. `alerts` array is empty (API not returning data)
2. API returning data but frontend filter not working
3. Status field mismatch

**Evidence Needed**: Check what API actually returns

---

### **Issue #2: Agent Names Not Showing**
**File**: `alert_routes.py:30-44`
**Code**:
```python
agent_match = re.search(r'Agent\s+([a-z0-9\-]+)\s+performed', alert.message, re.IGNORECASE)
if agent_match:
    agent_name = agent_match.group(1)
```

**Test Against Real Data**:
```
Message: "Enterprise Alert: Agent payment-processor-agent performed high-risk action: database_read"
Regex: r'Agent\s+([a-z0-9\-]+)\s+performed'
```

**Problem**: Regex should match, BUT check if:
1. Backend deployed correctly (Task Def 500)
2. API actually returning agent_name field
3. Frontend receiving and displaying field

---

### **Issue #3: Hardcoded Recommendations**
**File**: `AIAlertManagementSystem.jsx:386-393`

**SMOKING GUN**:
```javascript
const getRecommendedAction = (severity) => {
  const actions = {
    "high": "Immediate investigation required",  // ❌ HARDCODED!
    "medium": "Review within 4 hours",           // ❌ HARDCODED!
    "low": "Monitor and analyze trends"          // ❌ HARDCODED!
  };
  return actions[severity] || "Standard monitoring";
};
```

**Usage** (line 200):
```javascript
recommended_action: getRecommendedAction(alert.severity),  // ❌ OVERWRITES REAL DATA!
```

**ROOT CAUSE**: Frontend OVERWRITES database recommendations with hardcoded strings!

**Database Has**:
```
"Restrict admin privileges for database_write operations related to processing customer
refunds to only authorized personnel. Implement multi-factor authentication..."
```

**Frontend Shows**:
```
"Immediate investigation required"  // ❌ GENERIC GARBAGE
```

---

### **Issue #4: Standalone Status Confusing**
**File**: `AIAlertManagementSystem.jsx:749`

**Code**:
```javascript
<span className="font-medium">Status:</span>
{alert.correlation_id ? '🔗 Correlated' : '⚪ Standalone'}
```

**Meaning**:
- **Standalone**: Alert has NOT been correlated with other alerts (correlation_id = null)
- **Correlated**: Alert is part of a group (correlation_id = some_id)

**Problem**: "Standalone" is confusing terminology
- User expects to see approval status (pending/approved/rejected)
- Instead sees correlation status (standalone/correlated)

**Current Behavior**:
- All alerts have `correlation_id = null` (set in line 198)
- So ALL alerts show "⚪ Standalone"
- This provides ZERO useful information

---

### **Issue #5: Alert/Action Mismatch**
**Evidence**:
- Action 616: Has 2 alerts (duplicate bug)
- Actions 618, 619, 620: Have 0 alerts (missing creation)

**Root Cause #1**: Duplicate alert creation
- System creates multiple alerts for same action
- Likely triggered by retries or event handling

**Root Cause #2**: Missing alert creation
- New actions (618, 619, 620) don't have alerts
- Alert creation is NOT automatic
- Likely triggered manually or by specific conditions

---

### **Issue #6: Duplicate NIST/MITRE**
**Evidence**:
```
Action 615: risk_score=89, NIST=AU-9, MITRE=TA0040
Action 616: risk_score=86, NIST=AU-9, MITRE=Impact
Action 618: risk_score=86, NIST=?, MITRE=?
```

**Problem**: Multiple database actions share same NIST control (AU-9)
- This is CORRECT behavior (multiple actions can violate same control)
- BUT: MITRE tactics should be more specific

**Root Cause**: NIST/MITRE mapping is too coarse-grained
- AU-9 = "Protection of Audit Information"
- Multiple database actions correctly map to AU-9
- MITRE mapping needs refinement (TA0040 vs Impact)

---

## 📊 SUMMARY OF FINDINGS

| Issue | Root Cause | Severity | Location |
|-------|-----------|----------|----------|
| Counter shows 0 | API not returning data OR frontend not receiving | HIGH | Frontend |
| Agent names missing | Deployment issue OR API not returning field | HIGH | Backend/Frontend |
| Hardcoded recommendations | Frontend overwrites DB recommendations | CRITICAL | Frontend line 200 |
| Standalone status confusing | Poor UI terminology for correlation feature | MEDIUM | Frontend line 749 |
| Alert/Action mismatch | Duplicate alerts + missing alert creation | HIGH | Backend alert creation |
| Duplicate NIST mappings | Coarse-grained control mapping (correct behavior) | LOW | Policy engine |

---

## 🎯 CRITICAL FIX PRIORITIES

### **P0 - CRITICAL (Must Fix Immediately)**:
1. ✅ Remove `getRecommendedAction()` override - use database recommendations
2. ✅ Remove `getRandomThreatCategory()` - use real MITRE tactics

### **P1 - HIGH (Fix Today)**:
3. ✅ Investigate why counter shows 0 (check API response)
4. ✅ Investigate why agent_name not displaying (verify deployment)
5. ✅ Fix duplicate alert creation bug
6. ✅ Implement automatic alert creation for all high-risk actions

### **P2 - MEDIUM (Fix This Week)**:
7. ✅ Replace "Standalone" with "Uncorrelated" or remove entirely
8. ✅ Show actual approval status (pending/approved/rejected)

---

**Status**: READY FOR ENTERPRISE SOLUTION PLAN
