"""
BEHAV-001: Agent Rate Limiter Service

Per-agent, per-tenant rate limiting with Redis backend.

Features:
- Sliding window rate limiting using Redis sorted sets
- Per-agent and per-tenant aggregate limits
- Priority tiers for critical agents
- Fail-closed on Redis unavailability (SECURITY REQUIREMENT)
- Comprehensive audit logging
- Configuration caching with TTL

Algorithm: Sliding Window using Redis Sorted Sets
- More accurate than fixed window counters
- Prevents burst at window boundaries
- O(log N) operations per check

Compliance: SOC 2 A1.1, NIST 800-53 SC-5, SOC 2 CC6.1
Author: Enterprise Security Team
Version: 1.0.0
"""

import logging
import time
import os
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy.orm import Session

# Import models
from models_rate_limits import (
    OrgRateLimitConfig,
    AgentRateLimitOverride,
    RateLimitEvent,
    RateLimitResult
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Environment variable to enable/disable rate limiting globally
RATE_LIMIT_ENABLED = os.getenv("ASCEND_RATE_LIMIT_ENABLED", "true").lower() == "true"

# Redis connection settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cache TTL for config lookups (seconds)
CONFIG_CACHE_TTL = int(os.getenv("RATE_LIMIT_CONFIG_CACHE_TTL", "60"))

# Default limits when no config exists
DEFAULT_AGENT_LIMIT_PER_MINUTE = 100
DEFAULT_TENANT_LIMIT_PER_MINUTE = 1000


# =============================================================================
# Rate Limiter Service
# =============================================================================

class AgentRateLimiter:
    """
    Per-agent, per-tenant rate limiting with Redis backend.

    SECURITY: Fail-closed on Redis unavailability.
    If Redis is down, all actions are DENIED to prevent uncontrolled access.
    """

    def __init__(self, db: Session, redis_client=None):
        """
        Initialize rate limiter.

        Args:
            db: SQLAlchemy database session
            redis_client: Optional Redis client (will create one if not provided)
        """
        self.db = db
        self._redis = redis_client
        self._config_cache: Dict[int, Tuple[OrgRateLimitConfig, float]] = {}
        self._override_cache: Dict[str, Tuple[Optional[AgentRateLimitOverride], float]] = {}

        logger.info("BEHAV-001: AgentRateLimiter initialized")

    @property
    def redis(self):
        """Lazy initialization of Redis client."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                logger.info(f"BEHAV-001: Redis connected to {REDIS_URL}")
            except Exception as e:
                logger.error(f"BEHAV-001: Failed to connect to Redis: {e}")
                self._redis = None
        return self._redis

    async def check_and_increment(
        self,
        org_id: int,
        agent_id: str,
        action_type: str = None,
        ip_address: str = None,
        correlation_id: str = None
    ) -> RateLimitResult:
        """
        Check rate limits and increment counters atomically.

        SECURITY: Fail-closed - denies if Redis unavailable.

        Args:
            org_id: Organization ID
            agent_id: Agent identifier
            action_type: Type of action being performed
            ip_address: Client IP address (for logging)
            correlation_id: Request correlation ID

        Returns:
            RateLimitResult with allowed/denied and metadata
        """
        # Check if rate limiting is globally disabled
        if not RATE_LIMIT_ENABLED:
            logger.debug("BEHAV-001: Rate limiting disabled globally")
            return RateLimitResult(allowed=True, reason="Rate limiting disabled")

        try:
            # Load configuration (cached)
            config = await self._get_org_config(org_id)
            if not config or not config.enabled:
                logger.debug(f"BEHAV-001: Rate limiting disabled for org {org_id}")
                return RateLimitResult(allowed=True, reason="Rate limiting disabled for org")

            # Get effective limits for this agent
            agent_limit = await self._get_agent_limit(org_id, agent_id, config)
            tenant_limit = config.actions_per_minute

            # Check Redis availability
            if self.redis is None:
                logger.error("BEHAV-001: Redis unavailable, DENYING action (fail-closed)")
                await self._log_event(
                    org_id, agent_id, "blocked", "redis_unavailable",
                    0, 0, action_type, ip_address, correlation_id
                )
                return RateLimitResult(
                    allowed=False,
                    reason="Rate limiting service unavailable",
                    retry_after=60
                )

            # Get current timestamp
            now = time.time()
            window_start = now - 60  # 1-minute sliding window

            # Check agent-level limit
            agent_key = f"rate:agent:{org_id}:{agent_id}"
            agent_count = await self._sliding_window_increment(agent_key, now, window_start)

            if agent_count > agent_limit:
                logger.warning(
                    f"BEHAV-001: Agent rate limit exceeded - org={org_id}, "
                    f"agent={agent_id}, count={agent_count}, limit={agent_limit}"
                )
                await self._log_event(
                    org_id, agent_id, "blocked", "agent_minute",
                    agent_count, agent_limit, action_type, ip_address, correlation_id
                )
                return RateLimitResult(
                    allowed=False,
                    reason=f"Agent rate limit exceeded ({agent_limit}/min)",
                    retry_after=int(60 - (now % 60)),
                    limit_type="agent_minute",
                    current_agent_count=agent_count,
                    agent_limit=agent_limit
                )

            # Check tenant-level limit
            tenant_key = f"rate:tenant:{org_id}"
            tenant_count = await self._sliding_window_increment(tenant_key, now, window_start)

            if tenant_count > tenant_limit:
                logger.warning(
                    f"BEHAV-001: Tenant rate limit exceeded - org={org_id}, "
                    f"count={tenant_count}, limit={tenant_limit}"
                )
                await self._log_event(
                    org_id, agent_id, "blocked", "tenant_minute",
                    tenant_count, tenant_limit, action_type, ip_address, correlation_id
                )
                return RateLimitResult(
                    allowed=False,
                    reason=f"Tenant rate limit exceeded ({tenant_limit}/min)",
                    retry_after=60,
                    limit_type="tenant_minute",
                    current_agent_count=agent_count,
                    current_tenant_count=tenant_count,
                    agent_limit=agent_limit,
                    tenant_limit=tenant_limit
                )

            # Both limits OK
            logger.debug(
                f"BEHAV-001: Rate limit check passed - org={org_id}, agent={agent_id}, "
                f"agent_count={agent_count}/{agent_limit}, tenant_count={tenant_count}/{tenant_limit}"
            )

            return RateLimitResult(
                allowed=True,
                current_agent_count=agent_count,
                current_tenant_count=tenant_count,
                agent_limit=agent_limit,
                tenant_limit=tenant_limit,
                reset_at=datetime.fromtimestamp(now + 60, tz=UTC)
            )

        except Exception as e:
            logger.error(f"BEHAV-001: Rate limit check failed: {e}", exc_info=True)
            # FAIL-CLOSED: Deny on any error
            return RateLimitResult(
                allowed=False,
                reason="Rate limit check failed",
                retry_after=60
            )

    async def _sliding_window_increment(
        self,
        key: str,
        now: float,
        window_start: float
    ) -> int:
        """
        Sliding window rate limiting using Redis sorted sets.

        Algorithm:
        1. Remove entries older than window_start
        2. Add current timestamp
        3. Count entries in window
        4. Set expiry for auto-cleanup

        Args:
            key: Redis key for this counter
            now: Current timestamp
            window_start: Start of sliding window

        Returns:
            Number of entries in the window
        """
        try:
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Add current request (use timestamp as both score and member for uniqueness)
            # Add random suffix to handle sub-millisecond requests
            member = f"{now}:{id(pipe)}"
            pipe.zadd(key, {member: now})

            # Count entries in window
            pipe.zcard(key)

            # Set expiry (window + buffer)
            pipe.expire(key, 65)

            results = await pipe.execute()
            return results[2]  # zcard result

        except Exception as e:
            logger.error(f"BEHAV-001: Redis operation failed: {e}")
            raise

    async def _get_org_config(self, org_id: int) -> Optional[OrgRateLimitConfig]:
        """
        Get organization rate limit config with caching.

        Args:
            org_id: Organization ID

        Returns:
            OrgRateLimitConfig or None
        """
        # Check cache
        if org_id in self._config_cache:
            config, cached_at = self._config_cache[org_id]
            if time.time() - cached_at < CONFIG_CACHE_TTL:
                return config

        # Load from database
        config = self.db.query(OrgRateLimitConfig).filter(
            OrgRateLimitConfig.organization_id == org_id
        ).first()

        if config is None:
            # Create default config for this org
            config = OrgRateLimitConfig(
                organization_id=org_id,
                enabled=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"BEHAV-001: Created default rate limit config for org {org_id}")

        # Cache it
        self._config_cache[org_id] = (config, time.time())
        return config

    async def _get_agent_limit(
        self,
        org_id: int,
        agent_id: str,
        config: OrgRateLimitConfig
    ) -> int:
        """
        Get effective rate limit for an agent.

        Checks for agent-specific override, otherwise uses org default.

        Args:
            org_id: Organization ID
            agent_id: Agent identifier
            config: Org rate limit config

        Returns:
            Effective actions_per_minute limit
        """
        cache_key = f"{org_id}:{agent_id}"

        # Check cache
        if cache_key in self._override_cache:
            override, cached_at = self._override_cache[cache_key]
            if time.time() - cached_at < CONFIG_CACHE_TTL:
                if override and override.is_active:
                    return override.get_effective_limit(config.agent_actions_per_minute)
                return config.agent_actions_per_minute

        # Load from database
        override = self.db.query(AgentRateLimitOverride).filter(
            AgentRateLimitOverride.organization_id == org_id,
            AgentRateLimitOverride.agent_id == agent_id,
            AgentRateLimitOverride.is_active == True
        ).first()

        # Cache it (even if None)
        self._override_cache[cache_key] = (override, time.time())

        if override:
            return override.get_effective_limit(config.agent_actions_per_minute)

        return config.agent_actions_per_minute

    async def _log_event(
        self,
        org_id: int,
        agent_id: str,
        event_type: str,
        limit_type: str,
        current_count: int,
        limit_value: int,
        action_type: str = None,
        ip_address: str = None,
        correlation_id: str = None
    ):
        """
        Log rate limit event to database.

        Args:
            org_id: Organization ID
            agent_id: Agent identifier
            event_type: Type of event (blocked, limit_reached, etc.)
            limit_type: Which limit was hit
            current_count: Current counter value
            limit_value: Limit value
            action_type: Action type being performed
            ip_address: Client IP
            correlation_id: Request correlation ID
        """
        try:
            event = RateLimitEvent(
                organization_id=org_id,
                agent_id=agent_id,
                event_type=event_type,
                limit_type=limit_type,
                current_count=current_count,
                limit_value=limit_value,
                action_type=action_type,
                ip_address=ip_address,
                correlation_id=correlation_id
            )
            self.db.add(event)
            self.db.commit()
        except Exception as e:
            logger.error(f"BEHAV-001: Failed to log rate limit event: {e}")
            # Don't fail the request just because logging failed

    async def get_usage(self, org_id: int) -> Dict[str, Any]:
        """
        Get current rate limit usage for an organization.

        Args:
            org_id: Organization ID

        Returns:
            Dictionary with current usage statistics
        """
        try:
            config = await self._get_org_config(org_id)
            if not config:
                return {"error": "No config found"}

            now = time.time()
            window_start = now - 60

            # Get tenant count
            tenant_key = f"rate:tenant:{org_id}"
            tenant_count = 0
            if self.redis:
                await self.redis.zremrangebyscore(tenant_key, 0, window_start)
                tenant_count = await self.redis.zcard(tenant_key) or 0

            # Get agent counts
            agents = []
            overrides = self.db.query(AgentRateLimitOverride).filter(
                AgentRateLimitOverride.organization_id == org_id,
                AgentRateLimitOverride.is_active == True
            ).all()

            for override in overrides:
                agent_key = f"rate:agent:{org_id}:{override.agent_id}"
                agent_count = 0
                if self.redis:
                    await self.redis.zremrangebyscore(agent_key, 0, window_start)
                    agent_count = await self.redis.zcard(agent_key) or 0

                agents.append({
                    "agent_id": override.agent_id,
                    "current_minute": agent_count,
                    "limit_minute": override.get_effective_limit(config.agent_actions_per_minute),
                    "priority_tier": override.priority_tier
                })

            return {
                "tenant": {
                    "current_minute": tenant_count,
                    "limit_minute": config.actions_per_minute,
                    "limit_hour": config.actions_per_hour,
                    "limit_day": config.actions_per_day
                },
                "agents": agents,
                "config": {
                    "enabled": config.enabled,
                    "agent_default_limit": config.agent_actions_per_minute
                }
            }

        except Exception as e:
            logger.error(f"BEHAV-001: Failed to get usage: {e}")
            return {"error": str(e)}

    def clear_cache(self):
        """Clear the configuration cache."""
        self._config_cache.clear()
        self._override_cache.clear()
        logger.info("BEHAV-001: Rate limit config cache cleared")


# =============================================================================
# Synchronous Wrapper (for non-async contexts)
# =============================================================================

class SyncAgentRateLimiter:
    """
    Synchronous wrapper for rate limiting.

    For use in synchronous FastAPI endpoints or other non-async contexts.
    """

    def __init__(self, db: Session, redis_client=None):
        self._async_limiter = AgentRateLimiter(db, redis_client)

    def check_and_increment(
        self,
        org_id: int,
        agent_id: str,
        action_type: str = None,
        ip_address: str = None,
        correlation_id: str = None
    ) -> RateLimitResult:
        """
        Synchronous version of check_and_increment.

        IMPORTANT: This runs the async code in a blocking manner.
        Prefer the async version when possible.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self._async_limiter.check_and_increment(
                org_id, agent_id, action_type, ip_address, correlation_id
            )
        )


# =============================================================================
# Factory Functions
# =============================================================================

def create_rate_limiter(db: Session, redis_client=None) -> AgentRateLimiter:
    """
    Factory function to create rate limiter instance.

    Args:
        db: Database session
        redis_client: Optional Redis client

    Returns:
        AgentRateLimiter instance
    """
    return AgentRateLimiter(db, redis_client)


def create_sync_rate_limiter(db: Session, redis_client=None) -> SyncAgentRateLimiter:
    """
    Factory function to create synchronous rate limiter instance.

    Args:
        db: Database session
        redis_client: Optional Redis client

    Returns:
        SyncAgentRateLimiter instance
    """
    return SyncAgentRateLimiter(db, redis_client)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'AgentRateLimiter',
    'SyncAgentRateLimiter',
    'create_rate_limiter',
    'create_sync_rate_limiter',
    'RATE_LIMIT_ENABLED'
]
