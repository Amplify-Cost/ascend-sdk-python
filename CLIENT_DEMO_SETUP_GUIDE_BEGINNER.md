# OW-AI Demo Setup Guide (Beginner-Friendly Version)

**For Users with Limited Technical Experience**

**Purpose**: This guide will help you set up a demo environment to show clients how OW-AI's governance system stops risky AI agent actions.

**Time Required**: 30-45 minutes

**What You'll Create**: A simulated client organization with AI agents and governance rules that you can demonstrate live.

---

## Before You Start

### What You Need:
1. **Computer with Internet**: Mac, Windows, or Linux
2. **Web Browser**: Chrome, Firefox, Safari, or Edge
3. **Your OW-AI Admin Login**:
   - Website: https://pilot.owkai.app
   - Admin email: admin@owkai.com
   - Admin password: (your password)
4. **Notepad**: To write down important information as we go

### What You'll Learn:
- How to create a test organization
- How to add AI agents to monitor
- How to create governance rules
- How to see those rules block dangerous actions

---

## Part 1: Log Into OW-AI Platform

### Step 1.1: Open the Website
1. Open your web browser
2. Type this address in the address bar: `https://pilot.owkai.app`
3. Press Enter

**What You Should See**: A login page with email and password fields

### Step 1.2: Log In
1. In the **Email** field, type: `admin@owkai.com`
2. In the **Password** field, type your admin password
3. Click the blue **"Login"** button

**What You Should See**: The OW-AI dashboard with a menu on the left side showing options like:
- Dashboard
- Activity
- Authorization Center
- Analytics
- Settings

**If You Don't See This**: The password might be wrong. Try typing it again carefully.

---

## Part 2: Create a Demo Organization

This creates a fake company (TechCorp Demo Inc.) that you'll use to demonstrate the system.

### Step 2.1: Open Organizations Page
1. Look at the left menu
2. Click on **"Enterprise Users"** or **"Organizations"**
3. You should see a list of organizations (might be empty)

**What You Should See**: A page with a **"+ New Organization"** button at the top

### Step 2.2: Create TechCorp Demo Organization
1. Click the green **"+ New Organization"** button
2. Fill in these fields:

   **Organization Name**: `TechCorp Demo Inc.`

   **Domain**: `techcorp-demo.com`

   **Industry**: Click the dropdown and select `Financial Services`

   **Company Size**: Select `1000-5000 employees`

   **Compliance Requirements**: Check these boxes:
   - ☑ SOX (financial reporting)
   - ☑ PCI-DSS (payment card security)
   - ☑ GDPR (data privacy)

3. Click **"Create Organization"** button at the bottom

**What You Should See**:
- A green message saying "Organization created successfully"
- A **12-digit Organization ID number** (example: 987654321012)

**IMPORTANT**: Write down this Organization ID in your notepad. You'll need it later.

**Example**:
```
My TechCorp Demo Org ID: 987654321012
```

---

## Part 3: Add Demo Users to the Organization

These are fake employees of TechCorp that we'll use for testing.

### Step 3.1: Go to Users Section
1. Click on **"Users"** in the left menu
2. Click **"+ Add User"** button

### Step 3.2: Add 5 Demo Users

For each user below, click **"+ Add User"**, fill in the information, and click **"Create User"**:

#### User 1: CEO
- **Name**: Sarah Johnson
- **Email**: sarah.johnson@techcorp-demo.com
- **Role**: Select "Executive" from dropdown
- **Department**: Executive
- **Organization**: Select "TechCorp Demo Inc." from dropdown
- Click **"Create User"**

#### User 2: Security Director
- **Name**: Michael Chen
- **Email**: michael.chen@techcorp-demo.com
- **Role**: Select "Manager" from dropdown
- **Department**: Security
- **Organization**: Select "TechCorp Demo Inc." from dropdown
- Click **"Create User"**

#### User 3: Compliance Officer
- **Name**: Emily Rodriguez
- **Email**: emily.rodriguez@techcorp-demo.com
- **Role**: Select "Manager" from dropdown
- **Department**: Compliance
- **Organization**: Select "TechCorp Demo Inc." from dropdown
- Click **"Create User"**

#### User 4: IT Manager
- **Name**: David Kim
- **Email**: david.kim@techcorp-demo.com
- **Role**: Select "Manager" from dropdown
- **Department**: IT Operations
- **Organization**: Select "TechCorp Demo Inc." from dropdown
- Click **"Create User"**

#### User 5: Developer
- **Name**: Alex Martinez
- **Email**: alex.martinez@techcorp-demo.com
- **Role**: Select "User" from dropdown
- **Department**: Engineering
- **Organization**: Select "TechCorp Demo Inc." from dropdown
- Click **"Create User"**

**What You Should See**: After each user creation, you'll see a success message. The users list should now show all 5 TechCorp employees.

---

## Part 4: Add AI Agents to Monitor

These are the AI agents that will try to perform actions. Our rules will block the dangerous ones.

### Step 4.1: Go to Agents Section
1. Click on **"Agents"** in the left menu
2. Click **"+ Add Agent"** button

### Step 4.2: Add 3 Demo Agents

#### Agent 1: RDS Database Manager (HIGH RISK)
1. Click **"+ Add Agent"**
2. Fill in:
   - **Agent Name**: `rds-db-manager-prod`
   - **Agent Type**: Select "Database Agent" from dropdown
   - **Description**: `Manages production RDS databases with customer financial data`
   - **Risk Level**: Select "HIGH" from dropdown
   - **Capabilities**: Type `database_write, database_read, table_create, table_drop`
   - **Organization**: Select "TechCorp Demo Inc."
3. Click **"Create Agent"**

**What You Should See**: Green success message and the agent appears in the list with a RED badge saying "HIGH RISK"

#### Agent 2: S3 File Processor (MEDIUM RISK)
1. Click **"+ Add Agent"**
2. Fill in:
   - **Agent Name**: `s3-file-processor-agent`
   - **Agent Type**: Select "Storage Agent" from dropdown
   - **Description**: `Processes customer files in S3 buckets`
   - **Risk Level**: Select "MEDIUM" from dropdown
   - **Capabilities**: Type `s3_write, s3_read, file_delete`
   - **Organization**: Select "TechCorp Demo Inc."
3. Click **"Create Agent"**

**What You Should See**: Success message and agent with YELLOW "MEDIUM RISK" badge

#### Agent 3: EC2 Instance Manager (LOW RISK)
1. Click **"+ Add Agent"**
2. Fill in:
   - **Agent Name**: `ec2-instance-manager`
   - **Agent Type**: Select "Compute Agent" from dropdown
   - **Description**: `Monitors EC2 instances in development environment`
   - **Risk Level**: Select "LOW" from dropdown
   - **Capabilities**: Type `ec2_describe, instance_status, cloudwatch_read`
   - **Organization**: Select "TechCorp Demo Inc."
3. Click **"Create Agent"**

**What You Should See**: Success message and agent with GREEN "LOW RISK" badge

---

## Part 5: Create Governance Rules

These rules will automatically block dangerous actions and require approval for risky ones.

### Step 5.1: Go to Governance Section
1. Click on **"Authorization Center"** in the left menu
2. Click on **"Policy Management"** tab
3. Click **"+ New Policy"** button

### Step 5.2: Create 7 Governance Rules

#### Rule 1: BLOCK Production Database Writes with Customer Data
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Block Prod DB Writes with PII`
   - **Description**: `Block all database write operations to production databases containing customer financial data (PII)`
   - **Decision**: Select "DENY" (red option)
   - **Risk Threshold**: Move slider to `90` (high risk)
   - **Conditions**:
     - Click "Add Condition"
     - Field: `resource_type` | Operator: `equals` | Value: `rds:database`
     - Click "Add Condition"
     - Field: `environment` | Operator: `equals` | Value: `production`
     - Click "Add Condition"
     - Field: `action_type` | Operator: `equals` | Value: `database_write`
     - Click "Add Condition"
     - Field: `contains_pii` | Operator: `equals` | Value: `true`
   - **Compliance Tags**: Check SOX, PCI-DSS, GDPR
3. Click **"Create Policy"**

**What You Should See**: Policy created with RED "DENY" badge and "HIGH RISK" label

#### Rule 2: BLOCK Deleting Financial Files
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Block Financial File Deletion`
   - **Description**: `Prevent deletion of files in financial-records S3 bucket`
   - **Decision**: Select "DENY"
   - **Risk Threshold**: `85`
   - **Conditions**:
     - Field: `resource_type` | equals | `s3:bucket`
     - Field: `resource_name` | contains | `financial-records`
     - Field: `action_type` | equals | `file_delete`
   - **Compliance Tags**: Check SOX
3. Click **"Create Policy"**

**What You Should See**: Another DENY policy with HIGH RISK label

#### Rule 3: BLOCK Unverified Agents in Production
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Block Unverified Agents in Prod`
   - **Description**: `Deny access for agents that are not verified in production environment`
   - **Decision**: Select "DENY"
   - **Risk Threshold**: `95`
   - **Conditions**:
     - Field: `environment` | equals | `production`
     - Field: `agent_verified` | equals | `false`
   - **Compliance Tags**: Check SOX, GDPR
3. Click **"Create Policy"**

#### Rule 4: REQUIRE APPROVAL for EC2 Termination
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Approve Before EC2 Termination`
   - **Description**: `Production EC2 instances require manager approval before termination`
   - **Decision**: Select "REQUIRE_APPROVAL" (yellow option)
   - **Risk Threshold**: `70`
   - **Approval Levels**: Select "2" (Peer + Manager)
   - **Conditions**:
     - Field: `resource_type` | equals | `ec2:instance`
     - Field: `action_type` | equals | `terminate_instance`
     - Field: `environment` | equals | `production`
   - **Compliance Tags**: Check SOX
3. Click **"Create Policy"**

**What You Should See**: Policy with YELLOW "REQUIRE_APPROVAL" badge

#### Rule 5: REQUIRE APPROVAL for System Config Changes
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Approve System Config Changes`
   - **Description**: `System configuration changes require compliance officer approval`
   - **Decision**: Select "REQUIRE_APPROVAL"
   - **Risk Threshold**: `65`
   - **Approval Levels**: Select "3" (Peer + Manager + Department Head)
   - **Conditions**:
     - Field: `resource_type` | equals | `system:config`
     - Field: `action_type` | contains | `modify`
3. Click **"Create Policy"**

#### Rule 6: ALLOW Development Database Writes
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Allow Dev Database Writes`
   - **Description**: `Development database writes are allowed for verified agents`
   - **Decision**: Select "ALLOW" (green option)
   - **Risk Threshold**: `30`
   - **Conditions**:
     - Field: `environment` | equals | `development`
     - Field: `action_type` | equals | `database_write`
     - Field: `agent_verified` | equals | `true`
3. Click **"Create Policy"**

**What You Should See**: Policy with GREEN "ALLOW" badge and "LOW RISK" label

#### Rule 7: ALLOW Production Read Operations
1. Click **"+ New Policy"**
2. Fill in:
   - **Policy Name**: `Allow Prod Read-Only Access`
   - **Description**: `Production database read operations are allowed for verified agents`
   - **Decision**: Select "ALLOW"
   - **Risk Threshold**: `25`
   - **Conditions**:
     - Field: `environment` | equals | `production`
     - Field: `action_type` | equals | `database_read`
     - Field: `agent_verified` | equals | `true`
3. Click **"Create Policy"**

**What You Should See**: All 7 policies now visible:
- 3 RED (DENY) policies for high-risk actions
- 2 YELLOW (REQUIRE_APPROVAL) policies for medium-risk
- 2 GREEN (ALLOW) policies for low-risk actions

---

## Part 6: Test the System (Simulate Agent Actions)

Now we'll pretend to be AI agents trying to perform actions and watch the rules block them.

### Step 6.1: Go to Activity Monitoring
1. Click on **"Activity"** tab in the left menu
2. You should see a page showing recent agent actions

### Step 6.2: Create Test Actions

We'll create 7 test scenarios to prove the rules work.

#### Test 1: HIGH RISK - Production Database Write with PII (Should be BLOCKED)

1. Click on **"Agents"** in left menu
2. Find the `rds-db-manager-prod` agent
3. Click the **"Simulate Action"** button next to it
4. Fill in:
   - **Action Type**: `database_write`
   - **Resource Type**: `rds:database`
   - **Resource Name**: `customer-financials-prod`
   - **Environment**: `production`
   - **Contains PII**: Check YES box
   - **Description**: `Writing customer credit card data to production database`
5. Click **"Submit Action"**

**What You Should See**:
- A RED "DENIED" message appears
- Reason shown: "Blocked by policy: Block Prod DB Writes with PII"
- Risk Score: 92-95 (very high)
- CVSS Severity: CRITICAL

#### Test 2: HIGH RISK - Delete Financial Files (Should be BLOCKED)

1. Find the `s3-file-processor-agent` agent
2. Click **"Simulate Action"**
3. Fill in:
   - **Action Type**: `file_delete`
   - **Resource Type**: `s3:bucket`
   - **Resource Name**: `financial-records-2024`
   - **Environment**: `production`
   - **Description**: `Deleting old financial records from S3 bucket`
4. Click **"Submit Action"**

**What You Should See**:
- RED "DENIED" message
- Blocked by: "Block Financial File Deletion"
- Risk Score: 85-88

#### Test 3: HIGH RISK - Unverified Agent Access (Should be BLOCKED)

1. Click **"+ Add Agent"** (create temporary unverified agent)
2. Create agent:
   - Name: `unverified-test-agent`
   - Type: Database Agent
   - Risk Level: HIGH
   - **Agent Verified**: UNCHECKED (leave this blank)
   - Organization: TechCorp Demo Inc.
3. Click **"Simulate Action"** on this new agent
4. Fill in:
   - **Action Type**: `database_read`
   - **Resource Type**: `rds:database`
   - **Environment**: `production`
5. Click **"Submit Action"**

**What You Should See**:
- RED "DENIED" message
- Blocked by: "Block Unverified Agents in Prod"
- Risk Score: 95+

#### Test 4: MEDIUM RISK - EC2 Termination (Should REQUIRE APPROVAL)

1. Find the `ec2-instance-manager` agent
2. Click **"Simulate Action"**
3. Fill in:
   - **Action Type**: `terminate_instance`
   - **Resource Type**: `ec2:instance`
   - **Resource Name**: `web-server-prod-01`
   - **Environment**: `production`
4. Click **"Submit Action"**

**What You Should See**:
- YELLOW "PENDING APPROVAL" message
- Requires: "Manager approval needed"
- Risk Score: 68-72
- Approval workflow started

#### Test 5: MEDIUM RISK - System Config Change (Should REQUIRE APPROVAL)

1. Find any agent
2. Click **"Simulate Action"**
3. Fill in:
   - **Action Type**: `modify_config`
   - **Resource Type**: `system:config`
   - **Resource Name**: `database-connection-pool`
4. Click **"Submit Action"**

**What You Should See**:
- YELLOW "PENDING APPROVAL"
- Requires: "Department Head approval"
- Risk Score: 64-68

#### Test 6: LOW RISK - Development Database Write (Should be ALLOWED)

1. Find the `rds-db-manager-prod` agent
2. Click **"Simulate Action"**
3. Fill in:
   - **Action Type**: `database_write`
   - **Resource Type**: `rds:database`
   - **Resource Name**: `test-database-dev`
   - **Environment**: `development`
   - **Agent Verified**: Check YES
4. Click **"Submit Action"**

**What You Should See**:
- GREEN "ALLOWED" message
- Policy matched: "Allow Dev Database Writes"
- Risk Score: 28-32 (low)
- Action executed successfully

#### Test 7: LOW RISK - Production Read (Should be ALLOWED)

1. Find the `rds-db-manager-prod` agent
2. Click **"Simulate Action"**
3. Fill in:
   - **Action Type**: `database_read`
   - **Resource Type**: `rds:database`
   - **Resource Name**: `customer-financials-prod`
   - **Environment**: `production`
   - **Agent Verified**: Check YES
4. Click **"Submit Action"**

**What You Should See**:
- GREEN "ALLOWED" message
- Policy matched: "Allow Prod Read-Only Access"
- Risk Score: 22-28
- Read-only access granted

---

## Part 7: View Results Dashboard

### Step 7.1: Check Activity Tab
1. Click on **"Activity"** in the left menu
2. You should now see all 7 test actions listed

**What You Should See**:
- **3 actions with RED badges** (DENIED - blocked by rules)
- **2 actions with YELLOW badges** (PENDING APPROVAL - waiting for manager)
- **2 actions with GREEN badges** (ALLOWED - safe to proceed)

### Step 7.2: View Analytics
1. Click on **"Analytics"** in the left menu
2. Look at the dashboard

**What You Should See**:
- **Total Actions**: 7
- **Blocked Actions**: 3 (43% blocked - proving governance works!)
- **Pending Approvals**: 2 (29% requiring human review)
- **Allowed Actions**: 2 (29% low-risk operations)
- **Risk Distribution Chart**: Showing high/medium/low risk breakdown
- **CVSS Severity Breakdown**: CRITICAL, HIGH, MEDIUM, LOW counts
- **Top Blocked Policies**: "Block Prod DB Writes with PII" at #1

### Step 7.3: Export Report (Optional)
1. In the Analytics page, click **"Export Report"** button
2. Select "PDF" format
3. Click **"Download"**

**What You Get**: A professional PDF report showing all governance activity that you can share with clients or executives.

---

## Part 8: Live Demo Script (5 Minutes)

Use this script when showing the demo to clients:

### Opening (30 seconds)
> "Let me show you how OW-AI's governance system protects your organization from risky AI agent actions. I've set up a demo company called TechCorp with 3 AI agents and 7 governance rules."

### Demo Scenario 1: HIGH RISK BLOCK (1 minute)
1. Navigate to Agents page
2. Select `rds-db-manager-prod`
3. Click "Simulate Action"
4. Show: Database write to production with customer credit cards

> "Watch what happens when an AI agent tries to write customer credit card data to production..."

5. Click "Submit Action"
6. Point to RED "DENIED" message

> "The system AUTOMATICALLY BLOCKED this action because it violates our 'No PII in production writes' policy. Risk score: 95/100. This is exactly the kind of dangerous action that could cause a data breach."

### Demo Scenario 2: APPROVAL REQUIRED (1 minute)
1. Select `ec2-instance-manager`
2. Simulate: Terminate production EC2 instance

> "Now let's try something less dangerous but still risky - terminating a production server..."

3. Show YELLOW "PENDING APPROVAL" result

> "The system didn't block it completely, but it's requiring manager approval before proceeding. This gives humans control over medium-risk actions while still allowing automation for safe operations."

### Demo Scenario 3: LOW RISK ALLOW (1 minute)
1. Select `rds-db-manager-prod`
2. Simulate: Read from production database

> "Finally, let's try a safe operation - reading data from production..."

3. Show GREEN "ALLOWED" result

> "This action was approved instantly because read-only access is low risk. The AI can work efficiently without constant approvals."

### Analytics Summary (1.5 minutes)
1. Click "Analytics" tab
2. Show dashboard

> "Here's the power of this system: Out of 7 actions, we blocked 3 dangerous ones (43%), required approval for 2 medium-risk ones (29%), and allowed 2 safe ones (29%). That's intelligent governance - stopping threats without slowing down your business."

3. Show CVSS severity breakdown

> "We use industry-standard CVSS scoring - the same system the US government uses for cybersecurity. Each action gets a risk score from 0-100, and we automatically block anything above your threshold."

### Closing (30 seconds)
> "This entire system is policy-driven. Your security team can create rules in plain English like 'Block all database writes to production containing PII' and the AI enforcement happens in real-time. No coding required."

**Time Check**: 5 minutes total

---

## Part 9: Troubleshooting

### Problem: "Can't see the + New Organization button"

**Solution**:
1. Make sure you're logged in as admin
2. Check that you're on the "Organizations" page (not "Users" or "Agents")
3. Try refreshing the page (press F5 or Ctrl+R)
4. If still missing, your account might not have admin permissions

### Problem: "Policy not blocking the action as expected"

**Solution**:
1. Check that all conditions match EXACTLY
   - Example: If policy says `environment = production`, make sure you typed "production" not "prod"
2. Check risk threshold - if policy threshold is 90 but action risk is 85, it won't match
3. Look at the policy order - policies are evaluated in order, and the first match wins
4. Try editing the policy and lowering the risk threshold

### Problem: "Don't see any actions in the Activity tab"

**Solution**:
1. Make sure you clicked "Submit Action" after filling in the form
2. Check the date filter at the top - change it to "Last 7 Days"
3. Refresh the page
4. Check that you're viewing the correct organization (TechCorp Demo Inc.)

### Problem: "Agent simulation keeps showing errors"

**Solution**:
1. Make sure all required fields are filled in (Action Type, Resource Type, Resource Name)
2. Check that the agent is assigned to TechCorp Demo Inc. organization
3. Try logging out and logging back in
4. Clear your browser cache (Ctrl+Shift+Delete)

### Problem: "Analytics dashboard shows no data"

**Solution**:
1. You need at least 1 action in the system first - go create some test actions
2. Wait 1-2 minutes for analytics to process
3. Refresh the page
4. Check that you're viewing the right time range (Last 30 Days)

### Problem: "Can't log in to the website"

**Solution**:
1. Double-check you're going to the right website: `https://pilot.owkai.app`
2. Make sure you're typing the email correctly: `admin@owkai.com`
3. Check for typos in your password
4. Try the "Forgot Password" link
5. Contact your OW-AI administrator

---

## Part 10: What You've Accomplished

After completing this guide, you have:

✅ **Created a realistic demo environment** with TechCorp Demo Inc.

✅ **Set up 5 demo users** representing different roles (CEO to Developer)

✅ **Configured 3 AI agents** with different risk levels (HIGH, MEDIUM, LOW)

✅ **Created 7 governance rules** covering common security scenarios:
   - 3 DENY rules (block dangerous actions)
   - 2 REQUIRE_APPROVAL rules (human oversight for risky actions)
   - 2 ALLOW rules (safe operations proceed automatically)

✅ **Tested 7 realistic scenarios** proving the system works:
   - 43% of high-risk actions blocked automatically
   - 29% of medium-risk actions require approval
   - 29% of low-risk actions allowed instantly

✅ **Generated analytics** showing governance effectiveness

✅ **Prepared a 5-minute live demo** you can show to clients

---

## Part 11: Next Steps

### For Your First Client Demo:
1. Practice the 5-minute demo script 2-3 times before the real meeting
2. Have the Analytics page open in one browser tab, Activity page in another
3. Show the live blocking action first (most impressive)
4. Keep the demo under 7 minutes to leave time for questions
5. Have the PDF report ready to send after the meeting

### To Customize for Your Client:
1. Change "TechCorp Demo Inc." to your client's actual company name
2. Use their real AWS account ID in the organization setup
3. Create rules that match their actual compliance requirements (SOX, HIPAA, etc.)
4. Add their specific use cases (e.g., "Block access to patient records" for healthcare)

### To Add More Advanced Features:
1. Set up email notifications when high-risk actions are blocked
2. Configure Slack alerts for pending approvals
3. Create custom dashboards for different departments
4. Schedule weekly governance reports to be emailed automatically

---

## Quick Reference Card

**Website**: https://pilot.owkai.app

**Admin Login**: admin@owkai.com

**Key Pages**:
- **Activity**: See what AI agents are doing
- **Agents**: Manage AI agents
- **Authorization Center**: Create governance rules
- **Analytics**: View blocking statistics
- **Organizations**: Manage client companies

**Policy Types**:
- 🔴 **DENY** = Block completely (high risk)
- 🟡 **REQUIRE_APPROVAL** = Ask human first (medium risk)
- 🟢 **ALLOW** = Let it happen (low risk)

**Risk Scores**:
- **0-30**: Low risk (usually allowed)
- **31-70**: Medium risk (usually requires approval)
- **71-100**: High risk (usually blocked)

**Demo Company Info**:
- **Name**: TechCorp Demo Inc.
- **Domain**: techcorp-demo.com
- **Compliance**: SOX, PCI-DSS, GDPR
- **Org ID**: (write yours here: _______________)

---

## Support

If you get stuck at any point:

1. **Check the Troubleshooting section** (Part 9) - most common issues are covered there
2. **Review the screenshots** - compare what you see to what you should see
3. **Start over** - sometimes it's faster to delete the demo org and recreate it
4. **Contact OW-AI support** - We're here to help!

---

**Congratulations!** You've successfully set up a complete OW-AI governance demo environment. You're now ready to show clients how AI agents can be controlled, monitored, and governed to protect their organization.

---

**Document Version**: 1.0 (Beginner-Friendly)
**Last Updated**: 2025-11-13
**For Technical Users**: See `CLIENT_DEMO_SETUP_GUIDE.md` (the original version with curl commands and API calls)
