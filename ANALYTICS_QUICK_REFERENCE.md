# Analytics Routes - Quick Reference Card

## Endpoints Modified

### 1. Executive Dashboard
```
GET /api/analytics/executive/dashboard
Auth: Admin only
Returns: Real KPIs from database
```

**Real Metrics:**
- Platform Health (0-100): Success rate from agent_actions
- Security Posture (0-100): Risk-weighted score
- Operational Efficiency (0-100): Automation rate
- Compliance Status (0-100): Review coverage
- User Growth: Real counts and trends
- Strategic Insights: Dynamic based on thresholds

### 2. System Performance
```
GET /api/analytics/performance/system
Auth: Any authenticated user
Returns: CloudWatch + DB metrics
```

**Real Metrics:**
- System: CloudWatch ECS metrics OR status message
- Application: CloudWatch Logs OR unavailable
- Database: PostgreSQL connections (always available)

### 3. WebSocket Streaming
```
WS /ws/realtime/{user_email}
Auth: Any authenticated user
Updates: Every 10 seconds
```

**Real Metrics:**
- Recent actions (last hour)
- High-risk actions (last hour)
- Active agents (last hour)
- WebSocket connections
- CloudWatch system metrics (if enabled)

## Response Format

### With Data
```json
{
  "executive_kpis": { /* real values */ },
  "meta": {
    "version": "2.0.0",
    "mock_data": false,
    "has_activity": true,
    "real_data_sources": ["agent_actions", "users", "audit_logs"]
  }
}
```

### No Data
```json
{
  "executive_kpis": {
    "platform_health": {"score": 0, "status": "no_data"}
  },
  "meta": {
    "mock_data": false,
    "has_activity": false
  }
}
```

### CloudWatch Unavailable
```json
{
  "system_metrics": {
    "status": "cloudwatch_required",
    "message": "Configure CLOUDWATCH_ENABLED=true"
  }
}
```

## Testing

### Validate Changes
```bash
python validate_analytics_real_data.py
```

### Test Endpoints
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"test"}' \
  | jq -r '.access_token')

# Test executive dashboard
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/executive/dashboard | jq

# Test performance
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/performance/system | jq

# Test real-time metrics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analytics/realtime/metrics | jq
```

### Check Database
```bash
# Verify data exists
psql -d your_database -c "
SELECT
  COUNT(*) as total_actions,
  COUNT(*) FILTER (WHERE risk_level='high') as high_risk,
  COUNT(DISTINCT agent_id) as unique_agents
FROM agent_actions
WHERE timestamp >= NOW() - INTERVAL '1 hour';"
```

## Environment Setup

### Required
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Optional (CloudWatch)
```bash
CLOUDWATCH_ENABLED=true
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
ECS_CLUSTER_NAME=owkai-pilot
ECS_SERVICE_NAME=owkai-pilot-backend-service
CLOUDWATCH_LOG_GROUP=/ecs/owkai-pilot-backend
```

## Common Issues

### Issue: All metrics show 0
**Cause:** No data in database
**Fix:** Insert test data or wait for real activity
```bash
# Quick test data
psql -d your_database -c "
INSERT INTO agent_actions (agent_id, action_type, risk_level, status, timestamp)
VALUES ('test-agent', 'test-action', 'medium', 'completed', NOW());"
```

### Issue: CloudWatch shows "unavailable"
**Cause:** CloudWatch not configured
**Fix:** Set environment variables above OR disable:
```bash
export CLOUDWATCH_ENABLED=false
```

### Issue: WebSocket not connecting
**Cause:** Authentication issue
**Fix:** Use valid JWT token in connection string

### Issue: Slow response times
**Cause:** Missing database indexes
**Fix:** Check indexes on agent_actions.timestamp
```sql
CREATE INDEX IF NOT EXISTS idx_agent_actions_timestamp
ON agent_actions(timestamp);
```

## Key Changes Summary

| Component | Before | After |
|-----------|--------|-------|
| Platform Health | 94.2 (fake) | Real success rate |
| Security Score | 87.6 (fake) | Real risk calculation |
| User Count | 17 (fake) | Real user query |
| CPU Usage | 42.3 (fake) | CloudWatch OR status |
| Response Time | 145.2 (fake) | CloudWatch OR status |
| WebSocket Data | Randomized | Real DB queries |

## Data Sources

### Always Available
- `agent_actions` table
- `users` table
- `audit_logs` table
- `pg_stat_activity` (database connections)

### Optional (Requires CloudWatch)
- CPU/Memory/Disk usage
- API response times
- Request throughput
- Error rates

## Validation Checklist

✅ No hardcoded values in responses
✅ All zeros show status: "no_data"
✅ CloudWatch unavailable shows clear message
✅ Real database queries for all metrics
✅ Error handling for all queries
✅ WebSocket uses real data
✅ Meta fields include data_quality info

## Files Changed

- `routes/analytics_routes.py` (691 lines refactored)

## Files Added

- `ANALYTICS_ROUTES_REAL_DATA_FIX.md` (detailed docs)
- `ANALYTICS_FIX_SUMMARY.md` (executive summary)
- `ANALYTICS_QUICK_REFERENCE.md` (this file)
- `validate_analytics_real_data.py` (validation script)

## Support

For detailed documentation, see:
- **Technical:** `ANALYTICS_ROUTES_REAL_DATA_FIX.md`
- **Summary:** `ANALYTICS_FIX_SUMMARY.md`
- **Validation:** Run `./validate_analytics_real_data.py`

---

**Version:** 2.0.0
**Last Updated:** 2025-10-31
**Status:** ✅ Production Ready
