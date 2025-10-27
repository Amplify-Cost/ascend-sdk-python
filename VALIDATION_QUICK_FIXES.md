# BACKEND VALIDATION - QUICK FIX GUIDE

**Priority:** CRITICAL BLOCKERS
**Timeline:** 2 weeks to production ready
**Updated:** October 24, 2025

---

## CRITICAL BLOCKER #1: Demo Data Cleanup (83.3% of data)

### Problem
Database contains mostly test data:
- Agents: "TrendAgent_0", "security-scanner-test", "threat-hunter-test_99_new"
- Tools: "TrendTool", "enterprise-mcp", "test-scanner"
- 31 occurrences of "test" keyword in responses

### Fix Steps
```sql
-- 1. Identify test data
SELECT * FROM pending_agent_actions
WHERE agent_id LIKE '%test%' OR agent_id LIKE '%Agent_%' OR description LIKE '%test%';

SELECT * FROM agent_actions
WHERE agent_id LIKE '%test%' OR tool_name LIKE '%test%' OR tool_name LIKE '%Tool%';

SELECT * FROM alerts
WHERE agent_id LIKE '%test%' OR message LIKE '%test%';

-- 2. Delete or archive test data
BEGIN;
DELETE FROM pending_agent_actions WHERE agent_id LIKE '%test%';
DELETE FROM agent_actions WHERE agent_id LIKE '%test%' OR agent_id LIKE '%Agent_%';
DELETE FROM alerts WHERE agent_id LIKE '%test%';
COMMIT;

-- 3. Load real data (create script or manual entry)
-- Insert production agent names, real tool integrations
```

### Expected Outcome
- Demo data < 10% (currently 83.3%)
- Analytics show real operations
- All dashboards display actual data

### Time Estimate: 2-3 days

---

## CRITICAL BLOCKER #2: API Routing Issues (7 endpoints)

### Problem
These endpoints return HTML instead of JSON:
- `/agent/agent-actions`
- `/audit/logs`
- `/governance/policies`
- `/governance/unified-actions`
- `/logs`
- `/security-findings`
- `/rules`

### Root Cause
Web server routing gives frontend precedence over API routes

### Fix Option 1: Add /api/ Prefix (Recommended)
```python
# In main.py, update route prefixes
app.include_router(agent_router, prefix="/api/agent", tags=["Agent"])
app.include_router(audit_router, prefix="/api/audit", tags=["Audit"])
app.include_router(governance_router, prefix="/api/governance", tags=["Governance"])
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
app.include_router(rules_router, prefix="/api/rules", tags=["Rules"])
```

Then update frontend API calls:
```javascript
// Before
fetch('/agent/agent-actions')

// After
fetch('/api/agent/agent-actions')
```

### Fix Option 2: NGINX Configuration
```nginx
# In NGINX config, prioritize API routes
location ~ ^/(agent|audit|governance|logs|rules|security-findings) {
    # Check if Accept header wants JSON
    if ($http_accept ~* "application/json") {
        proxy_pass http://backend:8000;
    }
    # Otherwise serve frontend
    try_files $uri $uri/ /index.html;
}
```

### Fix Option 3: FastAPI Mount Order
```python
# In main.py, ensure API routes are mounted BEFORE static files
# Move this to the END of main.py
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

### Expected Outcome
- All API endpoints return JSON
- Frontend still accessible
- API integrations work

### Time Estimate: 1-2 days

---

## CRITICAL BLOCKER #3: Smart Rules System Broken

### Problem
- `/smart-rules` returns 500 Internal Server Error
- `/smart-rules/ab-tests` returns 404
- `/smart-rules/suggestions` returns 404

### Diagnostic Steps
```bash
# Check logs for smart rules errors
grep "smart-rules" /var/log/uwsgi/*.log
grep "smart_rules" /var/log/uwsgi/*.log

# Check if database table exists
psql $DATABASE_URL -c "\d smart_rules"

# Test endpoint directly
curl -X GET "https://pilot.owkai.app/smart-rules" \
  -H "Authorization: Bearer <token>" \
  -v 2>&1 | grep -A 20 "500"
```

### Common Fixes

#### If Table Missing
```sql
CREATE TABLE IF NOT EXISTS smart_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(100),
    conditions JSONB,
    actions JSONB,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### If Route Not Registered
```python
# In main.py
from routes import smart_rules_routes
app.include_router(smart_rules_routes.router, prefix="/smart-rules", tags=["Smart Rules"])
```

#### If Database Connection Issue
```python
# In routes/smart_rules_routes.py
# Check all database queries have proper error handling
try:
    rules = db.query(SmartRule).all()
except Exception as e:
    logger.error(f"Smart rules query failed: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

### Expected Outcome
- `/smart-rules` returns 200 with rule list
- All sub-endpoints functional
- No 500 errors

### Time Estimate: 2-3 days

---

## CRITICAL BLOCKER #4: Missing Admin Endpoints

### Problem
- `/admin/users` returns 404
- No way to manage users in production

### Quick Implementation

Create `/Users/mac_001/OW_AI_Project/ow-ai-backend/routes/admin_routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User
from dependencies import get_current_user, require_admin
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])

class RoleUpdate(BaseModel):
    role: str

@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_admin)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ],
        "total": len(users)
    }

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_admin)
):
    """Update user role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    valid_roles = ["admin", "approver", "user", "viewer"]
    if role_data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    user.role = role_data.role
    db.commit()

    return {"message": "Role updated", "user_id": user_id, "new_role": role_data.role}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _=Depends(require_admin)
):
    """Delete user (admin only)"""
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted", "user_id": user_id}
```

Then add to `main.py`:
```python
from routes import admin_routes
app.include_router(admin_routes.router)
```

Create admin middleware in `dependencies.py`:
```python
async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### Expected Outcome
- `/admin/users` returns user list
- `/admin/users/{id}/role` updates roles
- `/admin/users/{id}` deletes users
- All protected by admin-only access

### Time Estimate: 1-2 days

---

## HIGH PRIORITY: Token Validation Stability

### Problem
`/auth/me` occasionally returns 422, requires retry

### Diagnostic
```python
# In routes/auth.py, add more logging
@router.get("/me")
async def get_current_user_diagnostic(request: Request, ...):
    logger.info(f"Auth header: {request.headers.get('Authorization')}")
    logger.info(f"Cookies: {request.cookies}")
    # ... rest of function
```

### Potential Fixes

1. **Check token extraction:**
```python
def get_authentication_source(request: Request, credentials: HTTPAuthorizationCredentials):
    # Ensure we handle missing/malformed tokens gracefully
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(status_code=401, detail="No authorization header")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    return token, "bearer", "enterprise"
```

2. **Add token caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def validate_token_cached(token: str):
    """Cache token validation for 5 minutes"""
    return validate_enterprise_token(token, "access")
```

### Expected Outcome
- Consistent 200 responses
- No 422 errors
- Faster token validation

### Time Estimate: 1 day

---

## MEDIUM PRIORITY: Load Production Policies

### Problem
Only 1 policy in system, need multiple for production

### Sample Policies to Load

```sql
-- High-risk action policy
INSERT INTO governance_policies (
    policy_name,
    policy_type,
    rules,
    is_active,
    created_by
) VALUES (
    'High Risk Action Approval',
    'authorization',
    '{
        "conditions": [
            {"field": "risk_level", "operator": ">=", "value": "high"}
        ],
        "actions": [
            {"type": "require_approval", "approver_role": "admin"},
            {"type": "audit_log", "level": "critical"}
        ]
    }'::jsonb,
    true,
    7
);

-- NIST compliance policy
INSERT INTO governance_policies (
    policy_name,
    policy_type,
    rules,
    is_active,
    created_by
) VALUES (
    'NIST AC-3 Enforcement',
    'compliance',
    '{
        "conditions": [
            {"field": "nist_control", "operator": "==", "value": "AC-3"}
        ],
        "actions": [
            {"type": "enforce_access_control"},
            {"type": "log_access_attempt"}
        ]
    }'::jsonb,
    true,
    7
);

-- Add more policies as needed...
```

### Time Estimate: 2-3 days

---

## TESTING CHECKLIST

After fixes, verify:

### Data Quality
```bash
# Should have <10% demo data
curl -s "https://pilot.owkai.app/analytics/trends" -H "Authorization: Bearer $TOKEN" | grep -c "test"
# Count should be low (< 3)
```

### Routing
```bash
# Should return JSON, not HTML
curl -s "https://pilot.owkai.app/agent/agent-actions" -H "Authorization: Bearer $TOKEN" | head -c 50
# Should see: {"data": [...
# NOT: <!DOCTYPE html>
```

### Smart Rules
```bash
# Should return 200 with rules list
curl -s -X GET "https://pilot.owkai.app/smart-rules" -H "Authorization: Bearer $TOKEN" -w "\nStatus: %{http_code}\n"
# Status should be 200
```

### Admin
```bash
# Should return user list
curl -s -X GET "https://pilot.owkai.app/admin/users" -H "Authorization: Bearer $TOKEN" | jq '.users | length'
# Should see number of users
```

### Token Validation
```bash
# Run 10 times, all should succeed
for i in {1..10}; do
  curl -s -X GET "https://pilot.owkai.app/auth/me" -H "Authorization: Bearer $TOKEN" -w "Status: %{http_code}\n" -o /dev/null
done
# All should show: Status: 200
```

---

## DEPLOYMENT CHECKLIST

Before going to production:

- [ ] Demo data cleaned (<10% remaining)
- [ ] All API endpoints return JSON
- [ ] Smart rules system operational
- [ ] Admin endpoints implemented
- [ ] Token validation stable (10/10 success)
- [ ] Production policies loaded (5+ policies)
- [ ] Integration tests passing
- [ ] Load testing completed (100+ users)
- [ ] Security audit performed
- [ ] Monitoring configured
- [ ] Rollback plan documented
- [ ] Documentation updated

---

## SUPPORT CONTACTS

**For questions about:**
- Data cleanup: Check `scripts/database/seed_data.py`
- Routing issues: Check `main.py` route registration
- Smart rules: Check `routes/smart_rules_routes.py`
- Admin endpoints: Check `routes/admin_routes.py`
- Database: Check `models.py` and migrations

**AWS Deployment:** See `AWS_DEPLOYMENT_INSTRUCTIONS.txt`
**Database Schema:** See `models.py`
**API Documentation:** See `/docs` endpoint

---

## QUICK WINS (Do First)

1. **Fix routing** - Biggest impact, easiest fix (1 day)
2. **Implement admin endpoints** - Critical feature, straightforward (1-2 days)
3. **Clean demo data** - High impact on perception (2-3 days)
4. **Debug smart rules** - May be simple fix (1-3 days)

Total: 5-9 days to address all critical blockers

---

**Last Updated:** October 24, 2025
**Next Review:** After critical fixes implemented
**Full Report:** See `COMPLETE_BACKEND_VALIDATION.md`
