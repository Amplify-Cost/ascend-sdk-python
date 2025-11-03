# Phase 2: AWS CloudWatch Integration - Implementation Plan
**Date:** 2025-10-31
**Status:** 📋 PLANNING - Awaiting Approval
**Estimated Time:** 4-6 hours
**Risk Level:** LOW-MEDIUM

---

## Executive Summary

Phase 2 will integrate AWS CloudWatch to provide real-time system health monitoring with actual infrastructure metrics instead of placeholder messages. This replaces the "Coming Soon" Phase 2 status with live data from AWS.

**What Users Will See:**
- Real CPU, Memory, Disk usage from AWS ECS
- Real network latency from CloudWatch metrics
- Real API response times from CloudWatch Logs
- Live performance metrics (requests/sec, error rates)

---

## Prerequisites Check

Before implementing Phase 2, we need to verify:

### 1. AWS Resources Available
- [x] ECS Cluster: `owkai-pilot` ✅
- [x] ECS Service: `owkai-pilot-backend-service` ✅
- [ ] CloudWatch Access: Need to verify IAM permissions
- [ ] CloudWatch Logs: Need to verify log group exists
- [ ] CloudWatch Metrics: Need to verify ECS metrics enabled

### 2. IAM Permissions Required
The ECS task execution role needs:
- `cloudwatch:GetMetricStatistics`
- `cloudwatch:GetMetricData`
- `logs:FilterLogEvents`
- `logs:GetLogEvents`
- `ecs:DescribeTasks`
- `ecs:DescribeServices`

### 3. Environment Configuration
- AWS region: Need to confirm (likely us-east-1)
- Log group name: Need to identify
- Metric namespace: AWS/ECS

---

## Implementation Plan

### Step 1: Verify AWS CloudWatch Access (30 min)

**Tasks:**
1. Check current IAM role permissions
2. Identify CloudWatch log group name
3. Test CloudWatch metrics availability
4. Verify ECS container insights enabled

**Commands to Run:**
```bash
# Check ECS service details
aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service

# Check CloudWatch log groups
aws logs describe-log-groups --log-group-name-prefix /ecs/owkai

# Test CloudWatch metrics
aws cloudwatch list-metrics --namespace AWS/ECS --dimensions Name=ServiceName,Value=owkai-pilot-backend-service
```

**Acceptance Criteria:**
- [ ] IAM role has required permissions
- [ ] Log group identified
- [ ] Metrics available for CPU, Memory
- [ ] Container Insights enabled

---

### Step 2: Create CloudWatch Service Module (1 hour)

**New File:** `ow-ai-backend/services/cloudwatch_service.py`

**Purpose:** Centralized service to fetch CloudWatch metrics

**Functions to Implement:**
```python
class CloudWatchService:
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize CloudWatch client"""

    async def get_ecs_metrics(self, cluster: str, service: str, duration_minutes: int = 5) -> dict:
        """
        Get ECS service metrics for last N minutes
        Returns: {
            "cpu_usage": float,  # 0-100
            "memory_usage": float,  # 0-100
            "timestamp": str
        }
        """

    async def get_container_insights(self, cluster: str, service: str) -> dict:
        """
        Get detailed container insights
        Returns: {
            "disk_usage": float,
            "network_rx_bytes": int,
            "network_tx_bytes": int,
            "network_latency": float
        }
        """

    async def get_api_performance(self, log_group: str, duration_minutes: int = 5) -> dict:
        """
        Get API performance from CloudWatch Logs Insights
        Returns: {
            "requests_per_second": float,
            "avg_response_time": float,
            "p95_response_time": float,
            "error_rate": float  # 0-1
        }
        """

    async def get_system_health(self) -> dict:
        """
        Aggregate all metrics into system health summary
        Returns complete health dashboard data
        """
```

**Error Handling:**
- Graceful fallback to Phase 1 status if CloudWatch unavailable
- Cache metrics for 30 seconds to avoid excessive API calls
- Log errors without breaking endpoint

---

### Step 3: Update Analytics Routes (1 hour)

**File:** `ow-ai-backend/routes/analytics_routes.py`

**Endpoint:** `/api/analytics/realtime/metrics`

**Changes:**
```python
# BEFORE (Phase 1)
system_health = {
    "status": "phase_2_planned",
    "message": "System health monitoring with AWS CloudWatch will be available in Phase 2 (Week 1)",
    "available_metrics": ["CPU", "Memory", "Disk", "Network", "API Response Time"],
    "estimated_availability": "Week 1"
}

# AFTER (Phase 2)
try:
    cloudwatch_service = CloudWatchService()
    ecs_metrics = await cloudwatch_service.get_ecs_metrics("owkai-pilot", "owkai-pilot-backend-service")
    container_insights = await cloudwatch_service.get_container_insights("owkai-pilot", "owkai-pilot-backend-service")

    system_health = {
        "status": "live",
        "source": "aws_cloudwatch",
        "cpu_usage": ecs_metrics["cpu_usage"],
        "memory_usage": ecs_metrics["memory_usage"],
        "disk_usage": container_insights["disk_usage"],
        "network_latency": container_insights["network_latency"],
        "timestamp": ecs_metrics["timestamp"],
        "metrics_age_seconds": 60  # 1 minute refresh
    }
except Exception as e:
    # Fallback to Phase 1 status if CloudWatch unavailable
    logger.warning(f"CloudWatch unavailable, showing Phase 2 status: {e}")
    system_health = {
        "status": "phase_2_planned",
        "message": "System health monitoring temporarily unavailable",
        "error": str(e)
    }

# Update performance_metrics similarly
try:
    api_perf = await cloudwatch_service.get_api_performance("/ecs/owkai-pilot-backend")

    performance_metrics = {
        "status": "live",
        "source": "cloudwatch_logs_insights",
        "requests_per_second": api_perf["requests_per_second"],
        "avg_response_time": api_perf["avg_response_time"],
        "p95_response_time": api_perf["p95_response_time"],
        "error_rate": api_perf["error_rate"],
        "timestamp": api_perf["timestamp"]
    }
except Exception as e:
    performance_metrics = {
        "status": "phase_2_planned",
        "message": "Performance tracking temporarily unavailable"
    }
```

**Acceptance Criteria:**
- [ ] Endpoint returns real CloudWatch metrics when available
- [ ] Graceful fallback to Phase 1 status if CloudWatch fails
- [ ] Response time < 500ms (with caching)
- [ ] No breaking changes to response structure

---

### Step 4: Add Caching Layer (30 min)

**Purpose:** Avoid hitting CloudWatch API limits and reduce latency

**Implementation:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class MetricsCache:
    def __init__(self, ttl_seconds: int = 30):
        self._cache = {}
        self._ttl = ttl_seconds

    def get(self, key: str):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self._ttl):
                return value
        return None

    def set(self, key: str, value):
        self._cache[key] = (value, datetime.now())

# Global cache instance
metrics_cache = MetricsCache(ttl_seconds=30)
```

**Usage:**
```python
async def get_cached_metrics():
    cached = metrics_cache.get("system_health")
    if cached:
        return cached

    fresh_metrics = await cloudwatch_service.get_system_health()
    metrics_cache.set("system_health", fresh_metrics)
    return fresh_metrics
```

---

### Step 5: Update Configuration (15 min)

**File:** `ow-ai-backend/config.py`

**Add CloudWatch Settings:**
```python
# AWS CloudWatch Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CLOUDWATCH_ENABLED = os.getenv("CLOUDWATCH_ENABLED", "true").lower() == "true"
ECS_CLUSTER_NAME = os.getenv("ECS_CLUSTER_NAME", "owkai-pilot")
ECS_SERVICE_NAME = os.getenv("ECS_SERVICE_NAME", "owkai-pilot-backend-service")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "/ecs/owkai-pilot-backend")
METRICS_CACHE_TTL = int(os.getenv("METRICS_CACHE_TTL", "30"))
```

**Environment Variables:**
```bash
# Add to .env and ECS task definition
AWS_REGION=us-east-1
CLOUDWATCH_ENABLED=true
ECS_CLUSTER_NAME=owkai-pilot
ECS_SERVICE_NAME=owkai-pilot-backend-service
CLOUDWATCH_LOG_GROUP=/ecs/owkai-pilot-backend
METRICS_CACHE_TTL=30
```

---

### Step 6: Add Dependencies (5 min)

**File:** `ow-ai-backend/requirements.txt`

**Add:**
```
boto3>=1.28.0  # AWS SDK (may already be installed)
aioboto3>=12.0.0  # Async AWS SDK
```

**Install:**
```bash
pip install boto3 aioboto3
```

---

### Step 7: Frontend (No Changes Required!) (0 min)

**Why:** Frontend already has conditional rendering!

The frontend `RealTimeAnalyticsDashboard.jsx` automatically detects when:
```javascript
realTimeMetrics.system_health.status === 'phase_2_planned'
  ? /* Show coming soon */
  : /* Show actual metrics */
```

When backend returns `status: "live"` instead of `"phase_2_planned"`, the frontend will automatically switch from the "Coming Soon" card to the actual progress bars showing real CPU/Memory/Disk usage.

**No code changes needed! ✅**

---

### Step 8: Testing Plan (1 hour)

#### Local Testing
```bash
# 1. Test CloudWatch service directly
python -c "
from services.cloudwatch_service import CloudWatchService
import asyncio

async def test():
    cw = CloudWatchService()
    metrics = await cw.get_system_health()
    print(metrics)

asyncio.run(test())
"

# 2. Test analytics endpoint
curl http://localhost:8000/api/analytics/realtime/metrics \
  -H "Authorization: Bearer $TOKEN" | jq '.system_health'

# 3. Verify caching works
for i in {1..5}; do
  echo "Request $i:"
  time curl -s http://localhost:8000/api/analytics/realtime/metrics \
    -H "Authorization: Bearer $TOKEN" | jq '.system_health.cpu_usage'
done
```

#### Production Testing
```bash
# 1. Check CloudWatch metrics available
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=owkai-pilot-backend-service \
  --start-time 2025-10-31T00:00:00Z \
  --end-time 2025-10-31T23:59:59Z \
  --period 300 \
  --statistics Average

# 2. Test production endpoint
curl https://pilot.owkai.app/api/analytics/realtime/metrics \
  -H "Authorization: Bearer $TOKEN" | jq '.system_health'
```

**Acceptance Criteria:**
- [ ] CloudWatch service returns real metrics
- [ ] Caching reduces response time (first call ~500ms, cached ~50ms)
- [ ] Fallback works when CloudWatch unavailable
- [ ] Frontend automatically shows real metrics
- [ ] No console errors

---

### Step 9: Deployment (30 min)

**Backend Deployment:**
```bash
# 1. Add to requirements.txt
# 2. Update config.py with CloudWatch settings
# 3. Create cloudwatch_service.py
# 4. Update analytics_routes.py
# 5. Commit and push

git add .
git commit -m "feat(analytics): Phase 2 - AWS CloudWatch integration for real-time metrics"
git push origin pilot

# ECS will auto-deploy via GitHub Actions
```

**Monitor Deployment:**
```bash
aws ecs describe-services \
  --cluster owkai-pilot \
  --services owkai-pilot-backend-service \
  --query 'services[0].deployments[*].{Status:status,TaskDefinition:taskDefinition}'
```

---

## Response Structure Changes

### Before Phase 2 (Current)
```json
{
  "system_health": {
    "status": "phase_2_planned",
    "message": "System health monitoring with AWS CloudWatch will be available in Phase 2 (Week 1)",
    "available_metrics": ["CPU", "Memory", "Disk", "Network", "API Response Time"],
    "estimated_availability": "Week 1"
  },
  "performance_metrics": {
    "status": "phase_2_planned",
    "message": "Performance tracking with CloudWatch Logs Insights will be available in Phase 2 (Week 1)"
  }
}
```

### After Phase 2 (With CloudWatch)
```json
{
  "system_health": {
    "status": "live",
    "source": "aws_cloudwatch",
    "cpu_usage": 23.4,  // Real from ECS
    "memory_usage": 41.7,  // Real from ECS
    "disk_usage": 18.9,  // Real from Container Insights
    "network_latency": 8.3,  // Real from Container Insights
    "api_response_time": 156.2,  // Real from CloudWatch Logs
    "timestamp": "2025-10-31T10:30:00Z",
    "metrics_age_seconds": 30
  },
  "performance_metrics": {
    "status": "live",
    "source": "cloudwatch_logs_insights",
    "requests_per_second": 24.7,  // Real from logs
    "avg_response_time": 156.2,  // Real from logs
    "p95_response_time": 342.1,  // Real from logs
    "error_rate": 0.012,  // Real from logs (1.2%)
    "timestamp": "2025-10-31T10:30:00Z"
  }
}
```

### Fallback (CloudWatch Unavailable)
```json
{
  "system_health": {
    "status": "phase_2_planned",
    "message": "System health monitoring temporarily unavailable",
    "error": "Unable to connect to CloudWatch"
  }
}
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CloudWatch permissions missing | Medium | Medium | Graceful fallback to Phase 1 status |
| CloudWatch API limits hit | Low | Low | Caching layer (30s TTL) |
| Slow response times | Low | Medium | Caching + async calls |
| Cost increase (CloudWatch API calls) | Low | Low | Caching reduces calls by 95% |
| Breaking frontend | Very Low | High | Frontend already has conditional rendering |
| Breaking other features | Very Low | High | Only analytics endpoints modified |

**Overall Risk Level:** LOW-MEDIUM ✅

---

## Cost Analysis

**CloudWatch API Calls:**
- Without caching: ~1,200 calls/hour (assuming 20 users × 1 refresh/min)
- With caching (30s TTL): ~60 calls/hour (97% reduction)

**CloudWatch Costs:**
- First 1M API calls: FREE
- GetMetricStatistics: $0.01 per 1,000 calls
- Logs Insights queries: $0.005 per GB scanned

**Estimated Monthly Cost:**
- API calls: ~43,200/month = $0.43
- Logs queries: ~50 GB/month = $0.25
- **Total: < $1/month** ✅

---

## Rollback Plan

### If Phase 2 Fails:
```bash
# Backend rollback
git revert HEAD
git push origin pilot
# ECS auto-deploys previous version

# Or manual restore
cp routes/analytics_routes.py.backup_phase2_YYYYMMDD routes/analytics_routes.py
```

### Frontend:
**No rollback needed** - Frontend automatically falls back to "Coming Soon" when backend returns `status: "phase_2_planned"`

---

## Success Criteria

### Technical Metrics
- [ ] CloudWatch service successfully fetches metrics
- [ ] Response time < 500ms (first call), < 50ms (cached)
- [ ] Cache hit rate > 95%
- [ ] Graceful fallback works when CloudWatch unavailable
- [ ] No breaking changes to API contract
- [ ] Frontend automatically shows real metrics

### User Experience
- [ ] Dashboard shows real CPU/Memory/Disk percentages
- [ ] System health updates every 30 seconds
- [ ] Progress bars animate with real values
- [ ] No "Coming Soon" message for system health
- [ ] Clear timestamp showing data freshness

### Operational
- [ ] CloudWatch API calls < 100/hour (with caching)
- [ ] No errors in application logs
- [ ] ECS deployment succeeds
- [ ] All other features continue working
- [ ] Monitoring alerts configured

---

## Timeline

| Step | Time | Cumulative |
|------|------|------------|
| 1. Verify AWS CloudWatch Access | 30 min | 30 min |
| 2. Create CloudWatch Service Module | 1 hour | 1.5 hours |
| 3. Update Analytics Routes | 1 hour | 2.5 hours |
| 4. Add Caching Layer | 30 min | 3 hours |
| 5. Update Configuration | 15 min | 3.25 hours |
| 6. Add Dependencies | 5 min | 3.33 hours |
| 7. Frontend (No Changes) | 0 min | 3.33 hours |
| 8. Testing | 1 hour | 4.33 hours |
| 9. Deployment | 30 min | 5 hours |

**Total Estimated Time:** 5 hours

---

## Files to Modify

### New Files (2)
1. `ow-ai-backend/services/cloudwatch_service.py` (new)
2. `ow-ai-backend/services/__init__.py` (update imports)

### Modified Files (3)
1. `ow-ai-backend/routes/analytics_routes.py` (update `/api/analytics/realtime/metrics`)
2. `ow-ai-backend/config.py` (add CloudWatch settings)
3. `ow-ai-backend/requirements.txt` (add boto3, aioboto3)

### Frontend Files (0)
**No changes needed!** Conditional rendering already in place.

---

## Backups to Create

Before starting:
```bash
# Backend
cp routes/analytics_routes.py routes/analytics_routes.py.backup_phase2_20251031
cp config.py config.py.backup_phase2_20251031
cp requirements.txt requirements.txt.backup_phase2_20251031
```

---

## Next Steps After Phase 2

### Phase 3: Machine Learning Predictions (Week 2)
- Requires 14+ days of agent action data
- Train ML models for risk forecasting
- Agent workload prediction
- Anomaly detection
- Capacity planning

**Current data collection:** 0/14 days
**Estimated ready:** 2025-11-14

---

## Approval Checklist

Before proceeding with Phase 2 implementation:

- [ ] User approves CloudWatch integration plan
- [ ] User confirms AWS access is acceptable
- [ ] User approves < $1/month CloudWatch cost
- [ ] User approves 5-hour implementation timeline
- [ ] User confirms graceful fallback is acceptable
- [ ] Ready to verify AWS permissions

---

**Awaiting your approval to proceed with Phase 2 implementation.**

Once approved, I will:
1. Verify AWS CloudWatch access and permissions
2. Create CloudWatch service module
3. Update analytics routes with real metrics
4. Test locally and in production
5. Deploy to production
6. Verify real metrics appear in dashboard

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
