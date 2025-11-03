# A/B Testing Enterprise Fix - Comprehensive Plan

**Date:** 2025-10-30
**Status:** 🔍 AUDIT COMPLETE - AWAITING APPROVAL
**Priority:** HIGH - Feature appears to work but data doesn't persist

---

## Problem Identified

### What's Happening Now

1. **User clicks "🧪 A/B Test" button** on a smart rule
2. **POST request sent** to `/api/smart-rules/ab-test?rule_id=X`
3. **Backend creates test** and stores in `enterprise_ab_tests_storage` (in-memory dictionary)
4. **Success message shown**: "✅ Enterprise A/B test created successfully!"
5. **User navigates to A/B Testing tab**
6. **GET request sent** to `/api/smart-rules/ab-tests`
7. **Backend returns** only hardcoded demo tests (ignores in-memory storage)
8. **User sees** only 3 [DEMO] tests, not their newly created test

### Root Causes

#### 1. **No Database Table**
- A/B tests are stored in memory (`enterprise_ab_tests_storage` dict)
- Memory is lost when backend restarts
- No persistence layer exists

#### 2. **GET Endpoint Ignores Created Tests**
- `get_ab_tests_enterprise_demo()` (line 354-478) returns **only** hardcoded demo tests
- Never checks `enterprise_ab_tests_storage` dictionary
- Newly created tests exist in memory but are never retrieved

#### 3. **Disconnect Between Create and List**
- POST endpoint writes to memory
- GET endpoint reads from hardcoded array
- They don't communicate

---

## Current Code Structure

### Backend (`smart_rules_routes.py`)

**Line 24:** In-memory storage declaration
```python
enterprise_ab_tests_storage: Dict[str, Dict[str, Any]] = {}
```

**Lines 485-582:** POST `/ab-test` - Creates test and stores in memory
```python
@router.post("/ab-test")
async def create_ab_test(rule_id: int, ...):
    # ... creates test_id and demo_test object ...

    # Stores in memory
    enterprise_ab_tests_storage[test_id] = demo_test

    return {"success": True, "test_id": test_id, ...}
```

**Lines 354-482:** GET `/ab-tests` - Returns hardcoded demos only
```python
@router.get("/ab-tests")
async def get_ab_tests_enterprise_demo(...):
    # Hardcoded array
    demo_tests = [
        {"id": 1, "test_name": "[DEMO] Data Exfiltration..."},
        {"id": 2, "test_name": "[DEMO] Privilege Escalation..."},
        {"id": 3, "test_name": "[DEMO] Network Anomaly..."}
    ]

    # NEVER checks enterprise_ab_tests_storage!
    return demo_tests
```

### Database Status

**No `ab_tests` table exists:**
```bash
$ psql -c "\dt" | grep test
# No results
```

**Missing table structure** - needs to be created

---

## Enterprise-Level Solution

### Design Principles

1. **Real Data Storage** - PostgreSQL database table
2. **Simple to Use** - One-click A/B test creation
3. **Complete Lifecycle** - Create → Monitor → Deploy/Stop
4. **Real Metrics** - Track actual alert routing and performance
5. **Zero Demo Data** - All tests are real user-created tests
6. **Audit Trail** - Full history of who created/modified tests

### Architecture Overview

```
User clicks "A/B Test" button
         ↓
POST /api/smart-rules/ab-test
         ↓
Create TWO rules in smart_rules table:
  - variant_a_rule_id (clone of original)
  - variant_b_rule_id (clone with optimizations)
         ↓
Create record in NEW TABLE: ab_tests
  - test_id, rule_id, variant_a_rule_id, variant_b_rule_id
  - status, traffic_split, created_at, etc.
         ↓
Return success with test_id
         ↓
GET /api/smart-rules/ab-tests
         ↓
Query ab_tests table JOIN smart_rules
         ↓
Calculate real performance from alerts table
         ↓
Return actual test data to frontend
```

---

## Implementation Plan

### Phase 1: Database Schema (15 min)

**Create `ab_tests` table:**

```sql
CREATE TABLE ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Rule references
    base_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_a_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,
    variant_b_rule_id INTEGER REFERENCES smart_rules(id) ON DELETE CASCADE,

    -- Test configuration
    traffic_split INTEGER DEFAULT 50,
    duration_hours INTEGER DEFAULT 168,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'running',
    progress_percentage INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Performance metrics (calculated from alerts)
    variant_a_triggers INTEGER DEFAULT 0,
    variant_a_true_positives INTEGER DEFAULT 0,
    variant_a_false_positives INTEGER DEFAULT 0,
    variant_a_performance DECIMAL(5,2),

    variant_b_triggers INTEGER DEFAULT 0,
    variant_b_true_positives INTEGER DEFAULT 0,
    variant_b_false_positives INTEGER DEFAULT 0,
    variant_b_performance DECIMAL(5,2),

    -- Results
    winner VARCHAR(20),
    confidence_level INTEGER,
    statistical_significance VARCHAR(20),
    improvement VARCHAR(100),

    -- Audit
    created_by VARCHAR(255),
    tenant_id VARCHAR(100),

    -- Indexes
    CONSTRAINT ab_tests_traffic_split_check CHECK (traffic_split >= 0 AND traffic_split <= 100)
);

CREATE INDEX idx_ab_tests_status ON ab_tests(status);
CREATE INDEX idx_ab_tests_base_rule ON ab_tests(base_rule_id);
CREATE INDEX idx_ab_tests_created_by ON ab_tests(created_by);
```

**Migration script:**
```python
# alembic revision --autogenerate -m "add_ab_tests_table"
```

### Phase 2: Backend POST Endpoint (30 min)

**Enhanced `create_ab_test()` function:**

```python
@router.post("/ab-test")
async def create_ab_test(
    rule_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Enterprise A/B Test Creation

    Steps:
    1. Verify base rule exists
    2. Clone rule for Variant A (exact copy)
    3. Create AI-optimized rule for Variant B
    4. Create ab_tests record
    5. Return test details
    """
    try:
        data = await request.json()

        # 1. Get base rule
        base_rule = db.execute(text("""
            SELECT name, condition, action, risk_level, description,
                   recommendation, justification
            FROM smart_rules WHERE id = :rule_id
        """), {"rule_id": rule_id}).fetchone()

        if not base_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # 2. Create Variant A (exact clone)
        variant_a_result = db.execute(text("""
            INSERT INTO smart_rules (
                name, agent_id, action_type, description, condition, action,
                risk_level, recommendation, justification, created_at
            ) VALUES (
                :name, 'ab-test-variant-a', 'ab_test', :description,
                :condition, :action, :risk_level, :recommendation,
                :justification, NOW()
            ) RETURNING id
        """), {
            "name": f"{base_rule.name} - Variant A (Control)",
            "description": f"A/B Test Control: {base_rule.description}",
            "condition": base_rule.condition,
            "action": base_rule.action,
            "risk_level": base_rule.risk_level,
            "recommendation": base_rule.recommendation,
            "justification": base_rule.justification
        })
        variant_a_id = variant_a_result.fetchone()[0]

        # 3. Create Variant B (AI-optimized)
        optimized_condition = await optimize_rule_condition(base_rule.condition)

        variant_b_result = db.execute(text("""
            INSERT INTO smart_rules (
                name, agent_id, action_type, description, condition, action,
                risk_level, recommendation, justification, created_at
            ) VALUES (
                :name, 'ab-test-variant-b', 'ab_test', :description,
                :condition, :action, :risk_level, :recommendation,
                :justification, NOW()
            ) RETURNING id
        """), {
            "name": f"{base_rule.name} - Variant B (Optimized)",
            "description": f"A/B Test Optimized: {base_rule.description}",
            "condition": optimized_condition,
            "action": base_rule.action,
            "risk_level": base_rule.risk_level,
            "recommendation": "AI-optimized for reduced false positives",
            "justification": f"Optimized version of: {base_rule.justification}"
        })
        variant_b_id = variant_b_result.fetchone()[0]

        # 4. Create A/B test record
        test_id = str(uuid.uuid4())
        test_result = db.execute(text("""
            INSERT INTO ab_tests (
                test_id, test_name, description, base_rule_id,
                variant_a_rule_id, variant_b_rule_id, traffic_split,
                duration_hours, status, created_by, tenant_id, created_at
            ) VALUES (
                :test_id, :test_name, :description, :base_rule_id,
                :variant_a_rule_id, :variant_b_rule_id, :traffic_split,
                :duration_hours, 'running', :created_by, :tenant_id, NOW()
            ) RETURNING id
        """), {
            "test_id": test_id,
            "test_name": f"A/B Test: {base_rule.name}",
            "description": f"Testing optimizations for rule {rule_id}",
            "base_rule_id": rule_id,
            "variant_a_rule_id": variant_a_id,
            "variant_b_rule_id": variant_b_id,
            "traffic_split": data.get("traffic_split", 50),
            "duration_hours": data.get("test_duration_hours", 168),
            "created_by": current_user.get("email"),
            "tenant_id": current_user.get("tenant_id")
        })

        db.commit()

        logger.info(f"✅ Created A/B test {test_id} for rule {rule_id}")

        return {
            "success": True,
            "test_id": test_id,
            "variant_a_rule_id": variant_a_id,
            "variant_b_rule_id": variant_b_id,
            "message": "A/B test created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def optimize_rule_condition(condition: str) -> str:
    """
    Simple optimization strategy - can enhance with AI later

    For now, adds context awareness and reduces thresholds slightly
    """
    # Example: "file_access > 100" → "file_access > 80 AND time_context = valid"
    optimized = condition

    # Add context awareness
    if "AND time_context" not in condition:
        optimized += " AND time_context = 'business_hours'"

    # Reduce numeric thresholds by 20%
    import re
    def reduce_threshold(match):
        num = int(match.group(1))
        return str(int(num * 0.8))

    optimized = re.sub(r'>\s*(\d+)', lambda m: f"> {reduce_threshold(m)}", optimized)

    return optimized
```

### Phase 3: Backend GET Endpoint (30 min)

**Replace hardcoded demos with real data:**

```python
@router.get("/ab-tests")
async def get_ab_tests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all A/B tests with real performance data"""
    try:
        # Query all tests
        tests_query = db.execute(text("""
            SELECT
                t.id, t.test_id, t.test_name, t.description,
                t.base_rule_id, t.variant_a_rule_id, t.variant_b_rule_id,
                t.traffic_split, t.duration_hours, t.status,
                t.progress_percentage, t.winner, t.confidence_level,
                t.statistical_significance, t.improvement,
                t.created_by, t.created_at, t.completed_at,

                -- Variant A details
                ra.condition as variant_a_condition,
                ra.action as variant_a_action,

                -- Variant B details
                rb.condition as variant_b_condition,
                rb.action as variant_b_action
            FROM ab_tests t
            LEFT JOIN smart_rules ra ON t.variant_a_rule_id = ra.id
            LEFT JOIN smart_rules rb ON t.variant_b_rule_id = rb.id
            WHERE t.created_by = :email OR :role = 'admin'
            ORDER BY t.created_at DESC
        """), {
            "email": current_user.get("email"),
            "role": current_user.get("role")
        }).fetchall()

        results = []
        for test in tests_query:
            # Calculate real performance from alerts
            performance = await calculate_test_performance(
                db,
                test.variant_a_rule_id,
                test.variant_b_rule_id
            )

            # Calculate progress
            if test.status == 'running':
                progress = calculate_progress(test.created_at, test.duration_hours)
            else:
                progress = 100

            # Build response
            test_data = {
                "id": test.id,
                "test_id": test.test_id,
                "test_name": test.test_name,
                "description": test.description,
                "rule_id": test.base_rule_id,

                "variant_a": test.variant_a_condition,
                "variant_b": test.variant_b_condition,

                "variant_a_performance": performance["variant_a"]["score"],
                "variant_b_performance": performance["variant_b"]["score"],

                "confidence_level": test.confidence_level or
                                    performance.get("confidence", 50),
                "status": test.status,
                "progress_percentage": progress,
                "winner": test.winner,
                "statistical_significance": test.statistical_significance or "medium",
                "improvement": test.improvement or
                               calculate_improvement(performance),

                "sample_size": performance.get("total_alerts", 0),
                "traffic_split": test.traffic_split,
                "duration_hours": test.duration_hours,

                "enterprise_insights": {
                    "cost_savings": calculate_cost_savings(performance),
                    "false_positive_reduction": calculate_fp_reduction(performance),
                    "efficiency_gain": calculate_efficiency_gain(performance),
                    "recommendation": generate_recommendation(test, performance)
                },

                "results": {
                    "threat_detection_rate": {
                        "variant_a": f"{performance['variant_a']['detection_rate']}%",
                        "variant_b": f"{performance['variant_b']['detection_rate']}%"
                    },
                    "false_positive_rate": {
                        "variant_a": f"{performance['variant_a']['fp_rate']}%",
                        "variant_b": f"{performance['variant_b']['fp_rate']}%"
                    },
                    "response_time": {
                        "variant_a": f"{performance['variant_a']['avg_response']}s",
                        "variant_b": f"{performance['variant_b']['avg_response']}s"
                    }
                },

                "created_by": test.created_by,
                "created_at": test.created_at.isoformat(),
                "completed_at": test.completed_at.isoformat() if test.completed_at else None
            }

            results.append(test_data)

        logger.info(f"✅ Returned {len(results)} A/B tests")
        return results

    except Exception as e:
        logger.error(f"Failed to get A/B tests: {e}")
        return []


async def calculate_test_performance(
    db: Session,
    variant_a_rule_id: int,
    variant_b_rule_id: int
) -> dict:
    """Calculate real performance metrics from alerts table"""

    # Query alerts that matched each variant
    variant_a_perf = db.execute(text("""
        SELECT
            COUNT(*) as total_triggers,
            COUNT(CASE WHEN escalated_at IS NOT NULL THEN 1 END) as true_positives,
            COUNT(CASE WHEN escalated_at IS NULL
                       AND acknowledged_at IS NOT NULL
                       AND EXTRACT(EPOCH FROM (acknowledged_at - timestamp)) < 300
                  THEN 1 END) as false_positives,
            AVG(EXTRACT(EPOCH FROM (acknowledged_at - timestamp))) as avg_response
        FROM alerts
        WHERE alert_type LIKE '%variant_a%'
           OR alert_type LIKE :rule_pattern
    """), {"rule_pattern": f"%rule_{variant_a_rule_id}%"}).fetchone()

    variant_b_perf = db.execute(text("""
        SELECT
            COUNT(*) as total_triggers,
            COUNT(CASE WHEN escalated_at IS NOT NULL THEN 1 END) as true_positives,
            COUNT(CASE WHEN escalated_at IS NULL
                       AND acknowledged_at IS NOT NULL
                       AND EXTRACT(EPOCH FROM (acknowledged_at - timestamp)) < 300
                  THEN 1 END) as false_positives,
            AVG(EXTRACT(EPOCH FROM (acknowledged_at - timestamp))) as avg_response
        FROM alerts
        WHERE alert_type LIKE '%variant_b%'
           OR alert_type LIKE :rule_pattern
    """), {"rule_pattern": f"%rule_{variant_b_rule_id}%"}).fetchone()

    def calc_metrics(perf):
        total = perf.total_triggers or 1
        tp = perf.true_positives or 0
        fp = perf.false_positives or 0

        return {
            "score": int((tp / total) * 100) if total > 0 else 75,
            "detection_rate": int((tp / total) * 100) if total > 0 else 75,
            "fp_rate": int((fp / total) * 100) if total > 0 else 5,
            "avg_response": round(perf.avg_response or 2.0, 1)
        }

    return {
        "variant_a": calc_metrics(variant_a_perf),
        "variant_b": calc_metrics(variant_b_perf),
        "total_alerts": (variant_a_perf.total_triggers or 0) +
                       (variant_b_perf.total_triggers or 0),
        "confidence": 75 if (variant_a_perf.total_triggers or 0) > 30 else 50
    }
```

### Phase 4: Frontend Updates (15 min)

**Minimal changes needed** - frontend already expects real data format!

**Only change:** Remove [DEMO] badge if not a demo test

```jsx
// In A/B Testing tab header
<div className="text-sm text-purple-600 bg-purple-50 px-4 py-2 rounded-lg">
  {abTests.length === 0
    ? "ℹ️ No tests yet - Create from Smart Rules tab"
    : abTests.every(t => t.test_name?.includes('[DEMO]'))
      ? "ℹ️ Demo examples below - Create real tests from Smart Rules tab"
      : ""}
</div>
```

---

## Simplified Alternative (If Full Implementation Too Complex)

**Quick Fix Option: Just merge in-memory storage into GET endpoint**

```python
@router.get("/ab-tests")
async def get_ab_tests(...):
    # Hardcoded demos
    demo_tests = [...]

    # ADD THIS: Include in-memory tests
    real_tests = list(enterprise_ab_tests_storage.values())

    # Combine and return
    all_tests = real_tests + demo_tests
    return all_tests
```

**Pros:**
- 5-minute fix
- Tests appear immediately
- No database changes

**Cons:**
- Tests lost on restart
- No real performance tracking
- Not enterprise-grade
- Still using demo data approach

**Recommendation:** ❌ Not recommended - band-aid solution

---

## Recommended Approach

### Full Enterprise Implementation

**Why:**
1. **Real Data** - Customers need actual metrics, not simulated
2. **Persistence** - Tests survive restarts
3. **Scalability** - Can handle 100s of tests
4. **Audit Trail** - Complete history
5. **True Enterprise** - Meets enterprise security standards

**Timeline:**
- Database schema: 15 min
- POST endpoint: 30 min
- GET endpoint: 30 min
- Frontend tweaks: 15 min
- Testing: 30 min
**Total:** ~2 hours

**Complexity:** Medium
**Risk:** Low (additive changes, no breaking changes)
**Value:** High (transforms demo into production system)

---

## Testing Plan

### Phase 1: Database
```bash
# Create table
psql owkai_pilot -f create_ab_tests_table.sql

# Verify
psql owkai_pilot -c "\d ab_tests"
```

### Phase 2: Backend Create
```bash
# Test A/B test creation
TOKEN="..."
curl -X POST "http://localhost:8000/api/smart-rules/ab-test?rule_id=9" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"traffic_split": 50, "test_duration_hours": 168}'

# Should return: {"success": true, "test_id": "..."}
```

### Phase 3: Backend Retrieve
```bash
# Test A/B tests retrieval
curl "http://localhost:8000/api/smart-rules/ab-tests" \
  -H "Authorization: Bearer $TOKEN"

# Should return: Array with new test included
```

### Phase 4: Frontend
```
1. Open AI Rule Engine
2. Go to Smart Rules tab
3. Click "🧪 A/B Test" on any rule
4. See success message
5. Switch to A/B Testing tab
6. Verify new test appears (not just demos)
7. Check all metrics display correctly
```

---

## Success Criteria

- [ ] A/B tests persist after backend restart
- [ ] Created tests appear in A/B Testing tab immediately
- [ ] Performance metrics calculated from real alerts
- [ ] No demo data (or clearly separated from real tests)
- [ ] Can create unlimited tests
- [ ] All tests have real data (not hardcoded)
- [ ] Frontend shows accurate business impact
- [ ] Users can deploy winner when ready
- [ ] Full audit trail maintained

---

## Questions for Approval

1. **Do you want the full enterprise implementation** (2 hours, real data, persistence)?
   - OR quick fix (5 min, in-memory only, lost on restart)?

2. **AI-optimization of Variant B** - Should we use real AI or simple heuristics?
   - Real AI: Call OpenAI to optimize rule condition
   - Heuristics: Simple threshold adjustments

3. **Demo tests** - Keep the 3 demo tests for reference, or remove entirely?
   - Keep as examples (marked [DEMO])
   - Remove completely (cleaner)

4. **Alert routing** - Should we implement actual 50/50 traffic split now?
   - Yes: Requires alert processing modification
   - No: Calculate metrics post-hoc from existing alerts

---

**Ready to proceed? Awaiting your approval to implement.**
