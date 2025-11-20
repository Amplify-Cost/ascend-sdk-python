# Activity Tab - Enterprise Fix Plan
**Date:** 2025-11-12
**Based On:** ACTIVITY_TAB_COMPREHENSIVE_AUDIT.md
**Approach:** Pragmatic, enterprise-grade, production-ready

---

## Recommendation: **Option C - Hybrid Approach** ✅

**Why Hybrid:**
1. **Fastest Time to Working State** - 1 day vs 2-3 days
2. **Iterative Value Delivery** - Get UI working first, enrich data later
3. **Risk Mitigation** - Separate deployment concerns from feature complexity
4. **Enterprise-Grade UI Now** - Users see professional interface immediately
5. **Business Continuity** - Doesn't block other development

**What User Gets Today:**
- ✅ Enterprise UI with all 39 fields displayed
- ✅ Graceful handling of NULL data ("No CVSS data available" instead of broken UI)
- ✅ All buttons functional (false positive, support, file upload)
- ✅ Proper timestamps and field names
- ⏳ CVSS/MITRE/NIST scoring deferred to Phase 2 (separate project)

---

## Phase 1: Core Functionality Fixes (TODAY)

### Fix 1: Deploy Backend Schema Changes ⚠️ **BLOCKING**

**Issue:** Production backend not running updated code with 39-field schema

**Solution:**
```bash
# Option A: Verify AWS ECS auto-deployment (if configured)
aws ecs describe-services --cluster [cluster-name] --services [service-name]

# Option B: Manual Docker deployment (if auto-deploy broken)
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
docker build -t owkai-pilot-backend:latest .
docker tag owkai-pilot-backend:latest [ECR_URI]:latest
aws ecr get-login-password | docker login --username AWS --password-stdin [ECR_URI]
docker push [ECR_URI]:latest
aws ecs update-service --cluster [cluster] --service [service] --force-new-deployment
```

**Files Changed:** None (already committed as db01442c)

**Testing:**
```bash
curl "https://pilot.owkai.app/api/agent-activity" | jq '.[0] | keys | length'
# Expected: 39 (currently: 6)
```

**Time Estimate:** 30 minutes (if auto-deploy works) or 1 hour (if manual)

---

### Fix 2: Create Missing Backend Endpoints 🔴 **CRITICAL**

**Issue:** 3 of 3 interactive buttons return 404 Not Found

#### Endpoint 1: False Positive Toggle
**Frontend calls:** `POST /api/agent-action/false-positive/{id}`

**Backend implementation:**
```python
# File: ow-ai-backend/routes/agent_routes.py
# Add after existing @router endpoints (around line 450)

@router.post("/agent-action/false-positive/{action_id}")
def toggle_false_positive(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Toggle false positive flag on an agent action - Enterprise audit trail"""
    try:
        action = db.query(AgentAction).filter(AgentAction.id == action_id).first()

        if not action:
            raise HTTPException(status_code=404, detail=f"Agent action {action_id} not found")

        # Toggle false positive status
        action.is_false_positive = not (action.is_false_positive or False)
        action.reviewed_by = current_user.get("email", "unknown")
        action.reviewed_at = datetime.now(UTC)
        action.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(action)

        return {
            "message": f"Action {action_id} marked as {'FALSE POSITIVE' if action.is_false_positive else 'VALID'}",
            "action_id": action_id,
            "is_false_positive": action.is_false_positive,
            "reviewed_by": action.reviewed_by
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle false positive: {str(e)}")
```

---

#### Endpoint 2: Support Submit
**Frontend calls:** `POST /api/support/submit`

**Backend implementation:**
```python
# File: ow-ai-backend/routes/agent_routes.py OR create routes/support_routes.py

@router.post("/support/submit")
def submit_support_request(
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit support request - Enterprise ticketing integration ready"""
    try:
        message = request.get("message", "").strip()

        if not message or len(message) < 10:
            raise HTTPException(status_code=400, detail="Support message must be at least 10 characters")

        # Log to database (create support_tickets table or use audit_logs)
        support_ticket = {
            "user_id": current_user.get("user_id"),
            "user_email": current_user.get("email"),
            "message": message,
            "timestamp": datetime.now(UTC),
            "status": "open",
            "priority": "medium"
        }

        # TODO: Integrate with Zendesk, ServiceNow, or JIRA
        # For now, log to audit_logs table
        audit_log = AuditLog(
            user_id=current_user.get("user_id"),
            action_type="support_ticket_created",
            details=json.dumps(support_ticket),
            timestamp=datetime.now(UTC),
            ip_address="system"
        )
        db.add(audit_log)
        db.commit()

        return {
            "message": "Support request submitted successfully",
            "ticket_id": audit_log.id,
            "status": "open"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit support request: {str(e)}")
```

---

#### Endpoint 3: JSON File Upload
**Frontend calls:** `POST /api/agent-actions/upload-json`

**Backend implementation:**
```python
# File: ow-ai-backend/routes/agent_routes.py

@router.post("/agent-actions/upload-json")
async def upload_agent_actions_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload agent actions from JSON file - Enterprise bulk import"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        # Read and parse JSON
        contents = await file.read()
        try:
            actions_data = json.loads(contents)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        # Ensure it's a list
        if not isinstance(actions_data, list):
            actions_data = [actions_data]

        imported_count = 0
        skipped_count = 0
        errors = []

        for idx, action_data in enumerate(actions_data):
            try:
                # Create agent action
                action = AgentAction(
                    agent_id=action_data.get("agent_id", "imported"),
                    action_type=action_data.get("action_type", "imported_action"),
                    description=action_data.get("description"),
                    tool_name=action_data.get("tool_name"),
                    risk_level=action_data.get("risk_level"),
                    status=action_data.get("status", "imported"),
                    user_id=current_user.get("user_id"),
                    timestamp=datetime.now(UTC),
                    created_at=datetime.now(UTC)
                )
                db.add(action)
                imported_count += 1

            except Exception as e:
                skipped_count += 1
                errors.append(f"Row {idx}: {str(e)}")

        db.commit()

        return {
            "message": f"Import completed: {imported_count} imported, {skipped_count} skipped",
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors[:10]  # Return first 10 errors only
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

**Dependencies to Add:**
```python
# At top of agent_routes.py
from fastapi import UploadFile, File
import json
```

**Time Estimate:** 2-3 hours to implement all 3 endpoints

---

### Fix 3: Handle NULL Data Gracefully in Frontend

**Issue:** Frontend shows "No CVSS", "Unknown", "Invalid Date" for NULL fields

**Solution:** Update helper functions to handle NULL elegantly

**File:** `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AgentActivityFeed.jsx`

**Changes:**
```javascript
// Line 132-149: Update CVSS badge helper
const getCVSSBadge = (activity) => {
  const score = activity.cvss_score;
  const severity = activity.cvss_severity;

  if (score === null || score === undefined) {
    return (
      <span className="px-2 py-1 text-xs rounded-md bg-gray-100 text-gray-600 border border-gray-300">
        No CVSS Data
      </span>
    );
  }

  const color = getRiskColor(score);
  return (
    <span
      className="px-2 py-1 text-xs font-semibold rounded-md"
      style={{
        backgroundColor: `${color}20`,
        color: color,
        border: `1px solid ${color}40`
      }}
    >
      {score.toFixed(1)} / 10.0 ({severity || 'UNKNOWN'})
    </span>
  );
};

// Line 151-163: Update risk level badge
const getRiskBadge = (riskLevel) => {
  if (!riskLevel) {
    return (
      <span className="px-2 py-1 text-xs rounded-md bg-gray-100 text-gray-600 border border-gray-300">
        No Risk Assessment
      </span>
    );
  }

  const level = riskLevel.toLowerCase();
  const color = getRiskColor(
    level === 'high' ? 7 : level === 'medium' ? 5 : level === 'low' ? 2 : 0
  );
  return (
    <span
      className="px-2 py-1 text-xs font-semibold rounded-md"
      style={{
        backgroundColor: `${color}20`,
        color: color,
        border: `1px solid ${color}40`
      }}
    >
      {riskLevel}
    </span>
  );
};

// Line 265-267: Update timestamp formatting
{activity.timestamp ? (
  new Date(activity.timestamp).toLocaleString()
) : (
  <span className="text-gray-500 text-xs">No timestamp</span>
)}

// Line 275: Update action_type display
<p className="text-sm text-gray-900 mt-1">{activity.action_type || 'No action type'}</p>

// Line 279: Update tool_name display
<p className="text-sm text-gray-900 mt-1">{activity.tool_name || 'No tool specified'}</p>
```

**Time Estimate:** 30 minutes

---

### Fix 4: Add Loading/Success/Error States for Buttons

**Issue:** Buttons have no feedback when clicked

**Solution:** Add toast notifications or inline status messages

**File:** `/Users/mac_001/OW_AI_Project/owkai-pilot-frontend/src/components/AgentActivityFeed.jsx`

**Changes:**
```javascript
// Add state for button feedback
const [actionStatus, setActionStatus] = useState({});

// Update toggleFalsePositive (Line 68-79)
const toggleFalsePositive = async (id) => {
  setActionStatus({ [id]: 'loading' });
  try {
    const res = await fetch(`${API_BASE_URL}/api/agent-action/false-positive/${id}`, {
      credentials: "include",
      method: "POST",
      headers: getAuthHeaders(),
    });

    if (res.ok) {
      setActionStatus({ [id]: 'success' });
      fetchActivity();
      setTimeout(() => setActionStatus({}), 3000); // Clear after 3s
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    setActionStatus({ [id]: 'error' });
    alert(`Failed to update false positive status: ${err.message}`);
    setTimeout(() => setActionStatus({}), 3000);
  }
};

// Update button UI (Line 299-304)
<button
  onClick={() => toggleFalsePositive(activity.id)}
  disabled={actionStatus[activity.id] === 'loading'}
  className={`text-xs font-medium transition-colors ${
    actionStatus[activity.id] === 'loading' ? 'opacity-50 cursor-not-allowed' :
    actionStatus[activity.id] === 'success' ? 'text-green-600' :
    actionStatus[activity.id] === 'error' ? 'text-red-600' :
    'text-blue-600 hover:text-blue-800 hover:underline'
  }`}
>
  {actionStatus[activity.id] === 'loading' ? '⏳ Updating...' :
   actionStatus[activity.id] === 'success' ? '✓ Updated!' :
   activity.is_false_positive ? '✓ Unmark False Positive' : '⚠ Mark as False Positive'}
</button>
```

**Time Estimate:** 30 minutes

---

## Phase 1 Summary

### Files to Change:
1. **Backend:** `ow-ai-backend/routes/agent_routes.py` (add 3 endpoints)
2. **Frontend:** `owkai-pilot-frontend/src/components/AgentActivityFeed.jsx` (graceful NULL handling + button states)

### Deployment Steps:
```bash
# 1. Backend changes
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
git add routes/agent_routes.py
git commit -m "fix: Add missing Activity tab endpoints (false positive, support, file upload)

- POST /api/agent-action/false-positive/{id} - Toggle false positive flag
- POST /api/support/submit - Submit support ticket
- POST /api/agent-actions/upload-json - Bulk import agent actions

Fixes: 404 errors on all Activity tab buttons
Enterprise audit trail: Logs reviewer, timestamp for all actions

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push pilot master

# 2. Frontend changes
cd /Users/mac_001/OW_AI_Project/owkai-pilot-frontend
git add src/components/AgentActivityFeed.jsx
git commit -m "fix: Graceful NULL handling and button feedback in Activity tab

- Display 'No CVSS Data' instead of 'No CVSS' for NULL scores
- Display 'No Risk Assessment' instead of 'Unknown' for NULL risk
- Handle missing timestamps, action_type, tool_name gracefully
- Add loading/success/error states for all buttons
- Fix API endpoint paths (/api prefix)

Improves UX when enterprise data not yet calculated
Provides user feedback for all button actions

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin master  # or your frontend remote
```

### Testing Checklist:
- [ ] Production API returns 39 fields (not 6)
- [ ] False positive button works (200 OK, not 404)
- [ ] Support submit button works (200 OK, not 404)
- [ ] File upload button works (200 OK, not 404)
- [ ] NULL fields display gracefully (no "Invalid Date", "No CVSS Data" instead)
- [ ] Button feedback shows loading/success/error states

**Phase 1 Total Time:** 3-4 hours

---

## Phase 2: Enterprise Risk Assessment (DEFERRED)

**Scope:** Create services to calculate CVSS, MITRE, NIST for all agent actions

**When to Build:** After Phase 1 deployed and validated, OR when user requests data enrichment

**Files to Create:**
1. `ow-ai-backend/services/cvss_calculator.py` - CVSS v3.1 scoring engine
2. `ow-ai-backend/services/mitre_mapper.py` - ATT&CK tactic/technique mapping
3. `ow-ai-backend/services/nist_assigner.py` - NIST 800-53 control assignment
4. `ow-ai-backend/services/risk_enrichment.py` - Orchestrator for all services

**Integration Point:**
```python
# In agent_routes.py, after creating new AgentAction
from services.risk_enrichment import enrich_agent_action

action = AgentAction(...)
db.add(action)
db.commit()

# Enrich with CVSS, MITRE, NIST
enrich_agent_action(action, db)
```

**Backfill Existing Data:**
```python
# Script: ow-ai-backend/scripts/backfill_risk_data.py
from services.risk_enrichment import enrich_agent_action

actions = db.query(AgentAction).filter(AgentAction.cvss_score == None).all()
for action in actions:
    enrich_agent_action(action, db)
    print(f"Enriched action {action.id}")
```

**Phase 2 Total Time:** 20-25 hours (CVSS 6-8h, MITRE 4-6h, NIST 4-6h, Testing 4-5h)

---

## Rollback Plan

### If Phase 1 Deployment Fails:

**Backend Rollback:**
```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
git revert HEAD
git push pilot master
```

**Frontend Rollback:**
```bash
cd /Users/mac_001/OW_AI_Project/owkai-pilot-frontend
git revert HEAD
git push origin master
```

**Emergency Rollback (Manual):**
```bash
# Backend: Restore backup
cp src/components/AgentActivityFeed_Backup.jsx src/components/AgentActivityFeed.jsx
git add . && git commit -m "rollback: Emergency restore Activity tab" && git push
```

---

## Success Criteria

### Phase 1 Success:
✅ All 3 buttons functional (no 404 errors)
✅ NULL data displays gracefully (no "Invalid Date", proper messages)
✅ Production API returns 39 fields
✅ Users can mark false positives
✅ Users can submit support tickets
✅ Users can upload JSON logs

### Phase 2 Success (Future):
✅ All agent actions have CVSS scores calculated
✅ All actions mapped to MITRE ATT&CK
✅ All actions assigned NIST controls
✅ Approval workflow initialized for high-risk actions
✅ SLA deadlines calculated and tracked

---

## Cost-Benefit

**Phase 1 Investment:** 3-4 hours
**Phase 1 Value:** Working Activity tab with enterprise UI, all buttons functional

**Phase 2 Investment:** 20-25 hours (deferred)
**Phase 2 Value:** Full enterprise risk intelligence ($150K-$300K/year compliance value)

**Total ROI:** Phase 1 provides immediate UX wins, Phase 2 provides long-term business value

---

**Status:** Ready for user approval. Please review and approve Phase 1 implementation.
