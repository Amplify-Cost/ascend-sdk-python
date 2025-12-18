"""
BEHAV-001: Rate Limiting Models

Enterprise per-agent, per-tenant rate limiting with Redis backend.

Features:
- Organization-level rate limit configuration
- Per-agent override capabilities
- Priority tiers for critical agents
- Immutable event logging for compliance

Compliance: SOC 2 A1.1, NIST 800-53 SC-5, SOC 2 CC6.1
Author: Enterprise Security Team
Version: 1.0.0
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    Text, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from database import Base
from dataclasses import dataclass
from typing import Optional, Dict, Any


# =============================================================================
# BEHAV-001: Rate Limit Configuration Models
# =============================================================================


class OrgRateLimitConfig(Base):
    """
    Organization-level rate limit configuration.

    Each organization has exactly ONE configuration record that defines
    default rate limits for all agents and tenant-wide aggregate limits.

    Compliance: SOC 2 A1.1 (Availability Controls), NIST SC-5 (DoS Protection)
    """
    __tablename__ = "org_rate_limit_config"

    __table_args__ = (
        UniqueConstraint('organization_id', name='uq_org_rate_limit_config_org'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # Tenant-wide limits (aggregate across all agents)
    actions_per_minute = Column(Integer, default=1000, nullable=False)
    actions_per_hour = Column(Integer, default=50000, nullable=False)
    actions_per_day = Column(Integer, default=500000, nullable=False)

    # Default agent limits (can be overridden per-agent)
    agent_actions_per_minute = Column(Integer, default=100, nullable=False)
    agent_actions_per_hour = Column(Integer, default=5000, nullable=False)

    # Burst handling
    burst_multiplier = Column(Numeric(3, 2), default=1.5, nullable=False)
    burst_window_seconds = Column(Integer, default=10, nullable=False)

    # Response behavior
    rate_limit_response_code = Column(Integer, default=429, nullable=False)
    include_retry_after = Column(Boolean, default=True, nullable=False)

    # Feature toggle
    enabled = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "organization_id": self.organization_id,
            "tenant_limits": {
                "actions_per_minute": self.actions_per_minute,
                "actions_per_hour": self.actions_per_hour,
                "actions_per_day": self.actions_per_day
            },
            "agent_defaults": {
                "actions_per_minute": self.agent_actions_per_minute,
                "actions_per_hour": self.agent_actions_per_hour
            },
            "burst": {
                "multiplier": float(self.burst_multiplier),
                "window_seconds": self.burst_window_seconds
            },
            "enabled": self.enabled,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AgentRateLimitOverride(Base):
    """
    Per-agent rate limit overrides.

    Allows organizations to set higher (or lower) limits for specific agents,
    such as critical trading bots or high-throughput automation agents.

    Priority Tiers:
    - standard: Default limits from OrgRateLimitConfig
    - elevated: 2x default limits (for important agents)
    - critical: 5x default limits (for mission-critical agents)

    Compliance: SOC 2 CC6.1 (Audit Trail), NIST AC-6 (Least Privilege)
    """
    __tablename__ = "agent_rate_limit_overrides"

    __table_args__ = (
        UniqueConstraint('organization_id', 'agent_id', name='uq_agent_rate_limit_org_agent'),
        Index('idx_agent_rate_limit_org', 'organization_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id = Column(String(255), nullable=False, index=True)

    # Override limits (NULL = use org default)
    actions_per_minute = Column(Integer, nullable=True)
    actions_per_hour = Column(Integer, nullable=True)

    # Priority tier affects multipliers
    priority_tier = Column(
        String(20),
        default='standard',
        nullable=False
    )  # standard, elevated, critical

    # Reason for override (required for audit)
    override_reason = Column(Text, nullable=True)

    # Approval workflow
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Priority tier multipliers
    TIER_MULTIPLIERS = {
        'standard': 1.0,
        'elevated': 2.0,
        'critical': 5.0
    }

    def get_effective_limit(self, default_limit: int) -> int:
        """
        Calculate effective limit considering override and priority tier.

        Args:
            default_limit: The org default limit

        Returns:
            Effective rate limit for this agent
        """
        if self.actions_per_minute is not None:
            # Explicit override takes precedence
            return self.actions_per_minute

        # Apply tier multiplier to default
        multiplier = self.TIER_MULTIPLIERS.get(self.priority_tier, 1.0)
        return int(default_limit * multiplier)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "agent_id": self.agent_id,
            "organization_id": self.organization_id,
            "limits": {
                "actions_per_minute": self.actions_per_minute,
                "actions_per_hour": self.actions_per_hour
            },
            "priority_tier": self.priority_tier,
            "override_reason": self.override_reason,
            "is_active": self.is_active,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RateLimitEvent(Base):
    """
    Rate limit event log for analytics and alerting.

    Immutable append-only log of all rate limiting events including:
    - Limit reached (warning)
    - Burst allowed (temporary overage)
    - Blocked (action denied due to rate limit)

    Compliance: SOC 2 CC6.1 (Audit Logging), SOC 2 A1.1 (Capacity Management)
    """
    __tablename__ = "rate_limit_events"

    __table_args__ = (
        Index('idx_rate_limit_events_org_time', 'organization_id', 'created_at'),
        Index('idx_rate_limit_events_agent', 'organization_id', 'agent_id', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id = Column(String(255), nullable=True, index=True)

    # Event details
    event_type = Column(String(50), nullable=False)  # 'limit_reached', 'burst_allowed', 'blocked'
    limit_type = Column(String(50), nullable=False)  # 'agent_minute', 'agent_hour', 'tenant_minute', 'tenant_hour'

    # Counters at time of event
    current_count = Column(Integer, nullable=False)
    limit_value = Column(Integer, nullable=False)

    # Context
    action_type = Column(String(100), nullable=True)
    ip_address = Column(INET, nullable=True)
    correlation_id = Column(String(100), nullable=True)

    # Timestamp (immutable)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "limit_type": self.limit_type,
            "current_count": self.current_count,
            "limit_value": self.limit_value,
            "action_type": self.action_type,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# BEHAV-001: Rate Limit Result Dataclass
# =============================================================================


@dataclass
class RateLimitResult:
    """
    Result of a rate limit check.

    Contains the decision (allowed/denied) and metadata for response headers.
    """
    allowed: bool
    reason: Optional[str] = None
    retry_after: Optional[int] = None  # Seconds until retry allowed
    limit_type: Optional[str] = None  # Which limit was exceeded

    # Current usage (for response headers)
    current_agent_count: Optional[int] = None
    current_tenant_count: Optional[int] = None
    agent_limit: Optional[int] = None
    tenant_limit: Optional[int] = None

    # Reset timestamp
    reset_at: Optional[datetime] = None

    def to_response_headers(self) -> Dict[str, str]:
        """Generate rate limit response headers."""
        headers = {}

        if self.agent_limit is not None:
            headers["X-RateLimit-Limit-Agent"] = str(self.agent_limit)
        if self.current_agent_count is not None and self.agent_limit is not None:
            remaining = max(0, self.agent_limit - self.current_agent_count)
            headers["X-RateLimit-Remaining-Agent"] = str(remaining)

        if self.tenant_limit is not None:
            headers["X-RateLimit-Limit-Tenant"] = str(self.tenant_limit)
        if self.current_tenant_count is not None and self.tenant_limit is not None:
            remaining = max(0, self.tenant_limit - self.current_tenant_count)
            headers["X-RateLimit-Remaining-Tenant"] = str(remaining)

        if self.reset_at is not None:
            headers["X-RateLimit-Reset"] = str(int(self.reset_at.timestamp()))

        if not self.allowed and self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)

        return headers

    def to_error_response(self) -> Dict[str, Any]:
        """Generate error response body for 429 responses."""
        return {
            "error": "rate_limit_exceeded",
            "message": self.reason or "Rate limit exceeded",
            "retry_after": self.retry_after,
            "limit_type": self.limit_type,
            "current_usage": {
                "agent_minute": self.current_agent_count,
                "tenant_minute": self.current_tenant_count
            }
        }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'OrgRateLimitConfig',
    'AgentRateLimitOverride',
    'RateLimitEvent',
    'RateLimitResult'
]
