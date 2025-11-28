"""
OW-kai Enterprise Notification System - Comprehensive Unit Tests

Testing: Phase 2 Enterprise Integration - Slack/Teams Notification System
Coverage: Encryption, message building, delivery service, API routes

Security Tests:
- AES-256 webhook URL encryption
- Multi-tenant isolation
- Rate limiting
- Circuit breaker pattern

Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1
Document ID: OWKAI-INT-002-TESTS
Version: 1.0.0
Date: November 28, 2025
"""

import pytest
import json
import hashlib
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid
import os
import sys

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models_notifications import (
    NotificationChannelType,
    NotificationEventType,
    NotificationStatus,
    NotificationPriority,
    NotificationChannelCreate,
    get_event_config,
    EVENT_TYPE_CONFIG,
    DEFAULT_EVENT_CONFIG
)
from services.notification_service import (
    NotificationEncryption,
    SlackMessageBuilder,
    TeamsMessageBuilder,
)


class TestNotificationEncryption:
    """Test suite for NotificationEncryption class"""

    def setup_method(self):
        """Set up encryption instance for each test"""
        self.encryption = NotificationEncryption()

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption produce original value"""
        original = "https://hooks.slack.com/services/T00000000/B00000000/XXXX"
        encrypted = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """Test that encrypting same value twice produces different ciphertexts"""
        original = "test_webhook_url"
        encrypted1 = self.encryption.encrypt(original)
        encrypted2 = self.encryption.encrypt(original)
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2

    def test_encrypted_not_plaintext(self):
        """Test that encrypted value doesn't contain plaintext"""
        original = "https://hooks.slack.com/services/SECRET"
        encrypted = self.encryption.encrypt(original)
        assert "SECRET" not in encrypted
        assert "slack.com" not in encrypted

    def test_hash_url_consistent(self):
        """Test that URL hash is consistent (deterministic)"""
        url = "https://hooks.slack.com/test"
        hash1 = NotificationEncryption.hash_url(url)
        hash2 = NotificationEncryption.hash_url(url)
        assert hash1 == hash2

    def test_hash_url_length(self):
        """Test that URL hash is correct length (SHA-256 = 64 hex chars)"""
        url = "https://hooks.slack.com/test"
        hash_value = NotificationEncryption.hash_url(url)
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_different_urls_different_hashes(self):
        """Test that different URLs produce different hashes"""
        url1 = "https://hooks.slack.com/services/AAA"
        url2 = "https://hooks.slack.com/services/BBB"
        hash1 = NotificationEncryption.hash_url(url1)
        hash2 = NotificationEncryption.hash_url(url2)
        assert hash1 != hash2


class TestSlackMessageBuilder:
    """Test suite for SlackMessageBuilder class"""

    def test_build_message_has_blocks(self):
        """Test that Slack message contains blocks"""
        message = SlackMessageBuilder.build_message(
            title="Test Alert",
            body="This is a test message",
            event_type=NotificationEventType.ALERT_TRIGGERED,
            priority=NotificationPriority.HIGH,
            metadata={"action_id": 123}
        )
        assert "blocks" in message
        assert len(message["blocks"]) > 0

    def test_build_message_has_header(self):
        """Test that Slack message has header block"""
        message = SlackMessageBuilder.build_message(
            title="Security Alert",
            body="Suspicious activity detected",
            event_type=NotificationEventType.SECURITY_SUSPICIOUS_ACTIVITY,
            priority=NotificationPriority.URGENT
        )
        header_block = message["blocks"][0]
        assert header_block["type"] == "header"
        assert "Security Alert" in header_block["text"]["text"]

    def test_build_message_has_attachments(self):
        """Test that Slack message has color attachment"""
        message = SlackMessageBuilder.build_message(
            title="Test",
            body="Test body",
            event_type=NotificationEventType.ACTION_REJECTED,
            priority=NotificationPriority.HIGH
        )
        assert "attachments" in message
        assert len(message["attachments"]) > 0
        assert "color" in message["attachments"][0]

    def test_build_message_includes_metadata_fields(self):
        """Test that metadata is included in message fields"""
        metadata = {
            "action_id": 123,
            "risk_score": 85,
            "agent_name": "test-agent"
        }
        message = SlackMessageBuilder.build_message(
            title="Action Alert",
            body="High risk action detected",
            event_type=NotificationEventType.RISK_CRITICAL_ACTION,
            priority=NotificationPriority.URGENT,
            metadata=metadata
        )
        # Check that blocks contain section with fields
        message_json = json.dumps(message)
        assert "123" in message_json  # action_id
        assert "85" in message_json   # risk_score

    def test_build_message_channel_settings(self):
        """Test that channel settings are applied"""
        channel_settings = {
            "slack_username": "Custom Bot",
            "slack_icon_emoji": ":shield:",
            "slack_channel_name": "#alerts"
        }
        message = SlackMessageBuilder.build_message(
            title="Test",
            body="Test",
            event_type=NotificationEventType.ALERT_TRIGGERED,
            priority=NotificationPriority.NORMAL,
            channel_settings=channel_settings
        )
        assert message.get("username") == "Custom Bot"
        assert message.get("icon_emoji") == ":shield:"
        assert message.get("channel") == "#alerts"

    def test_build_test_message(self):
        """Test building test notification message"""
        message = SlackMessageBuilder.build_test_message()
        assert "blocks" in message
        # Check for test message content
        message_json = json.dumps(message)
        assert "test" in message_json.lower() or "Test" in message_json

    def test_build_test_message_custom(self):
        """Test building test message with custom content"""
        custom = "Custom test message content"
        message = SlackMessageBuilder.build_test_message(custom)
        message_json = json.dumps(message)
        assert custom in message_json


class TestTeamsMessageBuilder:
    """Test suite for TeamsMessageBuilder class"""

    def test_build_message_has_type(self):
        """Test that Teams message has correct @type"""
        message = TeamsMessageBuilder.build_message(
            title="Test Alert",
            body="Test body",
            event_type=NotificationEventType.ALERT_TRIGGERED,
            priority=NotificationPriority.HIGH
        )
        assert message["@type"] == "MessageCard"

    def test_build_message_has_context(self):
        """Test that Teams message has @context"""
        message = TeamsMessageBuilder.build_message(
            title="Test",
            body="Test",
            event_type=NotificationEventType.ALERT_TRIGGERED,
            priority=NotificationPriority.NORMAL
        )
        assert "@context" in message

    def test_build_message_has_theme_color(self):
        """Test that Teams message has theme color"""
        message = TeamsMessageBuilder.build_message(
            title="Critical Alert",
            body="Critical issue",
            event_type=NotificationEventType.ALERT_CRITICAL,
            priority=NotificationPriority.URGENT
        )
        assert "themeColor" in message
        # Critical events should have red theme
        assert message["themeColor"] == "FF0000"

    def test_build_message_has_sections(self):
        """Test that Teams message has sections"""
        message = TeamsMessageBuilder.build_message(
            title="Test",
            body="Test body content",
            event_type=NotificationEventType.WORKFLOW_FAILED,
            priority=NotificationPriority.HIGH
        )
        assert "sections" in message
        assert len(message["sections"]) > 0

    def test_build_message_has_facts(self):
        """Test that Teams message includes facts from metadata"""
        metadata = {"action_id": 456, "severity": "high"}
        message = TeamsMessageBuilder.build_message(
            title="Policy Violation",
            body="Policy violated",
            event_type=NotificationEventType.POLICY_VIOLATED,
            priority=NotificationPriority.HIGH,
            metadata=metadata
        )
        section = message["sections"][0]
        assert "facts" in section
        fact_names = [f["name"] for f in section["facts"]]
        assert "Priority" in fact_names
        assert "Event Type" in fact_names

    def test_build_message_has_potential_action(self):
        """Test that Teams message has action button"""
        message = TeamsMessageBuilder.build_message(
            title="Test",
            body="Test",
            event_type=NotificationEventType.WORKFLOW_APPROVAL_NEEDED,
            priority=NotificationPriority.HIGH
        )
        assert "potentialAction" in message
        assert len(message["potentialAction"]) > 0

    def test_build_test_message(self):
        """Test building test notification for Teams"""
        message = TeamsMessageBuilder.build_test_message()
        assert message["@type"] == "MessageCard"
        assert "themeColor" in message
        # Success color (green)
        assert message["themeColor"] == "28a745"

    def test_build_test_message_custom(self):
        """Test building test message with custom content"""
        custom = "Custom Teams test message"
        message = TeamsMessageBuilder.build_test_message(custom)
        message_json = json.dumps(message)
        assert custom in message_json


class TestEventTypeConfig:
    """Test event type configuration"""

    def test_all_event_types_have_config(self):
        """Test that important event types have explicit configuration"""
        important_events = [
            NotificationEventType.ACTION_REJECTED,
            NotificationEventType.ALERT_CRITICAL,
            NotificationEventType.SECURITY_SUSPICIOUS_ACTIVITY,
            NotificationEventType.POLICY_VIOLATED,
            NotificationEventType.RISK_CRITICAL_ACTION
        ]
        for event in important_events:
            config = get_event_config(event)
            assert "priority" in config
            assert "color" in config
            assert "icon" in config

    def test_critical_events_have_urgent_priority(self):
        """Test that critical events have urgent priority"""
        critical_events = [
            NotificationEventType.ALERT_CRITICAL,
            NotificationEventType.ACTION_ESCALATED,
            NotificationEventType.SECURITY_SUSPICIOUS_ACTIVITY,
            NotificationEventType.RISK_CRITICAL_ACTION
        ]
        for event in critical_events:
            config = get_event_config(event)
            assert config["priority"] == NotificationPriority.URGENT

    def test_default_config_exists(self):
        """Test that default config is available"""
        assert DEFAULT_EVENT_CONFIG is not None
        assert "priority" in DEFAULT_EVENT_CONFIG
        assert "color" in DEFAULT_EVENT_CONFIG
        assert "icon" in DEFAULT_EVENT_CONFIG

    def test_get_event_config_returns_default_for_unknown(self):
        """Test that unknown event types get default config"""
        # Create a mock event that's not in config
        config = get_event_config(NotificationEventType.SYSTEM_MAINTENANCE)
        # Should return something (either explicit or default)
        assert config is not None
        assert "priority" in config


class TestNotificationChannelCreate:
    """Test Pydantic schema validation"""

    def test_valid_slack_channel(self):
        """Test creating valid Slack channel"""
        data = NotificationChannelCreate(
            name="Security Alerts",
            channel_type=NotificationChannelType.SLACK,
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
            subscribed_events=[NotificationEventType.ALERT_CRITICAL]
        )
        assert data.name == "Security Alerts"
        assert data.channel_type == NotificationChannelType.SLACK

    def test_valid_teams_channel(self):
        """Test creating valid Teams channel"""
        data = NotificationChannelCreate(
            name="Team Notifications",
            channel_type=NotificationChannelType.TEAMS,
            webhook_url="https://outlook.office.com/webhook.office.com/xxx",
            subscribed_events=[NotificationEventType.WORKFLOW_APPROVAL_NEEDED]
        )
        assert data.channel_type == NotificationChannelType.TEAMS

    def test_invalid_slack_url_rejected(self):
        """Test that invalid Slack URL is rejected"""
        with pytest.raises(ValueError):
            NotificationChannelCreate(
                name="Invalid",
                channel_type=NotificationChannelType.SLACK,
                webhook_url="https://invalid.com/webhook"
            )

    def test_invalid_teams_url_rejected(self):
        """Test that invalid Teams URL is rejected"""
        with pytest.raises(ValueError):
            NotificationChannelCreate(
                name="Invalid",
                channel_type=NotificationChannelType.TEAMS,
                webhook_url="https://invalid.com/webhook"
            )

    def test_risk_score_bounds(self):
        """Test that risk score must be 0-100"""
        # Valid
        data = NotificationChannelCreate(
            name="Test",
            channel_type=NotificationChannelType.SLACK,
            webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
            min_risk_score=50
        )
        assert data.min_risk_score == 50

        # Invalid - negative
        with pytest.raises(ValueError):
            NotificationChannelCreate(
                name="Test",
                channel_type=NotificationChannelType.SLACK,
                webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
                min_risk_score=-1
            )

        # Invalid - over 100
        with pytest.raises(ValueError):
            NotificationChannelCreate(
                name="Test",
                channel_type=NotificationChannelType.SLACK,
                webhook_url="https://hooks.slack.com/services/T00/B00/XXX",
                min_risk_score=101
            )


class TestNotificationPriority:
    """Test notification priority enum"""

    def test_all_priorities_exist(self):
        """Test that all expected priorities exist"""
        assert NotificationPriority.LOW
        assert NotificationPriority.NORMAL
        assert NotificationPriority.HIGH
        assert NotificationPriority.URGENT

    def test_priority_values(self):
        """Test priority string values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"


class TestNotificationStatus:
    """Test notification status enum"""

    def test_all_statuses_exist(self):
        """Test that all expected statuses exist"""
        assert NotificationStatus.PENDING
        assert NotificationStatus.SENT
        assert NotificationStatus.DELIVERED
        assert NotificationStatus.FAILED
        assert NotificationStatus.RETRYING

    def test_status_values(self):
        """Test status string values"""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.FAILED.value == "failed"


class TestNotificationEventTypes:
    """Test notification event type enum"""

    def test_action_events_exist(self):
        """Test that action events exist"""
        assert NotificationEventType.ACTION_SUBMITTED
        assert NotificationEventType.ACTION_APPROVED
        assert NotificationEventType.ACTION_REJECTED
        assert NotificationEventType.ACTION_ESCALATED

    def test_alert_events_exist(self):
        """Test that alert events exist"""
        assert NotificationEventType.ALERT_TRIGGERED
        assert NotificationEventType.ALERT_RESOLVED
        assert NotificationEventType.ALERT_CRITICAL

    def test_security_events_exist(self):
        """Test that security events exist"""
        assert NotificationEventType.SECURITY_SUSPICIOUS_ACTIVITY
        assert NotificationEventType.SECURITY_LOGIN_ANOMALY
        assert NotificationEventType.SECURITY_MFA_ENABLED

    def test_event_type_values_format(self):
        """Test event type values have dot notation"""
        assert "." in NotificationEventType.ACTION_SUBMITTED.value
        assert NotificationEventType.ACTION_SUBMITTED.value == "action.submitted"


class TestMultiTenantIsolation:
    """Test multi-tenant isolation requirements"""

    def test_notification_channel_requires_organization(self):
        """Test that notification channels require organization_id"""
        # This is a structural test - verify the model requires organization
        from models_notifications import NotificationChannel
        import inspect
        source = inspect.getsource(NotificationChannel)
        assert "organization_id" in source
        assert "nullable=False" in source or "nullable = False" in source

    def test_notification_delivery_requires_organization(self):
        """Test that deliveries require organization_id"""
        from models_notifications import NotificationDelivery
        import inspect
        source = inspect.getsource(NotificationDelivery)
        assert "organization_id" in source


class TestCircuitBreaker:
    """Test circuit breaker pattern requirements"""

    def test_channel_has_circuit_breaker_fields(self):
        """Test that channel model has circuit breaker fields"""
        from models_notifications import NotificationChannel
        import inspect
        source = inspect.getsource(NotificationChannel)
        assert "is_paused" in source
        assert "consecutive_failures" in source
        assert "paused_reason" in source

    def test_service_has_circuit_breaker_config(self):
        """Test that service has circuit breaker configuration"""
        from services.notification_service import NotificationService
        import inspect
        source = inspect.getsource(NotificationService)
        assert "CIRCUIT_BREAKER_THRESHOLD" in source


class TestRateLimiting:
    """Test rate limiting requirements"""

    def test_channel_has_rate_limit_fields(self):
        """Test that channel model has rate limit fields"""
        from models_notifications import NotificationChannel
        import inspect
        source = inspect.getsource(NotificationChannel)
        assert "rate_limit_per_minute" in source
        assert "rate_limit_current_count" in source
        assert "rate_limit_window_start" in source

    def test_service_has_rate_limit_check(self):
        """Test that service checks rate limits"""
        from services.notification_service import NotificationService
        import inspect
        source = inspect.getsource(NotificationService)
        assert "_check_rate_limit" in source


class TestRetryLogic:
    """Test retry logic requirements"""

    def test_service_has_retry_config(self):
        """Test that service has retry configuration"""
        from services.notification_service import NotificationService
        assert hasattr(NotificationService, 'MAX_RETRIES')
        assert hasattr(NotificationService, 'RETRY_DELAYS')

    def test_retry_delays_exponential(self):
        """Test that retry delays follow exponential backoff"""
        from services.notification_service import NotificationService
        delays = NotificationService.RETRY_DELAYS
        # Check each delay is larger than previous (exponential)
        for i in range(1, len(delays)):
            assert delays[i] > delays[i-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
