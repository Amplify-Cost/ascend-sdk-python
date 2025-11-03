# OW-AI User Guide

## Getting Started

### Accessing the Platform

1. Navigate to `https://pilot.owkai.app`
2. Log in with your credentials
3. View the main dashboard

### Dashboard Overview

The dashboard provides:
- **Agent Activity**: Live feed of AI agent actions
- **Risk Metrics**: Current risk levels and trends
- **Pending Approvals**: Actions awaiting review
- **Active Alerts**: Security alerts

## Core Features

### 1. Agent Action Management

#### Viewing Actions

1. Click **Agent Control** in navigation
2. Filter by status, risk level, date range
3. Click action to view details

#### Approving/Denying Actions

1. Click on an action
2. Review details and risk assessment
3. Click **Approve** or **Deny**
4. Add comments
5. Submit

### 2. Smart Rules Engine

#### Creating a Rule

1. Navigate to **Smart Rules**
2. Click **Create New Rule**
3. Fill in name, description, condition, action
4. Set priority (1-10)
5. Click **Save**

#### Rule Examples

**Block production deletions:**
```sql
action_type == 'database_write' 
AND operation ILIKE '%DELETE%' 
AND target_system ILIKE '%production%'
```

**Require approval for high-risk:**
```sql
risk_score > 80
```

### 3. Alert Management

#### Viewing Alerts

1. Navigate to **Alerts**
2. Filter by status and severity
3. Click to view details

#### Responding to Alerts

1. **Acknowledge**: Mark as seen
2. **Resolve**: Close with notes
3. **Escalate**: Forward to team

### 4. Analytics & Reporting

View metrics:
- Approval Rate
- Response Time
- Risk Distribution
- Rule Effectiveness

## Common Workflows

### Morning Security Review

1. Log in and check dashboard
2. Review overnight alerts
3. Acknowledge critical alerts
4. Review pending high-risk actions
5. Approve/deny based on policy

### Creating Access Control Policy

1. Navigate to Smart Rules
2. Create rule for admin access
3. Set condition: `privilege_level == 'admin'`
4. Set action: `require_approval`
5. Enable and test

## Keyboard Shortcuts

- `Ctrl/Cmd + K`: Global search
- `A`: Approve selected action
- `D`: Deny selected action

## Troubleshooting

### Can't Log In
- Verify credentials
- Try password reset
- Contact admin

### Action Won't Approve
- Check permissions
- Ensure required fields filled
- Verify not already processed

## Getting Help

- **In-App Help**: Click `?` icon
- **Support**: support@owkai.com
