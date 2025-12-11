---
Document ID: ASCEND-USER-001
Version: 1.0.0
Author: Ascend Engineering Team
Publisher: OW-kai Technologies Inc.
Classification: Enterprise Client Documentation
Last Updated: December 2025
Compliance: SOC 2 CC6.1/CC6.2, PCI-DSS 7.1/8.3, HIPAA 164.312, NIST 800-53 AC-2/SI-4
---

# OW-AI Platform - User Manual

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Roles and Permissions](#user-roles-and-permissions)
3. [Authorization Center](#authorization-center)
4. [Alert Management](#alert-management)
5. [Emergency Agent Suspension](#emergency-agent-suspension)
6. [Smart Rules Engine](#smart-rules-engine)
7. [User Account Management](#user-account-management)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Getting Started

### First Time Login

#### Accessing the Platform
1. Navigate to https://pilot.owkai.app in your web browser
2. You'll see the OW-AI Platform login screen
3. Enter your email address and password provided by your administrator
4. Click "Login" to access the platform

#### Initial Setup
Upon first login, you may be prompted to:
- Change your temporary password
- Set up multi-factor authentication (if enabled)
- Review and accept terms of service
- Complete your user profile information

#### Dashboard Overview
After logging in, you'll see the main dashboard which includes:
- **Summary Cards**: Quick overview of pending actions, alerts, and rules
- **Activity Feed**: Recent activity across the platform
- **Quick Actions**: Shortcuts to common tasks
- **Performance Metrics**: Key system performance indicators

### Navigation
The platform uses a sidebar navigation with the following main sections:
- **Dashboard**: Overview and quick access
- **Authorization Center**: Policy management and approval workflows
- **Alert Management**: Security alerts and incident response
- **Smart Rules**: Intelligent rule creation and management
- **User Management**: User accounts and permissions (Admin only)
- **Settings**: Personal and system configuration

## User Roles and Permissions

The OW-AI Platform implements a four-tier role-based access control system:

### Admin
**Full system access with all privileges**

**Capabilities:**
- Complete system administration
- Create, edit, and delete policies
- Manage all user accounts and roles
- Configure system settings
- Access all alerts and rules
- Approve any actions regardless of risk level
- View comprehensive audit logs
- Manage integrations and API keys

**Use Cases:**
- System administrators
- Security team leads
- Compliance officers

### Security Analyst
**Advanced security operations and analysis**

**Capabilities:**
- View and manage all alerts
- Acknowledge and escalate alerts
- Create and modify smart rules
- Approve medium and high-risk actions
- Generate security reports
- Access audit logs for investigations
- Configure alert correlation rules

**Cannot:**
- Manage user accounts
- Create or modify policies
- Access system configuration
- Approve critical-risk actions

**Use Cases:**
- SOC analysts
- Security engineers
- Incident response team members

### Approver
**Focused on workflow approval and review**

**Capabilities:**
- View approval workflows assigned to them
- Approve or deny pending actions
- View alerts (read-only)
- Access relevant audit information
- Add comments to approval decisions
- Set approval conditions and timeframes

**Cannot:**
- Create policies or rules
- Manage alerts (acknowledge/escalate)
- Access user management
- Modify system settings

**Use Cases:**
- Department managers
- Compliance reviewers
- Business stakeholders

### Viewer
**Read-only access for monitoring and reporting**

**Capabilities:**
- View dashboards and metrics
- Access reports and analytics
- View alert summaries (no action capabilities)
- Monitor rule performance
- Export permitted data

**Cannot:**
- Make any system changes
- Approve actions
- Acknowledge alerts
- Create or modify rules
- Access audit logs

**Use Cases:**
- Business users
- Executives
- Audit teams
- External stakeholders

## Authorization Center

The Authorization Center is the core policy management and approval workflow system.

### Policy Management

#### Viewing Policies
1. Navigate to **Authorization Center** → **Policies**
2. You'll see a list of all active policies with:
   - Policy name and description
   - Effect (Allow, Deny, Require Approval)
   - Creation date and author
   - Performance metrics

#### Creating a Policy from Natural Language

**For Admin and Security Analyst roles:**

1. Click **"Create New Policy"** button
2. Select **"Natural Language"** option
3. Enter your policy description in plain English:
   ```
   Example: "Block any file access to sensitive data without manager approval during off-hours"
   ```
4. Provide additional context:
   - **Environment**: Production, Staging, Development
   - **Department**: Engineering, Finance, HR, etc.
   - **Risk Level**: Low, Medium, High, Critical
5. Click **"Generate Policy"**
6. Review the generated policy structure:
   - **Conditions**: When the policy applies
   - **Actions**: What happens when triggered
   - **Approval Requirements**: Who needs to approve
7. Test the policy with sample scenarios
8. Click **"Save and Activate"**

#### Policy Testing
Before activating a policy:
1. Use the **"Test Policy"** feature
2. Input sample scenarios:
   - User context (role, department, location)
   - Action details (type, resource, time)
   - Environmental factors
3. Review the policy decision and reasoning
4. Adjust policy conditions if needed

### Approval Workflows

#### Viewing Pending Approvals
1. Navigate to **Authorization Center** → **Pending Actions**
2. Filter by:
   - **Risk Level**: Show only high-risk items
   - **Age**: Actions pending for specific timeframes
   - **Type**: File access, API calls, database queries, etc.
   - **Agent**: Specific AI agents or systems

#### Approving an Action

**For Approver, Security Analyst, and Admin roles:**

1. Click on a pending action to view details
2. Review the action information:
   - **Agent Details**: Which AI agent is requesting access
   - **Action Type**: What the agent wants to do
   - **Resource**: What data/system is being accessed
   - **Risk Assessment**: Automated risk score and reasoning
   - **Business Context**: Why this action is needed
3. Consider approval factors:
   - **Necessity**: Is this action required for business operations?
   - **Risk Level**: Does the risk align with business tolerance?
   - **Timing**: Is this an appropriate time for this action?
   - **Precedent**: Have similar actions been approved before?
4. Make your decision:
   - **Approve**: Allow the action to proceed
   - **Approve with Conditions**: Set limitations (time, monitoring, etc.)
   - **Reject**: Deny the action with explanation
5. Add comments explaining your decision
6. Set any additional conditions:
   - **Time Limit**: Action must complete within X hours
   - **Monitoring**: Enhanced logging and monitoring
   - **Notification**: Alert specific people when action completes
7. Click **"Submit Decision"**

#### Approval Conditions
When approving with conditions, you can set:
- **Time Constraints**: "Approve for next 2 hours only"
- **Monitoring Requirements**: "Enable enhanced logging"
- **Scope Limitations**: "Limit to specific file types"
- **Notification Rules**: "Alert security team when complete"

### Real-Time Policy Evaluation

#### Understanding Policy Decisions
When policies are evaluated, the system provides:
1. **Decision**: Allow, Deny, or Require Approval
2. **Risk Score**: 0-100 scale with breakdown by category
3. **Policy Matches**: Which policies triggered
4. **Reasoning**: Why this decision was made
5. **Recommendations**: Suggested next steps

#### Risk Score Breakdown
Risk scores are calculated across multiple dimensions:
- **Data Sensitivity** (0-100): How sensitive is the accessed data?
- **User Privilege** (0-100): What's the user's access level?
- **Time Context** (0-100): Is this a normal time for this action?
- **Environmental** (0-100): Production vs. development environment
- **Historical** (0-100): How common is this type of action?

## Alert Management

The Alert Management system provides intelligent threat detection and response automation.

### Viewing Alerts

#### Alert Dashboard
1. Navigate to **Alert Management** → **Dashboard**
2. View summary statistics:
   - Total active alerts
   - Alerts by severity level
   - Recent activity timeline
   - Response time metrics

#### Alert List
1. Go to **Alert Management** → **All Alerts**
2. Use filters to find specific alerts:
   - **Severity**: Critical, High, Medium, Low
   - **Status**: New, Acknowledged, In Progress, Resolved
   - **Time Range**: Last hour, day, week, month
   - **Source**: Which system generated the alert
   - **Assigned To**: Who is responsible for the alert

#### Alert Details
Click any alert to view:
- **Alert Summary**: What happened and when
- **Severity Justification**: Why this severity was assigned
- **Affected Systems**: What systems are involved
- **Evidence**: Supporting data and logs
- **Correlation**: Related alerts or patterns
- **Recommendations**: Suggested response actions

### Responding to Alerts

#### Acknowledging an Alert

**For Security Analyst and Admin roles:**

1. Open the alert you want to acknowledge
2. Click **"Acknowledge Alert"**
3. Add a comment explaining:
   - What you've reviewed
   - Your initial assessment
   - Planned next steps
4. Optionally set:
   - **Estimated Resolution Time**: When you expect to resolve
   - **Assigned To**: Transfer to another team member
   - **Priority**: Adjust if initial assessment was incorrect
5. Click **"Acknowledge"**

#### Escalating an Alert

**When an alert needs higher-level attention:**

1. Open the alert requiring escalation
2. Click **"Escalate Alert"**
3. Select escalation level:
   - **Internal**: Escalate to security manager
   - **External**: Involve external incident response
   - **Executive**: Notify C-level executives
4. Provide escalation reason:
   - **Severity Increase**: Threat is worse than initially assessed
   - **Resource Constraint**: Need additional resources
   - **Expertise Required**: Need specialized knowledge
   - **Policy Requirement**: Policy mandates escalation
5. Set urgency level:
   - **Immediate**: Response needed within 15 minutes
   - **High**: Response needed within 1 hour
   - **Normal**: Response needed within 4 hours
6. Add detailed explanation of why escalation is needed
7. Click **"Escalate"**

#### Resolving an Alert

**When investigation is complete:**

1. Open the resolved alert
2. Click **"Resolve Alert"**
3. Select resolution type:
   - **True Positive**: Real security incident
   - **False Positive**: Benign activity incorrectly flagged
   - **Inconclusive**: Unable to determine with certainty
   - **Duplicate**: Same issue as another alert
4. Document resolution:
   - **Root Cause**: What actually happened
   - **Actions Taken**: How you responded
   - **Lessons Learned**: What can be improved
   - **Prevention Measures**: How to prevent recurrence
5. Update any affected systems or processes
6. Click **"Resolve"**

### Alert Correlation
The system automatically correlates related alerts to help identify:
- **Attack Patterns**: Multiple alerts indicating coordinated attack
- **System Issues**: Multiple alerts from same source system
- **False Positive Clusters**: Groups of alerts that are typically benign

## Emergency Agent Suspension

The Emergency Agent Suspension feature provides immediate control over AI agents that exhibit dangerous, unauthorized, or anomalous behavior. This is a critical security control for enterprise compliance.

**Compliance**: SOC 2 CC6.2 (Incident Response), NIST SP 800-53 IR-4 (Incident Handling), HIPAA 164.308(a)(6) (Security Incident Procedures)

### Understanding Suspension Types

The platform provides a two-tier suspension architecture to match the severity of the situation:

#### Standard Suspension (Soft Stop)
**Use when:** Agent is behaving unexpectedly but not causing immediate harm

**What it does:**
- Marks the agent as suspended in the database
- Agent continues current operation to completion (graceful shutdown)
- Agent will not start new operations
- Reversible through the Agent Registry Management interface

**Example scenarios:**
- Agent is processing data slower than expected
- Agent is accessing more resources than planned
- Agent is behaving differently than documented

#### Emergency Suspension (Hard Stop / Kill-Switch)
**Use when:** Agent poses immediate security risk requiring instant termination

**What it does:**
- Sends real-time kill signal via AWS SNS to agent immediately
- Agent terminates current operation within milliseconds
- Agent receives block notification in all environments
- Creates audit trail for compliance review
- Triggers notification to security team (if configured)

**Example scenarios:**
- Agent is accessing unauthorized sensitive data
- Agent is exhibiting signs of prompt injection attack
- Agent is attempting to escalate privileges
- Agent is communicating with unauthorized external endpoints
- Agent behavior indicates potential compromise

### Accessing Emergency Suspension

#### From the Agent Registry Management Dashboard

**For Admin and Security Analyst roles:**

1. Navigate to **Dashboard** → **Agent Registry Management**
2. Locate the agent requiring suspension in the agent list
3. You'll see agent details including:
   - Agent name and ID
   - Current status (Active, Suspended, Blocked)
   - Last activity timestamp
   - Organization assignment

### Performing Emergency Suspension

#### Step-by-Step Instructions

1. **Locate the Emergency Button**
   - In the Agent Registry Management view, find the red **"🛑 Emergency"** button
   - This button is prominently displayed in RED to indicate critical action
   - Located in the agent action toolbar

2. **Click the Emergency Button**
   - A confirmation modal will appear
   - The modal is designed to prevent accidental suspensions

3. **Complete the Confirmation Flow**
   - **Reason Field** (Required): Enter a detailed explanation for the suspension
     - Include what behavior triggered the suspension
     - Reference any related alerts or incidents
     - Be specific for audit purposes
   - **Confirmation Input**: Type `SUSPEND` exactly as shown
     - Case-sensitive input prevents accidental clicks
     - This deliberate friction ensures intentional action

4. **Submit the Emergency Suspension**
   - Click **"Confirm Emergency Suspend"**
   - The system will:
     - Publish kill signal to SNS topic immediately
     - Mark agent as blocked in the database
     - Create audit log entry
     - Send notification to configured recipients (if enabled)

5. **Verify Suspension Success**
   - Agent status will change to **"Blocked"** (red indicator)
   - Confirmation toast notification will appear
   - Audit log will show the suspension event

### Post-Suspension Actions

#### Immediate Steps
1. **Document the Incident**: Create a security incident report
2. **Review Agent Logs**: Examine what the agent was doing before suspension
3. **Check Related Alerts**: Look for correlated security alerts
4. **Notify Stakeholders**: Inform relevant team members

#### Investigation
1. **Analyze Agent Behavior**: Review recent activity patterns
2. **Check for Compromise Indicators**: Look for signs of attack
3. **Review Audit Trail**: Examine the full agent history
4. **Document Findings**: Record investigation results

#### Resolution Options
After investigation, you can:
- **Reinstate Agent**: If the suspension was precautionary and agent is safe
- **Modify Agent Configuration**: If the agent needs restrictions
- **Permanently Block**: If the agent poses ongoing risk
- **Escalate**: If the incident requires external investigation

### Kill-Switch Notification System

When Emergency Suspension is triggered, the following notification chain executes:

1. **Immediate**: SNS message published to `ascend-agent-control` topic
2. **Within seconds**: All subscribed agent SDKs receive the block command
3. **Real-time**: Dashboard notifications update (if notification integration is enabled)
4. **Async**: Email/webhook notifications sent to configured recipients

#### Notification Event Types
- `agent.blocked` - Emergency suspension was triggered
- `agent.suspended` - Standard suspension was initiated
- `agent.quarantined` - Agent was isolated for investigation
- `agent.unblocked` - Agent was reinstated after review

### Permissions Required

| Action | Admin | Security Analyst | Approver | Viewer |
|--------|-------|------------------|----------|--------|
| View Agent Status | ✅ | ✅ | ✅ | ✅ |
| Standard Suspension | ✅ | ✅ | ❌ | ❌ |
| Emergency Suspension | ✅ | ✅ | ❌ | ❌ |
| Reinstate Agent | ✅ | ✅ | ❌ | ❌ |
| View Audit Logs | ✅ | ✅ | ❌ | ❌ |

### Best Practices

#### When to Use Emergency Suspension
- **DO** use for active security threats
- **DO** use when agent is accessing prohibited resources
- **DO** use when you observe anomalous behavior indicating compromise
- **DON'T** use for routine maintenance (use standard suspension)
- **DON'T** use for performance issues (use standard suspension)
- **DON'T** use without documenting the reason

#### Documentation Requirements
For compliance purposes, always record:
- The specific behavior that triggered the suspension
- Any related alert IDs or incident numbers
- The time you first observed the issue
- Actions taken before suspension (if any)

#### Response Time Guidelines
- **Critical threats**: Suspend immediately, document after
- **Suspicious behavior**: Document briefly, then suspend
- **Uncertain situations**: Gather evidence quickly, escalate if needed

### Troubleshooting Emergency Suspension

#### Problem: Emergency button is not visible
**Possible causes:**
- You don't have Admin or Security Analyst role
- Agent is already blocked/suspended
- Page needs to be refreshed

**Solution:** Verify your role permissions with your administrator

#### Problem: Suspension completed but agent is still running
**Possible causes:**
- Agent SDK not polling for control messages
- Network connectivity issues
- Agent is operating in offline mode

**Solution:** Contact your DevOps team to manually terminate the agent process

#### Problem: Cannot type SUSPEND in confirmation
**Possible causes:**
- Caps lock is on (input is case-sensitive)
- Browser autocomplete is interfering

**Solution:** Ensure exact case: `SUSPEND` (all uppercase)

## Smart Rules Engine

The Smart Rules Engine provides AI-powered rule creation and optimization.

### Creating Rules

#### Natural Language Rule Creation

**For Security Analyst and Admin roles:**

1. Navigate to **Smart Rules** → **Create Rule**
2. Select **"Natural Language"** option
3. Describe what you want to detect:
   ```
   Examples:
   - "Alert me when any user accesses more than 100 files in 5 minutes"
   - "Block API calls from suspicious geographic locations"
   - "Notify security team when database queries access customer PII"
   ```
4. Set rule parameters:
   - **Severity**: How important is this rule?
   - **Enabled**: Should the rule be active immediately?
   - **Environment**: Where should this rule apply?
5. Review the generated rule:
   - **Condition**: When the rule triggers
   - **Action**: What happens when triggered
   - **Confidence Score**: How confident the AI is in this rule
6. Test the rule with sample data
7. Click **"Create Rule"**

#### Manual Rule Creation

**For advanced users:**

1. Select **"Manual Creation"** option
2. Define rule conditions using the rule builder:
   - **Data Sources**: What systems to monitor
   - **Triggers**: What events activate the rule
   - **Thresholds**: Numerical limits (time, count, size)
   - **Context**: User, time, location factors
3. Specify actions:
   - **Alert**: Generate an alert
   - **Block**: Prevent the action
   - **Monitor**: Increase logging/monitoring
   - **Approve**: Require manual approval
4. Set rule metadata:
   - **Name and Description**
   - **Severity Level**
   - **Notification Recipients**
5. Save and test the rule

### Managing Rules

#### Rule Performance Analytics
1. Go to **Smart Rules** → **Analytics**
2. View performance metrics:
   - **Trigger Frequency**: How often rules activate
   - **False Positive Rate**: Percentage of incorrect alerts
   - **Effectiveness Score**: Overall rule performance
   - **Response Time**: How quickly alerts are handled

#### Optimizing Rules
The system provides AI-powered optimization suggestions:
1. Navigate to **Smart Rules** → **Optimization**
2. Review suggestions for each rule:
   - **Threshold Adjustments**: Fine-tune numerical limits
   - **Condition Refinements**: Improve trigger accuracy
   - **Performance Improvements**: Reduce resource usage
3. Apply recommended optimizations
4. Monitor performance changes

#### A/B Testing Rules
**For testing rule improvements:**

1. Select a rule to test
2. Click **"Create A/B Test"**
3. Define test parameters:
   - **Duration**: How long to run the test
   - **Traffic Split**: Percentage of events for each version
   - **Success Metrics**: How to measure improvement
4. Create the test variant (modified rule)
5. Start the test and monitor results
6. Apply the winning version

### Rule Templates
The platform includes pre-built rule templates for common scenarios:

#### Data Protection Templates
- **PII Access Monitoring**: Track access to personal data
- **Data Exfiltration Detection**: Identify unusual data transfers
- **File Access Anomalies**: Detect abnormal file access patterns

#### Security Templates
- **Brute Force Detection**: Identify repeated failed login attempts
- **Privilege Escalation**: Monitor for unauthorized privilege changes
- **Suspicious Network Activity**: Detect unusual network patterns

#### Compliance Templates
- **SOX Compliance**: Rules for financial data access
- **HIPAA Compliance**: Healthcare data protection rules
- **GDPR Compliance**: EU data protection requirements

## User Account Management

### Personal Profile

#### Updating Your Profile
1. Click your name in the top-right corner
2. Select **"Profile Settings"**
3. Update your information:
   - **Name and Contact Information**
   - **Department and Role**
   - **Notification Preferences**
   - **Time Zone and Language**
4. Click **"Save Changes"**

#### Changing Your Password
1. Go to **Profile Settings** → **Security**
2. Click **"Change Password"**
3. Enter your current password
4. Enter your new password (meeting security requirements)
5. Confirm your new password
6. Click **"Update Password"**

#### Multi-Factor Authentication (MFA)
**If enabled by your organization:**

1. Go to **Profile Settings** → **Security**
2. Click **"Setup MFA"**
3. Choose your preferred method:
   - **Authenticator App**: Use Google Authenticator, Authy, etc.
   - **SMS**: Receive codes via text message
   - **Email**: Receive codes via email
4. Follow the setup instructions
5. Verify with a test code
6. Save backup codes in a secure location

### Session Management

#### Active Sessions
1. Go to **Profile Settings** → **Sessions**
2. View all active sessions:
   - **Device and Browser**: What you're logged in from
   - **Location**: Geographic location (if available)
   - **Last Activity**: When you last used that session
   - **IP Address**: Network identifier
3. Revoke suspicious or unused sessions

#### Session Security
- Sessions automatically expire after 30 minutes of inactivity
- You'll be warned 5 minutes before expiration
- Closing your browser ends the session
- Logging out from one device doesn't affect others

### Notification Preferences

#### Alert Notifications
Configure how you receive alert notifications:
- **Email**: Immediate, daily digest, or weekly summary
- **In-App**: Browser notifications when logged in
- **Mobile**: Push notifications (if mobile app is available)
- **Slack/Teams**: Integration with collaboration tools

#### Approval Notifications
Set preferences for approval workflow notifications:
- **Assigned Actions**: When actions are assigned to you
- **Escalated Items**: When items are escalated to your level
- **Deadline Reminders**: Approaching approval deadlines
- **Decision Updates**: When decisions are made on items you've handled

## Troubleshooting

### Common Login Issues

#### Problem: Cannot log in with correct credentials
**Possible Solutions:**
1. **Check Caps Lock**: Ensure caps lock is off
2. **Clear Browser Cache**: Clear cookies and cached data
3. **Try Incognito Mode**: Rule out browser extension issues
4. **Check Account Status**: Your account may be locked or suspended
5. **Contact Administrator**: Your password may have been reset

#### Problem: Page won't load or shows error
**Possible Solutions:**
1. **Refresh the Page**: Press F5 or Ctrl+R
2. **Check Internet Connection**: Ensure you have connectivity
3. **Try Different Browser**: Rule out browser-specific issues
4. **Disable Ad Blockers**: Some extensions can interfere
5. **Check System Status**: Visit the status page or contact support

#### Problem: Session keeps expiring
**Possible Solutions:**
1. **Check System Clock**: Ensure your computer's time is correct
2. **Stay Active**: Move your mouse or click periodically
3. **Close Extra Tabs**: Multiple tabs can cause session conflicts
4. **Check Network**: Unstable connections can cause timeouts

### Performance Issues

#### Problem: Platform is running slowly
**Possible Solutions:**
1. **Check Network Speed**: Run a speed test
2. **Close Unused Tabs**: Free up browser memory
3. **Update Browser**: Ensure you're using a supported version
4. **Clear Cache**: Remove stored data that may be corrupted
5. **Check System Resources**: Ensure your computer isn't overloaded

#### Problem: Large datasets won't load
**Possible Solutions:**
1. **Use Filters**: Narrow down the data you're viewing
2. **Reduce Time Range**: Look at smaller time periods
3. **Export Data**: Download for offline analysis
4. **Contact Support**: May need to increase limits

### Feature-Specific Issues

#### Problem: Policy evaluation is slow
**This may indicate:**
- High system load
- Complex policy conditions
- Network latency issues

**Solutions:**
- Simplify policy conditions
- Use policy caching
- Contact administrator about performance

#### Problem: Alerts not appearing
**Check:**
- Alert filters and time ranges
- Your role permissions
- Notification settings
- System connectivity

#### Problem: Cannot approve actions
**Verify:**
- You have appropriate role permissions
- The action hasn't already been processed
- Your session hasn't expired
- CSRF protection isn't blocking the request

### Browser Compatibility

#### Supported Browsers
- **Chrome**: Version 100+ (recommended)
- **Firefox**: Version 98+
- **Safari**: Version 15+
- **Edge**: Version 100+

#### Unsupported Browsers
- Internet Explorer (any version)
- Chrome/Firefox versions older than listed above
- Mobile browsers (limited support)

#### Browser Configuration
For optimal performance:
- Enable JavaScript
- Allow cookies from pilot.owkai.app
- Disable ad blockers for the site
- Keep browser updated

## FAQ

### General Questions

**Q: How long do JWT tokens last?**
A: Access tokens expire after 30 minutes. They automatically refresh before expiring if you're actively using the platform.

**Q: Can I have multiple roles?**
A: No, each user is assigned one role. However, roles are hierarchical - higher roles include permissions of lower roles.

**Q: What happens if I forget my password?**
A: Use the "Forgot Password" link on the login page. You'll receive a reset link via email.

**Q: Can I use the platform on mobile devices?**
A: The platform is optimized for desktop use. Mobile access is limited but functional for viewing dashboards and basic operations.

**Q: How often is data backed up?**
A: The platform creates automated backups daily with 30-day retention. Database backups occur every 6 hours.

### Security Questions

**Q: Is my data encrypted?**
A: Yes, all data is encrypted in transit (TLS 1.3) and at rest (AES-256). Database connections use SSL encryption.

**Q: Who can see my actions in the platform?**
A: All actions are logged for audit purposes. Administrators can view audit logs, but regular user actions are only visible to users with audit permissions.

**Q: What should I do if I suspect my account is compromised?**
A: Immediately change your password, revoke all active sessions, and contact your administrator. Review recent activity in your profile.

**Q: Can I use the same password as other systems?**
A: It's strongly recommended to use a unique password. The platform enforces complex password requirements and checks against common breaches.

### Approval Workflow Questions

**Q: How long do I have to approve an action?**
A: Default approval timeouts are:
- Low risk: 24 hours
- Medium risk: 4 hours
- High risk: 2 hours
- Critical risk: 30 minutes

**Q: What happens if I don't approve in time?**
A: Actions are automatically escalated to the next approval level or denied based on policy configuration.

**Q: Can I delegate my approval authority?**
A: Yes, you can temporarily delegate to another user of equal or higher role through the user settings.

**Q: Can I see who else has approved an action?**
A: Yes, the approval chain is visible in the action details, showing all approvers and their decisions.

### Alert Management Questions

**Q: Why am I not receiving alert notifications?**
A: Check your notification preferences in Profile Settings. Ensure your email address is correct and check spam folders.

**Q: Can I create custom alert types?**
A: Custom alerts can be created through the Smart Rules engine using natural language or manual configuration.

**Q: What's the difference between acknowledging and resolving an alert?**
A: Acknowledging means you've seen the alert and are investigating. Resolving means the investigation is complete and the issue is addressed.

**Q: Can alerts be automatically resolved?**
A: Some alerts can be configured for automatic resolution based on rules, but most require human review for security reasons.

### Smart Rules Questions

**Q: How accurate is the natural language rule creation?**
A: The AI typically achieves 85-90% accuracy in converting natural language to functional rules. Always review and test generated rules.

**Q: Can I modify AI-generated rules?**
A: Yes, all rules can be manually edited after creation to fine-tune conditions and actions.

**Q: How often should I review rule performance?**
A: Review rule analytics weekly for high-impact rules, monthly for standard rules. The system will also proactively suggest optimizations.

**Q: Can rules trigger other rules?**
A: Yes, rules can create cascading effects. However, the system includes loop detection to prevent infinite chains.

For additional support or questions not covered in this manual, contact your system administrator or the OW-AI Platform support team.