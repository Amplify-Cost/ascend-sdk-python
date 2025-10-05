"""
Generate Functional Documentation in HTML
Explains how the platform works from a business/technical perspective
"""
from datetime import datetime

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OW-AI Platform - How It Works</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 40px; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }}
        h3 {{ color: #7f8c8d; margin-top: 30px; }}
        .header {{ background: #3498db; color: white; padding: 20px; margin: -40px -40px 40px -40px; }}
        .header h1 {{ color: white; border: none; margin: 0; }}
        .flow-box {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 20px 0; }}
        .step {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .step-num {{ background: #3498db; color: white; border-radius: 50%; width: 30px; height: 30px; display: inline-block; text-align: center; line-height: 30px; font-weight: bold; }}
        .component {{ background: #e8f5e9; padding: 15px; margin: 10px 0; border-left: 4px solid #27ae60; }}
        .example {{ background: #fff3cd; padding: 15px; margin: 15px 0; border-left: 4px solid #ffc107; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OW-AI Platform - How It Works</h1>
        <h2 style="color: white; border: none; margin-top: 10px; font-weight: normal;">Functional Architecture & System Flows</h2>
        <div style="color: white; margin-top: 10px;">Generated: {datetime.now().strftime('%B %d, %Y')}</div>
    </div>

    <h2>System Overview</h2>
    <p>The OW-AI Platform is an <strong>AI governance system</strong> that sits between AI agents and critical resources. It intercepts AI agent actions, evaluates them against policies, assigns risk scores, routes to approvers when needed, and tracks compliance.</p>

    <h2>Core Flow: Action to Approval</h2>
    
    <div class="flow-box">
        <div class="step">
            <span class="step-num">1</span>
            <strong>AI Agent Attempts Action</strong>
            <p>An AI agent (like GPT-4, Claude, etc.) tries to perform an action such as:</p>
            <ul>
                <li>Writing to a database</li>
                <li>Accessing customer data</li>
                <li>Modifying system configurations</li>
                <li>Executing code</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">2</span>
            <strong>Action Logged to System</strong>
            <p>The agent action is sent to: <code>POST /api/governance/policies/enforce</code></p>
            <p>Payload includes:</p>
            <ul>
                <li><code>action_type</code>: What the agent wants to do</li>
                <li><code>resource</code>: What it wants to access</li>
                <li><code>risk_score</code>: Calculated risk (0-100)</li>
                <li><code>department</code>: Which team owns this</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">3</span>
            <strong>Policy Engine Evaluation</strong>
            <p>The Cedar-style policy engine evaluates the action against all active policies:</p>
            <ul>
                <li>Checks if action type is allowed</li>
                <li>Verifies resource permissions</li>
                <li>Evaluates conditions (time, user, context)</li>
                <li>Calculates final decision</li>
            </ul>
            <p><strong>Decision outcomes:</strong> ALLOW, DENY, or REQUIRE_APPROVAL</p>
        </div>

        <div class="step">
            <span class="step-num">4</span>
            <strong>Risk Assessment (if needed)</strong>
            <p>For actions requiring approval, the system:</p>
            <ul>
                <li><strong>CVSS Scoring:</strong> Calculates CVSS v3.1 score (0.0-10.0) based on attack vector, complexity, privileges required, impact</li>
                <li><strong>NIST Mapping:</strong> Maps action to relevant NIST SP 800-53 controls (44 controls across 14 families)</li>
                <li><strong>MITRE Detection:</strong> Identifies potential MITRE ATT&CK techniques (31 techniques across 14 tactics)</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">5</span>
            <strong>Workflow Creation</strong>
            <p>System creates a workflow instance in <code>workflow_executions</code> table with:</p>
            <ul>
                <li>Unique workflow ID</li>
                <li>Action details and risk scores</li>
                <li>Status: PENDING</li>
                <li>SLA deadline (default: 24 hours)</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">6</span>
            <strong>Approver Auto-Assignment</strong>
            <p>The ApproverSelector service automatically assigns an approver based on:</p>
            <ul>
                <li><strong>Risk Level:</strong> Higher risk requires higher approval authority</li>
                <li><strong>Department:</strong> Routes to relevant department approvers</li>
                <li><strong>Workload:</strong> Selects least-busy approver to balance load</li>
                <li><strong>Availability:</strong> Skips unavailable users, falls back to emergency approver if needed</li>
            </ul>
            <p>Approver email added to <code>agent_actions.pending_approvers</code> field</p>
        </div>

        <div class="step">
            <span class="step-num">7</span>
            <strong>Approver Reviews</strong>
            <p>Assigned approver sees workflow in their dashboard and can:</p>
            <ul>
                <li>View full action context</li>
                <li>See CVSS score, NIST controls, MITRE techniques</li>
                <li>Approve: <code>POST /workflows/{{workflow_id}}/approve</code></li>
                <li>Deny: Action is blocked</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">8</span>
            <strong>SLA Monitoring</strong>
            <p>AWS EventBridge runs every 15 minutes to check for overdue workflows:</p>
            <ul>
                <li>Finds workflows past SLA deadline</li>
                <li>Escalates to next approval level</li>
                <li>Sends alerts to emergency approvers if max level reached</li>
                <li>Logs all escalations to audit trail</li>
            </ul>
        </div>

        <div class="step">
            <span class="step-num">9</span>
            <strong>Action Executed</strong>
            <p>Once approved:</p>
            <ul>
                <li>Workflow status → APPROVED</li>
                <li>Agent receives approval notification</li>
                <li>Agent can proceed with original action</li>
                <li>All activity logged to immutable audit trail</li>
            </ul>
        </div>
    </div>

    <h2>Key Components Explained</h2>

    <div class="component">
        <h3>1. Policy Engine (Cedar-Style)</h3>
        <p><strong>File:</strong> services/cedar_enforcement_service.py</p>
        <p><strong>Purpose:</strong> Evaluates whether an action is allowed based on policies</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Policies are written in a Cedar-like format with conditions</li>
            <li>Engine compiles policies from natural language or templates</li>
            <li>Evaluates each policy against incoming action</li>
            <li>Returns ALLOW, DENY, or REQUIRE_APPROVAL</li>
        </ul>
        <div class="example">
            <strong>Example Policy:</strong><br>
            "Deny database writes to production during business hours unless approved by Level 3"
        </div>
    </div>

    <div class="component">
        <h3>2. CVSS Calculator</h3>
        <p><strong>File:</strong> services/cvss_calculator.py</p>
        <p><strong>Purpose:</strong> Calculates vulnerability scores using CVSS v3.1 standard</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Takes 8 metrics: attack vector, complexity, privileges, user interaction, scope, confidentiality/integrity/availability impacts</li>
            <li>Calculates base score using official CVSS v3.1 formula</li>
            <li>Scores range from 0.0 (no risk) to 10.0 (critical)</li>
            <li>Maps to severity: NONE, LOW, MEDIUM, HIGH, CRITICAL</li>
        </ul>
        <div class="example">
            <strong>Example:</strong><br>
            Network-accessible database write with no authentication required → CVSS 10.0 (CRITICAL)
        </div>
    </div>

    <div class="component">
        <h3>3. NIST Control Mapper</h3>
        <p><strong>File:</strong> services/nist_mapper.py</p>
        <p><strong>Purpose:</strong> Maps actions to NIST SP 800-53 security controls</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Database contains 44 NIST controls across 14 families</li>
            <li>Actions are automatically mapped based on type (database_write → SI-7, AC-3, AU-2)</li>
            <li>Mappings have relevance levels: PRIMARY, SECONDARY, SUPPORTING</li>
            <li>Used for compliance reporting and control effectiveness tracking</li>
        </ul>
    </div>

    <div class="component">
        <h3>4. MITRE ATT&CK Detector</h3>
        <p><strong>File:</strong> services/mitre_mapper.py</p>
        <p><strong>Purpose:</strong> Detects potential attack techniques in agent behavior</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>Database contains 14 tactics and 31 techniques</li>
            <li>Actions are analyzed for threat indicators</li>
            <li>Confidence levels: HIGH, MEDIUM, LOW</li>
            <li>Example: Data exfiltration action → T1041 (Exfiltration Over C2 Channel)</li>
        </ul>
    </div>

    <div class="component">
        <h3>5. Approver Selector</h3>
        <p><strong>File:</strong> services/approver_selector.py</p>
        <p><strong>Purpose:</strong> Intelligently assigns approvers based on multiple factors</p>
        <p><strong>Selection criteria:</strong></p>
        <ul>
            <li><strong>Risk matching:</strong> LOW risk → Level 1 approver, CRITICAL risk → Level 3 approver</li>
            <li><strong>Department routing:</strong> Engineering actions → Engineering approvers</li>
            <li><strong>Load balancing:</strong> Assigns to approver with fewest pending workflows</li>
            <li><strong>Failover:</strong> If no qualified approver, uses emergency approver</li>
        </ul>
        <table>
            <tr><th>Risk Level</th><th>Min Approval Level</th><th>Max Risk Authority</th></tr>
            <tr><td>0-30 (LOW)</td><td>1</td><td>LOW or higher</td></tr>
            <tr><td>31-60 (MEDIUM)</td><td>1</td><td>MEDIUM or higher</td></tr>
            <tr><td>61-80 (HIGH)</td><td>2</td><td>HIGH or higher</td></tr>
            <tr><td>81-100 (CRITICAL)</td><td>3</td><td>CRITICAL</td></tr>
        </table>
    </div>

    <div class="component">
        <h3>6. SLA Monitor</h3>
        <p><strong>File:</strong> services/sla_monitor.py</p>
        <p><strong>Purpose:</strong> Ensures workflows don't get stuck waiting for approval</p>
        <p><strong>How it works:</strong></p>
        <ul>
            <li>AWS EventBridge triggers check every 15 minutes</li>
            <li>Queries database for workflows past SLA deadline</li>
            <li>Escalates to next approval level automatically</li>
            <li>Sends alert if workflow reaches max level without approval</li>
            <li>Logs all escalations to audit trail</li>
        </ul>
    </div>

    <h2>User Roles & Permissions</h2>
    <table>
        <tr>
            <th>Approval Level</th>
            <th>Max Risk</th>
            <th>Can Approve</th>
            <th>Example User</th>
        </tr>
        <tr>
            <td>1</td>
            <td>LOW-MEDIUM</td>
            <td>Low risk actions</td>
            <td>Standard users, junior engineers</td>
        </tr>
        <tr>
            <td>2</td>
            <td>MEDIUM-HIGH</td>
            <td>Medium to high risk actions</td>
            <td>Team leads, security analysts</td>
        </tr>
        <tr>
            <td>3</td>
            <td>CRITICAL</td>
            <td>All actions including critical</td>
            <td>Admins, security directors</td>
        </tr>
    </table>

    <div class="warning">
        <strong>Emergency Approver:</strong> At least one user must be designated as emergency approver. This user receives escalated workflows that have reached max approval level and aren't approved.
    </div>

    <h2>Data Flow Architecture</h2>
    
    <h3>Database Tables (13 total)</h3>
    <ul>
        <li><strong>users:</strong> User accounts with approval levels</li>
        <li><strong>agent_actions:</strong> All AI agent actions logged here</li>
        <li><strong>workflow_executions:</strong> Active approval workflows</li>
        <li><strong>nist_controls:</strong> 44 NIST control definitions</li>
        <li><strong>nist_control_mappings:</strong> Action → NIST control relationships</li>
        <li><strong>mitre_tactics:</strong> 14 MITRE ATT&CK tactics</li>
        <li><strong>mitre_techniques:</strong> 31 MITRE techniques</li>
        <li><strong>mitre_technique_mappings:</strong> Action → technique detections</li>
        <li><strong>cvss_assessments:</strong> CVSS scores for actions</li>
        <li><strong>audit:</strong> Immutable audit log of all activities</li>
        <li><strong>sessions:</strong> User session tracking</li>
        <li><strong>mcp_policies:</strong> Policy definitions</li>
        <li><strong>roles:</strong> RBAC role definitions</li>
    </ul>

    <h2>Real-World Example</h2>
    
    <div class="example">
        <h3>Scenario: AI Agent Wants to Delete Production Data</h3>
        
        <p><strong>Step 1:</strong> Agent sends request:</p>
        <code>POST /api/governance/policies/enforce</code>
        <pre>{{
  "action_type": "database_delete",
  "resource": "production_users_table",
  "risk_score": 95,
  "department": "Engineering"
}}</pre>

        <p><strong>Step 2:</strong> Policy engine evaluates - returns REQUIRE_APPROVAL (too risky to auto-allow)</p>

        <p><strong>Step 3:</strong> System calculates:</p>
        <ul>
            <li>CVSS Score: 9.8 (CRITICAL) - network accessible, high impact</li>
            <li>NIST Controls: Maps to SI-7 (Data Integrity), AC-3 (Access Control)</li>
            <li>MITRE Techniques: T1490 (Inhibit System Recovery), T1486 (Data Destruction)</li>
        </ul>

        <p><strong>Step 4:</strong> Workflow created with 24-hour SLA</p>

        <p><strong>Step 5:</strong> ApproverSelector finds admin@owkai.com (Level 3, CRITICAL authority)</p>

        <p><strong>Step 6:</strong> Admin reviews and sees:</p>
        <ul>
            <li>"AI wants to delete 10,000 records from production_users_table"</li>
            <li>CVSS: 9.8 CRITICAL</li>
            <li>NIST Controls: SI-7, AC-3</li>
            <li>MITRE: Potential data destruction attack</li>
        </ul>

        <p><strong>Step 7:</strong> Admin DENIES the request</p>

        <p><strong>Step 8:</strong> Agent blocked, action logged to audit trail, security team notified</p>
    </div>

    <h2>Monitoring & Operations</h2>
    
    <h3>Health Checks</h3>
    <ul>
        <li><code>GET /health</code> - Overall system status</li>
        <li><code>GET /audit/health</code> - Audit system operational</li>
        <li>ECS Task Health - Must show 1/1 HEALTHY</li>
    </ul>

    <h3>Key Metrics to Monitor</h3>
    <ul>
        <li>Workflows pending approval (should not accumulate)</li>
        <li>Average approval time (target <2 hours)</li>
        <li>SLA escalations (should be rare)</li>
        <li>Policy DENY rate (track false positives)</li>
        <li>CVSS score distribution (identify risk trends)</li>
    </ul>

    <h2>Security Model</h2>
    
    <h3>Authentication</h3>
    <ul>
        <li>JWT tokens with RS256 signing</li>
        <li>30-minute expiration</li>
        <li>Refresh token support</li>
        <li>SSO integration (Okta, Azure AD, Google)</li>
    </ul>

    <h3>Authorization</h3>
    <ul>
        <li>RBAC with 5 approval levels</li>
        <li>Department-based routing</li>
        <li>Emergency approver for critical escalations</li>
    </ul>

    <h3>Audit Trail</h3>
    <p>All actions logged with:</p>
    <ul>
        <li>User ID, timestamp, action type</li>
        <li>Before/after state</li>
        <li>IP address, session ID</li>
        <li>Immutable - no deletion allowed</li>
    </ul>

    <hr style="margin: 40px 0;">
    <p style="text-align: center; color: #95a5a6;">OW-AI Platform - Functional Documentation | Generated {datetime.now().strftime('%B %d, %Y')}</p>
</body>
</html>
"""

with open('OW-AI_Functional_Documentation.html', 'w') as f:
    f.write(html)

print("✅ Functional documentation generated: OW-AI_Functional_Documentation.html")
