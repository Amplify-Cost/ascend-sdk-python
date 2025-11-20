# 🏢 Enterprise Production Simulator - Quick Start Guide

**Purpose**: Simulate real-world customer usage of your OW-kai platform with agent actions and MCP server requests.

---

## 🚀 Quick Start

### **Run Against Production (Burst Mode - 20 actions)**

```bash
cd /Users/mac_001/OW_AI_Project

python3 enterprise_production_simulator.py --url https://pilot.owkai.app --mode burst
```

### **Run Against Production (Continuous Mode - 60 seconds)**

```bash
cd /Users/mac_001/OW_AI_Project

python3 enterprise_production_simulator.py --url https://pilot.owkai.app --mode continuous --duration 60
```

### **Run Against Production (Realistic Mode - 5 minutes)**

```bash
cd /Users/mac_001/OW_AI_Project

python3 enterprise_production_simulator.py --url https://pilot.owkai.app --mode realistic --duration 300
```

### **Run Against Local Development**

```bash
cd /Users/mac_001/OW_AI_Project

python3 enterprise_production_simulator.py --url http://localhost:8000 --mode burst
```

**Note**: Authentication credentials are hardcoded in the script:
- Email: `admin@owkai.com`
- Password: `admin123`

---

## 📋 Simulation Modes

### **Burst Mode** (`--mode burst`)
- Sends **20 actions quickly** (alternating agent and MCP actions)
- Takes ~10-15 seconds
- Great for quick testing

### **Continuous Mode** (`--mode continuous`)
- Simulates steady enterprise usage
- Random 1-5 second delays between actions
- 60% agent actions, 40% MCP actions
- Runs for specified duration (default: 60 seconds)
- Prints stats every 10 seconds

### **Realistic Mode** (`--mode realistic`)
- Simulates workday activity patterns:
  - Morning rush (fast, high agent ratio)
  - Midday steady (moderate pace)
  - Afternoon peak (very fast)
  - Evening quiet (slow, low agent ratio)
- Cycles through patterns
- Runs for specified duration
- Prints stats every 15 seconds

---

## 📋 What It Tests

The simulator creates realistic enterprise scenarios:

### **1. Enterprise Agent Scenarios**

**Data Analytics**:
- Query customer analytics data (LOW risk)
- Update aggregated metrics (MEDIUM risk)

**Financial Processing**:
- Retrieve transaction history (MEDIUM risk)
- Process batch payments (HIGH risk)
- Submit payment to processor (HIGH risk)

**Healthcare Records**:
- Access patient medical records (HIGH risk - HIPAA protected)
- Update patient diagnosis codes (CRITICAL risk)

**Infrastructure Management**:
- List EC2 instances (LOW risk)
- Terminate staging instances (MEDIUM risk)
- Modify production RDS instance (HIGH risk)

**Customer Service**:
- Lookup customer account details (MEDIUM risk)
- Process customer refund (HIGH risk)

### **2. MCP Server Actions**

**Filesystem Server**:
- Read file (LOW risk)
- Write file (MEDIUM risk)
- Write production config (HIGH risk)

**Database MCP Server**:
- Execute SELECT query (MEDIUM risk)
- Execute DELETE query (HIGH risk)

**AWS MCP Server**:
- S3 upload to backups (MEDIUM risk)

**Slack MCP Server**:
- Send message to alerts channel (LOW risk)

---

## 📊 Expected Output

The simulator will show:

```
================================================================================
🏢 OW-KAI ENTERPRISE PRODUCTION SIMULATOR
🎯 Target: https://pilot.owkai.app
📊 Mode: BURST
================================================================================

[20:30:45] ✅ Authenticated successfully

[20:30:46] 🤖 AGENT ACTION #307 | data-pipeline-agent | LOW (Score: 25) | Status: approved | Query customer analytics data
[20:30:47] 🔧 MCP ACTION #308 | filesystem-server | Tool: read_file | LOW | Decision: approved
[20:30:48] 🤖 AGENT ACTION #309 | payment-processor-a | MEDIUM (Score: 55) | Status: pending_approval | Retrieve transaction history
[20:30:49] 🔧 MCP ACTION #310 | database-mcp-server | Tool: execute_query | MEDIUM | Decision: approved
[20:30:50] 🤖 AGENT ACTION #311 | fraud-detection-age | HIGH (Score: 75) | Status: pending_approval | Process batch payments
[20:30:51] 🔧 MCP ACTION #312 | filesystem-server | Tool: write_file | HIGH | Decision: pending
...

================================================================================
📊 SIMULATION STATISTICS
================================================================================
⏱️  Runtime: 15s | Rate: 1.33 actions/sec
📈 Total Actions: 20
   🤖 Agent Actions: 10
   🔧 MCP Actions: 10

🎯 Risk Distribution:
   ● LOW: 6
   ● MEDIUM: 8
   ● HIGH: 5
   ● CRITICAL: 1

📋 Status:
   ✅ Approved: 12
   ⏳ Pending: 7
   ❌ Denied: 0
   💥 Errors: 1
================================================================================
```

---

## 🔍 What to Check After Running

### **1. Agent Authorization Dashboard**
Go to: https://pilot.owkai.app → Authorization Center

**Check**:
- ✅ New actions appear in the Activity tab
- ✅ Actions are categorized by risk level
- ✅ Low-risk actions are auto-approved (if policies configured)
- ✅ High-risk actions require approval
- ✅ Policy evaluations are logged

### **2. Unified Authorization Queue**
Go to: https://pilot.owkai.app → Authorization Center → Queue

**Check**:
- ✅ All 25 actions appear in queue
- ✅ Actions show correct status (approved/pending/denied)
- ✅ Risk scores are calculated correctly
- ✅ Policy evaluations are shown

### **3. Audit Logs**
Go to: https://pilot.owkai.app → Audit Logs

**Check**:
- ✅ All actions are logged
- ✅ Timestamps are correct
- ✅ User attribution is correct (admin@owkai.com)
- ✅ Metadata is captured

### **4. Analytics Dashboard**
Go to: https://pilot.owkai.app → Analytics

**Check**:
- ✅ Action count increased by 25
- ✅ Risk distribution shows low/medium/high
- ✅ Policy evaluation metrics updated

---

## 🛠️ Troubleshooting

### **Error: "Authentication failed"**

**Cause**: Wrong credentials or API endpoint

**Fix**:
```bash
# Check if backend is running
curl https://pilot.owkai.app/

# Or for local:
curl http://localhost:8000/

# Verify credentials
# Email: admin@owkai.com
# Password: Admin@123
```

### **Error: "Connection refused"**

**Cause**: Backend not running

**Fix**:
```bash
# For local development, start backend:
cd /Users/mac_001/OW_AI_Project/ow-ai-backend
uvicorn main:app --reload --port 8000
```

### **Error: "HTTP 401 Unauthorized"**

**Cause**: Token expired or invalid

**Fix**: The simulator handles token refresh automatically. If this persists, check:
1. User exists in database
2. User has admin role
3. Password is correct

### **Error: "HTTP 500 Internal Server Error"**

**Cause**: Backend issue

**Fix**:
1. Check CloudWatch logs (production)
2. Check console output (local)
3. Verify database connection
4. Check recent deployments

---

## 📈 Advanced Usage

### **Run Multiple Times**

Simulate sustained load:

```bash
# Run 5 burst simulations with pauses
for i in {1..5}; do
  echo "Run $i/5..."
  python3 enterprise_production_simulator.py \
    --url https://pilot.owkai.app \
    --mode burst
  echo "Waiting 30 seconds..."
  sleep 30
done
```

### **Capture Output to File**

```bash
python3 enterprise_production_simulator.py \
  --url https://pilot.owkai.app \
  --mode continuous \
  --duration 300 \
  2>&1 | tee simulation_$(date +%Y%m%d_%H%M%S).log
```

### **Test Specific Scenarios**

Edit the script to focus on specific action types:

1. Comment out sections you don't want to test
2. Duplicate sections for more of a specific type
3. Modify risk levels, action types, or metadata

---

## 🎯 Success Criteria

The simulation is successful if:

- [x] **100% authentication success**
- [x] **>95% action creation success** (a few failures are OK)
- [x] **All actions appear in dashboard** within 30 seconds
- [x] **Risk scores are calculated** correctly
- [x] **Policies are evaluated** for each action
- [x] **Audit logs are created** for all actions
- [x] **No server errors** (HTTP 500)

---

## 📞 Support

**If Issues Occur**:

1. Check backend health:
   ```bash
   curl https://pilot.owkai.app/ -v
   ```

2. Check CloudWatch logs:
   ```bash
   aws logs tail /ecs/owkai-pilot-backend --since 5m
   ```

3. Verify database connection:
   ```bash
   # Check ECS task health
   aws ecs describe-services --cluster owkai-pilot --services owkai-pilot-backend-service
   ```

4. Review simulator output:
   - Look for specific error messages
   - Check failed action details
   - Verify authentication succeeded

---

## 🏆 Expected Results

**Burst Mode** (20 actions):
- **~15 seconds** execution time
- **20 actions created** (10 agent + 10 MCP)
- Mix of risk levels and statuses
- Quick verification test

**Continuous Mode** (60 seconds):
- **~12-15 actions** created
- Steady, realistic pacing
- Stats printed every 10 seconds
- Good for observing system behavior

**Realistic Mode** (5 minutes):
- **~40-60 actions** created
- Simulates workday activity patterns
- Variable pacing throughout
- Best for load testing

---

## 📝 Next Steps After Simulation

1. **Review Dashboard**:
   - Check that all actions appear
   - Verify risk scores are realistic
   - Confirm policies are applied

2. **Test Manual Approval**:
   - Find high-risk actions
   - Approve or deny manually
   - Verify state changes

3. **Check Analytics**:
   - View metrics dashboard
   - Export reports
   - Analyze risk distribution

4. **Test Playbooks**:
   - Verify auto-approval playbooks triggered
   - Check escalation playbooks for high-risk actions
   - Review playbook execution logs

---

**Ready to test your enterprise platform!** 🚀

Run the command above and watch your system handle realistic enterprise workloads.
