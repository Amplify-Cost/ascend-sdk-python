# Rate Limiting

Per-agent and per-tenant rate limiting for AI governance.

## Overview

ASCEND rate limiting prevents runaway agents and provides DoS protection using Redis-backed sliding window counters. The implementation uses sorted sets for accurate sliding window calculations that prevent burst attacks at window boundaries.

## Requirements

- Redis 6.0+ (ElastiCache, Redis Cloud, or self-hosted)
- Environment variables configured
- Database tables provisioned via migrations

## Configuration

### Environment Variables

```bash
# Required for rate limiting
REDIS_URL=redis://your-redis-host:6379

# Optional: Disable rate limiting globally (default: true)
ASCEND_RATE_LIMIT_ENABLED=true

# Optional: Config cache TTL in seconds (default: 60)
RATE_LIMIT_CONFIG_CACHE_TTL=60

# Rate limiting is also controlled via database config
# See: org_rate_limit_config table
```

### Default Limits

| Scope | Limit | Window |
|-------|-------|--------|
| Per-tenant | 1000 requests | 1 minute |
| Per-agent | 100 requests | 1 minute |

## Architecture

```
Request
   │
   ▼
┌─────────────────────┐
│ Rate Limit Check    │
│ ┌─────────────────┐ │
│ │ Tenant Counter  │ │  Redis: tenant:{org_id}:minute
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ Agent Counter   │ │  Redis: agent:{agent_id}:minute
│ └─────────────────┘ │
└─────────────────────┘
   │
   ▼
Limit Exceeded? ─── Yes ──→ 429 Too Many Requests
   │
   No
   │
   ▼
Process Request
```

## Database Schema

### org_rate_limit_config

```sql
CREATE TABLE org_rate_limit_config (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) UNIQUE,
    enabled BOOLEAN DEFAULT true,

    -- Tenant-wide limits
    actions_per_minute INTEGER DEFAULT 1000,
    actions_per_hour INTEGER DEFAULT 50000,
    actions_per_day INTEGER DEFAULT 500000,

    -- Per-agent limits
    agent_actions_per_minute INTEGER DEFAULT 100,
    agent_actions_per_hour INTEGER DEFAULT 5000,

    -- Burst handling
    burst_multiplier NUMERIC(3,2) DEFAULT 1.5,
    burst_window_seconds INTEGER DEFAULT 10,

    -- Response behavior
    rate_limit_response_code INTEGER DEFAULT 429,
    include_retry_after BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### agent_rate_limit_overrides

```sql
CREATE TABLE agent_rate_limit_overrides (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    agent_id VARCHAR(255) NOT NULL,
    custom_limit INTEGER,
    priority_tier VARCHAR(20) DEFAULT 'standard',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(organization_id, agent_id)
);
```

## Priority Tiers

| Tier | Multiplier | Use Case |
|------|------------|----------|
| `standard` | 1x | Normal operations |
| `elevated` | 2x | Batch processing |
| `critical` | 5x | Emergency operations |

## Customization

### Per-Org Configuration

```sql
-- Increase limits for a specific organization
UPDATE org_rate_limit_config
SET actions_per_minute = 2000,
    agent_actions_per_minute = 200
WHERE organization_id = 1;
```

### Per-Agent Overrides

```sql
-- Give a critical agent higher limits
INSERT INTO agent_rate_limit_overrides
(organization_id, agent_id, custom_limit, priority_tier)
VALUES (1, 'critical-automation-agent', 500, 'critical');
```

### Disable Rate Limiting

```sql
-- Disable for a specific org (testing)
UPDATE org_rate_limit_config
SET enabled = false
WHERE organization_id = 1;
```

## Fail-Closed Behavior

**IMPORTANT**: If Redis is unavailable and rate limiting is enabled, ALL requests are denied. This is by design for security.

```python
# Rate limiter behavior when Redis is down
if redis_unavailable and rate_limit_enabled:
    return RateLimitResponse(
        allowed=False,
        error="rate_limit_exceeded",
        message="Rate limit check failed",
        retry_after=60
    )
```

To avoid this, ensure Redis is properly provisioned before enabling rate limiting.

## API Response (429)

```json
{
  "detail": {
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded for agent",
    "retry_after": 60,
    "limit_type": "agent",
    "current_usage": {
      "agent_minute": 101,
      "tenant_minute": 500
    }
  }
}
```

## Monitoring

### Rate Limit Events Table

```sql
SELECT
    agent_id,
    event_type,
    COUNT(*) as count,
    MAX(created_at) as last_event
FROM rate_limit_events
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_id, event_type
ORDER BY count DESC;
```

### Current Usage (Redis)

```bash
redis-cli GET "tenant:1:minute"
redis-cli GET "agent:my-agent-id:minute"
```

## Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit-Agent: 100
X-RateLimit-Remaining-Agent: 42
X-RateLimit-Limit-Tenant: 1000
X-RateLimit-Remaining-Tenant: 500
X-RateLimit-Reset: 1702934520
Retry-After: 60  # Only on 429 responses
```

### Header Descriptions

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit-Agent` | Per-agent limit for this window |
| `X-RateLimit-Remaining-Agent` | Remaining requests for this agent |
| `X-RateLimit-Limit-Tenant` | Per-tenant limit for this window |
| `X-RateLimit-Remaining-Tenant` | Remaining requests for this tenant |
| `X-RateLimit-Reset` | Unix timestamp when window resets |
| `Retry-After` | Seconds until retry allowed (429 only) |

## Redis Setup Options

### Option 1: AWS ElastiCache (Recommended)

```bash
# Create via AWS Console or Terraform
aws elasticache create-cache-cluster \
    --cache-cluster-id owkai-rate-limit \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1
```

### Option 2: Managed Redis Service

- **Upstash**: Free tier with 10K commands/day
- **Redis Cloud**: 30MB free tier
- **Heroku Redis**: Free hobby tier

### Option 3: Docker (Development)

```bash
docker run -d -p 6379:6379 redis:7-alpine
export REDIS_URL=redis://localhost:6379
```

## Compliance

- **SOC 2**: Availability controls (A1.1)
- **NIST 800-53**: SC-5 (Denial of Service Protection)
- **ISO 27001**: A.12.1.3 (Capacity Management)

## Troubleshooting

### Rate Limit Check Failed

```
{"error": "rate_limit_exceeded", "current_usage": {"agent_minute": null}}
```

**Cause**: Redis connection failed
**Solution**: Check REDIS_URL and Redis availability

### All Requests Denied

**Cause**: Rate limiting enabled but Redis unavailable
**Solution**: Either:
1. Provision Redis and set REDIS_URL
2. Disable rate limiting: `UPDATE org_rate_limit_config SET enabled = false;`

### Limits Not Applying

**Cause**: Config not loaded
**Solution**: Verify org has config: `SELECT * FROM org_rate_limit_config WHERE organization_id = X;`
