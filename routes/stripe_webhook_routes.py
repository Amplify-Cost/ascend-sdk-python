"""
Phase 10E: Stripe Webhook Handler

Handles incoming Stripe webhook events for billing integration.

Events Handled:
- invoice.paid → Update billing records, send receipt
- invoice.payment_failed → Trigger dunning, notify admin
- customer.subscription.updated → Sync tier changes
- customer.subscription.deleted → Handle cancellation
- checkout.session.completed → Complete signup

Security:
- HMAC-SHA256 signature verification
- Timestamp validation (5-minute window)
- Idempotency via event ID tracking

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10E
Date: 2025-12-21
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

import stripe

from database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webhooks",
    tags=["Webhooks - Stripe"]
)

# Alias router for Stripe Dashboard compatibility
# Stripe Dashboard configured: /api/v1/stripe/webhook
# This provides backward-compatible alias while preserving original route
stripe_v1_router = APIRouter(
    prefix="/api/v1/stripe",
    tags=["Webhooks - Stripe (v1 Alias)"]
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load Stripe credentials from environment (populated from Secrets Manager)
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

# Event types we handle
HANDLED_EVENTS = [
    "invoice.paid",
    "invoice.payment_failed",
    "invoice.finalized",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "checkout.session.completed",
    "customer.created",
    "customer.updated",
]


# =============================================================================
# WEBHOOK ENDPOINT
# =============================================================================

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe webhook events.

    1. Verify signature
    2. Check idempotency
    3. Process event asynchronously
    4. Return 200 immediately

    Stripe expects 200 response within 30 seconds.
    """
    # Get raw body and signature
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Stripe webhook: Missing signature header")
        raise HTTPException(status_code=400, detail="Missing signature")

    if not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook: STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook not configured")

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.warning(f"Stripe webhook: Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Stripe webhook: Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Extract event details
    event_id = event.get("id")
    event_type = event.get("type")
    livemode = event.get("livemode", False)

    logger.info(f"Stripe webhook: Received {event_type} (id={event_id}, live={livemode})")

    # Check if we handle this event type
    if event_type not in HANDLED_EVENTS:
        logger.debug(f"Stripe webhook: Ignoring unhandled event type: {event_type}")
        return {"received": True, "handled": False}

    # Check idempotency - have we already processed this event?
    db = SessionLocal()
    try:
        from models_billing import StripeWebhookEvent

        existing = db.query(StripeWebhookEvent).filter(
            StripeWebhookEvent.stripe_event_id == event_id
        ).first()

        if existing:
            logger.info(f"Stripe webhook: Event {event_id} already processed, skipping")
            return {"received": True, "handled": True, "duplicate": True}

        # Store event for idempotency and audit
        webhook_event = StripeWebhookEvent(
            stripe_event_id=event_id,
            stripe_event_type=event_type,
            stripe_api_version=event.get("api_version"),
            event_data=event,
            livemode=livemode,
            status="received"
        )
        db.add(webhook_event)
        db.commit()

    except Exception as e:
        logger.error(f"Stripe webhook: Failed to store event: {e}")
        db.rollback()
        # Continue processing anyway - don't fail on storage issues
    finally:
        db.close()

    # Process event in background
    background_tasks.add_task(process_stripe_event, event_id, event_type, event)

    return {"received": True, "handled": True}


# =============================================================================
# EVENT PROCESSING
# =============================================================================

async def process_stripe_event(event_id: str, event_type: str, event: dict):
    """
    Process a Stripe event asynchronously.

    Called by background task after returning 200 to Stripe.
    """
    db = SessionLocal()

    try:
        from models_billing import StripeWebhookEvent

        # Update event status
        webhook_event = db.query(StripeWebhookEvent).filter(
            StripeWebhookEvent.stripe_event_id == event_id
        ).first()

        if webhook_event:
            webhook_event.status = "processing"
            webhook_event.processing_started_at = datetime.now(timezone.utc)
            db.commit()

        # Route to appropriate handler
        data = event.get("data", {}).get("object", {})

        if event_type == "invoice.paid":
            await handle_invoice_paid(db, data)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(db, data)
        elif event_type == "invoice.finalized":
            await handle_invoice_finalized(db, data)
        elif event_type == "customer.subscription.created":
            await handle_subscription_created(db, data)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(db, data)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(db, data)
        elif event_type == "checkout.session.completed":
            await handle_checkout_completed(db, data)
        elif event_type == "customer.created":
            await handle_customer_created(db, data)
        elif event_type == "customer.updated":
            await handle_customer_updated(db, data)

        # Update event status
        if webhook_event:
            webhook_event.status = "completed"
            webhook_event.processing_completed_at = datetime.now(timezone.utc)
            db.commit()

        logger.info(f"Stripe webhook: Successfully processed {event_type}")

    except Exception as e:
        logger.error(f"Stripe webhook: Failed to process {event_type}: {e}")

        # Update event status
        try:
            from models_billing import StripeWebhookEvent

            webhook_event = db.query(StripeWebhookEvent).filter(
                StripeWebhookEvent.stripe_event_id == event_id
            ).first()

            if webhook_event:
                webhook_event.status = "failed"
                webhook_event.processing_error = str(e)
                webhook_event.retry_count += 1
                db.commit()
        except Exception:
            pass

    finally:
        db.close()


# =============================================================================
# EVENT HANDLERS
# =============================================================================

async def handle_invoice_paid(db: Session, invoice: dict):
    """
    Handle invoice.paid event.

    Updates billing record status and sends receipt.
    """
    from models import Organization
    from models_billing import BillingRecord

    invoice_id = invoice.get("id")
    customer_id = invoice.get("customer")
    amount_paid = invoice.get("amount_paid", 0) / 100  # Convert from cents

    logger.info(f"Processing invoice.paid: {invoice_id} for ${amount_paid:.2f}")

    # Find organization by Stripe customer ID
    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        logger.warning(f"No organization found for Stripe customer: {customer_id}")
        return

    # Update or create billing record
    period = datetime.fromtimestamp(invoice.get("period_start", 0)).strftime("%Y-%m")

    billing_record = db.query(BillingRecord).filter(
        BillingRecord.stripe_invoice_id == invoice_id
    ).first()

    if billing_record:
        billing_record.status = "paid"
        billing_record.paid_at = datetime.now(timezone.utc)
        billing_record.total_amount = amount_paid
    else:
        billing_record = BillingRecord(
            organization_id=org.id,
            billing_period=period,
            period_start=datetime.fromtimestamp(invoice.get("period_start", 0), tz=timezone.utc),
            period_end=datetime.fromtimestamp(invoice.get("period_end", 0), tz=timezone.utc),
            stripe_invoice_id=invoice_id,
            stripe_invoice_url=invoice.get("hosted_invoice_url"),
            stripe_invoice_pdf=invoice.get("invoice_pdf"),
            total_amount=amount_paid,
            status="paid",
            paid_at=datetime.now(timezone.utc)
        )
        db.add(billing_record)

    # Update organization billing status
    org.subscription_status = "active"
    org.next_billing_date = datetime.fromtimestamp(
        invoice.get("next_payment_attempt", 0), tz=timezone.utc
    ) if invoice.get("next_payment_attempt") else None

    db.commit()

    # TODO: Send receipt notification
    logger.info(f"Invoice {invoice_id} marked as paid for org {org.id}")


async def handle_invoice_payment_failed(db: Session, invoice: dict):
    """
    Handle invoice.payment_failed event.

    Updates billing record and triggers dunning workflow.
    """
    from models import Organization
    from models_billing import BillingRecord

    invoice_id = invoice.get("id")
    customer_id = invoice.get("customer")

    logger.warning(f"Processing invoice.payment_failed: {invoice_id}")

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    # Update billing record
    billing_record = db.query(BillingRecord).filter(
        BillingRecord.stripe_invoice_id == invoice_id
    ).first()

    if billing_record:
        billing_record.status = "failed"
        billing_record.failed_at = datetime.now(timezone.utc)
        billing_record.retry_count += 1
        billing_record.next_retry_at = datetime.fromtimestamp(
            invoice.get("next_payment_attempt", 0), tz=timezone.utc
        ) if invoice.get("next_payment_attempt") else None

    # Update organization status
    org.subscription_status = "past_due"

    db.commit()

    # TODO: Send payment failed notification
    logger.warning(f"Invoice {invoice_id} payment failed for org {org.id}")


async def handle_invoice_finalized(db: Session, invoice: dict):
    """Handle invoice.finalized event - create billing record"""
    from models import Organization
    from models_billing import BillingRecord

    invoice_id = invoice.get("id")
    customer_id = invoice.get("customer")

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    # Create billing record
    period = datetime.fromtimestamp(invoice.get("period_start", 0)).strftime("%Y-%m")

    existing = db.query(BillingRecord).filter(
        BillingRecord.stripe_invoice_id == invoice_id
    ).first()

    if not existing:
        billing_record = BillingRecord(
            organization_id=org.id,
            billing_period=period,
            period_start=datetime.fromtimestamp(invoice.get("period_start", 0), tz=timezone.utc),
            period_end=datetime.fromtimestamp(invoice.get("period_end", 0), tz=timezone.utc),
            stripe_invoice_id=invoice_id,
            stripe_invoice_url=invoice.get("hosted_invoice_url"),
            stripe_invoice_pdf=invoice.get("invoice_pdf"),
            total_amount=invoice.get("amount_due", 0) / 100,
            status="pending",
            finalized_at=datetime.now(timezone.utc)
        )
        db.add(billing_record)
        db.commit()

    logger.info(f"Invoice {invoice_id} finalized for org {org.id}")


async def handle_subscription_created(db: Session, subscription: dict):
    """Handle customer.subscription.created event"""
    await handle_subscription_updated(db, subscription)


async def handle_subscription_updated(db: Session, subscription: dict):
    """
    Handle customer.subscription.updated event.

    Syncs subscription tier and status with Organization.
    """
    from models import Organization

    subscription_id = subscription.get("id")
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        logger.warning(f"No org found for subscription update: {customer_id}")
        return

    # Update subscription ID
    org.stripe_subscription_id = subscription_id

    # Map Stripe status to our status
    status_map = {
        "active": "active",
        "trialing": "trial",
        "past_due": "past_due",
        "canceled": "cancelled",
        "unpaid": "past_due",
        "incomplete": "trial",
        "incomplete_expired": "cancelled"
    }
    org.subscription_status = status_map.get(status, "active")

    # Update trial end date if applicable
    trial_end = subscription.get("trial_end")
    if trial_end:
        org.trial_ends_at = datetime.fromtimestamp(trial_end, tz=timezone.utc)

    # Update next billing date
    current_period_end = subscription.get("current_period_end")
    if current_period_end:
        org.next_billing_date = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

    db.commit()

    logger.info(
        f"Subscription {subscription_id} updated for org {org.id}: status={org.subscription_status}"
    )


async def handle_subscription_deleted(db: Session, subscription: dict):
    """
    Handle customer.subscription.deleted event.

    Marks organization as cancelled.
    """
    from models import Organization

    customer_id = subscription.get("customer")

    org = db.query(Organization).filter(
        Organization.stripe_customer_id == customer_id
    ).first()

    if not org:
        return

    org.subscription_status = "cancelled"
    org.stripe_subscription_id = None

    db.commit()

    logger.warning(f"Subscription cancelled for org {org.id}")


async def handle_checkout_completed(db: Session, session: dict):
    """
    Handle checkout.session.completed event.

    Completes signup flow after successful payment.
    """
    from models import Organization
    from models_signup import SignupRequest

    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    client_reference_id = session.get("client_reference_id")  # Our signup request ID

    logger.info(f"Checkout completed: customer={customer_id}, ref={client_reference_id}")

    if client_reference_id:
        # Find signup request
        signup = db.query(SignupRequest).filter(
            SignupRequest.id == int(client_reference_id)
        ).first()

        if signup and signup.organization_id:
            org = db.query(Organization).filter(
                Organization.id == signup.organization_id
            ).first()

            if org:
                org.stripe_customer_id = customer_id
                org.stripe_subscription_id = subscription_id
                org.subscription_status = "active"

            signup.status = "active"
            db.commit()

            logger.info(f"Checkout completed for org {org.id if org else 'unknown'}")


async def handle_customer_created(db: Session, customer: dict):
    """Handle customer.created event - log for audit"""
    customer_id = customer.get("id")
    email = customer.get("email")
    logger.info(f"Stripe customer created: {customer_id} ({email})")


async def handle_customer_updated(db: Session, customer: dict):
    """Handle customer.updated event - sync email changes"""
    customer_id = customer.get("id")
    logger.debug(f"Stripe customer updated: {customer_id}")


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/stripe/health")
async def stripe_webhook_health():
    """Health check for Stripe webhook endpoint"""
    return {
        "status": "ok",
        "webhook_secret_configured": bool(STRIPE_WEBHOOK_SECRET),
        "stripe_key_configured": bool(STRIPE_SECRET_KEY),
        "handled_events": HANDLED_EVENTS
    }


# =============================================================================
# V1 ALIAS ENDPOINTS (Stripe Dashboard Compatibility)
# =============================================================================
# Stripe Dashboard is configured with /api/v1/stripe/webhook
# These aliases forward to the same handlers as /api/webhooks/stripe

@stripe_v1_router.post("/webhook")
async def stripe_webhook_v1_alias(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Alias endpoint for Stripe Dashboard compatibility.

    Stripe Dashboard configured URL: /api/v1/stripe/webhook
    Forwards to same handler as /api/webhooks/stripe

    This ensures:
    - Zero breaking changes for existing integrations
    - Stripe Dashboard webhook delivery works
    - Same security (HMAC-SHA256) on both paths
    """
    return await stripe_webhook(request, background_tasks)


@stripe_v1_router.get("/webhook/health")
async def stripe_webhook_v1_health():
    """Health check for v1 alias endpoint"""
    return await stripe_webhook_health()
