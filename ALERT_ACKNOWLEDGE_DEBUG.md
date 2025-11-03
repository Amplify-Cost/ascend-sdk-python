# Alert Acknowledge/Escalate Debugging Guide

**Date:** 2025-10-30
**Issue:** Acknowledge and Escalate buttons not working in AI Alert Management

---

## Changes Made for Debugging

### Frontend Changes (/owkai-pilot-frontend/src/components/AIAlertManagementSystem.jsx)

**Before:**
```javascript
} else {
  setError('Failed to acknowledge alert');
}
```

**After:**
```javascript
} else {
  const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
  console.error('❌ Acknowledge failed:', {
    status: response.status,
    statusText: response.statusText,
    error: errorData
  });
  setError(`Failed to acknowledge alert: ${errorData.detail || response.statusText}`);
}
```

**What This Does:**
- Logs the actual HTTP status code (404, 500, etc.)
- Logs the error message from the backend
- Shows the detailed error in the UI instead of generic message

### Backend Changes (/ow-ai-backend/routes/smart_alerts.py)

Added logging at the start of both endpoints:

```python
logger.info(f"🔔 Acknowledge request received for alert {alert_id} by {current_user.get('email')}")
logger.info(f"⚠️ Escalate request received for alert {alert_id} by {current_user.get('email')}")
```

**What This Does:**
- Confirms the request reached the backend endpoint
- Shows which user is making the request
- Shows which alert ID is being targeted

---

## Next Steps for User

1. **Reload the frontend** (hard refresh: Cmd+Shift+R or Ctrl+Shift+R)
2. **Click Acknowledge or Escalate** on any alert
3. **Check browser console** for the new detailed error:
   ```
   ❌ Acknowledge failed: {
     status: 404,  // or 500, or 403, etc.
     statusText: "Not Found",
     error: { detail: "Alert not found" }
   }
   ```
4. **Check backend terminal** for the log entry:
   ```
   INFO:routes.smart_alerts:🔔 Acknowledge request received for alert 5 by admin@owkai.com
   ```

---

## Possible Issues and Solutions

### Issue 1: Backend shows NO log entry
**Diagnosis:** Request not reaching the backend
**Possible Causes:**
- CORS blocking the request
- Wrong URL (frontend calling different endpoint)
- Network error

**Solution:**
Check browser Network tab:
- Is the request being sent?
- What's the actual URL?
- What's the HTTP status?

### Issue 2: Backend shows "404 Not Found"
**Diagnosis:** Alert doesn't exist in database
**Solution:**
```sql
-- Check what alerts exist
SELECT id, severity, status FROM alerts ORDER BY id;
```
Try acknowledging an alert that exists in the database.

### Issue 3: Backend shows "Alert not found" (line 266 in smart_alerts.py)
**Diagnosis:** Alert ID not in database AND not in demo alert range (3001-3005)
**Solution:**
- Use an alert ID that exists in database (1-15)
- Or use demo alert IDs (3001-3005)

### Issue 4: Backend shows "403 Forbidden" or "CSRF token missing"
**Diagnosis:** CSRF protection failing
**Solution:**
Check that cookies include `owai_csrf` token and frontend sends `X-CSRF-Token` header.

### Issue 5: Backend shows "401 Unauthorized"
**Diagnosis:** Authentication failing
**Solution:**
Re-login to get fresh session cookies.

---

##Current Alert IDs in Database

Run this to see what alerts exist:
```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
python3 -c "
from database import get_db
from sqlalchemy import text
db = next(get_db())
alerts = db.execute(text('SELECT id, severity, status FROM alerts ORDER BY id')).fetchall()
for a in alerts:
    print(f'ID: {a[0]} | Severity: {a[1]} | Status: {a[2]}')
db.close()
"
```

---

## Expected Behavior

When acknowledge button is clicked:

1. **Frontend:**
   - Sends POST to `/api/alerts/{id}/acknowledge`
   - Includes cookies (owai_session, owai_csrf)
   - Includes header `X-CSRF-Token`

2. **Backend:**
   - Logs: `🔔 Acknowledge request received for alert {id}`
   - Tries to update database
   - If successful: Returns `{"success": true, "message": "Alert acknowledged successfully"}`
   - If not found: Returns 404 with `{"detail": "Alert not found"}`

3. **Frontend:**
   - If success (200 OK): Shows "✅ Alert acknowledged successfully"
   - If error: Shows detailed error message

---

**After making these changes, please test again and share the new console output!**
