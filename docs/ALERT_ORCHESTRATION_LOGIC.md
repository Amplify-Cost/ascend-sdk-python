# Alert Orchestration Logic Documentation

**Date:** 2025-10-30
**Component:** OW-AI Enterprise Orchestration Service
**Classification:** INTERNAL - TECHNICAL DOCUMENTATION

---

## Executive Summary

The OW-AI orchestration service automatically creates alerts for high-risk agent actions. This document explains the complete logic for all risk categories.

---

## Risk Categories Supported

The system supports **4 risk categories** from admin tools and API submissions:

| Risk Category | Risk Score Range | Auto-Alert Created | Orchestration Behavior |
|--------------|------------------|-------------------|----------------------|
| **LOW** | 0-49 | ❌ NO | No alert, may trigger low-priority workflows |
| **MEDIUM** | 50-69 | ❌ NO | No alert, may trigger medium-priority workflows |
| **HIGH** | 70-89 | ✅ YES | Alert auto-created, workflows triggered |
| **CRITICAL** | 90-100 | ✅ YES | Alert auto-created, high-priority workflows triggered |

---

## Alert Creation Logic

### Location
`/services/orchestration_service.py:38-45`

### Code
```python
# Auto-create alert for high/critical risk
if risk_level in ["high", "critical"]:
    alert_id = self._create_alert(action_id, risk_level, action_type)
    results["alert_created"] = True
    results["alert_id"] = alert_id
    logger.info(f"✅ Auto-created alert for action {action_id}")
```

### Business Rules

1. **Alert Creation Threshold**: Only `high` and `critical` risk levels trigger automatic alert creation
2. **Alert Severity**: Alert severity matches the action's `risk_level` (high → high, critical → critical)
3. **Alert Status**: New alerts start with status = `new`
4. **Alert Type**: All auto-created alerts have type = `High Risk Agent Action`
5. **Immediate Persistence**: Alerts are committed to database immediately upon creation

---

## Complete Workflow

### Step 1: Action Submission
**Endpoint**: `POST /api/agent-actions`
**Location**: `main.py:1536`

```python
# Accept risk_level from request OR default to "medium"
risk_level = data.get("risk_level", "medium")  # Line 1564
```

**Accepted Values**:
- `"low"` - Low risk action
- `"medium"` - Medium risk action (default)
- `"high"` - High risk action
- `"critical"` - Critical risk action

### Step 2: CVSS Risk Assessment
**Location**: `main.py:1576-1609`

The system calculates an enterprise risk score (0-100) using:
1. **CVSS v3.1 Base Score** (0-10) → Multiplied by 10 → (0-100)
2. **MITRE ATT&CK Mapping** → Identifies tactics and techniques
3. **NIST 800-53 Controls** → Maps to security controls

```python
# Calculate risk_score from CVSS
cvss_result = cvss_auto_mapper.auto_assess_action(...)
risk_score = min(int(cvss_result['base_score'] * 10), 100)
```

### Step 3: Orchestration Service Call
**Location**: `main.py:1612-1625`

```python
from services.orchestration_service import get_orchestration_service
orch = get_orchestration_service(db)

result = orch.orchestrate_action(
    action_id=action_id,
    risk_level=risk_level,  # ⚠️ CURRENT BUG: Variable not defined
    risk_score=risk_score,
    action_type=data["action_type"]
)
```

**⚠️ CRITICAL BUG IDENTIFIED (Line 1618)**:
- Uses `risk_level` variable that's not defined in this scope
- Should be: `risk_level=data.get("risk_level", "medium")`

### Step 4: Alert Creation (If High/Critical)
**Location**: `services/orchestration_service.py:60-81`

```python
def _create_alert(self, action_id: int, risk_level: str, action_type: str) -> int:
    """Create alert for high-risk action"""
    result = self.db.execute(text("""
        INSERT INTO alerts (
            agent_action_id, alert_type, severity, status,
            message, timestamp
        )
        VALUES (
            :action_id, 'High Risk Agent Action', :severity, 'new',
            :message, :timestamp
        )
        RETURNING id
    """), {
        "action_id": action_id,
        "severity": risk_level,  # Maps to alert severity
        "message": f"High-risk action: {action_type} (ID: {action_id})",
        "timestamp": datetime.utcnow()
    })

    self.db.commit()
    return result.fetchone()[0]
```

---

## Testing Results

### ✅ Comprehensive Test (All Categories)
**File**: `test_all_risk_categories.py`

| Risk Level | Risk Score | Action Type | Alert Created | Status |
|-----------|-----------|-------------|---------------|--------|
| LOW | 30 | file_read | ❌ NO | ✅ PASSED |
| MEDIUM | 55 | api_call | ❌ NO | ✅ PASSED |
| HIGH | 75 | database_write | ✅ YES | ✅ PASSED |
| CRITICAL | 95 | database_delete | ✅ YES | ✅ PASSED |

**Result**: All 4 risk categories handled correctly ✅

---

## Database Schema

### alerts Table
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    agent_action_id INTEGER REFERENCES agent_actions(id),
    alert_type VARCHAR(255),
    severity VARCHAR(50),  -- 'low', 'medium', 'high', 'critical'
    status VARCHAR(50),    -- 'new', 'acknowledged', 'resolved', 'escalated'
    message TEXT,
    timestamp TIMESTAMP,
    agent_id VARCHAR(255),
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    escalated_by VARCHAR(255),
    escalated_at TIMESTAMP
);
```

---

## Admin Tool Integration

### Creating Actions from Admin Tools

The admin interface should send:

```json
POST /api/agent-actions
{
    "agent_id": "admin-agent-001",
    "action_type": "database_write",
    "description": "Manual action from admin tool",
    "risk_level": "high",  // Options: "low", "medium", "high", "critical"
    "tool_name": "admin-console"
}
```

**Important**: All 4 risk categories are supported and handled correctly.

---

## Workflow Triggering

In addition to alert creation, the orchestration service also triggers workflows:

```python
# Auto-trigger workflows
triggered = self._trigger_workflows(action_id, risk_score, action_type)
results["workflows_triggered"] = triggered
```

**Workflow Logic** (`orchestration_service.py:87-110`):
- Finds all active workflows
- Matches trigger conditions (risk score thresholds)
- Creates workflow executions
- Returns list of triggered workflow IDs

---

## Critical Bug Fix Required

### Bug #4: Undefined Variable in Orchestration Call
**Location**: `main.py:1618`
**Severity**: HIGH
**Impact**: Orchestration receives wrong risk_level, may fail

**Current Code**:
```python
risk_level=risk_level,  # ❌ Variable not defined in this scope
```

**Fixed Code**:
```python
risk_level=data.get("risk_level", "medium"),  # ✅ Get from request data
```

**Alternative Fix** (if CVSS should override):
```python
# Calculate risk_level from risk_score
if risk_score >= 90:
    risk_level = "critical"
elif risk_score >= 70:
    risk_level = "high"
elif risk_score >= 50:
    risk_level = "medium"
else:
    risk_level = "low"
```

---

## Recommendations

1. ✅ **Fix Bug #4**: Update `main.py:1618` to use correct risk_level
2. ✅ **Document API**: Ensure API docs specify all 4 risk categories
3. ✅ **Admin Interface**: Verify dropdown includes all options
4. ✅ **Testing**: Continue testing with all categories from admin tools
5. ⚠️ **Decision Required**: Should risk_level be from user input OR calculated from CVSS?

---

## Monitoring and Observability

### Log Messages
```
✅ Auto-created alert for action {action_id}
✅ Triggered {count} workflows
❌ Orchestration failed: {error}
```

### Key Metrics to Track
- Alert creation rate by severity
- Orchestration success/failure rate
- Workflow trigger rate
- Average orchestration latency

---

## Compliance and Audit

All alert creation is logged to:
1. **alerts** table (immutable record)
2. **audit_logs** table (compliance trail)
3. Application logs (monitoring/debugging)

Audit trail includes:
- Who submitted the action
- When alert was created
- Risk score and level
- Linked action ID
- Orchestration result

---

**End of Documentation**
