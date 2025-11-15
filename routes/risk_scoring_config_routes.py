"""
Enterprise Risk Scoring Configuration API Routes
Provides admin endpoints for managing risk scoring weight configurations

Engineer: Donald King (OW-kai Enterprise)
Created: 2025-11-14
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import RiskScoringConfig, AuditLog
from dependencies import require_admin, require_csrf
from schemas.risk_config import RiskConfigCreate, RiskConfigResponse, RiskConfigValidation
from services.risk_config_validator import validate_risk_config
from services.risk_config_loader import clear_config_cache
from typing import List
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/risk-scoring", tags=["Risk Scoring Configuration"])

@router.get("/config", response_model=RiskConfigResponse)
def get_active_config(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Get currently active risk scoring configuration

    **RBAC:** Admin only
    **Returns:** Active configuration or factory default
    """
    try:
        active_config = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True
        ).first()

        if not active_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active configuration found"
            )

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
    admin_user: dict = Depends(require_admin)
):
    """
    Get configuration history (most recent first)

    **RBAC:** Admin only
    **Params:** limit (default 10, max 50)
    **Returns:** List of configurations ordered by creation date
    """
    try:
        # Validate limit
        if limit > 50:
            limit = 50

        configs = db.query(RiskScoringConfig).order_by(
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
    _=Depends(require_csrf)
):
    """
    Create new risk scoring configuration (does not activate)

    **RBAC:** Admin only
    **CSRF:** Required
    **Validation:** Runs validation checks before creation
    **Returns:** Created configuration (is_active = False)
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
            created_by=admin_user['email']
        )

        db.add(new_config)
        db.commit()
        db.refresh(new_config)

        # Create audit log entry
        audit_entry = AuditLog(
            action=f"risk_config_created",
            user_id=admin_user['user_id'],
            user_email=admin_user['email'],
            details={
                "config_id": new_config.id,
                "config_version": new_config.config_version,
                "warnings": validation_result['warnings']
            },
            timestamp=datetime.now(UTC)
        )
        db.add(audit_entry)
        db.commit()

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
    """
    try:
        # Find config to activate
        config_to_activate = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.id == config_id
        ).first()

        if not config_to_activate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Configuration {config_id} not found"
            )

        # Deactivate currently active config
        current_active = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True
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

        # Create immutable audit log entry
        audit_entry = AuditLog(
            action="risk_config_activated",
            user_id=admin_user['user_id'],
            user_email=admin_user['email'],
            details={
                "config_id": config_to_activate.id,
                "config_version": config_to_activate.config_version,
                "previous_config_id": current_active.id if current_active else None,
                "previous_config_version": current_active.config_version if current_active else None
            },
            timestamp=datetime.now(UTC)
        )
        db.add(audit_entry)
        db.commit()

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
    """
    try:
        # Find factory default
        factory_default = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_default == True
        ).first()

        if not factory_default:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Factory default configuration not found"
            )

        # Deactivate current active config
        current_active = db.query(RiskScoringConfig).filter(
            RiskScoringConfig.is_active == True
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

        # Create audit log entry
        audit_entry = AuditLog(
            action="risk_config_rollback_to_default",
            user_id=admin_user['user_id'],
            user_email=admin_user['email'],
            details={
                "factory_default_id": factory_default.id,
                "factory_default_version": factory_default.config_version,
                "previous_config_id": current_active.id if current_active else None,
                "previous_config_version": current_active.config_version if current_active else None,
                "reason": "emergency_rollback"
            },
            timestamp=datetime.now(UTC)
        )
        db.add(audit_entry)
        db.commit()

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
