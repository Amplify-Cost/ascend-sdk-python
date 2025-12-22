"""
Phase 10D: Billing Dashboard API Routes

Customer-facing billing API for usage, invoices, and subscriptions.

Endpoints:
- GET /api/billing/usage - Current usage summary
- GET /api/billing/usage/breakdown - Detailed usage by category
- GET /api/billing/invoices - Invoice history
- GET /api/billing/subscription - Current subscription
- POST /api/billing/portal - Redirect to Stripe Customer Portal

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10D
Date: 2025-12-21
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

import stripe

from database import get_db
from dependencies import get_current_user, get_organization_filter
from models import Organization
from models_billing import (
    UsageAggregate, BillingRecord, SpendLimit,
    UsageSummary, BillingRecordResponse
)
from services.metering_service import get_metering_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/billing",
    tags=["Billing - Dashboard"]
)

# =============================================================================
# CONFIGURATION
# =============================================================================

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class UsageSummaryResponse(BaseModel):
    """Usage summary for current billing period"""
    billing_period: str
    period_start: str
    period_end: str
    days_remaining: int

    # API Calls
    api_calls_used: int
    api_calls_included: int
    api_calls_overage: int
    api_calls_utilization_percent: float

    # Users
    users_active: int
    users_included: int
    users_overage: int

    # MCP Servers
    mcp_servers_active: int
    mcp_servers_included: int
    mcp_servers_overage: int

    # Cost
    base_cost: float
    overage_cost: float
    projected_total: float

    # Trend
    daily_average: float
    projected_usage: int


class UsageBreakdownItem(BaseModel):
    """Usage breakdown by category"""
    category: str
    quantity: int
    included: int
    overage: int
    unit_cost: float
    total_cost: float
    percent_of_total: float


class UsageBreakdownResponse(BaseModel):
    """Detailed usage breakdown"""
    billing_period: str
    items: List[UsageBreakdownItem]
    total_cost: float


class InvoiceResponse(BaseModel):
    """Invoice response"""
    id: int
    billing_period: str
    total_amount: float
    status: str
    paid_at: Optional[str]
    stripe_invoice_url: Optional[str]
    stripe_invoice_pdf: Optional[str]


class SubscriptionResponse(BaseModel):
    """Subscription details"""
    tier: str
    tier_display_name: str
    status: str
    trial_ends_at: Optional[str]
    next_billing_date: Optional[str]
    monthly_base_price: float

    # Included quantities
    included_api_calls: int
    included_users: int
    included_mcp_servers: int
    included_agents: int = 0


class PortalResponse(BaseModel):
    """Stripe Customer Portal response"""
    url: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get usage summary for current billing period.

    Returns real-time usage from Redis cache + DB aggregates.
    """
    # Get organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get current billing period
    now = datetime.now(timezone.utc)
    billing_period = now.strftime("%Y-%m")
    year, month = now.year, now.month

    # Calculate period dates
    _, last_day = monthrange(year, month)
    period_start = datetime(year, month, 1, tzinfo=timezone.utc)
    period_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
    days_remaining = (period_end - now).days

    # Get usage from aggregates
    api_calls = db.query(func.sum(UsageAggregate.total_quantity)).filter(
        UsageAggregate.organization_id == org_id,
        UsageAggregate.billing_period == billing_period,
        UsageAggregate.event_type == "action_evaluation"
    ).scalar() or 0

    # Also get real-time from Redis
    metering = get_metering_service()
    usage_snapshot = await metering.get_current_usage(org_id, billing_period)
    api_calls = max(api_calls, usage_snapshot.api_calls)

    # Calculate overages
    included = org.included_api_calls
    overage = max(0, api_calls - included)
    utilization = (api_calls / included * 100) if included > 0 else 0

    # Get active users count
    from models import User
    users_active = db.query(func.count(User.id)).filter(
        User.organization_id == org_id,
        User.is_active == True
    ).scalar() or 0

    users_overage = max(0, users_active - org.included_users)

    # MCP servers (placeholder - would need actual count)
    mcp_servers_active = 0
    mcp_servers_overage = max(0, mcp_servers_active - org.included_mcp_servers)

    # Calculate costs
    overage_cost = (
        overage * org.overage_rate_per_call +
        users_overage * org.overage_rate_per_user +
        mcp_servers_overage * org.overage_rate_per_server
    )

    # Get base price from subscription tier
    from models_billing import SubscriptionTier
    tier = db.query(SubscriptionTier).filter(
        SubscriptionTier.name == org.subscription_tier
    ).first()
    base_cost = tier.monthly_base_price if tier else 0

    # Calculate projections
    days_elapsed = now.day
    daily_average = api_calls / days_elapsed if days_elapsed > 0 else 0
    projected_usage = int(daily_average * last_day)
    projected_total = base_cost + (max(0, projected_usage - included) * org.overage_rate_per_call)

    return UsageSummaryResponse(
        billing_period=billing_period,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        days_remaining=days_remaining,
        api_calls_used=api_calls,
        api_calls_included=included,
        api_calls_overage=overage,
        api_calls_utilization_percent=round(utilization, 1),
        users_active=users_active,
        users_included=org.included_users,
        users_overage=users_overage,
        mcp_servers_active=mcp_servers_active,
        mcp_servers_included=org.included_mcp_servers,
        mcp_servers_overage=mcp_servers_overage,
        base_cost=base_cost,
        overage_cost=round(overage_cost, 2),
        projected_total=round(projected_total, 2),
        daily_average=round(daily_average, 0),
        projected_usage=projected_usage
    )


@router.get("/usage/breakdown", response_model=UsageBreakdownResponse)
async def get_usage_breakdown(
    billing_period: Optional[str] = None,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed usage breakdown by category.

    Returns usage itemized by event type.
    """
    if billing_period is None:
        billing_period = datetime.now(timezone.utc).strftime("%Y-%m")

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get aggregates
    aggregates = db.query(UsageAggregate).filter(
        UsageAggregate.organization_id == org_id,
        UsageAggregate.billing_period == billing_period
    ).all()

    items = []
    total_cost = 0

    # Map event types to included quantities
    included_map = {
        "action_evaluation": org.included_api_calls,
        "api_call": org.included_api_calls,
        "user_seat": org.included_users,
        "mcp_server_hour": org.included_mcp_servers * 720  # hours per month
    }

    rate_map = {
        "action_evaluation": org.overage_rate_per_call,
        "api_call": org.overage_rate_per_call,
        "user_seat": org.overage_rate_per_user,
        "mcp_server_hour": org.overage_rate_per_server / 720
    }

    for agg in aggregates:
        included = included_map.get(agg.event_type, 0)
        overage = max(0, agg.total_quantity - included)
        unit_cost = rate_map.get(agg.event_type, 0)
        item_cost = overage * unit_cost

        items.append(UsageBreakdownItem(
            category=agg.event_type,
            quantity=agg.total_quantity,
            included=included,
            overage=overage,
            unit_cost=unit_cost,
            total_cost=round(item_cost, 2),
            percent_of_total=0  # Calculated below
        ))
        total_cost += item_cost

    # Calculate percentages
    for item in items:
        item.percent_of_total = round((item.total_cost / total_cost * 100) if total_cost > 0 else 0, 1)

    return UsageBreakdownResponse(
        billing_period=billing_period,
        items=items,
        total_cost=round(total_cost, 2)
    )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = 12,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get invoice history.

    Returns up to 12 most recent invoices.
    """
    invoices = db.query(BillingRecord).filter(
        BillingRecord.organization_id == org_id
    ).order_by(BillingRecord.billing_period.desc()).limit(limit).all()

    return [
        InvoiceResponse(
            id=inv.id,
            billing_period=inv.billing_period,
            total_amount=inv.total_amount,
            status=inv.status,
            paid_at=inv.paid_at.isoformat() if inv.paid_at else None,
            stripe_invoice_url=inv.stripe_invoice_url,
            stripe_invoice_pdf=inv.stripe_invoice_pdf
        )
        for inv in invoices
    ]


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current subscription details.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get tier details
    from models_billing import SubscriptionTier
    tier = db.query(SubscriptionTier).filter(
        SubscriptionTier.name == org.subscription_tier
    ).first()

    tier_display = tier.display_name if tier else org.subscription_tier.title()
    base_price = tier.monthly_base_price if tier else 0

    return SubscriptionResponse(
        tier=org.subscription_tier,
        tier_display_name=tier_display,
        status=org.subscription_status,
        trial_ends_at=org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        next_billing_date=org.next_billing_date.isoformat() if org.next_billing_date else None,
        monthly_base_price=base_price,
        included_api_calls=org.included_api_calls,
        included_users=org.included_users,
        included_mcp_servers=org.included_mcp_servers,
        included_agents=getattr(org, 'included_agents', 0) or 0
    )


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    return_url: Optional[str] = None,
    org_id: int = Depends(get_organization_filter),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create Stripe Customer Portal session.

    Redirects user to Stripe's hosted portal for:
    - Update payment method
    - View invoices
    - Cancel subscription
    """
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured"
        )

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or not org.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer linked to this organization"
        )

    # Default return URL
    if not return_url:
        return_url = os.environ.get("APP_URL", "https://pilot.owkai.app") + "/settings/billing"

    try:
        stripe.api_key = STRIPE_SECRET_KEY

        session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=return_url
        )

        return PortalResponse(url=session.url)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.get("/tiers")
async def get_subscription_tiers(
    db: Session = Depends(get_db)
):
    """
    Get available subscription tiers.

    Public endpoint for pricing page.
    """
    from models_billing import SubscriptionTier

    tiers = db.query(SubscriptionTier).filter(
        SubscriptionTier.is_active == True
    ).order_by(SubscriptionTier.sort_order).all()

    return [
        {
            "name": tier.name,
            "display_name": tier.display_name,
            "description": tier.description,
            "monthly_price": tier.monthly_base_price,
            "yearly_price": tier.price_yearly_cents / 100.0 if tier.price_yearly_cents else 0,
            "included": {
                "api_calls": tier.included_api_calls,
                "users": tier.included_users,
                "mcp_servers": tier.included_mcp_servers,
                "agents": tier.included_agents
            },
            "stripe": {
                "product_id": tier.stripe_product_id,
                "price_id_monthly": tier.stripe_price_id_monthly,
                "price_id_yearly": tier.stripe_price_id_yearly
            },
            "trial_days": tier.trial_days,
            "features": tier.features
        }
        for tier in tiers
    ]
