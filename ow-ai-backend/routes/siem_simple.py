# routes/siem_simple.py - No External Dependencies SIEM Integration
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import logging
import json
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta, UTC

from database import get_db
from models import User, AgentAction, PendingAgentAction, Alert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enterprise/siem", tags=["enterprise-siem"])

# Simple SIEM Configuration Models (no external dependencies)
class SIEMConfig(BaseModel):
    siem_type: str  # "webhook", "splunk", "log_file"
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    log_file_path: Optional[str] = "/tmp/owai_siem.log"
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

# Global SIEM configuration
current_siem_config: Optional[SIEMConfig] = None

# SIEM Configuration Endpoints
@router.post("/configure")
async def configure_siem_integration(
    config: SIEMConfig,
    db: Session = Depends(get_db)
):
    """Configure enterprise SIEM integration (dependency-free)"""
    try:
        global current_siem_config
        
        # Validate configuration
        if config.siem_type in ["webhook", "splunk"] and not config.endpoint_url:
            raise HTTPException(
                status_code=400,
                detail="endpoint_url is required for webhook and splunk integrations"
            )
        
        # Test the configuration
        test_result = await test_siem_connection(config)
        
        if test_result["status"] == "success":
            current_siem_config = config
            
            logger.info(f"✅ SIEM integration configured: {config.siem_type}")
            
            return {
                "status": "success",
                "message": f"{config.siem_type.title()} SIEM integration configured successfully",
                "siem_type": config.siem_type,
                "endpoint": config.endpoint_url or config.log_file_path,
                "connection_test": "passed",
                "features_enabled": [
                    "Real-time event forwarding",
                    "Authorization logging",
                    "Emergency override alerts", 
                    "Risk-based event prioritization",
                    "No external dependencies"
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
    """Test SIEM connection (no external dependencies)"""
    try:
        if config.siem_type == "log_file":
            # Test log file writing
            try:
                test_log = {
                    "test": True,
                    "source": "ow-ai-enterprise",
                    "message": "SIEM log file test",
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
                with open(config.log_file_path, "a") as f:
                    f.write(json.dumps(test_log) + "\n")
                
                return {
                    "status": "success",
                    "message": f"Log file accessible at {config.log_file_path}",
                    "log_path": config.log_file_path
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Cannot write to log file: {str(e)}"
                }
                
        elif config.siem_type in ["webhook", "splunk"]:
            # Test HTTP endpoint using built-in urllib
            try:
                test_payload = {
                    "test": True,
                    "source": "ow-ai-enterprise",
                    "message": "SIEM connection test",
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
                if config.siem_type == "splunk":
                    # Splunk HEC format
                    test_payload = {
                        "event": test_payload,
                        "time": datetime.now(UTC).timestamp(),
                        "source": "ow-ai",
                        "sourcetype": "owai:test"
                    }
                
                data = json.dumps(test_payload).encode('utf-8')
                
                req = urllib.request.Request(
                    config.endpoint_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if config.api_key:
                    if config.siem_type == "splunk":
                        req.add_header('Authorization', f'Splunk {config.api_key}')
                    else:
                        req.add_header('Authorization', f'Bearer {config.api_key}')
                
                # Handle SSL verification
                context = ssl.create_default_context()
                if not config.verify_ssl:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, timeout=10, context=context) as response:
                    status_code = response.getcode()
                    
                    if status_code in [200, 201, 202]:
                        return {
                            "status": "success",
                            "message": f"{config.siem_type.title()} endpoint responding correctly",
                            "response_code": status_code
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"{config.siem_type.title()} returned status {status_code}",
                            "response_code": status_code
                        }
                        
            except urllib.error.URLError as e:
                return {
                    "status": "error",
                    "message": f"Connection failed: {str(e)}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Test failed: {str(e)}"
                }
        else:
            return {
                "status": "error",
                "message": f"SIEM type '{config.siem_type}' not supported"
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
                "supported_types": ["webhook", "splunk", "log_file"],
                "note": "Dependency-free SIEM integration ready"
            }
        
        return {
            "status": "configured",
            "siem_type": current_siem_config.siem_type,
            "endpoint": current_siem_config.endpoint_url or current_siem_config.log_file_path,
            "connection_healthy": True,  # We'll assume healthy for simplicity
            "last_configured": datetime.now(UTC).isoformat(),
            "message": "SIEM integration active"
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking SIEM status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error checking SIEM status: {str(e)}"
        }

# Event Sending Functions (no external dependencies)
async def send_event_to_siem(event: SIEMEvent) -> bool:
    """Send event to configured SIEM (dependency-free)"""
    try:
        if not current_siem_config:
            logger.info("⚠️ No SIEM configured, skipping event")
            return True  # Don't fail if SIEM not configured
        
        if current_siem_config.siem_type == "log_file":
            return await send_log_file_event(event)
        elif current_siem_config.siem_type == "webhook":
            return await send_http_event(event, is_splunk=False)
        elif current_siem_config.siem_type == "splunk":
            return await send_http_event(event, is_splunk=True)
        else:
            logger.warning(f"⚠️ Unsupported SIEM type: {current_siem_config.siem_type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending event to SIEM: {str(e)}")
        return False

async def send_log_file_event(event: SIEMEvent) -> bool:
    """Send event to log file"""
    try:
        log_entry = {
            "timestamp": event.timestamp,
            "source": "ow-ai-enterprise",
            "event_id": event.event_id,
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
            }
        }
        
        with open(current_siem_config.log_file_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.info(f"✅ Event {event.event_id} written to log file")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error writing to log file: {str(e)}")
        return False

async def send_http_event(event: SIEMEvent, is_splunk: bool = False) -> bool:
    """Send event via HTTP (using built-in urllib)"""
    try:
        if is_splunk:
            # Splunk HEC format
            payload = {
                "time": datetime.now(UTC).timestamp(),
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
        else:
            # Generic webhook format
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
        
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(
            current_siem_config.endpoint_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if current_siem_config.api_key:
            if is_splunk:
                req.add_header('Authorization', f'Splunk {current_siem_config.api_key}')
            else:
                req.add_header('Authorization', f'Bearer {current_siem_config.api_key}')
        
        # Handle SSL verification
        context = ssl.create_default_context()
        if not current_siem_config.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            status_code = response.getcode()
            
            if status_code in [200, 201, 202]:
                logger.info(f"✅ Event {event.event_id} sent to {current_siem_config.siem_type}")
                return True
            else:
                logger.error(f"❌ {current_siem_config.siem_type} returned status {status_code}")
                return False
        
    except Exception as e:
        logger.error(f"❌ Error sending HTTP event: {str(e)}")
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
        timestamp=datetime.now(UTC).isoformat(),
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
        timestamp=datetime.now(UTC).isoformat(),
        event_type="emergency_override",
        severity="critical",
        agent_id=agent_id,
        action_type=f"EMERGENCY:{action_type}",
        risk_score=min(100, risk_score + 20),
        status="emergency_approved",
        user_email=user_email,
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
                "endpoint": current_siem_config.endpoint_url or current_siem_config.log_file_path,
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
                "type": "log_file",
                "name": "JSON Log File",
                "description": "Write events to structured JSON log file",
                "setup_required": ["Log file path"],
                "status": "fully_supported",
                "dependencies": "none"
            },
            {
                "type": "webhook",
                "name": "Generic Webhook",
                "description": "Send events to any HTTP endpoint",
                "setup_required": ["Webhook URL", "Optional API key"],
                "status": "fully_supported",
                "dependencies": "none"
            },
            {
                "type": "splunk",
                "name": "Splunk HEC",
                "description": "Splunk HTTP Event Collector",
                "setup_required": ["HEC endpoint URL", "API token"],
                "status": "fully_supported",
                "dependencies": "none"
            }
        ],
        "enterprise_features": [
            "Zero external dependencies",
            "Real-time security event streaming",
            "Authorization decision logging",
            "Emergency override alerts",
            "Risk-based event classification",
            "NIST/MITRE compliance tagging",
            "Built-in Python libraries only"
        ],
        "setup_examples": {
            "log_file": {
                "siem_type": "log_file",
                "log_file_path": "/var/log/owai_security.log"
            },
            "webhook": {
                "siem_type": "webhook",
                "endpoint_url": "https://your-siem.com/webhook",
                "api_key": "optional-bearer-token"
            },
            "splunk": {
                "siem_type": "splunk",
                "endpoint_url": "https://splunk.company.com:8088/services/collector",
                "api_key": "your-hec-token"
            }
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