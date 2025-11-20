# Unified Authorization Queue Implementation Plan

**Project:** OW AI Enterprise Authorization Center
**Feature:** Unified Primary Queue + Filtered Secondary Views
**Author:** Donald King, OW-kai Enterprise Engineering
**Date:** November 15, 2025
**Status:** Awaiting Approval

---

## Executive Summary

This document outlines the implementation plan for a unified authorization queue that merges Agent Actions and MCP Server Actions into a single, enterprise-grade approval workflow. This aligns with industry standards used by Splunk, Palo Alto Networks, and other leading governance platforms.

### Business Value
- **Simplified Workflow:** Single queue for all authorization requests
- **Faster Approvals:** No context switching between tabs
- **Better Compliance:** Unified audit trail for all actions
- **Industry Standard:** Matches patterns used by enterprise leaders

### Current State Issues
1. **Backend Data Gap:** Only queries `agent_actions` table, missing MCP actions entirely
2. **Frontend Confusion:** Two separate tabs for essentially the same workflow
3. **Inconsistent Status Values:** "pending_approval" vs "PENDING"
4. **Different ID Types:** Integer (agent) vs UUID (MCP)

### Proposed Solution
- **Backend:** Unified data loader that queries BOTH tables
- **Frontend:** Single "Pending Actions" tab with filter dropdown
- **Compatibility:** Transform both action types to common schema
- **Enterprise UX:** Quick filters for All/Agent/MCP/High Risk

---

## Phase 1: Backend Implementation

### 1.1 Create Unified Data Loader

**File:** `ow-ai-backend/services/enterprise_unified_loader.py` (NEW)

**Purpose:** Query both `agent_actions` and `mcp_server_actions` tables, transform to common schema, sort by risk.

#### Implementation Code

```python
"""
Enterprise Unified Authorization Loader
Merges Agent Actions + MCP Server Actions into single approval queue
Author: Donald King, OW-kai Enterprise
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import text, union_all, select
from models import AgentAction
from models_mcp_governance import MCPServerAction

logger = logging.getLogger(__name__)

class EnterpriseUnifiedLoader:
    """
    Unified loader for ALL pending authorization actions
    Merges agent_actions + mcp_server_actions into single queue
    """

    def load_all_pending_actions(self, db: Session) -> Dict:
        """
        Load ALL pending actions from both tables
        Returns unified, sorted list with common schema
        """

        # Query 1: Agent Actions (status = 'pending_approval')
        agent_actions = db.query(AgentAction).filter(
            AgentAction.status == "pending_approval"
        ).all()

        # Query 2: MCP Server Actions (status = 'PENDING' or 'EVALUATE')
        mcp_actions = db.query(MCPServerAction).filter(
            MCPServerAction.status.in_(["PENDING", "EVALUATE"])
        ).all()

        logger.info(f"Found {len(agent_actions)} agent actions, {len(mcp_actions)} MCP actions")

        # Transform agent actions to common schema
        unified_actions = []

        for action in agent_actions:
            unified_actions.append({
                # Identification
                "id": f"agent-{action.id}",  # Prefix to avoid conflicts
                "numeric_id": action.id,  # Original ID for API calls
                "action_source": "agent",
                "action_type": action.action_type,

                # Display fields
                "description": action.description or f"{action.action_type} operation",
                "target_system": action.target_system or "Unknown",
                "agent_id": action.agent_id,

                # Risk assessment
                "risk_score": float(action.risk_score) if action.risk_score else 50.0,
                "risk_level": action.risk_level or "medium",

                # Status (normalized to uppercase)
                "status": "PENDING_APPROVAL",
                "requires_approval": action.requires_approval if action.requires_approval is not None else True,

                # Timestamps
                "created_at": action.timestamp.isoformat() if action.timestamp else action.created_at.isoformat(),
                "reviewed_at": action.reviewed_at.isoformat() if action.reviewed_at else None,

                # Approval details
                "approved_by": action.approved_by,
                "reviewed_by": action.reviewed_by,
                "created_by": action.created_by,

                # Enterprise compliance
                "nist_control": action.nist_control or "AC-3",
                "mitre_technique": action.mitre_technique or "T1078",
                "compliance_frameworks": ["SOX", "PCI_DSS", "NIST"],

                # Workflow
                "workflow_stage": action.workflow_stage or "pending_stage_1",
                "approval_level": action.approval_level or 1,
                "required_approval_level": action.required_approval_level or 1,

                # Original record (for compatibility)
                "_original_type": "AgentAction",
                "_original_id": action.id
            })

        # Transform MCP actions to common schema
        for mcp in mcp_actions:
            unified_actions.append({
                # Identification
                "id": f"mcp-{str(mcp.id)}",  # Prefix + UUID string
                "uuid_id": str(mcp.id),  # Original UUID for API calls
                "action_source": "mcp_server",
                "action_type": "mcp_server_action",

                # Display fields
                "description": f"{mcp.verb} on {mcp.resource}",
                "target_system": mcp.mcp_server_name,
                "agent_id": f"mcp:{mcp.mcp_server_name}",

                # Risk assessment (MCP uses Integer 0-100)
                "risk_score": float(mcp.risk_score) if mcp.risk_score else 0.0,
                "risk_level": mcp.risk_level or "LOW",

                # Status (already uppercase)
                "status": mcp.status,
                "requires_approval": mcp.requires_approval,

                # Timestamps
                "created_at": mcp.created_at.isoformat(),
                "reviewed_at": mcp.approved_at.isoformat() if mcp.approved_at else None,

                # Approval details
                "approved_by": mcp.approver_email,
                "reviewed_by": mcp.approver_id,
                "created_by": mcp.user_email,

                # MCP-specific fields
                "namespace": mcp.namespace,
                "verb": mcp.verb,
                "resource": mcp.resource,
                "mcp_server_name": mcp.mcp_server_name,
                "user_id": mcp.user_id,
                "user_email": mcp.user_email,

                # Enterprise compliance (map from MCP fields)
                "nist_control": "AC-3",  # Default for MCP actions
                "mitre_technique": "T1078",  # Default for MCP actions
                "compliance_frameworks": mcp.compliance_tags if mcp.compliance_tags else ["SOX", "PCI_DSS"],

                # Workflow
                "workflow_stage": "pending_stage_1",
                "approval_level": mcp.approval_level or 1,
                "required_approval_level": mcp.approval_level or 1,

                # Original record
                "_original_type": "MCPServerAction",
                "_original_id": str(mcp.id)
            })

        # Sort by risk score DESC, then created_at ASC (oldest first)
        unified_actions.sort(
            key=lambda x: (-x["risk_score"], x["created_at"])
        )

        logger.info(f"✅ Unified {len(unified_actions)} total actions (agent + MCP)")

        return {
            "success": True,
            "pending_actions": unified_actions,
            "actions": unified_actions,  # Backward compatibility
            "total": len(unified_actions),
            "counts": {
                "total": len(unified_actions),
                "agent_actions": len(agent_actions),
                "mcp_actions": len(mcp_actions),
                "high_risk": len([a for a in unified_actions if a["risk_score"] >= 70])
            }
        }

# Singleton instance
enterprise_unified_loader = EnterpriseUnifiedLoader()
```

**Evidence of Design Decisions:**

1. **Prefixed IDs:** `agent-{id}` and `mcp-{uuid}` prevent conflicts, keep original IDs for API calls
2. **Risk Score Compatibility:** Both use 0-100 scale (agent uses Float, MCP uses Integer)
3. **Status Normalization:** Transform to uppercase for consistency
4. **Sorting Logic:** High risk first, then oldest first (FIFO within risk level)
5. **Backward Compatibility:** Maintains `_original_type` and `_original_id` for API routing

### 1.2 Create API Endpoint

**File:** `ow-ai-backend/routes/authorization_routes.py` (MODIFY)

**Changes Required:**

```python
# Add import at top of file (Line ~10)
from services.enterprise_unified_loader import enterprise_unified_loader

# Add new endpoint (insert after existing /pending-actions endpoint)
@router.get("/api/authorization/unified-pending-actions")
async def get_unified_pending_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    🏢 ENTERPRISE: Unified pending actions from both agent_actions + mcp_server_actions
    Returns single queue sorted by risk score
    """
    try:
        result = enterprise_unified_loader.load_all_pending_actions(db)
        return result
    except Exception as e:
        logger.error(f"Failed to load unified pending actions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**File Locations:**
- Line ~10: Add import
- Line ~250: Add endpoint (after existing pending-actions endpoint)

---

## Phase 2: Frontend Implementation

### 2.1 Add Filter State and UI

**File:** `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx` (MODIFY)

#### Change 1: Add Filter State (Lines ~60)

```javascript
// After existing state declarations (around line 60)
const [actionSourceFilter, setActionSourceFilter] = useState("all"); // all, agent, mcp, high_risk
```

#### Change 2: Update API Call (Lines ~147-170)

**BEFORE:**
```javascript
// Line 147
const response = await fetch(`${API_BASE_URL}/api/authorization/pending-actions`, {
  headers: getAuthHeaders(),
});
```

**AFTER:**
```javascript
// Line 147 - Use new unified endpoint
const response = await fetch(`${API_BASE_URL}/api/authorization/unified-pending-actions`, {
  headers: getAuthHeaders(),
});

// Response already contains counts object
const data = await response.json();
console.log(`📊 Unified Queue: ${data.counts.total} total (${data.counts.agent_actions} agent, ${data.counts.mcp_actions} MCP)`);
```

#### Change 3: Add Filter Dropdown UI (Lines ~1784)

**Location:** Inside the "Pending Actions" tab rendering section

```javascript
{/* Filter Controls - Insert before the table */}
<div className="mb-6 flex items-center space-x-4">
  <div className="flex items-center space-x-2">
    <label className="text-sm font-medium text-gray-700">Filter by Source:</label>
    <select
      value={actionSourceFilter}
      onChange={(e) => setActionSourceFilter(e.target.value)}
      className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
    >
      <option value="all">All Actions ({pendingActions.length})</option>
      <option value="agent">
        Agent Actions ({pendingActions.filter(a => a.action_source === "agent").length})
      </option>
      <option value="mcp">
        MCP Actions ({pendingActions.filter(a => a.action_source === "mcp_server").length})
      </option>
      <option value="high_risk">
        High Risk (≥70) ({pendingActions.filter(a => a.risk_score >= 70).length})
      </option>
    </select>
  </div>

  {/* Quick Filter Buttons */}
  <div className="flex space-x-2">
    <button
      onClick={() => setActionSourceFilter("all")}
      className={`px-3 py-1 text-sm rounded ${
        actionSourceFilter === "all"
          ? "bg-blue-600 text-white"
          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
      }`}
    >
      All
    </button>
    <button
      onClick={() => setActionSourceFilter("agent")}
      className={`px-3 py-1 text-sm rounded ${
        actionSourceFilter === "agent"
          ? "bg-blue-600 text-white"
          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
      }`}
    >
      Agent
    </button>
    <button
      onClick={() => setActionSourceFilter("mcp")}
      className={`px-3 py-1 text-sm rounded ${
        actionSourceFilter === "mcp"
          ? "bg-blue-600 text-white"
          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
      }`}
    >
      MCP
    </button>
    <button
      onClick={() => setActionSourceFilter("high_risk")}
      className={`px-3 py-1 text-sm rounded ${
        actionSourceFilter === "high_risk"
          ? "bg-red-600 text-white"
          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
      }`}
    >
      🔴 High Risk
    </button>
  </div>
</div>
```

#### Change 4: Apply Filtering (Lines ~1800)

**BEFORE:**
```javascript
{pendingActions.map((action) => (
  <tr key={action.id}>
    {/* table cells */}
  </tr>
))}
```

**AFTER:**
```javascript
{/* Apply filter before mapping */}
{pendingActions
  .filter(action => {
    if (actionSourceFilter === "all") return true;
    if (actionSourceFilter === "agent") return action.action_source === "agent";
    if (actionSourceFilter === "mcp") return action.action_source === "mcp_server";
    if (actionSourceFilter === "high_risk") return action.risk_score >= 70;
    return true;
  })
  .map((action) => (
    <tr key={action.id}>
      {/* table cells */}
    </tr>
  ))}
```

#### Change 5: Update Tab Labels (Lines ~1650)

**BEFORE:**
```javascript
<button onClick={() => setActiveTab("pending")}>
  Pending Actions ({pendingActions.length})
</button>
<button onClick={() => setActiveTab("mcp-servers")}>
  MCP Servers ({pendingActions.filter(a => a.action_type === 'mcp_server_action').length})
</button>
```

**AFTER:**
```javascript
<button onClick={() => setActiveTab("pending")}>
  📋 All Pending Actions ({pendingActions.length})
</button>
<button onClick={() => setActiveTab("mcp-servers")}>
  🔧 MCP Servers ({pendingActions.filter(a => a.action_source === 'mcp_server').length})
</button>
```

### 2.2 Preserve Approval Routing Logic

**No changes needed** to approval handling (Lines 1244-1252) - it already routes correctly:

```javascript
// Existing logic handles both types correctly
let endpoint;
if (action?.action_type === 'mcp_server_action') {
  endpoint = `${API_BASE_URL}/api/mcp-governance/evaluate-action`;
} else {
  endpoint = `${API_BASE_URL}/api/authorization/authorize/${numericId}`;
}
```

**Why this works:**
- Agent actions have `numeric_id` field (integer)
- MCP actions have `uuid_id` field (UUID)
- Frontend already detects action type and routes to correct endpoint
- Unified loader preserves these fields in `_original_id`

---

## Phase 3: Testing Plan

### 3.1 Backend Testing

**Test 1: Verify Unified Endpoint Returns Both Types**

```bash
# Start backend locally
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
uvicorn main:app --reload --port 8000

# Get fresh token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@owkai.com&password=admin123"

# Test unified endpoint
TOKEN="<your_token>"
curl -s "http://localhost:8000/api/authorization/unified-pending-actions" \
  -H "Authorization: Bearer $TOKEN" | jq '.counts'

# Expected output:
# {
#   "total": 15,
#   "agent_actions": 10,
#   "mcp_actions": 5,
#   "high_risk": 3
# }
```

**Success Criteria:**
- ✅ Returns both agent and MCP actions
- ✅ Counts object shows breakdown
- ✅ Actions sorted by risk_score DESC
- ✅ All actions have `action_source` field

**Test 2: Verify Risk Score Sorting**

```bash
curl -s "http://localhost:8000/api/authorization/unified-pending-actions" \
  -H "Authorization: Bearer $TOKEN" | jq '.pending_actions[] | {id, action_source, risk_score}' | head -20
```

**Expected:** Risk scores in descending order (95, 87, 75, 68, 50...)

### 3.2 Frontend Testing

**Test 3: Verify Filter Dropdown Works**

1. Start frontend: `npm run dev`
2. Navigate to Authorization Center → Pending Actions tab
3. Verify filter dropdown shows:
   - "All Actions (15)"
   - "Agent Actions (10)"
   - "MCP Actions (5)"
   - "High Risk ≥70 (3)"
4. Click each filter, verify table updates correctly

**Test 4: Verify Quick Filter Buttons**

1. Click "Agent" button → only agent actions shown
2. Click "MCP" button → only MCP actions shown
3. Click "High Risk" button → only actions with risk_score ≥ 70 shown
4. Click "All" button → all actions shown

**Test 5: Verify Approval Still Works**

1. Filter to "Agent Actions"
2. Click "Approve" on an agent action
3. Verify it routes to `/api/authorization/authorize/{id}` (agent endpoint)
4. Filter to "MCP Actions"
5. Click "Approve" on an MCP action
6. Verify it routes to `/api/mcp-governance/evaluate-action` (MCP endpoint)

**Success Criteria:**
- ✅ Both agent and MCP approvals work correctly
- ✅ No errors in browser console
- ✅ Actions disappear from queue after approval

### 3.3 End-to-End Verification

**Test 6: Create Real Actions and Verify Flow**

```bash
# Create agent action via API
curl -X POST "http://localhost:8000/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-001",
    "action_type": "database_write",
    "description": "Test unified queue - agent action",
    "target_system": "PostgreSQL Production",
    "risk_level": "high"
  }'

# Verify it appears in unified queue
curl -s "http://localhost:8000/api/authorization/unified-pending-actions" \
  -H "Authorization: Bearer $TOKEN" | jq '.pending_actions[] | select(.description | contains("Test unified queue"))'
```

**Expected:**
- ✅ Action appears in unified endpoint response
- ✅ Action shows in frontend "All Actions" view
- ✅ Action shows in frontend "Agent" filter
- ✅ Action does NOT show in "MCP" filter

---

## Phase 4: Deployment Strategy

### 4.1 Backend Deployment

**Steps:**

1. **Commit Changes**
   ```bash
   cd /Users/mac_001/OW_AI_Project/ow-ai-backend
   git add services/enterprise_unified_loader.py
   git add routes/authorization_routes.py
   git commit -m "feat: Add unified authorization queue (agent + MCP actions)

   - Create EnterpriseUnifiedLoader service
   - Query both agent_actions and mcp_server_actions tables
   - Transform to common schema with prefixed IDs
   - Sort by risk_score DESC, created_at ASC
   - Add /api/authorization/unified-pending-actions endpoint
   - Return counts breakdown (total, agent, MCP, high_risk)

   Aligns with enterprise governance standards (Splunk, Palo Alto)
   Simplifies approval workflow with unified queue + smart filtering"
   ```

2. **Build and Deploy**
   ```bash
   # Build Docker image (no cache)
   docker build --no-cache -t owkai-pilot-backend:unified-queue .

   # Tag for ECR
   aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 637423433960.dkr.ecr.us-east-2.amazonaws.com
   docker tag owkai-pilot-backend:unified-queue 637423433960.dkr.ecr.us-east-2.amazonaws.com/owkai-pilot-backend:unified-queue

   # Push to ECR
   docker push 637423433960.dkr.ecr.us-east-2.amazonaws.com/owkai-pilot-backend:unified-queue

   # Update ECS service
   aws ecs update-service \
     --cluster owkai-pilot-cluster \
     --service owkai-pilot-backend-service \
     --force-new-deployment \
     --region us-east-2
   ```

3. **Verify Deployment**
   ```bash
   # Check service health
   aws ecs describe-services \
     --cluster owkai-pilot-cluster \
     --services owkai-pilot-backend-service \
     --region us-east-2 | jq '.services[0].deployments'

   # Test production endpoint
   curl -s "https://pilot.owkai.app/api/authorization/unified-pending-actions" \
     -H "Authorization: Bearer $PROD_TOKEN" | jq '.counts'
   ```

### 4.2 Frontend Deployment

**Steps:**

1. **Commit Changes**
   ```bash
   cd /Users/mac_001/OW_AI_Project/owkai-pilot-frontend
   git add src/components/AgentAuthorizationDashboard.jsx
   git commit -m "feat: Add unified authorization queue with smart filtering

   - Update API call to use unified-pending-actions endpoint
   - Add actionSourceFilter state (all, agent, mcp, high_risk)
   - Add filter dropdown with live counts
   - Add quick filter buttons (All, Agent, MCP, High Risk)
   - Update tab labels for clarity
   - Preserve existing approval routing logic

   Aligns with enterprise governance standards (Splunk, Palo Alto)
   Provides single queue with smart filtering for better UX"
   ```

2. **Build and Deploy**
   ```bash
   # Build production bundle
   npm run build

   # Verify build size
   ls -lh dist/assets/*.js

   # Deploy to Railway
   git push origin main
   ```

3. **Verify Production**
   - Navigate to https://pilot.owkai.app
   - Login as admin
   - Go to Authorization Center
   - Verify "All Pending Actions" tab shows unified queue
   - Test all filter options
   - Approve both agent and MCP actions

### 4.3 Rollback Plan

**If issues occur:**

**Backend Rollback:**
```bash
# Revert to previous task definition
PREV_TASK_DEF="owkai-pilot-backend:445"  # Current production version
aws ecs update-service \
  --cluster owkai-pilot-cluster \
  --service owkai-pilot-backend-service \
  --task-definition $PREV_TASK_DEF \
  --force-new-deployment \
  --region us-east-2
```

**Frontend Rollback:**
```bash
# Revert git commit
git revert HEAD
git push origin main
```

---

## Evidence Summary

### Database Schema Compatibility

**Agent Actions Table:**
- Primary Key: `id` (Integer)
- Risk Score: `risk_score` (Float, 0-100)
- Status: `"pending_approval"` (lowercase with underscore)
- Created: `timestamp` (DateTime)

**MCP Server Actions Table:**
- Primary Key: `id` (UUID)
- Risk Score: `risk_score` (Integer, 0-100)
- Status: `"PENDING"` or `"EVALUATE"` (uppercase)
- Created: `created_at` (DateTime)

**Compatibility Strategy:**
- ✅ Use prefixed IDs to avoid conflicts (`agent-123`, `mcp-uuid`)
- ✅ Convert both risk scores to Float for consistency
- ✅ Normalize status to uppercase
- ✅ Use `created_at` for both (agent has both `timestamp` and `created_at`)

### API Integration Evidence

**Existing Endpoints (Already in Production):**
- `POST /api/authorization/authorize/{id}` - Agent action approval
- `POST /api/mcp-governance/evaluate-action` - MCP action approval

**New Endpoint:**
- `GET /api/authorization/unified-pending-actions` - Unified queue (both types)

**Frontend Already Detects Action Type:**
File: `AgentAuthorizationDashboard.jsx` Lines 1244-1252
```javascript
if (action?.action_type === 'mcp_server_action') {
  endpoint = `${API_BASE_URL}/api/mcp-governance/evaluate-action`;
} else {
  endpoint = `${API_BASE_URL}/api/authorization/authorize/${numericId}`;
}
```

### Industry Alignment

**Splunk Enterprise Security:**
- Uses unified "Notable Events" queue
- Filters by Source, Severity, Status
- Quick filters for High/Medium/Low severity

**Palo Alto Cortex XSOAR:**
- Single "Incidents" queue for all sources
- Filter dropdown by Type, Severity, Source
- Quick action buttons for common filters

**Our Implementation:**
- ✅ Single "Pending Actions" queue
- ✅ Filter by Source (Agent/MCP), Risk Level
- ✅ Quick filter buttons (All/Agent/MCP/High Risk)
- ✅ Maintains specialized MCP tab for advanced users

---

## Risk Assessment

### Implementation Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ID conflicts between agent/MCP actions | Medium | High | Use prefixed IDs (`agent-123`, `mcp-uuid`) |
| Performance degradation (2 queries) | Low | Medium | Both queries use indexed status columns |
| Breaking existing approval flow | Low | Critical | Preserve original IDs in `_original_id` field |
| Frontend filter state bug | Low | Low | Comprehensive local testing before deploy |

### Data Integrity Safeguards

1. **Preserve Original Records:** Never modify source tables, only transform for display
2. **Original ID Tracking:** Keep `_original_id` and `_original_type` for API routing
3. **Backward Compatibility:** Existing `/pending-actions` endpoint still works
4. **Gradual Migration:** Frontend can switch endpoints without backend changes

---

## Success Metrics

### Post-Deployment Validation

**Metric 1: Data Completeness**
- ✅ Unified endpoint returns count of agent + MCP actions matching individual endpoints
- Formula: `unified.counts.total === agent_count + mcp_count`

**Metric 2: Filter Accuracy**
- ✅ Each filter returns correct subset of actions
- Agent filter count matches `action_source === "agent"` count
- MCP filter count matches `action_source === "mcp_server"` count
- High risk count matches `risk_score >= 70` count

**Metric 3: Approval Success Rate**
- ✅ Agent action approval success rate: 100%
- ✅ MCP action approval success rate: 100%
- Monitor for 48 hours post-deployment

**Metric 4: Performance**
- ✅ Unified endpoint response time < 500ms (p95)
- ✅ Frontend render time < 200ms for 50 actions

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Backend Implementation | 2 hours | None |
| Phase 2: Frontend Implementation | 2 hours | Phase 1 complete |
| Phase 3: Local Testing | 2 hours | Phases 1-2 complete |
| Phase 4: Production Deployment | 1 hour | Phase 3 verified |
| **Total** | **7 hours** | User approval |

---

## Approval Checklist

Before proceeding with implementation, confirm:

- [ ] Architecture aligns with Splunk/Palo Alto enterprise standards
- [ ] Backend unified loader design approved
- [ ] Frontend filter UI design approved
- [ ] Testing plan is comprehensive
- [ ] Deployment strategy includes rollback plan
- [ ] Risk mitigation strategies acceptable

---

## Next Steps

**Upon Approval:**

1. ✅ Mark "Create implementation plan" as complete
2. ⏭️ Implement backend unified loader
3. ⏭️ Add unified endpoint to authorization routes
4. ⏭️ Implement frontend filter UI
5. ⏭️ Test locally with evidence collection
6. ⏭️ Deploy to production (backend → frontend)
7. ⏭️ Verify end-to-end functionality
8. ✅ Document completion in CLAUDE.md

---

**Document End**

*This implementation plan follows OW-kai Enterprise engineering standards for comprehensive planning, evidence-based design, and production-grade deployment procedures.*
