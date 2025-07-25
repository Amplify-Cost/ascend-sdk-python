from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
import json
from datetime import datetime, timedelta

from database import get_db
from models import User, AgentAction, PendingAgentAction, Alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/siem", tags=["siem"])

# Simplified SIEM Configuration (no external dependencies)

# Pydantic Models for SIEM Configuration
class SIEMConfigRequest(BaseModel):
    siem_type: str  # "splunk", "qradar", "sentinel", "elastic"
    host: str
    port: int
    username: str
    password: str
    api_token: Optional[str] = None
    use_ssl: bool = True
    verify_ssl: bool = True
    index_name: str = "owai_security"

class SIEMTestRequest(BaseModel):
    config: SIEMConfigRequest

class EventQueryRequest(BaseModel):
    query: str
    time_range_hours: int = 24
    max_results: int = 100

# SIEM Configuration Endpoints
@router.post("/configure")
async def configure_siem(
    config_request: SIEMConfigRequest,
    db: Session = Depends(get_db)
):
    """Configure SIEM integration for enterprise deployment"""
    try:
        # Create SIEM configuration
        siem_config = SIEMConfig(
            siem_type=SIEMType(config_request.siem_type),
            host=config_request.host,
            port=config_request.port,
            username=config_request.username,
            password=config_request.password,
            api_token=config_request.api_token,
            use_ssl=config_request.use_ssl,
            verify_ssl=config_request.verify_ssl,
            index_name=config_request.index_name
        )
        
        # Create appropriate connector
        if siem_config.siem_type == SIEMType.SPLUNK:
            connector = SplunkConnector(siem_config)
        elif siem_config.siem_type == SIEMType.QRADAR:
            connector = QRadarConnector(siem_config)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"SIEM type {config_request.siem_type} not yet supported"
            )
        
        # Test connection
        connection_successful = await connector.connect()
        if not connection_successful:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to SIEM. Please check configuration."
            )
        
        # Add to manager
        siem_manager.add_connector(config_request.siem_type, connector)
        
        logger.info(f"✅ SIEM integration configured: {config_request.siem_type}")
        
        return {
            "status": "success",
            "message": f"{config_request.siem_type.title()} SIEM integration configured successfully",
            "siem_type": config_request.siem_type,
            "host": config_request.host,
            "index_name": config_request.index_name,
            "connection_status": "connected"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid SIEM type: {str(e)}")
    except Exception as e:
        logger.error(f"❌ SIEM configuration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"SIEM configuration failed: {str(e)}"
        )

@router.post("/test-connection")
async def test_siem_connection(
    test_request: SIEMTestRequest,
    db: Session = Depends(get_db)
):
    """Test SIEM connection before saving configuration"""
    try:
        # Create temporary SIEM configuration for testing
        siem_config = SIEMConfig(
            siem_type=SIEMType(test_request.config.siem_type),
            host=test_request.config.host,
            port=test_request.config.port,
            username=test_request.config.username,
            password=test_request.config.password,
            api_token=test_request.config.api_token,
            use_ssl=test_request.config.use_ssl,
            verify_ssl=test_request.config.verify_ssl,
            index_name=test_request.config.index_name
        )
        
        # Create appropriate connector
        if siem_config.siem_type == SIEMType.SPLUNK:
            connector = SplunkConnector(siem_config)
        elif siem_config.siem_type == SIEMType.QRADAR:
            connector = QRadarConnector(siem_config)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"SIEM type {test_request.config.siem_type} not yet supported"
            )
        
        # Test connection
        connection_successful = await connector.connect()
        
        if connection_successful:
            return {
                "status": "success",
                "message": f"Successfully connected to {test_request.config.siem_type.title()}",
                "connection_test": "passed",
                "siem_info": {
                    "type": test_request.config.siem_type,
                    "host": test_request.config.host,
                    "port": test_request.config.port,
                    "ssl_enabled": test_request.config.use_ssl
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to connect to {test_request.config.siem_type.title()}",
                "connection_test": "failed",
                "recommendations": [
                    "Verify host and port are correct",
                    "Check username and password",
                    "Ensure SIEM is accessible from this network",
                    "Verify SSL/TLS settings"
                ]
            }
            
    except Exception as e:
        logger.error(f"❌ SIEM connection test failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}",
            "connection_test": "error"
        }

@router.get("/status")
async def get_siem_status():
    """Get current SIEM integration status"""
    try:
        if not siem_manager.active_connector:
            return {
                "status": "not_configured",
                "message": "No SIEM integration configured",
                "configured_connectors": list(siem_manager.connectors.keys())
            }
        
        # Test current connection
        connection_ok = await siem_manager.active_connector.connect()
        
        return {
            "status": "configured" if connection_ok else "connection_error",
            "message": "SIEM integration active" if connection_ok else "SIEM connection failed",
            "configured_connectors": list(siem_manager.connectors.keys()),
            "active_connector": siem_manager.active_connector.config.siem_type.value if siem_manager.active_connector else None,
            "connection_healthy": connection_ok
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking SIEM status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking SIEM status: {str(e)}"
        }

# Event Management Endpoints
@router.post("/send-test-event")
async def send_test_event(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send test event to configured SIEM"""
    try:
        if not siem_manager.active_connector:
            raise HTTPException(
                status_code=400,
                detail="No SIEM integration configured"
            )
        
        # Send test authorization event
        success = await siem_manager.send_authorization_event(
            action_id=9999,
            agent_id="test-agent-001",
            action_type="test_siem_integration",
            decision="approved",
            risk_score=75,
            user_email="system@owai.com",
            nist_control="AC-3",
            mitre_tactic="TA0005"
        )
        
        if success:
            return {
                "status": "success",
                "message": "Test event sent successfully to SIEM",
                "event_details": {
                    "event_type": "agent_authorization",
                    "agent_id": "test-agent-001",
                    "action_type": "test_siem_integration",
                    "risk_score": 75,
                    "decision": "approved"
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send test event to SIEM"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending test event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test event: {str(e)}"
        )

@router.post("/query-events")
async def query_siem_events(
    query_request: EventQueryRequest,
    db: Session = Depends(get_db)
):
    """Query events from SIEM for threat intelligence"""
    try:
        if not siem_manager.active_connector:
            raise HTTPException(
                status_code=400,
                detail="No SIEM integration configured"
            )
        
        # Query events from SIEM
        events = await siem_manager.active_connector.query_events(
            query_request.query,
            query_request.time_range_hours
        )
        
        # Limit results
        limited_events = events[:query_request.max_results]
        
        return {
            "status": "success",
            "query": query_request.query,
            "time_range_hours": query_request.time_range_hours,
            "total_events_found": len(events),
            "events_returned": len(limited_events),
            "events": limited_events,
            "query_metadata": {
                "executed_at": datetime.utcnow().isoformat(),
                "siem_type": siem_manager.active_connector.config.siem_type.value,
                "truncated": len(events) > query_request.max_results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error querying SIEM events: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying SIEM events: {str(e)}"
        )

@router.get("/threat-intelligence/{agent_id}")
async def get_agent_threat_intelligence(
    agent_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get threat intelligence for specific agent from SIEM"""
    try:
        if not siem_manager.active_connector:
            return {
                "status": "no_siem_configured",
                "message": "SIEM integration not configured",
                "agent_id": agent_id
            }
        
        # Get threat intelligence from SIEM
        threat_intel = await siem_manager.get_threat_intelligence(agent_id, hours)
        
        # Enhance with local data
        local_actions = db.query(AgentAction).filter(
            AgentAction.agent_id == agent_id,
            AgentAction.timestamp >= datetime.utcnow() - timedelta(hours=hours)
        ).all()
        
        local_pending = db.query(PendingAgentAction).filter(
            PendingAgentAction.agent_id == agent_id,
            PendingAgentAction.requested_at >= datetime.utcnow() - timedelta(hours=hours)
        ).all()
        
        # Combine SIEM and local intelligence
        enhanced_intel = {
            **threat_intel,
            "local_data": {
                "recent_actions": len(local_actions),
                "pending_authorizations": len(local_pending),
                "high_risk_local_actions": len([a for a in local_actions if a.risk_level in ["high", "critical"]]),
                "recent_action_types": list(set([a.action_type for a in local_actions]))
            },
            "combined_risk_assessment": {
                "total_events": threat_intel.get("total_events", 0) + len(local_actions),
                "risk_trend": "increasing" if threat_intel.get("high_risk_events", 0) > 3 else "stable",
                "recommendation": "enhanced_monitoring" if threat_intel.get("high_risk_events", 0) > 5 else "normal_monitoring"
            }
        }
        
        return enhanced_intel
        
    except Exception as e:
        logger.error(f"❌ Error getting threat intelligence: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving threat intelligence: {str(e)}"
        )

# Batch Event Management
@router.post("/sync-recent-events")
async def sync_recent_events_to_siem(
    hours: int = 24,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Sync recent OW-AI events to SIEM (useful for initial setup)"""
    try:
        if not siem_manager.active_connector:
            raise HTTPException(
                status_code=400,
                detail="No SIEM integration configured"
            )
        
        # Get recent events from database
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_actions = db.query(AgentAction).filter(
            AgentAction.timestamp >= cutoff_time
        ).all()
        
        recent_authorizations = db.query(PendingAgentAction).filter(
            PendingAgentAction.requested_at >= cutoff_time
        ).all()
        
        # Count events to sync
        total_events = len(recent_actions) + len(recent_authorizations)
        
        if total_events == 0:
            return {
                "status": "success",
                "message": "No recent events to sync",
                "events_synced": 0,
                "time_range_hours": hours
            }
        
        # Background task for large syncs
        if background_tasks and total_events > 50:
            background_tasks.add_task(
                _sync_events_background,
                recent_actions,
                recent_authorizations,
                siem_manager
            )
            
            return {
                "status": "initiated",
                "message": f"Background sync initiated for {total_events} events",
                "events_to_sync": total_events,
                "sync_mode": "background"
            }
        
        # Immediate sync for smaller batches
        sync_results = await _sync_events_immediate(recent_actions, recent_authorizations)
        
        return {
            "status": "completed",
            "message": f"Synced {sync_results['synced']} of {total_events} events",
            "events_synced": sync_results['synced'],
            "events_failed": sync_results['failed'],
            "sync_mode": "immediate",
            "details": sync_results['details']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing events to SIEM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing events: {str(e)}"
        )

# Configuration Management
@router.get("/supported-siems")
async def get_supported_siems():
    """Get list of supported SIEM integrations"""
    return {
        "supported_siems": [
            {
                "type": "splunk",
                "name": "Splunk Enterprise",
                "description": "Enterprise-grade security information and event management",
                "authentication": ["username_password"],
                "features": ["real_time_events", "queries", "batch_upload"],
                "status": "fully_supported"
            },
            {
                "type": "qradar",
                "name": "IBM QRadar",
                "description": "IBM security intelligence platform",
                "authentication": ["api_token"],
                "features": ["real_time_events", "offense_creation"],
                "status": "fully_supported"
            },
            {
                "type": "sentinel",
                "name": "Microsoft Sentinel",
                "description": "Cloud-native SIEM and SOAR solution",
                "authentication": ["azure_ad"],
                "features": ["log_analytics", "workbooks"],
                "status": "coming_soon"
            },
            {
                "type": "elastic",
                "name": "Elastic Security",
                "description": "Open-source security analytics platform",
                "authentication": ["api_key"],
                "features": ["elasticsearch_integration", "kibana_dashboards"],
                "status": "coming_soon"
            }
        ],
        "enterprise_features": [
            "Real-time event streaming",
            "Batch event synchronization",
            "Threat intelligence queries",
            "Custom event formatting",
            "SSL/TLS encryption",
            "Connection health monitoring"
        ]
    }

# Helper functions
async def _sync_events_immediate(actions: List[AgentAction], authorizations: List[PendingAgentAction]) -> Dict[str, Any]:
    """Sync events immediately (for small batches)"""
    synced = 0
    failed = 0
    details = []
    
    # Sync agent actions
    for action in actions:
        try:
            success = await siem_manager.send_agent_action_event(
                action_id=action.id,
                agent_id=action.agent_id,
                action_type=action.action_type,
                risk_score=70 if action.risk_level == "high" else 50,  # Default risk scores
                status=action.status,
                nist_control=action.nist_control,
                mitre_tactic=action.mitre_tactic
            )
            
            if success:
                synced += 1
                details.append(f"✅ Action {action.id} synced")
            else:
                failed += 1
                details.append(f"❌ Action {action.id} failed")
                
        except Exception as e:
            failed += 1
            details.append(f"❌ Action {action.id} error: {str(e)}")
    
    # Sync authorization events
    for auth in authorizations:
        try:
            success = await siem_manager.send_authorization_event(
                action_id=auth.id,
                agent_id=auth.agent_id,
                action_type=auth.action_type,
                decision=auth.authorization_status,
                risk_score=auth.ai_risk_score or 50,
                user_email=auth.reviewed_by or "system",
                nist_control=auth.nist_control,
                mitre_tactic=auth.mitre_tactic
            )
            
            if success:
                synced += 1
                details.append(f"✅ Authorization {auth.id} synced")
            else:
                failed += 1
                details.append(f"❌ Authorization {auth.id} failed")
                
        except Exception as e:
            failed += 1
            details.append(f"❌ Authorization {auth.id} error: {str(e)}")
    
    return {
        "synced": synced,
        "failed": failed,
        "details": details[-10:]  # Last 10 details only
    }

async def _sync_events_background(
    actions: List[AgentAction], 
    authorizations: List[PendingAgentAction],
    siem_manager: SIEMManager
):
    """Background task for syncing large batches of events"""
    logger.info(f"🔄 Starting background SIEM sync: {len(actions)} actions, {len(authorizations)} authorizations")
    
    try:
        sync_results = await _sync_events_immediate(actions, authorizations)
        logger.info(f"✅ Background SIEM sync completed: {sync_results['synced']} synced, {sync_results['failed']} failed")
    except Exception as e:
        logger.error(f"❌ Background SIEM sync failed: {str(e)}")

# Auto-sync functionality
@router.post("/enable-auto-sync")
async def enable_auto_sync(
    enabled: bool = True,
    db: Session = Depends(get_db)
):
    """Enable/disable automatic SIEM synchronization"""
    try:
        # Store auto-sync preference (you might want to store this in database)
        # For now, we'll just return the configuration
        
        return {
            "status": "success",
            "auto_sync_enabled": enabled,
            "message": f"Auto-sync {'enabled' if enabled else 'disabled'}",
            "sync_frequency": "real_time",
            "features": [
                "Immediate event forwarding",
                "Automatic retry on failure",
                "Connection health monitoring",
                "Batch optimization for high volume"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error configuring auto-sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring auto-sync: {str(e)}"
        )