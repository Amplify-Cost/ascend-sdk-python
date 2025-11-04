# Phase 1 - Step 3: Implementation Plan
## Analytics Fix - Detailed Technical Design

**Date:** 2025-11-04 17:30:00 UTC
**Phase:** 1 - Analytics Fix
**Step:** 3 - PLAN
**Engineer:** OW-KAI Engineer
**Methodology:** Enterprise Architecture Design

---

## Executive Summary

**Objective:** Add database-backed policy evaluation tracking to existing Cedar enforcement engine

**Scope:** Minimal, surgical changes to add audit trail without modifying working Cedar engine

**Components to Create:**
1. Database table: `policy_evaluations`
2. SQLAlchemy model: `PolicyEvaluation`
3. Analytics service: `policy_analytics_service.py` (~200 lines)
4. Route modifications: 2 integration points

**Timeline:** 2-3 hours implementation + 1 hour testing = 3-4 hours total

---

## Part 1: Database Schema Design

### 1.1 Table Structure

```sql
CREATE TABLE policy_evaluations (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    policy_id INTEGER REFERENCES enterprise_policies(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Evaluation Context
    principal VARCHAR(255) NOT NULL,          -- e.g., "ai_agent:openai_gpt4"
    action VARCHAR(255) NOT NULL,             -- e.g., "database:read"
    resource VARCHAR(512) NOT NULL,           -- e.g., "arn:aws:db:prod/customers"

    -- Evaluation Result
    decision VARCHAR(50) NOT NULL,            -- "ALLOW", "DENY", "REQUIRE_APPROVAL"
    allowed BOOLEAN NOT NULL DEFAULT false,

    -- Performance Metrics
    evaluation_time_ms INTEGER,               -- Latency in milliseconds
    cache_hit BOOLEAN DEFAULT false,          -- Was result from cache?

    -- Policy Matching
    policies_triggered JSONB,                 -- Array of triggered policy IDs/names
    matched_conditions JSONB,                 -- Which conditions matched

    -- Timestamps
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Additional Context (optional)
    context JSONB,                            -- Full request context for forensics
    error_message TEXT                        -- If evaluation failed
);
```

### 1.2 Indexes for Performance

```sql
-- Query Optimization Indexes
CREATE INDEX idx_policy_evaluations_policy_id
    ON policy_evaluations(policy_id);

CREATE INDEX idx_policy_evaluations_user_id
    ON policy_evaluations(user_id);

CREATE INDEX idx_policy_evaluations_evaluated_at
    ON policy_evaluations(evaluated_at DESC);

CREATE INDEX idx_policy_evaluations_decision
    ON policy_evaluations(decision);

CREATE INDEX idx_policy_evaluations_principal
    ON policy_evaluations(principal);

-- Composite index for analytics queries
CREATE INDEX idx_policy_evaluations_date_decision
    ON policy_evaluations(evaluated_at DESC, decision);

-- GIN index for JSONB searching
CREATE INDEX idx_policy_evaluations_policies_triggered_gin
    ON policy_evaluations USING GIN (policies_triggered);
```

### 1.3 Performance Analysis

**Expected Query Patterns:**
1. **Today's evaluations:** `WHERE evaluated_at >= CURRENT_DATE`
2. **Policy effectiveness:** `WHERE policy_id = X GROUP BY decision`
3. **User activity:** `WHERE user_id = X AND evaluated_at >= ...`
4. **Denial analysis:** `WHERE decision = 'DENY' ORDER BY evaluated_at DESC`

**Index Usage:**
- `idx_policy_evaluations_evaluated_at`: Time-range queries (dashboard metrics)
- `idx_policy_evaluations_date_decision`: Combined filters (common in analytics)
- `idx_policy_evaluations_policy_id`: Per-policy statistics

**Estimated Performance:**
- Dashboard load (today's metrics): <100ms with proper indexes
- Policy detail view: <50ms (single policy lookup)
- Historical analysis (30 days): ~500ms (depends on volume)

---

## Part 2: SQLAlchemy Model Design

### 2.1 Model Class

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/models.py`

**Insert after `EnterprisePolicy` class (line 449):**

```python
class PolicyEvaluation(Base):
    """
    Policy Evaluation Audit Trail

    Stores results of Cedar policy engine evaluations for:
    - Compliance audit trail (SOX, HIPAA, PCI-DSS, GDPR)
    - Security analytics and threat detection
    - Policy effectiveness measurement
    - Performance monitoring
    """
    __tablename__ = "policy_evaluations"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Keys
    policy_id = Column(Integer, ForeignKey("enterprise_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Evaluation Context
    principal = Column(String(255), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    resource = Column(String(512), nullable=False)

    # Evaluation Result
    decision = Column(String(50), nullable=False, index=True)  # ALLOW, DENY, REQUIRE_APPROVAL
    allowed = Column(Boolean, nullable=False, default=False)

    # Performance Metrics
    evaluation_time_ms = Column(Integer, nullable=True)
    cache_hit = Column(Boolean, default=False)

    # Policy Matching (JSONB for flexible querying)
    policies_triggered = Column(JSONB, nullable=True)  # [{policy_id: 1, policy_name: "...", effect: "deny"}]
    matched_conditions = Column(JSONB, nullable=True)  # {environment: "production", risk_level: "high"}

    # Timestamps
    evaluated_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)

    # Additional Context
    context = Column(JSONB, nullable=True)  # Full request context for forensic analysis
    error_message = Column(Text, nullable=True)  # If evaluation failed

    # Relationships
    policy = relationship("EnterprisePolicy", foreign_keys=[policy_id])
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<PolicyEvaluation(id={self.id}, decision={self.decision}, policy_id={self.policy_id})>"
```

### 2.2 Model Design Rationale

**Why JSONB for `policies_triggered`?**
- Flexible: Can store multiple policies without schema changes
- Queryable: GIN indexes enable fast JSON searches
- Compact: Single column vs. many-to-many join table

**Why separate `decision` and `allowed`?**
- `decision`: Human-readable ("ALLOW", "DENY", "REQUIRE_APPROVAL")
- `allowed`: Boolean for simple queries (`WHERE allowed = true`)
- Redundancy is intentional for query optimization

**Why `evaluation_time_ms`?**
- Performance monitoring and SLA tracking
- Identify slow policies for optimization
- Track p50, p95, p99 latencies

**Why `cache_hit`?**
- Measure cache effectiveness
- Understand true policy engine load
- Optimize caching strategy based on data

---

## Part 3: Analytics Service Design

### 3.1 Service Architecture

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/services/policy_analytics_service.py`

```python
"""
Policy Analytics Service

Provides database-backed analytics for policy evaluation tracking.
Replaces fake random data with real metrics from policy_evaluations table.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from models import PolicyEvaluation, EnterprisePolicy, User

logger = logging.getLogger(__name__)


class PolicyAnalyticsService:
    """
    Tracks and analyzes policy evaluations for compliance and performance monitoring.
    """

    def __init__(self, db: Session):
        self.db = db

    async def log_evaluation(self,
                            evaluation_result: Dict[str, Any],
                            principal: str,
                            action: str,
                            resource: str,
                            context: Optional[Dict] = None,
                            user_id: Optional[int] = None,
                            policy_id: Optional[int] = None) -> PolicyEvaluation:
        """
        Log a policy evaluation to the database.

        Called after Cedar engine evaluates a policy to create audit trail.

        Args:
            evaluation_result: Result from EnforcementEngine.evaluate()
                {
                    "decision": "ALLOW|DENY|REQUIRE_APPROVAL",
                    "allowed": bool,
                    "policies_triggered": [...],
                    "evaluation_time_ms": int,
                    "timestamp": str
                }
            principal: Who made the request (e.g., "ai_agent:openai_gpt4")
            action: What action was requested (e.g., "database:write")
            resource: What resource (e.g., "arn:aws:db:prod/table")
            context: Additional request context (optional)
            user_id: Associated user ID (optional)
            policy_id: Primary policy ID if single policy evaluation (optional)

        Returns:
            PolicyEvaluation: Created database record

        Example:
            result = enforcement_engine.evaluate(principal, action, resource, context)
            await policy_analytics_service.log_evaluation(
                result, principal, action, resource, context, user_id=7
            )
        """
        try:
            evaluation = PolicyEvaluation(
                policy_id=policy_id,
                user_id=user_id,
                principal=principal,
                action=action,
                resource=resource,
                decision=evaluation_result.get("decision", "DENY"),
                allowed=evaluation_result.get("allowed", False),
                evaluation_time_ms=evaluation_result.get("evaluation_time_ms", 0),
                cache_hit=evaluation_result.get("cache_hit", False),
                policies_triggered=evaluation_result.get("policies_triggered", []),
                matched_conditions=context,
                context=context,
                error_message=evaluation_result.get("error")
            )

            self.db.add(evaluation)
            self.db.commit()
            self.db.refresh(evaluation)

            logger.info(f"Logged policy evaluation: {evaluation.id} - {evaluation.decision}")
            return evaluation

        except Exception as e:
            logger.error(f"Failed to log policy evaluation: {str(e)}")
            self.db.rollback()
            raise

    async def get_engine_metrics(self,
                                  time_range_hours: int = 24) -> Dict[str, Any]:
        """
        Calculate real-time policy engine metrics from database.

        REPLACES the fake random.randint() metrics in unified_governance_routes.py:881-893

        Args:
            time_range_hours: Look back period (default 24 hours)

        Returns:
            Dict with metrics:
            {
                "total_evaluations": int,
                "evaluations_today": int,
                "denials": int,
                "approvals_required": int,
                "average_response_time_ms": float,
                "success_rate": float,
                "cache_hit_rate": float,
                "active_policies": int,
                "total_policies": int,
                "evaluation_throughput": int,  # per hour
                "last_updated": str
            }
        """
        try:
            start_time = datetime.now(UTC) - timedelta(hours=time_range_hours)

            # Query: Total evaluations in time range
            total_evaluations = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= start_time
            ).scalar() or 0

            # Query: Evaluations today
            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
            evaluations_today = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= today_start
            ).scalar() or 0

            # Query: Denials count
            denials = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.decision == "DENY"
                )
            ).scalar() or 0

            # Query: Approvals required count
            approvals_required = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.decision == "REQUIRE_APPROVAL"
                )
            ).scalar() or 0

            # Query: Average response time
            avg_response_time = self.db.query(func.avg(PolicyEvaluation.evaluation_time_ms)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.evaluation_time_ms.isnot(None)
                )
            ).scalar() or 0.2

            # Query: Cache hit rate
            total_with_cache_data = self.db.query(func.count(PolicyEvaluation.id)).filter(
                PolicyEvaluation.evaluated_at >= start_time
            ).scalar() or 1

            cache_hits = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.cache_hit == True
                )
            ).scalar() or 0

            cache_hit_rate = (cache_hits / total_with_cache_data * 100) if total_with_cache_data > 0 else 0.0

            # Query: Success rate (non-errors)
            errors = self.db.query(func.count(PolicyEvaluation.id)).filter(
                and_(
                    PolicyEvaluation.evaluated_at >= start_time,
                    PolicyEvaluation.error_message.isnot(None)
                )
            ).scalar() or 0

            success_rate = ((total_evaluations - errors) / total_evaluations * 100) if total_evaluations > 0 else 100.0

            # Query: Active policies
            active_policies = self.db.query(func.count(EnterprisePolicy.id)).filter(
                EnterprisePolicy.status == 'active'
            ).scalar() or 0

            # Query: Total policies
            total_policies = self.db.query(func.count(EnterprisePolicy.id)).scalar() or 0

            # Calculate: Throughput (evaluations per hour)
            evaluation_throughput = int(total_evaluations / time_range_hours) if time_range_hours > 0 else 0

            return {
                "total_evaluations": total_evaluations,
                "evaluations_today": evaluations_today,
                "denials": denials,
                "approvals_required": approvals_required,
                "average_response_time_ms": round(float(avg_response_time), 2),
                "success_rate": round(success_rate, 1),
                "cache_hit_rate": round(cache_hit_rate, 1),
                "active_policies": active_policies,
                "total_policies": total_policies,
                "evaluation_throughput": evaluation_throughput,
                "last_updated": datetime.now(UTC).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get engine metrics: {str(e)}")
            # Fail gracefully with empty metrics rather than crashing
            return {
                "total_evaluations": 0,
                "evaluations_today": 0,
                "denials": 0,
                "approvals_required": 0,
                "average_response_time_ms": 0.0,
                "success_rate": 0.0,
                "cache_hit_rate": 0.0,
                "active_policies": 0,
                "total_policies": 0,
                "evaluation_throughput": 0,
                "last_updated": datetime.now(UTC).isoformat(),
                "error": str(e)
            }

    async def get_policy_effectiveness(self,
                                       policy_id: int,
                                       time_range_days: int = 30) -> Dict[str, Any]:
        """
        Analyze effectiveness of a specific policy.

        Args:
            policy_id: Policy to analyze
            time_range_days: Analysis period

        Returns:
            Dict with policy statistics:
            {
                "policy_id": int,
                "evaluations": int,
                "denials": int,
                "approvals": int,
                "approval_requests": int,
                "avg_evaluation_time_ms": float,
                "triggered_count": int,
                "effectiveness_score": float  # 0-100
            }
        """
        start_time = datetime.now(UTC) - timedelta(days=time_range_days)

        # Evaluations where this policy was primary
        evaluations = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Denials
        denials = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "DENY",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Approvals
        approvals = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "ALLOW",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Approval requests
        approval_requests = self.db.query(func.count(PolicyEvaluation.id)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.decision == "REQUIRE_APPROVAL",
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0

        # Average evaluation time
        avg_time = self.db.query(func.avg(PolicyEvaluation.evaluation_time_ms)).filter(
            and_(
                PolicyEvaluation.policy_id == policy_id,
                PolicyEvaluation.evaluated_at >= start_time
            )
        ).scalar() or 0.0

        # Calculate effectiveness score (denials + approval_requests = active protection)
        active_protections = denials + approval_requests
        effectiveness_score = (active_protections / evaluations * 100) if evaluations > 0 else 0.0

        return {
            "policy_id": policy_id,
            "evaluations": evaluations,
            "denials": denials,
            "approvals": approvals,
            "approval_requests": approval_requests,
            "avg_evaluation_time_ms": round(float(avg_time), 2),
            "triggered_count": evaluations,
            "effectiveness_score": round(effectiveness_score, 1)
        }


# Singleton instance
def get_policy_analytics_service(db: Session) -> PolicyAnalyticsService:
    """Factory function to create PolicyAnalyticsService instance"""
    return PolicyAnalyticsService(db)
```

### 3.2 Service Design Rationale

**Why async methods?**
- Future-proof for async database drivers
- Compatible with FastAPI async routes
- Minimal overhead (can still use sync Session)

**Why separate `log_evaluation()` and `get_engine_metrics()`?**
- **log_evaluation()**: Write path (called after each policy evaluation)
- **get_engine_metrics()**: Read path (called by dashboard API)
- Separation of concerns enables independent optimization

**Why time_range parameters?**
- Flexibility: Dashboard can show "today", "week", "month" views
- Performance: Smaller time ranges = faster queries
- User control: Let users adjust analysis period

**Why calculate `effectiveness_score`?**
- Single metric to assess policy value
- Higher score = policy is actively protecting resources
- Low score may indicate overly permissive or unused policy

---

## Part 4: Route Integration Plan

### 4.1 Enforcement Route Integration

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/routes/unified_governance_routes.py`

**Location:** Policy enforcement endpoint (approximately lines 1335-1458)

**Current Code Structure:**
```python
@router.post("/api/governance/policies/enforce")
async def enforce_policy(request: PolicyEnforcementRequest, db: Session = Depends(get_db)):
    # ... existing code ...

    result = enforcement_engine.evaluate(
        principal=principal,
        action=request.action,
        resource=request.resource,
        context=request.context
    )

    return result  # ← MODIFY HERE
```

**Modification:**
```python
from services.policy_analytics_service import get_policy_analytics_service

@router.post("/api/governance/policies/enforce")
async def enforce_policy(request: PolicyEnforcementRequest, db: Session = Depends(get_db)):
    # ... existing code ...

    result = enforcement_engine.evaluate(
        principal=principal,
        action=request.action,
        resource=request.resource,
        context=request.context
    )

    # ✅ NEW: Log evaluation to database for audit trail
    try:
        analytics_service = get_policy_analytics_service(db)
        await analytics_service.log_evaluation(
            evaluation_result=result,
            principal=principal,
            action=request.action,
            resource=request.resource,
            context=request.context,
            user_id=getattr(request, 'user_id', None),  # If available
            policy_id=None  # Will extract from policies_triggered
        )
    except Exception as e:
        # Log error but don't fail the enforcement decision
        logger.error(f"Failed to log policy evaluation: {str(e)}")

    return result
```

**Integration Notes:**
- ✅ Non-blocking: Logging failure doesn't affect policy decision
- ✅ Minimal code change: Single try/except block
- ✅ Backward compatible: Existing enforcement logic unchanged
- ✅ Error handling: Logs errors but continues

### 4.2 Analytics Endpoint Replacement

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/routes/unified_governance_routes.py`

**Location:** Lines 881-893 (engine-metrics endpoint)

**Current Code (FAKE DATA):**
```python
@router.get("/api/governance/policies/engine-metrics")
async def get_engine_metrics(db: Session = Depends(get_db)):
    import random

    base_metrics = {
        "average_response_time": round(0.2 + random.uniform(0.1, 0.3), 1),
        "success_rate": round(99.5 + random.uniform(0.0, 0.5), 1),
        "policies_evaluated_today": random.randint(1200, 2000),
        "active_policies": active_policies or 2,
        "total_policies": total_policies or 2,
        "evaluation_throughput": random.randint(800, 1200),
        "cache_hit_rate": round(85.0 + random.uniform(0.0, 10.0), 1),
        "policy_engine_uptime": "99.9%",
        "last_updated": datetime.now(UTC).isoformat()
    }
    return base_metrics
```

**Replacement (REAL DATA):**
```python
from services.policy_analytics_service import get_policy_analytics_service

@router.get("/api/governance/policies/engine-metrics")
async def get_engine_metrics(
    time_range_hours: int = 24,
    db: Session = Depends(get_db)
):
    """
    Get real-time policy engine metrics from database.

    Replaces fake random data with actual evaluation statistics.

    Query Parameters:
        time_range_hours: Analysis period (default 24 hours)

    Returns:
        Real metrics calculated from policy_evaluations table
    """
    analytics_service = get_policy_analytics_service(db)
    metrics = await analytics_service.get_engine_metrics(time_range_hours=time_range_hours)

    # Add policy engine uptime (can still be static or calculated from health checks)
    metrics["policy_engine_uptime"] = "99.9%"  # TODO: Calculate from health check logs

    return metrics
```

**Replacement Benefits:**
- ✅ **Real Data**: Queries actual database records
- ✅ **Backward Compatible**: Returns same JSON structure
- ✅ **Flexible**: Supports time range parameter
- ✅ **Documented**: Clear docstring for future engineers

---

## Part 5: Alembic Migration Design

### 5.1 Migration File

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/alembic/versions/XXXXX_add_policy_evaluations_table.py`

```python
"""add_policy_evaluations_table

Revision ID: XXXXX
Revises: <previous_revision>
Create Date: 2025-11-04 17:30:00

Enterprise Policy Evaluation Tracking
- Adds policy_evaluations table for audit trail
- Creates indexes for query performance
- Enables compliance reporting (SOX, HIPAA, PCI-DSS, GDPR)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXXXX'
down_revision = '<previous_revision>'  # Will be filled by alembic revision
branch_labels = None
depends_on = None


def upgrade():
    """Create policy_evaluations table and indexes"""

    # Create table
    op.create_table(
        'policy_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('policy_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('principal', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('resource', sa.String(length=512), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('evaluation_time_ms', sa.Integer(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('policies_triggered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('matched_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['enterprise_policies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_policy_evaluations_policy_id', 'policy_evaluations', ['policy_id'])
    op.create_index('idx_policy_evaluations_user_id', 'policy_evaluations', ['user_id'])
    op.create_index('idx_policy_evaluations_evaluated_at', 'policy_evaluations', ['evaluated_at'], postgresql_ops={'evaluated_at': 'DESC'})
    op.create_index('idx_policy_evaluations_decision', 'policy_evaluations', ['decision'])
    op.create_index('idx_policy_evaluations_principal', 'policy_evaluations', ['principal'])
    op.create_index('idx_policy_evaluations_date_decision', 'policy_evaluations', ['evaluated_at', 'decision'], postgresql_ops={'evaluated_at': 'DESC'})
    op.create_index('idx_policy_evaluations_policies_triggered_gin', 'policy_evaluations', ['policies_triggered'], postgresql_using='gin')


def downgrade():
    """Drop policy_evaluations table and indexes"""

    # Drop indexes
    op.drop_index('idx_policy_evaluations_policies_triggered_gin', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_date_decision', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_principal', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_decision', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_evaluated_at', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_user_id', table_name='policy_evaluations')
    op.drop_index('idx_policy_evaluations_policy_id', table_name='policy_evaluations')

    # Drop table
    op.drop_table('policy_evaluations')
```

### 5.2 Migration Commands

```bash
# Generate migration file
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
alembic revision --autogenerate -m "add_policy_evaluations_table"

# Review generated migration
cat alembic/versions/XXXXX_add_policy_evaluations_table.py

# Apply migration (local)
alembic upgrade head

# Verify table created
psql -U mac_001 -d owkai_pilot -c "\d policy_evaluations"

# Rollback if needed (testing only)
alembic downgrade -1
```

### 5.3 Migration Safety Checklist

- [ ] **Backward Compatible**: Existing code continues working without migration
- [ ] **Idempotent**: Can run multiple times safely
- [ ] **Reversible**: `downgrade()` fully removes changes
- [ ] **Tested Locally**: Applied and rolled back successfully
- [ ] **Documented**: Comments explain purpose and structure
- [ ] **Zero Downtime**: Table creation doesn't block existing queries
- [ ] **Foreign Key Constraints**: Use `ON DELETE SET NULL` (not CASCADE)

---

## Part 6: Testing Strategy

### 6.1 Unit Tests

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/tests/test_policy_analytics_service.py`

```python
import pytest
from datetime import datetime, UTC
from services.policy_analytics_service import PolicyAnalyticsService
from models import PolicyEvaluation

@pytest.mark.asyncio
async def test_log_evaluation(db_session):
    """Test logging policy evaluation to database"""
    service = PolicyAnalyticsService(db_session)

    result = {
        "decision": "DENY",
        "allowed": False,
        "policies_triggered": [{"policy_id": 1, "policy_name": "test", "effect": "deny"}],
        "evaluation_time_ms": 5,
        "cache_hit": False
    }

    evaluation = await service.log_evaluation(
        evaluation_result=result,
        principal="ai_agent:test",
        action="database:write",
        resource="arn:aws:db:prod/table",
        context={"environment": "production"},
        user_id=1
    )

    assert evaluation.id is not None
    assert evaluation.decision == "DENY"
    assert evaluation.allowed == False
    assert evaluation.evaluation_time_ms == 5

@pytest.mark.asyncio
async def test_get_engine_metrics_empty_database(db_session):
    """Test metrics calculation with no data"""
    service = PolicyAnalyticsService(db_session)

    metrics = await service.get_engine_metrics(time_range_hours=24)

    assert metrics["total_evaluations"] == 0
    assert metrics["evaluations_today"] == 0
    assert metrics["success_rate"] == 100.0  # No errors = 100% success

@pytest.mark.asyncio
async def test_get_engine_metrics_with_data(db_session):
    """Test metrics calculation with sample data"""
    service = PolicyAnalyticsService(db_session)

    # Insert test evaluations
    eval1 = PolicyEvaluation(
        principal="test", action="read", resource="test",
        decision="ALLOW", allowed=True, evaluation_time_ms=10
    )
    eval2 = PolicyEvaluation(
        principal="test", action="write", resource="test",
        decision="DENY", allowed=False, evaluation_time_ms=20
    )
    db_session.add_all([eval1, eval2])
    db_session.commit()

    metrics = await service.get_engine_metrics(time_range_hours=24)

    assert metrics["total_evaluations"] == 2
    assert metrics["denials"] == 1
    assert metrics["average_response_time_ms"] == 15.0  # (10 + 20) / 2
```

### 6.2 Integration Tests

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/tests/test_enforcement_integration.py`

```python
import pytest
from fastapi.testclient import TestClient

def test_policy_enforcement_logs_evaluation(client: TestClient, db_session):
    """Test that policy enforcement creates audit log"""

    # Count evaluations before
    before_count = db_session.query(PolicyEvaluation).count()

    # Enforce policy
    response = client.post("/api/governance/policies/enforce", json={
        "action": "database:read",
        "resource": "arn:aws:db:test/table",
        "context": {"user": "test"}
    })

    assert response.status_code == 200

    # Count evaluations after
    after_count = db_session.query(PolicyEvaluation).count()

    # Verify evaluation was logged
    assert after_count == before_count + 1

    # Verify evaluation data
    evaluation = db_session.query(PolicyEvaluation).order_by(
        PolicyEvaluation.id.desc()
    ).first()

    assert evaluation.action == "database:read"
    assert evaluation.resource == "arn:aws:db:test/table"

def test_analytics_endpoint_returns_real_data(client: TestClient):
    """Test that analytics endpoint returns real metrics"""

    response = client.get("/api/governance/policies/engine-metrics")

    assert response.status_code == 200
    data = response.json()

    # Verify expected fields
    assert "total_evaluations" in data
    assert "evaluations_today" in data
    assert "average_response_time_ms" in data

    # Verify NO random module usage (real data)
    # Real data will be consistent across calls
    response2 = client.get("/api/governance/policies/engine-metrics")
    data2 = response2.json()

    # Same metrics within 1 second should be identical
    assert data["total_evaluations"] == data2["total_evaluations"]
```

### 6.3 Manual Testing Script

**File:** `/tmp/test_phase1_analytics.sh`

```bash
#!/bin/bash
# Phase 1 Analytics Fix - Manual Validation Script

set -e

API_BASE="http://localhost:8000"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Replace with valid token

echo "=========================================="
echo "Phase 1 Analytics Fix - Validation"
echo "=========================================="
echo ""

# Test 1: Enforce policy (should log evaluation)
echo "Test 1: Enforce policy and verify logging..."
curl -s -X POST "$API_BASE/api/governance/policies/enforce" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "database:write",
    "resource": "arn:aws:db:test/table",
    "context": {"environment": "production"}
  }' | jq '.'

echo ""
sleep 1

# Test 2: Get engine metrics (should show real data)
echo "Test 2: Get real engine metrics..."
METRICS1=$(curl -s "$API_BASE/api/governance/policies/engine-metrics" \
  -H "Authorization: Bearer $TOKEN" | jq '.total_evaluations')

sleep 1

METRICS2=$(curl -s "$API_BASE/api/governance/policies/engine-metrics" \
  -H "Authorization: Bearer $TOKEN" | jq '.total_evaluations')

echo "  Metrics Call 1: $METRICS1 evaluations"
echo "  Metrics Call 2: $METRICS2 evaluations"

if [ "$METRICS1" == "$METRICS2" ]; then
    echo "  ✅ SUCCESS: Metrics are consistent (real data)"
else
    echo "  ❌ FAILURE: Metrics changed (still using random data?)"
fi

echo ""

# Test 3: Verify database has records
echo "Test 3: Check database for evaluation records..."
psql -U mac_001 -d owkai_pilot -c "SELECT COUNT(*) as total_evaluations FROM policy_evaluations;"

echo ""
echo "=========================================="
echo "Validation Complete"
echo "=========================================="
```

---

## Part 7: Deployment Plan

### 7.1 Deployment Steps

**Local Development:**
```bash
# 1. Create migration
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
alembic revision --autogenerate -m "add_policy_evaluations_table"

# 2. Review and edit migration if needed
vim alembic/versions/XXXXX_add_policy_evaluations_table.py

# 3. Apply migration
alembic upgrade head

# 4. Verify table
psql -U mac_001 -d owkai_pilot -c "\d policy_evaluations"

# 5. Restart backend
lsof -ti:8000 | xargs kill -9 2>/dev/null
python3 main.py &

# 6. Run tests
pytest tests/test_policy_analytics_service.py -v

# 7. Manual validation
bash /tmp/test_phase1_analytics.sh
```

**Production Deployment:**
```bash
# 1. Create git branch
git checkout -b phase1-analytics-fix
git add alembic/versions/
git add models.py
git add services/policy_analytics_service.py
git add routes/unified_governance_routes.py
git commit -m "Phase 1: Add policy evaluation tracking for analytics

- Create policy_evaluations table for audit trail
- Add PolicyEvaluation SQLAlchemy model
- Implement policy_analytics_service for real metrics
- Replace random data with database queries
- Add comprehensive indexes for performance

Enables SOX/HIPAA/PCI-DSS/GDPR compliance with full audit trail."

git push origin phase1-analytics-fix

# 2. GitHub Actions will build and deploy
# Monitor: aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service

# 3. Verify production deployment
curl https://pilot.owkai.app/api/governance/policies/engine-metrics \
  -H "Authorization: Bearer $PROD_TOKEN"

# 4. Check CloudWatch logs
aws logs tail /ecs/owkai-pilot-backend --since 5m --follow
```

### 7.2 Rollback Procedure

**If issues detected:**
```bash
# Immediate rollback (revert to previous task definition)
aws ecs update-service \
  --cluster owkai-pilot \
  --service owkai-pilot-backend-service \
  --task-definition owkai-pilot-backend:<previous-revision>

# Database rollback (if needed)
alembic downgrade -1

# Code rollback
git revert <commit-hash>
git push origin pilot/master
```

---

## Part 8: Success Criteria

### 8.1 Functional Requirements

- [ ] **Database Table Created**: `policy_evaluations` table exists with proper schema
- [ ] **Model Works**: Can insert and query `PolicyEvaluation` records
- [ ] **Service Functions**: `log_evaluation()` successfully persists data
- [ ] **Analytics Return Real Data**: `get_engine_metrics()` queries database
- [ ] **Route Integration Works**: Policy enforcement logs evaluations
- [ ] **No Breaking Changes**: Existing Cedar engine unchanged
- [ ] **Error Handling**: Logging failures don't crash enforcement

### 8.2 Performance Requirements

- [ ] **Dashboard Load Time**: <200ms for engine metrics query
- [ ] **Enforcement Overhead**: <10ms added latency for logging
- [ ] **Index Performance**: Queries use indexes (verify with EXPLAIN)
- [ ] **No Memory Leaks**: Service instances properly cleaned up

### 8.3 Quality Requirements

- [ ] **Tests Pass**: All unit and integration tests succeed
- [ ] **Code Review**: Changes reviewed for best practices
- [ ] **Documentation**: Docstrings explain all public methods
- [ ] **Backward Compatible**: Old API contracts maintained
- [ ] **Migration Reversible**: Can rollback without data loss

---

## Part 9: Timeline and Effort Estimate

### 9.1 Implementation Breakdown

| Task | Estimated Time | Dependencies |
|------|---------------|--------------|
| 1. Create Alembic migration | 30 minutes | None |
| 2. Add PolicyEvaluation model | 20 minutes | Migration |
| 3. Implement policy_analytics_service.py | 60 minutes | Model |
| 4. Integrate logging in enforcement route | 15 minutes | Service |
| 5. Replace analytics endpoint logic | 20 minutes | Service |
| 6. Write unit tests | 40 minutes | Service |
| 7. Manual testing and validation | 30 minutes | All above |
| 8. Documentation and cleanup | 15 minutes | All above |

**Total Implementation Time:** 3.5 hours

### 9.2 Testing and Deployment

| Task | Estimated Time |
|------|---------------|
| Local testing | 30 minutes |
| Code review | 20 minutes |
| Production deployment | 20 minutes |
| Production validation | 10 minutes |

**Total Testing/Deployment Time:** 1.5 hours

**Grand Total:** 5 hours (rounded up for safety)

---

## Part 10: Risk Assessment

### 10.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Migration fails in production** | Low | High | Test migration locally first, have rollback script ready |
| **Logging causes performance degradation** | Low | Medium | Use async, add circuit breaker, monitor latency |
| **Database fills up with evaluations** | Medium | Medium | Add retention policy (30-90 days), document in Phase 2 |
| **JSONB queries slow on large data** | Low | Medium | GIN indexes handle this, monitor query performance |
| **Service import errors** | Low | Low | Import testing in CI/CD |

### 10.2 Mitigation Strategies

**Performance Monitoring:**
```python
# Add to policy_analytics_service.py
import time

async def log_evaluation(self, ...):
    start_time = time.time()
    try:
        # ... logging logic ...
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > 50:  # Alert if logging takes >50ms
            logger.warning(f"Slow evaluation logging: {elapsed_ms}ms")
```

**Data Retention:**
```sql
-- Add to future migration (Phase 2)
CREATE INDEX idx_policy_evaluations_cleanup
    ON policy_evaluations(evaluated_at)
    WHERE evaluated_at < NOW() - INTERVAL '90 days';

-- Cleanup job (run daily)
DELETE FROM policy_evaluations
WHERE evaluated_at < NOW() - INTERVAL '90 days';
```

---

## Part 11: Quality Gates

Before proceeding to Step 4 (IMPLEMENT):

- [x] **Database schema designed** - ✅ Complete with indexes
- [x] **SQLAlchemy model designed** - ✅ Relationships defined
- [x] **Service API contracts defined** - ✅ Method signatures documented
- [x] **Integration points identified** - ✅ 2 route modifications mapped
- [x] **Migration script planned** - ✅ Upgrade/downgrade paths clear
- [x] **Testing strategy defined** - ✅ Unit, integration, manual tests
- [x] **Deployment plan created** - ✅ Local and production steps
- [x] **Rollback procedure documented** - ✅ Can revert safely
- [x] **Success criteria established** - ✅ Measurable requirements
- [x] **Risk assessment complete** - ✅ Mitigations planned

**Gate Status:** ✅ PASS - Ready to proceed to Step 4 (IMPLEMENT)

---

## Part 12: Next Steps

**Immediate Next Step:** Phase 1 - Step 4: IMPLEMENT

**Implementation Sequence:**
1. Create Alembic migration file
2. Add PolicyEvaluation model to models.py
3. Create policy_analytics_service.py
4. Integrate logging in enforcement route
5. Replace analytics endpoint
6. Write and run tests
7. Validate locally
8. Deploy to production

**Expected Duration:** 3-5 hours (implementation + testing)

---

## Appendix: Code Snippets

### A. Import Statement Additions

**models.py** (top of file):
```python
# No new imports needed - all dependencies already present
from sqlalchemy.dialects.postgresql import JSONB  # Already imported
```

**unified_governance_routes.py** (add to imports):
```python
from services.policy_analytics_service import get_policy_analytics_service
```

### B. Full Service File Template

See Part 3.1 above for complete `policy_analytics_service.py` code.

### C. Database Query Examples

```sql
-- Get today's evaluation count
SELECT COUNT(*) FROM policy_evaluations
WHERE evaluated_at >= CURRENT_DATE;

-- Get denial rate by policy
SELECT policy_id,
       COUNT(*) as total,
       SUM(CASE WHEN decision = 'DENY' THEN 1 ELSE 0 END) as denials,
       ROUND(SUM(CASE WHEN decision = 'DENY' THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100, 1) as denial_rate
FROM policy_evaluations
WHERE evaluated_at >= NOW() - INTERVAL '7 days'
GROUP BY policy_id
ORDER BY denial_rate DESC;

-- Get average response time by hour
SELECT DATE_TRUNC('hour', evaluated_at) as hour,
       AVG(evaluation_time_ms) as avg_response_time
FROM policy_evaluations
WHERE evaluated_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

**Plan Completed:** 2025-11-04 17:30:00 UTC
**Planner:** OW-KAI Engineer
**Status:** ✅ PLAN COMPLETE - READY FOR IMPLEMENTATION
**Next Phase:** Step 4 - IMPLEMENT (Create migration, model, service, integrate routes)
