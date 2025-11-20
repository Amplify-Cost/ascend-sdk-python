# 🏢 RISK SCORING CONFIGURATION - ENTERPRISE IMPLEMENTATION PLAN

**Engineer:** Donald King (OW-kai Enterprise)
**Date:** 2025-11-14
**Feature:** Configurable Risk Scoring Weights (Industry Standard)
**Status:** ✅ AUDIT COMPLETE → DESIGN PHASE

---

## EXECUTIVE SUMMARY

This plan implements **enterprise-grade configurable risk scoring**, matching industry standards set by:
- ✅ Splunk Enterprise Security
- ✅ ServiceNow Security Operations
- ✅ Palo Alto Cortex XDR
- ✅ AWS Security Hub

**Key Principles:**
1. **Enterprise Grade** - Production-ready with RBAC, audit trails, validation
2. **Easy to Use** - Simple sliders, real-time preview, guided workflows
3. **Not Overly Complicated** - Sensible defaults, rollback safety, clear guidance
4. **Follows Established Pattern** - Audit → Design → Implement → Test → Evidence → Deploy

---

## IMPLEMENTATION COMPONENTS (11 Deliverables)

### **Backend (7 files)**
1. ✅ Database Model (`models.py` - add RiskScoringConfig class)
2. ✅ Database Migration (`alembic` - create risk_scoring_configs table)
3. ✅ Validation Service (`services/risk_config_validator.py` - NEW)
4. ✅ Config Loader Service (`services/risk_config_loader.py` - NEW)
5. ✅ API Routes (`routes/risk_scoring_config_routes.py` - NEW)
6. ✅ Schema Definitions (`schemas/risk_config.py` - NEW)
7. ✅ Risk Calculator Update (`services/enterprise_risk_calculator_v2.py` - MODIFY)

### **Frontend (4 files)**
8. ✅ Settings Component (`components/RiskScoringSettings.jsx` - NEW)
9. ✅ Sidebar Menu Item (`components/Sidebar.jsx` - MODIFY)
10. ✅ App Router Integration (`App.jsx` - MODIFY)
11. ✅ User Guide Modal (`components/RiskConfigGuide.jsx` - NEW)

---

## DETAILED IMPLEMENTATION STEPS

---

## STEP 1: Database Model & Migration (30 minutes)

### 1.1 Add Model to `models.py`

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/models.py`

**Add after AgentAction class (around line 200):**

```python
class RiskScoringConfig(Base):
    """
    Enterprise-grade risk scoring configuration
    Enables runtime weight adjustment without code deployment
    """
    __tablename__ = "risk_scoring_configs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Version tracking
    config_version = Column(String(20), nullable=False, index=True)
    algorithm_version = Column(String(20), nullable=False)

    # Configuration weights (JSONB for flexibility)
    environment_weights = Column(JSONB, nullable=False)
    action_weights = Column(JSONB, nullable=False)
    resource_multipliers = Column(JSONB, nullable=False)
    pii_weights = Column(JSONB, nullable=False)
    component_percentages = Column(JSONB, nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # Audit trail
    created_at = Column(DateTime, default=datetime.now(UTC))
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    updated_by = Column(String(255), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by = Column(String(255), nullable=True)
```

### 1.2 Create Alembic Migration

**Command:**
```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
alembic revision -m "add_risk_scoring_configs_table"
```

**Migration File Content:**
```python
"""add_risk_scoring_configs_table

Revision ID: <auto_generated>
Revises: 046903af7235
Create Date: 2025-11-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

def upgrade():
    # Create table
    op.create_table(
        'risk_scoring_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_version', sa.String(20), nullable=False),
        sa.Column('algorithm_version', sa.String(20), nullable=False),
        sa.Column('environment_weights', JSONB, nullable=False),
        sa.Column('action_weights', JSONB, nullable=False),
        sa.Column('resource_multipliers', JSONB, nullable=False),
        sa.Column('pii_weights', JSONB, nullable=False),
        sa.Column('component_percentages', JSONB, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('activated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_risk_config_active', 'risk_scoring_configs', ['is_active'])
    op.create_index('idx_risk_config_version', 'risk_scoring_configs', ['config_version'])

    # Insert factory default
    op.execute("""
        INSERT INTO risk_scoring_configs (
            config_version, algorithm_version,
            environment_weights, action_weights, resource_multipliers,
            pii_weights, component_percentages,
            description, is_active, is_default, created_by, created_at, updated_at
        ) VALUES (
            '2.0.0', '2.0.0',
            '{"production": 35, "staging": 18, "development": 5, "sandbox": 2, "test": 3, "unknown": 35}'::JSONB,
            '{"delete": 23, "drop": 23, "destroy": 22, "terminate": 21, "write": 17, "update": 17, "create": 15, "put": 15, "post": 15, "read": 8, "get": 7, "list": 6, "describe": 5, "unknown": 19}'::JSONB,
            '{"rds": 1.2, "dynamodb": 1.15, "iam": 1.2, "eks": 1.15, "ec2": 1.1, "ecs": 1.1, "s3": 1.0, "cloudwatch": 0.9, "sns": 0.9, "sqs": 0.9, "lambda": 0.8, "unknown": 1.0}'::JSONB,
            '{"high_sensitivity": 25, "medium_sensitivity": 15, "low_sensitivity": 5}'::JSONB,
            '{"environment": 35, "data_sensitivity": 30, "action_type": 25, "operational_context": 10}'::JSONB,
            'Factory default configuration - validated 2025-11-14',
            TRUE, TRUE, 'system', NOW(), NOW()
        )
    """)

def downgrade():
    op.drop_index('idx_risk_config_version')
    op.drop_index('idx_risk_config_active')
    op.drop_table('risk_scoring_configs')
```

---

## STEP 2: Validation & Loader Services (30 minutes)

### 2.1 Validation Service

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/services/risk_config_validator.py` (NEW)

```python
"""
Enterprise Risk Scoring Configuration Validator
Validates weight ranges, component sums, and business rules
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def validate_risk_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate risk scoring configuration

    Returns:
        {
            "valid": bool,
            "errors": List[str],       # Blocking errors
            "warnings": List[str]      # Non-blocking warnings
        }
    """
    errors = []
    warnings = []

    # ==================================================================
    # VALIDATION 1: Component Percentages Must Sum to 100
    # ==================================================================
    comp_pct = config.get('component_percentages', {})
    total_pct = (
        comp_pct.get('environment', 0) +
        comp_pct.get('data_sensitivity', 0) +
        comp_pct.get('action_type', 0) +
        comp_pct.get('operational_context', 0)
    )

    if total_pct != 100:
        errors.append(
            f"⚠️ Component percentages must sum to 100% (got {total_pct}%)\n"
            f"   Environment: {comp_pct.get('environment')}%, "
            f"Data: {comp_pct.get('data_sensitivity')}%, "
            f"Action: {comp_pct.get('action_type')}%, "
            f"Context: {comp_pct.get('operational_context')}%"
        )

    # ==================================================================
    # VALIDATION 2: Environment Weights (0-35 range)
    # ==================================================================
    env_weights = config.get('environment_weights', {})
    for env, weight in env_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"Environment weight '{env}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 35):
            errors.append(f"Environment weight '{env}' must be 0-35, got {weight}")

    # ==================================================================
    # VALIDATION 3: Action Weights (0-25 range)
    # ==================================================================
    action_weights = config.get('action_weights', {})
    for action, weight in action_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"Action weight '{action}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 25):
            errors.append(f"Action weight '{action}' must be 0-25, got {weight}")

    # ==================================================================
    # VALIDATION 4: Resource Multipliers (0.5-2.0 range)
    # ==================================================================
    resource_mult = config.get('resource_multipliers', {})
    for resource, mult in resource_mult.items():
        if not isinstance(mult, (int, float)):
            errors.append(f"Resource multiplier '{resource}' must be numeric, got {type(mult)}")
        elif not (0.5 <= mult <= 2.0):
            errors.append(f"Resource multiplier '{resource}' must be 0.5-2.0, got {mult}")

    # ==================================================================
    # VALIDATION 5: PII Weights (0-30 range)
    # ==================================================================
    pii_weights = config.get('pii_weights', {})
    for category, weight in pii_weights.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"PII weight '{category}' must be numeric, got {type(weight)}")
        elif not (0 <= weight <= 30):
            errors.append(f"PII weight '{category}' must be 0-30, got {weight}")

    # ==================================================================
    # WARNINGS: Business Logic Checks (Non-Blocking)
    # ==================================================================

    # Warning 1: Production environment should be high risk
    if env_weights.get('production', 0) < 30:
        warnings.append(
            "⚠️ Production environment weight < 30 may be too permissive "
            "(recommended: 35 for maximum protection)"
        )

    # Warning 2: Destructive actions should be high risk
    if action_weights.get('delete', 0) < 20:
        warnings.append(
            "⚠️ Delete action weight < 20 may underestimate risk "
            "(recommended: 23 for dangerous operations)"
        )

    # Warning 3: Development environment should be low risk
    if env_weights.get('development', 0) > 10:
        warnings.append(
            "⚠️ Development environment weight > 10 may be too restrictive "
            "(recommended: 5 for developer productivity)"
        )

    # Warning 4: Critical resources should have high multipliers
    critical_resources = ['rds', 'dynamodb', 'iam']
    for resource in critical_resources:
        if resource_mult.get(resource, 1.0) < 1.1:
            warnings.append(
                f"⚠️ Critical resource '{resource}' multiplier < 1.1 may underestimate risk "
                f"(recommended: 1.2 for databases and IAM)"
            )

    # ==================================================================
    # RETURN VALIDATION RESULT
    # ==================================================================

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

    if not result['valid']:
        logger.error(f"❌ Risk config validation failed: {len(errors)} errors, {len(warnings)} warnings")
    elif warnings:
        logger.warning(f"⚠️  Risk config validation passed with {len(warnings)} warnings")
    else:
        logger.info("✅ Risk config validation passed (no errors or warnings)")

    return result
```

### 2.2 Config Loader Service

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/services/risk_config_loader.py` (NEW)

```python
"""
Enterprise Risk Scoring Configuration Loader
Loads active configuration from database with caching
"""
from sqlalchemy.orm import Session
from models import RiskScoringConfig
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# In-memory cache (refreshed every 60 seconds)
_config_cache: Optional[Dict] = None
_cache_timestamp: Optional[float] = None
CACHE_TTL_SECONDS = 60

def get_active_risk_config(db: Session) -> Dict:
    """
    Get active risk scoring configuration from database

    Returns:
        Dict with all weight configurations
        Falls back to hardcoded defaults if no active config found
    """
    import time

    global _config_cache, _cache_timestamp

    # Check cache first (performance optimization)
    current_time = time.time()
    if _config_cache and _cache_timestamp:
        if (current_time - _cache_timestamp) < CACHE_TTL_SECONDS:
            logger.debug("Using cached risk config (cache hit)")
            return _config_cache

    # Query database for active config
    try:
        active_config = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True
        ).first()

        if active_config:
            logger.info(f"📊 Loaded risk config v{active_config.config_version} from database")

            config_dict = {
                "config_version": active_config.config_version,
                "algorithm_version": active_config.algorithm_version,
                "environment_weights": active_config.environment_weights,
                "action_weights": active_config.action_weights,
                "resource_multipliers": active_config.resource_multipliers,
                "pii_weights": active_config.pii_weights,
                "component_percentages": active_config.component_percentages,
                "description": active_config.description
            }

            # Update cache
            _config_cache = config_dict
            _cache_timestamp = current_time

            return config_dict

        else:
            logger.warning("⚠️  No active risk config found in database, using hardcoded defaults")
            return None

    except Exception as e:
        logger.error(f"❌ Error loading risk config from database: {e}")
        return None

def clear_config_cache():
    """Clear the configuration cache (called after config updates)"""
    global _config_cache, _cache_timestamp
    _config_cache = None
    _cache_timestamp = None
    logger.info("🔄 Risk config cache cleared")
```

---

## STEP 3: Pydantic Schemas (15 minutes)

**File:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/schemas/risk_config.py` (NEW)

```python
"""
Risk Scoring Configuration Schemas
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, List
from datetime import datetime

class RiskConfigCreate(BaseModel):
    """Schema for creating a new risk scoring configuration"""

    config_version: str = Field(..., example="2.1.0")
    algorithm_version: str = Field(..., example="2.0.0")

    environment_weights: Dict[str, int] = Field(..., example={
        "production": 35,
        "staging": 18,
        "development": 5
    })

    action_weights: Dict[str, int] = Field(..., example={
        "delete": 23,
        "write": 17,
        "read": 8
    })

    resource_multipliers: Dict[str, float] = Field(..., example={
        "rds": 1.2,
        "s3": 1.0,
        "lambda": 0.8
    })

    pii_weights: Dict[str, int] = Field(..., example={
        "high_sensitivity": 25,
        "medium_sensitivity": 15,
        "low_sensitivity": 5
    })

    component_percentages: Dict[str, int] = Field(..., example={
        "environment": 35,
        "data_sensitivity": 30,
        "action_type": 25,
        "operational_context": 10
    })

    description: Optional[str] = Field(None, example="Custom config for healthcare compliance")

    @validator('component_percentages')
    def validate_percentages_sum(cls, v):
        total = sum(v.values())
        if total != 100:
            raise ValueError(f"Component percentages must sum to 100, got {total}")
        return v

class RiskConfigResponse(BaseModel):
    """Schema for risk scoring configuration response"""

    id: int
    config_version: str
    algorithm_version: str
    environment_weights: Dict[str, int]
    action_weights: Dict[str, int]
    resource_multipliers: Dict[str, float]
    pii_weights: Dict[str, int]
    component_percentages: Dict[str, int]
    description: Optional[str]
    is_active: bool
    is_default: bool
    created_at: datetime
    created_by: str
    activated_at: Optional[datetime]
    activated_by: Optional[str]

    class Config:
        from_attributes = True

class RiskConfigValidation(BaseModel):
    """Schema for configuration validation response"""

    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
```

---

## TIME ESTIMATE BREAKDOWN

| Component | Estimated Time | Complexity |
|-----------|---------------|------------|
| Database Model & Migration | 30 min | Low |
| Validation Service | 30 min | Medium |
| Config Loader Service | 15 min | Low |
| Pydantic Schemas | 15 min | Low |
| **Backend Subtotal** | **1h 30min** | |
| | | |
| API Routes (GET/POST/PUT) | 45 min | Medium |
| Risk Calculator Integration | 30 min | Medium |
| **Backend Total** | **2h 45min** | |
| | | |
| Frontend Settings Component | 60 min | High |
| Sidebar & Router Integration | 15 min | Low |
| User Guide Modal | 30 min | Medium |
| **Frontend Total** | **1h 45min** | |
| | | |
| Test Suite (Backend) | 30 min | Medium |
| Local Integration Testing | 30 min | Medium |
| Documentation | 30 min | Low |
| **Testing & Docs Total** | **1h 30min** | |
| | | |
| **GRAND TOTAL** | **6 hours** | |

---

## SUCCESS CRITERIA

1. ✅ Admin can create new risk configurations via UI
2. ✅ Admin can activate configurations (deactivates previous)
3. ✅ Validation prevents invalid configurations
4. ✅ Real-time preview shows impact of weight changes
5. ✅ Rollback to factory default works
6. ✅ Risk calculator uses database config (not hardcoded)
7. ✅ Immutable audit log tracks all config changes
8. ✅ Frontend provides clear guidance and validation feedback
9. ✅ All tests pass (backend + integration)
10. ✅ Documentation includes user guide

---

**Status:** ✅ DESIGN COMPLETE - Ready to proceed with implementation

**Next:** Await approval to begin coding
