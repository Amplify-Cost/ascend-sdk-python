"""
Enterprise Risk Scoring Configuration API Routes
Provides admin endpoints for managing risk scoring weight configurations

Engineer: Donald King (OW-kai Enterprise)
Created: 2025-11-14
Updated: 2025-11-17 - Implemented ImmutableAuditService for SOX compliance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import RiskScoringConfig
from dependencies import require_admin, require_csrf, get_organization_filter
from schemas.risk_config import RiskConfigCreate, RiskConfigResponse, RiskConfigValidation
from services.risk_config_validator import validate_risk_config
from services.risk_config_loader import clear_config_cache
from services.immutable_audit_service import ImmutableAuditService
from typing import List
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/risk-scoring", tags=["Risk Scoring Configuration"])

@router.get("/config", response_model=RiskConfigResponse)
def get_active_config(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get currently active risk scoring configuration

    **RBAC:** Admin only
    **Returns:** Active configuration or factory default
    **SEC-082:** Multi-tenant organization filtering
    **ONBOARD-028:** Restored factory default fallback (was removed by SEC-082)

    Enterprise Pattern: New tenants get sensible defaults, not 404 errors.
    """
    try:
        active_config = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True,
            RiskScoringConfig.organization_id == org_id
        ).first()

        if not active_config:
            # ONBOARD-028: Return factory default configuration instead of 404
            # ONBOARD-030: Aligned with frontend schema and Org 1 working config format
            # Enterprise Pattern: Wiz/Datadog/Splunk provide defaults for new tenants
            logger.info(f"No active config found for org_id={org_id}, returning factory default")
            return {
                "id": 0,  # Synthetic ID indicating factory default
                "config_version": "1.0.0-default",
                "algorithm_version": "2.0.0",
                # Environment weights (0-100 scale) - matches frontend WeightSlider
                "environment_weights": {
                    "production": 35,      # Highest risk
                    "staging": 20,         # Medium risk
                    "development": 5       # Lower risk
                },
                # Action type weights (0-100 scale) - matches frontend field names
                "action_weights": {
                    "delete": 25,          # Highest risk - destructive
                    "write": 20,           # High risk - data modification
                    "read": 10,            # Lower risk - data access
                    "describe": 5,         # Low risk - metadata only
                    "list": 8              # Low risk - enumeration
                },
                # Resource type multipliers (0.8-1.2 scale) - matches frontend
                "resource_multipliers": {
                    "rds": 1.2,            # Database - high value
                    "dynamodb": 1.2,       # NoSQL database
                    "s3": 1.1,             # Storage
                    "lambda": 0.9,         # Compute - lower risk
                    "ec2": 1.0,            # Compute
                    "iam": 1.2,            # Identity - critical
                    "secretsmanager": 1.2, # Secrets - critical
                    "kms": 1.2             # Encryption keys
                },
                # PII/sensitive data weights (0-100 scale) - matches frontend
                "pii_weights": {
                    "high_sensitivity": 30,    # SSN, health records, financial
                    "medium_sensitivity": 20,  # Email, phone, address
                    "low_sensitivity": 10,     # Name, general PII
                    "none": 0                  # No PII
                },
                # Component percentages (must sum to 100%) - matches frontend
                "component_percentages": {
                    "environment": 35,         # Environment impact
                    "data_sensitivity": 33,    # PII sensitivity impact
                    "action_type": 25,         # Action risk impact
                    "operational_context": 7   # Context factors
                },
                "description": "Factory default configuration - customize as needed",
                "is_active": False,
                "is_default": True,
                "created_at": datetime.now(UTC),
                "created_by": "system",
                "activated_at": None,
                "activated_by": None
            }

        logger.info(f"Active config v{active_config.config_version} retrieved by {admin_user['email']}")
        return active_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve active config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )

@router.get("/config/history", response_model=List[RiskConfigResponse])
def get_config_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get configuration history (most recent first)

    **RBAC:** Admin only
    **Params:** limit (default 10, max 50)
    **Returns:** List of configurations ordered by creation date
    **SEC-082:** Multi-tenant organization filtering
    """
    try:
        # Validate limit
        if limit > 50:
            limit = 50

        configs = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.organization_id == org_id
        ).order_by(
            RiskScoringConfig.created_at.desc()
        ).limit(limit).all()

        logger.info(f"Config history ({len(configs)} records) retrieved by {admin_user['email']}")
        return configs

    except Exception as e:
        logger.error(f"Failed to retrieve config history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration history"
        )

@router.post("/config", response_model=RiskConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    config_data: RiskConfigCreate,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Create new risk scoring configuration (does not activate)

    **RBAC:** Admin only
    **CSRF:** Required
    **Validation:** Runs validation checks before creation
    **Returns:** Created configuration (is_active = False)
    **SEC-082:** Multi-tenant organization filtering
    """
    try:
        # Validate configuration
        config_dict = config_data.model_dump()
        validation_result = validate_risk_config(config_dict)

        if not validation_result['valid']:
            logger.warning(f"Config validation failed: {validation_result['errors']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Configuration validation failed",
                    "errors": validation_result['errors'],
                    "warnings": validation_result['warnings']
                }
            )

        # Create new config (inactive by default)
        new_config = RiskScoringConfig(
            config_version=config_data.config_version,
            algorithm_version=config_data.algorithm_version,
            environment_weights=config_data.environment_weights,
            action_weights=config_data.action_weights,
            resource_multipliers=config_data.resource_multipliers,
            pii_weights=config_data.pii_weights,
            component_percentages=config_data.component_percentages,
            description=config_data.description,
            is_active=False,
            is_default=False,
            created_by=admin_user['email'],
            organization_id=org_id  # SEC-082: Set organization ID
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        # Create immutable audit log entry (enterprise compliance)
        audit_service = ImmutableAuditService(db)
        audit_service.log_event(
            event_type="CONFIG_CHANGE",
            actor_id=admin_user['email'],
            resource_type="RISK_CONFIG",
            resource_id=str(new_config.id),
            action="CREATE",
            organization_id=org_id,  # SEC-100c: Multi-tenant audit isolation
            event_data={
                "outcome": "SUCCESS",  # SEC-100: Moved from invalid kwarg
                "config_id": new_config.id,
                "config_version": new_config.config_version,
                "algorithm_version": new_config.algorithm_version,
                "warnings": validation_result['warnings'],
                "created_by": admin_user['email']
            },
            risk_level="MEDIUM",
            compliance_tags=["SOX", "CONFIG_MANAGEMENT", "AUDIT_TRAIL"]
        )

        logger.info(
            f"Config v{new_config.config_version} (ID: {new_config.id}) "
            f"created by {admin_user['email']} with {len(validation_result['warnings'])} warnings"
        )

        return new_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create config: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create configuration"
        )

@router.put("/config/{config_id}/activate", response_model=RiskConfigResponse)
def activate_config(
    config_id: int,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Activate a risk scoring configuration (deactivates previous)

    **RBAC:** Admin only
    **CSRF:** Required
    **Side Effects:**
      - Deactivates currently active config
      - Activates specified config
      - Clears config cache
      - Creates immutable audit log entry
    **SEC-082:** Multi-tenant organization filtering
    """
    try:
        # Find config to activate
        config_to_activate = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.id == config_id,
            RiskScoringConfig.organization_id == org_id
        ).first()

        if not config_to_activate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # Deactivate currently active config
        current_active = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True,
            RiskScoringConfig.organization_id == org_id
        ).first()

        if current_active:
            current_active.is_active = False
            logger.info(f"Deactivated config v{current_active.config_version} (ID: {current_active.id})")

        # Activate new config
        config_to_activate.is_active = True
        config_to_activate.activated_at = datetime.now(UTC)
        config_to_activate.activated_by = admin_user['email']

        db.commit()
        db.refresh(config_to_activate)

        # Clear config cache (force reload on next request)
        clear_config_cache()

        # Create immutable audit log entry (enterprise compliance)
        audit_service = ImmutableAuditService(db)
        audit_service.log_event(
            event_type="CONFIG_CHANGE",
            actor_id=admin_user['email'],
            resource_type="RISK_CONFIG",
            resource_id=str(config_to_activate.id),
            action="ACTIVATE",
            organization_id=org_id,  # SEC-100c: Multi-tenant audit isolation
            event_data={
                "outcome": "SUCCESS",  # SEC-100: Moved from invalid kwarg
                "config_id": config_to_activate.id,
                "config_version": config_to_activate.config_version,
                "algorithm_version": config_to_activate.algorithm_version,
                "previous_config_id": current_active.id if current_active else None,
                "previous_config_version": current_active.config_version if current_active else None,
                "activated_by": admin_user['email'],
                "activated_at": config_to_activate.activated_at.isoformat()
            },
            risk_level="HIGH",  # Config activation is high-impact
            compliance_tags=["SOX", "CONFIG_MANAGEMENT", "CRITICAL_CHANGE", "AUDIT_TRAIL"]
        )

        logger.info(
            f"Config v{config_to_activate.config_version} (ID: {config_to_activate.id}) "
            f"activated by {admin_user['email']}"
        )

        return config_to_activate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate config: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate configuration"
        )

@router.post("/config/validate", response_model=RiskConfigValidation)
def validate_config(
    config_data: RiskConfigCreate,
    admin_user: dict = Depends(require_admin)
):
    """
    Dry-run validation of risk scoring configuration (no DB write)

    **RBAC:** Admin only
    **Returns:** Validation result with errors and warnings
    **Use Case:** Preview validation before creating config
    """
    try:
        config_dict = config_data.model_dump()
        validation_result = validate_risk_config(config_dict)

        logger.info(
            f"Config validation dry-run by {admin_user['email']}: "
            f"valid={validation_result['valid']}, "
            f"errors={len(validation_result['errors'])}, "
            f"warnings={len(validation_result['warnings'])}"
        )

        return validation_result

    except Exception as e:
        logger.error(f"Failed to validate config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate configuration"
        )

@router.post("/config/rollback-to-default", response_model=RiskConfigResponse)
def rollback_to_default(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    _=Depends(require_csrf)
):
    """
    Emergency rollback to factory default configuration

    **RBAC:** Admin only
    **CSRF:** Required
    **Side Effects:**
      - Deactivates current config
      - Activates factory default (is_default = True)
      - Clears config cache
      - Creates audit log entry
    **SEC-082:** Multi-tenant organization filtering
    """
    try:
        # Find factory default
        factory_default = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_default == True,
            RiskScoringConfig.organization_id == org_id
        ).first()

        if not factory_default:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factory default configuration not found"
            )

        # Deactivate current active config
        current_active = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True,
            RiskScoringConfig.organization_id == org_id
        ).first()

        if current_active and current_active.id != factory_default.id:
            current_active.is_active = False
            logger.info(f"Deactivated config v{current_active.config_version} (ID: {current_active.id})")

        # Activate factory default
        factory_default.is_active = True
        factory_default.activated_at = datetime.now(UTC)
        factory_default.activated_by = admin_user['email']

        db.commit()
        db.refresh(factory_default)

        # Clear config cache
        clear_config_cache()

        # Create immutable audit log entry (enterprise compliance - emergency rollback)
        audit_service = ImmutableAuditService(db)
        audit_service.log_event(
            event_type="CONFIG_CHANGE",
            actor_id=admin_user['email'],
            resource_type="RISK_CONFIG",
            resource_id=str(factory_default.id),
            action="ROLLBACK_TO_DEFAULT",
            organization_id=org_id,  # SEC-100c: Multi-tenant audit isolation
            event_data={
                "outcome": "SUCCESS",  # SEC-100: Moved from invalid kwarg
                "factory_default_id": factory_default.id,
                "factory_default_version": factory_default.config_version,
                "previous_config_id": current_active.id if current_active else None,
                "previous_config_version": current_active.config_version if current_active else None,
                "reason": "emergency_rollback",
                "activated_by": admin_user['email'],
                "activated_at": factory_default.activated_at.isoformat()
            },
            risk_level="CRITICAL",  # Emergency rollback is critical event
            compliance_tags=["SOX", "CONFIG_MANAGEMENT", "EMERGENCY_ROLLBACK", "AUDIT_TRAIL", "INCIDENT_RESPONSE"]
        )

        logger.warning(
            f"EMERGENCY ROLLBACK to factory default v{factory_default.config_version} "
            f"by {admin_user['email']}"
        )

        return factory_default

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rollback to default: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rollback to default configuration"
        )
