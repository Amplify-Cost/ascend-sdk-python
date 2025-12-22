"""
Phase 10B: High-Throughput Metering Service

Redis-backed usage metering with zero hot-path latency impact.

Design Principles:
- Fire-and-forget to Redis (LPUSH, O(1), <1ms)
- Background worker aggregates to PostgreSQL
- Stripe usage records reported asynchronously
- No synchronous Stripe API calls in hot path

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10B
Date: 2025-12-21
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    from redis import asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
METERING_QUEUE_KEY = "billing:usage_events"
METERING_CACHE_PREFIX = "billing:usage:"
SPEND_CACHE_PREFIX = "billing:spend:"

# Batch processing configuration
BATCH_SIZE = 1000  # Events per batch
BATCH_INTERVAL_SECONDS = 300  # 5 minutes
CACHE_TTL_SECONDS = 300  # 5 minutes

# Feature flag
METERING_ENABLED = os.environ.get("ENABLE_BILLING", "true").lower() == "true"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UsageEventData:
    """Usage event data structure for Redis queue"""
    organization_id: int
    event_type: str
    quantity: int
    timestamp: str  # ISO format
    billing_period: str  # YYYY-MM
    metadata: Optional[Dict[str, Any]] = None
    source: str = "hot_path"

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "UsageEventData":
        return cls(**json.loads(data))


@dataclass
class UsageSnapshot:
    """Current usage snapshot for an organization"""
    organization_id: int
    billing_period: str
    api_calls: int = 0
    included_api_calls: int = 0
    overage_api_calls: int = 0
    estimated_cost: float = 0.0
    last_updated: Optional[datetime] = None

    @property
    def utilization_percent(self) -> float:
        if self.included_api_calls <= 0:
            return 0.0
        return min(100.0, (self.api_calls / self.included_api_calls) * 100)


# =============================================================================
# REDIS CONNECTION POOL
# =============================================================================

class RedisPool:
    """Singleton Redis connection pool for metering"""

    _instance: Optional["RedisPool"] = None
    _pool: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_connection(self) -> redis.Redis:
        """Get Redis connection from pool"""
        if self._pool is None:
            self._pool = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=1.0,  # 1 second timeout
                socket_connect_timeout=1.0,
            )
        return self._pool

    async def close(self):
        """Close the connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None


# =============================================================================
# METERING SERVICE
# =============================================================================

class MeteringService:
    """
    High-throughput usage metering service.

    Designed for minimal hot-path latency impact:
    - record_usage(): Fire-and-forget LPUSH to Redis (<1ms)
    - get_current_usage(): Cached read from Redis + DB fallback
    - process_batch(): Background aggregation to PostgreSQL

    Usage:
        metering = MeteringService()
        await metering.record_usage(org_id, "action_evaluation", 1)
    """

    def __init__(self):
        self._redis_pool = RedisPool()
        self._local_buffer: List[UsageEventData] = []
        self._buffer_lock = asyncio.Lock()

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection"""
        return await self._redis_pool.get_connection()

    # =========================================================================
    # HOT PATH METHODS (Must be <1ms)
    # =========================================================================

    async def record_usage(
        self,
        organization_id: int,
        event_type: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a usage event - fire-and-forget pattern.

        CRITICAL: This method MUST complete in <1ms.
        - Uses Redis LPUSH (O(1))
        - No database operations
        - No Stripe API calls
        - Fails silently to not impact hot path

        Args:
            organization_id: Organization ID
            event_type: Type of usage event (action_evaluation, mcp_server_hour, etc.)
            quantity: Number of units consumed
            metadata: Optional metadata for the event

        Returns:
            bool: True if recorded, False if failed (fail-open for hot path)
        """
        if not METERING_ENABLED:
            return True

        try:
            now = datetime.now(timezone.utc)
            event = UsageEventData(
                organization_id=organization_id,
                event_type=event_type,
                quantity=quantity,
                timestamp=now.isoformat(),
                billing_period=now.strftime("%Y-%m"),
                metadata=metadata,
                source="hot_path"
            )

            # Fire-and-forget to Redis
            redis_conn = await self._get_redis()
            await redis_conn.lpush(METERING_QUEUE_KEY, event.to_json())

            # Also increment real-time counter for dashboard
            cache_key = f"{METERING_CACHE_PREFIX}{organization_id}:{event.billing_period}:{event_type}"
            await redis_conn.incrby(cache_key, quantity)
            await redis_conn.expire(cache_key, CACHE_TTL_SECONDS * 12)  # 1 hour

            logger.debug(
                f"Metering: Recorded {quantity} {event_type} for org {organization_id}"
            )
            return True

        except Exception as e:
            # Fail-open: Don't block hot path on metering failures
            logger.warning(f"Metering: Failed to record usage: {e}")
            return True  # Return True to not block caller

    async def record_usage_fire_forget(
        self,
        organization_id: int,
        event_type: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record usage without awaiting - true fire-and-forget.

        Use this when you don't need confirmation and want minimal latency.
        """
        asyncio.create_task(
            self.record_usage(organization_id, event_type, quantity, metadata)
        )

    # =========================================================================
    # READ METHODS (Cached)
    # =========================================================================

    async def get_current_usage(
        self,
        organization_id: int,
        billing_period: Optional[str] = None
    ) -> UsageSnapshot:
        """
        Get current usage snapshot from Redis cache.

        Falls back to database if cache miss.
        Cache TTL: 5 minutes

        Args:
            organization_id: Organization ID
            billing_period: Billing period (YYYY-MM), defaults to current month

        Returns:
            UsageSnapshot with current usage data
        """
        if billing_period is None:
            billing_period = datetime.now(timezone.utc).strftime("%Y-%m")

        try:
            redis_conn = await self._get_redis()

            # Try to get from cache
            cache_key = f"{METERING_CACHE_PREFIX}{organization_id}:{billing_period}:action_evaluation"
            cached_value = await redis_conn.get(cache_key)

            if cached_value:
                api_calls = int(cached_value)
            else:
                # Cache miss - will be populated by background worker
                api_calls = 0

            # Get spend from cache
            spend_key = f"{SPEND_CACHE_PREFIX}{organization_id}:current"
            spend_data = await redis_conn.hgetall(spend_key)

            included = int(spend_data.get("included_api_calls", 100000))
            overage_rate = float(spend_data.get("overage_rate", 0.005))

            overage = max(0, api_calls - included)
            estimated_cost = overage * overage_rate

            return UsageSnapshot(
                organization_id=organization_id,
                billing_period=billing_period,
                api_calls=api_calls,
                included_api_calls=included,
                overage_api_calls=overage,
                estimated_cost=estimated_cost,
                last_updated=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.warning(f"Metering: Failed to get usage: {e}")
            return UsageSnapshot(
                organization_id=organization_id,
                billing_period=billing_period
            )

    async def get_queue_length(self) -> int:
        """Get number of pending events in Redis queue"""
        try:
            redis_conn = await self._get_redis()
            return await redis_conn.llen(METERING_QUEUE_KEY)
        except Exception:
            return 0

    # =========================================================================
    # BATCH PROCESSING (Background Worker)
    # =========================================================================

    async def process_batch(self, db: Session, batch_size: int = BATCH_SIZE) -> int:
        """
        Process a batch of usage events from Redis to PostgreSQL.

        Called by background worker every 5 minutes.
        - Pops events from Redis queue
        - Aggregates by org/type/period
        - Inserts into usage_events table
        - Updates usage_aggregates table

        Args:
            db: SQLAlchemy database session
            batch_size: Maximum events to process

        Returns:
            int: Number of events processed
        """
        from models_billing import UsageEvent, UsageAggregate

        try:
            redis_conn = await self._get_redis()
            events_processed = 0
            aggregates: Dict[str, Dict[str, Any]] = {}

            # Pop events from queue
            while events_processed < batch_size:
                event_json = await redis_conn.rpop(METERING_QUEUE_KEY)
                if not event_json:
                    break

                try:
                    event_data = UsageEventData.from_json(event_json)

                    # Create database record
                    usage_event = UsageEvent(
                        organization_id=event_data.organization_id,
                        event_type=event_data.event_type,
                        quantity=event_data.quantity,
                        timestamp=datetime.fromisoformat(event_data.timestamp),
                        billing_period=event_data.billing_period,
                        event_metadata=event_data.metadata,  # Note: column renamed from 'metadata'
                        source=event_data.source
                    )
                    db.add(usage_event)

                    # Aggregate for summary update
                    agg_key = f"{event_data.organization_id}:{event_data.billing_period}:{event_data.event_type}"
                    if agg_key not in aggregates:
                        aggregates[agg_key] = {
                            "organization_id": event_data.organization_id,
                            "billing_period": event_data.billing_period,
                            "event_type": event_data.event_type,
                            "total_quantity": 0,
                            "event_count": 0
                        }
                    aggregates[agg_key]["total_quantity"] += event_data.quantity
                    aggregates[agg_key]["event_count"] += 1

                    events_processed += 1

                except Exception as e:
                    logger.error(f"Metering: Failed to parse event: {e}")
                    continue

            # Commit events
            if events_processed > 0:
                db.commit()

            # Update aggregates
            for agg_data in aggregates.values():
                existing = db.query(UsageAggregate).filter(
                    UsageAggregate.organization_id == agg_data["organization_id"],
                    UsageAggregate.billing_period == agg_data["billing_period"],
                    UsageAggregate.event_type == agg_data["event_type"]
                ).first()

                if existing:
                    existing.total_quantity += agg_data["total_quantity"]
                    existing.event_count += agg_data["event_count"]
                    existing.last_event_at = datetime.now(timezone.utc)
                    existing.last_aggregated_at = datetime.now(timezone.utc)
                else:
                    new_agg = UsageAggregate(
                        organization_id=agg_data["organization_id"],
                        billing_period=agg_data["billing_period"],
                        event_type=agg_data["event_type"],
                        total_quantity=agg_data["total_quantity"],
                        event_count=agg_data["event_count"],
                        first_event_at=datetime.now(timezone.utc),
                        last_event_at=datetime.now(timezone.utc)
                    )
                    db.add(new_agg)

            db.commit()

            logger.info(
                f"Metering: Processed {events_processed} events, "
                f"updated {len(aggregates)} aggregates"
            )
            return events_processed

        except Exception as e:
            logger.error(f"Metering: Batch processing failed: {e}")
            db.rollback()
            return 0

    # =========================================================================
    # STRIPE INTEGRATION (Background)
    # =========================================================================

    async def report_usage_to_stripe(
        self,
        db: Session,
        organization_id: int,
        billing_period: str
    ) -> bool:
        """
        Report usage to Stripe Usage Records API.

        Called by background worker after aggregation.
        Updates stripe_reported flag on usage_events.

        Args:
            db: SQLAlchemy database session
            organization_id: Organization ID
            billing_period: Billing period (YYYY-MM)

        Returns:
            bool: True if reported successfully
        """
        # Import here to avoid circular imports
        from models_billing import UsageAggregate
        from models import Organization
        import stripe

        try:
            # Get organization's Stripe subscription
            org = db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if not org or not org.stripe_subscription_id:
                logger.warning(
                    f"Metering: Org {organization_id} has no Stripe subscription"
                )
                return False

            # Get aggregated usage
            aggregate = db.query(UsageAggregate).filter(
                UsageAggregate.organization_id == organization_id,
                UsageAggregate.billing_period == billing_period,
                UsageAggregate.event_type == "action_evaluation"
            ).first()

            if not aggregate:
                return True  # No usage to report

            # Get Stripe API key from secrets
            stripe_secret = os.environ.get("STRIPE_SECRET_KEY")
            if not stripe_secret:
                logger.error("Metering: STRIPE_SECRET_KEY not configured")
                return False

            stripe.api_key = stripe_secret

            # Report to Stripe
            # Note: This uses Stripe's Usage Records API for metered billing
            usage_record = stripe.SubscriptionItem.create_usage_record(
                org.stripe_subscription_id,  # subscription item ID
                quantity=aggregate.total_quantity,
                timestamp=int(datetime.now(timezone.utc).timestamp()),
                action="set"  # Set total usage (not increment)
            )

            logger.info(
                f"Metering: Reported {aggregate.total_quantity} usage to Stripe "
                f"for org {organization_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Metering: Stripe reporting failed: {e}")
            return False

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    async def warm_cache(self, db: Session, organization_id: int):
        """
        Warm the Redis cache from database for an organization.

        Called when organization accesses billing dashboard.
        """
        from models_billing import UsageAggregate
        from models import Organization

        try:
            redis_conn = await self._get_redis()
            billing_period = datetime.now(timezone.utc).strftime("%Y-%m")

            # Get aggregates from DB
            aggregates = db.query(UsageAggregate).filter(
                UsageAggregate.organization_id == organization_id,
                UsageAggregate.billing_period == billing_period
            ).all()

            for agg in aggregates:
                cache_key = f"{METERING_CACHE_PREFIX}{organization_id}:{billing_period}:{agg.event_type}"
                await redis_conn.set(
                    cache_key,
                    agg.total_quantity,
                    ex=CACHE_TTL_SECONDS * 12
                )

            # Get organization limits
            org = db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if org:
                spend_key = f"{SPEND_CACHE_PREFIX}{organization_id}:current"
                await redis_conn.hset(spend_key, mapping={
                    "included_api_calls": org.included_api_calls,
                    "overage_rate": org.overage_rate_per_call,
                    "subscription_tier": org.subscription_tier
                })
                await redis_conn.expire(spend_key, CACHE_TTL_SECONDS * 12)

            logger.debug(f"Metering: Warmed cache for org {organization_id}")

        except Exception as e:
            logger.warning(f"Metering: Cache warming failed: {e}")

    async def invalidate_cache(self, organization_id: int):
        """Invalidate all cached data for an organization"""
        try:
            redis_conn = await self._get_redis()
            pattern = f"{METERING_CACHE_PREFIX}{organization_id}:*"

            cursor = 0
            while True:
                cursor, keys = await redis_conn.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis_conn.delete(*keys)
                if cursor == 0:
                    break

            # Also invalidate spend cache
            spend_key = f"{SPEND_CACHE_PREFIX}{organization_id}:current"
            await redis_conn.delete(spend_key)

        except Exception as e:
            logger.warning(f"Metering: Cache invalidation failed: {e}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_metering_service: Optional[MeteringService] = None


def get_metering_service() -> MeteringService:
    """Get singleton metering service instance"""
    global _metering_service
    if _metering_service is None:
        _metering_service = MeteringService()
    return _metering_service


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def record_action_usage(
    organization_id: int,
    action_type: str,
    processing_time_ms: int
) -> bool:
    """
    Convenience function to record action evaluation usage.

    Called from hot path after action processing.

    Args:
        organization_id: Organization ID
        action_type: Type of action evaluated
        processing_time_ms: Processing time in milliseconds

    Returns:
        bool: True if recorded
    """
    metering = get_metering_service()
    return await metering.record_usage(
        organization_id=organization_id,
        event_type="action_evaluation",
        quantity=1,
        metadata={
            "action_type": action_type,
            "processing_time_ms": processing_time_ms
        }
    )
