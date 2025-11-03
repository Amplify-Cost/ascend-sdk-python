"""
Enterprise Documentation - Part 3
Admin Guide, Security & Compliance, Developer Integration
"""
from pathlib import Path
from datetime import datetime

DOCS = {}

# 1. ADMINISTRATOR GUIDE
DOCS['admin_guide'] = """# OW-AI Administrator Guide

**Last Updated:** """ + datetime.now().strftime('%B %d, %Y') + """

## Administrator Responsibilities

As an OW-AI Administrator, you are responsible for:

✅ Platform configuration and maintenance
✅ User and role management
✅ Smart rules creation and optimization
✅ Workflow configuration
✅ Compliance monitoring
✅ Performance tuning
✅ Integration management
✅ Security administration
✅ Audit and reporting

## Initial Platform Setup

### 1. Organization Configuration

#### Access Settings Page
```
Dashboard → Settings → Organization
```

**Configure:**
```yaml
Organization Settings:
  name: "Your Company Name"
  industry: "Financial Services"  # or Healthcare, E-commerce, etc.
  size: "1000-5000 employees"
  
  compliance_requirements:
    - SOC 2 Type II
    - PCI DSS
    - GDPR
    - HIPAA
    
  business_hours:
    timezone: "America/New_York"
    start_time: "08:00"
    end_time: "18:00"
    working_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
  alert_settings:
    critical_alerts: "immediate"
    high_alerts: "within_15min"
    medium_alerts: "within_1hr"
    low_alerts: "daily_digest"
```

### 2. User Management

#### Creating Users
```
Dashboard → Admin → Users → Add User
```

**User Types:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Admin** | Full access, configuration, user management | IT administrators, security leads |
| **Approver** | Review and approve actions, view analytics | Managers, security team |
| **Viewer** | Read-only access to dashboard and reports | Compliance team, executives |
| **Agent** | API access only, cannot login to dashboard | Service accounts, integrations |

**Bulk User Import:**
```bash
# CSV format: email,role,department,manager_email
owai users import --file users.csv

# Example users.csv:
# email,role,department,manager_email
# john.doe@company.com,approver,engineering,cto@company.com
# jane.smith@company.com,viewer,compliance,cco@company.com
# security-team@company.com,admin,security,ciso@company.com
```

**User Provisioning via API:**
```python
from owai import AdminClient

admin = AdminClient(api_key="sk_admin_...")

# Create user
user = admin.users.create(
    email="newuser@company.com",
    role="approver",
    department="Customer Support",
    manager="manager@company.com",
    metadata={
        "employee_id": "EMP-12345",
        "location": "New York",
        "cost_center": "CS-001"
    }
)

# Assign to approval workflows
admin.workflows.add_approver(
    workflow_id="wf_high_risk",
    user_email="newuser@company.com",
    stage=1
)
```

#### Access Control Matrix
```
┌─────────────────────────────────────────────────────────────────────┐
│                    PERMISSION MATRIX                                 │
├──────────────────┬───────┬──────────┬─────────┬────────────────────┤
│ Action           │ Admin │ Approver │ Viewer  │ Agent              │
├──────────────────┼───────┼──────────┼─────────┼────────────────────┤
│ View Dashboard   │   ✅  │    ✅    │   ✅    │   ❌               │
│ View Actions     │   ✅  │    ✅    │   ✅    │   ❌               │
│ Approve Actions  │   ✅  │    ✅    │   ❌    │   ❌               │
│ Create Rules     │   ✅  │    ❌    │   ❌    │   ❌               │
│ Edit Rules       │   ✅  │    ❌    │   ❌    │   ❌               │
│ Manage Users     │   ✅  │    ❌    │   ❌    │   ❌               │
│ Configure System │   ✅  │    ❌    │   ❌    │   ❌               │
│ API Access       │   ✅  │    ✅    │   ❌    │   ✅               │
│ Export Data      │   ✅  │    ✅    │   ✅    │   ❌               │
│ Audit Logs       │   ✅  │    ✅    │   ✅    │   ❌               │
└──────────────────┴───────┴──────────┴─────────┴────────────────────┘
```

### 3. Smart Rules Configuration

#### Rule Design Principles

**Good Rules:**
- ✅ **Specific**: Target exact behavior
- ✅ **Testable**: Can verify in shadow mode
- ✅ **Maintainable**: Easy to understand and update
- ✅ **Performant**: Evaluate quickly
- ✅ **Documented**: Clear purpose and justification

**Poor Rules:**
- ❌ Too broad (catches everything)
- ❌ Too narrow (never triggers)
- ❌ Complex conditions (hard to debug)
- ❌ Overlapping priorities (conflicts)
- ❌ No business justification

#### Rule Templates by Industry

**Financial Services:**
```sql
-- Rule: High-Value Transaction Review
IF action_type == 'financial_transaction'
   AND amount > 10000
THEN require_approval
PRIORITY 10

-- Rule: Wire Transfer Dual Control
IF action_type == 'wire_transfer'
   AND destination_country NOT IN ('US', 'CA', 'UK', 'EU')
THEN require_two_approvals
PRIORITY 10

-- Rule: After-Hours Trading Alert
IF action_type == 'trade_execution'
   AND (EXTRACT(HOUR FROM NOW()) < 9 OR EXTRACT(HOUR FROM NOW()) > 16)
THEN notify_and_approve
PRIORITY 8

-- Rule: Suspicious Pattern Detection
IF action_type == 'account_modification'
   AND daily_action_count > AVERAGE(daily_action_count) * 5
THEN block_and_investigate
PRIORITY 10
```

**Healthcare:**
```sql
-- Rule: HIPAA Minimum Necessary
IF accessing_patient_records
   AND NOT assigned_to_patient
   AND NOT emergency_override
THEN require_justification
PRIORITY 10

-- Rule: Bulk PHI Access Prevention
IF action_type == 'data_access'
   AND record_type == 'phi'
   AND records_count > 50
THEN block_and_alert
PRIORITY 10

-- Rule: After-Hours PHI Access
IF accessing_phi_data
   AND EXTRACT(HOUR FROM NOW()) NOT BETWEEN 6 AND 22
   AND NOT on_call_list
THEN require_approval_and_log
PRIORITY 9

-- Rule: Cross-Department Access
IF accessing_patient_records
   AND patient_department != user_department
THEN require_justification
PRIORITY 7
```

**E-Commerce:**
```sql
-- Rule: Customer PII Export Control
IF action_type == 'data_export'
   AND contains_pii
   AND destination_external
THEN require_legal_approval
PRIORITY 10

-- Rule: Pricing Override Limits
IF action_type == 'price_override'
   AND discount_percent > 30
THEN require_manager_approval
PRIORITY 8

-- Rule: Bulk Order Cancellation
IF action_type == 'order_cancellation'
   AND order_count > 100
THEN require_approval_and_notify
PRIORITY 9

-- Rule: Customer Data Deletion (GDPR)
IF action_type == 'data_deletion'
   AND deletion_reason == 'gdpr_request'
THEN require_legal_review
PRIORITY 10
```

#### Rule Testing & Validation

**Shadow Mode Testing:**
```bash
# Enable shadow mode for new rule
owai rules create \
  --name "Test: High Risk Data Access" \
  --condition "action_type == 'data_access' AND risk_score > 80" \
  --action require_approval \
  --shadow-mode true \
  --duration 7d

# After 7 days, review results
owai rules test-results --rule-id rule_12345

# Output:
# ┌─────────────────────────────────────────────┐
# │ Shadow Mode Test Results (7 days)           │
# ├─────────────────────────────────────────────┤
# │ Total Actions Evaluated: 1,247              │
# │ Would Trigger: 34 (2.7%)                    │
# │ False Positives: 2 (5.9%)                   │
# │ False Negatives: 0 (0%)                     │
# │ Average Evaluation Time: 12ms               │
# │                                              │
# │ Recommendation: ✅ ENABLE                   │
# │ Confidence: 94%                             │
# └─────────────────────────────────────────────┘
```

**A/B Testing Rules:**
```python
# Test two versions of a rule
admin.rules.ab_test(
    variant_a={
        "name": "Version A: Strict",
        "condition": "risk_score > 70",
        "action": "require_approval"
    },
    variant_b={
        "name": "Version B: Moderate",
        "condition": "risk_score > 80",
        "action": "require_approval"
    },
    traffic_split=50,  # 50/50 split
    duration_days=14
)

# After 14 days
results = admin.rules.ab_test_results(test_id="test_123")
print(f"Winner: {results.winner}")
print(f"Improvement: {results.improvement_percent}%")
```

### 4. Workflow Configuration

#### Multi-Stage Approval Workflow
```python
# Create high-risk approval workflow
workflow = admin.workflows.create(
    name="High-Risk Action Approval",
    trigger_conditions={
        "risk_score_min": 80,
        "action_types": [
            "database_write",
            "system_modification",
            "financial_transaction"
        ]
    },
    stages=[
        {
            "stage": 1,
            "name": "Technical Review",
            "approvers": [
                "tech-lead@company.com",
                "senior-engineer@company.com"
            ],
            "approval_required": 1,  # Any 1 approver
            "sla_minutes": 30,
            "auto_escalate": True
        },
        {
            "stage": 2,
            "name": "Security Review",
            "approvers": ["security-team@company.com"],
            "approval_required": 1,
            "sla_minutes": 60,
            "required_only_if": "risk_score > 90"  # Conditional stage
        },
        {
            "stage": 3,
            "name": "Executive Approval",
            "approvers": [
                "cto@company.com",
                "ciso@company.com"
            ],
            "approval_required": 1,
            "sla_minutes": 120,
            "required_only_if": "business_impact == 'critical'"
        }
    ],
    escalation_policy={
        "on_timeout": "escalate_to_next_stage",
        "on_denial": "notify_requester",
        "on_approval": "execute_immediately"
    },
    notifications={
        "slack_channel": "#approvals",
        "email_template": "high_risk_approval",
        "sms_on_timeout": True
    }
)
```

#### Workflow Metrics Dashboard
```
Dashboard → Admin → Workflows → Metrics

┌──────────────────────────────────────────────────────────┐
│ WORKFLOW PERFORMANCE (Last 30 Days)                      │
├──────────────────────────────────────────────────────────┤
│ Workflow: High-Risk Action Approval                      │
│                                                           │
│ Total Executions: 342                                    │
│ Completed: 318 (93%)                                     │
│ In Progress: 24 (7%)                                     │
│ Timed Out: 0 (0%)                                        │
│                                                           │
│ Stage Performance:                                        │
│ ├─ Stage 1 (Technical): Avg 12 min (SLA: 30 min) ✅     │
│ ├─ Stage 2 (Security): Avg 25 min (SLA: 60 min) ✅      │
│ └─ Stage 3 (Executive): Avg 45 min (SLA: 120 min) ✅    │
│                                                           │
│ Outcomes:                                                 │
│ ├─ Approved: 302 (88%)                                   │
│ ├─ Denied: 16 (5%)                                       │
│ └─ In Progress: 24 (7%)                                  │
│                                                           │
│ Bottlenecks: None identified ✅                          │
│ SLA Compliance: 100% ✅                                  │
└──────────────────────────────────────────────────────────┘
```

### 5. Integration Management

#### Supported Integrations

**Authentication:**
- ✅ Okta SSO
- ✅ Azure AD / Entra ID
- ✅ Google Workspace
- ✅ SAML 2.0 (Generic)
- 🔄 Coming: Auth0, OneLogin

**Notification Channels:**
- ✅ Slack
- ✅ Microsoft Teams
- ✅ Email (SMTP/SendGrid)
- ✅ PagerDuty
- ✅ Webhooks
- 🔄 Coming: Discord, ServiceNow

**SIEM / Logging:**
- ✅ Splunk
- ✅ DataDog
- ✅ CloudWatch
- ✅ Elasticsearch
- 🔄 Coming: Sumo Logic, New Relic

**Ticketing:**
- ✅ Jira
- ✅ ServiceNow
- ✅ Linear
- 🔄 Coming: GitHub Issues, Asana

#### Slack Integration Setup
```bash
# Step 1: Add Slack App
Dashboard → Integrations → Slack → Add to Slack

# Step 2: Configure Channels
owai integrations slack configure \
  --channel-critical "#security-alerts" \
  --channel-high "#security-team" \
  --channel-approvals "#approvals" \
  --channel-general "#owai-feed"

# Step 3: Test
owai integrations slack test

# Slack will receive:
# 🔔 OW-AI Test Message
# Integration configured successfully!
# Critical alerts → #security-alerts
# High priority → #security-team
# Approvals → #approvals
# General feed → #owai-feed
```

**Slack Approval Commands:**
```
# In Slack, users can:
/owai approve <action_id> [comments]
/owai deny <action_id> [reason]
/owai status <action_id>
/owai pending
```

#### Splunk Integration
```python
# Configure Splunk forwarding
admin.integrations.splunk.configure(
    host="splunk.company.com",
    port=8088,
    token="splunk-hec-token-here",
    index="owai",
    sourcetype="owai:action",
    
    # What to forward
    events=[
        "action.created",
        "action.approved",
        "action.denied",
        "action.executed",
        "alert.created",
        "alert.acknowledged",
        "workflow.started",
        "workflow.completed",
        "rule.triggered"
    ]
)

# Splunk receives:
# {
#   "timestamp": "2025-10-23T14:32:15Z",
#   "event_type": "action.created",
#   "action_id": 1247,
#   "action_type": "database_write",
#   "risk_score": 85,
#   "agent": "support-agent-v2",
#   "user": "sarah@company.com",
#   ...
# }
```

### 6. Performance Monitoring

#### System Health Dashboard
```
Dashboard → Admin → System Health

┌─────────────────────────────────────────────────────────────┐
│ SYSTEM HEALTH (Real-Time)                                   │
├─────────────────────────────────────────────────────────────┤
│ API Status: ✅ Operational                                  │
│ Database: ✅ Connected (12ms latency)                       │
│ Alert System: ✅ Active                                     │
│ Workflow Engine: ✅ Processing                              │
│                                                              │
│ Current Load:                                                │
│ ├─ Actions/sec: 12.4 (normal)                              │
│ ├─ API Requests/min: 2,847                                  │
│ ├─ Active Users: 47                                         │
│ └─ Queue Depth: 3 pending approvals                        │
│                                                              │
│ Resource Usage:                                              │
│ ├─ CPU: 34% (█████████░░░░░░░░)                           │
│ ├─ Memory: 52% (█████████████░░░░)                         │
│ ├─ Database: 28% (███████░░░░░░░░░)                       │
│ └─ Storage: 41% (██████████░░░░░░░)                        │
│                                                              │
│ Performance Metrics (24h):                                   │
│ ├─ Avg Response Time: 87ms                                  │
│ ├─ P95 Response Time: 245ms                                 │
│ ├─ Error Rate: 0.02%                                        │
│ └─ Uptime: 99.98%                                           │
└─────────────────────────────────────────────────────────────┘
```

#### Performance Tuning

**Database Optimization:**
```sql
-- Check slow queries
SELECT 
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Add indexes for common queries
CREATE INDEX idx_actions_status_created 
ON agent_actions(status, created_at);

CREATE INDEX idx_alerts_severity_status 
ON alerts(severity, status, created_at);

-- Partition large tables
CREATE TABLE agent_actions_2025_10 PARTITION OF agent_actions
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');
```

**Caching Strategy:**
```python
# Configure Redis caching
admin.system.cache.configure(
    provider="redis",
    host="redis.company.internal",
    port=6379,
    
    # What to cache
    cache_rules={
        "smart_rules": {
            "ttl": 300,  # 5 minutes
            "invalidate_on": ["rule.updated", "rule.deleted"]
        },
        "user_permissions": {
            "ttl": 600,  # 10 minutes
            "invalidate_on": ["user.updated", "role.changed"]
        },
        "action_assessments": {
            "ttl": 3600,  # 1 hour
            "cache_key": "action:{action_id}:assessment"
        }
    }
)
```

### 7. Backup & Disaster Recovery

#### Automated Backups
```yaml
Backup Configuration:
  
  database:
    frequency: "daily"
    time: "02:00 UTC"
    retention_days: 30
    location: "s3://owai-backups/production/"
    encryption: true
    
  configuration:
    frequency: "on_change"
    retention_versions: 10
    includes:
      - rules
      - workflows
      - integrations
      - user_settings
      
  audit_logs:
    frequency: "hourly"
    retention_years: 7
    compression: true
```

#### Disaster Recovery Procedures

**RTO: 1 hour | RPO: 5 minutes**
```
DISASTER RECOVERY PLAYBOOK

1. Incident Detection (0-5 min)
   ├─ Monitoring alerts trigger
   ├─ On-call engineer paged
   └─ Incident response initiated

2. Assessment (5-15 min)
   ├─ Determine impact scope
   ├─ Check database integrity
   ├─ Verify backup availability
   └─ Notify stakeholders

3. Recovery Execution (15-45 min)
   ├─ Spin up new infrastructure
   ├─ Restore from latest backup
   ├─ Apply transaction logs
   ├─ Verify data integrity
   └─ Run smoke tests

4. Validation (45-55 min)
   ├─ API health checks
   ├─ User login tests
   ├─ Critical workflow tests
   ├─ Integration tests
   └─ Performance validation

5. Production Cutover (55-60 min)
   ├─ Update DNS/load balancers
   ├─ Monitor traffic switch
   ├─ Verify no errors
   └─ Declare recovery complete

6. Post-Incident (60+ min)
   ├─ Root cause analysis
   ├─ Incident report
   ├─ Process improvements
   └─ Stakeholder communication
```

### 8. Compliance Reporting

#### Automated Compliance Reports
```python
# Generate SOC 2 compliance report
report = admin.compliance.generate_report(
    framework="SOC2_TypeII",
    period_start="2025-Q4-start",
    period_end="2025-Q4-end",
    
    controls=[
        "CC6.1",  # Logical Access
        "CC6.6",  # System Operations
        "CC7.2",  # Risk Assessment
        "CC8.1"   # Change Management
    ],
    
    include_evidence=True,
    format="pdf"
)

# Report includes:
# ✅ Control objectives
# ✅ Implementation details
# ✅ Testing procedures
# ✅ Evidence (audit logs, screenshots)
# ✅ Exceptions (if any)
# ✅ Management response
```

#### Compliance Dashboard
```
Dashboard → Compliance → Overview

┌────────────────────────────────────────────────────────────┐
│ COMPLIANCE POSTURE (Current)                               │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ SOC 2 Type II: ✅ 100% Compliant                          │
│ ├─ CC6.1 Logical Access: ✅ Pass                          │
│ ├─ CC6.6 System Operations: ✅ Pass                       │
│ ├─ CC7.2 Risk Assessment: ✅ Pass                         │
│ └─ CC8.1 Change Management: ✅ Pass                       │
│                                                             │
│ GDPR: ✅ 100% Compliant                                   │
│ ├─ Article 25 (Data Protection): ✅ Implemented           │
│ ├─ Article 30 (Records): ✅ Complete                      │
│ ├─ Article 32 (Security): ✅ Enforced                     │
│ └─ Article 33 (Breach): ✅ Procedures Active              │
│                                                             │
│ HIPAA: ✅ 100% Compliant                                  │
│ ├─ §164.308 Administrative: ✅ Implemented                │
│ ├─ §164.312 Technical: ✅ Enforced                        │
│ └─ §164.316 Policies: ✅ Documented                       │
│                                                             │
│ Next Audit: December 15, 2025                              │
│ Evidence Package: Ready ✅                                 │
└────────────────────────────────────────────────────────────┘
```

### 9. Troubleshooting Guide

#### Common Issues & Solutions

**Issue: Actions Not Being Evaluated**
```
Symptoms:
- Actions appearing in log but no risk assessment
- Rules not triggering
- No alerts generated

Diagnosis:
1. Check OrchestrationService status
   Dashboard → Admin → Services → Orchestration

2. Check service logs
   owai logs service orchestration --tail 100

3. Verify database connection
   owai system check --verbose

Solution:
- Restart orchestration service if hung
- Check for database connectivity issues
- Verify smart rules are enabled
```

**Issue: Slow Approval Times**
```
Symptoms:
- Approvals taking longer than expected
- Users not receiving notifications
- Workflow timeouts

Diagnosis:
1. Check notification delivery
   owai integrations test --all

2. Check approver availability
   owai workflows bottleneck-analysis

3. Review SLA compliance
   Dashboard → Workflows → SLA Report

Solution:
- Add backup approvers
- Adjust SLA timers
- Enable auto-escalation
- Check email/Slack integration
```

**Issue: High False Positive Rate**
```
Symptoms:
- Rules triggering too frequently
- Low approval rate
- User complaints

Diagnosis:
1. Review rule analytics
   Dashboard → Smart Rules → Analytics

2. Identify problematic rules
   owai rules analyze-false-positives

3. Check rule conditions
   owai rules validate --rule-id <id>

Solution:
- Enable shadow mode to test adjustments
- Make conditions more specific
- Add exclusion criteria
- Adjust risk thresholds
```

## Best Practices

### Security

✅ **Enable MFA** for all admin accounts
✅ **Rotate API keys** quarterly
✅ **Review audit logs** weekly
✅ **Test disaster recovery** quarterly
✅ **Update integrations** as needed
✅ **Monitor performance** continuously

### Operations

✅ **Review rules monthly** for effectiveness
✅ **Update workflows** based on feedback
✅ **Train new approvers** regularly
✅ **Monitor SLA compliance** weekly
✅ **Optimize performance** quarterly
✅ **Plan capacity** proactively

### Compliance

✅ **Run compliance reports** monthly
✅ **Update evidence** continuously
✅ **Review controls** quarterly
✅ **Audit user access** monthly
✅ **Document changes** immediately
✅ **Prepare for audits** proactively

## Administrator Checklist

### Daily
- [ ] Review critical alerts
- [ ] Check system health dashboard
- [ ] Monitor approval queue depth
- [ ] Review any workflow timeouts

### Weekly
- [ ] Review rule performance metrics
- [ ] Analyze false positive trends
- [ ] Check integration health
- [ ] Review user access logs
- [ ] Update documentation

### Monthly
- [ ] Generate compliance reports
- [ ] Review and optimize rules
- [ ] Audit user permissions
- [ ] Performance tuning review
- [ ] Backup restoration test
- [ ] Team training session

### Quarterly
- [ ] Disaster recovery drill
- [ ] Capacity planning review
- [ ] Security assessment
- [ ] Integration updates
- [ ] Policy review and updates
- [ ] Executive reporting

---

## Getting Help

**Documentation**: https://docs.owkai.app
**Support Email**: support@owkai.com
**Emergency**: support@owkai.com (24/7)
**Community**: https://community.owkai.app
"""

# 2. SECURITY & COMPLIANCE DEEP DIVE
DOCS['security_compliance'] = """# Security & Compliance Deep Dive

**Last Updated:** """ + datetime.now().strftime('%B %d, %Y') + """

## Security Architecture

### Defense in Depth Strategy

OW-AI implements multiple layers of security:
```
┌────────────────────────────────────────────────────────────┐
│                   SECURITY LAYERS                           │
├────────────────────────────────────────────────────────────┤
│                                                             │
│ Layer 7: Physical Security                                 │
│ └─→ AWS data centers (SOC 1/2/3 certified)                │
│                                                             │
│ Layer 6: Network Security                                  │
│ ├─→ VPC isolation                                          │
│ ├─→ Security groups                                        │
│ ├─→ Network ACLs                                           │
│ └─→ TLS 1.3 encryption                                     │
│                                                             │
│ Layer 5: Infrastructure Security                           │
│ ├─→ ECS task isolation                                     │
│ ├─→ IAM least privilege                                    │
│ ├─→ Secrets Manager                                        │
│ └─→ CloudTrail logging                                     │
│                                                             │
│ Layer 4: Application Security                              │
│ ├─→ Input validation (Pydantic)                           │
│ ├─→ SQL injection prevention (SQLAlchemy ORM)             │
│ ├─→ XSS protection                                         │
│ └─→ CSRF protection                                        │
│                                                             │
│ Layer 3: Authentication & Authorization                    │
│ ├─→ JWT with RS256                                         │
│ ├─→ MFA support                                            │
│ ├─→ SSO integration                                        │
│ └─→ Role-Based Access Control                             │
│                                                             │
│ Layer 2: Data Security                                     │
│ ├─→ Encryption at rest (AES-256)                          │
│ ├─→ Encryption in transit (TLS 1.3)                       │
│ ├─→ Database encryption                                    │
│ └─→ PII tokenization                                       │
│                                                             │
│ Layer 1: Monitoring & Response                             │
│ ├─→ Real-time threat detection                            │
│ ├─→ Anomaly detection                                      │
│ ├─→ Automated incident response                           │
│ └─→ Security audit logs                                    │
└────────────────────────────────────────────────────────────┘
```

### Authentication Deep Dive

#### JWT Implementation

**Token Structure:**
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-2025-01"
  },
  "payload": {
    "sub": "user_abc123",
    "email": "user@company.com",
    "role": "approver",
    "permissions": ["read", "approve", "deny"],
    "iat": 1698765432,
    "exp": 1698769032,
    "iss": "owai.app",
    "aud": "owai-api"
  },
  "signature": "..."
}
```

**Token Lifecycle:**
```python
# Token generation
def create_access_token(user: User) -> str:
    """Generate JWT access token"""
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "permissions": get_user_permissions(user),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iss": "owai.app",
        "aud": "owai-api"
    }
    
    # Sign with RSA private key
    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "key-2025-01"}
    )
    
    return token

# Token validation
def validate_token(token: str) -> dict:
    """Validate and decode JWT"""
    try:
        # Decode with RSA public key
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="owai-api",
            issuer="owai.app"
        )
        
        # Additional checks
        if payload["exp"] < datetime.utcnow().timestamp():
            raise TokenExpired()
            
        if is_token_revoked(payload["sub"], token):
            raise TokenRevoked()
            
        return payload
        
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(str(e))
```

**Key Rotation:**
```python
# Automatic key rotation every 90 days
class JWTKeyManager:
    def rotate_keys(self):
        """Rotate RSA key pair"""
        # Generate new key pair
        new_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        new_public_key = new_private_key.public_key()
        
        # Store in Secrets Manager
        secrets_manager.update_secret(
            "jwt-private-key",
            new_private_key.export()
        )
        
        # Keep old public key for verification (grace period)
        self.public_keys["key-2025-01"] = old_public_key  # 30-day grace
        self.public_keys["key-2025-02"] = new_public_key  # Current
        
        # Audit log
        audit_log.record("jwt_keys_rotated", {
            "old_kid": "key-2025-01",
            "new_kid": "key-2025-02",
            "timestamp": datetime.utcnow()
        })
```

### Authorization Framework

#### RBAC Implementation
```python
class RBACManager:
    """Role-Based Access Control"""
    
    # Permission matrix
    PERMISSIONS = {
        "admin": [
            "read", "write", "delete",
            "approve", "deny",
            "configure", "manage_users",
            "audit", "export"
        ],
        "approver": [
            "read",
            "approve", "deny",
            "audit"
        ],
        "viewer": [
            "read",
            "audit"
        ],
        "agent": [
            "write"  # API only
        ]
    }
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has permission"""
        role_permissions = self.PERMISSIONS.get(user.role, [])
        return permission in role_permissions
    
    def require_permission(self, permission: str):
        """Decorator for permission checking"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = get_current_user()
                if not self.has_permission(user, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission '{permission}' required"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator

# Usage
@app.post("/admin/users")
@rbac.require_permission("manage_users")
async def create_user(user_data: UserCreate):
    """Only admins can create users"""
    return admin_service.create_user(user_data)
```

### Data Encryption

#### Encryption at Rest
```python
# Database-level encryption
# PostgreSQL with AWS RDS encryption enabled

# Application-level encryption for sensitive fields
class EncryptedField:
    """Encrypted database field"""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.kms_client = boto3.client('kms')
        self.key_id = os.getenv('KMS_KEY_ID')
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt data with AWS KMS"""
        response = self.kms_client.encrypt(
            KeyId=self.key_id,
            Plaintext=plaintext.encode('utf-8')
        )
        return base64.b64encode(response['CiphertextBlob']).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt data with AWS KMS"""
        response = self.kms_client.decrypt(
            CiphertextBlob=base64.b64decode(ciphertext)
        )
        return response['Plaintext'].decode('utf-8')

# Example: Encrypt API keys
class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    _encrypted_key = Column("api_key", String(512))
    
    @property
    def api_key(self) -> str:
        return EncryptedField("api_key").decrypt(self._encrypted_key)
    
    @api_key.setter
    def api_key(self, value: str):
        self._encrypted_key = EncryptedField("api_key").encrypt(value)
```

#### Encryption in Transit
```yaml
# TLS Configuration
tls:
  version: "1.3"  # TLS 1.3 only
  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
    - TLS_AES_128_GCM_SHA256
  
  certificates:
    provider: "AWS Certificate Manager"
    renewal: "automatic"
    domains:
      - "pilot.owkai.app"
      - "*.pilot.owkai.app"
  
  hsts:
    enabled: true
    max_age: 31536000  # 1 year
    include_subdomains: true
    preload: true
```

### Security Monitoring

#### Real-Time Threat Detection
```python
class ThreatDetector:
    """Real-time security threat detection"""
    
    def analyze_request(self, request: Request) -> ThreatAssessment:
        """Analyze request for threats"""
        assessment = ThreatAssessment()
        
        # Check for common attacks
        assessment.sql_injection = self.detect_sql_injection(request)
        assessment.xss = self.detect_xss(request)
        assessment.path_traversal = self.detect_path_traversal(request)
        assessment.rate_limit_abuse = self.check_rate_limits(request)
        assessment.credential_stuffing = self.detect_credential_stuffing(request)
        
        # Anomaly detection
        assessment.anomaly_score = self.calculate_anomaly_score(request)
        
        # Threat intelligence
        assessment.known_bad_ip = self.check_threat_intel(request.client.host)
        
        if assessment.is_threat():
            self.block_and_alert(request, assessment)
        
        return assessment
    
    def detect_sql_injection(self, request: Request) -> bool:
        """Detect SQL injection attempts"""
        patterns = [
            r"union\s+select",
            r";\s*drop\s+table",
            r"'\s*or\s+'1'\s*=\s*'1",
            r"--",
            r"/\*.*\*/"
        ]
        
        # Check all input
        for value in self.get_all_inputs(request):
            for pattern in patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return True
        return False
```

## Compliance Frameworks

### SOC 2 Type II

#### Trust Service Criteria Coverage

**CC6.1 - Logical and Physical Access Controls**
```
Implementation:
├─ Multi-factor authentication (MFA)
├─ Role-based access control (RBAC)
├─ Least privilege principle
├─ Regular access reviews
└─ Terminated user deprovisioning

Evidence:
├─ Access control policies
├─ User provisioning logs
├─ Access review reports
├─ MFA enrollment records
└─ Termination checklist

Testing:
├─ Sample 25 user accounts
├─ Verify RBAC implementation
├─ Check MFA enforcement
├─ Review access logs
└─ Test privilege escalation prevention
```

**CC6.6 - Logical and Physical Access Control - System Operations**
```
Implementation:
├─ Change management procedures
├─ Code review requirements
├─ Deployment approval process
├─ Rollback procedures
└─ Production access logging

Evidence:
├─ Change management policy
├─ Pull request records
├─ Deployment logs
├─ Approval workflows
└─ Incident reports

Testing:
├─ Sample 40 production changes
├─ Verify approval obtained
├─ Check change tickets
├─ Review deployment logs
└─ Test rollback capability
```

**CC7.2 - System Monitoring - Risk Assessment**
```
Implementation:
├─ Automated risk scoring (CVSS)
├─ Continuous monitoring
├─ Threat intelligence integration
├─ Vulnerability scanning
└─ Risk mitigation tracking

Evidence:
├─ Risk assessment methodology
├─ Risk scores for all actions
├─ Mitigation action logs
├─ Vulnerability scan reports
└─ Threat intel feeds

Testing:
├─ Sample 100 high-risk actions
├─ Verify risk scores calculated
├─ Check mitigation applied
├─ Review monitoring coverage
└─ Test alert generation
```

**CC8.1 - Change Management**
```
Implementation:
├─ Formal change approval process
├─ Testing requirements
├─ Staged rollouts
├─ Emergency change procedures
└─ Post-deployment validation

Evidence:
├─ Change management policy
├─ Change tickets
├─ Test results
├─ Approval records
└─ Post-deployment reports

Testing:
├─ Sample all changes (234 in Q4)
├─ Verify tickets exist
├─ Check approval obtained
├─ Review test evidence
└─ Confirm no unauthorized changes
```

### GDPR Compliance

#### Data Protection by Design (Article 25)
```python
class GDPRComplianceEngine:
    """GDPR compliance enforcement"""
    
    def process_personal_data(
        self,
        data: PersonalData,
        purpose: str,
        legal_basis: str
    ) -> ProcessingResult:
        """Process personal data with GDPR compliance"""
        
        # 1. Check lawful basis
        if not self.has_lawful_basis(data.subject_id, legal_basis):
            raise GDPRViolation("No lawful basis for processing")
        
        # 2. Purpose limitation
        if not self.is_purpose_legitimate(purpose):
            raise GDPRViolation("Purpose not legitimate")
        
        # 3. Data minimization
        if not self.is_data_minimal(data, purpose):
            raise GDPRViolation("Excessive data for purpose")
        
        # 4. Accuracy
        if not self.is_data_accurate(data):
            raise GDPRViolation("Data accuracy not verified")
        
        # 5. Storage limitation
        retention = self.get_retention_period(purpose)
        if data.age_days > retention:
            self.schedule_deletion(data)
        
        # 6. Integrity and confidentiality
        encrypted_data = self.encrypt(data)
        
        # 7. Accountability
        self.record_processing_activity(data, purpose, legal_basis)
        
        return ProcessingResult(
            success=True,
            compliance_check=True,
            retention_days=retention
        )
    
    def handle_data_subject_request(
        self,
        request_type: str,
        subject_id: str
    ) -> DSARResult:
        """Handle Data Subject Access Request"""
        
        if request_type == "access":  # Article 15
            return self.export_personal_data(subject_id)
        
        elif request_type == "rectification":  # Article 16
            return self.rectify_personal_data(subject_id)
        
        elif request_type == "erasure":  # Article 17 (Right to be Forgotten)
            return self.erase_personal_data(subject_id)
        
        elif request_type == "restriction":  # Article 18
            return self.restrict_processing(subject_id)
        
        elif request_type == "portability":  # Article 20
            return self.export_portable_data(subject_id)
        
        elif request_type == "objection":  # Article 21
            return self.stop_processing(subject_id)
```

#### Records of Processing Activities (Article 30)
```json
{
  "processing_activity": "Customer Support Ticket Processing",
  "controller": {
    "name": "Your Company Inc.",
    "contact": "dpo@company.com"
  },
  "purposes": [
    "Contract fulfillment",
    "Customer service"
  ],
  "legal_basis": "Contract (GDPR Article 6(1)(b))",
  "categories_of_data_subjects": [
    "Customers",
    "Prospective customers"
  ],
  "categories_of_personal_data": [
    "Contact information (name, email, phone)",
    "Account information",
    "Support history"
  ],
  "categories_of_recipients": [
    "Support staff",
    "Management (for escalations)"
  ],
  "transfers_to_third_countries": "None",
  "retention_period": "7 years after account closure",
  "security_measures": [
    "Encryption at rest (AES-256)",
    "Encryption in transit (TLS 1.3)",
    "Access controls (RBAC)",
    "Audit logging",
    "Regular security assessments"
  ],
  "last_updated": "2025-01-15"
}
```

### HIPAA Compliance

#### Administrative Safeguards (§164.308)
```
Security Management Process:
├─ Risk Analysis ✅
│  └─ Automated CVSS scoring for all PHI access
├─ Risk Management ✅
│  └─ Smart rules enforce mitigation
├─ Sanction Policy ✅
│  └─ Violations trigger automated sanctions
└─ Information System Activity Review ✅
   └─ Continuous audit log review

Workforce Security:
├─ Authorization/Supervision ✅
│  └─ Approval workflows for PHI access
├─ Workforce Clearance ✅
│  └─ Background checks before access
└─ Termination Procedures ✅
   └─ Automated access revocation

Access Management:
├─ Access Authorization ✅
│  └─ Role-based access control
├─ Access Establishment ✅
│  └─ Formal provisioning process
└─ Access Modification ✅
   └─ Change management workflow
```

#### Technical Safeguards (§164.312)
```python
class HIPAAComplianceEngine:
    """HIPAA technical safeguards"""
    
    def enforce_access_controls(self, user: User, phi: PHI) -> bool:
        """§164.312(a)(1) - Access Control"""
        
        # Unique User Identification
        if not user.is_authenticated():
            raise AccessDenied("Authentication required")
        
        # Emergency Access Procedure
        if phi.is_emergency_access_needed():
            if user.has_emergency_override():
                self.log_emergency_access(user, phi)
                return True
        
        # Automatic Logoff
        if user.session_inactive_minutes() > 15:
            self.force_logout(user)
            raise SessionExpired()
        
        # Encryption and Decryption
        if not phi.is_encrypted():
            raise SecurityViolation("PHI must be encrypted")
        
        return True
    
    def audit_controls(self, event: AccessEvent):
        """§164.312(b) - Audit Controls"""
        
        # Record all PHI access
        audit_log = {
            "timestamp": datetime.utcnow(),
            "user_id": event.user.id,
            "user_email": event.user.email,
            "action": event.action,
            "phi_record_id": event.phi.id,
            "patient_id": event.phi.patient_id,
            "purpose": event.purpose,
            "ip_address": event.ip_address,
            "success": event.success
        }
        
        # Immutable storage
        self.write_to_audit_trail(audit_log)
        
        # 6-year retention
        self.set_retention_policy(audit_log, years=6)
    
    def integrity_controls(self, phi: PHI):
        """§164.312(c)(1) - Integrity"""
        
        # Mechanism to authenticate PHI
        checksum = self.calculate_checksum(phi)
        if checksum != phi.stored_checksum:
            raise IntegrityViolation("PHI has been modified")
        
        # Detect unauthorized changes
        if phi.last_modified_by not in phi.authorized_users:
            self.alert_security_team("Unauthorized PHI modification")
    
    def transmission_security(self, phi: PHI, destination: str):
        """§164.312(e)(1) - Transmission Security"""
        
        # Integrity controls
        phi.add_hmac_signature()
        
        # Encryption
        encrypted_phi = self.encrypt_phi(phi, algorithm="AES-256-GCM")
        
        # Transmit over TLS 1.3
        self.transmit_over_tls(encrypted_phi, destination)
        
        # Log transmission
        self.log_phi_transmission(phi, destination)
```

### PCI DSS (Payment Card Industry)

For organizations handling payment data:
```
Requirement 3: Protect Stored Cardholder Data
├─ Never store sensitive authentication data
├─ Encrypt cardholder data (AES-256)
├─ Mask PAN when displayed
└─ Cryptographic key management

Requirement 7: Restrict Access by Business Need
├─ Limit access to card data
├─ Assign unique IDs
├─ Implement least privilege
└─ Document access requirements

Requirement 8: Identify and Authenticate Access
├─ Assign unique ID to each user
├─ Require strong passwords
├─ Implement MFA
└─ Lock account after failed attempts

Requirement 10: Track and Monitor Access
├─ Link all access to individual users
├─ Log all actions on cardholder data
├─ Review logs daily
└─ Retain audit trail for 1 year
```

## Security Best Practices

### Secure Development Lifecycle
```
1. Requirements Phase
   ├─ Security requirements gathered
   ├─ Threat modeling completed
   └─ Compliance needs identified

2. Design Phase
   ├─ Security architecture review
   ├─ Data flow diagrams
   └─ Authentication/authorization design

3. Implementation Phase
   ├─ Secure coding standards
   ├─ Input validation
   ├─ Code review (2+ reviewers)
   └─ Static analysis (SAST)

4. Testing Phase
   ├─ Security testing (DAST)
   ├─ Penetration testing
   ├─ Vulnerability scanning
   └─ Compliance validation

5. Deployment Phase
   ├─ Security configuration review
   ├─ Deployment checklist
   └─ Post-deployment validation

6. Operations Phase
   ├─ Continuous monitoring
   ├─ Incident response
   ├─ Patch management
   └─ Security reviews
```

### Incident Response Procedures
```
INCIDENT RESPONSE PLAYBOOK

Phase 1: Detection (0-15 min)
├─ Automated alert triggers
├─ Security team notified
├─ Initial assessment
└─ Severity classification

Phase 2: Containment (15-60 min)
├─ Isolate affected systems
├─ Preserve evidence
├─ Prevent further damage
└─ Implement temporary controls

Phase 3: Eradication (1-4 hours)
├─ Remove threat actor access
├─ Patch vulnerabilities
├─ Remove malware
└─ Restore from clean backup

Phase 4: Recovery (4-24 hours)
├─ Restore systems to production
├─ Monitor for re-infection
├─ Validate functionality
└─ Gradual traffic restoration

Phase 5: Post-Incident (24+ hours)
├─ Root cause analysis
├─ Incident report
├─ Lessons learned
├─ Update procedures
└─ Stakeholder communication
```

## Audit Preparation

### Evidence Collection
```bash
# Automated evidence collection
owai audit generate-evidence-package \
  --framework SOC2 \
  --period Q4-2025 \
  --output /tmp/soc2-evidence/

# Package includes:
# ├─ access_logs/
# │  ├─ user_access_log.csv
# │  ├─ privileged_access_log.csv
# │  └─ failed_login_attempts.csv
# ├─ change_management/
# │  ├─ production_changes.csv
# │  ├─ approval_records.pdf
# │  └─ test_results/
# ├─ risk_assessment/
# │  ├─ risk_scores.csv
# │  ├─ high_risk_actions.pdf
# │  └─ mitigation_actions.csv
# ├─ compliance_controls/
# │  ├─ control_testing.pdf
# │  ├─ exceptions.csv
# │  └─ remediation_plans.pdf
# └─ policies/
#    ├─ information_security_policy.pdf
#    ├─ access_control_policy.pdf
#    └─ incident_response_plan.pdf
```

### Auditor Support
```
Audit Support Process:

1. Pre-Audit (2 weeks before)
   ├─ Generate evidence package
   ├─ Review for completeness
   ├─ Prepare narratives
   └─ Schedule kickoff meeting

2. Fieldwork (During audit)
   ├─ Provide requested evidence
   ├─ Answer auditor questions
   ├─ Demonstrate controls
   └─ Facilitate system walkthroughs

3. Follow-up
   ├─ Respond to additional requests
   ├─ Clarify findings
   ├─ Provide supplemental evidence
   └─ Discuss remediation plans

4. Post-Audit
   ├─ Review draft report
   ├─ Provide management response
   ├─ Implement recommendations
   └─ Plan follow-up audit
```

---

## Security Contacts

**Security Team**: security@owkai.com
**Vulnerability Reports**: security@owkai.com
**Compliance Questions**: compliance@owkai.com
**Emergency (24/7)**: security@owkai.com

**Bug Bounty Program**: https://bugcrowd.com/owkai
**Security Updates**: https://status.owkai.app
"""

# Write Part 3 docs
print("🏢 Generating Part 3 Documentation...")
print()

docs_dir = Path('../enterprise-docs')
docs_dir.mkdir(exist_ok=True)

for doc_name, content in DOCS.items():
    # Write markdown
    md_path = docs_dir / f"{doc_name}.md"
    with open(md_path, 'w') as f:
        f.write(content)
    print(f"✅ Created: {md_path}")

print()
print("📝 Converting to HTML...")

# HTML converter (same template as before)
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - OW-AI Enterprise Documentation</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .nav {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            padding: 25px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .nav-logo {{
            font-size: 24px;
            font-weight: bold;
            color: white;
        }}
        .nav-links {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .nav a {{
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 6px;
            transition: all 0.3s;
            font-weight: 500;
            font-size: 14px;
        }}
        .nav a:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }}
        .content {{
            padding: 60px;
        }}
        h1 {{
            color: #2c3e50;
            font-size: 48px;
            margin-bottom: 20px;
            border-bottom: 4px solid #667eea;
            padding-bottom: 20px;
        }}
        h2 {{
            color: #34495e;
            font-size: 36px;
            margin: 50px 0 25px 0;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
        }}
        h3 {{
            color: #7f8c8d;
            font-size: 28px;
            margin: 35px 0 20px 0;
        }}
        h4 {{
            color: #95a5a6;
            font-size: 22px;
            margin: 25px 0 15px 0;
        }}
        p {{
            margin: 15px 0;
            font-size: 17px;
            line-height: 1.8;
        }}
        code {{
            background: #f8f9fa;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 14px;
            color: #e74c3c;
        }}
        pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 25px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 25px 0;
            font-size: 14px;
            line-height: 1.6;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.3);
        }}
        pre code {{
            background: none;
            color: #ecf0f1;
            padding: 0;
        }}
        ul, ol {{
            margin: 20px 0 20px 40px;
        }}
        li {{
            margin: 10px 0;
            font-size: 17px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border: 1px solid #e0e0e0;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 40px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <div class="nav-logo">🛡️ OW-AI</div>
            <div class="nav-links">
                <a href="product_overview.html">Overview</a>
                <a href="architecture.html">Architecture</a>
                <a href="api.html">API</a>
                <a href="user_guide.html">User Guide</a>
                <a href="admin_guide.html">Admin Guide</a>
                <a href="security_compliance.html">Security</a>
            </div>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>© 2025 OW-AI Enterprise Platform | Documentation Version 2.0</p>
            <p style="margin-top: 10px;">🔒 SOC 2 Type II Certified | GDPR Compliant | HIPAA Ready</p>
        </div>
    </div>
</body>
</html>
"""

import markdown

for md_file in docs_dir.glob('*.md'):
    with open(md_file, 'r') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    html_file = md_file.with_suffix('.html')
    with open(html_file, 'w') as f:
        title = md_file.stem.replace('_', ' ').title()
        f.write(html_template.format(title=title, content=html_content))
    
    print(f"✅ Converted: {html_file.name}")

print()
print("✅ Part 3 documentation complete!")
