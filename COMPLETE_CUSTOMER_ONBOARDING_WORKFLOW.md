# 🚀 COMPLETE CUSTOMER ONBOARDING & TESTING WORKFLOW

**Created:** 2025-11-10
**Purpose:** Step-by-step guide to onboard a new customer and test all platform features end-to-end

---

## 📋 TABLE OF CONTENTS

1. [Pre-Onboarding Setup](#1-pre-onboarding-setup)
2. [Create New Organization](#2-create-new-organization)
3. [Send Agent Actions to Your App](#3-send-agent-actions-to-your-app)
4. [Trigger and Respond to Alerts](#4-trigger-and-respond-to-alerts)
5. [Test Authorization Workflow](#5-test-authorization-workflow)
6. [Monitor and Verify](#6-monitor-and-verify)
7. [Production Deployment](#7-production-deployment)

---

## 1. PRE-ONBOARDING SETUP

### Option A: Automated Onboarding (Recommended)

**Create a new customer instantly:**

```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

# Create your own organization
python3 customer_onboarding_simulation.py \
  --customer "Acme Corporation" \
  --domain "acme-demo.com"
```

**What this creates:**
- 4 user accounts (CEO, Security Manager, 2 Engineers)
- 15 agent actions (varied statuses)
- 12 security alerts
- All with realistic data patterns

**Login credentials created:**
- CEO: `ceo@acme-demo.com` / `Demo2024!`
- Manager: `security.manager@acme-demo.com` / `Demo2024!`
- Engineer 1: `engineer1@acme-demo.com` / `Demo2024!`
- Engineer 2: `engineer2@acme-demo.com` / `Demo2024!`

### Option B: Manual Onboarding (For Real Customers)

**Step-by-step manual user creation:**

```bash
# Connect to production database
export PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL'
PSQL="/opt/homebrew/opt/postgresql@14/bin/psql -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com -p 5432 -U owkai_admin -d owkai_pilot"

# Create admin user
$PSQL -c "
INSERT INTO users (email, password, role, approval_level, is_emergency_approver, max_risk_approval, is_active, created_at, password_last_changed)
VALUES (
  'admin@yourcustomer.com',
  '\$2b\$14\$HASHED_REDACTED-CREDENTIAL_HERE',  -- Generate with bcrypt
  'admin',
  5,
  true,
  100,
  true,
  NOW(),
  NOW()
);
"
```

**Generate bcrypt password:**
```python
import bcrypt
password = "REDACTED-CREDENTIAL"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=14))
print(hashed.decode('utf-8'))
```

---

## 2. CREATE NEW ORGANIZATION

### Verify Organization Created

```bash
# Check users were created
export PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL'
/opt/homebrew/opt/postgresql@14/bin/psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 -U owkai_admin -d owkai_pilot \
  -c "SELECT id, email, role, approval_level FROM users WHERE email LIKE '%acme-demo.com';"
```

**Expected Output:**
```
id |            email             | role    | approval_level
---+------------------------------+---------+---------------
26 | ceo@acme-demo.com            | admin   | 5
27 | security.manager@acme-demo.com| manager | 3
28 | engineer1@acme-demo.com      | user    | 1
29 | engineer2@acme-demo.com      | user    | 1
```

---

## 3. SEND AGENT ACTIONS TO YOUR APP

### 3.1 Understanding Agent Actions

Agent actions represent AI agents requesting to perform operations that require human approval.

**Agent Action Flow:**
```
AI Agent → Action Request → Authorization Center → Human Approver → Execution
```

### 3.2 Create Agent Action via API

**Get authentication token first:**

```bash
# Login to get token
TOKEN=$(curl -s -X POST "https://pilot.owkai.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@acme-demo.com",
    "password": "Demo2024!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

**Submit agent action:**

```bash
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "data-migration-agent",
    "action_type": "database_write",
    "description": "Migrate 50,000 customer records from legacy system to new database",
    "tool_name": "postgresql_connector",
    "risk_level": "high",
    "risk_score": 85,
    "target_system": "production-db",
    "target_resource": "customers_table",
    "nist_control": "AC-2",
    "mitre_tactic": "TA0001",
    "requires_approval": true
  }'
```

**Expected Response:**
```json
{
  "id": 156,
  "agent_id": "data-migration-agent",
  "status": "pending_approval",
  "risk_score": 85,
  "created_at": "2025-11-10T21:15:00Z"
}
```

### 3.3 Create Multiple Test Actions

**Script to create varied test actions:**

```bash
# Save as: create_test_actions.sh
TOKEN="your_token_here"

# High-risk database operation
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "db-admin-agent",
    "action_type": "database_write",
    "description": "Delete outdated customer records (GDPR compliance)",
    "risk_score": 90,
    "requires_approval": true
  }'

# Medium-risk file operation
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "file-processor",
    "action_type": "file_write",
    "description": "Generate and save monthly financial report",
    "risk_score": 55,
    "requires_approval": true
  }'

# Low-risk read operation
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "analytics-agent",
    "action_type": "data_read",
    "description": "Query user engagement metrics for dashboard",
    "risk_score": 25,
    "requires_approval": false
  }'
```

### 3.4 Verify Actions Created

**Check in Authorization Center:**

1. Login to https://pilot.owkai.app
2. Navigate to "Authorization Center"
3. Look for "Pending Actions" card
4. Should see your newly created actions

**Or check via API:**

```bash
curl "https://pilot.owkai.app/api/authorization/dashboard" \
  -H "Authorization: Bearer $TOKEN" | jq '.pending_actions | length'
```

---

## 4. TRIGGER AND RESPOND TO ALERTS

### 4.1 Understanding Alerts

Alerts are security incidents triggered by:
- High-risk agent actions
- Policy violations
- Anomalous behavior
- Compliance issues

### 4.2 Create Alert Manually

```bash
# Create high-severity alert
curl -X POST "https://pilot.owkai.app/api/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "High Risk Agent Action",
    "severity": "critical",
    "message": "Agent attempted to access production database without approval",
    "agent_id": "unauthorized-agent-001",
    "status": "new"
  }'
```

### 4.3 Alerts Are Auto-Generated

**Agent actions with high risk automatically create alerts:**

```bash
# This action will trigger an alert
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "production-modifier",
    "action_type": "system_modification",
    "description": "Modify production firewall rules",
    "risk_score": 95,
    "requires_approval": true
  }'
```

**System will:**
1. Create the agent action with `pending_approval` status
2. Auto-generate a "High Risk Agent Action" alert
3. Display both in their respective dashboards

### 4.4 Respond to Alerts

**Via Web Interface (Recommended):**

1. Login to https://pilot.owkai.app
2. Navigate to "AI Alert Management"
3. Click on an alert
4. Options:
   - **Acknowledge** - Mark as reviewed
   - **Escalate** - Send to higher authority
   - **Mark as False Positive** - Dismiss as benign

**Via API:**

```bash
# Acknowledge alert
curl -X PUT "https://pilot.owkai.app/api/alerts/123/acknowledge" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "acknowledged_by": "ceo@acme-demo.com",
    "notes": "Reviewed and validated. Proceeding with authorization."
  }'

# Escalate alert
curl -X PUT "https://pilot.owkai.app/api/alerts/123/escalate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "escalated_by": "security.manager@acme-demo.com",
    "escalation_reason": "Requires executive approval due to data sensitivity"
  }'
```

---

## 5. TEST AUTHORIZATION WORKFLOW

### 5.1 Complete Authorization Flow

**Scenario: High-Risk Database Migration**

**Step 1: Agent submits action**
```bash
ACTION_ID=$(curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "migration-agent",
    "action_type": "database_write",
    "description": "Migrate 100,000 records to new schema",
    "risk_score": 88,
    "requires_approval": true
  }' | jq -r '.id')

echo "Action ID: $ACTION_ID"
```

**Step 2: Action appears in Authorization Center**
- Status: `pending_approval`
- Risk Score: 88 (High)
- Requires: Manager approval (Level 3+)

**Step 3: Review and approve**

```bash
# Approve action
curl -X PUT "https://pilot.owkai.app/api/agent-action/${ACTION_ID}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved_by": "ceo@acme-demo.com",
    "approval_notes": "Approved for weekend maintenance window",
    "conditions": "Execute between 2 AM - 4 AM UTC only"
  }'
```

**Step 4: Or reject action**

```bash
# Reject action
curl -X PUT "https://pilot.owkai.app/api/agent-action/${ACTION_ID}/reject" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rejected_by": "security.manager@acme-demo.com",
    "rejection_reason": "Insufficient testing in staging environment"
  }'
```

**Step 5: Verify status changed**

```bash
curl "https://pilot.owkai.app/api/agent-action/${ACTION_ID}" \
  -H "Authorization: Bearer $TOKEN" | jq '{status, approved_by, reviewed_at}'
```

### 5.2 Test Multi-Level Approval

**Create action requiring multiple approvals:**

```bash
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "critical-ops-agent",
    "action_type": "system_shutdown",
    "description": "Emergency shutdown of production cluster",
    "risk_score": 99,
    "requires_approval": true,
    "approval_chain": [
      {"level": 1, "role": "engineer"},
      {"level": 3, "role": "manager"},
      {"level": 5, "role": "admin"}
    ]
  }'
```

**Multi-step approval process:**
1. Engineer reviews first (Level 1)
2. Manager approves second (Level 3)
3. Admin gives final approval (Level 5)

---

## 6. MONITOR AND VERIFY

### 6.1 Dashboard Monitoring

**Login and check:**
1. **Dashboard** - View analytics and trends
2. **Authorization Center** - Monitor pending actions
3. **AI Alert Management** - Review security alerts
4. **Activity Feed** - See recent agent activity
5. **Smart Rules** - Check active rules

### 6.2 Verification Queries

**Check pending actions:**
```bash
curl "https://pilot.owkai.app/api/authorization/dashboard" \
  -H "Authorization: Bearer $TOKEN" | jq '.summary'
```

**Expected:**
```json
{
  "total_pending": 5,
  "critical_pending": 2,
  "emergency_pending": 0
}
```

**Check alerts:**
```bash
curl "https://pilot.owkai.app/api/alerts" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
```

**Check activity feed:**
```bash
curl "https://pilot.owkai.app/api/authorization/automation/activity-feed?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0:3]'
```

### 6.3 Database Verification

**Verify data in production database:**

```bash
export PGREDACTED-CREDENTIAL='REDACTED-CREDENTIAL'
/opt/homebrew/opt/postgresql@14/bin/psql \
  -h owkai-pilot-db.cpwaouykib7n.us-east-2.rds.amazonaws.com \
  -p 5432 -U owkai_admin -d owkai_pilot \
  -c "
SELECT
  aa.id,
  aa.agent_id,
  aa.status,
  aa.risk_score,
  u.email as requested_by,
  TO_CHAR(aa.created_at, 'YYYY-MM-DD HH24:MI') as created
FROM agent_actions aa
LEFT JOIN users u ON aa.user_id = u.id
WHERE u.email LIKE '%acme-demo.com'
ORDER BY aa.created_at DESC
LIMIT 10;
"
```

---

## 7. PRODUCTION DEPLOYMENT

### 7.1 Customer Onboarding Checklist

**For real customer onboarding:**

- [ ] Create organization admin account
- [ ] Send welcome email with credentials
- [ ] Configure SSO (if applicable)
- [ ] Set up approval workflows
- [ ] Configure alert thresholds
- [ ] Train team on platform
- [ ] Integrate with customer's AI agents
- [ ] Set up API keys
- [ ] Configure webhooks (if needed)
- [ ] Enable audit logging
- [ ] Set data retention policies

### 7.2 Integration with Customer's AI Agents

**Provide customer with API endpoint:**

```bash
# Customer's AI agent sends actions to your platform
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer {CUSTOMER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "customer-ai-agent-001",
    "action_type": "database_write",
    "description": "Action description",
    "risk_score": 75
  }'
```

**Customer receives:**
- API documentation
- Authentication tokens
- Webhook endpoints
- Integration examples
- Support contact

### 7.3 Ongoing Support

**Monitoring for customer:**
- Weekly usage reports
- Security alert summaries
- Performance metrics
- Compliance reports

**Customer success metrics:**
- Actions approved/rejected
- Average approval time
- Alert response time
- User adoption rate

---

## 📊 COMPLETE TESTING SCENARIO

### Real-World Simulation

**Scenario: Healthcare Company - HIPAA Compliance**

```bash
# Create organization
python3 customer_onboarding_simulation.py \
  --customer "HealthCare Plus" \
  --domain "healthcareplus-demo.com"

# Login as admin
TOKEN=$(curl -s -X POST "https://pilot.owkai.app/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "ceo@healthcareplus-demo.com", "password": "Demo2024!"}' \
  | jq -r '.access_token')

# Agent requests patient data access
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "medical-records-ai",
    "action_type": "data_read",
    "description": "Access 500 patient records for treatment analysis",
    "risk_score": 85,
    "compliance_framework": "HIPAA",
    "requires_approval": true
  }'

# System creates alert (HIPAA data access)
# Security manager reviews in Authorization Center
# Manager approves with conditions
# Audit log captures everything
# Compliance report generated
```

**Test this end-to-end:**
1. ✅ Organization created
2. ✅ Agent action submitted
3. ✅ Alert triggered
4. ✅ Approval workflow executed
5. ✅ Audit trail captured
6. ✅ Compliance documented

---

## 🎯 SUCCESS CRITERIA

**Your onboarding is successful when:**

1. ✅ New organization users can login
2. ✅ Agent actions appear in Authorization Center
3. ✅ Alerts are created and displayed
4. ✅ Approval workflow functions (approve/reject)
5. ✅ Dashboard shows real-time data
6. ✅ Activity feed displays actions
7. ✅ All data persists in database
8. ✅ Zero console errors
9. ✅ Audit logs capture all events
10. ✅ Users can respond to alerts

---

## 🔧 TROUBLESHOOTING

### Issue: Can't Login

**Check user exists:**
```bash
psql ... -c "SELECT email, is_active FROM users WHERE email = 'your@email.com';"
```

**Verify password:**
```python
import bcrypt
# Check if password matches hash
bcrypt.checkpw(b"Demo2024!", stored_hash.encode('utf-8'))
```

### Issue: Actions Not Appearing

**Check action was created:**
```bash
psql ... -c "SELECT id, agent_id, status FROM agent_actions ORDER BY id DESC LIMIT 5;"
```

**Check user_id matches:**
```bash
psql ... -c "SELECT id FROM users WHERE email = 'your@email.com';"
```

### Issue: Alerts Not Triggering

**Verify risk score threshold:**
- Actions with `risk_score >= 80` should auto-create alerts
- Check alert table: `SELECT * FROM alerts WHERE timestamp >= NOW() - INTERVAL '1 hour';`

---

## 📚 API DOCUMENTATION

### Core Endpoints

**Authentication:**
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token

**Agent Actions:**
- `POST /api/agent-action` - Create action
- `GET /api/agent-action/{id}` - Get action
- `PUT /api/agent-action/{id}/approve` - Approve
- `PUT /api/agent-action/{id}/reject` - Reject

**Alerts:**
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `PUT /api/alerts/{id}/acknowledge` - Acknowledge
- `PUT /api/alerts/{id}/escalate` - Escalate

**Authorization:**
- `GET /api/authorization/dashboard` - Dashboard data
- `GET /api/authorization/automation/activity-feed` - Activity feed

---

**Next Steps:**
1. Run the automated onboarding script for your test organization
2. Login to the platform
3. Submit test agent actions
4. Review and respond to alerts
5. Test the complete workflow

This is your complete customer onboarding playbook!
