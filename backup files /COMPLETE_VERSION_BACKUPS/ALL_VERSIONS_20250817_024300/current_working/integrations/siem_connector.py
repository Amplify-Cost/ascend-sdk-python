# integrations/siem_connector.py - Enterprise SIEM Integration
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SIEMType(Enum):
    SPLUNK = "splunk"
    QRADAR = "qradar"
    SENTINEL = "sentinel"
    ELASTIC = "elastic"

@dataclass
class SIEMConfig:
    siem_type: SIEMType
    host: str
    port: int
    username: str
    password: str
    api_token: Optional[str] = None
    use_ssl: bool = True
    verify_ssl: bool = True
    index_name: str = "owai_security"

@dataclass
class SecurityEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    agent_id: str
    action_type: str
    risk_score: int
    status: str
    details: Dict[str, Any]
    compliance_frameworks: List[str]
    nist_control: Optional[str] = None
    mitre_tactic: Optional[str] = None

class SIEMConnector:
    """Base class for SIEM integrations"""
    
    def __init__(self, config: SIEMConfig):
        self.config = config
        self.session = None
        
    async def connect(self) -> bool:
        """Establish connection to SIEM"""
        raise NotImplementedError
        
    async def send_event(self, event: SecurityEvent) -> bool:
        """Send security event to SIEM"""
        raise NotImplementedError
        
    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Send multiple events in batch"""
        raise NotImplementedError
        
    async def query_events(self, query: str, time_range: int = 24) -> List[Dict]:
        """Query events from SIEM"""
        raise NotImplementedError

class SplunkConnector(SIEMConnector):
    """Enterprise Splunk SIEM Integration"""
    
    def __init__(self, config: SIEMConfig):
        super().__init__(config)
        self.base_url = f"{'https' if config.use_ssl else 'http'}://{config.host}:{config.port}"
        self.session_key = None
        
    async def connect(self) -> bool:
        """Authenticate with Splunk Enterprise"""
        try:
            auth_url = f"{self.base_url}/services/auth/login"
            auth_data = {
                'username': self.config.username,
                'password': self.config.password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    auth_url, 
                    data=auth_data,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        # Parse session key from XML response
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response_text)
                        self.session_key = root.find('.//sessionKey').text
                        logger.info("✅ Connected to Splunk Enterprise")
                        return True
                    else:
                        logger.error(f"❌ Splunk authentication failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Splunk connection error: {str(e)}")
            return False
    
    async def send_event(self, event: SecurityEvent) -> bool:
        """Send OW-AI security event to Splunk"""
        try:
            if not self.session_key:
                await self.connect()
            
            # Format event for Splunk
            splunk_event = {
                "time": event.timestamp.timestamp(),
                "source": "ow-ai",
                "sourcetype": "owai:security:event",
                "index": self.config.index_name,
                "event": {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "agent_id": event.agent_id,
                    "action_type": event.action_type,
                    "risk_score": event.risk_score,
                    "status": event.status,
                    "nist_control": event.nist_control,
                    "mitre_tactic": event.mitre_tactic,
                    "compliance_frameworks": event.compliance_frameworks,
                    "details": event.details,
                    "platform": "ow-ai-enterprise"
                }
            }
            
            url = f"{self.base_url}/services/collectors/event"
            headers = {
                'Authorization': f'Splunk {self.session_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=splunk_event,
                    headers=headers,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Event {event.event_id} sent to Splunk")
                        return True
                    else:
                        logger.error(f"❌ Splunk event send failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending event to Splunk: {str(e)}")
            return False
    
    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Send multiple events to Splunk in batch"""
        try:
            if not self.session_key:
                await self.connect()
            
            # Prepare batch payload
            batch_events = []
            for event in events:
                splunk_event = {
                    "time": event.timestamp.timestamp(),
                    "source": "ow-ai",
                    "sourcetype": "owai:security:event",
                    "index": self.config.index_name,
                    "event": {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "severity": event.severity,
                        "agent_id": event.agent_id,
                        "action_type": event.action_type,
                        "risk_score": event.risk_score,
                        "status": event.status,
                        "nist_control": event.nist_control,
                        "mitre_tactic": event.mitre_tactic,
                        "compliance_frameworks": event.compliance_frameworks,
                        "details": event.details
                    }
                }
                batch_events.append(json.dumps(splunk_event))
            
            # Send batch
            url = f"{self.base_url}/services/collectors/event"
            headers = {
                'Authorization': f'Splunk {self.session_key}',
                'Content-Type': 'application/json'
            }
            
            batch_payload = '\n'.join(batch_events)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=batch_payload,
                    headers=headers,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Batch of {len(events)} events sent to Splunk")
                        return {
                            "status": "success",
                            "events_sent": len(events),
                            "message": "Events successfully sent to Splunk"
                        }
                    else:
                        logger.error(f"❌ Splunk batch send failed: {response.status}")
                        return {
                            "status": "error",
                            "events_sent": 0,
                            "message": f"Failed to send events: {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"❌ Error in batch send to Splunk: {str(e)}")
            return {
                "status": "error",
                "events_sent": 0,
                "message": str(e)
            }
    
    async def query_events(self, query: str, time_range: int = 24) -> List[Dict]:
        """Query OW-AI events from Splunk"""
        try:
            if not self.session_key:
                await self.connect()
            
            # Construct Splunk search query
            search_query = f'search index={self.config.index_name} source="ow-ai" earliest=-{time_range}h {query}'
            
            # Start search job
            search_url = f"{self.base_url}/services/search/jobs"
            headers = {
                'Authorization': f'Splunk {self.session_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            search_data = {'search': search_query}
            
            async with aiohttp.ClientSession() as session:
                # Submit search
                async with session.post(
                    search_url,
                    data=search_data,
                    headers=headers,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status == 201:
                        response_text = await response.text()
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response_text)
                        job_id = root.find('.//sid').text
                        
                        # Wait for job completion and get results
                        await asyncio.sleep(2)  # Wait for search to complete
                        
                        results_url = f"{self.base_url}/services/search/jobs/{job_id}/results"
                        async with session.get(
                            results_url,
                            headers=headers,
                            ssl=self.config.verify_ssl
                        ) as results_response:
                            if results_response.status == 200:
                                results_text = await results_response.text()
                                # Parse XML results and convert to JSON
                                results_root = ET.fromstring(results_text)
                                events = []
                                for result in results_root.findall('.//result'):
                                    event_data = {}
                                    for field in result.findall('.//field'):
                                        field_name = field.get('k')
                                        field_value = field.find('.//value').text if field.find('.//value') is not None else ""
                                        event_data[field_name] = field_value
                                    events.append(event_data)
                                
                                logger.info(f"✅ Retrieved {len(events)} events from Splunk")
                                return events
                    
                    logger.error(f"❌ Splunk query failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error querying Splunk: {str(e)}")
            return []

class QRadarConnector(SIEMConnector):
    """IBM QRadar SIEM Integration"""
    
    def __init__(self, config: SIEMConfig):
        super().__init__(config)
        self.base_url = f"{'https' if config.use_ssl else 'http'}://{config.host}/api"
        
    async def connect(self) -> bool:
        """Test QRadar API connection"""
        try:
            url = f"{self.base_url}/system/about"
            headers = {
                'SEC': self.config.api_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Connected to IBM QRadar")
                        return True
                    else:
                        logger.error(f"❌ QRadar connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ QRadar connection error: {str(e)}")
            return False
    
    async def send_event(self, event: SecurityEvent) -> bool:
        """Send OW-AI event to QRadar"""
        try:
            # QRadar uses custom event format
            qradar_event = {
                "magnitude": self._risk_to_magnitude(event.risk_score),
                "event_name": f"OW-AI: {event.event_type}",
                "description": f"Agent {event.agent_id} performed {event.action_type}",
                "severity": self._severity_to_qradar(event.severity),
                "source_ip": "10.0.0.1",  # OW-AI system IP
                "custom_properties": {
                    "ow_ai_event_id": event.event_id,
                    "ow_ai_agent_id": event.agent_id,
                    "ow_ai_risk_score": event.risk_score,
                    "ow_ai_nist_control": event.nist_control or "",
                    "ow_ai_mitre_tactic": event.mitre_tactic or "",
                    "ow_ai_status": event.status
                }
            }
            
            url = f"{self.base_url}/siem/offenses"
            headers = {
                'SEC': self.config.api_token,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=qradar_event,
                    headers=headers,
                    ssl=self.config.verify_ssl
                ) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Event {event.event_id} sent to QRadar")
                        return True
                    else:
                        logger.error(f"❌ QRadar event send failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending event to QRadar: {str(e)}")
            return False
    
    def _risk_to_magnitude(self, risk_score: int) -> int:
        """Convert OW-AI risk score to QRadar magnitude (1-10)"""
        return min(10, max(1, risk_score // 10))
    
    def _severity_to_qradar(self, severity: str) -> int:
        """Convert severity to QRadar severity levels"""
        severity_map = {
            "low": 3,
            "medium": 5,
            "high": 7,
            "critical": 9
        }
        return severity_map.get(severity.lower(), 5)

class SIEMManager:
    """Enterprise SIEM Integration Manager"""
    
    def __init__(self):
        self.connectors: Dict[str, SIEMConnector] = {}
        self.active_connector: Optional[SIEMConnector] = None
        
    def add_connector(self, name: str, connector: SIEMConnector):
        """Add SIEM connector"""
        self.connectors[name] = connector
        if not self.active_connector:
            self.active_connector = connector
    
    async def send_authorization_event(
        self, 
        action_id: int,
        agent_id: str,
        action_type: str,
        decision: str,
        risk_score: int,
        user_email: str,
        nist_control: str = None,
        mitre_tactic: str = None
    ) -> bool:
        """Send authorization decision to SIEM"""
        if not self.active_connector:
            logger.warning("⚠️ No SIEM connector configured")
            return False
        
        event = SecurityEvent(
            event_id=f"owai-auth-{action_id}",
            timestamp=datetime.utcnow(),
            event_type="agent_authorization",
            severity="high" if risk_score >= 70 else "medium",
            source="ow-ai-authorization",
            agent_id=agent_id,
            action_type=action_type,
            risk_score=risk_score,
            status=decision,
            details={
                "authorization_decision": decision,
                "approver": user_email,
                "risk_assessment": {
                    "score": risk_score,
                    "factors": ["automated_risk_assessment"]
                }
            },
            compliance_frameworks=["NIST", "SOC2"],
            nist_control=nist_control,
            mitre_tactic=mitre_tactic
        )
        
        return await self.active_connector.send_event(event)
    
    async def send_agent_action_event(
        self,
        action_id: int,
        agent_id: str,
        action_type: str,
        risk_score: int,
        status: str,
        nist_control: str = None,
        mitre_tactic: str = None
    ) -> bool:
        """Send agent action to SIEM"""
        if not self.active_connector:
            logger.warning("⚠️ No SIEM connector configured")
            return False
        
        event = SecurityEvent(
            event_id=f"owai-action-{action_id}",
            timestamp=datetime.utcnow(),
            event_type="agent_action",
            severity="critical" if risk_score >= 80 else "high" if risk_score >= 60 else "medium",
            source="ow-ai-monitoring",
            agent_id=agent_id,
            action_type=action_type,
            risk_score=risk_score,
            status=status,
            details={
                "action_details": {
                    "type": action_type,
                    "risk_score": risk_score,
                    "status": status
                }
            },
            compliance_frameworks=["NIST", "MITRE"],
            nist_control=nist_control,
            mitre_tactic=mitre_tactic
        )
        
        return await self.active_connector.send_event(event)
    
    async def get_threat_intelligence(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """Query SIEM for threat intelligence about specific agent"""
        if not self.active_connector:
            return {"status": "no_siem_configured"}
        
        query = f'agent_id="{agent_id}" severity IN ("high", "critical")'
        events = await self.active_connector.query_events(query, hours)
        
        # Analyze events for threat patterns
        threat_analysis = {
            "agent_id": agent_id,
            "time_period_hours": hours,
            "total_events": len(events),
            "high_risk_events": len([e for e in events if int(e.get("risk_score", 0)) >= 70]),
            "threat_indicators": [],
            "recommendations": []
        }
        
        # Add threat indicators based on patterns
        if threat_analysis["high_risk_events"] > 5:
            threat_analysis["threat_indicators"].append("High frequency of risky actions")
            threat_analysis["recommendations"].append("Consider additional oversight for this agent")
        
        return threat_analysis

# Global SIEM manager instance
siem_manager = SIEMManager()