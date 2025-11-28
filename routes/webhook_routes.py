"""
OW-kai Enterprise Webhook API Routes

Banking-Level Security: Multi-tenant isolation, rate limiting, full audit trail
Compliance: SOC 2 CC6.1, PCI-DSS 8.3.1, HIPAA 164.312

Document ID: OWKAI-INT-001-ROUTES
Version: 1.0.0
Date: November 28, 2025
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from dependencies import get_current_user, get_organization_filter
from models import User
from models_webhooks import (
    WebhookSubscription,
    WebhookDelivery,
    WebhookDeliveryQueue,
    WebhookEventType,
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionWithSecret,
    WebhookDeliveryResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    WebhookEventListResponse,
    WebhookEventTypeSchema,
    WEBHOOK_EVENT_METADATA
)
from services.webhook_service import WebhookService

logger = logging.getLogger("enterprise.webhooks.routes")

router = APIRouter(prefix="/api/webhooks", tags=["Enterprise Webhooks"])


# ===== List Available Events =====

@router.get("/events", response_model=WebhookEventListResponse)
async def list_webhook_events(
    current_user: User = Depends(get_current_user)
):
    """
    List all available webhook event types.

    Returns a list of events that can be subscribed to, with descriptions
    and payload schema references.

    Requires: Authenticated user
    """
    events = []
    for event_type in WebhookEventType:
        metadata = WEBHOOK_EVENT_METADATA.get(event_type, {})
        events.append(WebhookEventTypeSchema(
            type=event_type.value,
            description=metadata.get("description", ""),
            payload_schema=metadata.get("payload_schema", ""),
            category=metadata.get("category", "Other")
        ))

    return WebhookEventListResponse(
        events=events,
        total=len(events)
    )


# ===== Webhook Subscriptions CRUD =====

@router.post("", response_model=WebhookSubscriptionWithSecret, status_code=201)
async def create_webhook_subscription(
    request: WebhookSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Create a new webhook subscription.

    IMPORTANT: The webhook secret is only returned ONCE at creation time.
    Store it securely - it cannot be retrieved again.

    Security:
    - HTTPS required for target URL
    - HMAC-SHA256 signature on every delivery
    - Multi-tenant isolation enforced

    Rate Limits:
    - Default: 100 events/minute per subscription
    - Configurable up to 1000/minute

    Requires: Admin role
    """
    # Role check - only admins can create webhooks
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage webhooks"
        )

    service = WebhookService(db)

    try:
        subscription, secret = service.create_subscription(
            organization_id=organization_id,
            name=request.name,
            target_url=str(request.target_url),
            event_types=request.event_types,
            created_by=current_user.id,
            description=request.description,
            event_filters=request.event_filters,
            custom_headers=request.custom_headers,
            retry_config=request.retry_config,
            rate_limit_per_minute=request.rate_limit_per_minute or 100
        )

        logger.info(
            f"Webhook subscription created: {subscription.id} by user {current_user.id} "
            f"for org {organization_id}"
        )

        # Return subscription with secret (only time secret is shown)
        return WebhookSubscriptionWithSecret(
            id=subscription.id,
            subscription_id=str(subscription.subscription_id),
            name=subscription.name,
            description=subscription.description,
            target_url=subscription.target_url,
            event_types=subscription.event_types,
            event_filters=subscription.event_filters,
            is_active=subscription.is_active,
            is_verified=subscription.is_verified,
            rate_limit_per_minute=subscription.rate_limit_per_minute,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            secret_key=secret  # Only returned at creation!
        )

    except Exception as e:
        logger.error(f"Failed to create webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    include_inactive: bool = Query(False, description="Include inactive subscriptions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    List all webhook subscriptions for the organization.

    Multi-tenant: Only returns subscriptions for the user's organization.

    Requires: Authenticated user
    """
    service = WebhookService(db)
    subscriptions = service.list_subscriptions(
        organization_id=organization_id,
        include_inactive=include_inactive
    )

    return [
        WebhookSubscriptionResponse(
            id=sub.id,
            subscription_id=str(sub.subscription_id),
            name=sub.name,
            description=sub.description,
            target_url=sub.target_url,
            event_types=sub.event_types,
            event_filters=sub.event_filters,
            is_active=sub.is_active,
            is_verified=sub.is_verified,
            rate_limit_per_minute=sub.rate_limit_per_minute,
            created_at=sub.created_at,
            updated_at=sub.updated_at
        )
        for sub in subscriptions
    ]


@router.get("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Get a specific webhook subscription.

    Multi-tenant: Only returns subscription if it belongs to user's organization.

    Requires: Authenticated user
    """
    service = WebhookService(db)
    subscription = service.get_subscription(subscription_id, organization_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    return WebhookSubscriptionResponse(
        id=subscription.id,
        subscription_id=str(subscription.subscription_id),
        name=subscription.name,
        description=subscription.description,
        target_url=subscription.target_url,
        event_types=subscription.event_types,
        event_filters=subscription.event_filters,
        is_active=subscription.is_active,
        is_verified=subscription.is_verified,
        rate_limit_per_minute=subscription.rate_limit_per_minute,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )


@router.put("/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: int,
    request: WebhookSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Update a webhook subscription.

    Note: Cannot change the secret via update. Use rotate-secret endpoint.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage webhooks"
        )

    service = WebhookService(db)

    # Build update dict from non-None values
    updates = {k: v for k, v in request.model_dump().items() if v is not None}

    # Convert HttpUrl to string if present
    if 'target_url' in updates:
        updates['target_url'] = str(updates['target_url'])

    subscription = service.update_subscription(
        subscription_id=subscription_id,
        organization_id=organization_id,
        **updates
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    logger.info(f"Webhook subscription {subscription_id} updated by user {current_user.id}")

    return WebhookSubscriptionResponse(
        id=subscription.id,
        subscription_id=str(subscription.subscription_id),
        name=subscription.name,
        description=subscription.description,
        target_url=subscription.target_url,
        event_types=subscription.event_types,
        event_filters=subscription.event_filters,
        is_active=subscription.is_active,
        is_verified=subscription.is_verified,
        rate_limit_per_minute=subscription.rate_limit_per_minute,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at
    )


@router.delete("/{subscription_id}", status_code=204)
async def delete_webhook_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Delete a webhook subscription.

    This will also delete all delivery history for this subscription.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage webhooks"
        )

    service = WebhookService(db)
    success = service.delete_subscription(subscription_id, organization_id)

    if not success:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    logger.info(f"Webhook subscription {subscription_id} deleted by user {current_user.id}")
    return None


# ===== Secret Management =====

class RotateSecretResponse(BaseModel):
    """Response for secret rotation"""
    subscription_id: int
    new_secret: str
    message: str


@router.post("/{subscription_id}/rotate-secret", response_model=RotateSecretResponse)
async def rotate_webhook_secret(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Rotate the webhook signing secret.

    IMPORTANT: The new secret is only returned ONCE.
    Update your webhook receiver immediately after rotating.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage webhooks"
        )

    service = WebhookService(db)
    subscription, new_secret = service.rotate_secret(subscription_id, organization_id)

    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    logger.info(f"Webhook secret rotated for subscription {subscription_id} by user {current_user.id}")

    return RotateSecretResponse(
        subscription_id=subscription_id,
        new_secret=new_secret,
        message="Secret rotated successfully. Update your webhook receiver with the new secret."
    )


# ===== Test Webhook =====

@router.post("/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    subscription_id: int,
    request: WebhookTestRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Send a test webhook to verify configuration.

    This sends a test event to the configured URL and returns the result.
    Use this to verify your webhook receiver is correctly configured.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to test webhooks"
        )

    service = WebhookService(db)

    try:
        delivery = await service.send_test_webhook(
            subscription_id=subscription_id,
            organization_id=organization_id,
            event_type=request.event_type if request else "action.submitted",
            custom_payload=request.custom_payload if request else None
        )

        return WebhookTestResponse(
            success=delivery.delivery_status == "success",
            delivery_id=delivery.id,
            response_status=delivery.response_status,
            response_time_ms=delivery.response_time_ms,
            error_message=delivery.error_message,
            signature_header=delivery.signature_sent or ""
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Test webhook failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Delivery History =====

@router.get("/{subscription_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_webhook_deliveries(
    subscription_id: int,
    status: Optional[str] = Query(None, description="Filter by delivery status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Get delivery history for a webhook subscription.

    Returns recent webhook deliveries with status, response details, and timing.

    Requires: Authenticated user
    """
    service = WebhookService(db)

    # Verify subscription exists and belongs to org
    subscription = service.get_subscription(subscription_id, organization_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")

    deliveries = service.get_deliveries(
        subscription_id=subscription_id,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
        status=status
    )

    return [
        WebhookDeliveryResponse(
            id=d.id,
            event_id=str(d.event_id),
            event_type=d.event_type,
            delivery_status=d.delivery_status,
            attempt_count=d.attempt_count,
            response_status=d.response_status,
            response_time_ms=d.response_time_ms,
            error_message=d.error_message,
            created_at=d.created_at,
            delivered_at=d.delivered_at
        )
        for d in deliveries
    ]


# ===== Dead Letter Queue =====

class DLQEntryResponse(BaseModel):
    """Response for DLQ entry"""
    id: int
    event_id: str
    event_type: str
    failure_reason: str
    total_attempts: int
    last_attempt_at: str
    resolved: bool
    created_at: str


@router.get("/dlq/entries", response_model=List[DLQEntryResponse])
async def get_dlq_entries(
    resolved: bool = Query(False, description="Include resolved entries"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Get dead letter queue entries.

    These are webhook deliveries that permanently failed after all retries.
    Review and resolve or retry these entries.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to view DLQ"
        )

    service = WebhookService(db)
    entries = service.get_dlq_entries(
        organization_id=organization_id,
        resolved=resolved,
        limit=limit
    )

    return [
        DLQEntryResponse(
            id=e.id,
            event_id=str(e.event_id),
            event_type=e.event_type,
            failure_reason=e.failure_reason,
            total_attempts=e.total_attempts,
            last_attempt_at=e.last_attempt_at.isoformat(),
            resolved=e.resolved,
            created_at=e.created_at.isoformat()
        )
        for e in entries
    ]


class ResolveDLQRequest(BaseModel):
    """Request to resolve a DLQ entry"""
    notes: Optional[str] = None


@router.post("/dlq/{dlq_id}/resolve")
async def resolve_dlq_entry(
    dlq_id: int,
    request: ResolveDLQRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Mark a DLQ entry as resolved.

    Use this when you've manually handled the failed webhook
    or determined it doesn't need to be delivered.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage DLQ"
        )

    service = WebhookService(db)
    entry = service.resolve_dlq_entry(
        dlq_id=dlq_id,
        organization_id=organization_id,
        resolved_by=current_user.id,
        notes=request.notes if request else None
    )

    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")

    logger.info(f"DLQ entry {dlq_id} resolved by user {current_user.id}")

    return {"message": "DLQ entry resolved", "dlq_id": dlq_id}


@router.post("/dlq/{dlq_id}/retry")
async def retry_dlq_entry(
    dlq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Retry a failed webhook from the DLQ.

    Creates a new delivery attempt for the failed webhook.
    The DLQ entry is automatically marked as resolved.

    Requires: Admin role
    """
    if current_user.role not in ['admin', 'platform_admin']:
        raise HTTPException(
            status_code=403,
            detail="Admin role required to manage DLQ"
        )

    service = WebhookService(db)
    delivery_id = await service.retry_dlq_entry(
        dlq_id=dlq_id,
        organization_id=organization_id
    )

    if not delivery_id:
        raise HTTPException(
            status_code=404,
            detail="DLQ entry not found or subscription inactive"
        )

    logger.info(f"DLQ entry {dlq_id} retried as delivery {delivery_id} by user {current_user.id}")

    return {
        "message": "Webhook retry initiated",
        "dlq_id": dlq_id,
        "new_delivery_id": delivery_id
    }


# ===== Webhook Metrics =====

class WebhookMetricsResponse(BaseModel):
    """Webhook metrics for dashboard"""
    total_subscriptions: int
    active_subscriptions: int
    total_deliveries_24h: int
    successful_deliveries_24h: int
    failed_deliveries_24h: int
    success_rate_24h: float
    avg_response_time_ms: float
    dlq_unresolved: int


@router.get("/metrics", response_model=WebhookMetricsResponse)
async def get_webhook_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: int = Depends(get_organization_filter)
):
    """
    Get webhook metrics for the organization.

    Returns delivery success rates, response times, and DLQ status.

    Requires: Authenticated user
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_

    # Get subscription counts
    total_subs = db.query(func.count(WebhookSubscription.id)).filter(
        WebhookSubscription.organization_id == organization_id
    ).scalar() or 0

    active_subs = db.query(func.count(WebhookSubscription.id)).filter(
        and_(
            WebhookSubscription.organization_id == organization_id,
            WebhookSubscription.is_active == True
        )
    ).scalar() or 0

    # Get delivery stats for last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)

    delivery_stats = db.query(
        func.count(WebhookDelivery.id).label('total'),
        func.count(WebhookDelivery.id).filter(
            WebhookDelivery.delivery_status == 'success'
        ).label('success'),
        func.count(WebhookDelivery.id).filter(
            WebhookDelivery.delivery_status == 'failed'
        ).label('failed'),
        func.avg(WebhookDelivery.response_time_ms).label('avg_time')
    ).filter(
        and_(
            WebhookDelivery.organization_id == organization_id,
            WebhookDelivery.created_at >= cutoff
        )
    ).first()

    total_deliveries = delivery_stats.total or 0
    successful = delivery_stats.success or 0
    failed = delivery_stats.failed or 0
    avg_time = float(delivery_stats.avg_time or 0)

    success_rate = (successful / total_deliveries * 100) if total_deliveries > 0 else 100.0

    # Get DLQ count
    dlq_count = db.query(func.count(WebhookDeliveryQueue.id)).filter(
        and_(
            WebhookDeliveryQueue.organization_id == organization_id,
            WebhookDeliveryQueue.resolved == False
        )
    ).scalar() or 0

    return WebhookMetricsResponse(
        total_subscriptions=total_subs,
        active_subscriptions=active_subs,
        total_deliveries_24h=total_deliveries,
        successful_deliveries_24h=successful,
        failed_deliveries_24h=failed,
        success_rate_24h=round(success_rate, 2),
        avg_response_time_ms=round(avg_time, 2),
        dlq_unresolved=dlq_count
    )
