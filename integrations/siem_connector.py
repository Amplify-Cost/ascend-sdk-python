"""
SEC-052: Enterprise SIEM Connector Module
==========================================

Banking-level SIEM integrations with support for:
- Splunk Enterprise (HEC)
- IBM QRadar (REST API)
- Microsoft Sentinel (Azure Log Analytics)
- Elastic/ELK Stack (REST API)

Compliance: SOC 2 CC6.6, PCI-DSS 10.2, NIST SI-4, HIPAA 164.312
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import List, Dict, Any, Optional
import json
import logging
import hashlib
import hmac
import base64
import urllib.request
import urllib.parse
import urllib.error
import ssl

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class SIEMType(str, Enum):
    """Supported SIEM platforms."""
    SPLUNK = "splunk"
    QRADAR = "qradar"
    SENTINEL = "sentinel"
    ELASTIC = "elastic"


@dataclass
class SIEMConfig:
    """SIEM connection configuration."""
    siem_type: SIEMType
    host: str
    port: int
    username: str = ""
    password: str = ""
    api_token: Optional[str] = None
    use_ssl: bool = True
    verify_ssl: bool = True
    index_name: str = "owai_security"
    # Azure Sentinel specific
    workspace_id: Optional[str] = None
    shared_key: Optional[str] = None
    log_type: str = "OWAISecurityEvents"
    # Elastic specific
    cloud_id: Optional[str] = None


@dataclass
class SecurityEvent:
    """
    Standardized security event for SIEM ingestion.

    Compliance: SOC 2 CC7.1, NIST AU-2, PCI-DSS 10.2
    """
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    agent_id: str
    action_type: str
    risk_score: int
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_frameworks: List[str] = field(default_factory=list)
    nist_control: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    organization_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "risk_score": self.risk_score,
            "status": self.status,
            "details": self.details,
            "compliance_frameworks": self.compliance_frameworks,
            "nist_control": self.nist_control,
            "mitre_tactic": self.mitre_tactic,
            "mitre_technique": self.mitre_technique,
            "organization_id": self.organization_id
        }


# ============================================================================
# Abstract Base Class
# ============================================================================

class SIEMConnector(ABC):
    """
    Abstract base class for SIEM connectors.

    All connectors must implement:
    - connect(): Establish connection to SIEM
    - send_event(): Send single event
    - batch_send_events(): Send multiple events
    - query_events(): Query events from SIEM
    """

    def __init__(self, config: SIEMConfig):
        self.config = config
        self._connected = False
        self._session_key = None

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to SIEM. Returns True on success."""
        pass

    @abstractmethod
    async def send_event(self, event: SecurityEvent) -> bool:
        """Send a single security event. Returns True on success."""
        pass

    @abstractmethod
    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Send multiple events in batch. Returns result summary."""
        pass

    @abstractmethod
    async def query_events(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Query events from SIEM. Returns list of matching events."""
        pass

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context based on configuration."""
        context = ssl.create_default_context()
        if not self.config.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context


# ============================================================================
# Splunk Connector
# ============================================================================

class SplunkConnector(SIEMConnector):
    """
    Splunk Enterprise connector using HTTP Event Collector (HEC).

    Compliance: SOC 2 CC6.6, PCI-DSS 10.2
    """

    async def connect(self) -> bool:
        """Authenticate with Splunk and obtain session key."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            auth_url = f"{protocol}://{self.config.host}:{self.config.port}/services/auth/login"

            data = urllib.parse.urlencode({
                "username": self.config.username,
                "password": self.config.password
            }).encode('utf-8')

            request = urllib.request.Request(auth_url, data=data, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                response_text = response.read().decode('utf-8')
                # Parse XML response for session key
                if '<sessionKey>' in response_text:
                    start = response_text.find('<sessionKey>') + len('<sessionKey>')
                    end = response_text.find('</sessionKey>')
                    self._session_key = response_text[start:end]
                    self._connected = True
                    logger.info(f"SEC-052: Splunk connection established to {self.config.host}")
                    return True

            return False

        except Exception as e:
            logger.error(f"SEC-052: Splunk connection failed: {e}")
            self._connected = False
            return False

    async def send_event(self, event: SecurityEvent) -> bool:
        """Send event via HEC."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            hec_url = f"{protocol}://{self.config.host}:8088/services/collector/event"

            payload = {
                "event": event.to_dict(),
                "sourcetype": "owai:security",
                "index": self.config.index_name,
                "time": event.timestamp.timestamp() if event.timestamp else datetime.now(UTC).timestamp()
            }

            headers = {
                "Authorization": f"Splunk {self.config.api_token or self._session_key}",
                "Content-Type": "application/json"
            }

            data = json.dumps(payload).encode('utf-8')
            request = urllib.request.Request(hec_url, data=data, headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                success = result.get("text") == "Success"
                if success:
                    logger.info(f"SEC-052: Event {event.event_id} sent to Splunk")
                return success

        except Exception as e:
            logger.error(f"SEC-052: Splunk send_event failed: {e}")
            return False

    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Send multiple events in batch."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            hec_url = f"{protocol}://{self.config.host}:8088/services/collector/event"

            # Build batch payload (newline-delimited JSON)
            batch_payload = ""
            for event in events:
                payload = {
                    "event": event.to_dict(),
                    "sourcetype": "owai:security",
                    "index": self.config.index_name,
                    "time": event.timestamp.timestamp() if event.timestamp else datetime.now(UTC).timestamp()
                }
                batch_payload += json.dumps(payload) + "\n"

            headers = {
                "Authorization": f"Splunk {self.config.api_token or self._session_key}",
                "Content-Type": "application/json"
            }

            data = batch_payload.encode('utf-8')
            request = urllib.request.Request(hec_url, data=data, headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"SEC-052: Batch sent {len(events)} events to Splunk")
                return {
                    "success": True,
                    "events_sent": len(events),
                    "splunk_response": result
                }

        except Exception as e:
            logger.error(f"SEC-052: Splunk batch_send failed: {e}")
            return {"success": False, "error": str(e), "events_sent": 0}

    async def query_events(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Query events using SPL."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            search_url = f"{protocol}://{self.config.host}:{self.config.port}/services/search/jobs"

            # Create search job
            spl_query = f'search index={self.config.index_name} earliest=-{hours}h {query}'

            data = urllib.parse.urlencode({
                "search": spl_query,
                "output_mode": "json",
                "exec_mode": "oneshot"
            }).encode('utf-8')

            headers = {
                "Authorization": f"Splunk {self._session_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            request = urllib.request.Request(search_url, data=data, headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                events = result.get("results", [])
                logger.info(f"SEC-052: Splunk query returned {len(events)} events")
                return events

        except Exception as e:
            logger.error(f"SEC-052: Splunk query failed: {e}")
            return []


# ============================================================================
# QRadar Connector
# ============================================================================

class QRadarConnector(SIEMConnector):
    """
    IBM QRadar connector using REST API.

    Compliance: SOC 2 CC6.6, PCI-DSS 10.2
    """

    async def connect(self) -> bool:
        """Verify QRadar API connectivity."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            test_url = f"{protocol}://{self.config.host}:{self.config.port}/api/system/servers"

            headers = {
                "SEC": self.config.api_token,
                "Accept": "application/json",
                "Version": "14.0"
            }

            request = urllib.request.Request(test_url, headers=headers, method='GET')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                if response.status == 200:
                    self._connected = True
                    logger.info(f"SEC-052: QRadar connection established to {self.config.host}")
                    return True

            return False

        except Exception as e:
            logger.error(f"SEC-052: QRadar connection failed: {e}")
            self._connected = False
            return False

    async def send_event(self, event: SecurityEvent) -> bool:
        """Create offense in QRadar."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            offense_url = f"{protocol}://{self.config.host}:{self.config.port}/api/siem/offenses"

            # Map risk score to QRadar magnitude (1-10)
            magnitude = min(10, max(1, event.risk_score // 10))

            # Map severity to QRadar severity
            severity_map = {"low": 3, "medium": 5, "high": 7, "critical": 9}
            qradar_severity = severity_map.get(event.severity.lower(), 5)

            payload = {
                "description": f"OW-AI Security Event: {event.event_type}",
                "severity": qradar_severity,
                "magnitude": magnitude,
                "event_count": 1,
                "offense_type": 0,
                "offense_source": event.agent_id,
                "custom_properties": {
                    "owai_event_id": event.event_id,
                    "owai_action_type": event.action_type,
                    "owai_risk_score": event.risk_score,
                    "owai_nist_control": event.nist_control or "",
                    "owai_mitre_tactic": event.mitre_tactic or ""
                }
            }

            headers = {
                "SEC": self.config.api_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "14.0"
            }

            data = json.dumps(payload).encode('utf-8')
            request = urllib.request.Request(offense_url, data=data, headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                if response.status in [200, 201]:
                    logger.info(f"SEC-052: Event {event.event_id} sent to QRadar")
                    return True

            return False

        except Exception as e:
            logger.error(f"SEC-052: QRadar send_event failed: {e}")
            return False

    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """SEC-052: Send multiple events to QRadar."""
        results = {"success": True, "events_sent": 0, "errors": []}

        for event in events:
            try:
                success = await self.send_event(event)
                if success:
                    results["events_sent"] += 1
                else:
                    results["errors"].append({"event_id": event.event_id, "error": "Send failed"})
            except Exception as e:
                results["errors"].append({"event_id": event.event_id, "error": str(e)})

        results["success"] = len(results["errors"]) == 0
        logger.info(f"SEC-052: QRadar batch sent {results['events_sent']}/{len(events)} events")
        return results

    async def query_events(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """SEC-052: Query QRadar using AQL."""
        try:
            protocol = "https" if self.config.use_ssl else "http"
            search_url = f"{protocol}://{self.config.host}:{self.config.port}/api/ariel/searches"

            # Build AQL query
            aql_query = f"SELECT * FROM events WHERE LOGSOURCENAME ILIKE '%owai%' LAST {hours} HOURS"
            if query:
                aql_query += f" AND ({query})"

            # Create search
            headers = {
                "SEC": self.config.api_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Version": "14.0"
            }

            params = urllib.parse.urlencode({"query_expression": aql_query})
            request = urllib.request.Request(f"{search_url}?{params}", headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                search_id = result.get("search_id")

                if not search_id:
                    return []

                # Poll for results
                results_url = f"{search_url}/{search_id}/results"
                request = urllib.request.Request(results_url, headers=headers, method='GET')

                with urllib.request.urlopen(request, context=context, timeout=60) as response:
                    events = json.loads(response.read().decode('utf-8'))
                    logger.info(f"SEC-052: QRadar query returned {len(events.get('events', []))} events")
                    return events.get("events", [])

        except Exception as e:
            logger.error(f"SEC-052: QRadar query failed: {e}")
            return []


# ============================================================================
# Microsoft Sentinel Connector (NEW - SEC-052)
# ============================================================================

class SentinelConnector(SIEMConnector):
    """
    Microsoft Sentinel connector using Azure Log Analytics Data Collector API.

    SEC-052: Enterprise Azure integration for Microsoft customers.
    Compliance: SOC 2 CC6.6, PCI-DSS 10.2, Azure Security Benchmark

    Required config:
    - workspace_id: Azure Log Analytics Workspace ID
    - shared_key: Primary or Secondary key from Log Analytics
    - log_type: Custom log table name (default: OWAISecurityEvents)
    """

    def _build_signature(self, date: str, content_length: int, method: str, content_type: str, resource: str) -> str:
        """Build Azure Log Analytics authorization signature (HMAC-SHA256)."""
        x_headers = f"x-ms-date:{date}"
        string_to_hash = f"{method}\n{content_length}\n{content_type}\n{x_headers}\n{resource}"
        bytes_to_hash = string_to_hash.encode('utf-8')
        decoded_key = base64.b64decode(self.config.shared_key)
        encoded_hash = base64.b64encode(
            hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
        ).decode('utf-8')
        return f"SharedKey {self.config.workspace_id}:{encoded_hash}"

    async def connect(self) -> bool:
        """Verify Sentinel connectivity by checking workspace."""
        try:
            if not self.config.workspace_id or not self.config.shared_key:
                logger.error("SEC-052: Sentinel requires workspace_id and shared_key")
                return False

            # Test with a minimal payload
            test_event = SecurityEvent(
                event_id="sentinel-test",
                timestamp=datetime.now(UTC),
                event_type="connection_test",
                severity="low",
                source="owai-sentinel-connector",
                agent_id="test",
                action_type="connection_test",
                risk_score=0,
                status="test"
            )

            # Try to send test event
            success = await self.send_event(test_event)
            if success:
                self._connected = True
                logger.info(f"SEC-052: Sentinel connection established to workspace {self.config.workspace_id[:8]}...")
            return success

        except Exception as e:
            logger.error(f"SEC-052: Sentinel connection failed: {e}")
            self._connected = False
            return False

    async def send_event(self, event: SecurityEvent) -> bool:
        """Send event to Azure Log Analytics."""
        try:
            # Azure Log Analytics Data Collector API
            uri = f"https://{self.config.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

            # Prepare payload
            payload = [event.to_dict()]
            body = json.dumps(payload)
            content_length = len(body)

            # Build date and signature
            rfc1123date = datetime.now(UTC).strftime('%a, %d %b %Y %H:%M:%S GMT')
            signature = self._build_signature(
                rfc1123date, content_length, "POST", "application/json", "/api/logs"
            )

            headers = {
                "Content-Type": "application/json",
                "Authorization": signature,
                "Log-Type": self.config.log_type,
                "x-ms-date": rfc1123date,
                "time-generated-field": "timestamp"
            }

            request = urllib.request.Request(uri, data=body.encode('utf-8'), headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                if response.status in [200, 202]:
                    logger.info(f"SEC-052: Event {event.event_id} sent to Sentinel")
                    return True

            return False

        except urllib.error.HTTPError as e:
            logger.error(f"SEC-052: Sentinel send_event HTTP error: {e.code} - {e.read().decode('utf-8')}")
            return False
        except Exception as e:
            logger.error(f"SEC-052: Sentinel send_event failed: {e}")
            return False

    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Send multiple events to Sentinel in batch."""
        try:
            # Azure Log Analytics supports batch payloads up to 30MB
            uri = f"https://{self.config.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

            # Prepare batch payload
            payload = [event.to_dict() for event in events]
            body = json.dumps(payload)
            content_length = len(body)

            # Build date and signature
            rfc1123date = datetime.now(UTC).strftime('%a, %d %b %Y %H:%M:%S GMT')
            signature = self._build_signature(
                rfc1123date, content_length, "POST", "application/json", "/api/logs"
            )

            headers = {
                "Content-Type": "application/json",
                "Authorization": signature,
                "Log-Type": self.config.log_type,
                "x-ms-date": rfc1123date,
                "time-generated-field": "timestamp"
            }

            request = urllib.request.Request(uri, data=body.encode('utf-8'), headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                if response.status in [200, 202]:
                    logger.info(f"SEC-052: Batch sent {len(events)} events to Sentinel")
                    return {
                        "success": True,
                        "events_sent": len(events),
                        "sentinel_response": {"status": response.status}
                    }

            return {"success": False, "events_sent": 0, "error": "Unexpected response"}

        except Exception as e:
            logger.error(f"SEC-052: Sentinel batch_send failed: {e}")
            return {"success": False, "error": str(e), "events_sent": 0}

    async def query_events(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Query events from Sentinel using Log Analytics Query API.

        Note: Requires additional Azure AD authentication for query API.
        For full query support, use Azure SDK or configure service principal.
        """
        try:
            # Log Analytics Query API requires Azure AD token
            # This is a simplified version - production would use azure-identity
            logger.warning("SEC-052: Sentinel query requires Azure AD authentication. Use Azure Portal or SDK for queries.")

            # Return empty for now - full implementation would require:
            # 1. Azure AD service principal
            # 2. OAuth2 token acquisition
            # 3. Query API call to api.loganalytics.io
            return []

        except Exception as e:
            logger.error(f"SEC-052: Sentinel query failed: {e}")
            return []


# ============================================================================
# Elastic Connector (NEW - SEC-052)
# ============================================================================

class ElasticConnector(SIEMConnector):
    """
    Elastic/ELK Stack connector using REST API.

    SEC-052: Enterprise Elasticsearch integration for ELK customers.
    Compliance: SOC 2 CC6.6, PCI-DSS 10.2, Elastic Security

    Supports:
    - Elastic Cloud (using cloud_id)
    - Self-hosted Elasticsearch (using host/port)
    - API key authentication
    - Basic authentication
    """

    async def connect(self) -> bool:
        """Verify Elasticsearch connectivity."""
        try:
            protocol = "https" if self.config.use_ssl else "http"

            # Handle Elastic Cloud vs self-hosted
            if self.config.cloud_id:
                # Parse cloud_id to get endpoint
                base_url = self._parse_cloud_id()
            else:
                base_url = f"{protocol}://{self.config.host}:{self.config.port}"

            test_url = f"{base_url}/_cluster/health"

            headers = self._build_auth_headers()
            headers["Accept"] = "application/json"

            request = urllib.request.Request(test_url, headers=headers, method='GET')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    cluster_status = result.get("status", "unknown")
                    self._connected = True
                    logger.info(f"SEC-052: Elastic connection established, cluster status: {cluster_status}")
                    return True

            return False

        except Exception as e:
            logger.error(f"SEC-052: Elastic connection failed: {e}")
            self._connected = False
            return False

    def _parse_cloud_id(self) -> str:
        """Parse Elastic Cloud ID to get endpoint URL."""
        try:
            # Cloud ID format: name:base64(host$es_uuid$kibana_uuid)
            parts = self.config.cloud_id.split(":")
            if len(parts) == 2:
                decoded = base64.b64decode(parts[1]).decode('utf-8')
                host_parts = decoded.split("$")
                if host_parts:
                    return f"https://{host_parts[1]}.{host_parts[0]}"
        except Exception as e:
            logger.error(f"SEC-052: Failed to parse cloud_id: {e}")

        # Fallback to standard host
        protocol = "https" if self.config.use_ssl else "http"
        return f"{protocol}://{self.config.host}:{self.config.port}"

    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers."""
        headers = {}

        if self.config.api_token:
            # API key authentication
            headers["Authorization"] = f"ApiKey {self.config.api_token}"
        elif self.config.username and self.config.password:
            # Basic authentication
            credentials = base64.b64encode(
                f"{self.config.username}:{self.config.password}".encode('utf-8')
            ).decode('utf-8')
            headers["Authorization"] = f"Basic {credentials}"

        return headers

    def _get_base_url(self) -> str:
        """Get base URL for API calls."""
        if self.config.cloud_id:
            return self._parse_cloud_id()
        protocol = "https" if self.config.use_ssl else "http"
        return f"{protocol}://{self.config.host}:{self.config.port}"

    async def send_event(self, event: SecurityEvent) -> bool:
        """Index event to Elasticsearch."""
        try:
            base_url = self._get_base_url()

            # Use date-based index for ILM compatibility
            date_suffix = event.timestamp.strftime("%Y.%m.%d") if event.timestamp else datetime.now(UTC).strftime("%Y.%m.%d")
            index_url = f"{base_url}/{self.config.index_name}-{date_suffix}/_doc/{event.event_id}"

            payload = event.to_dict()
            payload["@timestamp"] = event.timestamp.isoformat() if event.timestamp else datetime.now(UTC).isoformat()

            headers = self._build_auth_headers()
            headers["Content-Type"] = "application/json"

            data = json.dumps(payload).encode('utf-8')
            request = urllib.request.Request(index_url, data=data, headers=headers, method='PUT')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=30) as response:
                if response.status in [200, 201]:
                    result = json.loads(response.read().decode('utf-8'))
                    logger.info(f"SEC-052: Event {event.event_id} indexed to Elastic")
                    return result.get("result") in ["created", "updated"]

            return False

        except Exception as e:
            logger.error(f"SEC-052: Elastic send_event failed: {e}")
            return False

    async def batch_send_events(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Bulk index events to Elasticsearch."""
        try:
            base_url = self._get_base_url()
            bulk_url = f"{base_url}/_bulk"

            # Build NDJSON bulk payload
            bulk_payload = ""
            for event in events:
                date_suffix = event.timestamp.strftime("%Y.%m.%d") if event.timestamp else datetime.now(UTC).strftime("%Y.%m.%d")
                index_name = f"{self.config.index_name}-{date_suffix}"

                # Action line
                action = {"index": {"_index": index_name, "_id": event.event_id}}
                bulk_payload += json.dumps(action) + "\n"

                # Document line
                doc = event.to_dict()
                doc["@timestamp"] = event.timestamp.isoformat() if event.timestamp else datetime.now(UTC).isoformat()
                bulk_payload += json.dumps(doc) + "\n"

            headers = self._build_auth_headers()
            headers["Content-Type"] = "application/x-ndjson"

            request = urllib.request.Request(bulk_url, data=bulk_payload.encode('utf-8'), headers=headers, method='POST')
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))

                errors = result.get("errors", False)
                items = result.get("items", [])
                success_count = sum(1 for item in items if item.get("index", {}).get("status") in [200, 201])

                logger.info(f"SEC-052: Elastic bulk indexed {success_count}/{len(events)} events")

                return {
                    "success": not errors,
                    "events_sent": success_count,
                    "errors": [item for item in items if item.get("index", {}).get("status") not in [200, 201]]
                }

        except Exception as e:
            logger.error(f"SEC-052: Elastic batch_send failed: {e}")
            return {"success": False, "error": str(e), "events_sent": 0}

    async def query_events(self, query: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Query events using Elasticsearch DSL."""
        try:
            base_url = self._get_base_url()
            search_url = f"{base_url}/{self.config.index_name}-*/_search"

            # Build Elasticsearch query
            es_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": f"now-{hours}h",
                                        "lte": "now"
                                    }
                                }
                            }
                        ]
                    }
                },
                "size": 1000,
                "sort": [{"@timestamp": {"order": "desc"}}]
            }

            # Add query string if provided
            if query:
                es_query["query"]["bool"]["must"].append({
                    "query_string": {"query": query}
                })

            headers = self._build_auth_headers()
            headers["Content-Type"] = "application/json"

            request = urllib.request.Request(
                search_url,
                data=json.dumps(es_query).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            context = self._create_ssl_context()

            with urllib.request.urlopen(request, context=context, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                hits = result.get("hits", {}).get("hits", [])
                events = [hit.get("_source", {}) for hit in hits]
                logger.info(f"SEC-052: Elastic query returned {len(events)} events")
                return events

        except Exception as e:
            logger.error(f"SEC-052: Elastic query failed: {e}")
            return []


# ============================================================================
# SIEM Manager
# ============================================================================

class SIEMManager:
    """
    Central manager for SIEM connectors.

    Handles:
    - Connector registration
    - Active connector selection
    - Event routing
    - Threat intelligence aggregation
    """

    def __init__(self):
        self.connectors: Dict[str, SIEMConnector] = {}
        self.active_connector: Optional[SIEMConnector] = None

    def add_connector(self, name: str, connector: SIEMConnector) -> None:
        """Register a connector and set as active."""
        self.connectors[name] = connector
        self.active_connector = connector
        logger.info(f"SEC-052: SIEM connector '{name}' registered and set as active")

    def remove_connector(self, name: str) -> bool:
        """Remove a connector."""
        if name in self.connectors:
            connector = self.connectors.pop(name)
            if self.active_connector == connector:
                self.active_connector = next(iter(self.connectors.values()), None)
            logger.info(f"SEC-052: SIEM connector '{name}' removed")
            return True
        return False

    def set_active(self, name: str) -> bool:
        """Set active connector by name."""
        if name in self.connectors:
            self.active_connector = self.connectors[name]
            logger.info(f"SEC-052: Active SIEM connector set to '{name}'")
            return True
        return False

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
        """Send authorization decision event to SIEM."""
        if not self.active_connector:
            logger.warning("SEC-052: No active SIEM connector for authorization event")
            return False

        event = SecurityEvent(
            event_id=f"owai-auth-{action_id}-{int(datetime.now(UTC).timestamp())}",
            timestamp=datetime.now(UTC),
            event_type="authorization_decision",
            severity="high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
            source="ow-ai-authorization",
            agent_id=agent_id,
            action_type=action_type,
            risk_score=risk_score,
            status=decision,
            details={
                "action_id": action_id,
                "decision": decision,
                "authorized_by": user_email
            },
            compliance_frameworks=["NIST", "SOC2", "PCI-DSS"],
            nist_control=nist_control,
            mitre_tactic=mitre_tactic
        )

        return await self.active_connector.send_event(event)

    async def send_agent_action_event(
        self,
        action_id: int,
        agent_id: str,
        action_type: str,
        status: str,
        risk_score: int,
        details: Dict[str, Any] = None
    ) -> bool:
        """Send agent action event to SIEM."""
        if not self.active_connector:
            logger.warning("SEC-052: No active SIEM connector for agent action event")
            return False

        event = SecurityEvent(
            event_id=f"owai-action-{action_id}-{int(datetime.now(UTC).timestamp())}",
            timestamp=datetime.now(UTC),
            event_type="agent_action",
            severity="high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
            source="ow-ai-agent",
            agent_id=agent_id,
            action_type=action_type,
            risk_score=risk_score,
            status=status,
            details=details or {},
            compliance_frameworks=["NIST", "SOC2"]
        )

        return await self.active_connector.send_event(event)

    async def get_threat_intelligence(self, agent_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get threat intelligence for an agent from SIEM."""
        if not self.active_connector:
            return {
                "status": "not_configured",
                "message": "No SIEM configured",
                "agent_id": agent_id,
                "threat_score": 0,
                "threat_indicators": [],
                "recommendations": []
            }

        try:
            # Query events for this agent
            events = await self.active_connector.query_events(
                f"agent_id:{agent_id}",
                hours
            )

            # Analyze events for threat indicators
            high_risk_events = [e for e in events if e.get("risk_score", 0) > 70]
            threat_indicators = []

            for event in high_risk_events:
                threat_indicators.append({
                    "type": event.get("event_type"),
                    "severity": event.get("severity"),
                    "timestamp": event.get("timestamp"),
                    "details": event.get("details", {})
                })

            # Calculate threat score
            threat_score = min(100, len(high_risk_events) * 10) if high_risk_events else 0

            return {
                "status": "success",
                "agent_id": agent_id,
                "time_period_hours": hours,
                "total_events": len(events),
                "high_risk_events": len(high_risk_events),
                "threat_score": threat_score,
                "confidence_level": 0.85 if events else 0,
                "threat_indicators": threat_indicators[:10],  # Limit to top 10
                "recommendations": self._generate_recommendations(threat_score, threat_indicators)
            }

        except Exception as e:
            logger.error(f"SEC-052: Threat intelligence failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "agent_id": agent_id,
                "threat_score": 0
            }

    def _generate_recommendations(self, threat_score: int, indicators: List[Dict]) -> List[str]:
        """Generate security recommendations based on threat analysis."""
        recommendations = []

        if threat_score > 70:
            recommendations.append("CRITICAL: Immediate review of agent permissions required")
            recommendations.append("Consider temporarily disabling agent until investigation complete")
        elif threat_score > 40:
            recommendations.append("HIGH: Review recent agent actions for anomalies")
            recommendations.append("Enable enhanced logging for this agent")
        elif threat_score > 20:
            recommendations.append("MEDIUM: Monitor agent activity closely")
        else:
            recommendations.append("Agent activity within normal parameters")

        if any(i.get("severity") == "critical" for i in indicators):
            recommendations.insert(0, "ALERT: Critical severity events detected - escalate immediately")

        return recommendations
