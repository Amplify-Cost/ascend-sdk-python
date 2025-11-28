"""
OW-kai Enterprise Webhook System - Comprehensive Unit Tests

Testing: Phase 1 Enterprise Integration - Webhook Event System
Coverage: HMAC signing, signature verification, payload building, service logic

Security Tests:
- HMAC-SHA256 signature generation
- Signature verification with constant-time comparison
- Replay attack prevention via timestamps
- Secret hashing and storage

Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, NIST 800-63B
Document ID: OWKAI-INT-001-TESTS
Version: 1.0.0
Date: November 28, 2025
"""

import pytest
import time
import json
import hmac
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

# Import the modules under test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.webhook_signer import WebhookSigner, WebhookPayloadBuilder


class TestWebhookSigner:
    """Test suite for WebhookSigner class"""

    def test_generate_secret_length(self):
        """Test that generated secrets are 64 characters (32 bytes hex)"""
        secret = WebhookSigner.generate_secret()
        assert len(secret) == 64
        assert all(c in '0123456789abcdef' for c in secret)

    def test_generate_secret_uniqueness(self):
        """Test that each generated secret is unique"""
        secrets = [WebhookSigner.generate_secret() for _ in range(100)]
        assert len(set(secrets)) == 100  # All should be unique

    def test_generate_salt_length(self):
        """Test that generated salts are 32 characters (16 bytes hex)"""
        salt = WebhookSigner.generate_salt()
        assert len(salt) == 32
        assert all(c in '0123456789abcdef' for c in salt)

    def test_hash_secret_deterministic(self):
        """Test that hashing same secret+salt produces same result"""
        secret = "test_secret_12345"
        salt = "test_salt_67890"
        hash1 = WebhookSigner.hash_secret(secret, salt)
        hash2 = WebhookSigner.hash_secret(secret, salt)
        assert hash1 == hash2

    def test_hash_secret_different_salts(self):
        """Test that different salts produce different hashes"""
        secret = "test_secret_12345"
        salt1 = "salt1"
        salt2 = "salt2"
        hash1 = WebhookSigner.hash_secret(secret, salt1)
        hash2 = WebhookSigner.hash_secret(secret, salt2)
        assert hash1 != hash2

    def test_sign_payload_format(self):
        """Test that signature has correct format: sha256=<hex>"""
        payload = {"event": "test", "data": {"id": 1}}
        secret = WebhookSigner.generate_secret()
        signature, timestamp = WebhookSigner.sign_payload(payload, secret)

        assert signature.startswith("sha256=")
        hex_part = signature[7:]  # Remove "sha256=" prefix
        assert len(hex_part) == 64  # SHA-256 produces 64 hex chars
        assert all(c in '0123456789abcdef' for c in hex_part)

    def test_sign_payload_timestamp(self):
        """Test that timestamp is close to current time"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        _, timestamp = WebhookSigner.sign_payload(payload, secret)

        current_time = int(time.time())
        assert abs(current_time - timestamp) <= 1

    def test_sign_payload_custom_timestamp(self):
        """Test signing with custom timestamp"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        custom_ts = 1700000000
        signature, timestamp = WebhookSigner.sign_payload(payload, secret, custom_ts)

        assert timestamp == custom_ts

    def test_sign_payload_deterministic(self):
        """Test that same payload+secret+timestamp produces same signature"""
        payload = {"event": "test", "data": {"id": 1}}
        secret = "fixed_secret_for_test"
        timestamp = 1700000000

        sig1, _ = WebhookSigner.sign_payload(payload, secret, timestamp)
        sig2, _ = WebhookSigner.sign_payload(payload, secret, timestamp)

        assert sig1 == sig2

    def test_sign_payload_different_payloads(self):
        """Test that different payloads produce different signatures"""
        secret = "fixed_secret_for_test"
        timestamp = 1700000000

        payload1 = {"event": "test1"}
        payload2 = {"event": "test2"}

        sig1, _ = WebhookSigner.sign_payload(payload1, secret, timestamp)
        sig2, _ = WebhookSigner.sign_payload(payload2, secret, timestamp)

        assert sig1 != sig2

    def test_verify_signature_valid(self):
        """Test verification of a valid signature"""
        payload = {"event": "test", "data": {"id": 123}}
        secret = WebhookSigner.generate_secret()

        # Sign the payload
        signature, timestamp = WebhookSigner.sign_payload(payload, secret)

        # Verify it
        is_valid, error = WebhookSigner.verify_signature(
            payload, signature, timestamp, secret
        )

        assert is_valid is True
        assert error is None

    def test_verify_signature_invalid_signature(self):
        """Test rejection of invalid signature"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        timestamp = int(time.time())

        # Create a wrong signature
        wrong_signature = "sha256=" + "a" * 64

        is_valid, error = WebhookSigner.verify_signature(
            payload, wrong_signature, timestamp, secret
        )

        assert is_valid is False
        assert "mismatch" in error.lower()

    def test_verify_signature_expired_timestamp(self):
        """Test rejection of expired timestamp (replay attack prevention)"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()

        # Create signature with old timestamp (10 minutes ago)
        old_timestamp = int(time.time()) - 600
        signature, _ = WebhookSigner.sign_payload(payload, secret, old_timestamp)

        is_valid, error = WebhookSigner.verify_signature(
            payload, signature, old_timestamp, secret
        )

        assert is_valid is False
        assert "expired" in error.lower()

    def test_verify_signature_invalid_format(self):
        """Test rejection of malformed signature"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        timestamp = int(time.time())

        # Signature without sha256= prefix
        bad_signature = "abc123"

        is_valid, error = WebhookSigner.verify_signature(
            payload, bad_signature, timestamp, secret
        )

        assert is_valid is False
        assert "format" in error.lower()

    def test_get_signature_headers_contains_all_headers(self):
        """Test that all required headers are generated"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        event_id = "evt_test123"
        delivery_id = 42

        headers = WebhookSigner.get_signature_headers(
            payload, secret, event_id, delivery_id
        )

        assert WebhookSigner.SIGNATURE_HEADER in headers
        assert WebhookSigner.TIMESTAMP_HEADER in headers
        assert WebhookSigner.EVENT_ID_HEADER in headers
        assert WebhookSigner.DELIVERY_ID_HEADER in headers
        assert "Content-Type" in headers
        assert "User-Agent" in headers

    def test_get_signature_headers_values(self):
        """Test header values are correct"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        event_id = "evt_abc123"
        delivery_id = 99

        headers = WebhookSigner.get_signature_headers(
            payload, secret, event_id, delivery_id
        )

        assert headers[WebhookSigner.SIGNATURE_HEADER].startswith("sha256=")
        assert headers[WebhookSigner.EVENT_ID_HEADER] == event_id
        assert headers[WebhookSigner.DELIVERY_ID_HEADER] == "99"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "OWkai-Webhook/1.0"


class TestWebhookPayloadBuilder:
    """Test suite for WebhookPayloadBuilder class"""

    def test_build_payload_structure(self):
        """Test that payload has correct structure"""
        payload = WebhookPayloadBuilder.build_payload(
            event_type="test.event",
            data={"key": "value"},
            organization_id=1,
            idempotency_key="test_key_123"
        )

        assert "id" in payload
        assert "type" in payload
        assert "timestamp" in payload
        assert "api_version" in payload
        assert "organization_id" in payload
        assert "data" in payload
        assert "metadata" in payload

    def test_build_payload_event_id_format(self):
        """Test event ID has correct format"""
        payload = WebhookPayloadBuilder.build_payload(
            event_type="test.event",
            data={},
            organization_id=1,
            idempotency_key="test"
        )

        assert payload["id"].startswith("evt_")
        assert len(payload["id"]) == 28  # evt_ + 24 hex chars

    def test_build_payload_api_version(self):
        """Test API version is set correctly"""
        payload = WebhookPayloadBuilder.build_payload(
            event_type="test.event",
            data={},
            organization_id=1,
            idempotency_key="test"
        )

        assert payload["api_version"] == WebhookPayloadBuilder.API_VERSION

    def test_build_payload_metadata(self):
        """Test metadata contains idempotency key and delivery attempt"""
        custom_metadata = {"custom_field": "custom_value"}
        payload = WebhookPayloadBuilder.build_payload(
            event_type="test.event",
            data={},
            organization_id=1,
            idempotency_key="idem_key_123",
            metadata=custom_metadata
        )

        assert payload["metadata"]["idempotency_key"] == "idem_key_123"
        assert payload["metadata"]["delivery_attempt"] == 1
        assert payload["metadata"]["custom_field"] == "custom_value"

    def test_build_action_submitted_payload(self):
        """Test action.submitted event payload"""
        payload = WebhookPayloadBuilder.build_action_submitted_payload(
            action_id=100,
            action_type="database_write",
            agent_id="agent_001",
            description="Test action",
            risk_score=75,
            requested_by="user@example.com",
            organization_id=1,
            nist_controls=["AC-2", "AU-12"],
            mitre_tactics=["TA0001"]
        )

        assert payload["type"] == "action.submitted"
        assert payload["data"]["action_id"] == 100
        assert payload["data"]["action_type"] == "database_write"
        assert payload["data"]["risk_score"] == 75
        assert payload["data"]["risk_level"] == "high"
        assert payload["data"]["nist_controls"] == ["AC-2", "AU-12"]
        assert payload["data"]["mitre_tactics"] == ["TA0001"]

    def test_build_action_approved_payload(self):
        """Test action.approved event payload"""
        payload = WebhookPayloadBuilder.build_action_approved_payload(
            action_id=100,
            action_type="database_write",
            agent_id="agent_001",
            risk_score=60,
            approved_by="admin@example.com",
            approval_notes="Approved for testing",
            organization_id=1
        )

        assert payload["type"] == "action.approved"
        assert payload["data"]["action_id"] == 100
        assert payload["data"]["approved_by"] == "admin@example.com"
        assert payload["data"]["approval_notes"] == "Approved for testing"
        assert payload["data"]["risk_level"] == "medium"

    def test_build_action_rejected_payload(self):
        """Test action.rejected event payload"""
        payload = WebhookPayloadBuilder.build_action_rejected_payload(
            action_id=100,
            action_type="high_risk_operation",
            agent_id="agent_001",
            risk_score=95,
            rejected_by="security@example.com",
            rejection_reason="Policy violation",
            organization_id=1
        )

        assert payload["type"] == "action.rejected"
        assert payload["data"]["rejected_by"] == "security@example.com"
        assert payload["data"]["rejection_reason"] == "Policy violation"
        assert payload["data"]["risk_level"] == "critical"

    def test_build_alert_triggered_payload(self):
        """Test alert.triggered event payload"""
        payload = WebhookPayloadBuilder.build_alert_triggered_payload(
            alert_id=500,
            alert_type="security_anomaly",
            severity="high",
            title="Suspicious activity detected",
            description="Multiple failed login attempts",
            source="auth_service",
            organization_id=1
        )

        assert payload["type"] == "alert.triggered"
        assert payload["data"]["alert_id"] == 500
        assert payload["data"]["severity"] == "high"
        assert payload["data"]["title"] == "Suspicious activity detected"

    def test_build_policy_violated_payload(self):
        """Test policy.violated event payload"""
        payload = WebhookPayloadBuilder.build_policy_violated_payload(
            policy_id=10,
            policy_name="No Production Access",
            violation_type="blocked_action",
            action_id=200,
            details={"attempted_action": "database_delete"},
            organization_id=1
        )

        assert payload["type"] == "policy.violated"
        assert payload["data"]["policy_id"] == 10
        assert payload["data"]["policy_name"] == "No Production Access"
        assert payload["data"]["violation_type"] == "blocked_action"


class TestRiskLevelConversion:
    """Test the risk score to risk level conversion"""

    def test_critical_risk_level(self):
        """Test risk score >= 90 returns critical"""
        from services.webhook_signer import _get_risk_level
        assert _get_risk_level(90) == "critical"
        assert _get_risk_level(95) == "critical"
        assert _get_risk_level(100) == "critical"

    def test_high_risk_level(self):
        """Test risk score 70-89 returns high"""
        from services.webhook_signer import _get_risk_level
        assert _get_risk_level(70) == "high"
        assert _get_risk_level(80) == "high"
        assert _get_risk_level(89) == "high"

    def test_medium_risk_level(self):
        """Test risk score 40-69 returns medium"""
        from services.webhook_signer import _get_risk_level
        assert _get_risk_level(40) == "medium"
        assert _get_risk_level(50) == "medium"
        assert _get_risk_level(69) == "medium"

    def test_low_risk_level(self):
        """Test risk score < 40 returns low"""
        from services.webhook_signer import _get_risk_level
        assert _get_risk_level(0) == "low"
        assert _get_risk_level(20) == "low"
        assert _get_risk_level(39) == "low"


class TestSignatureSecurityProperties:
    """Security-focused tests for the signing implementation"""

    def test_constant_time_comparison(self):
        """Verify constant-time comparison is used (hmac.compare_digest)"""
        # This is a structural test - we verify the code uses hmac.compare_digest
        import inspect
        source = inspect.getsource(WebhookSigner.verify_signature)
        assert "hmac.compare_digest" in source

    def test_signature_prevents_tampering(self):
        """Test that any payload modification invalidates signature"""
        payload = {"event": "test", "data": {"amount": 100}}
        secret = WebhookSigner.generate_secret()
        signature, timestamp = WebhookSigner.sign_payload(payload, secret)

        # Tamper with payload
        tampered_payload = {"event": "test", "data": {"amount": 999}}

        is_valid, error = WebhookSigner.verify_signature(
            tampered_payload, signature, timestamp, secret
        )

        assert is_valid is False

    def test_signature_bound_to_timestamp(self):
        """Test that changing timestamp invalidates signature"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()
        signature, timestamp = WebhookSigner.sign_payload(payload, secret)

        # Use different timestamp for verification
        wrong_timestamp = timestamp + 1

        is_valid, error = WebhookSigner.verify_signature(
            payload, signature, wrong_timestamp, secret
        )

        assert is_valid is False

    def test_replay_attack_prevention(self):
        """Test that old signatures are rejected after tolerance window"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()

        # Create signature with timestamp just outside tolerance
        old_timestamp = int(time.time()) - WebhookSigner.TIMESTAMP_TOLERANCE_SECONDS - 1
        signature, _ = WebhookSigner.sign_payload(payload, secret, old_timestamp)

        is_valid, _ = WebhookSigner.verify_signature(
            payload, signature, old_timestamp, secret
        )

        assert is_valid is False

    def test_future_timestamp_rejected(self):
        """Test that future timestamps are rejected"""
        payload = {"event": "test"}
        secret = WebhookSigner.generate_secret()

        # Create signature with future timestamp
        future_timestamp = int(time.time()) + WebhookSigner.TIMESTAMP_TOLERANCE_SECONDS + 1
        signature, _ = WebhookSigner.sign_payload(payload, secret, future_timestamp)

        is_valid, _ = WebhookSigner.verify_signature(
            payload, signature, future_timestamp, secret
        )

        assert is_valid is False


class TestCustomerVerificationCode:
    """Test that the customer verification code works correctly"""

    def test_customer_verification_function_exists(self):
        """Test that customer verification code is documented"""
        from services.webhook_signer import CUSTOMER_VERIFICATION_CODE
        assert "verify_owkai_webhook" in CUSTOMER_VERIFICATION_CODE
        assert "X-OWkai-Signature" in CUSTOMER_VERIFICATION_CODE
        assert "X-OWkai-Timestamp" in CUSTOMER_VERIFICATION_CODE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
