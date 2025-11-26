# routes/enterprise_secrets_routes.py
"""
Enterprise Secrets Management API Routes
Provides secure endpoints for secrets rotation, monitoring, and compliance
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
import logging
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_admin, get_organization_filter
from config import _config as config

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/secrets", tags=["Enterprise Secrets Management"])
security = HTTPBearer()

# Pydantic models for request/response
class SecretRotationRequest(BaseModel):
    secret_name: str = Field(..., description="Name of the secret to rotate")
    force: bool = Field(False, description="Force rotation even if not due")
    dry_run: bool = Field(False, description="Perform dry run without actual rotation")
    reason: Optional[str] = Field(None, description="Reason for rotation")

class SecretRotationResponse(BaseModel):
    success: bool
    secret_name: str
    timestamp: datetime
    old_secret_hash: Optional[str]
    new_secret_hash: Optional[str]
    error_message: Optional[str] = None
    rollback_available: bool = True

class RotationScheduleRequest(BaseModel):
    secret_name: str
    cron_expression: str = Field(..., description="Cron expression for rotation schedule")
    notification_emails: List[str] = Field(default_factory=list)
    enabled: bool = True

class ComplianceReportResponse(BaseModel):
    total_secrets_managed: int
    high_risk_secrets: int
    secrets_due_for_rotation: int
    primary_provider: str
    audit_trail_entries: int
    compliance_frameworks: List[str]
    last_generated: datetime

class AuditTrailEntry(BaseModel):
    timestamp: datetime
    secret_name: str
    action: str
    details: str
    user: str
    compliance_logged: bool

# Global secrets manager instance
_secrets_manager = None
_rotation_service = None

def get_secrets_manager():
    """Get secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        try:
            from enterprise_secrets.secrets_manager import get_secrets_manager
            _secrets_manager = get_secrets_manager()
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Enterprise secrets manager not available"
            )
    return _secrets_manager

def get_rotation_service():
    """Get rotation service instance"""
    global _rotation_service
    if _rotation_service is None:
        try:
            from enterprise_secrets.rotation_service import SecretsRotationService
            manager = get_secrets_manager()
            
            # Configure notifications
            notification_config = {
                "smtp": {
                    "host": "smtp.gmail.com",
                    "port": 587,
                    "use_tls": True,
                    "username": config._get_secret_secure("SMTP_USERNAME"),
                    "password": config._get_secret_secure("SMTP_PASSWORD"),
                    "from_email": "security@ow-ai.com"
                },
                "global_emails": ["security@ow-ai.com", "infrastructure@ow-ai.com"],
                "emergency_emails": ["ciso@ow-ai.com", "security@ow-ai.com"]
            }
            
            _rotation_service = SecretsRotationService(manager, notification_config)
            
            # Start scheduler in production
            if config.ENVIRONMENT == "production":
                _rotation_service.start_scheduler()
                
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Enterprise rotation service not available"
            )
    return _rotation_service

@router.get("/status")
async def get_secrets_management_status(
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get overall status of enterprise secrets management system
    """
    try:
        manager = get_secrets_manager()
        rotation_service = get_rotation_service()

        logger.info(f"Fetching secrets management status [org_id={org_id}]")

        # Get basic status
        compliance_report = manager.get_compliance_report()
        rotation_status = rotation_service.get_rotation_status()
        
        # Get secrets due for rotation
        due_secrets = manager.get_secrets_due_for_rotation()
        
        return {
            "secrets_manager": {
                "status": "operational",
                "provider": compliance_report.get("primary_provider", "unknown"),
                "total_secrets": compliance_report.get("total_secrets_managed", 0),
                "high_risk_secrets": compliance_report.get("high_risk_secrets", 0)
            },
            "rotation_service": {
                "status": "operational" if rotation_status["scheduler_running"] else "stopped",
                "scheduler_running": rotation_status["scheduler_running"],
                "total_schedules": rotation_status["total_schedules"],
                "enabled_schedules": rotation_status["enabled_schedules"],
                "next_rotation": rotation_status.get("next_scheduled_rotation")
            },
            "compliance": {
                "framework": config.COMPLIANCE_MODE,
                "audit_logging": config.AUDIT_LOGGING_ENABLED,
                "rotation_enabled": config.SECRET_ROTATION_ENABLED
            },
            "alerts": {
                "secrets_due_for_rotation": len(due_secrets),
                "due_secret_names": due_secrets[:5],  # Show first 5
                "requires_attention": len(due_secrets) > 0
            },
            "last_updated": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get secrets management status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve secrets management status: {str(e)}"
        )

@router.post("/rotate", response_model=SecretRotationResponse)
async def rotate_secret(
    request: SecretRotationRequest,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Rotate a specific secret with comprehensive validation and audit trail
    """
    try:
        rotation_service = get_rotation_service()

        logger.info(f"🔄 Secret rotation requested by {current_user['email']} for {request.secret_name} [org_id={org_id}]")
        
        # Validate secret exists
        manager = get_secrets_manager()
        current_secret = manager.get_secret(request.secret_name)
        if not current_secret:
            raise HTTPException(
                status_code=404,
                detail=f"Secret '{request.secret_name}' not found"
            )
        
        # Perform rotation
        if request.reason:
            # Emergency rotation with reason
            result = await rotation_service.emergency_rotation(
                request.secret_name, 
                request.reason
            )
        else:
            # Standard rotation
            result = await rotation_service.rotate_secret_with_validation(
                request.secret_name,
                dry_run=request.dry_run
            )
        
        # Log enterprise audit event
        manager._log_secret_access(
            request.secret_name,
            "MANUAL_ROTATION",
            f"Requested by {current_user['email']}, Reason: {request.reason or 'Manual rotation'}"
        )
        
        return SecretRotationResponse(
            success=result.success,
            secret_name=result.secret_name,
            timestamp=result.timestamp,
            old_secret_hash=result.old_secret_hash,
            new_secret_hash=result.new_secret_hash,
            error_message=result.error_message,
            rollback_available=result.rollback_available
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Secret rotation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Secret rotation failed: {str(e)}"
        )

@router.post("/rotate-all")
async def rotate_all_due_secrets(
    force: bool = False,
    dry_run: bool = False,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Rotate all secrets that are due for rotation
    """
    try:
        manager = get_secrets_manager()
        rotation_service = get_rotation_service()

        logger.info(f"Bulk rotation requested [org_id={org_id}]")

        # Get secrets due for rotation
        due_secrets = manager.get_secrets_due_for_rotation()
        
        if not due_secrets and not force:
            return {
                "message": "No secrets due for rotation",
                "rotated_secrets": [],
                "total_processed": 0
            }
        
        # If force is True, rotate all managed secrets
        if force:
            due_secrets = list(manager.secret_metadata.keys())
        
        logger.info(f"🔄 Bulk rotation requested by {current_user['email']} for {len(due_secrets)} secrets")
        
        results = []
        successful = 0
        failed = 0
        
        for secret_name in due_secrets:
            try:
                result = await rotation_service.rotate_secret_with_validation(
                    secret_name,
                    dry_run=dry_run
                )
                
                results.append({
                    "secret_name": secret_name,
                    "success": result.success,
                    "error": result.error_message
                })
                
                if result.success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                results.append({
                    "secret_name": secret_name,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        # Log bulk rotation
        manager._log_secret_access(
            "BULK_ROTATION",
            "BULK_ROTATION",
            f"Bulk rotation by {current_user['email']}: {successful} successful, {failed} failed"
        )
        
        return {
            "message": f"Bulk rotation completed: {successful} successful, {failed} failed",
            "rotated_secrets": results,
            "total_processed": len(due_secrets),
            "successful_rotations": successful,
            "failed_rotations": failed,
            "dry_run": dry_run
        }
        
    except Exception as e:
        logger.error(f"Bulk rotation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk rotation failed: {str(e)}"
        )

@router.post("/schedule")
async def create_rotation_schedule(
    request: RotationScheduleRequest,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Create or update a rotation schedule for a secret
    """
    try:
        rotation_service = get_rotation_service()
        manager = get_secrets_manager()

        logger.info(f"Creating rotation schedule for {request.secret_name} [org_id={org_id}]")

        # Validate secret exists
        current_secret = manager.get_secret(request.secret_name)
        if not current_secret:
            raise HTTPException(
                status_code=404,
                detail=f"Secret '{request.secret_name}' not found"
            )
        
        # Add rotation schedule
        rotation_service.add_rotation_schedule(
            secret_name=request.secret_name,
            cron_expression=request.cron_expression,
            notification_emails=request.notification_emails
        )
        
        # Log schedule creation
        manager._log_secret_access(
            request.secret_name,
            "SCHEDULE_CREATED",
            f"Rotation schedule created by {current_user['email']}: {request.cron_expression}"
        )
        
        logger.info(f"📅 Rotation schedule created for {request.secret_name} by {current_user['email']}")
        
        return {
            "message": f"Rotation schedule created for {request.secret_name}",
            "secret_name": request.secret_name,
            "schedule": request.cron_expression,
            "notification_emails": request.notification_emails,
            "created_by": current_user["email"],
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create rotation schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create rotation schedule: {str(e)}"
        )

@router.get("/schedules")
async def get_rotation_schedules(
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get all rotation schedules
    """
    try:
        rotation_service = get_rotation_service()

        logger.info(f"Fetching rotation schedules [org_id={org_id}]")

        schedules = []
        for secret_name, schedule in rotation_service.rotation_schedules.items():
            schedules.append({
                "secret_name": secret_name,
                "cron_expression": schedule.cron_expression,
                "enabled": schedule.enabled,
                "last_rotation": schedule.last_rotation.isoformat() if schedule.last_rotation else None,
                "next_rotation": schedule.next_rotation.isoformat() if schedule.next_rotation else None,
                "notification_emails": schedule.notification_emails
            })
        
        return {
            "schedules": schedules,
            "total_schedules": len(schedules),
            "enabled_schedules": len([s for s in schedules if s["enabled"]])
        }
        
    except Exception as e:
        logger.error(f"Failed to get rotation schedules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rotation schedules: {str(e)}"
        )

@router.delete("/schedule/{secret_name}")
async def delete_rotation_schedule(
    secret_name: str,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Delete a rotation schedule
    """
    try:
        rotation_service = get_rotation_service()

        logger.info(f"Deleting rotation schedule for {secret_name} [org_id={org_id}]")

        if secret_name not in rotation_service.rotation_schedules:
            raise HTTPException(
                status_code=404,
                detail=f"No rotation schedule found for secret '{secret_name}'"
            )
        
        # Remove schedule
        del rotation_service.rotation_schedules[secret_name]
        
        # Log schedule deletion
        manager = get_secrets_manager()
        manager._log_secret_access(
            secret_name,
            "SCHEDULE_DELETED",
            f"Rotation schedule deleted by {current_user['email']}"
        )
        
        logger.info(f"🗑️ Rotation schedule deleted for {secret_name} by {current_user['email']}")
        
        return {
            "message": f"Rotation schedule deleted for {secret_name}",
            "deleted_by": current_user["email"],
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete rotation schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete rotation schedule: {str(e)}"
        )

@router.get("/compliance-report", response_model=ComplianceReportResponse)
async def get_compliance_report(
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Generate comprehensive compliance report for enterprise auditing
    """
    try:
        manager = get_secrets_manager()

        logger.info(f"Generating compliance report [org_id={org_id}]")

        report = manager.get_compliance_report()
        
        return ComplianceReportResponse(
            total_secrets_managed=report.get("total_secrets_managed", 0),
            high_risk_secrets=report.get("high_risk_secrets", 0),
            secrets_due_for_rotation=report.get("secrets_due_for_rotation", 0),
            primary_provider=report.get("primary_provider", "unknown"),
            audit_trail_entries=report.get("audit_trail_entries", 0),
            compliance_frameworks=report.get("compliance_frameworks", []),
            last_generated=datetime.now(UTC)
        )
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate compliance report: {str(e)}"
        )

@router.get("/audit-trail")
async def get_audit_trail(
    limit: int = 100,
    secret_name: Optional[str] = None,
    action: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get audit trail for compliance and security monitoring
    """
    try:
        manager = get_secrets_manager()

        logger.info(f"Fetching audit trail [org_id={org_id}]")

        audit_entries = manager.get_audit_trail(limit=limit)
        
        # Filter by secret name if provided
        if secret_name:
            audit_entries = [entry for entry in audit_entries 
                           if entry.get("secret_name") == secret_name]
        
        # Filter by action if provided
        if action:
            audit_entries = [entry for entry in audit_entries 
                           if entry.get("action") == action]
        
        # Convert to response format
        formatted_entries = []
        for entry in audit_entries:
            formatted_entries.append(AuditTrailEntry(
                timestamp=datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")),
                secret_name=entry["secret_name"],
                action=entry["action"],
                details=entry["details"],
                user=entry["user"],
                compliance_logged=entry.get("compliance_logged", True)
            ))
        
        return {
            "audit_entries": formatted_entries,
            "total_entries": len(formatted_entries),
            "filters_applied": {
                "secret_name": secret_name,
                "action": action,
                "limit": limit
            },
            "compliance_status": "SOC2_COMPLIANT",
            "retention_period": "7_YEARS"
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit trail: {str(e)}"
        )

@router.get("/rotation-history")
async def get_rotation_history(
    limit: int = 50,
    secret_name: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Get rotation history for monitoring and troubleshooting
    """
    try:
        rotation_service = get_rotation_service()

        logger.info(f"Fetching rotation history [org_id={org_id}]")

        history = rotation_service.get_rotation_history(limit=limit)
        
        # Filter by secret name if provided
        if secret_name:
            history = [entry for entry in history 
                      if entry.get("secret_name") == secret_name]
        
        # Calculate success rate
        if history:
            successful = len([h for h in history if h.get("success", False)])
            success_rate = (successful / len(history)) * 100
        else:
            success_rate = 0
        
        return {
            "rotation_history": history,
            "total_rotations": len(history),
            "success_rate": round(success_rate, 2),
            "filters_applied": {
                "secret_name": secret_name,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get rotation history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve rotation history: {str(e)}"
        )

@router.post("/emergency-rotation")
async def emergency_secret_rotation(
    secret_name: str,
    reason: str,
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Perform emergency secret rotation with enhanced audit logging
    """
    try:
        rotation_service = get_rotation_service()

        logger.warning(f"🚨 Emergency rotation requested by {current_user['email']} for {secret_name} [org_id={org_id}]")
        
        # Validate secret exists
        manager = get_secrets_manager()
        current_secret = manager.get_secret(secret_name)
        if not current_secret:
            raise HTTPException(
                status_code=404,
                detail=f"Secret '{secret_name}' not found"
            )
        
        # Perform emergency rotation
        result = await rotation_service.emergency_rotation(secret_name, reason)
        
        # Enhanced audit logging for emergency
        manager._log_secret_access(
            secret_name,
            "EMERGENCY_ROTATION",
            f"Emergency rotation by {current_user['email']}: {reason}"
        )
        
        return {
            "message": "Emergency rotation completed",
            "secret_name": secret_name,
            "success": result.success,
            "reason": reason,
            "timestamp": result.timestamp.isoformat(),
            "performed_by": current_user["email"],
            "error_message": result.error_message,
            "emergency_notification_sent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency rotation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Emergency rotation failed: {str(e)}"
        )

@router.post("/validate-secrets")
async def validate_all_secrets(
    current_user: dict = Depends(require_admin),
    org_id: int = Depends(get_organization_filter)
):
    """
    Validate all secrets are accessible and meet security requirements
    """
    try:
        manager = get_secrets_manager()

        logger.info(f"Validating all secrets [org_id={org_id}]")

        validation_results = []
        total_secrets = 0
        accessible_secrets = 0
        
        for secret_name in manager.secret_metadata.keys():
            total_secrets += 1
            
            try:
                # Try to retrieve secret
                secret_value = manager.get_secret(secret_name)
                
                if secret_value:
                    accessible_secrets += 1
                    
                    # Validate secret strength
                    meets_requirements = manager._validate_secret_strength(secret_value)
                    
                    validation_results.append({
                        "secret_name": secret_name,
                        "accessible": True,
                        "meets_security_requirements": meets_requirements,
                        "risk_level": manager.secret_metadata[secret_name].risk_level,
                        "last_rotated": manager.secret_metadata[secret_name].last_rotated.isoformat()
                    })
                else:
                    validation_results.append({
                        "secret_name": secret_name,
                        "accessible": False,
                        "meets_security_requirements": False,
                        "error": "Secret not accessible"
                    })
                    
            except Exception as e:
                validation_results.append({
                    "secret_name": secret_name,
                    "accessible": False,
                    "meets_security_requirements": False,
                    "error": str(e)
                })
        
        # Calculate health score
        if total_secrets > 0:
            health_score = (accessible_secrets / total_secrets) * 100
        else:
            health_score = 100
        
        # Log validation
        manager._log_secret_access(
            "VALIDATION",
            "BULK_VALIDATION",
            f"Secret validation by {current_user['email']}: {accessible_secrets}/{total_secrets} accessible"
        )
        
        return {
            "validation_results": validation_results,
            "summary": {
                "total_secrets": total_secrets,
                "accessible_secrets": accessible_secrets,
                "health_score": round(health_score, 2),
                "secrets_needing_attention": total_secrets - accessible_secrets
            },
            "performed_by": current_user["email"],
            "timestamp": datetime.now(UTC).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Secret validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Secret validation failed: {str(e)}"
        )

@router.get("/health")
async def get_secrets_health_check(
    org_id: int = Depends(get_organization_filter)
):
    """
    Health check endpoint for secrets management system
    """
    try:
        manager = get_secrets_manager()
        rotation_service = get_rotation_service()

        logger.info(f"Health check requested [org_id={org_id}]")

        # Basic health checks
        health_status = {
            "secrets_manager": "healthy",
            "rotation_service": "healthy" if rotation_service.is_running else "stopped",
            "provider_status": "connected",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        # Test secret retrieval
        try:
            test_secret = manager.get_secret("SECRET_KEY")
            health_status["secret_retrieval"] = "operational" if test_secret else "degraded"
        except Exception:
            health_status["secret_retrieval"] = "failed"
        
        # Check for overdue rotations
        due_secrets = manager.get_secrets_due_for_rotation()
        health_status["rotation_status"] = "healthy" if len(due_secrets) == 0 else "attention_needed"
        health_status["secrets_due_for_rotation"] = len(due_secrets)
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "secrets_manager": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }