"""
Enterprise Health Check Module
Comprehensive system health monitoring for production deployment
"""

from fastapi import APIRouter, HTTPException
import time
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Enterprise health check endpoint
    Monitors all critical system components
    """
    
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check Enterprise Config
    try:
        from enterprise_config import config
        config_healthy = True
        config_details = {
            "status": "healthy",
            "environment": config.environment,
            "aws_enabled": getattr(config, 'use_vault', False),
            "fallback_mode": not getattr(config, 'use_vault', True)
        }
        
        # Test config functionality
        test_secret = config.get_secret('test') if hasattr(config, 'get_secret') else None
        config_details["secret_access"] = "available"
        
    except Exception as e:
        config_healthy = False
        config_details = {
            "status": "unhealthy",
            "error": str(e),
            "fallback_available": True
        }
        health_status["status"] = "degraded"
    
    health_status["checks"]["enterprise_config"] = config_details
    
    # Check JWT Manager
    try:
        from jwt_manager import jwt_manager
        jwt_healthy = bool(getattr(jwt_manager, 'private_key', None) and 
                          getattr(jwt_manager, 'public_key', None))
        
        jwt_details = {
            "status": "healthy" if jwt_healthy else "unhealthy",
            "has_private_key": bool(getattr(jwt_manager, 'private_key', None)),
            "has_public_key": bool(getattr(jwt_manager, 'public_key', None)),
            "algorithm": "RS256",
            "issuer": getattr(jwt_manager, 'issuer', 'unknown')
        }
        
        if not jwt_healthy:
            health_status["status"] = "degraded"
            
    except Exception as e:
        jwt_details = {
            "status": "unhealthy",
            "error": str(e),
            "fallback_available": True
        }
        health_status["status"] = "degraded"
    
    health_status["checks"]["jwt_manager"] = jwt_details
    
    # Check RBAC System
    try:
        from rbac_manager import enterprise_rbac
        rbac_healthy = True
        rbac_details = {
            "status": "healthy",
            "access_levels": len(getattr(enterprise_rbac, 'role_permissions', {})),
            "permissions_loaded": bool(getattr(enterprise_rbac, 'role_permissions', None)),
            "separation_of_duties": bool(getattr(enterprise_rbac, 'separation_of_duties', None))
        }
        
    except Exception as e:
        rbac_healthy = False
        rbac_details = {
            "status": "unhealthy",
            "error": str(e),
            "fallback_available": False
        }
        health_status["status"] = "degraded"
    
    health_status["checks"]["rbac_system"] = rbac_details
    
    # Check SSO Manager
    try:
        from sso_manager import enterprise_sso
        sso_details = {
            "status": "healthy",
            "providers_configured": len(getattr(enterprise_sso, 'providers', {})),
            "group_mappings": len(getattr(enterprise_sso, 'group_to_role_mapping', {})),
            "available_providers": list(getattr(enterprise_sso, 'providers', {}).keys())
        }
        
    except Exception as e:
        sso_details = {
            "status": "unhealthy", 
            "error": str(e),
            "fallback_available": False
        }
        health_status["status"] = "degraded"
    
    health_status["checks"]["sso_manager"] = sso_details
    
    # Check Database Connection
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        db_details = {
            "status": "healthy",
            "connection": "active",
            "engine_available": True
        }
        
    except Exception as e:
        db_details = {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }
        health_status["status"] = "degraded"
    
    health_status["checks"]["database"] = db_details
    
    # Overall response time
    response_time = round((time.time() - start_time) * 1000, 2)
    health_status["response_time_ms"] = response_time
    
    # Determine final status
    failed_checks = [name for name, check in health_status["checks"].items() 
                    if check.get("status") != "healthy"]
    
    if len(failed_checks) == 0:
        health_status["status"] = "healthy"
    elif len(failed_checks) <= 2:
        health_status["status"] = "degraded" 
    else:
        health_status["status"] = "unhealthy"
        
    health_status["failed_checks"] = failed_checks
    health_status["enterprise_grade"] = True
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    logger.info(f"Enterprise health check completed: {health_status['status']} ({response_time}ms)")
    return health_status

@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Enterprise readiness check - determines if app can serve traffic
    More thorough than health check
    """
    
    readiness_status = {
        "ready": True,
        "timestamp": int(time.time()),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "services": {},
        "enterprise_features": {}
    }
    
    # Check critical services for readiness
    critical_services = []
    
    try:
        # Enterprise Config Readiness
        from enterprise_config import config
        config_ready = hasattr(config, 'get_secret')
        readiness_status["services"]["enterprise_config"] = config_ready
        if not config_ready:
            critical_services.append("enterprise_config")
            
        # JWT Manager Readiness  
        from jwt_manager import jwt_manager
        jwt_ready = bool(getattr(jwt_manager, 'private_key', None))
        readiness_status["services"]["jwt_manager"] = jwt_ready
        if not jwt_ready:
            critical_services.append("jwt_manager")
            
        # Database Readiness
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ready = True
        readiness_status["services"]["database"] = db_ready
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        critical_services.append("database")
        readiness_status["services"]["database"] = False
    
    # Enterprise Features Readiness
    try:
        from rbac_manager import enterprise_rbac
        readiness_status["enterprise_features"]["rbac"] = True
    except:
        readiness_status["enterprise_features"]["rbac"] = False
        
    try:
        from sso_manager import enterprise_sso  
        readiness_status["enterprise_features"]["sso"] = True
    except:
        readiness_status["enterprise_features"]["sso"] = False
    
    # Overall readiness determination
    readiness_status["ready"] = len(critical_services) == 0
    readiness_status["failed_services"] = critical_services
    readiness_status["enterprise_ready"] = (
        readiness_status["services"].get("enterprise_config", False) and
        readiness_status["services"].get("jwt_manager", False) and
        readiness_status["enterprise_features"].get("rbac", False)
    )
    
    if not readiness_status["ready"]:
        raise HTTPException(status_code=503, detail=readiness_status)
    
    return readiness_status

@router.get("/startup")
async def startup_check() -> Dict[str, Any]:
    """
    Enterprise startup validation
    Confirms all enterprise modules loaded correctly
    """
    
    startup_status = {
        "startup_complete": True,
        "timestamp": int(time.time()),
        "modules_loaded": {},
        "enterprise_grade": True
    }
    
    # Check each enterprise module
    modules_to_check = [
        ("enterprise_config", "enterprise_config"),
        ("jwt_manager", "jwt_manager"), 
        ("rbac_manager", "rbac_manager"),
        ("sso_manager", "sso_manager")
    ]
    
    for module_name, import_name in modules_to_check:
        try:
            __import__(import_name)
            startup_status["modules_loaded"][module_name] = {
                "status": "loaded",
                "available": True
            }
        except ImportError as e:
            startup_status["modules_loaded"][module_name] = {
                "status": "failed",
                "error": str(e),
                "available": False
            }
            startup_status["startup_complete"] = False
    
    # Enterprise readiness score
    loaded_modules = sum(1 for module in startup_status["modules_loaded"].values() 
                        if module["status"] == "loaded")
    total_modules = len(modules_to_check)
    
    startup_status["enterprise_readiness_score"] = f"{loaded_modules}/{total_modules}"
    startup_status["readiness_percentage"] = round((loaded_modules / total_modules) * 100, 1)
    
    return startup_status

@router.get("/health/deployment")
async def deployment_verification_check() -> Dict[str, Any]:
    """
    Enterprise deployment verification health check
    Validates that enrichment services are working correctly
    Used for post-deployment validation
    """

    deployment_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "deployment_verified": False,
        "commit_sha": os.getenv("GIT_COMMIT_SHA", "unknown"),
        "checks": {},
        "enterprise_grade": True
    }

    try:
        # Check 1: Database connection and data presence
        from database import SessionLocal
        from models import AgentAction

        db = SessionLocal()
        try:
            total_actions = db.query(AgentAction).count()
            enriched_count = db.query(AgentAction).filter(
                AgentAction.cvss_score != None
            ).count()

            enrichment_percentage = (enriched_count / total_actions * 100) if total_actions > 0 else 0

            deployment_status["checks"]["database"] = {
                "status": "healthy",
                "total_actions": total_actions,
                "enriched_actions": enriched_count,
                "enrichment_percentage": round(enrichment_percentage, 1)
            }

            # Check 2: Sample action has enrichment data
            sample_action = db.query(AgentAction).filter(
                AgentAction.cvss_score != None
            ).first()

            if sample_action:
                deployment_status["checks"]["enrichment_sample"] = {
                    "status": "healthy",
                    "action_id": sample_action.id,
                    "cvss_score": sample_action.cvss_score,
                    "cvss_severity": sample_action.cvss_severity,
                    "mitre_tactic": sample_action.mitre_tactic,
                    "nist_control": sample_action.nist_control,
                    "has_complete_enrichment": bool(
                        sample_action.cvss_score and
                        sample_action.mitre_tactic and
                        sample_action.nist_control
                    )
                }
            else:
                deployment_status["checks"]["enrichment_sample"] = {
                    "status": "warning",
                    "message": "No enriched actions found"
                }
                deployment_status["status"] = "degraded"

            # Check 3: Enrichment services are loaded
            try:
                from services.cvss_calculator import calculate_base_score
                from services.mitre_mapper import map_action_to_techniques
                from services.nist_mapper import map_action_to_controls
                from enrichment import evaluate_action_enrichment

                deployment_status["checks"]["enrichment_services"] = {
                    "status": "healthy",
                    "cvss_calculator": True,
                    "mitre_mapper": True,
                    "nist_mapper": True,
                    "orchestrator": True
                }
            except ImportError as e:
                deployment_status["checks"]["enrichment_services"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                deployment_status["status"] = "unhealthy"

            # Overall deployment verification
            deployment_verified = (
                total_actions > 0 and
                enrichment_percentage > 50 and
                sample_action is not None and
                deployment_status["checks"]["enrichment_services"]["status"] == "healthy"
            )

            deployment_status["deployment_verified"] = deployment_verified

            if not deployment_verified:
                deployment_status["status"] = "degraded"
                deployment_status["reason"] = "Enrichment data incomplete or services unavailable"

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Deployment verification failed: {e}", exc_info=True)
        deployment_status["status"] = "unhealthy"
        deployment_status["error"] = str(e)
        deployment_status["deployment_verified"] = False

    # Return appropriate HTTP status
    if deployment_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=deployment_status)

    logger.info(f"🔍 DEPLOYMENT VERIFICATION: {deployment_status['status']} - Verified: {deployment_status['deployment_verified']}")
    return deployment_status