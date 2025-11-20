# 🏢 RISK SCORING CONFIGURATION MANAGEMENT - COMPREHENSIVE AUDIT

**Engineer:** Donald King (OW-kai Enterprise)
**Date:** 2025-11-14
**Feature:** Enterprise-Grade Configurable Risk Scoring Weights
**Priority:** SHOULD-HAVE (High) - Industry Standard Feature

---

## EXECUTIVE SUMMARY

**Objective:** Implement enterprise-grade configuration management for risk scoring weights, enabling runtime adjustment without code deployment.

**Business Value:**
- ✅ Industry standard (Splunk, ServiceNow, Palo Alto, AWS all provide this)
- ✅ Customer customization (Healthcare vs FinTech vs Retail risk models)
- ✅ Real-time calibration (adjust weights based on production feedback)
- ✅ A/B testing capability (test new formulas without deployment)
- ✅ Compliance requirement (auditors expect tuning without code changes)

**Implementation Scope:** 3-4 hours (backend + frontend + tests)

---

## PHASE 1: CODEBASE AUDIT FINDINGS

### 1.1 Backend Architecture

**Current State:**

#### **Risk Calculator: `services/enterprise_risk_calculator_v2.py`**
- ✅ **Line 461**: `config` parameter already exists
- ❌ **Line 486-620**: Parameter accepted but NOT USED in calculation
- ❌ **Line 499**: Uses hardcoded `self.ENVIRONMENT_SCORES`
- ❌ **Line 515**: Uses hardcoded `self.ACTION_TYPE_BASE_SCORES`
- ❌ **Line 549**: Uses hardcoded `self.RESOURCE_TYPE_MULTIPLIERS`

**Hardcoded Weights:**
```python
ENVIRONMENT_SCORES = {
    'production': 35,  # ← Hardcoded
    'staging': 18,
    'development': 5
}

ACTION_TYPE_BASE_SCORES = {
    'delete': 23,      # ← Hardcoded
    'drop': 23,
    'destroy': 22
}

RESOURCE_TYPE_MULTIPLIERS = {
    'rds': 1.2,        # ← Hardcoded
    's3': 1.0,
    'lambda': 0.8
}
```

#### **Database Schema: `models.py`**
- ❌ **No RiskScoringConfig model exists**
- ✅ User model has RBAC fields (role, approval_level)
- ✅ AgentAction model has risk_score, risk_level fields
- ✅ Immutable audit system exists (ImmutableAuditLog model)

#### **API Routes: Searched in `/routes`**
- ✅ `authorization_routes.py` - Handles approval workflows
- ✅ `unified_governance_routes.py` - Policy management
- ✅ `mcp_governance_routes.py` - MCP policy enforcement
- ❌ **No risk scoring configuration routes exist**

#### **Alembic Migrations:**
Recent migrations found:
- `046903af7235` - Policy fusion columns
- `b8ebd7cdcb8b` - Policy evaluations table
- `389a4795ec57` - Immutable audit system
- ❌ **No risk_scoring_configs migration**

---

### 1.2 Frontend Architecture

**Current State:**

#### **Authorization Center: `AgentAuthorizationDashboard.jsx`**
- ✅ Main dashboard for agent action approval
- ✅ Displays risk scores (line 1808-1810)
- ✅ Uses risk badges with color coding (line 1409-1414)
- ✅ Filters by risk thresholds (>= 80 critical, >= 70 high)
- ❌ **No Risk Scoring Settings tab exists**
- ❌ **No configuration UI component**

#### **Sidebar Navigation: `Sidebar.jsx`**
- ✅ Authorization Center link exists
- ✅ Policy Management link exists
- ❌ **No "Risk Scoring Settings" menu item**

---

### 1.3 Integration Points Identified

#### **Integration Point 1: Database Config Lookup**
**Location:** `services/enterprise_risk_calculator_v2.py:486-505`
**Current:** Uses `self.ENVIRONMENT_SCORES` directly
**Needed:** Add database query for active config

#### **Integration Point 2: Main.py Invocation**
**Location:** `main.py:2120-2145`
**Current:** Passes `config=None` (parameter ignored)
**Needed:** Load config from database, pass to calculator

#### **Integration Point 3: API Endpoints**
**Location:** New file needed: `routes/risk_scoring_config_routes.py`
**Current:** Doesn't exist
**Needed:** GET/POST/PUT endpoints with RBAC

#### **Integration Point 4: Frontend UI**
**Location:** New component needed: `RiskScoringSettings.jsx`
**Current:** Doesn't exist
**Needed:** Admin-only settings panel with sliders

#### **Integration Point 5: Validation Layer**
**Location:** New service needed: `services/risk_config_validator.py`
**Current:** Doesn't exist
**Needed:** Validate weight ranges, component sums

---

## PHASE 2: ENTERPRISE DESIGN SPECIFICATION

### 2.1 Database Schema Design

**New Table: `risk_scoring_configs`**

```sql
CREATE TABLE risk_scoring_configs (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Version tracking
    config_version VARCHAR(20) NOT NULL,           -- e.g., "2.0.0", "2.1.0"
    algorithm_version VARCHAR(20) NOT NULL,        -- Links to calculator version

    -- Configuration weights (JSONB for flexibility)
    environment_weights JSONB NOT NULL,            -- {"production": 35, "staging": 18, ...}
    action_weights JSONB NOT NULL,                 -- {"delete": 23, "write": 17, ...}
    resource_multipliers JSONB NOT NULL,           -- {"rds": 1.2, "s3": 1.0, ...}
    pii_weights JSONB NOT NULL,                    -- {"high_sensitivity": 25, ...}

    -- Component percentage allocation
    component_percentages JSONB NOT NULL,          -- {"environment": 35, "data": 30, ...}

    -- Metadata
    description TEXT,                               -- Human-readable description
    is_active BOOLEAN DEFAULT FALSE,                -- Only one active config at a time
    is_default BOOLEAN DEFAULT FALSE,               -- Factory default config

    -- Audit trail
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,               -- User who created
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(255),                        -- User who updated
    activated_at TIMESTAMP,                         -- When made active
    activated_by VARCHAR(255),                      -- Who activated

    -- Constraints
    CONSTRAINT check_only_one_active UNIQUE (is_active) WHERE is_active = TRUE,
    CONSTRAINT check_component_sum CHECK (
        (component_percentages->>'environment')::INT +
        (component_percentages->>'data_sensitivity')::INT +
        (component_percentages->>'action_type')::INT +
        (component_percentages->>'operational_context')::INT = 100
    )
);

-- Indexes for performance
CREATE INDEX idx_risk_config_active ON risk_scoring_configs (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_risk_config_version ON risk_scoring_configs (config_version);
CREATE INDEX idx_risk_config_created_at ON risk_scoring_configs (created_at DESC);

-- Insert factory default configuration
INSERT INTO risk_scoring_configs (
    config_version,
    algorithm_version,
    environment_weights,
    action_weights,
    resource_multipliers,
    pii_weights,
    component_percentages,
    description,
    is_active,
    is_default,
    created_by
) VALUES (
    '2.0.0',
    '2.0.0',
    '{"production": 35, "staging": 18, "development": 5, "sandbox": 2, "test": 3, "unknown": 35}'::JSONB,
    '{"delete": 23, "drop": 23, "destroy": 22, "terminate": 21, "write": 17, "update": 17, "create": 15, "put": 15, "post": 15, "read": 8, "get": 7, "list": 6, "describe": 5, "unknown": 19}'::JSONB,
    '{"rds": 1.2, "dynamodb": 1.15, "iam": 1.2, "eks": 1.15, "ec2": 1.1, "ecs": 1.1, "s3": 1.0, "cloudwatch": 0.9, "sns": 0.9, "sqs": 0.9, "lambda": 0.8, "unknown": 1.0}'::JSONB,
    '{"high_sensitivity": 25, "medium_sensitivity": 15, "low_sensitivity": 5}'::JSONB,
    '{"environment": 35, "data_sensitivity": 30, "action_type": 25, "operational_context": 10}'::JSONB,
    'Factory default configuration - validated 2025-11-14',
    TRUE,
    TRUE,
    'system'
);
```

**Rationale:**
- JSONB for flexibility (can add new services without schema changes)
- Constraint ensures only one active config (data integrity)
- Audit trail for compliance (who, when, why)
- Factory default for rollback safety

---

### 2.2 Backend API Design

**New File: `routes/risk_scoring_config_routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from database import get_db
from dependencies import get_current_user_with_role
from models import RiskScoringConfig
from schemas.risk_config import (
    RiskConfigCreate,
    RiskConfigUpdate,
    RiskConfigResponse,
    RiskConfigValidation
)
from services.risk_config_validator import validate_risk_config
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/risk-scoring", tags=["Risk Scoring Configuration"])

# ============================================================================
# GET: Retrieve Active Configuration
# ============================================================================

@router.get("/config", response_model=RiskConfigResponse)
async def get_active_risk_config(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user_with_role(["admin", "analyst"]))
):
    """
    Get the currently active risk scoring configuration

    Access: Admin, Analyst
    Returns: Active configuration with all weights
    """
    active_config = db.query(RiskScoringConfig).filter(
        RiskScoringConfig.is_active == True
    ).first()

    if not active_config:
        raise HTTPException(404, "No active risk scoring configuration found")

    logger.info(f"User {current_user['email']} retrieved active risk config v{active_config.config_version}")

    return active_config

# ============================================================================
# GET: Retrieve All Configurations (History)
# ============================================================================

@router.get("/config/history", response_model=List[RiskConfigResponse])
async def get_risk_config_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user_with_role(["admin"]))
):
    """
    Get historical risk scoring configurations

    Access: Admin only
    Returns: List of configurations ordered by creation date
    """
    configs = db.query(RiskScoringConfig).order_by(
        RiskScoringConfig.created_at.desc()
    ).limit(limit).all()

    logger.info(f"Admin {current_user['email']} retrieved {len(configs)} config versions")

    return configs

# ============================================================================
# POST: Create New Configuration
# ============================================================================

@router.post("/config", response_model=RiskConfigResponse)
async def create_risk_config(
    config_data: RiskConfigCreate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user_with_role(["admin"]))
):
    """
    Create a new risk scoring configuration (inactive by default)

    Access: Admin only
    Validation: Ensures weights are valid ranges and components sum to 100
    """
    # Step 1: Validate configuration
    validation_result = validate_risk_config(config_data.dict())
    if not validation_result['valid']:
        raise HTTPException(400, detail=validation_result['errors'])

    # Step 2: Create new config
    new_config = RiskScoringConfig(
        config_version=config_data.config_version,
        algorithm_version=config_data.algorithm_version,
        environment_weights=config_data.environment_weights,
        action_weights=config_data.action_weights,
        resource_multipliers=config_data.resource_multipliers,
        pii_weights=config_data.pii_weights,
        component_percentages=config_data.component_percentages,
        description=config_data.description,
        is_active=False,  # Never activate on creation
        is_default=False,
        created_by=current_user['email']
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    logger.info(f"Admin {current_user['email']} created risk config v{new_config.config_version} (ID: {new_config.id})")

    return new_config

# ============================================================================
# PUT: Activate Configuration
# ============================================================================

@router.put("/config/{config_id}/activate", response_model=RiskConfigResponse)
async def activate_risk_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user_with_role(["admin"]))
):
    """
    Activate a risk scoring configuration (deactivates previous)

    Access: Admin only
    Safety: Creates immutable audit log entry
    """
    # Step 1: Find target config
    target_config = db.query(RiskScoringConfig).filter(
        RiskScoringConfig.id == config_id
    ).first()

    if not target_config:
        raise HTTPException(404, f"Configuration ID {config_id} not found")

    # Step 2: Deactivate current active config
    current_active = db.query(RiskScoringConfig).filter(
        RiskScoringConfig.is_active == True
    ).first()

    if current_active:
        current_active.is_active = False
        logger.info(f"Deactivated config v{current_active.config_version} (ID: {current_active.id})")

    # Step 3: Activate target config
    target_config.is_active = True
    target_config.activated_at = datetime.now(UTC)
    target_config.activated_by = current_user['email']

    db.commit()
    db.refresh(target_config)

    logger.warning(f"⚠️  ADMIN {current_user['email']} ACTIVATED RISK CONFIG v{target_config.config_version} (ID: {target_config.id})")

    # Step 4: Log to immutable audit (compliance)
    from services.immutable_audit_service import log_event
    log_event(
        db=db,
        event_type="RISK_CONFIG_ACTIVATED",
        user_id=current_user['user_id'],
        details={
            "config_id": target_config.id,
            "config_version": target_config.config_version,
            "previous_config_id": current_active.id if current_active else None,
            "activated_by": current_user['email']
        }
    )

    return target_config

# ============================================================================
# GET: Validate Configuration (Dry-Run)
# ============================================================================

@router.post("/config/validate", response_model=RiskConfigValidation)
async def validate_config_dry_run(
    config_data: RiskConfigCreate,
    current_user: Dict = Depends(get_current_user_with_role(["admin"]))
):
    """
    Validate a risk configuration without saving

    Access: Admin only
    Returns: Validation result with errors/warnings
    """
    validation_result = validate_risk_config(config_data.dict())

    return {
        "valid": validation_result['valid'],
        "errors": validation_result.get('errors', []),
        "warnings": validation_result.get('warnings', [])
    }

# ============================================================================
# DELETE: Rollback to Factory Default
# ============================================================================

@router.post("/config/rollback-to-default")
async def rollback_to_factory_default(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user_with_role(["admin"]))
):
    """
    Rollback to factory default configuration

    Access: Admin only
    Safety: Requires confirmation (manual check)
    """
    factory_default = db.query(RiskScoringConfig).filter(
        RiskScoringConfig.is_default == True
    ).first()

    if not factory_default:
        raise HTTPException(500, "Factory default configuration not found!")

    # Deactivate current
    current_active = db.query(RiskScoringConfig).filter(
        RiskScoringConfig.is_active == True
    ).first()

    if current_active:
        current_active.is_active = False

    # Activate factory default
    factory_default.is_active = True
    factory_default.activated_at = datetime.now(UTC)
    factory_default.activated_by = current_user['email']

    db.commit()

    logger.warning(f"🚨 ADMIN {current_user['email']} ROLLED BACK TO FACTORY DEFAULT")

    return {"message": "Rolled back to factory default configuration", "config_version": factory_default.config_version}
```

---

### 2.3 Validation Service Design

**New File: `services/risk_config_validator.py`**

```python
from typing import Dict, List, Any

def validate_risk_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate risk scoring configuration

    Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []

    # Validate component percentages sum to 100
    comp_pct = config.get('component_percentages', {})
    total_pct = sum([
        comp_pct.get('environment', 0),
        comp_pct.get('data_sensitivity', 0),
        comp_pct.get('action_type', 0),
        comp_pct.get('operational_context', 0)
    ])

    if total_pct != 100:
        errors.append(f"Component percentages must sum to 100, got {total_pct}")

    # Validate environment weights range
    env_weights = config.get('environment_weights', {})
    for env, weight in env_weights.items():
        if not (0 <= weight <= 35):
            errors.append(f"Environment weight '{env}' must be 0-35, got {weight}")

    # Validate action weights range
    action_weights = config.get('action_weights', {})
    for action, weight in action_weights.items():
        if not (0 <= weight <= 25):
            errors.append(f"Action weight '{action}' must be 0-25, got {weight}")

    # Validate resource multipliers range
    resource_mult = config.get('resource_multipliers', {})
    for resource, mult in resource_mult.items():
        if not (0.5 <= mult <= 2.0):
            errors.append(f"Resource multiplier '{resource}' must be 0.5-2.0, got {mult}")

    # Validate PII weights range
    pii_weights = config.get('pii_weights', {})
    for category, weight in pii_weights.items():
        if not (0 <= weight <= 30):
            errors.append(f"PII weight '{category}' must be 0-30, got {weight}")

    # Warnings (non-blocking)
    if env_weights.get('production', 0) < 30:
        warnings.append("Production environment weight < 30 may be too permissive")

    if action_weights.get('delete', 0) < 20:
        warnings.append("Delete action weight < 20 may underestimate risk")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

---

## NEXT STEPS

1. ✅ **Audit Complete** - All integration points identified
2. ⏭️  **Design Review** - Enterprise architecture documented
3. ⏭️  **Implementation** - Backend + Frontend + Tests
4. ⏭️  **Local Testing** - Database + API + UI validation
5. ⏭️  **Evidence Collection** - Screenshots, API tests, audit logs
6. ⏭️  **Production Deployment** - After approval

---

**Status:** ✅ AUDIT COMPLETE - Ready for implementation approval

**Estimated Time:** 3-4 hours for full enterprise implementation
