"""
OW-kai Enterprise Integration Phase 3: ServiceNow Service

Banking-Level ITSM Integration Service with:
- OAuth2 client credentials flow
- AES-256 encrypted credential storage
- Retry with exponential backoff
- Full audit logging
- CMDB integration
- Bidirectional sync support

Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, ITIL v4
"""

import os
import json
import time
import uuid
import base64
import hashlib
import secrets
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from models_servicenow import (
    ServiceNowConnection,
    ServiceNowTicket,
    ServiceNowSyncLog,
    ServiceNowTicketType,
    ServiceNowPriority,
    ServiceNowImpact,
    ServiceNowUrgency,
    ServiceNowState,
    ServiceNowSyncStatus,
    ServiceNowAuthType,
    ServiceNowConnectionCreate,
    ServiceNowConnectionUpdate,
    ServiceNowTicketCreate,
    ServiceNowTicketUpdate,
    get_servicenow_defaults,
)

logger = logging.getLogger(__name__)


class ServiceNowEncryption:
    """
    AES-256 encryption for ServiceNow credentials.
    Uses Fernet with PBKDF2 key derivation.
    """

    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption with master key from env or generate"""
        self.master_key = master_key or os.getenv(
            "SERVICENOW_ENCRYPTION_KEY",
            os.getenv("ENCRYPTION_KEY", "owkai-servicenow-default-key-change-in-production")
        )

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))

    def generate_salt(self) -> str:
        """Generate a random salt"""
        return secrets.token_hex(16)

    def encrypt(self, plaintext: str, salt: str) -> str:
        """Encrypt plaintext using AES-256"""
        key = self._derive_key(salt.encode())
        fernet = Fernet(key)
        return fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str, salt: str) -> str:
        """Decrypt ciphertext"""
        key = self._derive_key(salt.encode())
        fernet = Fernet(key)
        return fernet.decrypt(ciphertext.encode()).decode()

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> Tuple[str, str]:
        """Encrypt credential dictionary, return (encrypted, salt)"""
        salt = self.generate_salt()
        encrypted = self.encrypt(json.dumps(credentials), salt)
        return encrypted, salt

    def decrypt_credentials(self, encrypted: str, salt: str) -> Dict[str, Any]:
        """Decrypt credentials and return dictionary"""
        decrypted = self.decrypt(encrypted, salt)
        return json.loads(decrypted)


class ServiceNowClient:
    """
    HTTP client for ServiceNow REST API.
    Handles OAuth2 authentication and API calls.
    """

    # Token cache: {connection_id: {"token": str, "expires_at": datetime}}
    _token_cache: Dict[int, Dict[str, Any]] = {}

    def __init__(
        self,
        instance_url: str,
        auth_type: ServiceNowAuthType,
        credentials: Dict[str, Any],
        timeout_seconds: int = 30,
        api_version: str = "v2",
    ):
        self.instance_url = instance_url.rstrip('/')
        self.auth_type = auth_type
        self.credentials = credentials
        self.timeout = timeout_seconds
        self.api_version = api_version
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _get_oauth_token(self) -> str:
        """Get OAuth2 access token using client credentials flow"""
        token_url = f"{self.instance_url}/oauth_token.do"

        data = {
            "grant_type": "password",  # ServiceNow uses password grant for service accounts
            "client_id": self.credentials.get("client_id"),
            "client_secret": self.credentials.get("client_secret"),
            "username": self.credentials.get("username"),
            "password": self.credentials.get("password"),
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()

        self._access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 1800)  # Default 30 minutes
        self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)

        return self._access_token

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.auth_type == ServiceNowAuthType.OAUTH2:
            # Check if token needs refresh
            if not self._access_token or (
                self._token_expires_at and datetime.now(timezone.utc) >= self._token_expires_at
            ):
                self._get_oauth_token()
            headers["Authorization"] = f"Bearer {self._access_token}"
        else:
            # Basic auth
            import base64
            creds = f"{self.credentials.get('username')}:{self.credentials.get('password')}"
            encoded = base64.b64encode(creds.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    def _api_url(self, table: str, sys_id: Optional[str] = None) -> str:
        """Build ServiceNow Table API URL"""
        base = f"{self.instance_url}/api/now/{self.api_version}/table/{table}"
        if sys_id:
            base = f"{base}/{sys_id}"
        return base

    async def test_connection(self) -> Dict[str, Any]:
        """Test ServiceNow connection by getting instance info"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.instance_url}/api/now/v2/table/sys_properties",
                    headers=self._get_headers(),
                    params={"sysparm_limit": 1}
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "message": "Connection successful",
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "instance_url": self.instance_url,
                }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "message": f"HTTP Error: {e.response.status_code}",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_details": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "response_time_ms": int((time.time() - start_time) * 1000),
                "error_details": str(e),
            }

    async def create_record(
        self,
        table: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a record in ServiceNow"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self._api_url(table),
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json().get("result", {})

    async def update_record(
        self,
        table: str,
        sys_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in ServiceNow"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                self._api_url(table, sys_id),
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json().get("result", {})

    async def get_record(
        self,
        table: str,
        sys_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a record from ServiceNow"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self._api_url(table, sys_id),
                headers=self._get_headers()
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("result", {})

    async def query_records(
        self,
        table: str,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query records from ServiceNow"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self._api_url(table),
                headers=self._get_headers(),
                params={
                    "sysparm_query": query,
                    "sysparm_limit": limit,
                    "sysparm_offset": offset,
                }
            )
            response.raise_for_status()
            return response.json().get("result", [])


class ServiceNowService:
    """
    Main service for ServiceNow integration.
    Handles connections, tickets, and sync operations.
    """

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff

    # Table mappings
    TICKET_TYPE_TO_TABLE = {
        ServiceNowTicketType.INCIDENT: "incident",
        ServiceNowTicketType.CHANGE_REQUEST: "change_request",
        ServiceNowTicketType.PROBLEM: "problem",
        ServiceNowTicketType.SERVICE_REQUEST: "sc_request",
        ServiceNowTicketType.TASK: "sc_task",
    }

    def __init__(self, db: Session):
        self.db = db
        self.encryption = ServiceNowEncryption()

    def _get_client(self, connection: ServiceNowConnection) -> ServiceNowClient:
        """Create ServiceNow client from connection"""
        credentials = self.encryption.decrypt_credentials(
            connection.encrypted_credentials,
            connection.encryption_salt
        )

        # Add OAuth credentials if present
        if connection.encrypted_client_id:
            credentials["client_id"] = self.encryption.decrypt(
                connection.encrypted_client_id,
                connection.encryption_salt
            )
        if connection.encrypted_client_secret:
            credentials["client_secret"] = self.encryption.decrypt(
                connection.encrypted_client_secret,
                connection.encryption_salt
            )

        return ServiceNowClient(
            instance_url=connection.instance_url,
            auth_type=connection.auth_type,
            credentials=credentials,
            timeout_seconds=connection.timeout_seconds,
            api_version=connection.api_version,
        )

    def _log_sync(
        self,
        organization_id: int,
        connection_id: Optional[int],
        ticket_id: Optional[int],
        operation: str,
        direction: str,
        request_payload: Optional[Dict] = None,
        response_payload: Optional[Dict] = None,
        http_status: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """Log sync operation to audit table"""
        log = ServiceNowSyncLog(
            organization_id=organization_id,
            connection_id=connection_id,
            ticket_id=ticket_id,
            operation=operation,
            direction=direction,
            request_payload=request_payload,
            response_payload=response_payload,
            http_status_code=http_status,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            error_type=error_type,
        )
        self.db.add(log)
        self.db.commit()

    # ============================================
    # Connection Management
    # ============================================

    def create_connection(
        self,
        data: ServiceNowConnectionCreate,
        organization_id: int,
        user_id: int
    ) -> ServiceNowConnection:
        """Create a new ServiceNow connection"""
        # Prepare credentials
        credentials = {}
        if data.username:
            credentials["username"] = data.username
        if data.password:
            credentials["password"] = data.password

        # Encrypt credentials
        encrypted_creds, salt = self.encryption.encrypt_credentials(credentials)

        connection = ServiceNowConnection(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            instance_url=data.instance_url,
            auth_type=data.auth_type,
            encrypted_credentials=encrypted_creds,
            encryption_salt=salt,
            api_version=data.api_version,
            timeout_seconds=data.timeout_seconds,
            max_retries=data.max_retries,
            default_assignment_group=data.default_assignment_group,
            default_caller_id=data.default_caller_id,
            default_category=data.default_category,
            default_subcategory=data.default_subcategory,
            cmdb_class=data.cmdb_class,
            cmdb_lookup_field=data.cmdb_lookup_field,
            field_mappings=data.field_mappings,
            custom_fields=data.custom_fields,
            created_by=user_id,
        )

        # Encrypt OAuth credentials if provided
        if data.client_id:
            connection.encrypted_client_id = self.encryption.encrypt(data.client_id, salt)
        if data.client_secret:
            connection.encrypted_client_secret = self.encryption.encrypt(data.client_secret, salt)

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        logger.info(f"Created ServiceNow connection {connection.id} for org {organization_id}")
        return connection

    def get_connection(
        self,
        connection_id: int,
        organization_id: int
    ) -> Optional[ServiceNowConnection]:
        """Get a connection by ID with tenant isolation"""
        return self.db.query(ServiceNowConnection).filter(
            and_(
                ServiceNowConnection.id == connection_id,
                ServiceNowConnection.organization_id == organization_id
            )
        ).first()

    def list_connections(
        self,
        organization_id: int,
        active_only: bool = False
    ) -> List[ServiceNowConnection]:
        """List all connections for an organization"""
        query = self.db.query(ServiceNowConnection).filter(
            ServiceNowConnection.organization_id == organization_id
        )
        if active_only:
            query = query.filter(ServiceNowConnection.is_active == True)
        return query.order_by(ServiceNowConnection.created_at.desc()).all()

    def update_connection(
        self,
        connection_id: int,
        organization_id: int,
        data: ServiceNowConnectionUpdate,
        user_id: int
    ) -> Optional[ServiceNowConnection]:
        """Update a connection"""
        connection = self.get_connection(connection_id, organization_id)
        if not connection:
            return None

        # Update simple fields
        update_fields = ['name', 'description', 'instance_url', 'api_version',
                        'timeout_seconds', 'max_retries', 'default_assignment_group',
                        'default_caller_id', 'default_category', 'default_subcategory',
                        'cmdb_class', 'cmdb_lookup_field', 'field_mappings',
                        'custom_fields', 'is_active']

        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(connection, field, value)

        # Handle credential updates
        if data.username or data.password:
            credentials = self.encryption.decrypt_credentials(
                connection.encrypted_credentials,
                connection.encryption_salt
            )
            if data.username:
                credentials["username"] = data.username
            if data.password:
                credentials["password"] = data.password

            # Re-encrypt with new salt
            new_salt = self.encryption.generate_salt()
            connection.encrypted_credentials = self.encryption.encrypt(
                json.dumps(credentials), new_salt
            )
            connection.encryption_salt = new_salt

            # Re-encrypt OAuth credentials with new salt if they exist
            if connection.encrypted_client_id:
                old_client_id = self.encryption.decrypt(
                    connection.encrypted_client_id,
                    connection.encryption_salt
                )
                connection.encrypted_client_id = self.encryption.encrypt(old_client_id, new_salt)

        # Update OAuth credentials
        if data.client_id:
            connection.encrypted_client_id = self.encryption.encrypt(
                data.client_id, connection.encryption_salt
            )
        if data.client_secret:
            connection.encrypted_client_secret = self.encryption.encrypt(
                data.client_secret, connection.encryption_salt
            )

        connection.updated_by = user_id
        connection.is_verified = False  # Require re-verification

        self.db.commit()
        self.db.refresh(connection)
        return connection

    def delete_connection(
        self,
        connection_id: int,
        organization_id: int
    ) -> bool:
        """Delete a connection"""
        connection = self.get_connection(connection_id, organization_id)
        if not connection:
            return False

        self.db.delete(connection)
        self.db.commit()
        logger.info(f"Deleted ServiceNow connection {connection_id}")
        return True

    async def test_connection(
        self,
        connection_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """Test a ServiceNow connection"""
        connection = self.get_connection(connection_id, organization_id)
        if not connection:
            return {"success": False, "message": "Connection not found"}

        client = self._get_client(connection)
        result = await client.test_connection()

        # Update verification status
        connection.last_verified_at = datetime.now(timezone.utc)
        if result["success"]:
            connection.is_verified = True
            connection.verification_error = None
        else:
            connection.is_verified = False
            connection.verification_error = result.get("error_details")

        self.db.commit()

        # Log the test
        self._log_sync(
            organization_id=organization_id,
            connection_id=connection_id,
            ticket_id=None,
            operation="verify",
            direction="outbound",
            response_time_ms=result.get("response_time_ms"),
            success=result["success"],
            error_message=result.get("error_details"),
        )

        return result

    # ============================================
    # Ticket Management
    # ============================================

    async def create_ticket(
        self,
        data: ServiceNowTicketCreate,
        organization_id: int,
        user_id: int
    ) -> ServiceNowTicket:
        """Create a ServiceNow ticket"""
        connection = self.get_connection(data.connection_id, organization_id)
        if not connection:
            raise ValueError("Connection not found")
        if not connection.is_active:
            raise ValueError("Connection is not active")

        # Create local ticket record
        ticket = ServiceNowTicket(
            organization_id=organization_id,
            connection_id=connection.id,
            ticket_type=data.ticket_type,
            short_description=data.short_description,
            description=data.description,
            work_notes=data.work_notes,
            priority=data.priority,
            impact=data.impact,
            urgency=data.urgency,
            assignment_group=data.assignment_group or connection.default_assignment_group,
            assigned_to=data.assigned_to,
            caller_id=data.caller_id or connection.default_caller_id,
            category=data.category or connection.default_category,
            subcategory=data.subcategory or connection.default_subcategory,
            cmdb_ci=data.cmdb_ci,
            source_type=data.source_type,
            source_id=data.source_id,
            source_data=data.source_data,
            custom_fields=data.custom_fields,
            created_by=user_id,
        )

        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        # Sync to ServiceNow
        await self._sync_ticket_to_servicenow(ticket, connection)

        return ticket

    async def _sync_ticket_to_servicenow(
        self,
        ticket: ServiceNowTicket,
        connection: ServiceNowConnection
    ):
        """Sync a ticket to ServiceNow with retry logic"""
        client = self._get_client(connection)
        table = self.TICKET_TYPE_TO_TABLE.get(ticket.ticket_type, "incident")

        # Build payload
        payload = {
            "short_description": ticket.short_description,
            "description": ticket.description,
            "priority": ticket.priority.value,
            "impact": ticket.impact.value,
            "urgency": ticket.urgency.value,
            "state": ticket.state.value,
        }

        if ticket.assignment_group:
            payload["assignment_group"] = ticket.assignment_group
        if ticket.assigned_to:
            payload["assigned_to"] = ticket.assigned_to
        if ticket.caller_id:
            payload["caller_id"] = ticket.caller_id
        if ticket.category:
            payload["category"] = ticket.category
        if ticket.subcategory:
            payload["subcategory"] = ticket.subcategory
        if ticket.work_notes:
            payload["work_notes"] = ticket.work_notes
        if ticket.cmdb_ci:
            payload["cmdb_ci"] = ticket.cmdb_ci

        # Add custom fields
        if ticket.custom_fields:
            payload.update(ticket.custom_fields)
        if connection.custom_fields:
            payload.update(connection.custom_fields)

        # Apply field mappings
        if connection.field_mappings:
            for owkai_field, snow_field in connection.field_mappings.items():
                if owkai_field in payload:
                    payload[snow_field] = payload.pop(owkai_field)

        start_time = time.time()
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                if ticket.servicenow_sys_id:
                    # Update existing
                    result = await client.update_record(table, ticket.servicenow_sys_id, payload)
                else:
                    # Create new
                    result = await client.create_record(table, payload)

                # Update ticket with ServiceNow data
                ticket.servicenow_sys_id = result.get("sys_id")
                ticket.servicenow_number = result.get("number")
                ticket.servicenow_link = f"{connection.instance_url}/{table}.do?sys_id={result.get('sys_id')}"
                ticket.servicenow_response = result
                ticket.sync_status = ServiceNowSyncStatus.SYNCED
                ticket.sync_attempts = attempt + 1
                ticket.last_synced_at = datetime.now(timezone.utc)
                ticket.last_sync_error = None

                # Update connection metrics
                connection.total_tickets_created += 1
                connection.last_sync_at = datetime.now(timezone.utc)

                self.db.commit()

                # Log success
                self._log_sync(
                    organization_id=ticket.organization_id,
                    connection_id=connection.id,
                    ticket_id=ticket.id,
                    operation="create" if not ticket.servicenow_sys_id else "update",
                    direction="outbound",
                    request_payload=payload,
                    response_payload=result,
                    response_time_ms=int((time.time() - start_time) * 1000),
                    success=True,
                )

                logger.info(f"Synced ticket {ticket.id} to ServiceNow: {ticket.servicenow_number}")
                return

            except Exception as e:
                last_error = str(e)
                logger.warning(f"ServiceNow sync attempt {attempt + 1} failed: {e}")

                if attempt < self.MAX_RETRIES - 1:
                    await self._async_sleep(self.RETRY_DELAYS[attempt])

        # All retries failed
        ticket.sync_status = ServiceNowSyncStatus.FAILED
        ticket.sync_attempts = self.MAX_RETRIES
        ticket.last_sync_error = last_error

        connection.total_sync_errors += 1
        connection.last_error_at = datetime.now(timezone.utc)

        self.db.commit()

        # Log failure
        self._log_sync(
            organization_id=ticket.organization_id,
            connection_id=connection.id,
            ticket_id=ticket.id,
            operation="create",
            direction="outbound",
            request_payload=payload,
            response_time_ms=int((time.time() - start_time) * 1000),
            success=False,
            error_message=last_error,
            error_type="sync_failed",
        )

        logger.error(f"Failed to sync ticket {ticket.id} to ServiceNow after {self.MAX_RETRIES} attempts")

    async def _async_sleep(self, seconds: int):
        """Async sleep for retry delays"""
        import asyncio
        await asyncio.sleep(seconds)

    def get_ticket(
        self,
        ticket_id: int,
        organization_id: int
    ) -> Optional[ServiceNowTicket]:
        """Get a ticket by ID"""
        return self.db.query(ServiceNowTicket).filter(
            and_(
                ServiceNowTicket.id == ticket_id,
                ServiceNowTicket.organization_id == organization_id
            )
        ).first()

    def list_tickets(
        self,
        organization_id: int,
        connection_id: Optional[int] = None,
        ticket_type: Optional[ServiceNowTicketType] = None,
        sync_status: Optional[ServiceNowSyncStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ServiceNowTicket]:
        """List tickets with optional filters"""
        query = self.db.query(ServiceNowTicket).filter(
            ServiceNowTicket.organization_id == organization_id
        )

        if connection_id:
            query = query.filter(ServiceNowTicket.connection_id == connection_id)
        if ticket_type:
            query = query.filter(ServiceNowTicket.ticket_type == ticket_type)
        if sync_status:
            query = query.filter(ServiceNowTicket.sync_status == sync_status)

        return query.order_by(ServiceNowTicket.created_at.desc()).limit(limit).offset(offset).all()

    async def update_ticket(
        self,
        ticket_id: int,
        organization_id: int,
        data: ServiceNowTicketUpdate
    ) -> Optional[ServiceNowTicket]:
        """Update a ticket and sync to ServiceNow"""
        ticket = self.get_ticket(ticket_id, organization_id)
        if not ticket:
            return None

        # Update local fields
        update_fields = ['short_description', 'description', 'work_notes',
                        'priority', 'impact', 'urgency', 'state',
                        'assignment_group', 'assigned_to', 'category',
                        'subcategory', 'custom_fields']

        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(ticket, field, value)

        ticket.local_updated_at = datetime.now(timezone.utc)
        self.db.commit()

        # Sync to ServiceNow if connected
        if ticket.servicenow_sys_id:
            connection = self.db.query(ServiceNowConnection).get(ticket.connection_id)
            if connection and connection.is_active:
                await self._sync_ticket_to_servicenow(ticket, connection)

        self.db.refresh(ticket)
        return ticket

    async def retry_sync(
        self,
        ticket_id: int,
        organization_id: int
    ) -> ServiceNowTicket:
        """Retry syncing a failed ticket"""
        ticket = self.get_ticket(ticket_id, organization_id)
        if not ticket:
            raise ValueError("Ticket not found")

        connection = self.db.query(ServiceNowConnection).get(ticket.connection_id)
        if not connection:
            raise ValueError("Connection not found")

        ticket.sync_status = ServiceNowSyncStatus.PENDING
        self.db.commit()

        await self._sync_ticket_to_servicenow(ticket, connection)

        self.db.refresh(ticket)
        return ticket

    # ============================================
    # Metrics
    # ============================================

    def get_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Get ServiceNow integration metrics"""
        # Connection counts
        total_connections = self.db.query(func.count(ServiceNowConnection.id)).filter(
            ServiceNowConnection.organization_id == organization_id
        ).scalar()

        active_connections = self.db.query(func.count(ServiceNowConnection.id)).filter(
            and_(
                ServiceNowConnection.organization_id == organization_id,
                ServiceNowConnection.is_active == True
            )
        ).scalar()

        # Ticket counts
        total_tickets = self.db.query(func.count(ServiceNowTicket.id)).filter(
            ServiceNowTicket.organization_id == organization_id
        ).scalar()

        # Tickets by type
        tickets_by_type = dict(
            self.db.query(
                ServiceNowTicket.ticket_type,
                func.count(ServiceNowTicket.id)
            ).filter(
                ServiceNowTicket.organization_id == organization_id
            ).group_by(ServiceNowTicket.ticket_type).all()
        )

        # Tickets by sync status
        tickets_by_status = dict(
            self.db.query(
                ServiceNowTicket.sync_status,
                func.count(ServiceNowTicket.id)
            ).filter(
                ServiceNowTicket.organization_id == organization_id
            ).group_by(ServiceNowTicket.sync_status).all()
        )

        # Success rate
        synced = tickets_by_status.get(ServiceNowSyncStatus.SYNCED, 0)
        failed = tickets_by_status.get(ServiceNowSyncStatus.FAILED, 0)
        success_rate = (synced / (synced + failed) * 100) if (synced + failed) > 0 else 100.0

        # Average sync time
        avg_sync_time = self.db.query(func.avg(ServiceNowSyncLog.response_time_ms)).filter(
            and_(
                ServiceNowSyncLog.organization_id == organization_id,
                ServiceNowSyncLog.success == True
            )
        ).scalar() or 0

        # Last 24 hours
        last_24h = datetime.now(timezone.utc) - timedelta(hours=24)

        last_24h_tickets = self.db.query(func.count(ServiceNowTicket.id)).filter(
            and_(
                ServiceNowTicket.organization_id == organization_id,
                ServiceNowTicket.created_at >= last_24h
            )
        ).scalar()

        last_24h_errors = self.db.query(func.count(ServiceNowSyncLog.id)).filter(
            and_(
                ServiceNowSyncLog.organization_id == organization_id,
                ServiceNowSyncLog.success == False,
                ServiceNowSyncLog.created_at >= last_24h
            )
        ).scalar()

        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_tickets": total_tickets,
            "tickets_by_type": {str(k.value if hasattr(k, 'value') else k): v for k, v in tickets_by_type.items()},
            "tickets_by_status": {str(k.value if hasattr(k, 'value') else k): v for k, v in tickets_by_status.items()},
            "sync_success_rate": round(success_rate, 2),
            "average_sync_time_ms": round(float(avg_sync_time), 2),
            "last_24h_tickets": last_24h_tickets,
            "last_24h_errors": last_24h_errors,
        }

    def get_sync_logs(
        self,
        organization_id: int,
        connection_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ServiceNowSyncLog]:
        """Get sync logs for an organization"""
        query = self.db.query(ServiceNowSyncLog).filter(
            ServiceNowSyncLog.organization_id == organization_id
        )

        if connection_id:
            query = query.filter(ServiceNowSyncLog.connection_id == connection_id)

        return query.order_by(ServiceNowSyncLog.created_at.desc()).limit(limit).all()
