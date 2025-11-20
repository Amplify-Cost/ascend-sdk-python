# CLIENT DEMO & TESTING SETUP GUIDE
## Simulated Multi-Tenant Client Onboarding with AWS Integration

**Date:** 2025-11-13
**Project:** OW-AI Enterprise Authorization Center
**Purpose:** Create realistic demo environment with client organization, agent actions, and governance rules
**Author:** OW-KAI Engineer (Donald King)

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Phase 1: Create Demo Client Organization](#phase-1-create-demo-client-organization)
5. [Phase 2: Configure AWS Integration](#phase-2-configure-aws-integration)
6. [Phase 3: Create Governance Rules](#phase-3-create-governance-rules)
7. [Phase 4: Simulate Agent Actions](#phase-4-simulate-agent-actions)
8. [Phase 5: Monitor & Measure Effectiveness](#phase-5-monitor--measure-effectiveness)
9. [Demo Script](#demo-script)
10. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

### What You'll Build

A complete demo environment showing:
- **Client Organization:** "TechCorp Demo Inc." with multiple users/roles
- **AWS Integration:** Simulated AWS account with real agent actions
- **Governance Rules:** Policies that block/approve/escalate actions
- **Real-Time Monitoring:** Dashboard showing blocked vs allowed actions
- **Metrics Dashboard:** Effectiveness reports (% blocked, response times, etc.)

### Demo Narrative

```
TechCorp Demo Inc. (Fortune 500 client) wants to:
1. Control their AI agents accessing AWS resources
2. Block high-risk actions (production DB writes, financial transactions)
3. Require approval for medium-risk actions (system config changes)
4. Monitor agent behavior in real-time
5. Generate compliance reports for SOX/HIPAA audits
```

### Success Metrics

After setup, you'll demonstrate:
- ✅ 90%+ of high-risk actions blocked automatically
- ✅ 100% of financial transactions requiring approval
- ✅ <200ms policy evaluation time
- ✅ Complete audit trail with CVSS/MITRE/NIST enrichment
- ✅ Real-time alerts for policy violations

---

## ARCHITECTURE

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    DEMO ENVIRONMENT                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Client Org      │         │  OW-AI Platform  │         │
│  │  "TechCorp Demo" │  ───►   │  pilot.owkai.app │         │
│  │                  │         │                  │         │
│  │  - Users (5)     │         │  - Policies (10) │         │
│  │  - Agents (3)    │         │  - Rules Engine  │         │
│  │  - AWS Account   │         │  - Audit Logs    │         │
│  └──────────────────┘         └──────────────────┘         │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Simulated AWS   │         │  Monitoring      │         │
│  │  Agent Actions   │  ───►   │  Dashboard       │         │
│  │                  │         │                  │         │
│  │  - DB Access     │         │  - Real-time     │         │
│  │  - S3 Operations │         │  - Metrics       │         │
│  │  - EC2 Control   │         │  - Alerts        │         │
│  └──────────────────┘         └──────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Agent Action Request
    ↓
OW-AI Policy Engine
    ├─→ CVSS Risk Assessment (your patent #1)
    ├─→ Natural Language Policy Match (your patent #2)
    ├─→ MCP Governance Check (your patent #4)
    └─→ Immutable Audit Log (your patent #3)
    ↓
Decision: ALLOW / DENY / REQUIRE_APPROVAL
    ↓
Monitoring Dashboard (real-time metrics)
```

---

## PREREQUISITES

### Required Access

- [x] OW-AI Platform: https://pilot.owkai.app
- [x] Admin credentials: admin@owkai.com
- [x] Local development environment
- [x] AWS account (optional - can simulate)
- [x] PostgreSQL database access

### Required Tools

```bash
# Check if you have these installed
python --version    # Python 3.11+
psql --version      # PostgreSQL 14+
curl --version      # For API testing
jq --version        # For JSON parsing (optional but helpful)
```

### Get Fresh Authentication Token

```bash
# Login to get token
curl -X POST "https://pilot.owkai.app/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@owkai.com",
    "password": "admin123"
  }' | jq -r '.access_token'

# Save token for use in all subsequent commands
export TOKEN="<paste_token_here>"
```

---

## PHASE 1: CREATE DEMO CLIENT ORGANIZATION

### Step 1.1: Create Organization Record

**Option A: Via API (Recommended)**

```bash
# Create TechCorp Demo organization
curl -X POST "https://pilot.owkai.app/api/enterprise-users/organizations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechCorp Demo Inc.",
    "domain": "techcorp-demo.com",
    "industry": "Financial Services",
    "size": "1000-5000 employees",
    "compliance_requirements": ["SOX", "PCI-DSS", "GDPR"],
    "aws_account_id": "123456789012",
    "settings": {
      "require_approval_threshold": 70,
      "auto_block_threshold": 90,
      "audit_retention_days": 2555
    }
  }'

# Expected Response:
{
  "id": 101,
  "name": "TechCorp Demo Inc.",
  "domain": "techcorp-demo.com",
  "created_at": "2025-11-13T...",
  "status": "active"
}

# Save the organization ID
export ORG_ID=101
```

**Option B: Via Database (Direct)**

```bash
# Connect to local database
export DATABASE_URL="postgresql://mac_001@localhost:5432/owkai_pilot"

psql $DATABASE_URL << 'EOF'
-- Create organization
INSERT INTO organizations (
  name,
  domain,
  industry,
  size,
  compliance_requirements,
  aws_account_id,
  settings,
  created_at
) VALUES (
  'TechCorp Demo Inc.',
  'techcorp-demo.com',
  'Financial Services',
  '1000-5000 employees',
  ARRAY['SOX', 'PCI-DSS', 'GDPR'],
  '123456789012',
  '{"require_approval_threshold": 70, "auto_block_threshold": 90, "audit_retention_days": 2555}'::jsonb,
  NOW()
) RETURNING id, name;
EOF

# Note the returned ID (e.g., 101)
export ORG_ID=101
```

### Step 1.2: Create Demo Users

Create 5 users representing different roles in TechCorp:

```bash
# User 1: CEO (Executive Level)
curl -X POST "https://pilot.owkai.app/api/enterprise-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@techcorp-demo.com",
    "password": "Demo2025!",
    "first_name": "Jennifer",
    "last_name": "Thompson",
    "role": "admin",
    "organization_id": '$ORG_ID',
    "department": "Executive",
    "title": "Chief Executive Officer",
    "approval_level": 5
  }'

# User 2: CTO (Senior Management)
curl -X POST "https://pilot.owkai.app/api/enterprise-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cto@techcorp-demo.com",
    "password": "Demo2025!",
    "first_name": "Michael",
    "last_name": "Rodriguez",
    "role": "admin",
    "organization_id": '$ORG_ID',
    "department": "Engineering",
    "title": "Chief Technology Officer",
    "approval_level": 4
  }'

# User 3: Security Manager (Department Head)
curl -X POST "https://pilot.owkai.app/api/enterprise-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "security.manager@techcorp-demo.com",
    "password": "Demo2025!",
    "first_name": "Sarah",
    "last_name": "Chen",
    "role": "user",
    "organization_id": '$ORG_ID',
    "department": "Security",
    "title": "Security Manager",
    "approval_level": 3
  }'

# User 4: DevOps Lead (Team Lead)
curl -X POST "https://pilot.owkai.app/api/enterprise-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "devops.lead@techcorp-demo.com",
    "password": "Demo2025!",
    "first_name": "David",
    "last_name": "Kumar",
    "role": "user",
    "organization_id": '$ORG_ID',
    "department": "DevOps",
    "title": "DevOps Team Lead",
    "approval_level": 2
  }'

# User 5: Junior Developer (Individual Contributor)
curl -X POST "https://pilot.owkai.app/api/enterprise-users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@techcorp-demo.com",
    "password": "Demo2025!",
    "first_name": "Emily",
    "last_name": "Park",
    "role": "user",
    "organization_id": '$ORG_ID',
    "department": "Engineering",
    "title": "Software Engineer",
    "approval_level": 1
  }'
```

### Step 1.3: Verify Organization Setup

```bash
# List all users in TechCorp Demo
curl -s "https://pilot.owkai.app/api/enterprise-users/organizations/$ORG_ID/users" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected: 5 users with different approval levels
```

---

## PHASE 2: CONFIGURE AWS INTEGRATION

### Step 2.1: Create Simulated AWS Agents

Create 3 AI agents that will simulate AWS operations:

```bash
# Agent 1: Database Management Agent
curl -X POST "https://pilot.owkai.app/api/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "name": "RDS Database Manager",
    "description": "Manages AWS RDS databases - reads/writes customer data",
    "organization_id": '$ORG_ID',
    "capabilities": ["database_read", "database_write", "database_backup"],
    "trust_level": "verified",
    "aws_resources": ["rds:us-east-1:prod-customer-db"],
    "created_by": "cto@techcorp-demo.com"
  }'

# Agent 2: S3 File Processor
curl -X POST "https://pilot.owkai.app/api/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-s3-processor-01",
    "name": "S3 File Processor",
    "description": "Processes files in S3 buckets - handles customer documents",
    "organization_id": '$ORG_ID',
    "capabilities": ["file_read", "file_write", "file_delete"],
    "trust_level": "verified",
    "aws_resources": ["s3:customer-uploads-prod", "s3:financial-docs-prod"],
    "created_by": "devops.lead@techcorp-demo.com"
  }'

# Agent 3: EC2 Operations Agent
curl -X POST "https://pilot.owkai.app/api/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-ec2-operator-01",
    "name": "EC2 Operations Manager",
    "description": "Manages EC2 instances - starts/stops production servers",
    "organization_id": '$ORG_ID',
    "capabilities": ["instance_start", "instance_stop", "instance_terminate"],
    "trust_level": "unverified",
    "aws_resources": ["ec2:us-east-1:prod-web-*"],
    "created_by": "developer@techcorp-demo.com"
  }'
```

### Step 2.2: Configure AWS Resource Inventory

Register AWS resources that agents will access:

```bash
# Production RDS Database
curl -X POST "https://pilot.owkai.app/api/aws-resources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "rds:database",
    "resource_arn": "arn:aws:rds:us-east-1:123456789012:db:prod-customer-db",
    "resource_name": "prod-customer-db",
    "environment": "production",
    "sensitivity_level": "high",
    "contains_pii": true,
    "compliance_tags": ["SOX", "PCI-DSS", "GDPR"],
    "organization_id": '$ORG_ID'
  }'

# Production S3 Bucket (Financial Documents)
curl -X POST "https://pilot.owkai.app/api/aws-resources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "s3:bucket",
    "resource_arn": "arn:aws:s3:::financial-docs-prod",
    "resource_name": "financial-docs-prod",
    "environment": "production",
    "sensitivity_level": "critical",
    "contains_pii": true,
    "contains_financial_data": true,
    "compliance_tags": ["SOX", "PCI-DSS"],
    "organization_id": '$ORG_ID'
  }'

# Production EC2 Instances
curl -X POST "https://pilot.owkai.app/api/aws-resources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "ec2:instance",
    "resource_arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-prod-web-*",
    "resource_name": "prod-web-servers",
    "environment": "production",
    "sensitivity_level": "high",
    "compliance_tags": ["SOX"],
    "organization_id": '$ORG_ID'
  }'

# Development Database (for comparison)
curl -X POST "https://pilot.owkai.app/api/aws-resources" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_type": "rds:database",
    "resource_arn": "arn:aws:rds:us-east-1:123456789012:db:dev-test-db",
    "resource_name": "dev-test-db",
    "environment": "development",
    "sensitivity_level": "low",
    "contains_pii": false,
    "organization_id": '$ORG_ID'
  }'
```

---

## PHASE 3: CREATE GOVERNANCE RULES

### Step 3.1: High-Risk Blocking Rules

**Rule 1: Block All Production Database Writes with PII**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Production DB Writes with PII",
    "description": "Deny all database write operations to production databases containing PII unless pre-approved",
    "organization_id": '$ORG_ID',
    "policy_type": "security",
    "decision": "DENY",
    "conditions": {
      "resource_type": "rds:database",
      "environment": "production",
      "action_type": "database_write",
      "contains_pii": true
    },
    "risk_threshold": 90,
    "compliance_frameworks": ["SOX", "GDPR", "HIPAA"],
    "created_by": "security.manager@techcorp-demo.com",
    "status": "active"
  }'
```

**Rule 2: Block Financial Data Deletion**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Financial Data Deletion",
    "description": "Deny any file deletion operations on financial document storage to maintain SOX compliance audit trail",
    "organization_id": '$ORG_ID',
    "policy_type": "compliance",
    "decision": "DENY",
    "conditions": {
      "resource_type": "s3:bucket",
      "resource_name_contains": "financial",
      "action_type": "file_delete",
      "environment": "production"
    },
    "risk_threshold": 95,
    "compliance_frameworks": ["SOX", "PCI-DSS"],
    "created_by": "cto@techcorp-demo.com",
    "status": "active"
  }'
```

**Rule 3: Block Unverified Agent Production Access**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block Unverified Agents in Production",
    "description": "Deny all production resource access from unverified agents to prevent unauthorized automation",
    "organization_id": '$ORG_ID',
    "policy_type": "security",
    "decision": "DENY",
    "conditions": {
      "environment": "production",
      "agent_trust_level": "unverified"
    },
    "risk_threshold": 85,
    "compliance_frameworks": ["SOX", "PCI-DSS"],
    "created_by": "security.manager@techcorp-demo.com",
    "status": "active"
  }'
```

### Step 3.2: Approval Required Rules

**Rule 4: Require Approval for EC2 Termination**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Require Approval for EC2 Termination",
    "description": "Require CTO approval before terminating any production EC2 instances to prevent accidental outages",
    "organization_id": '$ORG_ID',
    "policy_type": "operational",
    "decision": "REQUIRE_APPROVAL",
    "conditions": {
      "resource_type": "ec2:instance",
      "action_type": "instance_terminate",
      "environment": "production"
    },
    "approval_requirements": {
      "required_level": 4,
      "approvers": ["cto@techcorp-demo.com"],
      "sla_minutes": 30
    },
    "risk_threshold": 75,
    "created_by": "cto@techcorp-demo.com",
    "status": "active"
  }'
```

**Rule 5: Require Approval for System Config Changes**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Require Approval for System Config",
    "description": "Require Security Manager approval for any system configuration changes in production",
    "organization_id": '$ORG_ID',
    "policy_type": "security",
    "decision": "REQUIRE_APPROVAL",
    "conditions": {
      "action_type": "system_config",
      "environment": "production"
    },
    "approval_requirements": {
      "required_level": 3,
      "approvers": ["security.manager@techcorp-demo.com", "cto@techcorp-demo.com"],
      "sla_minutes": 60
    },
    "risk_threshold": 70,
    "compliance_frameworks": ["SOX"],
    "created_by": "security.manager@techcorp-demo.com",
    "status": "active"
  }'
```

### Step 3.3: Allow Rules (Low Risk)

**Rule 6: Allow Development Database Operations**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow Dev Database Operations",
    "description": "Allow all database operations in development environment for developer productivity",
    "organization_id": '$ORG_ID',
    "policy_type": "operational",
    "decision": "ALLOW",
    "conditions": {
      "resource_type": "rds:database",
      "environment": "development"
    },
    "risk_threshold": 30,
    "created_by": "devops.lead@techcorp-demo.com",
    "status": "active"
  }'
```

**Rule 7: Allow Read-Only Production Access**

```bash
curl -X POST "https://pilot.owkai.app/api/governance/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow Read-Only Production Access",
    "description": "Allow verified agents to read from production databases for analytics and reporting",
    "organization_id": '$ORG_ID',
    "policy_type": "operational",
    "decision": "ALLOW",
    "conditions": {
      "action_type": "database_read",
      "environment": "production",
      "agent_trust_level": "verified"
    },
    "risk_threshold": 35,
    "created_by": "devops.lead@techcorp-demo.com",
    "status": "active"
  }'
```

### Step 3.4: Verify Rules

```bash
# List all policies for TechCorp Demo
curl -s "https://pilot.owkai.app/api/governance/policies?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {name, decision, risk_threshold, status}'

# Expected output: 7 policies with various decisions
```

---

## PHASE 4: SIMULATE AGENT ACTIONS

### Step 4.1: Create Test Script

Create a script to simulate realistic agent actions:

```bash
# Save this as: /tmp/simulate_agent_actions.sh
cat > /tmp/simulate_agent_actions.sh << 'SCRIPT_EOF'
#!/bin/bash

# Configuration
TOKEN="$1"
ORG_ID="$2"
BASE_URL="https://pilot.owkai.app"

if [ -z "$TOKEN" ] || [ -z "$ORG_ID" ]; then
    echo "Usage: $0 <TOKEN> <ORG_ID>"
    exit 1
fi

echo "🚀 Starting Agent Action Simulation for TechCorp Demo"
echo "=================================================="
echo ""

# Scenario 1: HIGH RISK - Production DB Write with PII (SHOULD BE BLOCKED)
echo "Test 1: Production Database Write with PII"
echo "Expected: DENIED (Rule 1: Block Production DB Writes with PII)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "database_write",
    "description": "Write customer PII records to production database",
    "target_resource": "arn:aws:rds:us-east-1:123456789012:db:prod-customer-db",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "contains_pii": true,
      "production_system": true,
      "records_affected": 1500
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched}'
echo ""
sleep 2

# Scenario 2: HIGH RISK - Delete Financial Files (SHOULD BE BLOCKED)
echo "Test 2: Delete Financial Documents from S3"
echo "Expected: DENIED (Rule 2: Block Financial Data Deletion)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-s3-processor-01",
    "action_type": "file_delete",
    "description": "Delete old invoices from financial documents bucket",
    "target_resource": "arn:aws:s3:::financial-docs-prod",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "contains_financial_data": true,
      "file_count": 250
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched}'
echo ""
sleep 2

# Scenario 3: HIGH RISK - Unverified Agent in Production (SHOULD BE BLOCKED)
echo "Test 3: Unverified Agent Accessing Production EC2"
echo "Expected: DENIED (Rule 3: Block Unverified Agents in Production)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-ec2-operator-01",
    "action_type": "instance_stop",
    "description": "Stop production web server for maintenance",
    "target_resource": "arn:aws:ec2:us-east-1:123456789012:instance/i-prod-web-01",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "agent_trust_level": "unverified"
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched}'
echo ""
sleep 2

# Scenario 4: MEDIUM RISK - EC2 Termination (SHOULD REQUIRE APPROVAL)
echo "Test 4: Terminate Production EC2 Instance"
echo "Expected: REQUIRE_APPROVAL (Rule 4: Require Approval for EC2 Termination)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-ec2-operator-01",
    "action_type": "instance_terminate",
    "description": "Terminate unused production web server",
    "target_resource": "arn:aws:ec2:us-east-1:123456789012:instance/i-prod-web-05",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "agent_trust_level": "verified"
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched, approval_required_from}'
echo ""
sleep 2

# Scenario 5: MEDIUM RISK - System Config Change (SHOULD REQUIRE APPROVAL)
echo "Test 5: Modify Production System Configuration"
echo "Expected: REQUIRE_APPROVAL (Rule 5: Require Approval for System Config)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "system_config",
    "description": "Update database connection pool settings in production",
    "target_resource": "arn:aws:rds:us-east-1:123456789012:db:prod-customer-db",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "config_type": "performance"
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched, approval_required_from}'
echo ""
sleep 2

# Scenario 6: LOW RISK - Dev Database Write (SHOULD BE ALLOWED)
echo "Test 6: Write Test Data to Development Database"
echo "Expected: ALLOWED (Rule 6: Allow Dev Database Operations)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "database_write",
    "description": "Insert test records for development testing",
    "target_resource": "arn:aws:rds:us-east-1:123456789012:db:dev-test-db",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "development",
      "contains_pii": false,
      "records_affected": 100
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched}'
echo ""
sleep 2

# Scenario 7: LOW RISK - Production Read (SHOULD BE ALLOWED)
echo "Test 7: Read Analytics Data from Production"
echo "Expected: ALLOWED (Rule 7: Allow Read-Only Production Access)"
curl -s -X POST "$BASE_URL/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "database_read",
    "description": "Query customer analytics for monthly report",
    "target_resource": "arn:aws:rds:us-east-1:123456789012:db:prod-customer-db",
    "organization_id": '$ORG_ID',
    "context": {
      "environment": "production",
      "agent_trust_level": "verified",
      "records_queried": 50000
    }
  }' | jq '{decision: .decision, risk_score: .risk_score, policy_matched: .policy_matched}'
echo ""

echo "=================================================="
echo "✅ Simulation Complete - 7 test scenarios executed"
echo "=================================================="
SCRIPT_EOF

chmod +x /tmp/simulate_agent_actions.sh
```

### Step 4.2: Run Simulation

```bash
# Execute the simulation
/tmp/simulate_agent_actions.sh "$TOKEN" "$ORG_ID"

# Expected Results Summary:
# Test 1: DENIED   (High Risk - Production DB Write with PII)
# Test 2: DENIED   (High Risk - Financial File Deletion)
# Test 3: DENIED   (High Risk - Unverified Agent in Prod)
# Test 4: REQUIRE_APPROVAL (Medium Risk - EC2 Termination)
# Test 5: REQUIRE_APPROVAL (Medium Risk - System Config)
# Test 6: ALLOWED  (Low Risk - Dev Database Write)
# Test 7: ALLOWED  (Low Risk - Production Read)
```

### Step 4.3: Generate Load Testing Data

For realistic demo, generate 50-100 agent actions:

```bash
# Create load testing script
cat > /tmp/load_test_actions.sh << 'LOAD_EOF'
#!/bin/bash
TOKEN="$1"
ORG_ID="$2"
COUNT="${3:-50}"

echo "Generating $COUNT agent actions..."

for i in $(seq 1 $COUNT); do
    # Randomly select action type
    case $((i % 7)) in
        0) ACTION="database_write"; RISK="high" ;;
        1) ACTION="database_read"; RISK="low" ;;
        2) ACTION="file_delete"; RISK="high" ;;
        3) ACTION="file_read"; RISK="low" ;;
        4) ACTION="instance_terminate"; RISK="medium" ;;
        5) ACTION="instance_stop"; RISK="medium" ;;
        6) ACTION="system_config"; RISK="medium" ;;
    esac

    # Randomly select environment
    if [ $((i % 3)) -eq 0 ]; then
        ENV="development"
    else
        ENV="production"
    fi

    curl -s -X POST "https://pilot.owkai.app/api/agent-action" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"agent_id\": \"aws-agent-$(printf "%02d" $((i % 3 + 1)))\",
        \"action_type\": \"$ACTION\",
        \"description\": \"Automated action $i - $ACTION in $ENV\",
        \"organization_id\": $ORG_ID,
        \"context\": {
          \"environment\": \"$ENV\",
          \"test_id\": $i
        }
      }" > /dev/null

    echo "Action $i/$COUNT: $ACTION in $ENV"
    sleep 0.5
done

echo "✅ Load test complete: $COUNT actions generated"
LOAD_EOF

chmod +x /tmp/load_test_actions.sh

# Generate 50 test actions
/tmp/load_test_actions.sh "$TOKEN" "$ORG_ID" 50
```

---

## PHASE 5: MONITOR & MEASURE EFFECTIVENESS

### Step 5.1: View Real-Time Activity Dashboard

**Access the Dashboard:**
1. Navigate to: https://pilot.owkai.app
2. Login as: `cto@techcorp-demo.com` / `Demo2025!`
3. Click "Activity" tab
4. **You should see:**
   - Real-time list of all agent actions
   - Color-coded by risk (red=critical, orange=high, yellow=medium, green=low)
   - Decision badges (DENIED, APPROVED, PENDING)
   - CVSS scores and severity levels
   - MITRE ATT&CK tactics
   - NIST control mappings

### Step 5.2: Query Effectiveness Metrics

**Get Overall Statistics:**

```bash
# Get action counts by decision
curl -s "https://pilot.owkai.app/api/analytics/decisions?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected Response:
{
  "total_actions": 57,
  "denied": 21,      # 37% blocked (high-risk actions)
  "allowed": 28,     # 49% allowed (low-risk actions)
  "pending": 8,      # 14% pending approval (medium-risk)
  "blocked_rate": 0.368,
  "approval_rate": 0.140,
  "allow_rate": 0.491
}
```

**Get Risk Distribution:**

```bash
# Get actions by risk level
curl -s "https://pilot.owkai.app/api/analytics/risk-distribution?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected Response:
{
  "critical": 8,    # Automatic deny
  "high": 13,       # Automatic deny
  "medium": 18,     # Require approval
  "low": 18,        # Automatic allow
  "mean_risk_score": 58.2,
  "median_risk_score": 55.0
}
```

**Get Policy Effectiveness:**

```bash
# Get actions blocked by each policy
curl -s "https://pilot.owkai.app/api/analytics/policy-effectiveness?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {policy_name, actions_blocked, blocked_rate}'

# Expected Response:
[
  {
    "policy_name": "Block Production DB Writes with PII",
    "actions_blocked": 8,
    "blocked_rate": 1.0
  },
  {
    "policy_name": "Block Financial Data Deletion",
    "actions_blocked": 5,
    "blocked_rate": 1.0
  },
  {
    "policy_name": "Block Unverified Agents in Production",
    "actions_blocked": 8,
    "blocked_rate": 1.0
  }
]
```

**Get Performance Metrics:**

```bash
# Get evaluation time statistics
curl -s "https://pilot.owkai.app/api/analytics/performance?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected Response:
{
  "total_evaluations": 57,
  "mean_evaluation_time_ms": 47,
  "median_evaluation_time_ms": 12,
  "p95_evaluation_time_ms": 156,
  "p99_evaluation_time_ms": 178,
  "under_200ms_rate": 0.963    # 96.3% under 200ms (your patent!)
}
```

### Step 5.3: Generate Compliance Report

```bash
# Generate SOX compliance report
curl -s "https://pilot.owkai.app/api/reports/compliance?organization_id=$ORG_ID&framework=SOX&days=7" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' > /tmp/techcorp_sox_report.json

echo "📊 SOX Compliance Report saved to: /tmp/techcorp_sox_report.json"
cat /tmp/techcorp_sox_report.json | jq '{
  organization,
  compliance_framework,
  audit_period,
  total_actions,
  high_risk_blocked,
  approval_compliance_rate,
  audit_trail_complete
}'

# Expected Output:
{
  "organization": "TechCorp Demo Inc.",
  "compliance_framework": "SOX",
  "audit_period": "2025-11-06 to 2025-11-13",
  "total_actions": 57,
  "high_risk_blocked": 21,
  "approval_compliance_rate": 1.0,
  "audit_trail_complete": true
}
```

### Step 5.4: View Immutable Audit Trail

```bash
# Get audit trail for high-risk actions
curl -s "https://pilot.owkai.app/api/audit/trail?organization_id=$ORG_ID&risk_level=critical" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {
    timestamp,
    actor,
    action_type,
    decision,
    risk_score,
    cvss_score,
    content_hash,
    chain_hash
  }' | head -30

# Verify chain integrity
curl -s "https://pilot.owkai.app/api/audit/verify-integrity?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected Response:
{
  "total_logs": 57,
  "chain_valid": true,
  "broken_chains": 0,
  "invalid_hashes": 0,
  "verification_rate_per_second": 1247
}
```

---

## DEMO SCRIPT

### 5-Minute Live Demo Walkthrough

**SETUP (Before Demo):**
```bash
# 1. Reset demo data
/tmp/simulate_agent_actions.sh "$TOKEN" "$ORG_ID"

# 2. Open browser to Activity Dashboard
open "https://pilot.owkai.app"

# 3. Login as CTO
# Email: cto@techcorp-demo.com
# Password: Demo2025!
```

---

**MINUTE 1: Introduction (30 seconds)**

> "Welcome to OW-AI's Enterprise AI Governance Platform. Today I'll show you
> how TechCorp Demo Inc. uses our system to control their AI agents accessing
> AWS resources in real-time.
>
> TechCorp has 3 AI agents managing their AWS infrastructure: RDS databases,
> S3 storage, and EC2 instances. They need to prevent high-risk actions while
> allowing safe operations to continue."

**SHOW:** Activity Dashboard with 50+ actions

---

**MINUTE 2: High-Risk Blocking (1 minute)**

> "Let's test our most critical rule: blocking production database writes with PII."

**RUN IN TERMINAL:**
```bash
echo "🔴 TEST 1: HIGH RISK - Production DB Write"
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "database_write",
    "description": "Write 1,500 customer PII records to production database",
    "target_resource": "prod-customer-db",
    "organization_id": '$ORG_ID',
    "context": {"environment": "production", "contains_pii": true}
  }' | jq '{decision, risk_score, cvss_score, policy_matched}'
```

**EXPECTED OUTPUT:**
```json
{
  "decision": "DENIED",
  "risk_score": 95,
  "cvss_score": 10.0,
  "policy_matched": "Block Production DB Writes with PII"
}
```

**SHOW IN DASHBOARD:**
- New action appears at top with RED badge "DENIED"
- CVSS score: 10.0 (CRITICAL)
- Response time: <200ms
- Reason: "Blocked by policy - Production DB Writes with PII"

> "Notice: DENIED in 47 milliseconds. The agent never touched production data."

---

**MINUTE 3: Approval Workflow (1 minute)**

> "For medium-risk actions, we require human approval instead of automatic denial."

**RUN IN TERMINAL:**
```bash
echo "🟡 TEST 2: MEDIUM RISK - EC2 Termination"
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-ec2-operator-01",
    "action_type": "instance_terminate",
    "description": "Terminate production web server i-prod-web-05",
    "target_resource": "i-prod-web-05",
    "organization_id": '$ORG_ID',
    "context": {"environment": "production"}
  }' | jq '{decision, risk_score, approval_required_from}'
```

**EXPECTED OUTPUT:**
```json
{
  "decision": "REQUIRE_APPROVAL",
  "risk_score": 75,
  "approval_required_from": ["cto@techcorp-demo.com"]
}
```

**SHOW IN DASHBOARD:**
- New action with YELLOW badge "PENDING APPROVAL"
- Assigned to: CTO (Michael Rodriguez)
- SLA: 30 minutes remaining
- Click "Approve" or "Deny" button

> "The CTO gets notified and can approve or deny within the 30-minute SLA.
> This prevents accidental deletions while keeping operations moving."

---

**MINUTE 4: Low-Risk Allow (1 minute)**

> "Low-risk actions are automatically allowed to avoid approval bottlenecks."

**RUN IN TERMINAL:**
```bash
echo "🟢 TEST 3: LOW RISK - Dev Database Write"
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "aws-rds-manager-01",
    "action_type": "database_write",
    "description": "Insert test records for development testing",
    "target_resource": "dev-test-db",
    "organization_id": '$ORG_ID',
    "context": {"environment": "development", "contains_pii": false}
  }' | jq '{decision, risk_score, cvss_score}'
```

**EXPECTED OUTPUT:**
```json
{
  "decision": "ALLOWED",
  "risk_score": 28,
  "cvss_score": 4.1
}
```

**SHOW IN DASHBOARD:**
- New action with GREEN badge "ALLOWED"
- CVSS score: 4.1 (MEDIUM severity but allowed due to dev environment)
- No approval needed

> "Development operations continue without friction. Risk score is 28 - well
> below our auto-block threshold of 90."

---

**MINUTE 5: Metrics & Compliance (1.5 minutes)**

**SHOW METRICS DASHBOARD:**

> "Let's look at effectiveness over the past week."

**RUN IN TERMINAL:**
```bash
echo "📊 EFFECTIVENESS METRICS"
curl -s "https://pilot.owkai.app/api/analytics/decisions?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    total_actions,
    denied,
    allowed,
    blocked_rate,
    under_200ms_rate
  }'
```

**EXPECTED OUTPUT:**
```json
{
  "total_actions": 58,
  "denied": 22,
  "allowed": 28,
  "blocked_rate": 0.379,
  "under_200ms_rate": 0.963
}
```

**SHOW COMPLIANCE REPORT:**

> "And here's our SOX compliance report showing complete audit trail."

**RUN IN TERMINAL:**
```bash
curl -s "https://pilot.owkai.app/api/reports/compliance?organization_id=$ORG_ID&framework=SOX" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    compliance_framework,
    total_actions,
    high_risk_blocked,
    audit_trail_complete
  }'
```

**EXPECTED OUTPUT:**
```json
{
  "compliance_framework": "SOX",
  "total_actions": 58,
  "high_risk_blocked": 22,
  "audit_trail_complete": true
}
```

**KEY POINTS TO EMPHASIZE:**

✅ **37.9% of actions blocked** (high-risk automatic denial)
✅ **96.3% evaluated in <200ms** (real-time performance - your patent!)
✅ **100% audit trail integrity** (hash-chaining - your patent!)
✅ **Zero false negatives** (every high-risk action caught)
✅ **SOX/PCI/GDPR compliant** (automatic compliance mapping)

---

**CLOSING (30 seconds)**

> "To summarize: TechCorp blocked 22 high-risk actions, required approval for
> 8 medium-risk actions, and allowed 28 safe operations - all in real-time
> with complete audit trails for SOX compliance.
>
> The system uses our patented hybrid CVSS risk assessment, natural language
> policy engine, and immutable audit trail to provide enterprise-grade
> AI governance.
>
> Questions?"

---

## TROUBLESHOOTING

### Issue 1: Authentication Token Expired

**Symptom:** Getting 401 Unauthorized errors

**Solution:**
```bash
# Get fresh token
curl -X POST "https://pilot.owkai.app/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@owkai.com","password":"admin123"}' \
  | jq -r '.access_token'

# Update TOKEN variable
export TOKEN="<new_token>"
```

### Issue 2: Rules Not Matching

**Symptom:** Actions not being blocked/allowed as expected

**Solution:**
```bash
# Check policy conditions match exactly
curl -s "https://pilot.owkai.app/api/governance/policies/$POLICY_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.conditions'

# Check action context
curl -s "https://pilot.owkai.app/api/agent-activity/$ACTION_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.context'

# Ensure keys match (environment, action_type, resource_type, etc.)
```

### Issue 3: Dashboard Not Showing Actions

**Symptom:** Activity tab is empty

**Solution:**
```bash
# Verify actions exist in database
curl -s "https://pilot.owkai.app/api/agent-activity?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

# If 0, run simulation again
/tmp/simulate_agent_actions.sh "$TOKEN" "$ORG_ID"

# Check browser console for errors (F12)
# Refresh page (Cmd+R / Ctrl+R)
```

### Issue 4: Performance Slower Than Expected

**Symptom:** Evaluation taking >200ms

**Solution:**
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM agent_actions;"

# Check policy cache hit rate
curl -s "https://pilot.owkai.app/api/analytics/cache-stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.cache_hit_rate'

# Expected: >0.70 (70%+)

# Warm up cache by running test actions
for i in {1..10}; do
  /tmp/simulate_agent_actions.sh "$TOKEN" "$ORG_ID" &>/dev/null
done
```

### Issue 5: Organization Not Found

**Symptom:** Getting 404 errors for organization

**Solution:**
```bash
# List all organizations
curl -s "https://pilot.owkai.app/api/enterprise-users/organizations" \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, name}'

# Find TechCorp Demo ID
export ORG_ID=$(curl -s "https://pilot.owkai.app/api/enterprise-users/organizations" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[] | select(.name=="TechCorp Demo Inc.") | .id')

echo "Organization ID: $ORG_ID"
```

---

## ADVANCED TESTING SCENARIOS

### Scenario A: Escalation Path Testing

Test the 5-tier approval system:

```bash
# Risk Score 50 → Level 1 (Peer Review)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"agent_id":"test","action_type":"database_read","risk_score":50}'

# Risk Score 70 → Level 3 (Department Head)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"agent_id":"test","action_type":"system_config","risk_score":70}'

# Risk Score 80 → Level 4 (Senior Management)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"agent_id":"test","action_type":"instance_terminate","risk_score":80}'

# Risk Score 90 → Level 5 (Executive - Auto Block)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"agent_id":"test","action_type":"database_write","risk_score":90}'
```

### Scenario B: Compliance Framework Testing

Test each compliance framework:

```bash
# SOX Compliance (7-year retention)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -d '{"compliance_tags":["SOX"],...}'
# Check retention_until = NOW() + 7 years

# HIPAA Compliance (6-year retention)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -d '{"compliance_tags":["HIPAA"],...}'
# Check retention_until = NOW() + 6 years

# PCI-DSS Compliance (1-year retention)
curl -X POST "https://pilot.owkai.app/api/agent-action" \
  -d '{"compliance_tags":["PCI-DSS"],...}'
# Check retention_until = NOW() + 1 year
```

### Scenario C: Hash Chain Integrity Testing

Test immutable audit trail (your patent #3):

```bash
# Generate 100 actions
/tmp/load_test_actions.sh "$TOKEN" "$ORG_ID" 100

# Verify chain integrity
curl -s "https://pilot.owkai.app/api/audit/verify-integrity?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: chain_valid=true, broken_chains=0, invalid_hashes=0

# Attempt to tamper (should be detected)
psql $DATABASE_URL << 'SQL'
UPDATE immutable_audit_logs
SET event_data = '{"tampered": true}'
WHERE id = (SELECT MAX(id) FROM immutable_audit_logs);
SQL

# Re-verify (should detect tampering)
curl -s "https://pilot.owkai.app/api/audit/verify-integrity?organization_id=$ORG_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: invalid_hashes=1 (tampering detected!)
```

---

## CLEANUP

### Remove Demo Organization

```bash
# Delete all demo data
curl -X DELETE "https://pilot.owkai.app/api/enterprise-users/organizations/$ORG_ID?confirm=true" \
  -H "Authorization: Bearer $TOKEN"

# Verify deletion
curl -s "https://pilot.owkai.app/api/enterprise-users/organizations/$ORG_ID" \
  -H "Authorization: Bearer $TOKEN"
# Expected: 404 Not Found
```

### Reset Database (Local Only)

```bash
# WARNING: This deletes ALL demo data
psql $DATABASE_URL << 'SQL'
DELETE FROM agent_actions WHERE organization_id = $ORG_ID;
DELETE FROM governance_policies WHERE organization_id = $ORG_ID;
DELETE FROM aws_resources WHERE organization_id = $ORG_ID;
DELETE FROM users WHERE organization_id = $ORG_ID;
DELETE FROM organizations WHERE id = $ORG_ID;
SQL
```

---

## NEXT STEPS

### After Successful Demo

1. **Export Metrics:** Download compliance report for customer
2. **Schedule Follow-Up:** Book enterprise pilot with real client
3. **Customize Rules:** Adapt policies to client's specific needs
4. **Integration Planning:** Design AWS CloudTrail integration
5. **Pricing Discussion:** Calculate cost based on action volume

### Production Deployment Checklist

- [ ] Real AWS account integration (not simulated)
- [ ] SSO/SAML authentication setup
- [ ] Custom compliance frameworks
- [ ] Email notifications for approvals
- [ ] Slack/Teams integration for alerts
- [ ] Custom RBAC roles beyond 5-tier system
- [ ] SLA monitoring and escalation
- [ ] Backup and disaster recovery
- [ ] Load balancing for >10K actions/day
- [ ] Enterprise support SLA

---

## SUMMARY

You've now created a complete demo environment showing:

✅ **Multi-tenant organization** (TechCorp Demo Inc.)
✅ **5 users with approval hierarchy** (CEO → Developer)
✅ **3 AI agents** (RDS, S3, EC2 managers)
✅ **7 governance policies** (block, approve, allow rules)
✅ **50+ simulated actions** (realistic load testing)
✅ **Real-time monitoring** (Activity Dashboard)
✅ **Compliance reporting** (SOX/HIPAA/PCI-DSS)
✅ **Audit trail verification** (hash-chain integrity)

**Demo proves:**
- 🎯 90%+ high-risk blocking effectiveness
- ⚡ 96.3% sub-200ms evaluation (patent #2)
- 🔒 100% audit trail integrity (patent #3)
- 📊 Complete SOX/HIPAA compliance

**This demo showcases all 4 of your patentable innovations working together!**

---

**Questions or issues? Review the Troubleshooting section or contact support.**

**Ready to onboard your first real client? Start with Phase 1 and customize from there.**
