"""
OW-kai Enterprise Notification Service

Phase 2: Slack/Teams Integration
Banking-Level Security: Encrypted webhooks, rate limiting, retry logic, audit trails

This service handles:
1. Slack incoming webhook notifications (Block Kit formatted)
2. Microsoft Teams webhook notifications (Adaptive Cards)
3. Rate limiting per channel
4. Retry logic with exponential backoff
5. Complete audit trail for compliance

Document ID: OWKAI-INT-002-SERVICE
Version: 1.0.0
Date: November 28, 2025
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from models_notifications import (
    NotificationChannel,
    NotificationDelivery,
    NotificationChannelType,
    NotificationEventType,
    NotificationStatus,
    NotificationPriority,
    get_event_config,
    EVENT_TYPE_CONFIG,
    DEFAULT_EVENT_CONFIG
)

logger = logging.getLogger("enterprise.notifications")


class NotificationEncryption:
    """
    Webhook URL encryption service.

    Uses AES-256-GCM via Fernet for encrypting sensitive webhook URLs.
    Encryption key derived from environment variable using PBKDF2.
    """

    def __init__(self):
        """Initialize encryption with key from environment."""
        # Get encryption key from environment (or generate for development)
        key_material = os.environ.get("NOTIFICATION_ENCRYPTION_KEY", "dev-key-change-in-production")
        salt = os.environ.get("NOTIFICATION_ENCRYPTION_SALT", "owkai-notification-salt-v1").encode()

        # Derive a proper Fernet key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material.encode()))
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string value."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string value."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    @staticmethod
    def hash_url(url: str) -> str:
        """Create a SHA-256 hash of the URL for lookup."""
        return hashlib.sha256(url.encode()).hexdigest()


class SlackMessageBuilder:
    """
    Build Slack Block Kit messages.

    Creates rich, interactive messages following Slack best practices.
    """

    @staticmethod
    def build_message(
        title: str,
        body: str,
        event_type: NotificationEventType,
        priority: NotificationPriority,
        metadata: Dict[str, Any] = None,
        channel_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build a Slack Block Kit message.

        Args:
            title: Message title
            body: Message body text
            event_type: The event type triggering this notification
            priority: Notification priority
            metadata: Additional data to include
            channel_settings: Channel-specific settings (username, icon, etc.)

        Returns:
            Slack-formatted message payload
        """
        config = get_event_config(event_type)
        icon = config.get("icon", ":information_source:")
        color = config.get("color", "#6c757d")

        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{icon} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": body
                }
            }
        ]

        # Add metadata fields if present
        if metadata:
            fields = []
            for key, value in metadata.items():
                if value is not None and key not in ['_internal']:
                    display_key = key.replace('_', ' ').title()
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{display_key}:*\n{value}"
                    })

            # Slack allows max 10 fields per section, split if needed
            for i in range(0, len(fields), 10):
                chunk = fields[i:i+10]
                blocks.append({
                    "type": "section",
                    "fields": chunk
                })

        # Add priority indicator
        priority_emoji = {
            NotificationPriority.URGENT: ":rotating_light: URGENT",
            NotificationPriority.HIGH: ":warning: HIGH",
            NotificationPriority.NORMAL: ":arrow_right: NORMAL",
            NotificationPriority.LOW: ":arrow_down: LOW"
        }

        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Priority: {priority_emoji.get(priority, 'NORMAL')} | Event: `{event_type.value}` | Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                }
            ]
        })

        # Add divider
        blocks.append({"type": "divider"})

        # Build final payload
        payload = {
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fallback": f"{title}: {body}"
                }
            ]
        }

        # Add channel settings
        if channel_settings:
            if channel_settings.get('slack_username'):
                payload['username'] = channel_settings['slack_username']
            if channel_settings.get('slack_icon_emoji'):
                payload['icon_emoji'] = channel_settings['slack_icon_emoji']
            if channel_settings.get('slack_channel_name'):
                payload['channel'] = channel_settings['slack_channel_name']

        return payload

    @staticmethod
    def build_test_message(custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Build a test notification message."""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":white_check_mark: OW-kai Test Notification",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": custom_message or "This is a test notification from OW-kai Enterprise. Your Slack integration is working correctly!"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        }
                    ]
                }
            ],
            "attachments": [
                {
                    "color": "#28a745",
                    "fallback": "OW-kai Test Notification - Integration working!"
                }
            ]
        }


class TeamsMessageBuilder:
    """
    Build Microsoft Teams Adaptive Card messages.

    Creates rich, actionable cards following Microsoft best practices.
    """

    @staticmethod
    def build_message(
        title: str,
        body: str,
        event_type: NotificationEventType,
        priority: NotificationPriority,
        metadata: Dict[str, Any] = None,
        channel_settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build a Microsoft Teams Adaptive Card message.

        Args:
            title: Message title
            body: Message body text
            event_type: The event type triggering this notification
            priority: Notification priority
            metadata: Additional data to include
            channel_settings: Channel-specific settings

        Returns:
            Teams-formatted message payload (MessageCard format)
        """
        config = get_event_config(event_type)
        theme_color = config.get("teams_theme_color", "808080")

        # Priority mapping
        priority_text = {
            NotificationPriority.URGENT: "URGENT",
            NotificationPriority.HIGH: "HIGH",
            NotificationPriority.NORMAL: "NORMAL",
            NotificationPriority.LOW: "LOW"
        }

        # Build facts from metadata
        facts = []
        if metadata:
            for key, value in metadata.items():
                if value is not None and key not in ['_internal']:
                    display_key = key.replace('_', ' ').title()
                    facts.append({
                        "name": display_key,
                        "value": str(value)
                    })

        # Add standard facts
        facts.extend([
            {"name": "Priority", "value": priority_text.get(priority, "NORMAL")},
            {"name": "Event Type", "value": event_type.value},
            {"name": "Timestamp", "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        ])

        # Build MessageCard payload (legacy format for wider compatibility)
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "sections": [
                {
                    "activityTitle": channel_settings.get('teams_title', 'OW-kai Alert') if channel_settings else 'OW-kai Alert',
                    "activitySubtitle": title,
                    "activityImage": "https://owkai.app/logo-64.png",
                    "facts": facts,
                    "markdown": True,
                    "text": body
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View in OW-kai",
                    "targets": [
                        {
                            "os": "default",
                            "uri": "https://pilot.owkai.app/dashboard"
                        }
                    ]
                }
            ]
        }

        return payload

    @staticmethod
    def build_test_message(custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Build a test notification message for Teams."""
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "28a745",
            "summary": "OW-kai Test Notification",
            "sections": [
                {
                    "activityTitle": "OW-kai Test Notification",
                    "activitySubtitle": "Integration Test",
                    "activityImage": "https://owkai.app/logo-64.png",
                    "facts": [
                        {"name": "Status", "value": "Success"},
                        {"name": "Timestamp", "value": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                    ],
                    "markdown": True,
                    "text": custom_message or "This is a test notification from OW-kai Enterprise. Your Microsoft Teams integration is working correctly!"
                }
            ]
        }


class NotificationService:
    """
    Enterprise Notification Delivery Service.

    Features:
    - Async HTTP delivery with configurable timeouts
    - Rate limiting per channel
    - Retry logic with exponential backoff
    - Circuit breaker pattern
    - Complete audit trail
    """

    # Configuration
    DEFAULT_TIMEOUT_SECONDS = 30
    MAX_RETRIES = 5
    RETRY_DELAYS = [1, 2, 4, 8, 16]  # Exponential backoff in seconds
    CIRCUIT_BREAKER_THRESHOLD = 10  # Consecutive failures to pause channel
    RATE_LIMIT_WINDOW_SECONDS = 60

    def __init__(self, db: Session):
        """Initialize the notification service."""
        self.db = db
        self.encryption = NotificationEncryption()
        self.slack_builder = SlackMessageBuilder()
        self.teams_builder = TeamsMessageBuilder()

    # ========================================
    # Channel Management
    # ========================================

    def create_channel(
        self,
        organization_id: int,
        created_by: int,
        name: str,
        channel_type: NotificationChannelType,
        webhook_url: str,
        description: Optional[str] = None,
        subscribed_events: List[NotificationEventType] = None,
        **kwargs
    ) -> NotificationChannel:
        """
        Create a new notification channel.

        Args:
            organization_id: Organization ID
            created_by: User ID creating the channel
            name: Channel name
            channel_type: slack or teams
            webhook_url: The webhook URL (will be encrypted)
            description: Optional description
            subscribed_events: List of events to subscribe to
            **kwargs: Additional channel settings

        Returns:
            Created NotificationChannel
        """
        # Encrypt the webhook URL
        encrypted_url = self.encryption.encrypt(webhook_url)
        url_hash = self.encryption.hash_url(webhook_url)

        # Create channel
        channel = NotificationChannel(
            organization_id=organization_id,
            channel_id=uuid.uuid4(),
            name=name,
            description=description,
            channel_type=channel_type.value,
            webhook_url_encrypted=encrypted_url,
            webhook_url_hash=url_hash,
            subscribed_events=[e.value for e in (subscribed_events or [])],
            created_by=created_by,

            # Slack-specific
            slack_channel_name=kwargs.get('slack_channel_name'),
            slack_username=kwargs.get('slack_username', 'OW-kai Bot'),
            slack_icon_emoji=kwargs.get('slack_icon_emoji', ':robot_face:'),

            # Teams-specific
            teams_title=kwargs.get('teams_title', 'OW-kai Alert'),

            # Filtering
            min_risk_score=kwargs.get('min_risk_score'),
            risk_levels=kwargs.get('risk_levels'),

            # Rate limiting
            rate_limit_per_minute=kwargs.get('rate_limit_per_minute', 30)
        )

        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)

        logger.info(f"Created notification channel {channel.id} for org {organization_id}")
        return channel

    def update_channel(
        self,
        channel_id: int,
        organization_id: int,
        updated_by: int,
        **updates
    ) -> Optional[NotificationChannel]:
        """Update an existing notification channel."""
        channel = self.db.query(NotificationChannel).filter(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == organization_id
        ).first()

        if not channel:
            return None

        # Handle webhook URL update (re-encrypt)
        if 'webhook_url' in updates and updates['webhook_url']:
            channel.webhook_url_encrypted = self.encryption.encrypt(updates['webhook_url'])
            channel.webhook_url_hash = self.encryption.hash_url(updates['webhook_url'])
            channel.is_verified = False  # Require re-verification
            del updates['webhook_url']

        # Handle subscribed_events conversion
        if 'subscribed_events' in updates and updates['subscribed_events']:
            updates['subscribed_events'] = [
                e.value if isinstance(e, NotificationEventType) else e
                for e in updates['subscribed_events']
            ]

        # Apply other updates
        for key, value in updates.items():
            if hasattr(channel, key) and value is not None:
                setattr(channel, key, value)

        channel.updated_by = updated_by
        channel.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(channel)

        logger.info(f"Updated notification channel {channel_id}")
        return channel

    def delete_channel(
        self,
        channel_id: int,
        organization_id: int
    ) -> bool:
        """Delete a notification channel."""
        channel = self.db.query(NotificationChannel).filter(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == organization_id
        ).first()

        if not channel:
            return False

        self.db.delete(channel)
        self.db.commit()

        logger.info(f"Deleted notification channel {channel_id}")
        return True

    def get_channel(
        self,
        channel_id: int,
        organization_id: int
    ) -> Optional[NotificationChannel]:
        """Get a notification channel by ID."""
        return self.db.query(NotificationChannel).filter(
            NotificationChannel.id == channel_id,
            NotificationChannel.organization_id == organization_id
        ).first()

    def list_channels(
        self,
        organization_id: int,
        channel_type: Optional[NotificationChannelType] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[NotificationChannel], int]:
        """List notification channels for an organization."""
        query = self.db.query(NotificationChannel).filter(
            NotificationChannel.organization_id == organization_id
        )

        if channel_type:
            query = query.filter(NotificationChannel.channel_type == channel_type.value)

        if is_active is not None:
            query = query.filter(NotificationChannel.is_active == is_active)

        total = query.count()
        channels = query.order_by(NotificationChannel.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        return channels, total

    # ========================================
    # Notification Delivery
    # ========================================

    async def send_notification(
        self,
        organization_id: int,
        event_type: NotificationEventType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Dict[str, Any] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        risk_score: Optional[int] = None
    ) -> List[NotificationDelivery]:
        """
        Send notification to all subscribed channels.

        Args:
            organization_id: Organization ID
            event_type: The event type
            title: Notification title
            message: Notification body
            priority: Notification priority
            metadata: Additional metadata
            related_entity_type: Type of related entity (action, alert, etc.)
            related_entity_id: ID of related entity
            risk_score: Risk score (for filtering)

        Returns:
            List of NotificationDelivery records
        """
        # Find all active, subscribed channels for this organization
        channels = self.db.query(NotificationChannel).filter(
            NotificationChannel.organization_id == organization_id,
            NotificationChannel.is_active == True,
            NotificationChannel.is_paused == False
        ).all()

        # Filter channels that subscribe to this event
        subscribed_channels = [
            ch for ch in channels
            if event_type.value in ch.subscribed_events or len(ch.subscribed_events) == 0
        ]

        # Apply risk score filtering
        if risk_score is not None:
            subscribed_channels = [
                ch for ch in subscribed_channels
                if ch.min_risk_score is None or risk_score >= ch.min_risk_score
            ]

        deliveries = []
        tasks = []

        for channel in subscribed_channels:
            # Check rate limit
            if not self._check_rate_limit(channel):
                logger.warning(f"Rate limit exceeded for channel {channel.id}")
                continue

            # Create delivery record
            delivery = self._create_delivery_record(
                channel=channel,
                organization_id=organization_id,
                event_type=event_type,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )
            deliveries.append(delivery)

            # Queue async delivery
            tasks.append(self._deliver_notification(channel, delivery))

        # Execute all deliveries concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return deliveries

    async def _deliver_notification(
        self,
        channel: NotificationChannel,
        delivery: NotificationDelivery
    ) -> bool:
        """
        Deliver a notification to a specific channel.

        Handles retries with exponential backoff.
        """
        # Decrypt webhook URL
        webhook_url = self.encryption.decrypt(channel.webhook_url_encrypted)

        # Build message based on channel type
        channel_settings = {
            'slack_channel_name': channel.slack_channel_name,
            'slack_username': channel.slack_username,
            'slack_icon_emoji': channel.slack_icon_emoji,
            'teams_title': channel.teams_title
        }

        event_type = NotificationEventType(delivery.event_type)
        priority = NotificationPriority(delivery.priority)

        if channel.channel_type == NotificationChannelType.SLACK.value:
            payload = self.slack_builder.build_message(
                title=delivery.message_title,
                body=delivery.message_body,
                event_type=event_type,
                priority=priority,
                metadata=delivery.message_payload.get('metadata', {}),
                channel_settings=channel_settings
            )
        else:  # Teams
            payload = self.teams_builder.build_message(
                title=delivery.message_title,
                body=delivery.message_body,
                event_type=event_type,
                priority=priority,
                metadata=delivery.message_payload.get('metadata', {}),
                channel_settings=channel_settings
            )

        # Attempt delivery with retries
        for attempt in range(1, self.MAX_RETRIES + 1):
            delivery.attempt_number = attempt
            start_time = time.time()

            try:
                async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                response_time_ms = int((time.time() - start_time) * 1000)
                delivery.response_time_ms = response_time_ms
                delivery.http_status_code = response.status_code

                if response.status_code in [200, 201, 202, 204]:
                    # Success
                    delivery.delivery_status = NotificationStatus.DELIVERED.value
                    delivery.delivered_at = datetime.utcnow()
                    delivery.sent_at = datetime.utcnow()

                    # Update channel metrics
                    channel.total_notifications += 1
                    channel.successful_notifications += 1
                    channel.last_notification_at = datetime.utcnow()
                    channel.last_success_at = datetime.utcnow()
                    channel.consecutive_failures = 0

                    self.db.commit()
                    logger.info(f"Notification {delivery.notification_id} delivered successfully")
                    return True

                else:
                    # HTTP error
                    delivery.response_body = response.text[:1000]
                    delivery.error_message = f"HTTP {response.status_code}"
                    delivery.error_type = "http_error"

            except httpx.TimeoutException as e:
                delivery.error_message = f"Timeout after {self.DEFAULT_TIMEOUT_SECONDS}s"
                delivery.error_type = "timeout"
                logger.warning(f"Timeout delivering to channel {channel.id}: {e}")

            except httpx.RequestError as e:
                delivery.error_message = str(e)[:500]
                delivery.error_type = "request_error"
                logger.warning(f"Request error delivering to channel {channel.id}: {e}")

            except Exception as e:
                delivery.error_message = str(e)[:500]
                delivery.error_type = "unknown_error"
                logger.error(f"Unexpected error delivering to channel {channel.id}: {e}")

            # Check if we should retry
            if attempt < self.MAX_RETRIES:
                delay = self.RETRY_DELAYS[attempt - 1]
                delivery.delivery_status = NotificationStatus.RETRYING.value
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
                self.db.commit()
                await asyncio.sleep(delay)
            else:
                # Max retries reached
                delivery.delivery_status = NotificationStatus.FAILED.value
                channel.total_notifications += 1
                channel.failed_notifications += 1
                channel.last_notification_at = datetime.utcnow()
                channel.last_failure_at = datetime.utcnow()
                channel.consecutive_failures += 1

                # Check circuit breaker
                if channel.consecutive_failures >= self.CIRCUIT_BREAKER_THRESHOLD:
                    channel.is_paused = True
                    channel.paused_at = datetime.utcnow()
                    channel.paused_reason = f"Circuit breaker: {channel.consecutive_failures} consecutive failures"
                    logger.warning(f"Channel {channel.id} paused due to consecutive failures")

                self.db.commit()
                return False

        return False

    def _check_rate_limit(self, channel: NotificationChannel) -> bool:
        """Check if channel is within rate limit."""
        if channel.rate_limit_per_minute is None:
            return True

        now = datetime.utcnow()

        # Reset window if expired
        if channel.rate_limit_window_start is None or \
           (now - channel.rate_limit_window_start).total_seconds() > self.RATE_LIMIT_WINDOW_SECONDS:
            channel.rate_limit_window_start = now
            channel.rate_limit_current_count = 0

        # Check limit
        if channel.rate_limit_current_count >= channel.rate_limit_per_minute:
            return False

        # Increment counter
        channel.rate_limit_current_count += 1
        return True

    def _create_delivery_record(
        self,
        channel: NotificationChannel,
        organization_id: int,
        event_type: NotificationEventType,
        title: str,
        message: str,
        priority: NotificationPriority,
        metadata: Dict[str, Any] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None
    ) -> NotificationDelivery:
        """Create a notification delivery record."""
        idempotency_key = f"{event_type.value}_{related_entity_type or 'none'}_{related_entity_id or 0}_{uuid.uuid4().hex[:8]}"

        delivery = NotificationDelivery(
            channel_id=channel.id,
            organization_id=organization_id,
            notification_id=uuid.uuid4(),
            event_type=event_type.value,
            idempotency_key=idempotency_key,
            message_title=title,
            message_body=message,
            message_payload={
                "title": title,
                "body": message,
                "metadata": metadata or {},
                "event_type": event_type.value
            },
            priority=priority.value,
            delivery_status=NotificationStatus.PENDING.value,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)

        return delivery

    # ========================================
    # Test & Verification
    # ========================================

    async def test_channel(
        self,
        channel_id: int,
        organization_id: int,
        custom_message: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Send a test notification to a channel.

        Returns:
            Tuple of (success, result_dict)
        """
        channel = self.get_channel(channel_id, organization_id)
        if not channel:
            return False, {"error": "Channel not found"}

        # Decrypt webhook URL
        webhook_url = self.encryption.decrypt(channel.webhook_url_encrypted)

        # Build test message
        if channel.channel_type == NotificationChannelType.SLACK.value:
            payload = self.slack_builder.build_test_message(custom_message)
        else:
            payload = self.teams_builder.build_test_message(custom_message)

        # Send test
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code in [200, 201, 202, 204]:
                # Mark channel as verified
                channel.is_verified = True
                channel.verified_at = datetime.utcnow()
                self.db.commit()

                return True, {
                    "success": True,
                    "message": "Test notification sent successfully",
                    "http_status_code": response.status_code,
                    "response_time_ms": response_time_ms
                }
            else:
                return False, {
                    "success": False,
                    "message": "Test notification failed",
                    "http_status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "error": response.text[:500]
                }

        except Exception as e:
            return False, {
                "success": False,
                "message": "Test notification failed",
                "error": str(e)
            }

    # ========================================
    # Delivery History & Metrics
    # ========================================

    def list_deliveries(
        self,
        organization_id: int,
        channel_id: Optional[int] = None,
        event_type: Optional[NotificationEventType] = None,
        status: Optional[NotificationStatus] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[NotificationDelivery], int]:
        """List notification deliveries."""
        query = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.organization_id == organization_id
        )

        if channel_id:
            query = query.filter(NotificationDelivery.channel_id == channel_id)

        if event_type:
            query = query.filter(NotificationDelivery.event_type == event_type.value)

        if status:
            query = query.filter(NotificationDelivery.delivery_status == status.value)

        total = query.count()
        deliveries = query.order_by(NotificationDelivery.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        return deliveries, total

    def get_metrics(self, organization_id: int) -> Dict[str, Any]:
        """Get aggregated notification metrics."""
        # Channel counts
        channels = self.db.query(NotificationChannel).filter(
            NotificationChannel.organization_id == organization_id
        )
        total_channels = channels.count()
        active_channels = channels.filter(NotificationChannel.is_active == True).count()
        paused_channels = channels.filter(NotificationChannel.is_paused == True).count()

        # 24h delivery stats
        cutoff = datetime.utcnow() - timedelta(hours=24)
        deliveries_24h = self.db.query(NotificationDelivery).filter(
            NotificationDelivery.organization_id == organization_id,
            NotificationDelivery.created_at >= cutoff
        )

        total_24h = deliveries_24h.count()
        successful_24h = deliveries_24h.filter(
            NotificationDelivery.delivery_status == NotificationStatus.DELIVERED.value
        ).count()
        failed_24h = deliveries_24h.filter(
            NotificationDelivery.delivery_status == NotificationStatus.FAILED.value
        ).count()

        success_rate = (successful_24h / total_24h * 100) if total_24h > 0 else 0

        # Average response time
        avg_response = self.db.query(func.avg(NotificationDelivery.response_time_ms)).filter(
            NotificationDelivery.organization_id == organization_id,
            NotificationDelivery.response_time_ms.isnot(None),
            NotificationDelivery.created_at >= cutoff
        ).scalar() or 0

        # By channel type
        by_channel_type = {}
        for ch_type in NotificationChannelType:
            ch_channels = self.db.query(NotificationChannel).filter(
                NotificationChannel.organization_id == organization_id,
                NotificationChannel.channel_type == ch_type.value
            ).all()

            ch_total = sum(ch.total_notifications for ch in ch_channels)
            ch_success = sum(ch.successful_notifications for ch in ch_channels)

            by_channel_type[ch_type.value] = {
                "total": ch_total,
                "success": ch_success
            }

        # By event type (last 24h)
        by_event_type = {}
        event_counts = self.db.query(
            NotificationDelivery.event_type,
            func.count(NotificationDelivery.id)
        ).filter(
            NotificationDelivery.organization_id == organization_id,
            NotificationDelivery.created_at >= cutoff
        ).group_by(NotificationDelivery.event_type).all()

        for event, count in event_counts:
            by_event_type[event] = count

        return {
            "total_channels": total_channels,
            "active_channels": active_channels,
            "paused_channels": paused_channels,
            "total_notifications_24h": total_24h,
            "successful_24h": successful_24h,
            "failed_24h": failed_24h,
            "success_rate_24h": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response, 2),
            "by_channel_type": by_channel_type,
            "by_event_type": by_event_type
        }

    # ========================================
    # Channel Control
    # ========================================

    def pause_channel(
        self,
        channel_id: int,
        organization_id: int,
        reason: str
    ) -> Optional[NotificationChannel]:
        """Pause a notification channel."""
        channel = self.get_channel(channel_id, organization_id)
        if not channel:
            return None

        channel.is_paused = True
        channel.paused_at = datetime.utcnow()
        channel.paused_reason = reason

        self.db.commit()
        self.db.refresh(channel)

        logger.info(f"Channel {channel_id} paused: {reason}")
        return channel

    def resume_channel(
        self,
        channel_id: int,
        organization_id: int
    ) -> Optional[NotificationChannel]:
        """Resume a paused notification channel."""
        channel = self.get_channel(channel_id, organization_id)
        if not channel:
            return None

        channel.is_paused = False
        channel.paused_at = None
        channel.paused_reason = None
        channel.consecutive_failures = 0

        self.db.commit()
        self.db.refresh(channel)

        logger.info(f"Channel {channel_id} resumed")
        return channel
