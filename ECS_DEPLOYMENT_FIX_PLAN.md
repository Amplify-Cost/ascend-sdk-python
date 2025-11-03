# ECS Deployment Failure - Root Cause Analysis & Fix Plan
**Date:** 2025-10-30
**Issue:** ECS deployment failed with "Max attempts exceeded" - ServicesStable waiter failed

---

## Root Cause Analysis

### What Happened
1. Code was pushed to GitHub (pilot/main)
2. AWS ECS detected the new commit and started deployment
3. New container started but failed health checks
4. ECS retried multiple times (default: 3 retries)
5. After max attempts, ECS gave up and rolled back to previous version

### Why It Failed

**Primary Issue:** Production database is missing required schema
- New code references `ab_tests` table
- A/B test scheduler queries this table on startup
- Production database doesn't have this table yet
- While wrapped in try/except, queries may slow startup or cause health check timeouts

**Secondary Issues:**
1. **Missing CVSS columns** in `agent_actions` table
2. **Missing A/B test tracking columns** in `alerts` table
3. **Health check timeout** - ECS expects app to respond within 30 seconds

---

## Changes That Were Deployed

### Code Changes (Commit: d352846)
```
5 files changed, 1496 insertions(+)
+ AB_TESTING_FIX_DEPLOYMENT_COMPLETE.md
+ PRODUCTION_DATABASE_FIX_COMPLETE.md
+ ow-ai-backend/fix_production_database_schema.sql
+ ow-ai-backend/services/ab_test_alert_router.py
+ ow-ai-backend/services/ab_test_scheduler.py
```

### What These Do:
1. **ab_test_scheduler.py** - Background thread that queries `ab_tests` table every 60 min
2. **ab_test_alert_router.py** - Routes alerts to A/B tests (queries `ab_tests`, updates `alerts`)
3. **SQL migration script** - Adds missing columns to database
4. **Documentation** - Deployment guides

### Startup Behavior:
```python
# In main.py line 263-270
try:
    from services.ab_test_scheduler import start_scheduler
    start_scheduler(SessionLocal, check_interval_minutes=60)
    print("🧪 ENTERPRISE: A/B Test auto-completion scheduler started")
except Exception as scheduler_error:
    print(f"⚠️  A/B Test scheduler failed to start: {scheduler_error}")
```

**Even with try/except, the scheduler immediately runs:**
```python
def check_and_complete_tests(self):
    expired_tests = self._find_expired_tests(db)  # Queries ab_tests table
```

If `ab_tests` table doesn't exist:
- Query fails
- Exception is caught
- But startup is slower
- Health check might timeout

---

## Deployment Fix Strategy

### Option 1: Database-First Approach (RECOMMENDED)
**Apply database migration BEFORE redeploying code**

**Steps:**
1. **Connect to production database**
   ```bash
   # Get RDS endpoint from AWS Console or environment
   psql -h <rds-endpoint> -p 5432 -U <username> -d <database>
   ```

2. **Apply migration script**
   ```bash
   # Download from GitHub
   curl -o schema_fix.sql https://raw.githubusercontent.com/Amplify-Cost/owkai-pilot-backend/main/ow-ai-backend/fix_production_database_schema.sql

   # Apply to production
   psql -h <rds-endpoint> -p 5432 -U <username> -d <database> -f schema_fix.sql
   ```

3. **Verify schema applied**
   ```sql
   \d agent_actions  -- Should show cvss_* columns
   \d ab_tests       -- Should show test_id column
   \d alerts         -- Should show ab_test_* columns
   ```

4. **Trigger redeployment**
   - ECS will automatically redeploy
   - OR manually restart ECS service
   - Health checks will pass because database schema exists

**Pros:**
- ✅ Safest approach
- ✅ No code changes needed
- ✅ Database ready before code needs it
- ✅ Clean deployment

**Cons:**
- Requires database access
- Need AWS credentials

---

### Option 2: Make Code More Resilient (ALTERNATIVE)
**Delay scheduler startup until after health checks pass**

**Changes Needed:**
```python
# In main.py, delay scheduler start
@app.on_event("startup")
async def startup():
    print("🚀 ENTERPRISE: Application startup complete")

    # Start scheduler AFTER a delay (let health checks pass first)
    import asyncio
    asyncio.create_task(delayed_scheduler_start())

async def delayed_scheduler_start():
    """Start scheduler after 60 seconds to avoid startup delays"""
    await asyncio.sleep(60)
    try:
        from services.ab_test_scheduler import start_scheduler
        start_scheduler(SessionLocal, check_interval_minutes=60)
        print("🧪 ENTERPRISE: A/B Test scheduler started (delayed)")
    except Exception as e:
        print(f"⚠️  Scheduler failed: {e}")
```

**Pros:**
- No database changes needed immediately
- App starts faster
- Health checks pass

**Cons:**
- ❌ Scheduler won't work until database is migrated
- ❌ Code still expects schema eventually
- ❌ Adds complexity
- ❌ Band-aid solution

---

### Option 3: Rollback and Redeploy (SAFEST)
**Remove changes from production, apply database migration, then redeploy**

**Steps:**
1. **Rollback git push**
   ```bash
   git log --oneline -5
   # Find commit before d352846
   git push pilot <previous-commit>:main --force
   ```

2. **Apply database migration** (same as Option 1)

3. **Re-push code**
   ```bash
   git push pilot dead-code-removal-20251016:main
   ```

**Pros:**
- ✅ Most controlled approach
- ✅ Clear separation of concerns
- ✅ Easy to test at each step

**Cons:**
- Takes more time
- Two separate deployments

---

## Recommended Solution: Option 1 (Database-First)

### Detailed Implementation Steps

#### Step 1: Get Production Database Credentials
```bash
# From AWS Console
# OR from environment variables
aws rds describe-db-instances --query 'DBInstances[0].Endpoint.Address'
```

#### Step 2: Test Connection
```bash
psql -h <rds-endpoint> -p 5432 -U <username> -d <database> -c "SELECT version();"
```

#### Step 3: Backup Current Schema (Safety)
```bash
pg_dump -h <rds-endpoint> -p 5432 -U <username> -d <database> --schema-only > production_schema_backup_$(date +%Y%m%d).sql
```

#### Step 4: Apply Migration
```bash
psql -h <rds-endpoint> -p 5432 -U <username> -d <database> << 'EOF'
-- Add CVSS columns to agent_actions
ALTER TABLE agent_actions
ADD COLUMN IF NOT EXISTS cvss_score FLOAT,
ADD COLUMN IF NOT EXISTS cvss_severity VARCHAR(20),
ADD COLUMN IF NOT EXISTS cvss_vector VARCHAR(255);

-- Create ab_tests table (full schema from script)
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    -- ... rest of columns from migration script
);

-- Add A/B test tracking to alerts
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS ab_test_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS evaluated_by_variant VARCHAR(20),
-- ... rest of columns
;
EOF
```

#### Step 5: Verify Schema
```bash
psql -h <rds-endpoint> -p 5432 -U <username> -d <database> << 'EOF'
-- Check agent_actions
SELECT column_name FROM information_schema.columns
WHERE table_name = 'agent_actions' AND column_name LIKE 'cvss%';

-- Check ab_tests exists
SELECT COUNT(*) as test_count FROM ab_tests;

-- Check alerts
SELECT column_name FROM information_schema.columns
WHERE table_name = 'alerts' AND column_name LIKE 'ab_test%';
EOF
```

#### Step 6: Monitor Deployment
```bash
# Watch ECS service
aws ecs describe-services --cluster <cluster-name> --services <service-name>

# Check logs
aws logs tail /ecs/<task-family> --follow
```

---

## Health Check Configuration

### Current ECS Health Check (Likely)
```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60
  }
}
```

### What Goes Wrong
1. Container starts
2. FastAPI loads and imports modules
3. Scheduler starts and immediately queries `ab_tests`
4. Query fails (table doesn't exist)
5. Startup slows down
6. Health check runs at 30 seconds
7. App not ready yet → health check fails
8. ECS retries 3 times
9. All retries fail → rollback

### After Database Migration
1. Container starts
2. FastAPI loads and imports modules
3. Scheduler starts and queries `ab_tests` ✅ (table exists)
4. Query succeeds quickly
5. App fully ready in <30 seconds
6. Health check passes ✅
7. Deployment succeeds ✅

---

## Testing Before Production

### Test Locally First
```bash
# 1. Drop local ab_tests table to simulate production
psql -h localhost -U mac_001 -d owkai_pilot -c "DROP TABLE IF EXISTS ab_tests CASCADE;"

# 2. Restart backend
lsof -ti:8000 | xargs kill -9
python3 main.py

# 3. Check if it starts (it should, with warnings)
# Look for: "⚠️  A/B Test scheduler failed to start"

# 4. Apply migration
psql -h localhost -U mac_001 -d owkai_pilot -f fix_production_database_schema.sql

# 5. Restart backend again
lsof -ti:8000 | xargs kill -9
python3 main.py

# 6. Verify scheduler starts
# Look for: "✅ A/B Test Scheduler started"
```

---

## Rollback Plan (If Needed)

### If Migration Fails
```sql
-- Remove added columns
ALTER TABLE agent_actions DROP COLUMN IF EXISTS cvss_score, DROP COLUMN IF EXISTS cvss_severity, DROP COLUMN IF EXISTS cvss_vector;
ALTER TABLE alerts DROP COLUMN IF EXISTS ab_test_id, DROP COLUMN IF EXISTS evaluated_by_variant;
DROP TABLE IF EXISTS ab_tests CASCADE;
```

### If Deployment Still Fails
```bash
# Force rollback to previous code
git push pilot <previous-commit-hash>:main --force
```

---

## Monitoring After Deployment

### Check Application Logs
```bash
aws logs tail /ecs/<task-family> --follow --filter "ENTERPRISE\|ERROR\|scheduler"
```

### Expected Log Messages
```
✅ Enterprise Config loaded
✅ Enterprise JWT Manager loaded
✅ A/B Test Scheduler started (checking every 60 minutes)
🚀 ENTERPRISE: Application startup complete
```

### Check Health Endpoint
```bash
curl https://pilot.owkai.app/health
# Should return: {"status": "healthy"}
```

### Verify A/B Tests Work
```bash
curl https://pilot.owkai.app/api/smart-rules/ab-tests \
  -H "Authorization: Bearer $TOKEN"
# Should return array of tests (may be empty if none created yet)
```

---

## Summary

**Recommended Action:** **Option 1 - Database-First Approach**

1. ✅ Connect to production RDS database
2. ✅ Apply migration script (`fix_production_database_schema.sql`)
3. ✅ Verify schema changes
4. ✅ Wait for ECS to auto-redeploy (or trigger manually)
5. ✅ Monitor deployment logs
6. ✅ Verify application health

**Time Estimate:** 15-30 minutes

**Risk Level:** Low (migration script is idempotent - safe to run multiple times)

**Rollback:** Easy (SQL commands to drop added columns/tables)

---

## Approval Checklist

Before proceeding with deployment:

- [ ] Database backup completed
- [ ] RDS credentials verified
- [ ] Migration script reviewed
- [ ] Rollback plan understood
- [ ] Monitoring tools ready
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled (if required)

---

## Next Steps

1. **Review this plan** - Confirm approach is acceptable
2. **Get database credentials** - From AWS Console or environment
3. **Test locally** - Simulate production scenario
4. **Apply to production** - Execute migration
5. **Monitor deployment** - Watch logs and health checks
6. **Verify functionality** - Test A/B testing features

---

**Created:** 2025-10-30
**Status:** READY FOR APPROVAL
**Risk:** LOW
**Impact:** Enables A/B testing and CVSS scoring features

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
