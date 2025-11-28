"""
OW-kai Enterprise Webhook Signing Service

Banking-Level Security: HMAC-SHA256 signature generation and verification
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, NIST 800-63B

This module provides cryptographic signing for webhook payloads to ensure:
1. Authenticity - Payloads originated from OW-kai
2. Integrity - Payloads were not modified in transit
3. Non-repudiation - Signatures can be verified by recipients

Document ID: OWKAI-INT-001-SIGNER
Version: 1.0.0
Date: November 28, 2025
"""

import hmac
import hashlib
import secrets
import time
import json
import logging
from typing import Tuple, Optional
from datetime import datetime

logger = logging.getLogger("enterprise.webhooks.signer")


class WebhookSigner:
    """
    Enterprise Webhook Signing Service

    Implements HMAC-SHA256 signing following industry best practices:
    - Stripe-style signature format: sha256=<hex_signature>
    - Timestamp included to prevent replay attacks
    - Constant-time comparison for signature verification

    Security Standards:
    - HMAC-SHA256 (FIPS 198-1 compliant)
    - Cryptographically secure secret generation
    - Replay attack prevention with timestamps
    """

    # Signature header name
    SIGNATURE_HEADER = "X-OWkai-Signature"
    TIMESTAMP_HEADER = "X-OWkai-Timestamp"
    EVENT_ID_HEADER = "X-OWkai-Event-ID"
    DELIVERY_ID_HEADER = "X-OWkai-Delivery-ID"

    # Signature tolerance (5 minutes) to prevent replay attacks
    TIMESTAMP_TOLERANCE_SECONDS = 300

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a cryptographically secure webhook secret.

        Returns:
            32-byte hex-encoded secret (64 characters)

        Security: Uses secrets module for cryptographic randomness
        """
        return secrets.token_hex(32)

    @staticmethod
    def hash_secret(secret: str, salt: str) -> str:
        """
        Hash the secret for secure storage.

        The actual secret is never stored - only this hash.

        Args:
            secret: The plaintext secret
            salt: Random salt for hashing

        Returns:
            SHA-512 hash of salted secret
        """
        salted = f"{salt}{secret}".encode('utf-8')
        return hashlib.sha512(salted).hexdigest()

    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt for secret hashing."""
        return secrets.token_hex(16)

    @staticmethod
    def sign_payload(
        payload: dict,
        secret: str,
        timestamp: Optional[int] = None
    ) -> Tuple[str, int]:
        """
        Sign a webhook payload using HMAC-SHA256.

        The signature is computed over: timestamp.payload_json
        This binds the timestamp to the payload, preventing replay attacks.

        Args:
            payload: The webhook payload dictionary
            secret: The webhook secret (plaintext)
            timestamp: Unix timestamp (defaults to current time)

        Returns:
            Tuple of (signature_string, timestamp)
            Signature format: sha256=<hex_signature>

        Example:
            signature, ts = signer.sign_payload(payload, secret)
            # signature = "sha256=abc123..."
            # ts = 1732812345
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Serialize payload consistently (sorted keys, no extra whitespace)
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))

        # Create signed message: timestamp.payload
        message = f"{timestamp}.{payload_json}".encode('utf-8')

        # Compute HMAC-SHA256
        signature = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        signature_string = f"sha256={signature}"

        logger.debug(f"Generated signature for payload (ts={timestamp})")

        return signature_string, timestamp

    @staticmethod
    def verify_signature(
        payload: dict,
        signature_header: str,
        timestamp: int,
        secret: str,
        tolerance_seconds: int = TIMESTAMP_TOLERANCE_SECONDS
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a webhook signature.

        This method is provided for customers to use in their webhook receivers.

        Args:
            payload: The received webhook payload
            signature_header: The X-OWkai-Signature header value
            timestamp: The X-OWkai-Timestamp header value
            secret: The webhook secret
            tolerance_seconds: Maximum age of webhook (default 5 minutes)

        Returns:
            Tuple of (is_valid, error_message)

        Security:
        - Constant-time comparison to prevent timing attacks
        - Timestamp validation to prevent replay attacks
        """
        # Check timestamp freshness
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance_seconds:
            return False, f"Timestamp expired. Received: {timestamp}, Current: {current_time}"

        # Parse signature header
        if not signature_header.startswith("sha256="):
            return False, "Invalid signature format. Expected: sha256=<signature>"

        received_signature = signature_header[7:]  # Remove "sha256=" prefix

        # Recompute signature
        expected_signature, _ = WebhookSigner.sign_payload(payload, secret, timestamp)
        expected_hex = expected_signature[7:]  # Remove "sha256=" prefix

        # Constant-time comparison (prevents timing attacks)
        if hmac.compare_digest(received_signature, expected_hex):
            return True, None
        else:
            return False, "Signature mismatch"

    @staticmethod
    def get_signature_headers(
        payload: dict,
        secret: str,
        event_id: str,
        delivery_id: int
    ) -> dict:
        """
        Generate all webhook security headers.

        Args:
            payload: The webhook payload
            secret: The webhook secret
            event_id: Unique event identifier
            delivery_id: Delivery attempt ID

        Returns:
            Dictionary of headers to include in webhook request
        """
        signature, timestamp = WebhookSigner.sign_payload(payload, secret)

        return {
            WebhookSigner.SIGNATURE_HEADER: signature,
            WebhookSigner.TIMESTAMP_HEADER: str(timestamp),
            WebhookSigner.EVENT_ID_HEADER: event_id,
            WebhookSigner.DELIVERY_ID_HEADER: str(delivery_id),
            "Content-Type": "application/json",
            "User-Agent": "OWkai-Webhook/1.0"
        }


# Customer verification code (to be included in documentation)
CUSTOMER_VERIFICATION_CODE = '''
"""
OW-kai Webhook Signature Verification (Customer Implementation)

Copy this code to your webhook receiver to verify OW-kai webhooks.
"""

import hmac
import hashlib
import time
import json

def verify_owkai_webhook(
    payload_bytes: bytes,
    signature_header: str,
    timestamp_header: str,
    secret: str,
    tolerance_seconds: int = 300
) -> bool:
    """
    Verify an OW-kai webhook signature.

    Args:
        payload_bytes: Raw request body bytes
        signature_header: Value of X-OWkai-Signature header
        timestamp_header: Value of X-OWkai-Timestamp header
        secret: Your webhook secret (from OW-kai dashboard)
        tolerance_seconds: Maximum age of webhook (default 5 minutes)

    Returns:
        True if signature is valid, False otherwise

    Example (Flask):
        @app.route('/webhook', methods=['POST'])
        def webhook():
            if not verify_owkai_webhook(
                request.data,
                request.headers.get('X-OWkai-Signature'),
                request.headers.get('X-OWkai-Timestamp'),
                os.environ['OWKAI_WEBHOOK_SECRET']
            ):
                return 'Invalid signature', 401

            # Process webhook...
            return 'OK', 200

    Example (FastAPI):
        @app.post("/webhook")
        async def webhook(request: Request):
            body = await request.body()
            if not verify_owkai_webhook(
                body,
                request.headers.get('X-OWkai-Signature'),
                request.headers.get('X-OWkai-Timestamp'),
                os.environ['OWKAI_WEBHOOK_SECRET']
            ):
                raise HTTPException(401, 'Invalid signature')

            # Process webhook...
            return {"status": "ok"}
    """
    try:
        # Validate timestamp
        timestamp = int(timestamp_header)
        current_time = int(time.time())
        if abs(current_time - timestamp) > tolerance_seconds:
            print(f"Webhook timestamp expired: {timestamp}")
            return False

        # Parse signature
        if not signature_header.startswith("sha256="):
            print("Invalid signature format")
            return False
        received_signature = signature_header[7:]

        # Compute expected signature
        # Note: payload_bytes should be the raw body, not parsed JSON
        message = f"{timestamp}.{payload_bytes.decode('utf-8')}".encode('utf-8')
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        if hmac.compare_digest(received_signature, expected_signature):
            return True
        else:
            print("Signature mismatch")
            return False

    except Exception as e:
        print(f"Webhook verification error: {e}")
        return False
'''


class WebhookPayloadBuilder:
    """
    Build standardized webhook payloads.

    All payloads follow a consistent structure for easy parsing.
    """

    API_VERSION = "2025-11-28"

    @staticmethod
    def build_payload(
        event_type: str,
        data: dict,
        organization_id: int,
        idempotency_key: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """
        Build a standardized webhook payload.

        Args:
            event_type: The event type (e.g., "action.approved")
            data: Event-specific data
            organization_id: Organization ID for context
            idempotency_key: Unique key for deduplication
            metadata: Optional additional metadata

        Returns:
            Standardized webhook payload
        """
        import uuid

        payload = {
            "id": f"evt_{uuid.uuid4().hex[:24]}",
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "api_version": WebhookPayloadBuilder.API_VERSION,
            "organization_id": organization_id,
            "data": data,
            "metadata": {
                "idempotency_key": idempotency_key,
                "delivery_attempt": 1,
                **(metadata or {})
            }
        }

        return payload

    @staticmethod
    def build_action_submitted_payload(
        action_id: int,
        action_type: str,
        agent_id: str,
        description: str,
        risk_score: int,
        requested_by: str,
        organization_id: int,
        nist_controls: list = None,
        mitre_tactics: list = None
    ) -> dict:
        """Build payload for action.submitted event."""
        import uuid

        data = {
            "action_id": action_id,
            "action_type": action_type,
            "agent_id": agent_id,
            "description": description,
            "risk_score": risk_score,
            "risk_level": _get_risk_level(risk_score),
            "requested_by": requested_by,
            "submitted_at": datetime.utcnow().isoformat() + "Z",
            "nist_controls": nist_controls or [],
            "mitre_tactics": mitre_tactics or []
        }

        return WebhookPayloadBuilder.build_payload(
            event_type="action.submitted",
            data=data,
            organization_id=organization_id,
            idempotency_key=f"action_submitted_{action_id}_{uuid.uuid4().hex[:8]}"
        )

    @staticmethod
    def build_action_approved_payload(
        action_id: int,
        action_type: str,
        agent_id: str,
        risk_score: int,
        approved_by: str,
        approval_notes: str,
        organization_id: int
    ) -> dict:
        """Build payload for action.approved event."""
        import uuid

        data = {
            "action_id": action_id,
            "action_type": action_type,
            "agent_id": agent_id,
            "risk_score": risk_score,
            "risk_level": _get_risk_level(risk_score),
            "approved_by": approved_by,
            "approved_at": datetime.utcnow().isoformat() + "Z",
            "approval_notes": approval_notes
        }

        return WebhookPayloadBuilder.build_payload(
            event_type="action.approved",
            data=data,
            organization_id=organization_id,
            idempotency_key=f"action_approved_{action_id}_{uuid.uuid4().hex[:8]}"
        )

    @staticmethod
    def build_action_rejected_payload(
        action_id: int,
        action_type: str,
        agent_id: str,
        risk_score: int,
        rejected_by: str,
        rejection_reason: str,
        organization_id: int
    ) -> dict:
        """Build payload for action.rejected event."""
        import uuid

        data = {
            "action_id": action_id,
            "action_type": action_type,
            "agent_id": agent_id,
            "risk_score": risk_score,
            "risk_level": _get_risk_level(risk_score),
            "rejected_by": rejected_by,
            "rejected_at": datetime.utcnow().isoformat() + "Z",
            "rejection_reason": rejection_reason
        }

        return WebhookPayloadBuilder.build_payload(
            event_type="action.rejected",
            data=data,
            organization_id=organization_id,
            idempotency_key=f"action_rejected_{action_id}_{uuid.uuid4().hex[:8]}"
        )

    @staticmethod
    def build_alert_triggered_payload(
        alert_id: int,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        source: str,
        organization_id: int
    ) -> dict:
        """Build payload for alert.triggered event."""
        import uuid

        data = {
            "alert_id": alert_id,
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "description": description,
            "source": source,
            "triggered_at": datetime.utcnow().isoformat() + "Z"
        }

        return WebhookPayloadBuilder.build_payload(
            event_type="alert.triggered",
            data=data,
            organization_id=organization_id,
            idempotency_key=f"alert_triggered_{alert_id}_{uuid.uuid4().hex[:8]}"
        )

    @staticmethod
    def build_policy_violated_payload(
        policy_id: int,
        policy_name: str,
        violation_type: str,
        action_id: int,
        details: dict,
        organization_id: int
    ) -> dict:
        """Build payload for policy.violated event."""
        import uuid

        data = {
            "policy_id": policy_id,
            "policy_name": policy_name,
            "violation_type": violation_type,
            "action_id": action_id,
            "details": details,
            "violated_at": datetime.utcnow().isoformat() + "Z"
        }

        return WebhookPayloadBuilder.build_payload(
            event_type="policy.violated",
            data=data,
            organization_id=organization_id,
            idempotency_key=f"policy_violated_{policy_id}_{action_id}_{uuid.uuid4().hex[:8]}"
        )


def _get_risk_level(risk_score: int) -> str:
    """Convert numeric risk score to level."""
    if risk_score >= 90:
        return "critical"
    elif risk_score >= 70:
        return "high"
    elif risk_score >= 40:
        return "medium"
    else:
        return "low"
