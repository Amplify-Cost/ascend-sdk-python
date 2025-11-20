# Root Cause Identified: Application Logs Not Captured in Production

**Date:** 2025-11-12
**Time:** 1:23 PM EST
**Status:** 🔍 ROOT CAUSE FOUND
**Severity:** HIGH - Application logging completely absent in production

---

## 🎯 The Discovery

After deploying debug logging (commit fc523302) and testing the API, we discovered:

### What We See:
```bash
# CloudWatch Logs (/ecs/owkai-pilot-backend):
INFO:     10.0.2.81:14174 - "GET /api/agent-activity HTTP/1.1" 200 OK
INFO:     10.0.2.81:14190 - "GET /api/agent-activity HTTP/1.1" 200 OK
INFO:     10.0.2.81:16946 - "GET /api/agent-activity HTTP/1.1" 200 OK
```

### What We DON'T See (But Should):
```python
# From routes/agent_routes.py:409-426
logger.info("🔍 DEPLOYMENT DEBUG: Starting agent-activity query")
logger.info(f"🔍 DEPLOYMENT DEBUG: Query returned {len(actions)} actions")
logger.info(f"🔍 DEPLOYMENT DEBUG: First action - ID: {id}, agent_id: {agent_id}")
logger.warning("🔍 DEPLOYMENT DEBUG: No actions found - falling back to demo data")
logger.error(f"🔍 DEPLOYMENT DEBUG: Activity query failed with error: {error}")
```

### What This Means:
**ONLY Uvicorn HTTP access logs appear in CloudWatch. Application-level logs (from Python's logging module) are NOT being captured.**

---

## 🔍 Evidence Analysis

### Evidence 1: Latest Code Is Deployed ✅
```bash
Task Definition: owkai-pilot-backend:429
Image: fc5233029013ec2cc57eb65d0a652a0562e06a8d (commit fc523302)
Status: PRIMARY, ACTIVE, running
```
**Conclusion:** The code with debug logging IS deployed and running

### Evidence 2: API Returns Demo Data ❌
```json
GET /api/agent-activity
{
  "id": 1,
  "agent_id": "security-scanner-01",
  "action": "Vulnerability scan completed",
  "timestamp": "2025-11-12T18:21:58.367871",
  "status": "completed"
}
```
**Conclusion:** API is returning hardcoded demo data (IDs 1, 2, 3 with agent_id "security-scanner-01", etc.)

### Evidence 3: No Application Logs ❌
```bash
# Checked last 10 minutes of logs
aws logs tail /ecs/owkai-pilot-backend --since 10m --filter-pattern "DEPLOYMENT DEBUG"

# Result: NO MATCHES
# Only HTTP access logs present
```
**Conclusion:** Python logger.info() calls are not reaching CloudWatch

### Evidence 4: API Returns HTTP 200 ✅
```bash
INFO:     10.0.2.81:16946 - "GET /api/agent-activity HTTP/1.1" 200 OK
```
**Conclusion:** API endpoint is being called and responding successfully

---

## 💡 Root Cause: Application Logging Not Configured

### The Problem:
Uvicorn's default logging configuration in Docker/ECS only captures HTTP access logs. Application-level logs from Python's `logging` module require explicit configuration to:
1. Output to stdout/stderr
2. Be captured by CloudWatch Logs driver
3. Have appropriate log level set

### Why Demo Data Is Returned:
Without application logs, we can't see **why** the API returns demo data, but we know:
1. Code reaches the endpoint (HTTP 200 response)
2. Code executes the get_agent_activity() function
3. Function falls back to demo data (lines 426-490 in agent_routes.py)
4. No errors are logged because logging isn't working

### Most Likely Scenario:
```python
# routes/agent_routes.py:408-429
try:
    logger.info("🔍 DEPLOYMENT DEBUG: Starting agent-activity query")  # NOT LOGGED
    query = db.query(AgentAction).order_by(AgentAction.timestamp.desc())
    actions = query.limit(50).all()

    logger.info(f"🔍 DEPLOYMENT DEBUG: Query returned {len(actions)} actions")  # NOT LOGGED

    if actions and len(actions) > 0:
        # This should work if database has data
        return actions
    else:
        # Falls back to demo data
        raise Exception("No activity data")

except Exception as db_error:
    logger.warning(f"Activity query failed: {db_error}")  # NOT LOGGED
    # Returns demo data
    return [hardcoded_demo_data...]
```

**We need logging to see which path executes!**

---

## 🔧 Solutions (In Order of Complexity)

### Solution 1: Use Print Statements (Quick Test)
**Time:** 5 minutes
**Risk:** Low
**Purpose:** Verify if stdout/stderr reaches CloudWatch

```python
# Add print() alongside logger calls
print("🔍 DEPLOYMENT DEBUG: Starting agent-activity query")
print(f"🔍 DEPLOYMENT DEBUG: Query returned {len(actions)} actions")
```

**Deploy and test:** If prints appear in CloudWatch, logging config is the issue.

---

### Solution 2: Configure Logging in Dockerfile
**Time:** 15 minutes
**Risk:** Low
**Purpose:** Ensure all logs go to stdout

```dockerfile
# Add to Dockerfile
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
```

```python
# Update logging config in main.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

---

### Solution 3: Use Uvicorn's Logging Config
**Time:** 10 minutes
**Risk:** Low
**Purpose:** Integrate application logs with Uvicorn

```python
# main.py startup
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

---

### Solution 4: Direct Database Query Test (Fastest Diagnosis)
**Time:** 2 minutes
**Risk:** None (read-only)
**Purpose:** Verify database has enriched data

```bash
# Connect to production RDS
export PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL'
/opt/homebrew/opt/postgresql@14/bin/psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -U owkai_admin \
  -d owkai_pilot \
  -c "SELECT id, agent_id, cvss_score, mitre_tactic, nist_control FROM agent_actions ORDER BY id DESC LIMIT 5;"
```

**Expected Result:** All 300 actions have enrichment data
**If True:** Database is fine, API logic is the issue
**If False:** Database doesn't have enrichment data (backfill didn't work)

---

## 📊 Current State Summary

### What's Working ✅:
- GitHub Actions deployment pipeline
- Docker image building and pushing
- ECS task updates
- HTTP access logging
- API endpoint responding (HTTP 200)
- Zero downtime deployments
- Deployment verification (correctly caught URL issue)

### What's NOT Working ❌:
- Application-level logging (Python logger.info/warning/error)
- Ability to diagnose why API returns demo data
- Visibility into database query results
- Error visibility (exceptions not logged)

### Impact:
- **Cannot diagnose** why API returns demo data
- **Cannot verify** if database query succeeds or fails
- **Cannot see** if enrichment fields are accessible
- **Cannot debug** production issues effectively

---

## 🚀 Recommended Next Steps

### Immediate (5 minutes):
**Option A: Direct Database Query**
```bash
# Test if database has enriched data
psql ... -c "SELECT COUNT(*),
              COUNT(cvss_score),
              COUNT(mitre_tactic),
              COUNT(nist_control)
         FROM agent_actions;"
```

**Expected:**
- Total: 300
- CVSS: 300
- MITRE: 300
- NIST: 300

**If all 300:** Database is fine, API logic issue
**If < 300:** Backfill didn't work fully

---

### Short Term (15 minutes):
**Option B: Add Print Statements + Redeploy**
```python
# routes/agent_routes.py - add print() calls
def get_agent_activity(...):
    try:
        print("🔍 DEBUG: Starting query", flush=True)
        query = db.query(AgentAction).order_by(AgentAction.timestamp.desc())
        actions = query.limit(50).all()
        print(f"🔍 DEBUG: Got {len(actions)} actions", flush=True)

        if actions:
            print(f"🔍 DEBUG: First action ID: {actions[0].id}, cvss: {actions[0].cvss_score}", flush=True)
            return actions
        else:
            print("🔍 DEBUG: No actions, returning demo data", flush=True)
            raise Exception("No activity data")
    except Exception as e:
        print(f"🔍 DEBUG: Exception: {e}", flush=True)
        # Demo data fallback
```

**Deploy:** Commit, push, wait 10 min
**Test:** Check CloudWatch for print statements
**Result:** Will show exact execution path

---

### Medium Term (30 minutes):
**Option C: Fix Logging Configuration**
1. Update Dockerfile with `ENV PYTHONUNBUFFERED=1`
2. Configure logging in main.py to use StreamHandler(sys.stdout)
3. Ensure all loggers use root logger config
4. Deploy and test

---

## 🎯 Expected Outcomes

### After Database Query:
If enrichment data exists in database:
- **Confirms:** Backfill worked correctly
- **Eliminates:** Database as root cause
- **Focuses:** Investigation on API query logic

If enrichment data missing:
- **Confirms:** Backfill didn't apply to production
- **Action:** Re-run backfill script against production RDS
- **Root Cause:** Wrong database targeted or backfill failed silently

### After Print Statements Deploy:
Will show one of these scenarios:

**Scenario A: Database Query Succeeds**
```
🔍 DEBUG: Starting query
🔍 DEBUG: Got 300 actions
🔍 DEBUG: First action ID: 186, cvss: 8.2
```
**Action:** API should return real data, investigate response serialization

**Scenario B: Database Query Returns Empty**
```
🔍 DEBUG: Starting query
🔍 DEBUG: Got 0 actions
🔍 DEBUG: No actions, returning demo data
```
**Action:** Check DATABASE_URL, verify table not empty, check query filters

**Scenario C: Database Query Throws Error**
```
🔍 DEBUG: Starting query
🔍 DEBUG: Exception: (psycopg2.OperationalError) connection failed
```
**Action:** Fix database connection, security groups, credentials

---

## 📋 Decision Matrix

| Test | Time | Info Gained | Risk | Recommended Order |
|------|------|-------------|------|-------------------|
| Database Query | 2 min | Confirms backfill worked | None | **1st - Do Now** |
| Print Statements | 15 min | Shows exact execution path | Low | **2nd - If DB has data** |
| Fix Logging | 30 min | Permanent solution | Low | **3rd - After diagnosis** |
| Add More Debug | 10 min | Incremental info | Low | Skip (print better) |

---

## 💡 Key Insight

**The absence of application logs is actually a GOOD discovery** because it explains:
1. Why we couldn't see errors in previous deployments
2. Why the API silently returns demo data
3. Why no "Activity query failed" warnings appeared
4. Why debugging has been difficult

**Fix logging = Unlock all future debugging capability**

---

**Current Status:** Ready to test database directly (2 min) or deploy print statements (15 min)

**Recommendation:** Start with database query to confirm backfill worked, then add print statements to diagnose API logic.
