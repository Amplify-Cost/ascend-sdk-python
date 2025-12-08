# SEC-082: RLS Activation - Quick Reference Card

## 30-Second Overview

**Problem:** RLS policies exist but were never activated (missing `SET app.current_organization_id`)

**Solution:** New `get_db_with_rls()` dependency automatically activates RLS

**Impact:** Defense-in-depth security - database layer blocks cross-tenant access even if app has bugs

---

## Which Database Dependency Should I Use?

```python
# ✅ AUTHENTICATED ENDPOINTS (use this 95% of the time)
from dependencies import get_db_with_rls

@router.get("/alerts")
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db_with_rls)  # ⭐ USE THIS
):
    return db.query(Alert).all()

# ✅ PUBLIC ENDPOINTS (health, login, etc.)
from dependencies import get_db_public

@router.get("/health")
async def health_check(db: Session = Depends(get_db_public)):
    return {"status": "ok"}

# ⚠️ LEGACY (being phased out)
from dependencies import get_db

@router.get("/old-endpoint")
async def old_endpoint(db: Session = Depends(get_db)):
    # Still works but NO RLS PROTECTION
    return {}
```

---

## Decision Tree

```
┌─────────────────────────────────────────┐
│  Does endpoint require authentication?  │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
        YES                NO
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│get_db_with_rls()│  │ get_db_public() │
│   ✅ USE THIS   │  │  (health, etc)  │
└─────────────────┘  └─────────────────┘
```

---

## What Does RLS Do?

### Without RLS (BEFORE)
```python
# Developer makes a mistake:
alerts = db.query(Alert).all()  # ❌ Returns ALL orgs' data!
```

### With RLS (AFTER)
```python
# Same mistake, but RLS protects:
alerts = db.query(Alert).all()  # ✅ Only returns current org's data
                                 # PostgreSQL automatically adds WHERE clause
```

---

## Migration Checklist

When migrating a route to RLS:

```python
# BEFORE:
@router.get("/data")
async def get_data(
    org_filter: int = Depends(get_organization_filter),  # ❌ Remove this
    db: Session = Depends(get_db)                        # ❌ Replace this
):
    return db.query(Model).filter(Model.organization_id == org_filter).all()

# AFTER:
@router.get("/data")
async def get_data(
    current_user: dict = Depends(get_current_user),      # ✅ Add this
    db: Session = Depends(get_db_with_rls)               # ✅ Use this
):
    org_filter = current_user.get("organization_id")     # ✅ Get from user
    return db.query(Model).filter(Model.organization_id == org_filter).all()
    # Defense-in-depth: Both app filter AND RLS enforce isolation
```

**Checklist:**
- [ ] Replace `get_db` → `get_db_with_rls`
- [ ] Add `current_user: dict = Depends(get_current_user)`
- [ ] Replace `org_filter: int = Depends(get_organization_filter)` with `org_filter = current_user.get("organization_id")`
- [ ] Test endpoint still works
- [ ] Verify RLS is active in logs

---

## Testing RLS Activation

```python
from dependencies import verify_rls_active

# In your test:
db = next(get_db_with_rls(current_user={"organization_id": 123}))

# Verify RLS is active:
assert verify_rls_active(db, expected_org_id=123) == True
```

---

## Audit Logs to Watch For

```log
# ✅ Good - RLS activated successfully:
INFO - 🔐 SEC-082: RLS activated | org_id=4 | user=admin@acmecorp.com

# ⚠️ Warning - User missing organization_id:
WARNING - ⚠️ SEC-082: No organization_id in token | user=test@example.com

# 🚨 Error - RLS activation failed:
ERROR - 🚨 SEC-082: Failed to set RLS context | org_id=4 | error=...
```

---

## Common Questions

### Q: What if I need to query across organizations (admin report)?
A: Use `get_db_public()` but add explicit authorization checks:

```python
@router.get("/admin/all-alerts")
async def get_all_alerts(
    current_user: dict = Depends(require_admin),  # Check admin role
    db: Session = Depends(get_db_public)          # No RLS for cross-org query
):
    return db.query(Alert).all()  # Returns all orgs (authorized)
```

### Q: Will this break existing code?
A: No - `get_db()` still works for backward compatibility. But new code should use `get_db_with_rls()`.

### Q: What's the performance impact?
A: Negligible (~1ms per request). RLS uses indexed columns, same performance as manual filtering.

### Q: How do I know RLS is working?
A: Check logs for `🔐 SEC-082: RLS activated` messages. Use `verify_rls_active()` in tests.

---

## Priority Migration List

Migrate these routes FIRST (high-risk data):

1. `/api/alerts/*` - Alert data (PII/PHI)
2. `/api/agent-actions/*` - Action logs
3. `/api/governance/policies/*` - Policy configuration
4. `/api/automation/playbooks/*` - Playbook data
5. `/api/users/*` - User management

---

## Emergency Rollback

If RLS causes issues:

```python
# Temporarily disable RLS on a route:
from dependencies import get_db  # Use legacy function

@router.get("/problem-endpoint")
async def problematic_endpoint(
    db: Session = Depends(get_db)  # No RLS (temporary workaround)
):
    # Add to TODO: Investigate why RLS broke this endpoint
    return {}
```

---

## Security Benefits

```
┌────────────────────────────────────────────────────┐
│           DEFENSE-IN-DEPTH ACHIEVED                │
├────────────────────────────────────────────────────┤
│  Layer 1: JWT Authentication                       │
│  Layer 2: Role-Based Access Control                │
│  Layer 3: Application organization_id filtering    │
│  Layer 4: Database RLS policies (NEW!)             │
└────────────────────────────────────────────────────┘
```

Even if Layers 1-3 have bugs, Layer 4 (RLS) prevents data leakage.

---

## Files to Reference

- **Implementation:** `/Users/mac_001/OW_AI_Project/ow-ai-backend/dependencies.py`
- **Full Documentation:** `SEC-082_RLS_ACTIVATION_IMPLEMENTATION.md`
- **Tests:** `tests/test_sec082_rls_activation.py`

---

## Quick Commands

```bash
# Run tests:
pytest tests/test_sec082_rls_activation.py -v

# Check if a route uses RLS:
grep -n "get_db_with_rls" ow-ai-backend/routes/*.py

# Find routes still using legacy get_db:
grep -n "Depends(get_db)" ow-ai-backend/routes/*.py | grep -v "get_db_with_rls"
```

---

## Summary

| Aspect | Before SEC-082 | After SEC-082 |
|--------|----------------|---------------|
| **RLS Status** | Policies defined but INACTIVE | Policies ACTIVE |
| **Protection** | Application layer only | Application + Database layer |
| **Bug Impact** | One bug = data leakage | Defense-in-depth protects |
| **Migration** | N/A | Gradual, backward compatible |

---

**Remember:** Always use `get_db_with_rls()` for authenticated endpoints!

🔐 **RLS = Your safety net when application logic fails**
