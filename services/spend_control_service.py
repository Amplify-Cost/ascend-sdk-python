"""
Phase 10C: Financial Kill-Switch & Spend Control Service

Enforces spending limits and provides financial kill-switch functionality.

Features:
- Per-org monthly spend limits
- Warning threshold notifications (80% default)
- Automatic kill-switch at 100%
- Manual override with audit trail
- Redis-cached for hot-path performance (<0.5ms)

Compliance: SOC 2 CC6.1, PCI-DSS 3.5
Engineer: OW-KAI Platform Engineering Team
Version: Phase 10C
Date: 2025-12-21
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis versions
    from redis import asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
SPEND_CACHE_PREFIX = "billing:spend:"
SPEND_CACHE_TTL = 60  # 1 minute cache
KILL_SWITCH_KEY_PREFIX = "billing:kill_switch:"

# Feature flags
SPEND_LIMITS_ENABLED = os.environ.get("ENABLE_SPEND_LIMITS", "true").lower() == "true"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SpendCheckResult:
    """Result of spend limit check"""
    allowed: bool
    blocked: bool = False
    current_spend: float = 0.0
    monthly_limit: float = 0.0
    utilization_percent: float = 0.0
    status: str = "active"
    warning_triggered: bool = False
    kill_switch_active: bool = False
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SpendLimitConfig:
    """Spend limit configuration for an organization"""
    organization_id: int
    monthly_limit: float
    warning_threshold_percent: float = 80.0
    hard_limit_action: str = "block"  # block, notify, none
    current_spend: float = 0.0
    limit_enforced: bool = True
    kill_switch_triggered: bool = False


# =============================================================================
# REDIS CONNECTION
# =============================================================================

class RedisPool:
    """Singleton Redis connection pool"""
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_connection(self) -> redis.Redis:
        if self._pool is None:
            self._pool = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
            )
        return self._pool


# =============================================================================
# SPEND CONTROL SERVICE
# =============================================================================

class SpendControlService:
    """
    Financial kill-switch with configurable spend limits.

    Hot-path integration:
    - check_spend_limit(): Called before each action (<0.5ms via Redis)
    - Uses fail-open pattern if Redis unavailable

    Background operations:
    - update_spend(): Updates current spend from aggregates
    - trigger_kill_switch(): Blocks all actions for org
    - release_kill_switch(): Restores access with audit
    """

    def __init__(self):
        self._redis_pool = RedisPool()

    async def _get_redis(self) -> redis.Redis:
        return await self._redis_pool.get_connection()

    # =========================================================================
    # HOT PATH METHODS (Must be <0.5ms)
    # =========================================================================

    async def check_spend_limit(self, organization_id: int) -> SpendCheckResult:
        """
        Check if organization is within spend limits.

        CRITICAL: This method MUST complete in <0.5ms.
        - Uses Redis GET (O(1))
        - Fails open if Redis unavailable
        - No database operations

        Args:
            organization_id: Organization ID

        Returns:
            SpendCheckResult with allowed/blocked status
        """
        if not SPEND_LIMITS_ENABLED:
            return SpendCheckResult(allowed=True)

        try:
            redis_conn = await self._get_redis()

            # Check kill switch first (fastest path for blocked orgs)
            kill_switch_key = f"{KILL_SWITCH_KEY_PREFIX}{organization_id}"
            is_killed = await redis_conn.get(kill_switch_key)

            if is_killed:
                return SpendCheckResult(
                    allowed=False,
                    blocked=True,
                    status="killed",
                    kill_switch_active=True,
                    message="Spend limit exceeded. Contact support to restore access."
                )

            # Get cached spend data
            cache_key = f"{SPEND_CACHE_PREFIX}{organization_id}:limits"
            cached = await redis_conn.hgetall(cache_key)

            if not cached:
                # Cache miss - allow and refresh in background
                return SpendCheckResult(allowed=True)

            current_spend = float(cached.get("current_spend", 0))
            monthly_limit = float(cached.get("monthly_limit", 999999))
            warning_threshold = float(cached.get("warning_threshold", 80))
            limit_enforced = cached.get("limit_enforced", "true") == "true"
            hard_limit_action = cached.get("hard_limit_action", "block")

            # Calculate utilization
            utilization = (current_spend / monthly_limit * 100) if monthly_limit > 0 else 0

            # Check if limit exceeded
            if limit_enforced and current_spend >= monthly_limit:
                if hard_limit_action == "block":
                    return SpendCheckResult(
                        allowed=False,
                        blocked=True,
                        current_spend=current_spend,
                        monthly_limit=monthly_limit,
                        utilization_percent=utilization,
                        status="exceeded",
                        message=f"Monthly spend limit of ${monthly_limit:.2f} exceeded."
                    )

            # Check warning threshold
            warning_triggered = utilization >= warning_threshold

            return SpendCheckResult(
                allowed=True,
                blocked=False,
                current_spend=current_spend,
                monthly_limit=monthly_limit,
                utilization_percent=utilization,
                status="warning" if warning_triggered else "active",
                warning_triggered=warning_triggered
            )

        except Exception as e:
            # Fail-open: Don't block on Redis failures
            logger.warning(f"SpendControl: Check failed, allowing: {e}")
            return SpendCheckResult(allowed=True)

    async def is_blocked(self, organization_id: int) -> bool:
        """Quick check if org is blocked (for middleware)"""
        result = await self.check_spend_limit(organization_id)
        return result.blocked

    # =========================================================================
    # CONFIGURATION METHODS
    # =========================================================================

    async def set_spend_limit(
        self,
        db: Session,
        organization_id: int,
        monthly_limit: float,
        warning_threshold_percent: float = 80.0,
        hard_limit_action: str = "block",
        user_id: Optional[int] = None
    ) -> bool:
        """
        Set or update spend limit for an organization.

        Creates SpendLimit record in DB and caches in Redis.
        Records audit event for compliance.

        Args:
            db: Database session
            organization_id: Organization ID
            monthly_limit: Monthly spend limit in USD
            warning_threshold_percent: Warning threshold (default 80%)
            hard_limit_action: Action at limit (block/notify/none)
            user_id: User making the change (for audit)

        Returns:
            bool: True if successful
        """
        from models_billing import SpendLimit, SpendLimitEvent

        try:
            # Get or create spend limit record
            spend_limit = db.query(SpendLimit).filter(
                SpendLimit.organization_id == organization_id
            ).first()

            old_values = None
            if spend_limit:
                old_values = {
                    "monthly_limit": spend_limit.monthly_limit,
                    "warning_threshold_percent": spend_limit.warning_threshold_percent,
                    "hard_limit_action": spend_limit.hard_limit_action
                }
                spend_limit.monthly_limit = monthly_limit
                spend_limit.warning_threshold_percent = warning_threshold_percent
                spend_limit.hard_limit_action = hard_limit_action
                spend_limit.updated_at = datetime.now(timezone.utc)
            else:
                spend_limit = SpendLimit(
                    organization_id=organization_id,
                    monthly_limit=monthly_limit,
                    warning_threshold_percent=warning_threshold_percent,
                    hard_limit_action=hard_limit_action,
                    current_billing_period=datetime.now(timezone.utc).strftime("%Y-%m")
                )
                db.add(spend_limit)

            # Record audit event
            event = SpendLimitEvent(
                organization_id=organization_id,
                event_type="limit_set" if old_values is None else "limit_updated",
                previous_value=old_values,
                new_value={
                    "monthly_limit": monthly_limit,
                    "warning_threshold_percent": warning_threshold_percent,
                    "hard_limit_action": hard_limit_action
                },
                triggered_by=f"user:{user_id}" if user_id else "system",
                user_id=user_id
            )
            db.add(event)
            db.commit()

            # Update Redis cache
            await self._update_cache(spend_limit)

            logger.info(
                f"SpendControl: Set limit ${monthly_limit:.2f} for org {organization_id}"
            )
            return True

        except Exception as e:
            logger.error(f"SpendControl: Failed to set limit: {e}")
            db.rollback()
            return False

    async def get_spend_limit(
        self,
        db: Session,
        organization_id: int
    ) -> Optional[SpendLimitConfig]:
        """Get spend limit configuration for an organization"""
        from models_billing import SpendLimit

        spend_limit = db.query(SpendLimit).filter(
            SpendLimit.organization_id == organization_id
        ).first()

        if not spend_limit:
            return None

        return SpendLimitConfig(
            organization_id=organization_id,
            monthly_limit=spend_limit.monthly_limit,
            warning_threshold_percent=spend_limit.warning_threshold_percent,
            hard_limit_action=spend_limit.hard_limit_action,
            current_spend=spend_limit.current_spend,
            limit_enforced=spend_limit.limit_enforced,
            kill_switch_triggered=spend_limit.kill_switch_triggered
        )

    # =========================================================================
    # SPEND UPDATE METHODS (Background)
    # =========================================================================

    async def update_spend(
        self,
        db: Session,
        organization_id: int,
        new_spend: float
    ) -> SpendCheckResult:
        """
        Update current spend for an organization.

        Called by background worker after aggregating usage.
        Updates DB and Redis cache.
        Triggers warning/kill-switch if thresholds exceeded.

        Args:
            db: Database session
            organization_id: Organization ID
            new_spend: New current spend amount

        Returns:
            SpendCheckResult with updated status
        """
        from models_billing import SpendLimit, SpendLimitEvent

        try:
            spend_limit = db.query(SpendLimit).filter(
                SpendLimit.organization_id == organization_id
            ).first()

            if not spend_limit:
                return SpendCheckResult(allowed=True)

            old_spend = spend_limit.current_spend
            spend_limit.current_spend = new_spend
            spend_limit.updated_at = datetime.now(timezone.utc)

            # Check warning threshold
            utilization = (new_spend / spend_limit.monthly_limit * 100)
            warning_triggered = utilization >= spend_limit.warning_threshold_percent

            if warning_triggered and not spend_limit.warning_sent:
                spend_limit.warning_sent = True
                spend_limit.warning_sent_at = datetime.now(timezone.utc)
                spend_limit.status = "warning"

                # Record warning event
                event = SpendLimitEvent(
                    organization_id=organization_id,
                    event_type="warning_triggered",
                    previous_value={"spend": old_spend},
                    new_value={"spend": new_spend, "utilization": utilization},
                    triggered_by="system"
                )
                db.add(event)

                # TODO: Send notification to org admins
                logger.warning(
                    f"SpendControl: Warning threshold reached for org {organization_id} "
                    f"({utilization:.1f}%)"
                )

            # Check if limit exceeded
            limit_exceeded = new_spend >= spend_limit.monthly_limit

            if limit_exceeded and spend_limit.limit_enforced:
                if spend_limit.hard_limit_action == "block":
                    await self._trigger_kill_switch_internal(
                        db, organization_id, "spend_limit_exceeded"
                    )

            db.commit()

            # Update cache
            await self._update_cache(spend_limit)

            return SpendCheckResult(
                allowed=not (limit_exceeded and spend_limit.hard_limit_action == "block"),
                blocked=limit_exceeded and spend_limit.hard_limit_action == "block",
                current_spend=new_spend,
                monthly_limit=spend_limit.monthly_limit,
                utilization_percent=utilization,
                status=spend_limit.status,
                warning_triggered=warning_triggered
            )

        except Exception as e:
            logger.error(f"SpendControl: Failed to update spend: {e}")
            db.rollback()
            return SpendCheckResult(allowed=True)

    # =========================================================================
    # KILL SWITCH METHODS
    # =========================================================================

    async def trigger_kill_switch(
        self,
        db: Session,
        organization_id: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Manually trigger kill switch for an organization.

        Blocks all API access immediately.
        Records audit event for compliance.

        Args:
            db: Database session
            organization_id: Organization ID
            reason: Reason for triggering
            user_id: Admin user ID

        Returns:
            bool: True if successful
        """
        return await self._trigger_kill_switch_internal(
            db, organization_id, reason, user_id
        )

    async def _trigger_kill_switch_internal(
        self,
        db: Session,
        organization_id: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> bool:
        """Internal kill switch trigger"""
        from models_billing import SpendLimit, SpendLimitEvent

        try:
            spend_limit = db.query(SpendLimit).filter(
                SpendLimit.organization_id == organization_id
            ).first()

            if spend_limit:
                spend_limit.kill_switch_triggered = True
                spend_limit.kill_switch_triggered_at = datetime.now(timezone.utc)
                spend_limit.kill_switch_triggered_by = f"user:{user_id}" if user_id else "system"
                spend_limit.kill_switch_reason = reason
                spend_limit.status = "exceeded"

            # Record event
            event = SpendLimitEvent(
                organization_id=organization_id,
                event_type="kill_switch_triggered",
                new_value={"reason": reason},
                triggered_by=f"user:{user_id}" if user_id else "system",
                user_id=user_id
            )
            db.add(event)
            db.commit()

            # Set Redis kill switch flag
            redis_conn = await self._get_redis()
            kill_switch_key = f"{KILL_SWITCH_KEY_PREFIX}{organization_id}"
            await redis_conn.set(kill_switch_key, "1")  # No expiry - must be manually released

            logger.warning(
                f"SpendControl: Kill switch triggered for org {organization_id}: {reason}"
            )
            return True

        except Exception as e:
            logger.error(f"SpendControl: Failed to trigger kill switch: {e}")
            db.rollback()
            return False

    async def release_kill_switch(
        self,
        db: Session,
        organization_id: int,
        reason: str,
        user_id: int
    ) -> bool:
        """
        Release kill switch for an organization.

        Requires admin user for audit compliance.

        Args:
            db: Database session
            organization_id: Organization ID
            reason: Reason for release
            user_id: Admin user ID (required)

        Returns:
            bool: True if successful
        """
        from models_billing import SpendLimit, SpendLimitEvent

        try:
            spend_limit = db.query(SpendLimit).filter(
                SpendLimit.organization_id == organization_id
            ).first()

            if spend_limit:
                spend_limit.kill_switch_triggered = False
                spend_limit.kill_switch_released = True
                spend_limit.kill_switch_released_at = datetime.now(timezone.utc)
                spend_limit.kill_switch_released_by = user_id
                spend_limit.release_reason = reason
                spend_limit.status = "active"
                spend_limit.warning_sent = False  # Reset warning

            # Record event
            event = SpendLimitEvent(
                organization_id=organization_id,
                event_type="kill_switch_released",
                new_value={"reason": reason, "released_by": user_id},
                triggered_by=f"user:{user_id}",
                user_id=user_id
            )
            db.add(event)
            db.commit()

            # Remove Redis kill switch flag
            redis_conn = await self._get_redis()
            kill_switch_key = f"{KILL_SWITCH_KEY_PREFIX}{organization_id}"
            await redis_conn.delete(kill_switch_key)

            # Update cache
            if spend_limit:
                await self._update_cache(spend_limit)

            logger.info(
                f"SpendControl: Kill switch released for org {organization_id} "
                f"by user {user_id}: {reason}"
            )
            return True

        except Exception as e:
            logger.error(f"SpendControl: Failed to release kill switch: {e}")
            db.rollback()
            return False

    # =========================================================================
    # CACHE METHODS
    # =========================================================================

    async def _update_cache(self, spend_limit) -> bool:
        """Update Redis cache from SpendLimit model"""
        try:
            redis_conn = await self._get_redis()
            cache_key = f"{SPEND_CACHE_PREFIX}{spend_limit.organization_id}:limits"

            await redis_conn.hset(cache_key, mapping={
                "monthly_limit": str(spend_limit.monthly_limit),
                "current_spend": str(spend_limit.current_spend),
                "warning_threshold": str(spend_limit.warning_threshold_percent),
                "hard_limit_action": spend_limit.hard_limit_action,
                "limit_enforced": "true" if spend_limit.limit_enforced else "false",
                "status": spend_limit.status or "active"
            })
            await redis_conn.expire(cache_key, SPEND_CACHE_TTL * 10)  # 10 minutes

            return True

        except Exception as e:
            logger.warning(f"SpendControl: Cache update failed: {e}")
            return False

    async def warm_cache(self, db: Session, organization_id: int):
        """Warm cache from database"""
        from models_billing import SpendLimit

        spend_limit = db.query(SpendLimit).filter(
            SpendLimit.organization_id == organization_id
        ).first()

        if spend_limit:
            await self._update_cache(spend_limit)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_spend_control_service: Optional[SpendControlService] = None


def get_spend_control_service() -> SpendControlService:
    """Get singleton spend control service instance"""
    global _spend_control_service
    if _spend_control_service is None:
        _spend_control_service = SpendControlService()
    return _spend_control_service


# =============================================================================
# FASTAPI DEPENDENCY
# =============================================================================

async def check_spend_limit_dependency(organization_id: int) -> SpendCheckResult:
    """
    FastAPI dependency for checking spend limits.

    Usage:
        @router.post("/action")
        async def submit_action(
            spend_check: SpendCheckResult = Depends(check_spend_limit_dependency)
        ):
            if spend_check.blocked:
                raise HTTPException(402, spend_check.message)
    """
    service = get_spend_control_service()
    return await service.check_spend_limit(organization_id)
