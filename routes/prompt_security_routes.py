"""
Phase 10: Prompt Security Admin Routes
======================================

Enterprise-grade admin endpoints for prompt injection detection and LLM-to-LLM governance.

Endpoints:
- GET /config - Get org configuration
- PUT /config - Update org configuration
- GET /patterns - List all effective patterns
- POST /patterns/override - Add pattern override
- DELETE /patterns/override/{pattern_id} - Remove pattern override
- GET /custom-patterns - List custom patterns
- POST /custom-patterns - Create custom pattern
- GET /audit-log - Query audit log
- GET /chain-log - Query LLM chain log
- GET /stats - Detection statistics

Compliance: SOC 2 CC6.1, PCI-DSS 6.5, HIPAA 164.312(e), NIST 800-53 SI-10, OWASP LLM Top 10

Author: OW-kai Enterprise Security Team
Version: 1.0.0
Created: 2025-12-18
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from dependencies import require_admin, get_organization_filter
from dependencies_api_keys import get_current_user_or_api_key, get_organization_filter_dual_auth
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, Field
import logging

from models_prompt_security import (
    GlobalPromptPattern,
    OrgPromptSecurityConfig,
    OrgPromptPatternOverride,
    OrgCustomPromptPattern,
    PromptSecurityAuditLog,
    LLMChainAuditLog,
)
from services.prompt_security_service import PromptSecurityService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin/prompt-security", tags=["Prompt Security Admin"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class ConfigUpdateRequest(BaseModel):
    """Request body for updating prompt security configuration."""
    enabled: Optional[bool] = None
    mode: Optional[str] = Field(None, pattern="^(enforce|monitor|off)$")
    severity_scores: Optional[Dict[str, int]] = None
    block_threshold: Optional[int] = Field(None, ge=0, le=100)
    escalate_threshold: Optional[int] = Field(None, ge=0, le=100)
    alert_threshold: Optional[int] = Field(None, ge=0, le=100)
    scan_system_prompts: Optional[bool] = None
    scan_user_prompts: Optional[bool] = None
    scan_agent_responses: Optional[bool] = None
    scan_llm_to_llm: Optional[bool] = None
    detect_base64: Optional[bool] = None
    detect_unicode_smuggling: Optional[bool] = None
    detect_html_entities: Optional[bool] = None
    max_decode_depth: Optional[int] = Field(None, ge=1, le=10)
    llm_chain_depth_limit: Optional[int] = Field(None, ge=1, le=20)
    require_chain_approval: Optional[bool] = None
    enabled_categories: Optional[List[str]] = None
    disabled_pattern_ids: Optional[List[str]] = None
    notify_on_block: Optional[bool] = None
    notify_on_critical: Optional[bool] = None
    notification_emails: Optional[List[str]] = None

    # ========================================================================
    # VAL-FIX-001: Multi-Signal Configuration Fields
    # ========================================================================
    # These fields reduce false positives on business terminology while
    # maintaining security for actual injection attempts.
    # ========================================================================

    multi_signal_required: Optional[bool] = Field(
        None,
        description="VAL-FIX-001: Require 2+ pattern matches for HIGH risk (>=80). "
                    "When True, single pattern matches are capped at single_pattern_max_risk."
    )
    single_pattern_max_risk: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="VAL-FIX-001: Maximum risk score when only 1 pattern matches. "
                    "Default 70 places single matches in MEDIUM tier, not HIGH."
    )
    business_context_filter: Optional[bool] = Field(
        None,
        description="VAL-FIX-001: Enable pre-filter for common business terminology. "
                    "Reduces false positives on reports, analytics, calculations."
    )
    critical_patterns_always_block: Optional[bool] = Field(
        None,
        description="VAL-FIX-001: Critical patterns (PROMPT-001, 004, etc.) always use full risk. "
                    "WARNING: Setting to False significantly reduces security."
    )


class PatternOverrideRequest(BaseModel):
    """Request body for creating/updating pattern override."""
    pattern_id: str
    is_disabled: bool = False
    severity_override: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    risk_score_override: Optional[int] = Field(None, ge=0, le=100)
    modification_reason: str = Field(..., min_length=10, max_length=500)


class CustomPatternRequest(BaseModel):
    """Request body for creating custom pattern."""
    pattern_id: str = Field(..., pattern="^CUSTOM-PROMPT-[A-Z0-9-]+$")
    category: str = Field(..., pattern="^(prompt_injection|jailbreak|role_manipulation|encoding_attack|delimiter_attack|data_exfiltration|chain_attack|custom)$")
    attack_vector: str = Field(..., pattern="^(direct|indirect|chain|encoded)$")
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    pattern_type: str = Field(default="regex", pattern="^(regex|semantic)$")
    pattern_value: str = Field(..., min_length=1, max_length=2000)
    pattern_flags: Optional[str] = None
    applies_to: List[str] = Field(default=["user_prompt"])
    description: str = Field(..., min_length=10, max_length=500)
    recommendation: Optional[str] = None
    cwe_ids: List[str] = Field(default=[])
    mitre_techniques: List[str] = Field(default=[])
    cvss_base_score: Optional[float] = Field(None, ge=0, le=10)


# ============================================================================
# CONFIGURATION ENDPOINTS
# ============================================================================


@router.get("/config")
def get_config(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get prompt security configuration for organization.

    **RBAC:** Admin only
    **Returns:** Current configuration or defaults
    """
    try:
        service = PromptSecurityService(db, org_id)
        config = service.get_config()
        config["patterns_info"] = service.get_patterns_info()
        return config
    except Exception as e:
        logger.error(f"Failed to get prompt security config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.put("/config")
def update_config(
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    http_request: Request = None
):
    """
    Update prompt security configuration for organization.

    **RBAC:** Admin only
    **Audit:** All changes logged
    """
    try:
        # Get or create config
        config = db.query(OrgPromptSecurityConfig).filter(
            OrgPromptSecurityConfig.organization_id == org_id
        ).first()

        if not config:
            config = OrgPromptSecurityConfig(organization_id=org_id)
            db.add(config)

        # Store old values for audit
        old_values = config.to_dict() if config.id else {}

        # Update fields that were provided
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(config, field):
                setattr(config, field, value)

        config.updated_at = datetime.now(UTC)
        config.updated_by = admin_user.get("user_id")

        db.commit()
        db.refresh(config)

        # Audit log
        PromptSecurityAuditLog.log_change(
            db=db,
            organization_id=org_id,
            user_id=admin_user.get("user_id"),
            user_email=admin_user.get("email"),
            action="updated",
            resource_type="org_config",
            resource_id=str(config.id),
            old_value=old_values,
            new_value=config.to_dict(),
            change_reason="Configuration updated via admin API",
            ip_address=http_request.client.host if http_request and http_request.client else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None
        )
        db.commit()

        return config.to_dict()

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update prompt security config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


# ============================================================================
# PATTERN ENDPOINTS
# ============================================================================


@router.get("/patterns")
def list_patterns(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    include_disabled: bool = False
):
    """
    List all effective patterns for organization.

    **RBAC:** Admin only
    **Returns:** Global patterns with org overrides applied + custom patterns
    """
    try:
        # Get global patterns
        global_patterns = db.query(GlobalPromptPattern).filter(
            GlobalPromptPattern.is_active == True
        ).all()

        # Get org overrides
        overrides = {
            o.pattern_id: o for o in db.query(OrgPromptPatternOverride).filter(
                OrgPromptPatternOverride.organization_id == org_id
            ).all()
        }

        # Get org config for disabled patterns
        config = db.query(OrgPromptSecurityConfig).filter(
            OrgPromptSecurityConfig.organization_id == org_id
        ).first()
        disabled_ids = set(config.disabled_pattern_ids or []) if config else set()

        patterns = []
        for gp in global_patterns:
            override = overrides.get(gp.pattern_id)

            # Skip disabled if not requested
            if not include_disabled:
                if gp.pattern_id in disabled_ids:
                    continue
                if override and override.is_disabled:
                    continue

            pattern_data = gp.to_dict()
            pattern_data["source"] = "global"

            # Apply override
            if override:
                pattern_data["override"] = {
                    "is_disabled": override.is_disabled,
                    "severity_override": override.severity_override,
                    "risk_score_override": override.risk_score_override,
                    "modification_reason": override.modification_reason,
                }
                if override.severity_override:
                    pattern_data["effective_severity"] = override.severity_override
                else:
                    pattern_data["effective_severity"] = gp.severity
            else:
                pattern_data["effective_severity"] = gp.severity

            patterns.append(pattern_data)

        # Get custom patterns
        custom_patterns = db.query(OrgCustomPromptPattern).filter(
            OrgCustomPromptPattern.organization_id == org_id,
            OrgCustomPromptPattern.is_active == True if not include_disabled else True
        ).all()

        for cp in custom_patterns:
            pattern_data = cp.to_dict()
            pattern_data["source"] = "custom"
            pattern_data["effective_severity"] = cp.severity
            patterns.append(pattern_data)

        return {
            "total": len(patterns),
            "global_count": len([p for p in patterns if p["source"] == "global"]),
            "custom_count": len([p for p in patterns if p["source"] == "custom"]),
            "patterns": patterns
        }

    except Exception as e:
        logger.error(f"Failed to list patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list patterns: {str(e)}"
        )


@router.post("/patterns/override")
def create_pattern_override(
    request: PatternOverrideRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    http_request: Request = None
):
    """
    Create or update pattern override for organization.

    **RBAC:** Admin only
    **Audit:** All overrides logged for SOC 2 compliance
    """
    try:
        # Verify pattern exists
        global_pattern = db.query(GlobalPromptPattern).filter(
            GlobalPromptPattern.pattern_id == request.pattern_id
        ).first()

        if not global_pattern:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern {request.pattern_id} not found"
            )

        # Get or create override
        override = db.query(OrgPromptPatternOverride).filter(
            OrgPromptPatternOverride.organization_id == org_id,
            OrgPromptPatternOverride.pattern_id == request.pattern_id
        ).first()

        old_values = override.to_dict() if override else None

        if override:
            # Update existing
            override.is_disabled = request.is_disabled
            override.severity_override = request.severity_override
            override.risk_score_override = request.risk_score_override
            override.modification_reason = request.modification_reason
            override.modified_by = admin_user.get("user_id")
            override.updated_at = datetime.now(UTC)
        else:
            # Create new
            override = OrgPromptPatternOverride(
                organization_id=org_id,
                pattern_id=request.pattern_id,
                is_disabled=request.is_disabled,
                severity_override=request.severity_override,
                risk_score_override=request.risk_score_override,
                modification_reason=request.modification_reason,
                modified_by=admin_user.get("user_id")
            )
            db.add(override)

        db.commit()
        db.refresh(override)

        # Audit log
        PromptSecurityAuditLog.log_change(
            db=db,
            organization_id=org_id,
            user_id=admin_user.get("user_id"),
            user_email=admin_user.get("email"),
            action="created" if old_values is None else "updated",
            resource_type="org_override",
            resource_id=request.pattern_id,
            old_value=old_values,
            new_value=override.to_dict(),
            change_reason=request.modification_reason,
            ip_address=http_request.client.host if http_request and http_request.client else None
        )
        db.commit()

        return override.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create pattern override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create override: {str(e)}"
        )


@router.delete("/patterns/override/{pattern_id}")
def delete_pattern_override(
    pattern_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    http_request: Request = None
):
    """
    Delete pattern override for organization.

    **RBAC:** Admin only
    **Effect:** Restores pattern to global defaults
    """
    try:
        override = db.query(OrgPromptPatternOverride).filter(
            OrgPromptPatternOverride.organization_id == org_id,
            OrgPromptPatternOverride.pattern_id == pattern_id
        ).first()

        if not override:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Override for pattern {pattern_id} not found"
            )

        old_values = override.to_dict()
        db.delete(override)
        db.commit()

        # Audit log
        PromptSecurityAuditLog.log_change(
            db=db,
            organization_id=org_id,
            user_id=admin_user.get("user_id"),
            user_email=admin_user.get("email"),
            action="deleted",
            resource_type="org_override",
            resource_id=pattern_id,
            old_value=old_values,
            change_reason="Override removed - pattern restored to global defaults",
            ip_address=http_request.client.host if http_request and http_request.client else None
        )
        db.commit()

        return {"message": f"Override for {pattern_id} deleted", "pattern_id": pattern_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete pattern override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete override: {str(e)}"
        )


# ============================================================================
# CUSTOM PATTERN ENDPOINTS
# ============================================================================


@router.get("/custom-patterns")
def list_custom_patterns(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    List custom patterns for organization.

    **RBAC:** Admin only
    """
    try:
        patterns = db.query(OrgCustomPromptPattern).filter(
            OrgCustomPromptPattern.organization_id == org_id
        ).all()

        return {
            "total": len(patterns),
            "patterns": [p.to_dict() for p in patterns]
        }

    except Exception as e:
        logger.error(f"Failed to list custom patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list custom patterns: {str(e)}"
        )


@router.post("/custom-patterns")
def create_custom_pattern(
    request: CustomPatternRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    http_request: Request = None
):
    """
    Create custom pattern for organization.

    **RBAC:** Admin only
    **Pattern ID Format:** Must start with CUSTOM-PROMPT-
    """
    import re

    try:
        # Verify pattern ID doesn't exist
        existing = db.query(OrgCustomPromptPattern).filter(
            OrgCustomPromptPattern.organization_id == org_id,
            OrgCustomPromptPattern.pattern_id == request.pattern_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Pattern {request.pattern_id} already exists"
            )

        # Validate regex pattern
        try:
            flags = 0
            if request.pattern_flags:
                if "IGNORECASE" in request.pattern_flags:
                    flags |= re.IGNORECASE
                if "MULTILINE" in request.pattern_flags:
                    flags |= re.MULTILINE
            re.compile(request.pattern_value, flags)
        except re.error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid regex pattern: {str(e)}"
            )

        # Create pattern
        pattern = OrgCustomPromptPattern(
            organization_id=org_id,
            pattern_id=request.pattern_id,
            category=request.category,
            attack_vector=request.attack_vector,
            severity=request.severity,
            pattern_type=request.pattern_type,
            pattern_value=request.pattern_value,
            pattern_flags=request.pattern_flags,
            applies_to=request.applies_to,
            description=request.description,
            recommendation=request.recommendation,
            cwe_ids=request.cwe_ids,
            mitre_techniques=request.mitre_techniques,
            cvss_base_score=request.cvss_base_score,
            created_by=admin_user.get("user_id")
        )
        db.add(pattern)
        db.commit()
        db.refresh(pattern)

        # Audit log
        PromptSecurityAuditLog.log_change(
            db=db,
            organization_id=org_id,
            user_id=admin_user.get("user_id"),
            user_email=admin_user.get("email"),
            action="created",
            resource_type="org_custom",
            resource_id=request.pattern_id,
            new_value=pattern.to_dict(),
            change_reason=f"Custom pattern created: {request.description}",
            ip_address=http_request.client.host if http_request and http_request.client else None
        )
        db.commit()

        return pattern.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create custom pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom pattern: {str(e)}"
        )


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================


@router.get("/audit-log")
def get_audit_log(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    limit: int = 100,
    offset: int = 0,
    action_filter: Optional[str] = None
):
    """
    Query prompt security audit log.

    **RBAC:** Admin only
    **Filters:** action (created, updated, detection, block)
    """
    try:
        query = db.query(PromptSecurityAuditLog).filter(
            PromptSecurityAuditLog.organization_id == org_id
        )

        if action_filter:
            query = query.filter(PromptSecurityAuditLog.action == action_filter)

        total = query.count()
        logs = query.order_by(desc(PromptSecurityAuditLog.created_at)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "logs": [log.to_dict() for log in logs]
        }

    except Exception as e:
        logger.error(f"Failed to get audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}"
        )


@router.get("/chain-log")
def get_chain_log(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    limit: int = 100,
    offset: int = 0,
    status_filter: Optional[str] = None
):
    """
    Query LLM-to-LLM chain audit log.

    **RBAC:** Admin only
    **Filters:** status (allowed, blocked, escalated)
    """
    try:
        query = db.query(LLMChainAuditLog).filter(
            LLMChainAuditLog.organization_id == org_id
        )

        if status_filter:
            query = query.filter(LLMChainAuditLog.status == status_filter)

        total = query.count()
        logs = query.order_by(desc(LLMChainAuditLog.created_at)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "chains": [log.to_dict() for log in logs]
        }

    except Exception as e:
        logger.error(f"Failed to get chain log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chain log: {str(e)}"
        )


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter),
    days: int = 30
):
    """
    Get prompt security detection statistics.

    **RBAC:** Admin only
    **Params:** days (default: 30)
    """
    try:
        service = PromptSecurityService(db, org_id)
        stats = service.get_detection_stats(days=days)

        # Add pattern info
        stats["patterns_info"] = service.get_patterns_info()

        return stats

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
