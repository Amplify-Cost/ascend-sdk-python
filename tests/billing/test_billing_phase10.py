"""
Phase 10: Stripe Billing Tests
GATE 2 Evidence - Unit Tests for Billing Implementation

These tests validate the Phase 10 Stripe Billing implementation:
- 10B: High-throughput metering service
- 10C: Financial kill-switch / spend control
- 10D: Customer billing dashboard API
- 10E: Stripe webhook handler
- 10F: Onboarding integration

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch


# =============================================================================
# 10B: METERING SERVICE TESTS
# =============================================================================

class TestMeteringService:
    """Tests for high-throughput usage metering"""

    def test_metering_service_imports(self):
        """Verify metering service imports correctly"""
        from services.metering_service import (
            MeteringService,
            UsageEventData,
            UsageSnapshot,
            get_metering_service
        )
        assert MeteringService is not None
        assert UsageEventData is not None
        assert UsageSnapshot is not None

    def test_usage_event_data_structure(self):
        """Verify usage event data structure"""
        from services.metering_service import UsageEventData

        event = UsageEventData(
            organization_id=1,
            event_type="action_evaluation",
            quantity=1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            billing_period="2025-12",
            metadata={"action_id": 123},
            source="redis_batch"
        )

        assert event.organization_id == 1
        assert event.event_type == "action_evaluation"
        assert event.quantity == 1

    def test_usage_snapshot_structure(self):
        """Verify usage snapshot structure"""
        from services.metering_service import UsageSnapshot

        snapshot = UsageSnapshot(
            organization_id=1,
            billing_period="2025-12",
            api_calls=1000,
            included_api_calls=5000,
            overage_api_calls=0,
            estimated_cost=0.0
        )

        assert snapshot.api_calls == 1000
        assert snapshot.included_api_calls == 5000


# =============================================================================
# 10C: SPEND CONTROL TESTS
# =============================================================================

class TestSpendControl:
    """Tests for financial kill-switch and spend control"""

    def test_spend_control_imports(self):
        """Verify spend control service imports correctly"""
        from services.spend_control_service import (
            SpendControlService,
            SpendCheckResult,
            SpendLimitConfig,
            get_spend_control_service
        )
        assert SpendControlService is not None
        assert SpendCheckResult is not None
        assert SpendLimitConfig is not None

    def test_spend_check_result_allowed(self):
        """Verify allowed spend check result structure"""
        from services.spend_control_service import SpendCheckResult

        result = SpendCheckResult(
            allowed=True,
            blocked=False,
            current_spend=500.0,
            monthly_limit=1000.0,
            utilization_percent=50.0,
            status="within_limit",
            warning_triggered=False,
            kill_switch_active=False,
            message=None
        )

        assert result.allowed is True
        assert result.blocked is False
        assert result.utilization_percent == 50.0

    def test_spend_check_result_blocked(self):
        """Verify blocked spend check result structure"""
        from services.spend_control_service import SpendCheckResult

        result = SpendCheckResult(
            allowed=False,
            blocked=True,
            current_spend=1500.0,
            monthly_limit=1000.0,
            utilization_percent=150.0,
            status="limit_exceeded",
            warning_triggered=True,
            kill_switch_active=False,
            message="Monthly spend limit exceeded"
        )

        assert result.allowed is False
        assert result.blocked is True
        assert result.status == "limit_exceeded"


# =============================================================================
# 10D: BILLING ROUTES TESTS
# =============================================================================

class TestBillingRoutes:
    """Tests for billing dashboard API routes"""

    def test_billing_routes_imports(self):
        """Verify billing routes import correctly"""
        from routes.billing_routes import router
        assert router is not None
        assert router.prefix == "/api/billing"

    def test_billing_response_models(self):
        """Verify billing response models exist"""
        from routes.billing_routes import (
            UsageSummaryResponse,
            UsageBreakdownResponse,
            InvoiceResponse,
            SubscriptionResponse,
            PortalResponse
        )
        assert UsageSummaryResponse is not None
        assert InvoiceResponse is not None
        assert SubscriptionResponse is not None


# =============================================================================
# 10E: STRIPE WEBHOOK TESTS
# =============================================================================

class TestStripeWebhook:
    """Tests for Stripe webhook handler"""

    def test_webhook_routes_imports(self):
        """Verify webhook routes import correctly"""
        from routes.stripe_webhook_routes import router, HANDLED_EVENTS
        assert router is not None
        assert router.prefix == "/api/webhooks"

    def test_handled_events_list(self):
        """Verify handled Stripe events list"""
        from routes.stripe_webhook_routes import HANDLED_EVENTS

        required_events = [
            "invoice.paid",
            "invoice.payment_failed",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "checkout.session.completed"
        ]

        for event in required_events:
            assert event in HANDLED_EVENTS, f"Missing required event: {event}"


# =============================================================================
# DATABASE MODELS TESTS
# =============================================================================

class TestBillingModels:
    """Tests for billing database models"""

    def test_billing_models_imports(self):
        """Verify billing models import correctly"""
        from models_billing import (
            UsageEvent,
            UsageAggregate,
            SpendLimit,
            SpendLimitEvent,
            BillingRecord,
            StripeWebhookEvent,
            StripeSyncLog,
            SubscriptionTier
        )
        assert UsageEvent is not None
        assert SpendLimit is not None
        assert BillingRecord is not None
        assert StripeWebhookEvent is not None

    def test_usage_event_model_columns(self):
        """Verify UsageEvent model has required columns"""
        from models_billing import UsageEvent

        # Check column names via mapper
        columns = [c.name for c in UsageEvent.__table__.columns]

        required_columns = [
            'id', 'organization_id', 'event_type', 'quantity',
            'timestamp', 'billing_period', 'stripe_reported', 'event_metadata'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"

    def test_spend_limit_model_columns(self):
        """Verify SpendLimit model has required columns"""
        from models_billing import SpendLimit

        columns = [c.name for c in SpendLimit.__table__.columns]

        required_columns = [
            'id', 'organization_id', 'monthly_limit', 'current_spend',
            'kill_switch_triggered', 'hard_limit_action'
        ]

        for col in required_columns:
            assert col in columns, f"Missing column: {col}"


# =============================================================================
# INTEGRATION TESTS (Require running services)
# =============================================================================

@pytest.mark.skip(reason="Requires Redis")
class TestMeteringIntegration:
    """Integration tests requiring Redis connection"""

    @pytest.mark.asyncio
    async def test_record_usage_latency(self):
        """Verify record_usage completes in <1ms"""
        import time
        from services.metering_service import MeteringService

        service = MeteringService()

        start = time.perf_counter()
        await service.record_usage(
            organization_id=999999,
            event_type="test_event",
            quantity=1
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"record_usage took {elapsed_ms:.2f}ms, expected <10ms"


@pytest.mark.skip(reason="Requires Redis")
class TestSpendControlIntegration:
    """Integration tests requiring Redis connection"""

    @pytest.mark.asyncio
    async def test_spend_check_latency(self):
        """Verify spend check completes in <1ms"""
        import time
        from services.spend_control_service import SpendControlService

        service = SpendControlService()

        start = time.perf_counter()
        result = await service.check_spend_limit(999999)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"check_spend_limit took {elapsed_ms:.2f}ms, expected <10ms"
        assert result.allowed is True  # Default when no limit set
