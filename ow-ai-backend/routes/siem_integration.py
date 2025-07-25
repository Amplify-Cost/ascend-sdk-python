# routes/siem_integration.py - Simple Enterprise SIEM Integration
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
import json
import requests
from datetime import datetime, timedelta

from database import get_db
from models import User, AgentAction, PendingAgentAction, Alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enterprise/siem", tags=["enterprise-siem"])

# Simple SIEM Configuration Models
class SIEMConfig(BaseModel):
    siem_type: str  # "splunk", "qradar", "webhook"
    endpoint_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    verify_ssl: bool = True

class SIEMEvent(BaseModel):
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    agent_id: str
    action_type: str
    risk_score: int
    status: str
    user_email: Optional[str] = None
    nist_control: Optional[str] = None
    mitre_tactic: Optional[str] = None

# Global SIEM configuration (in production, store in database)
current_siem_config: Optional[SIEMConfig] = None

# SIEM Configuration Endpoints
@router.post("/configure")
async def configure_siem_integration(
    config: SIEMConfig,
    db: Session = Depends(get_db)
):
    """Configure enterprise SIEM integration"""
    try:
        global current_siem_config
        
        # Test the configuration
        test_result = await test_siem_connection(config)
        
        if test_result["status"] == "success":
            current_siem_config = config
            
            logger.info(f"✅ SIEM integration configured: {config.siem_type}")
            
            return {
                "status": "success",
                "message": f"{config.siem_type.title()} SIEM integration configured successfully",
                "siem_type": config.siem_type,
                "endpoint": config.endpoint_url,
                "connection_test": "passed",
                "features_enabled": [
                    "Real-time event forwarding",
                    "Authorization logging",
                    "Emergency override alerts",
                    "Risk-based event prioritization"
                ]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"SIEM configuration test failed: {test_result.get('message', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"❌ SIEM configuration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"SIEM configuration failed: {str(e)}"
        )

@router.post("/test-connection")
async def test_siem_connection(config: SIEMConfig):
    """Test SIEM connection"""
    try:
        if config.siem_type == "webhook":
            # Test webhook endpoint
            test_payload = {
                "test": True,
                "source": "ow-ai-enterprise",
                "message": "SIEM integration test",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            headers = {"Content-Type": "application/json"}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            response = requests.post(
                config.endpoint_url,
                json=test_payload,
                headers=headers,
                timeout=10,
                verify=config.verify_ssl
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    "status": "success",
                    "message": "Webhook endpoint responding correctly",
                    "response_code": response.status_code
                }
            else:
                return {
                    "status": "error",
                    "message": f"Webhook returned status {response.status_code}",
                    "response_code": response.status_code
                }
                
        elif config.siem_type == "splunk":
            # Test Splunk HEC endpoint
            test_payload = {
                "event": {
                    "test": True,
                    "source": "ow-ai-enterprise",
                    "message": "Splunk HEC test"
                },
                "time": datetime.utcnow().timestamp(),
                "source": "ow-ai",
                "sourcetype": "owai:test"
            }
            
            headers = {
                "Authorization": f"Splunk {config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                config.endpoint_url,
                json=test_payload,
                headers=headers,
                timeout=10,
                verify=config.verify_ssl
            )
            
            if response.status_code in [200, 201]:
                return {
                    "status": "success",
                    "message": "Splunk HEC endpoint responding correctly",
                    "response_code": response.status_code
                }
            else:
                return {
                    "status": "error",
                    "message": f"Splunk HEC returned status {response.status_code}",
                    "response_code": response.status_code
                }
                
        else:
            return {
                "status": "error",
                "message": f"SIEM type '{config.siem_type}' not supported yet"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Connection failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}"
        }

@router.get("/status")
async def get_siem_status():
    """Get current SIEM integration status"""
    try:
        if not current_siem_config:
            return {
                "status": "not_configured",
                "message": "No SIEM integration configured",
                "integration_available": True,
                "supported_types": ["splunk", "qradar", "webhook"]
            }
        
        # Test current connection
        test_result = await test_siem_connection(current_siem_config)
        
        return {
            "status": "configured",
            "siem_type": current_siem_config.siem_type,
            "endpoint": current_siem_config.endpoint_url,
            "connection_healthy": test_result["status"] == "success",
            "last_test": datetime.utcnow().isoformat(),
            "message": "SIEM integration active"
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking SIEM status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking SIEM status: {str(e)}"
        }

# Event Sending Functions
async def send_event_to_siem(event: SIEMEvent) -> bool:
    """Send event to configured SIEM"""
    try:
        if not current_siem_config:
            logger.info("⚠️ No SIEM configured, skipping event")
            return True  # Don't fail if SIEM not configured
        
        if current_siem_config.siem_type == "webhook":
            return await send_webhook_event(event)
        elif current_siem_config.siem_type == "splunk":
            return await send_splunk_event(event)
        else:
            logger.warning(f"⚠️ Unsupported SIEM type: {current_siem_config.siem_type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending event to SIEM: {str(e)}")
        return False

async def send_webhook_event(event: SIEMEvent) -> bool:
    """Send event to webhook endpoint"""
    try:
        payload = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "source": "ow-ai-enterprise",
            "event_type": event.event_type,
            "severity": event.severity,
            "agent_id": event.agent_id,
            "action_type": event.action_type,
            "risk_score": event.risk_score,
            "status": event.status,
            "user_email": event.user_email,
            "compliance": {
                "nist_control": event.nist_control,
                "mitre_tactic": event.mitre_tactic
            },
            "platform": "ow-ai-enterprise-security"
        }
        
        headers = {"Content-Type": "application/json"}
        if current_siem_config.api_key:
            headers["Authorization"] = f"Bearer {current_siem_config.api_key}"
        
        response = requests.post(
            current_siem_config.endpoint_url,
            json=payload,
            headers=headers,
            timeout=10,
            verify=current_siem_config.verify_ssl
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Event {event.event_id} sent to webhook SIEM")
            return True
        else:
            logger.error(f"❌ Webhook SIEM returned status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending webhook event: {str(e)}")
        return False

async def send_splunk_event(event: SIEMEvent) -> bool:
    """Send event to Splunk HEC"""
    try:
        payload = {
            "time": datetime.utcnow().timestamp(),
            "source": "ow-ai-enterprise",
            "sourcetype": "owai:security:event",
            "event": {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "agent_id": event.agent_id,
                "action_type": event.action_type,
                "risk_score": event.risk_score,
                "status": event.status,
                "user_email": event.user_email,
                "nist_control": event.nist_control,
                "mitre_tactic": event.mitre_tactic,
                "platform": "ow-ai-enterprise"
            }
        }
        
        headers = {
            "Authorization": f"Splunk {current_siem_config.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            current_siem_config.endpoint_url,
            json=payload,
            headers=headers,
            timeout=10,
            verify=current_siem_config.verify_ssl
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Event {event.event_id} sent to Splunk")
            return True
        else:
            logger.error(f"❌ Splunk returned status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending Splunk event: {str(e)}")
        return False

# Enterprise Event Creation Functions
async def send_authorization_event(
    action_id: int,
    agent_id: str,
    action_type: str,
    decision: str,
    risk_score: int,
    user_email: str,
    nist_control: str = None,
    mitre_tactic: str = None
):
    """Send authorization decision event to SIEM"""
    event = SIEMEvent(
        event_id=f"owai-auth-{action_id}",
        timestamp=datetime.utcnow().isoformat(),
        event_type="agent_authorization",
        severity="high" if risk_score >= 70 else "medium",
        agent_id=agent_id,
        action_type=action_type,
        risk_score=risk_score,
        status=decision,
        user_email=user_email,
        nist_control=nist_control,
        mitre_tactic=mitre_tactic
    )
    
    return await send_event_to_siem(event)

async def send_emergency_override_event(
    action_id: int,
    agent_id: str,
    action_type: str,
    risk_score: int,
    user_email: str,
    nist_control: str = None,
    mitre_tactic: str = None
):
    """Send emergency override event to SIEM"""
    event = SIEMEvent(
        event_id=f"owai-emergency-{action_id}",
        timestamp=datetime.utcnow().isoformat(),
        event_type="emergency_override",
        severity="critical",
        agent_id=agent_id,
        action_type=f"EMERGENCY:{action_type}",
        risk_score=min(100, risk_score + 20),  # Boost risk for emergency
        status="emergency_approved",
        user_email=user_email,
        nist_control=nist_control,
        mitre_tactic=mitre_tactic
    )
    
    return await send_event_to_siem(event)

async def send_agent_action_event(
    action_id: int,
    agent_id: str,
    action_type: str,
    risk_score: int,
    status: str,
    nist_control: str = None,
    mitre_tactic: str = None
):
    """Send agent action event to SIEM"""
    event = SIEMEvent(
        event_id=f"owai-action-{action_id}",
        timestamp=datetime.utcnow().isoformat(),
        event_type="agent_action",
        severity="critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium",
        agent_id=agent_id,
        action_type=action_type,
        risk_score=risk_score,
        status=status,
        nist_control=nist_control,
        mitre_tactic=mitre_tactic
    )
    
    return await send_event_to_siem(event)

# Test and Management Endpoints
@router.post("/send-test-event")
async def send_test_event():
    """Send test event to configured SIEM"""
    try:
        if not current_siem_config:
            raise HTTPException(
                status_code=400,
                detail="No SIEM integration configured"
            )
        
        success = await send_authorization_event(
            action_id=9999,
            agent_id="test-agent-enterprise",
            action_type="test_siem_integration",
            decision="approved",
            risk_score=75,
            user_email="admin@company.com",
            nist_control="AC-3",
            mitre_tactic="TA0005"
        )
        
        if success:
            return {
                "status": "success",
                "message": "Test event sent successfully to SIEM",
                "siem_type": current_siem_config.siem_type,
                "event_details": {
                    "event_type": "agent_authorization",
                    "agent_id": "test-agent-enterprise",
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

@router.get("/supported-integrations")
async def get_supported_integrations():
    """Get list of supported SIEM integrations"""
    return {
        "supported_siems": [
            {
                "type": "splunk",
                "name": "Splunk Enterprise",
                "description": "HTTP Event Collector (HEC) integration",
                "setup_required": ["HEC endpoint URL", "API token"],
                "status": "fully_supported"
            },
            {
                "type": "webhook",
                "name": "Generic Webhook",
                "description": "Send events to any HTTP endpoint",
                "setup_required": ["Webhook URL", "Optional API key"],
                "status": "fully_supported"
            },
            {
                "type": "qradar",
                "name": "IBM QRadar",
                "description": "IBM QRadar SIEM integration",
                "setup_required": ["QRadar API endpoint", "API token"],
                "status": "coming_soon"
            }
        ],
        "enterprise_features": [
            "Real-time security event streaming",
            "Authorization decision logging",
            "Emergency override alerts",
            "Risk-based event classification",
            "NIST/MITRE compliance tagging",
            "Custom event formatting"
        ],
        "setup_guide": {
            "splunk": "Configure HTTP Event Collector in Splunk, use HEC endpoint URL",
            "webhook": "Provide any HTTP endpoint that accepts JSON payloads",
            "custom": "Contact support for custom SIEM integrations"
        }
    }

@router.delete("/disconnect")
async def disconnect_siem():
    """Disconnect current SIEM integration"""
    try:
        global current_siem_config
        
        if not current_siem_config:
            return {
                "status": "success",
                "message": "No SIEM integration was configured"
            }
        
        siem_type = current_siem_config.siem_type
        current_siem_config = None
        
        logger.info(f"✅ SIEM integration disconnected: {siem_type}")
        
        return {
            "status": "success",
            "message": f"{siem_type.title()} SIEM integration disconnected",
            "previous_siem": siem_type
        }
        
    except Exception as e:
        logger.error(f"❌ Error disconnecting SIEM: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disconnecting SIEM: {str(e)}"
        )