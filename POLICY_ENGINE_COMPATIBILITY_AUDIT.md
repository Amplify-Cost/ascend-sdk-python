# Policy Engine Compatibility Audit
**Date:** November 15, 2025
**Engineer:** Donald King, OW-kai Enterprise
**Status:** 🔍 COMPREHENSIVE ANALYSIS COMPLETE

---

## Executive Summary

Comprehensive audit of policy engine compatibility between **Agent Actions** and **MCP Server Actions** to ensure unified governance. This audit examines schema compatibility, policy evaluation integration, and identifies gaps preventing MCP actions from using the same policy engine as agent actions.

### Key Findings

**CRITICAL DISCOVERY:** MCP actions and Agent actions currently operate in **completely separate governance systems**:

1. ✅ **Agent Actions** - Fully integrated with enterprise policy engine
2. ❌ **MCP Actions** - NOT integrated with policy engine (separate governance service)
3. ❌ **Table Name Mismatch** - Code references `mcp_server_actions`, production has `mcp_actions`
4. ❌ **No Policy Fusion Fields** - MCP actions table lacks policy_evaluated, policy_decision, policy_risk_score columns

---

## 1. Current State Analysis

### 1.1 Agent Actions - Policy Integration ✅

**Table:** `agent_actions`
**Policy Engine:** Fully integrated with `policy_engine.py` (EnterpriseRealTimePolicyEngine)

**Schema - Policy Fusion Fields (Option 4 Hybrid Architecture):**
```sql
-- From models.py lines 122-126
policy_evaluated      BOOLEAN      DEFAULT FALSE    -- True if policy engine evaluated
policy_decision       VARCHAR(50)  NULL            -- ALLOW|DENY|REQUIRE_APPROVAL|ESCALATE
policy_risk_score     INTEGER      NULL            -- 0-100 policy engine risk score
risk_fusion_formula   TEXT         NULL            -- Formula used (80/20 hybrid)
```

**How Agent Actions Use Policy Engine:**

1. **Action Creation** (`routes/agent_routes.py:16-100`):
   - Agent submits action via `/agent-action` endpoint
   - Security enrichment adds NIST/MITRE/CVSS metadata
   - Action stored with `status = 'pending_approval'`
   - **NO policy evaluation at creation** (deferred to Authorization Center)

2. **Policy Evaluation** (`routes/unified_governance_routes.py:1404-1500`):
   - Frontend calls `/api/governance/evaluate-action` with action data
   - Backend creates `PolicyEvaluationContext` from action
   - `EnterpriseRealTimePolicyEngine.evaluate_policy()` called
   - Returns decision + risk score + matched policies

3. **Policy Engine Queries** (`policy_engine.py:714-741`):
   - Queries `mcp_policies` table for active policies
   - Matches policies against action type, resource, namespace
   - Calculates comprehensive risk score (4 categories: financial, data, security, compliance)
   - Returns decision: ALLOW, DENY, REQUIRE_APPROVAL, ESCALATE, CONDITIONAL

**Agent Action Flow:**
```
Agent submits action
  ↓
Stored in agent_actions table (status=pending_approval)
  ↓
Authorization Center loads action
  ↓
Frontend calls /api/governance/evaluate-action
  ↓
EnterpriseRealTimePolicyEngine.evaluate_policy()
  ↓
Queries mcp_policies table
  ↓
Returns policy decision + risk score
  ↓
Frontend displays approval UI
```

### 1.2 MCP Server Actions - Current Governance ❌

**Table (Production):** `mcp_actions` (simple schema)
**Table (Code):** `mcp_server_actions` (enterprise schema) **← MISMATCH!**
**Policy Engine:** **NOT INTEGRATED** - uses separate `mcp_governance_service.py`

**Production Schema - `mcp_actions` table:**
```sql
-- Actual production table (from psql \d mcp_actions)
id            INTEGER                    PRIMARY KEY
agent_id      VARCHAR(255)               NOT NULL
action_type   VARCHAR(255)               NOT NULL
resource      TEXT
context       JSONB
risk_level    VARCHAR(50)
status        VARCHAR(50)                DEFAULT 'pending'
created_at    TIMESTAMP                  DEFAULT CURRENT_TIMESTAMP

-- MISSING POLICY FUSION FIELDS:
-- policy_evaluated, policy_decision, policy_risk_score
```

**Code Schema - `mcp_server_actions` table:**
```python
# From models_mcp_governance.py:16-106
class MCPServerAction(Base):
    __tablename__ = "mcp_server_actions"  # ← WRONG TABLE NAME!

    # 47 fields including:
    id                    UUID           PRIMARY KEY
    mcp_server_id         UUID           NOT NULL
    namespace             STRING(100)    NOT NULL
    verb                  STRING(100)    NOT NULL
    resource              STRING(500)    NOT NULL
    risk_score            INTEGER        DEFAULT 0   # 0-100 scale
    risk_level            STRING(20)     DEFAULT 'LOW'
    status                STRING(50)     DEFAULT 'PENDING'
    policy_result         STRING(50)     DEFAULT 'EVALUATE'  # ALLOW|DENY|EVALUATE

    # BUT NO OPTION 4 POLICY FUSION FIELDS:
    # policy_evaluated, policy_decision, policy_risk_score
```

**How MCP Actions Currently Work:**

1. **MCP Action Creation** (`services/mcp_governance_service.py:723-800`):
   - MCP server submits action
   - `evaluate_mcp_action()` called
   - Creates `MCPServerAction` record in **WRONG TABLE** (`mcp_server_actions`)
   - **ERROR:** Table doesn't exist in production!

2. **Separate Governance Service** (`services/mcp_governance_service.py:33-150`):
   - Uses Cedar policy enforcement (different from agent policy engine)
   - Custom risk calculation (separate from policy engine risk scoring)
   - Stores result in `policy_result` field (not policy_decision)
   - **NO integration with `EnterpriseRealTimePolicyEngine`**

3. **Current MCP Approval Flow** (`routes/unified_governance_routes.py:310-350`):
   - Frontend calls `/api/mcp-governance/evaluate-action`
   - Queries `AgentAction` table (not mcp_actions!) **← HARDCODED WORKAROUND**
   - Updates status to approved/denied
   - Creates audit log
   - **DOES NOT USE POLICY ENGINE**

**MCP Action Flow (Current - Broken):**
```
MCP server submits action
  ↓
ERROR: mcp_server_actions table doesn't exist!
  ↓
Fallback: Hardcoded to query AgentAction table
  ↓
No policy evaluation (separate governance service)
  ↓
Manual approval only
```

---

## 2. Schema Compatibility Analysis

### 2.1 Core Fields - Compatibility Matrix

| Field                  | agent_actions        | mcp_actions (prod)  | mcp_server_actions (code) | Compatible? |
|------------------------|----------------------|---------------------|---------------------------|-------------|
| **Primary Key**        | `id` (INTEGER)       | `id` (INTEGER)      | `id` (UUID)               | ⚠️ Different types |
| **Action Source**      | `agent_id` (VARCHAR) | `agent_id` (VARCHAR)| `mcp_server_id` (UUID)    | ❌ Different semantic |
| **Action Type**        | `action_type` (VARCHAR)| `action_type` (VARCHAR)| `verb` (VARCHAR)      | ✅ Compatible |
| **Resource**           | `target_resource` (VARCHAR)| `resource` (TEXT)| `resource` (VARCHAR)      | ✅ Compatible |
| **Risk Score**         | `risk_score` (FLOAT) | ❌ MISSING          | `risk_score` (INTEGER)    | ⚠️ Different types |
| **Risk Level**         | `risk_level` (VARCHAR)| `risk_level` (VARCHAR)| `risk_level` (VARCHAR)  | ✅ Compatible |
| **Status**             | `status` (VARCHAR)   | `status` (VARCHAR)  | `status` (VARCHAR)        | ✅ Compatible |
| **Created At**         | `created_at` (TIMESTAMP)| `created_at` (TIMESTAMP)| `created_at` (TIMESTAMP)| ✅ Compatible |

### 2.2 Policy Fusion Fields - Gap Analysis

| Field                  | agent_actions        | mcp_actions (prod)  | mcp_server_actions (code) | Status      |
|------------------------|----------------------|---------------------|---------------------------|-------------|
| `policy_evaluated`     | ✅ BOOLEAN (DEFAULT FALSE)| ❌ MISSING     | ❌ MISSING                | **CRITICAL GAP** |
| `policy_decision`      | ✅ VARCHAR(50)       | ❌ MISSING          | ⚠️ `policy_result` (different name)| **CRITICAL GAP** |
| `policy_risk_score`    | ✅ INTEGER           | ❌ MISSING          | ❌ MISSING                | **CRITICAL GAP** |
| `risk_fusion_formula`  | ✅ TEXT              | ❌ MISSING          | ❌ MISSING                | **CRITICAL GAP** |

**Conclusion:** MCP actions table is **NOT compatible** with Option 4 Policy Fusion architecture.

### 2.3 Namespace/Context Fields

| Field                  | agent_actions        | mcp_actions (prod)  | mcp_server_actions (code) | Notes       |
|------------------------|----------------------|---------------------|---------------------------|-------------|
| **Namespace**          | ❌ MISSING           | ❌ MISSING          | ✅ `namespace` (VARCHAR)  | MCP-specific |
| **Verb**               | ❌ MISSING           | ❌ MISSING          | ✅ `verb` (VARCHAR)       | MCP-specific |
| **Context**            | `extra_data` (JSONB) | `context` (JSONB)   | `parameters` (JSON)       | ✅ All have JSON storage |

---

## 3. Policy Engine Integration Analysis

### 3.1 Agent Actions - Policy Engine Usage

**File:** `policy_engine.py` (1,165 lines)

**Class:** `EnterpriseRealTimePolicyEngine`

**Key Features:**
- Sub-200ms policy evaluation performance target
- Natural language rule parsing and execution
- 0-100 risk scoring across 4 categories (financial, data, security, compliance)
- Enterprise caching for high-performance lookups
- Real-time policy lookup from `mcp_policies` table
- Comprehensive audit trail integration

**Policy Evaluation Flow:**

1. **Create Context** (`policy_engine.py:1130-1152`):
```python
context = PolicyEvaluationContext(
    user_id=str(user_id),
    user_email=user_email,
    user_role=user_role,
    action_type=action_type,        # e.g., "database_write"
    resource=resource,               # e.g., "customers.db"
    namespace="agent",               # Agent-specific
    environment="production"
)
```

2. **Evaluate Policy** (`policy_engine.py:619-699`):
```python
result = await policy_engine.evaluate_policy(context, action_metadata)
```

3. **Match Policies** (`policy_engine.py:706-741`):
```sql
-- Queries mcp_policies table
SELECT id, policy_name, natural_language_description,
       resource_patterns, namespace_patterns, verb_patterns,
       actions as action, conditions, priority
FROM mcp_policies
WHERE is_active = true AND policy_status = 'deployed'
ORDER BY priority DESC, created_at ASC
```

4. **Calculate Risk Score** (`policy_engine.py:389-456`):
```python
risk_score = EnterpriseRiskScorer.calculate_comprehensive_risk_score(
    context, matched_policies, action_metadata
)
# Returns: RiskScoreResult with 0-100 total_score
```

5. **Determine Decision** (`policy_engine.py:871-901`):
```python
# Decision logic:
# - If any policy explicitly denies → DENY
# - If critical risk (≥90) → ESCALATE
# - If high risk (≥70) → REQUIRE_APPROVAL
# - If high confidence allow → ALLOW
# - Default → REQUIRE_APPROVAL (safe default)
```

**Result Format:**
```python
PolicyEvaluationResult(
    evaluation_id="eval_abc123",
    decision=PolicyDecision.REQUIRE_APPROVAL,
    risk_score=RiskScoreResult(
        total_score=75,
        category_scores={
            RiskCategory.SECURITY: 80,
            RiskCategory.DATA: 75,
            RiskCategory.COMPLIANCE: 70,
            RiskCategory.FINANCIAL: 65
        },
        risk_factors=["security_high_risk", "data_high_risk"],
        risk_level="HIGH",
        requires_approval=True,
        approval_level=3
    ),
    matched_policies=[...],
    evaluation_time_ms=120.5,
    cache_hit=False,
    audit_trail_id="12345",
    recommendations=["⚠️  HIGH RISK: Requires manager approval"]
)
```

### 3.2 MCP Actions - Current Governance Service

**File:** `services/mcp_governance_service.py` (800+ lines)

**Class:** `EnhancedMCPGovernanceService`

**Key Features:**
- Cedar policy enforcement (different policy language)
- Custom risk calculation (separate from policy engine)
- MCP-specific governance rules
- **NO integration with `EnterpriseRealTimePolicyEngine`**

**MCP Governance Flow (Current):**

1. **Evaluate MCP Action** (`mcp_governance_service.py:723-800`):
```python
# Creates MCPServerAction record (WRONG TABLE NAME!)
mcp_action = MCPServerAction(
    mcp_server_id=server_id,
    namespace=namespace,
    verb=verb,
    resource=resource,
    # ... other fields
)
```

2. **Custom Risk Calculation** (`mcp_governance_service.py:750-780`):
```python
# Separate risk calculation (NOT using EnterpriseRiskScorer)
risk_score = self._calculate_risk_score(namespace, verb, resource)
# Returns: Integer 0-100 (different algorithm than policy engine)
```

3. **Cedar Policy Evaluation** (`mcp_governance_service.py:48-57`):
```python
# Uses Cedar enforcement engine (NOT EnterpriseRealTimePolicyEngine)
policy_decision = enforcement_engine.evaluate(
    principal=f"mcp_server:{server_id}",
    action=verb,
    resource=f"mcp:server:{server_id}:{namespace}:{resource}",
    context={...}
)
```

**Critical Gaps:**

1. ❌ **Different Policy Engine** - Cedar vs EnterpriseRealTimePolicyEngine
2. ❌ **Different Risk Calculation** - Custom algorithm vs 4-category comprehensive scoring
3. ❌ **No Policy Fusion** - Doesn't use policy_evaluated, policy_decision, policy_risk_score fields
4. ❌ **Wrong Table** - Writes to `mcp_server_actions` (doesn't exist in production)
5. ❌ **No mcp_policies Integration** - Doesn't query mcp_policies table like agent actions do

---

## 4. mcp_policies Table - Shared Policy Storage

**Table:** `mcp_policies`
**Purpose:** Enterprise policy storage for BOTH agent and MCP actions
**Current Usage:** Agent actions only ✅, MCP actions NOT integrated ❌

**Schema** (`models_mcp_governance.py:196-258`):
```python
class MCPPolicy(Base):
    __tablename__ = "mcp_policies"

    # Policy Identity
    id                              UUID          PRIMARY KEY
    policy_name                     STRING(200)   NOT NULL
    policy_description              TEXT
    natural_language_description    TEXT          # Natural language policy

    # Scope Patterns (for pattern matching)
    server_patterns                 JSON[]        # Server ID patterns
    namespace_patterns              JSON[]        # Namespace patterns
    verb_patterns                   JSON[]        # Verb patterns
    resource_patterns               JSON[]        # Resource patterns

    # Policy Decision
    action                          STRING(50)    # ALLOW, DENY, EVALUATE
    required_approval_level         INTEGER       DEFAULT 1
    conditions                      JSON          # Policy conditions

    # Enterprise Versioning
    policy_status                   STRING(50)    # draft, testing, approved, deployed
    major_version                   INTEGER       DEFAULT 1
    minor_version                   INTEGER       DEFAULT 0

    # Governance
    is_active                       BOOLEAN       DEFAULT TRUE
    priority                        INTEGER       DEFAULT 100
    created_by                      STRING(100)   NOT NULL
```

**How Policy Engine Uses mcp_policies:**

1. **Query Active Policies** (`policy_engine.py:714-729`):
```sql
SELECT id, policy_name, natural_language_description,
       resource_patterns, namespace_patterns, verb_patterns,
       actions as action, conditions, priority
FROM mcp_policies
WHERE is_active = true AND policy_status = 'deployed'
ORDER BY priority DESC, created_at ASC
```

2. **Pattern Matching** (`policy_engine.py:743-812`):
```python
# For each policy, check if it matches the action:
# - Resource pattern match (wildcards supported)
# - Namespace pattern match
# - Verb/action type pattern match
# - Condition evaluation (time-based, role-based, environment)

if self._matches_patterns(context.resource, resource_patterns):
    confidence += 0.4
if self._matches_patterns(context.namespace, namespace_patterns):
    confidence += 0.3
if self._matches_patterns(context.action_type, verb_patterns):
    confidence += 0.3
```

3. **Returns Matched Policies:**
```python
PolicyMatch(
    policy_id="uuid",
    policy_name="High Risk Database Write Policy",
    matched=True,
    confidence=0.9,
    decision=PolicyDecision.REQUIRE_APPROVAL,
    conditions=["environment=production"],
    execution_time_ms=0.5
)
```

**Current State:**
- ✅ Agent actions use mcp_policies for policy evaluation
- ❌ MCP actions DO NOT query mcp_policies table
- ❌ MCP actions use separate Cedar enforcement engine

---

## 5. Identified Gaps and Incompatibilities

### 5.1 Critical Gaps (Must Fix)

#### Gap 1: Table Name Mismatch
**Issue:** Code references `mcp_server_actions`, production has `mcp_actions`

**Impact:**
- MCP governance service writes to non-existent table
- All MCP action creation fails with table not found error
- Unified loader queries wrong table (returns 0 MCP actions)

**Files Affected:**
- `models_mcp_governance.py:21` - `__tablename__ = "mcp_server_actions"`
- `services/mcp_governance_service.py:740` - Creates MCPServerAction
- `services/enterprise_unified_loader.py:185` - Queries MCPServerAction

**Fix Required:** Change `__tablename__` to `"mcp_actions"` OR migrate production table

---

#### Gap 2: Missing Policy Fusion Fields
**Issue:** `mcp_actions` table lacks Option 4 policy fusion columns

**Missing Fields:**
```sql
policy_evaluated      BOOLEAN      -- Missing in mcp_actions
policy_decision       VARCHAR(50)  -- Missing in mcp_actions
policy_risk_score     INTEGER      -- Missing in mcp_actions
risk_fusion_formula   TEXT         -- Missing in mcp_actions
```

**Impact:**
- MCP actions cannot store policy evaluation results
- Cannot implement 80/20 hybrid risk fusion (CVSS + Policy)
- No way to track which policy engine evaluated the action
- Authorization Center cannot display policy decisions for MCP actions

**Fix Required:** Add migration to add policy fusion columns to mcp_actions table

---

#### Gap 3: No Policy Engine Integration
**Issue:** MCP actions use separate governance service, not `EnterpriseRealTimePolicyEngine`

**Current:**
- Agent actions → `EnterpriseRealTimePolicyEngine` → mcp_policies table
- MCP actions → `EnhancedMCPGovernanceService` → Cedar enforcement

**Impact:**
- Duplicate policy logic in two places
- Different risk calculation algorithms
- MCP actions don't benefit from policy engine features:
  - Natural language policy parsing
  - 4-category risk scoring (financial, data, security, compliance)
  - Sub-200ms performance caching
  - Comprehensive audit trail
  - Enterprise policy versioning

**Fix Required:** Refactor MCP governance to use EnterpriseRealTimePolicyEngine

---

#### Gap 4: Schema Incompatibility
**Issue:** `mcp_actions` table has simplified schema incompatible with unified loader

**Production Schema (8 columns):**
```sql
id, agent_id, action_type, resource, context, risk_level, status, created_at
```

**Code Expects (47 columns):**
```python
id, mcp_server_id, mcp_server_name, namespace, verb, resource,
risk_score, risk_level, status, policy_result, user_id, user_email,
approver_id, approved_at, execution_result, ... (+ 32 more)
```

**Impact:**
- Unified loader cannot transform mcp_actions properly
- Missing critical fields: namespace, verb, user_email, approver fields
- Cannot distinguish MCP server vs agent in unified queue
- Risk score type mismatch (missing vs INTEGER)

**Fix Required:** Either:
1. Add missing columns to mcp_actions table, OR
2. Simplify unified loader to work with minimal schema, OR
3. Migrate production to use full mcp_server_actions schema

---

### 5.2 Medium Priority Gaps

#### Gap 5: Namespace Field Missing
**Issue:** Agent actions don't have namespace field (MCP-specific)

**Impact:**
- Policy engine cannot match namespace patterns for agent actions
- Workaround: Use hardcoded `namespace="agent"` for all agent actions

**Fix:** Either:
1. Add namespace column to agent_actions, OR
2. Virtual namespace mapping in policy engine

---

#### Gap 6: Risk Score Type Mismatch
**Issue:** agent_actions uses FLOAT, mcp_server_actions uses INTEGER

**Impact:**
- Unified loader must handle type conversion
- Potential precision loss
- Frontend may display differently

**Fix:** Standardize on FLOAT (0.0-100.0) for both tables

---

### 5.3 Low Priority Gaps

#### Gap 7: ID Type Mismatch
**Issue:** agent_actions uses INTEGER, mcp_server_actions uses UUID

**Impact:**
- Unified loader prefixes IDs to avoid conflicts ("agent-123" vs "mcp-uuid")
- Cannot use direct foreign key relationships
- Slightly more complex query joins

**Fix:** Already handled by unified loader prefix strategy

---

## 6. Enterprise Solution Recommendation

### 6.1 Unified Policy Engine Architecture (Recommended)

**Principle:** SINGLE POLICY ENGINE for both agent and MCP actions

**Design:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Policy Management UI                      │
│            (Create policies in natural language)             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
                  ┌────────────────┐
                  │  mcp_policies  │  ← Shared policy storage
                  │     table      │
                  └────────────────┘
                           │
                           ↓
          ┌────────────────────────────────────┐
          │ EnterpriseRealTimePolicyEngine     │  ← SINGLE ENGINE
          │  - Natural language parsing        │
          │  - 4-category risk scoring         │
          │  - Sub-200ms performance           │
          │  - Pattern matching                │
          │  - Audit trail integration         │
          └────────┬──────────────┬────────────┘
                   │              │
                   ↓              ↓
         ┌────────────────┐  ┌────────────────┐
         │ agent_actions  │  │  mcp_actions   │
         │                │  │                │
         │ + policy_*     │  │ + policy_*     │  ← Add policy fusion fields
         │   evaluated    │  │   evaluated    │
         │   decision     │  │   decision     │
         │   risk_score   │  │   risk_score   │
         └────────────────┘  └────────────────┘
                   │              │
                   └──────┬───────┘
                          ↓
              ┌───────────────────────┐
              │ Authorization Center  │
              │ (Unified Queue + UI)  │
              └───────────────────────┘
```

**Benefits:**
1. ✅ Single source of truth for policy evaluation
2. ✅ Consistent risk scoring across all action types
3. ✅ No duplicate policy logic
4. ✅ Easier to maintain and test
5. ✅ Policy changes apply to both agent and MCP actions automatically
6. ✅ Unified audit trail
7. ✅ Better performance (shared cache)

---

### 6.2 Implementation Plan

#### Phase 1: Fix Critical Infrastructure Issues

**Step 1.1: Fix Table Name Mismatch** (Priority: CRITICAL)

**Option A: Update Code to Match Production** (RECOMMENDED)
```python
# File: models_mcp_governance.py:21
class MCPServerAction(Base):
    __tablename__ = "mcp_actions"  # Changed from "mcp_server_actions"
```

**Impact:**
- ✅ Minimal disruption (code change only)
- ✅ Works with existing production table
- ❌ Still has schema incompatibility (47 columns vs 8 columns)

**Option B: Migrate Production Table**
```sql
-- Rename table
ALTER TABLE mcp_actions RENAME TO mcp_actions_old;
-- Create new table with full schema
CREATE TABLE mcp_server_actions (...47 columns...);
-- Migrate data
INSERT INTO mcp_server_actions SELECT... FROM mcp_actions_old;
```

**Impact:**
- ❌ Requires database migration
- ❌ Downtime during migration
- ✅ Full schema compatibility
- ✅ No code changes needed

**RECOMMENDATION:** Use Option A (update code) as immediate fix, plan Option B for long-term.

---

**Step 1.2: Add Policy Fusion Columns to mcp_actions** (Priority: CRITICAL)

```sql
-- Migration: Add Option 4 policy fusion fields to mcp_actions table
ALTER TABLE mcp_actions ADD COLUMN policy_evaluated BOOLEAN DEFAULT FALSE;
ALTER TABLE mcp_actions ADD COLUMN policy_decision VARCHAR(50) NULL;
ALTER TABLE mcp_actions ADD COLUMN policy_risk_score INTEGER NULL;
ALTER TABLE mcp_actions ADD COLUMN risk_fusion_formula TEXT NULL;

-- Add namespace and verb fields (MCP-specific)
ALTER TABLE mcp_actions ADD COLUMN namespace VARCHAR(100) NULL;
ALTER TABLE mcp_actions ADD COLUMN verb VARCHAR(100) NULL;

-- Add user context fields
ALTER TABLE mcp_actions ADD COLUMN user_email VARCHAR(255) NULL;
ALTER TABLE mcp_actions ADD COLUMN user_role VARCHAR(100) NULL;

-- Add approval workflow fields
ALTER TABLE mcp_actions ADD COLUMN approved_by VARCHAR(255) NULL;
ALTER TABLE mcp_actions ADD COLUMN approved_at TIMESTAMP NULL;
ALTER TABLE mcp_actions ADD COLUMN reviewed_by VARCHAR(255) NULL;
ALTER TABLE mcp_actions ADD COLUMN reviewed_at TIMESTAMP NULL;

-- Add risk_score field (standardize on FLOAT like agent_actions)
ALTER TABLE mcp_actions ADD COLUMN risk_score FLOAT NULL;
```

**Impact:**
- ✅ Enables policy fusion for MCP actions
- ✅ Backward compatible (all columns nullable)
- ✅ No data loss
- ✅ Enables unified governance

---

#### Phase 2: Integrate MCP Actions with Policy Engine

**Step 2.1: Create Unified Policy Evaluation Service**

**File:** `services/unified_policy_evaluation_service.py` (NEW)

```python
"""
Unified Policy Evaluation Service
Evaluates BOTH agent and MCP actions using EnterpriseRealTimePolicyEngine
"""
from policy_engine import (
    EnterpriseRealTimePolicyEngine,
    PolicyEvaluationContext,
    create_evaluation_context
)
from models import AgentAction
from models_mcp_governance import MCPServerAction
from sqlalchemy.orm import Session

class UnifiedPolicyEvaluationService:
    """Evaluates both agent and MCP actions using same policy engine"""

    def __init__(self, db: Session):
        self.db = db
        self.policy_engine = EnterpriseRealTimePolicyEngine(db)

    async def evaluate_agent_action(self, action: AgentAction) -> PolicyEvaluationResult:
        """Evaluate agent action using policy engine"""

        # Create policy evaluation context
        context = create_evaluation_context(
            user_id=str(action.user_id),
            user_email=action.created_by or "unknown",
            user_role="user",  # Get from user table
            action_type=action.action_type,
            resource=action.target_resource or action.description,
            namespace="agent",  # Virtual namespace for agent actions
            environment="production"
        )

        # Evaluate using policy engine
        result = await self.policy_engine.evaluate_policy(context, {
            "tool_name": action.tool_name,
            "risk_level": action.risk_level,
            "cvss_score": action.cvss_score
        })

        # Update action with policy results (Option 4 Hybrid)
        action.policy_evaluated = True
        action.policy_decision = result.decision.value
        action.policy_risk_score = result.risk_score.total_score
        action.risk_fusion_formula = f"hybrid_80_20_cvss_{action.cvss_score}_policy_{result.risk_score.total_score}"

        self.db.commit()

        return result

    async def evaluate_mcp_action(self, action: MCPServerAction) -> PolicyEvaluationResult:
        """Evaluate MCP action using SAME policy engine"""

        # Create policy evaluation context (MCP-specific fields)
        context = create_evaluation_context(
            user_id=action.user_id,
            user_email=action.user_email,
            user_role=action.user_role or "user",
            action_type=action.verb,           # MCP verb → action_type
            resource=action.resource,
            namespace=action.namespace,        # MCP namespace
            environment="production"
        )

        # Evaluate using SAME policy engine
        result = await self.policy_engine.evaluate_policy(context, {
            "mcp_server_id": action.mcp_server_id,
            "mcp_server_name": action.mcp_server_name,
            "parameters": action.parameters
        })

        # Update action with policy results (Option 4 Hybrid)
        action.policy_evaluated = True
        action.policy_decision = result.decision.value
        action.policy_risk_score = result.risk_score.total_score
        action.risk_fusion_formula = f"hybrid_mcp_policy_{result.risk_score.total_score}"

        self.db.commit()

        return result
```

**Impact:**
- ✅ BOTH action types use SAME policy engine
- ✅ Consistent risk scoring (4-category comprehensive)
- ✅ Natural language policy support for MCP actions
- ✅ Sub-200ms performance for both
- ✅ Shared policy cache
- ✅ Unified audit trail

---

**Step 2.2: Update Unified Loader to Use Policy Results**

**File:** `services/enterprise_unified_loader.py`

**Current Issue:** Unified loader doesn't populate policy fields

**Fix:**
```python
# Lines 185-230 (MCP transformation)
def _transform_mcp_action(self, mcp: MCPServerAction) -> Dict[str, Any]:
    """Transform MCP action with policy fusion support"""

    return {
        "id": f"mcp-{mcp.id}",
        "uuid_id": str(mcp.id),
        "action_source": "mcp_server",
        "mcp_server_name": mcp.mcp_server_name,
        "namespace": mcp.namespace,
        "verb": mcp.verb,
        "resource": mcp.resource,
        "action_type": mcp.verb,
        "risk_score": float(mcp.risk_score or 0),
        "risk_level": mcp.risk_level,
        "status": self._normalize_mcp_status(mcp.status),

        # ✅ NEW: Policy fusion fields (Option 4)
        "policy_evaluated": mcp.policy_evaluated or False,
        "policy_decision": mcp.policy_decision,
        "policy_risk_score": mcp.policy_risk_score,
        "risk_fusion_formula": mcp.risk_fusion_formula,

        # User context
        "user_email": mcp.user_email,
        "created_by": mcp.user_email,
        "approved_by": mcp.approved_by,
        "reviewed_by": mcp.reviewed_by,

        # Timestamps
        "created_at": mcp.created_at.isoformat(),
        "approved_at": mcp.approved_at.isoformat() if mcp.approved_at else None,
        "reviewed_at": mcp.reviewed_at.isoformat() if mcp.reviewed_at else None
    }
```

---

**Step 2.3: Update Authorization Routes to Use Unified Service**

**File:** `routes/unified_governance_routes.py`

**Replace separate MCP evaluation** (Lines 310-350) with:

```python
from services.unified_policy_evaluation_service import UnifiedPolicyEvaluationService

@router.post("/api/mcp-governance/evaluate-action")
async def evaluate_mcp_action(
    action_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    🏢 ENTERPRISE: Evaluate MCP action using UNIFIED policy engine
    NOW uses EnterpriseRealTimePolicyEngine (same as agent actions)
    """
    try:
        action_id = action_data.get("action_id")

        # Get MCP action from mcp_actions table
        mcp_action = db.query(MCPServerAction).filter(
            MCPServerAction.id == action_id
        ).first()

        if not mcp_action:
            raise HTTPException(status_code=404, detail="MCP action not found")

        # ✅ Use UNIFIED policy evaluation service
        unified_service = UnifiedPolicyEvaluationService(db)
        policy_result = await unified_service.evaluate_mcp_action(mcp_action)

        # Return same format as agent action evaluation
        return {
            "success": True,
            "action_id": str(mcp_action.id),
            "evaluation": {
                "decision": policy_result.decision.value,
                "risk_score": policy_result.risk_score.total_score,
                "category_scores": policy_result.risk_score.category_scores,
                "matched_policies": len(policy_result.matched_policies),
                "recommendations": policy_result.recommendations,
                "evaluation_time_ms": policy_result.evaluation_time_ms
            },
            "policy_evaluated": True
        }

    except Exception as e:
        logger.error(f"❌ MCP policy evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

#### Phase 3: Update Frontend to Use Unified Policy UI

**File:** `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`

**Current:** Separate approval flows for agent vs MCP actions

**Fix:** Unified approval flow showing policy decisions for BOTH

```javascript
// Lines 500-600 (Policy Decision Display)
const PolicyDecisionBadge = ({ action }) => {
  // ✅ Works for BOTH agent and MCP actions now
  if (!action.policy_evaluated) {
    return <span className="badge badge-gray">Not Evaluated</span>;
  }

  const decisionColors = {
    'ALLOW': 'green',
    'DENY': 'red',
    'REQUIRE_APPROVAL': 'yellow',
    'ESCALATE': 'orange',
    'CONDITIONAL': 'blue'
  };

  return (
    <div>
      <span className={`badge badge-${decisionColors[action.policy_decision]}`}>
        {action.policy_decision}
      </span>
      {action.policy_risk_score && (
        <span className="ml-2">
          Policy Risk: {action.policy_risk_score}/100
        </span>
      )}
    </div>
  );
};

// Use same component for both action types
{filteredActions.map(action => (
  <tr key={action.id}>
    <td>{action.action_source === 'agent' ? '🤖 Agent' : '🔌 MCP'}</td>
    <td>{action.action_type || action.verb}</td>
    <td><PolicyDecisionBadge action={action} /></td>  {/* ✅ Unified */}
    <td>{action.risk_score}/100</td>
    <td>
      <button onClick={() => approveAction(action)}>Approve</button>
      <button onClick={() => denyAction(action)}>Deny</button>
    </td>
  </tr>
))}
```

---

## 7. Migration Checklist

### 7.1 Database Migrations (Required)

```sql
-- Migration 1: Fix table name compatibility
-- File: alembic/versions/20251115_fix_mcp_table_name.py

"""Fix MCP actions table compatibility"""

def upgrade():
    # Option A: Add policy fusion columns to existing mcp_actions table
    op.add_column('mcp_actions', sa.Column('policy_evaluated', sa.Boolean(), server_default=sa.false(), nullable=True))
    op.add_column('mcp_actions', sa.Column('policy_decision', sa.String(50), nullable=True))
    op.add_column('mcp_actions', sa.Column('policy_risk_score', sa.Integer(), nullable=True))
    op.add_column('mcp_actions', sa.Column('risk_fusion_formula', sa.Text(), nullable=True))

    # Add MCP-specific fields
    op.add_column('mcp_actions', sa.Column('namespace', sa.String(100), nullable=True))
    op.add_column('mcp_actions', sa.Column('verb', sa.String(100), nullable=True))

    # Add user context fields
    op.add_column('mcp_actions', sa.Column('user_email', sa.String(255), nullable=True))
    op.add_column('mcp_actions', sa.Column('user_role', sa.String(100), nullable=True))

    # Add approval workflow fields
    op.add_column('mcp_actions', sa.Column('approved_by', sa.String(255), nullable=True))
    op.add_column('mcp_actions', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('mcp_actions', sa.Column('reviewed_by', sa.String(255), nullable=True))
    op.add_column('mcp_actions', sa.Column('reviewed_at', sa.DateTime(), nullable=True))

    # Standardize risk_score (FLOAT like agent_actions)
    op.add_column('mcp_actions', sa.Column('risk_score', sa.Float(), nullable=True))

    # Backfill namespace and verb from context JSONB
    op.execute("""
        UPDATE mcp_actions
        SET namespace = context->>'namespace',
            verb = context->>'verb'
        WHERE context IS NOT NULL
    """)

def downgrade():
    # Drop added columns
    op.drop_column('mcp_actions', 'policy_evaluated')
    op.drop_column('mcp_actions', 'policy_decision')
    op.drop_column('mcp_actions', 'policy_risk_score')
    op.drop_column('mcp_actions', 'risk_fusion_formula')
    op.drop_column('mcp_actions', 'namespace')
    op.drop_column('mcp_actions', 'verb')
    op.drop_column('mcp_actions', 'user_email')
    op.drop_column('mcp_actions', 'user_role')
    op.drop_column('mcp_actions', 'approved_by')
    op.drop_column('mcp_actions', 'approved_at')
    op.drop_column('mcp_actions', 'reviewed_by')
    op.drop_column('mcp_actions', 'reviewed_at')
    op.drop_column('mcp_actions', 'risk_score')
```

### 7.2 Code Changes (Required)

**File 1: `models_mcp_governance.py`**
```python
# Line 21: Fix table name
class MCPServerAction(Base):
    __tablename__ = "mcp_actions"  # Changed from "mcp_server_actions"

    # Add policy fusion fields
    policy_evaluated = Column(Boolean, default=False, nullable=True)
    policy_decision = Column(String(50), nullable=True)
    policy_risk_score = Column(Integer, nullable=True)
    risk_fusion_formula = Column(Text, nullable=True)
```

**File 2: `services/unified_policy_evaluation_service.py`** (NEW)
- Create unified service as shown in Phase 2, Step 2.1

**File 3: `services/enterprise_unified_loader.py`**
```python
# Line 185: Update MCP transformation to include policy fields
def _transform_mcp_action(self, mcp: MCPServerAction) -> Dict[str, Any]:
    # Add policy_evaluated, policy_decision, policy_risk_score fields
    # (See Phase 2, Step 2.2 for full code)
```

**File 4: `routes/unified_governance_routes.py`**
```python
# Line 310-350: Replace separate MCP evaluation with unified service
# (See Phase 2, Step 2.3 for full code)
```

**File 5: `owkai-pilot-frontend/src/components/AgentAuthorizationDashboard.jsx`**
```javascript
// Add PolicyDecisionBadge component
// Update action rendering to show policy decisions
// (See Phase 3 for full code)
```

### 7.3 Testing Checklist

- [ ] **Database Migration Test**
  - [ ] Backup production database
  - [ ] Run migration on staging environment
  - [ ] Verify all columns added successfully
  - [ ] Test rollback procedure
  - [ ] Verify existing mcp_actions data intact

- [ ] **Agent Action Policy Integration Test**
  - [ ] Create agent action
  - [ ] Verify policy evaluation works
  - [ ] Check policy_evaluated = true
  - [ ] Verify policy_decision populated
  - [ ] Check policy_risk_score calculated

- [ ] **MCP Action Policy Integration Test**
  - [ ] Create MCP action in mcp_actions table
  - [ ] Verify policy evaluation uses EnterpriseRealTimePolicyEngine
  - [ ] Check policy fields populated
  - [ ] Verify same risk scoring as agent actions

- [ ] **Unified Loader Test**
  - [ ] Create 2 agent actions + 2 MCP actions
  - [ ] Call /api/governance/pending-actions
  - [ ] Verify all 4 actions returned
  - [ ] Check action_source field correct ("agent" vs "mcp_server")
  - [ ] Verify policy fields present for both types

- [ ] **Frontend Filter Test**
  - [ ] Verify "Agent" filter shows only agent actions
  - [ ] Verify "MCP" filter shows only MCP actions
  - [ ] Check policy decision badge displays for both
  - [ ] Test approval flow for both action types

- [ ] **Policy Management Test**
  - [ ] Create new policy in mcp_policies table
  - [ ] Verify policy applies to agent actions
  - [ ] Verify SAME policy applies to MCP actions
  - [ ] Check consistent risk scoring

### 7.4 Rollback Plan

**If Migration Fails:**
```bash
# Rollback database migration
cd ow-ai-backend
alembic downgrade -1

# Verify rollback
psql -h owkai-pilot-db... -c "\d mcp_actions"
```

**If Policy Integration Fails:**
```python
# Revert code changes
git revert <commit-hash>
git push pilot master
```

**If Frontend Breaks:**
```javascript
// Temporarily disable policy decision display
const showPolicyDecisions = false;
```

---

## 8. Success Criteria

### 8.1 Technical Success Metrics

- ✅ **Single Policy Engine**: Both agent and MCP actions use `EnterpriseRealTimePolicyEngine`
- ✅ **Schema Compatibility**: mcp_actions table has all policy fusion fields
- ✅ **Unified Loader**: Returns both action types with policy fields populated
- ✅ **Consistent Risk Scoring**: Both action types use 4-category comprehensive risk scoring
- ✅ **Performance**: Policy evaluation completes in <200ms for both types
- ✅ **No Duplication**: Remove separate MCP governance service (mcp_governance_service.py)

### 8.2 Business Success Metrics

- ✅ **Single Policy Management**: Create one policy, applies to both agent and MCP actions
- ✅ **Unified Approval Queue**: Authorization Center shows all pending actions
- ✅ **Consistent UX**: Same approval workflow for both action types
- ✅ **Better Visibility**: Policy decisions displayed for all actions
- ✅ **Simplified Maintenance**: One policy engine to maintain and test

### 8.3 Compliance Success Metrics

- ✅ **Audit Trail**: All policy evaluations logged (both action types)
- ✅ **Policy Versioning**: Policy changes tracked and auditable
- ✅ **Risk Consistency**: Same risk methodology across all actions
- ✅ **Regulatory Compliance**: Unified policy framework for SOX/HIPAA/GDPR

---

## 9. Timeline and Effort Estimate

### Phase 1: Critical Infrastructure Fixes (2-3 hours)
- Database migration: 1 hour
- Model changes: 30 minutes
- Testing: 1 hour
- Deployment: 30 minutes

### Phase 2: Policy Engine Integration (4-5 hours)
- Unified service implementation: 2 hours
- Loader updates: 1 hour
- Route updates: 1 hour
- Testing: 1 hour

### Phase 3: Frontend Updates (2-3 hours)
- Component updates: 1 hour
- Policy decision UI: 1 hour
- Testing: 1 hour

**Total Estimated Effort:** 8-11 hours (1-2 business days)

---

## 10. Recommendation Summary

**RECOMMENDED APPROACH:** Unified Policy Engine Architecture

**Immediate Actions (Priority: CRITICAL):**
1. ✅ Fix table name mismatch (`mcp_server_actions` → `mcp_actions`)
2. ✅ Add policy fusion columns to mcp_actions table
3. ✅ Create unified policy evaluation service
4. ✅ Update unified loader to populate policy fields
5. ✅ Replace separate MCP governance with unified service

**Benefits:**
- ✅ Single source of truth for policy evaluation
- ✅ Consistent risk scoring (4-category comprehensive)
- ✅ No duplicate policy logic
- ✅ Easier to maintain and test
- ✅ Better user experience (unified approval queue)
- ✅ Enterprise-grade architecture aligned with industry standards

**Risks:**
- ⚠️  Database migration requires testing on staging first
- ⚠️  Requires coordination between backend and frontend deployments
- ⚠️  Existing MCP actions may need backfill for new fields

**Mitigation:**
- ✅ All new columns are nullable (backward compatible)
- ✅ Comprehensive rollback plan documented
- ✅ Phased deployment (database → backend → frontend)

---

## 11. Files Summary

### Files to Modify

**Backend:**
1. `models_mcp_governance.py` - Fix table name, add policy fusion fields
2. `services/enterprise_unified_loader.py` - Add policy field transformation
3. `routes/unified_governance_routes.py` - Replace MCP evaluation with unified service
4. NEW: `services/unified_policy_evaluation_service.py` - Unified policy service
5. NEW: `alembic/versions/20251115_fix_mcp_table_name.py` - Database migration

**Frontend:**
1. `src/components/AgentAuthorizationDashboard.jsx` - Add policy decision UI

### Files to Potentially Remove (After Migration)

1. `services/mcp_governance_service.py` - Replaced by unified service
2. Cedar policy enforcement code - No longer needed

---

## 12. Next Steps

**Awaiting User Approval:**

This comprehensive audit has identified critical gaps preventing MCP actions from using the same policy engine as agent actions. The recommended solution provides a unified architecture aligned with enterprise standards.

**Please review and approve one of the following:**

**Option 1: Full Unified Policy Engine (RECOMMENDED)**
- Implement all phases as documented above
- Timeline: 1-2 business days
- Result: Complete policy engine unification

**Option 2: Minimal Fix (Quick Fix)**
- Only fix table name mismatch
- Only add policy_evaluated, policy_decision, policy_risk_score columns
- Keep separate governance services for now
- Timeline: 2-3 hours
- Result: Schema compatibility, but still duplicate policy logic

**Option 3: Custom Approach**
- User specifies which parts to implement
- Phased rollout over multiple deployments

**Please advise which approach you'd like to proceed with.**

---

**Engineer:** Donald King, OW-kai Enterprise
**Date:** November 15, 2025
**Status:** 🔍 AUDIT COMPLETE - AWAITING APPROVAL
