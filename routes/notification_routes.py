"""
OW-kai Enterprise Notification API Routes

Phase 2: Slack/Teams Integration REST API
Endpoints for managing notification channels (Slack/Teams) and viewing delivery history.

Document ID: OWKAI-INT-002-ROUTES
Version: 1.0.0
Date: November 28, 2025
Compliance: SOC 2 CC6.1, Multi-tenant Isolation
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from database import get_db
from dependencies import get_current_user
from models_notifications import (
    NotificationChannelType,
    NotificationEventType,
    NotificationStatus,
    NotificationPriority,
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationChannelResponse,
    NotificationChannelListResponse,
    NotificationDeliveryResponse,
    NotificationDeliveryListResponse,
    NotificationMetricsResponse,
    NotificationTestRequest,
    NotificationTestResponse,
    NotificationSendRequest
)
from services.notification_service import NotificationService

logger = logging.getLogger("enterprise.notifications.routes")

router = APIRouter(prefix="/api/notifications", tags=["Enterprise Notifications"])


# ============================================
# Event Types Discovery
# ============================================

@router.get("/events", summary="List available notification event types")
async def list_event_types():
    """
    List all available notification event types.

    Returns categorized event types that can be subscribed to for notifications.
    """
    events = {
        "action_events": [
            {"type": "action.submitted", "description": "When a new action is submitted for approval"},
            {"type": "action.approved", "description": "When an action is approved"},
            {"type": "action.rejected", "description": "When an action is rejected"},
            {"type": "action.escalated", "description": "When an action is escalated"},
            {"type": "action.pending_approval", "description": "When an action requires approval"}
        ],
        "alert_events": [
            {"type": "alert.triggered", "description": "When a new alert is triggered"},
            {"type": "alert.resolved", "description": "When an alert is resolved"},
            {"type": "alert.acknowledged", "description": "When an alert is acknowledged"},
            {"type": "alert.critical", "description": "When a critical severity alert occurs"}
        ],
        "policy_events": [
            {"type": "policy.violated", "description": "When a policy violation occurs"},
            {"type": "policy.created", "description": "When a new policy is created"},
            {"type": "policy.updated", "description": "When a policy is updated"}
        ],
        "workflow_events": [
            {"type": "workflow.started", "description": "When a workflow starts"},
            {"type": "workflow.completed", "description": "When a workflow completes"},
            {"type": "workflow.failed", "description": "When a workflow fails"},
            {"type": "workflow.timeout", "description": "When a workflow times out"},
            {"type": "workflow.approval_needed", "description": "When workflow requires approval"}
        ],
        "security_events": [
            {"type": "security.mfa_enabled", "description": "When MFA is enabled for a user"},
            {"type": "security.suspicious_activity", "description": "When suspicious activity is detected"},
            {"type": "security.login_anomaly", "description": "When a login anomaly is detected"}
        ],
        "risk_events": [
            {"type": "risk.threshold_exceeded", "description": "When risk threshold is exceeded"},
            {"type": "risk.critical_action", "description": "When a critical risk action is detected"}
        ],
        "system_events": [
            {"type": "system.health_warning", "description": "When system health warning occurs"},
            {"type": "system.maintenance", "description": "When system maintenance is scheduled"}
        ]
    }

    return {
        "events": events,
        "total_event_types": sum(len(v) for v in events.values())
    }


# ============================================
# Channel Management Endpoints
# ============================================

@router.post(
    "/channels",
    response_model=NotificationChannelResponse,
    status_code=201,
    summary="Create a notification channel"
)
async def create_channel(
    channel_data: NotificationChannelCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new notification channel (Slack or Teams).

    **Security:**
    - Webhook URL is encrypted at rest using AES-256
    - Multi-tenant isolation: channel belongs to user's organization

    **Slack Configuration:**
    - webhook_url: Your Slack incoming webhook URL
    - slack_channel_name: Override channel (optional)
    - slack_username: Bot display name (default: "OW-kai Bot")
    - slack_icon_emoji: Bot icon (default: ":robot_face:")

    **Teams Configuration:**
    - webhook_url: Your Teams incoming webhook URL
    - teams_title: Card title (default: "OW-kai Alert")
    """
    service = NotificationService(db)

    # Validate user has an organization
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    try:
        channel = service.create_channel(
            organization_id=current_user["organization_id"],
            created_by=current_user["user_id"],
            name=channel_data.name,
            channel_type=channel_data.channel_type,
            webhook_url=channel_data.webhook_url,
            description=channel_data.description,
            subscribed_events=channel_data.subscribed_events,
            slack_channel_name=channel_data.slack_channel_name,
            slack_username=channel_data.slack_username,
            slack_icon_emoji=channel_data.slack_icon_emoji,
            teams_title=channel_data.teams_title,
            min_risk_score=channel_data.min_risk_score,
            risk_levels=channel_data.risk_levels,
            rate_limit_per_minute=channel_data.rate_limit_per_minute
        )

        logger.info(f"Created notification channel {channel.id} for org {current_user['organization_id']}")

        return NotificationChannelResponse(
            id=channel.id,
            channel_id=str(channel.channel_id),
            name=channel.name,
            description=channel.description,
            channel_type=channel.channel_type,
            slack_channel_name=channel.slack_channel_name,
            slack_username=channel.slack_username,
            slack_icon_emoji=channel.slack_icon_emoji,
            teams_title=channel.teams_title,
            subscribed_events=channel.subscribed_events,
            min_risk_score=channel.min_risk_score,
            risk_levels=channel.risk_levels,
            rate_limit_per_minute=channel.rate_limit_per_minute,
            is_active=channel.is_active,
            is_verified=channel.is_verified,
            verified_at=channel.verified_at,
            total_notifications=channel.total_notifications,
            successful_notifications=channel.successful_notifications,
            failed_notifications=channel.failed_notifications,
            last_notification_at=channel.last_notification_at,
            consecutive_failures=channel.consecutive_failures,
            is_paused=channel.is_paused,
            paused_reason=channel.paused_reason,
            created_at=channel.created_at,
            updated_at=channel.updated_at
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/channels",
    response_model=NotificationChannelListResponse,
    summary="List notification channels"
)
async def list_channels(
    channel_type: Optional[NotificationChannelType] = Query(None, description="Filter by channel type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all notification channels for the current organization.

    Supports filtering by channel type (slack/teams) and active status.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    channels, total = service.list_channels(
        organization_id=current_user["organization_id"],
        channel_type=channel_type,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

    return NotificationChannelListResponse(
        channels=[
            NotificationChannelResponse(
                id=ch.id,
                channel_id=str(ch.channel_id),
                name=ch.name,
                description=ch.description,
                channel_type=ch.channel_type,
                slack_channel_name=ch.slack_channel_name,
                slack_username=ch.slack_username,
                slack_icon_emoji=ch.slack_icon_emoji,
                teams_title=ch.teams_title,
                subscribed_events=ch.subscribed_events,
                min_risk_score=ch.min_risk_score,
                risk_levels=ch.risk_levels,
                rate_limit_per_minute=ch.rate_limit_per_minute,
                is_active=ch.is_active,
                is_verified=ch.is_verified,
                verified_at=ch.verified_at,
                total_notifications=ch.total_notifications,
                successful_notifications=ch.successful_notifications,
                failed_notifications=ch.failed_notifications,
                last_notification_at=ch.last_notification_at,
                consecutive_failures=ch.consecutive_failures,
                is_paused=ch.is_paused,
                paused_reason=ch.paused_reason,
                created_at=ch.created_at,
                updated_at=ch.updated_at
            )
            for ch in channels
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/channels/{channel_id}",
    response_model=NotificationChannelResponse,
    summary="Get channel details"
)
async def get_channel(
    channel_id: int = Path(..., description="Channel ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific notification channel.

    **Note:** Webhook URL is never returned for security reasons.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    channel = service.get_channel(channel_id, current_user["organization_id"])

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return NotificationChannelResponse(
        id=channel.id,
        channel_id=str(channel.channel_id),
        name=channel.name,
        description=channel.description,
        channel_type=channel.channel_type,
        slack_channel_name=channel.slack_channel_name,
        slack_username=channel.slack_username,
        slack_icon_emoji=channel.slack_icon_emoji,
        teams_title=channel.teams_title,
        subscribed_events=channel.subscribed_events,
        min_risk_score=channel.min_risk_score,
        risk_levels=channel.risk_levels,
        rate_limit_per_minute=channel.rate_limit_per_minute,
        is_active=channel.is_active,
        is_verified=channel.is_verified,
        verified_at=channel.verified_at,
        total_notifications=channel.total_notifications,
        successful_notifications=channel.successful_notifications,
        failed_notifications=channel.failed_notifications,
        last_notification_at=channel.last_notification_at,
        consecutive_failures=channel.consecutive_failures,
        is_paused=channel.is_paused,
        paused_reason=channel.paused_reason,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


@router.put(
    "/channels/{channel_id}",
    response_model=NotificationChannelResponse,
    summary="Update a channel"
)
async def update_channel(
    channel_id: int,
    channel_data: NotificationChannelUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a notification channel.

    If webhook_url is provided, it will be re-encrypted and the channel
    will require re-verification.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)

    # Convert Pydantic model to dict, excluding unset fields
    updates = channel_data.model_dump(exclude_unset=True)

    channel = service.update_channel(
        channel_id=channel_id,
        organization_id=current_user["organization_id"],
        updated_by=current_user["user_id"],
        **updates
    )

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return NotificationChannelResponse(
        id=channel.id,
        channel_id=str(channel.channel_id),
        name=channel.name,
        description=channel.description,
        channel_type=channel.channel_type,
        slack_channel_name=channel.slack_channel_name,
        slack_username=channel.slack_username,
        slack_icon_emoji=channel.slack_icon_emoji,
        teams_title=channel.teams_title,
        subscribed_events=channel.subscribed_events,
        min_risk_score=channel.min_risk_score,
        risk_levels=channel.risk_levels,
        rate_limit_per_minute=channel.rate_limit_per_minute,
        is_active=channel.is_active,
        is_verified=channel.is_verified,
        verified_at=channel.verified_at,
        total_notifications=channel.total_notifications,
        successful_notifications=channel.successful_notifications,
        failed_notifications=channel.failed_notifications,
        last_notification_at=channel.last_notification_at,
        consecutive_failures=channel.consecutive_failures,
        is_paused=channel.is_paused,
        paused_reason=channel.paused_reason,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


@router.delete(
    "/channels/{channel_id}",
    status_code=204,
    summary="Delete a channel"
)
async def delete_channel(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a notification channel.

    This will also delete all delivery history associated with the channel.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    success = service.delete_channel(channel_id, current_user["organization_id"])

    if not success:
        raise HTTPException(status_code=404, detail="Channel not found")

    logger.info(f"Deleted notification channel {channel_id} by user {current_user["user_id"]}")
    return None


# ============================================
# Test & Verification Endpoints
# ============================================

@router.post(
    "/channels/{channel_id}/test",
    response_model=NotificationTestResponse,
    summary="Send test notification"
)
async def test_channel(
    channel_id: int,
    test_data: Optional[NotificationTestRequest] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test notification to verify channel configuration.

    On success, the channel will be marked as verified.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)

    custom_message = test_data.message if test_data else None
    success, result = await service.test_channel(
        channel_id=channel_id,
        organization_id=current_user["organization_id"],
        custom_message=custom_message
    )

    return NotificationTestResponse(
        success=success,
        message=result.get("message", ""),
        http_status_code=result.get("http_status_code"),
        response_time_ms=result.get("response_time_ms"),
        error=result.get("error")
    )


# ============================================
# Channel Control Endpoints
# ============================================

@router.post(
    "/channels/{channel_id}/pause",
    response_model=NotificationChannelResponse,
    summary="Pause a channel"
)
async def pause_channel(
    channel_id: int,
    reason: str = Query(..., min_length=1, max_length=500, description="Reason for pausing"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pause a notification channel.

    Paused channels will not receive any notifications until resumed.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    channel = service.pause_channel(channel_id, current_user["organization_id"], reason)

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return NotificationChannelResponse(
        id=channel.id,
        channel_id=str(channel.channel_id),
        name=channel.name,
        description=channel.description,
        channel_type=channel.channel_type,
        slack_channel_name=channel.slack_channel_name,
        slack_username=channel.slack_username,
        slack_icon_emoji=channel.slack_icon_emoji,
        teams_title=channel.teams_title,
        subscribed_events=channel.subscribed_events,
        min_risk_score=channel.min_risk_score,
        risk_levels=channel.risk_levels,
        rate_limit_per_minute=channel.rate_limit_per_minute,
        is_active=channel.is_active,
        is_verified=channel.is_verified,
        verified_at=channel.verified_at,
        total_notifications=channel.total_notifications,
        successful_notifications=channel.successful_notifications,
        failed_notifications=channel.failed_notifications,
        last_notification_at=channel.last_notification_at,
        consecutive_failures=channel.consecutive_failures,
        is_paused=channel.is_paused,
        paused_reason=channel.paused_reason,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


@router.post(
    "/channels/{channel_id}/resume",
    response_model=NotificationChannelResponse,
    summary="Resume a paused channel"
)
async def resume_channel(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resume a paused notification channel.

    This also resets the consecutive failure counter.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    channel = service.resume_channel(channel_id, current_user["organization_id"])

    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return NotificationChannelResponse(
        id=channel.id,
        channel_id=str(channel.channel_id),
        name=channel.name,
        description=channel.description,
        channel_type=channel.channel_type,
        slack_channel_name=channel.slack_channel_name,
        slack_username=channel.slack_username,
        slack_icon_emoji=channel.slack_icon_emoji,
        teams_title=channel.teams_title,
        subscribed_events=channel.subscribed_events,
        min_risk_score=channel.min_risk_score,
        risk_levels=channel.risk_levels,
        rate_limit_per_minute=channel.rate_limit_per_minute,
        is_active=channel.is_active,
        is_verified=channel.is_verified,
        verified_at=channel.verified_at,
        total_notifications=channel.total_notifications,
        successful_notifications=channel.successful_notifications,
        failed_notifications=channel.failed_notifications,
        last_notification_at=channel.last_notification_at,
        consecutive_failures=channel.consecutive_failures,
        is_paused=channel.is_paused,
        paused_reason=channel.paused_reason,
        created_at=channel.created_at,
        updated_at=channel.updated_at
    )


# ============================================
# Delivery History Endpoints
# ============================================

@router.get(
    "/channels/{channel_id}/deliveries",
    response_model=NotificationDeliveryListResponse,
    summary="Get delivery history for a channel"
)
async def list_channel_deliveries(
    channel_id: int,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (pending, sent, delivered, failed)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get delivery history for a specific channel.

    Includes all notification attempts with response details.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)

    # Convert string to enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = NotificationEventType(event_type)
        except ValueError:
            pass

    status_enum = None
    if status:
        try:
            status_enum = NotificationStatus(status)
        except ValueError:
            pass

    deliveries, total = service.list_deliveries(
        organization_id=current_user["organization_id"],
        channel_id=channel_id,
        event_type=event_type_enum,
        status=status_enum,
        page=page,
        page_size=page_size
    )

    return NotificationDeliveryListResponse(
        deliveries=[
            NotificationDeliveryResponse(
                id=d.id,
                notification_id=str(d.notification_id),
                event_type=d.event_type,
                message_title=d.message_title,
                priority=d.priority,
                delivery_status=d.delivery_status,
                attempt_number=d.attempt_number,
                http_status_code=d.http_status_code,
                response_time_ms=d.response_time_ms,
                error_message=d.error_message,
                related_entity_type=d.related_entity_type,
                related_entity_id=d.related_entity_id,
                created_at=d.created_at,
                sent_at=d.sent_at,
                delivered_at=d.delivered_at
            )
            for d in deliveries
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/deliveries",
    response_model=NotificationDeliveryListResponse,
    summary="List all deliveries"
)
async def list_all_deliveries(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all notification deliveries across all channels.

    Useful for cross-channel delivery monitoring.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)

    event_type_enum = None
    if event_type:
        try:
            event_type_enum = NotificationEventType(event_type)
        except ValueError:
            pass

    status_enum = None
    if status:
        try:
            status_enum = NotificationStatus(status)
        except ValueError:
            pass

    deliveries, total = service.list_deliveries(
        organization_id=current_user["organization_id"],
        event_type=event_type_enum,
        status=status_enum,
        page=page,
        page_size=page_size
    )

    return NotificationDeliveryListResponse(
        deliveries=[
            NotificationDeliveryResponse(
                id=d.id,
                notification_id=str(d.notification_id),
                event_type=d.event_type,
                message_title=d.message_title,
                priority=d.priority,
                delivery_status=d.delivery_status,
                attempt_number=d.attempt_number,
                http_status_code=d.http_status_code,
                response_time_ms=d.response_time_ms,
                error_message=d.error_message,
                related_entity_type=d.related_entity_type,
                related_entity_id=d.related_entity_id,
                created_at=d.created_at,
                sent_at=d.sent_at,
                delivered_at=d.delivered_at
            )
            for d in deliveries
        ],
        total=total,
        page=page,
        page_size=page_size
    )


# ============================================
# Metrics Endpoint
# ============================================

@router.get(
    "/metrics",
    response_model=NotificationMetricsResponse,
    summary="Get notification metrics"
)
async def get_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated notification metrics for the organization.

    Includes:
    - Channel counts (total, active, paused)
    - 24-hour delivery statistics
    - Success rate and average response time
    - Breakdown by channel type and event type
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    service = NotificationService(db)
    metrics = service.get_metrics(current_user["organization_id"])

    return NotificationMetricsResponse(**metrics)


# ============================================
# Manual Send Endpoint (Admin)
# ============================================

@router.post(
    "/send",
    summary="Send a manual notification (Admin)",
    status_code=202
)
async def send_manual_notification(
    notification_data: NotificationSendRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually send a notification to all subscribed channels.

    **Requires admin role.**

    This endpoint allows administrators to send custom notifications
    for testing or announcements.
    """
    if not current_user.get("organization_id"):
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    # Check admin role
    if current_user.get("role") not in ['admin', 'platform_admin']:
        raise HTTPException(status_code=403, detail="Admin role required")

    service = NotificationService(db)

    deliveries = await service.send_notification(
        organization_id=current_user["organization_id"],
        event_type=notification_data.event_type,
        title=notification_data.title,
        message=notification_data.message,
        priority=notification_data.priority,
        metadata=notification_data.metadata,
        related_entity_type=notification_data.related_entity_type,
        related_entity_id=notification_data.related_entity_id
    )

    return {
        "message": f"Notification queued for {len(deliveries)} channel(s)",
        "delivery_count": len(deliveries),
        "delivery_ids": [str(d.notification_id) for d in deliveries]
    }
