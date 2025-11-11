# 🎬 LIVE AGENT SIMULATOR - See Your Platform in Action!

**Purpose:** Watch your platform actively catch and monitor AI agent actions in REAL-TIME

---

## 🚀 QUICK START

### Step 1: Open Two Windows

**Window 1 - Run the simulator:**
```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend

# Start sending live agent actions
python3 live_agent_simulator.py \
  --email admin@owkai.com \
  --password your_password \
  --interval 10
```

**Window 2 - Open your platform:**
```
https://pilot.owkai.app
```
Login and keep these tabs open:
- Authorization Center
- AI Alert Management
- Dashboard
- Activity Feed

### Step 2: Watch It Work!

The simulator will send realistic agent actions every 10 seconds. You'll see:

**In Terminal (Window 1):**
```
[21:15:30] Sending Agent Action #1
  Agent: payment-processor
  Action: api_call
  Risk Score: 85 (high)
  Description: Processing customer payment via Stripe API
  ✅ Action sent successfully (ID: 234)
  ⚠️  Requires approval - Check Authorization Center
  🚨 ALERT TRIGGERED - Check AI Alert Management
```

**In Browser (Window 2):**
- **Authorization Center** → Counter increments → New pending action appears
- **AI Alert Management** → New alert appears for high-risk action
- **Dashboard** → Metrics update in real-time
- **Activity Feed** → New activity shows up

---

## 📊 WHAT THE SIMULATOR DOES

### Realistic AI Agent Scenarios

The simulator mimics 10 different AI agents:

**Low Risk (Common):**
- 📊 `analytics-reporter` - Generating reports (risk: 10-30)
- 💾 `backup-automation` - Creating backups (risk: 15-35)
- 📧 `email-marketing` - Sending emails (risk: 20-40)
- 📄 `document-processor` - Processing files (risk: 25-45)

**Medium Risk (Common):**
- 🔄 `data-sync-agent` - Database sync (risk: 50-75)

**High Risk (Rare):**
- 💳 `payment-processor` - Processing payments (risk: 75-90)
- 📤 `data-export-agent` - Exporting data (risk: 80-95)
- 🤖 `ml-model-updater` - Deploying ML models (risk: 70-85)

**Critical Risk (Very Rare):**
- 👤 `user-provisioning` - Creating admin accounts (risk: 90-99)
- 🔐 `firewall-manager` - Modifying firewall rules (risk: 85-99)

### Frequency Distribution

Actions are weighted by frequency:
- **Common** (70%): Low/medium risk actions happen frequently
- **Rare** (25%): High-risk actions happen occasionally
- **Very Rare** (5%): Critical actions happen rarely

This creates realistic patterns where:
- You see steady stream of normal activity
- Occasional high-risk alerts pop up
- Rare critical incidents require immediate attention

---

## 🧪 TESTING SCENARIOS

### Scenario 1: Monitor Real-Time Activity (5 minutes)

```bash
# Start simulator with 5-second intervals (faster)
python3 live_agent_simulator.py \
  --email admin@owkai.com \
  --password your_password \
  --interval 5
```

**What to watch:**
1. Open Authorization Center
2. Watch pending actions counter increment
3. See new actions appear in list
4. Try approving/rejecting actions as they come in
5. Verify counter decrements when you approve

**Expected Result:** Real-time updates as simulator sends actions

---

### Scenario 2: Alert Response Workflow (10 minutes)

```bash
# Normal interval
python3 live_agent_simulator.py \
  --email admin@owkai.com \
  --password your_password \
  --interval 10
```

**Workflow:**
1. **Simulator sends high-risk action** (risk score 85+)
   - Terminal shows: `🚨 ALERT TRIGGERED`

2. **Alert appears in AI Alert Management**
   - Navigate to AI Alerts
   - See new "High Risk Agent Action" alert
   - Risk score matches what simulator sent

3. **Review the alert**
   - Click on alert to see details
   - See agent ID, description, timestamp

4. **Respond to alert**
   - Click "Acknowledge" → Add notes
   - Or click "Escalate" if critical

5. **Verify in Authorization Center**
   - Corresponding action should be "pending_approval"
   - Approve or reject the action

6. **Check Activity Feed**
   - See the complete audit trail
   - Timestamp, user, decision all logged

**Expected Result:** Complete workflow from detection → alert → response → approval

---

### Scenario 3: Stress Test (30 minutes)

```bash
# Fast interval - lots of activity
python3 live_agent_simulator.py \
  --email admin@owkai.com \
  --password your_password \
  --interval 3
```

**What to test:**
- Can platform handle high volume?
- Do counters stay accurate?
- Are all actions captured?
- Any performance degradation?
- Console errors?

**Expected Result:** Platform handles load smoothly, zero errors

---

## 📈 WHAT YOU'LL SEE

### Terminal Output Example

```
================================================================================
        LIVE AGENT SIMULATOR - Real-Time Platform Testing
================================================================================

Platform: https://pilot.owkai.app
User: admin@owkai.com
Interval: ~10 seconds between actions
Started: 2025-11-10 21:30:00

🔐 Authenticating...
✅ Authenticated successfully
Token: eyJhbGciOiJIUzI1NiIsInR5cC...

🚀 SIMULATOR STARTED
Sending realistic agent actions every ~10 seconds...
Press Ctrl+C to stop

Watch your platform at: https://pilot.owkai.app
  - Authorization Center: See pending actions appear
  - AI Alert Management: See alerts trigger
  - Dashboard: Watch metrics update
  - Activity Feed: See live agent activity


[21:30:05] Sending Agent Action #1
  Agent: data-sync-agent
  Action: database_write
  Risk Score: 62 (medium)
  Description: Synchronizing customer data from Salesforce to PostgreSQL - Batch #427
  ✅ Action sent successfully (ID: 245)

⏳ Next action in 12 seconds...

[21:30:17] Sending Agent Action #2
  Agent: payment-processor
  Action: api_call
  Risk Score: 87 (high)
  Description: Processing customer payment via Stripe API
  ✅ Action sent successfully (ID: 246)
  ⚠️  Requires approval - Check Authorization Center
  🚨 ALERT TRIGGERED - Check AI Alert Management

⏳ Next action in 8 seconds...

[21:30:25] Sending Agent Action #3
  Agent: email-marketing
  Action: email_send
  Risk Score: 28 (low)
  Description: Sending automated marketing email campaign (scheduled task)
  ✅ Action sent successfully (ID: 247)

⏳ Next action in 11 seconds...

...

────────────────────────────────────────────────────────────────────────────────
Statistics:
  Actions Sent: 15
  Alerts Generated: 4
  Rate: 3.2 actions/minute
  Runtime: 280 seconds
────────────────────────────────────────────────────────────────────────────────
```

### Browser View

**Authorization Center:**
```
╔════════════════════════════════════════════════╗
║  Pending Actions: 7 ← Updates in real-time!   ║
║  Critical: 2                                   ║
║  Emergency: 0                                  ║
╚════════════════════════════════════════════════╝

Recent Actions:
[21:30:25] email-marketing         | Low    | 28  | Pending
[21:30:17] payment-processor       | High   | 87  | Pending ← Just appeared!
[21:30:05] data-sync-agent         | Medium | 62  | Pending
```

**AI Alert Management:**
```
Alerts: 12 total

[21:30:17] 🚨 High Risk Agent Action - CRITICAL
  Agent: payment-processor
  Risk Score: 87
  Status: New ← Just triggered!

[21:29:45] ⚠️  High Risk Agent Action - HIGH
  Agent: data-export-agent
  Risk Score: 82
  Status: Acknowledged
```

---

## 🎯 SUCCESS CRITERIA

Your platform is working perfectly when you can:

1. ✅ **ALL actions are logged** (100% of actions from simulator)
   - **Analytics Dashboard** → See ALL actions (approved + pending)
   - **Activity Feed** → See chronological list of ALL agent actions
   - **Agent Actions table in database** → Every single action persisted

2. ✅ **High-risk actions require approval** (risk score 70+)
   - **Authorization Center** → See pending actions (score 70+)
   - Counter shows number of pending actions
   - Low-risk actions (< 70) auto-approved but still logged

3. ✅ **Critical actions trigger alerts** (risk score 80+)
   - **AI Alert Management** → New alerts appear
   - Alert type: "High Risk Agent Action"
   - Alert severity: "critical" (90+) or "high" (80-89)

4. ✅ **Approval workflow works**
   - Click approve/reject on pending action
   - Status updates immediately
   - Counter decrements
   - Action moves to completed/rejected list

5. ✅ **Dashboard updates**
   - **Analytics** → All actions shown in graphs
   - Metrics reflect new actions
   - Trends update
   - Charts show activity

6. ✅ **Zero console errors**
   - Open DevTools → Console
   - No 500 errors
   - No failed requests
   - All APIs returning 200 OK

## 📍 WHERE TO FIND EVERY ACTION

**ALL actions are logged in multiple places:**

1. **Analytics Dashboard** (`/analytics`)
   - Shows ALL agent actions (approved, pending, rejected)
   - See risk distribution, top agents, top tools
   - Every action from simulator appears here

2. **Activity Feed** (`/activity` or Authorization Center → Activity tab)
   - Chronological list of ALL agent actions
   - Shows timestamps, agent IDs, risk scores
   - Filter by status, risk level, date range

3. **Authorization Center** (`/authorization-center`)
   - **Pending tab**: Only high-risk actions (score 70+) awaiting approval
   - **Approved/Rejected tabs**: Actions after decision
   - Low-risk actions auto-approved but still in database

4. **AI Alert Management** (`/alerts`)
   - Only critical actions (score 80+) that triggered alerts
   - Subset of all actions - the most dangerous ones

5. **Database** (agent_actions table)
   - Every single action persisted permanently
   - Query: `SELECT * FROM agent_actions ORDER BY timestamp DESC;`

---

## 🛠️ CUSTOMIZATION

### Adjust Speed

```bash
# Very fast (stress test)
python3 live_agent_simulator.py --email admin@owkai.com --password pw --interval 3

# Normal speed
python3 live_agent_simulator.py --email admin@owkai.com --password pw --interval 10

# Slow (demo/presentation)
python3 live_agent_simulator.py --email admin@owkai.com --password pw --interval 20
```

### Stop Simulator

Press `Ctrl+C` to stop gracefully. You'll see final statistics:

```
⚠️  Simulator stopped by user

────────────────────────────────────────────────────────────────────────────────
Statistics:
  Actions Sent: 42
  Alerts Generated: 11
  Rate: 4.2 actions/minute
  Runtime: 600 seconds
────────────────────────────────────────────────────────────────────────────────

✅ Simulation complete
```

---

## 💡 TIPS FOR BEST DEMO

### Prepare Your Screen

**Layout 1: Side by Side**
```
┌─────────────────┬─────────────────┐
│   Terminal      │   Browser       │
│   (Simulator)   │   (Platform)    │
│                 │                 │
│  Sending        │  Authorization  │
│  actions...     │  Center showing │
│                 │  new actions    │
└─────────────────┴─────────────────┘
```

**Layout 2: Multiple Tabs**
- Tab 1: Authorization Center (main view)
- Tab 2: AI Alert Management (watch alerts)
- Tab 3: Dashboard (see trends)
- Tab 4: Activity Feed (audit trail)

### Demo Script (5 minutes)

1. **Start simulator** (30 sec)
   - Show terminal starting
   - Explain what it's doing

2. **Show Authorization Center** (2 min)
   - Watch counter increment
   - Point out risk scores
   - Approve one action live
   - Show counter decrement

3. **Show Alert Triggered** (1 min)
   - Wait for high-risk action (risk 80+)
   - Show alert in AI Alerts
   - Acknowledge it
   - Show audit trail

4. **Show Dashboard** (1 min)
   - Point out updated metrics
   - Show activity trends
   - Real data, not fake!

5. **Show Activity Feed** (30 sec)
   - Recent actions
   - Timestamps
   - Complete audit trail

---

## 🚨 TROUBLESHOOTING

### Simulator won't authenticate

**Check credentials:**
```bash
# Verify user exists
export PGREDACTED-CREDENTIAL='...'
psql ... -c "SELECT email, is_active FROM users WHERE email = 'admin@owkai.com';"
```

### Actions not appearing in platform

**Check browser console:**
- Open DevTools → Console
- Look for API errors
- Check network tab for failed requests

**Refresh Authorization Center:**
- Click refresh or reload page
- Actions should appear

### Want to see database updates?

**Query while simulator runs:**
```bash
# In another terminal, watch database
watch -n 2 "psql ... -c 'SELECT COUNT(*) FROM agent_actions WHERE created_at >= NOW() - INTERVAL \"5 minutes\";'"
```

---

## 🎉 WHAT THIS PROVES

Running the live simulator demonstrates:

1. ✅ **Real-time monitoring works** - Platform catches actions as they happen
2. ✅ **Alert system works** - High-risk actions trigger alerts automatically
3. ✅ **Authorization workflow works** - Can approve/reject in real-time
4. ✅ **Dashboard updates work** - Metrics reflect live data
5. ✅ **Audit trail works** - Complete history of all actions
6. ✅ **Platform is production-ready** - Handles continuous load

**This is your platform operating exactly as it would with real AI agents in production!**

---

**Ready to see it in action?**

```bash
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
python3 live_agent_simulator.py --email admin@owkai.com --password your_password --interval 10
```

Then open https://pilot.owkai.app and watch your platform work in real-time!
