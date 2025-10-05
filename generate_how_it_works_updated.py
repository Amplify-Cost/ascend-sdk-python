from datetime import datetime

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OW-AI Platform - How It Works</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f5f7fa; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; margin: -40px -40px 40px -40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header h1 {{ color: white; border: none; margin: 0; font-size: 2.5em; }}
        h2 {{ color: #2c3e50; margin-top: 40px; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        h3 {{ color: #34495e; margin-top: 25px; }}
        .section {{ background: white; padding: 25px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .flow {{ background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 15px 0; }}
        .component {{ background: #f3e5f5; border-left: 4px solid #9c27b0; padding: 15px; margin: 15px 0; }}
        .code {{ background: #263238; color: #aed581; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: 'Courier New', monospace; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #667eea; color: white; }}
        .highlight {{ background: #fff9c4; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>How OW-AI Platform Works</h1>
        <p style="margin-top: 10px; font-size: 1.2em;">Enterprise AI Governance Architecture</p>
        <div style="margin-top: 10px; opacity: 0.9;">Last Updated: {datetime.now().strftime('%B %d, %Y')}</div>
    </div>

    <div class="section">
        <h2>Architecture Overview</h2>
        <p>OW-AI is an enterprise AI governance platform that provides <span class="highlight">real-time authorization, policy enforcement, and audit trails</span> for all AI agent and MCP server actions.</p>
        
        <div class="flow">
            <strong>Request Flow:</strong><br>
            User/Agent → Policy Check → Risk Assessment → Approval Workflow → Execution → Audit Log
        </div>
    </div>

    <div class="section">
        <h2>Core Components</h2>

        <div class="component">
            <h3>1. Unified Policy Engine (Cedar-based)</h3>
            <p><strong>Location:</strong> <code>services/cedar_enforcement_service.py</code></p>
            <p><strong>Purpose:</strong> Single enforcement point for ALL actions (agent + MCP)</p>
            
            <div class="code">
policy_decision = enforcement_engine.evaluate(
    principal="ai_agent:gpt4" | "mcp_server:filesystem",
    action="write" | "delete" | "execute",
    resource="database:production" | "mcp:server:*",
    context={{"user": "admin@company.com"}}
)
# Returns: ALLOW | DENY | REQUIRE_APPROVAL
            </div>
            
            <p><strong>Features:</strong></p>
            <ul>
                <li>Natural language policy compilation</li>
                <li>Rich condition evaluation (AND/OR logic)</li>
                <li>Caching for performance</li>
                <li>Input validation and error handling</li>
            </ul>
        </div>

        <div class="component">
            <h3>2. Governance Workflows</h3>
            <p><strong>Location:</strong> <code>routes/unified_governance_routes.py</code></p>
            <p><strong>Purpose:</strong> Multi-stage approval workflows with SLA tracking</p>
            
            <table>
                <tr><th>Stage</th><th>Role Required</th><th>SLA</th></tr>
                <tr><td>Stage 1</td><td>Team Lead</td><td>2 hours</td></tr>
                <tr><td>Stage 2</td><td>Operations</td><td>4 hours</td></tr>
                <tr><td>Stage 3</td><td>Executive</td><td>24 hours</td></tr>
            </table>
            
            <p><strong>Smart Escalation:</strong> Automatically escalates overdue approvals</p>
        </div>

        <div class="component">
            <h3>3. Smart Rules Engine</h3>
            <p><strong>Location:</strong> <code>routes/smart_rules_routes.py</code></p>
            <p><strong>Purpose:</strong> Pattern detection and automated policy suggestions</p>
            
            <ul>
                <li>Detects repeated policy violations</li>
                <li>Identifies anomalous behavior patterns</li>
                <li>Suggests policy updates based on denials</li>
                <li>Creates tickets for security review</li>
            </ul>
        </div>

        <div class="component">
            <h3>4. Immutable Audit Trail</h3>
            <p><strong>Location:</strong> <code>services/immutable_audit_service.py</code></p>
            <p><strong>Purpose:</strong> Tamper-proof logging with cryptographic verification</p>
            
            <div class="code">
audit_entry = {{
    "event_type": "policy_violation",
    "agent_id": "gpt4",
    "action": "delete",
    "resource": "production_db",
    "decision": "DENY",
    "hash_chain": "sha256_hash",
    "timestamp": "2025-10-05T10:30:00Z"
}}
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Unified Policy Architecture</h2>
        
        <h3>Single Policy Model</h3>
        <p>All policies stored in <code>governance_policies</code> table:</p>
        
        <table>
            <tr><th>Field</th><th>Type</th><th>Description</th></tr>
            <tr><td>policy_name</td><td>string</td><td>Human-readable name</td></tr>
            <tr><td>natural_language</td><td>text</td><td>Plain English description</td></tr>
            <tr><td>effect</td><td>enum</td><td>deny | permit | require_approval</td></tr>
            <tr><td>actions</td><td>array</td><td>[read, write, delete, execute]</td></tr>
            <tr><td>resources</td><td>array</td><td>[database:*, mcp:server:*, s3:*]</td></tr>
            <tr><td>conditions</td><td>json</td><td>Environment, time, role restrictions</td></tr>
            <tr><td>risk_level</td><td>enum</td><td>low | medium | high</td></tr>
        </table>

        <h3>Resource Pattern Examples</h3>
        <div class="code">
# Agent Resources
"database:production:*"      # All production databases
"s3://sensitive-data/*"      # S3 buckets with sensitive data
"api:external:payment"       # External payment APIs
"financial:transactions"     # Financial data
"pii:customer_records"       # Personal data

# MCP Server Resources  
"mcp:server:filesystem"      # Filesystem operations
"mcp:server:github"          # GitHub operations
"mcp:server:slack"           # Slack operations
"mcp:namespace:production"   # Specific namespace
"mcp:resource:critical-file" # Specific resource
        </div>
    </div>

    <div class="section">
        <h2>Enterprise UI Features</h2>
        
        <h3>Policy Management Dashboard</h3>
        <ul>
            <li><strong>Analytics:</strong> Real-time metrics, denial rates, cache performance</li>
            <li><strong>Testing Sandbox:</strong> Test policies before production deployment</li>
            <li><strong>Visual Builder:</strong> No-code policy creation with dropdowns</li>
            <li><strong>Compliance Mapping:</strong> NIST 800-53, SOC 2, ISO 27001 coverage</li>
            <li><strong>Version Control:</strong> Policy history, rollback, diff view</li>
            <li><strong>Impact Analysis:</strong> Pre-deployment risk assessment</li>
        </ul>

        <h3>Authorization Dashboard</h3>
        <ul>
            <li>Pending approval queue with priority sorting</li>
            <li>Real-time execution tracking</li>
            <li>SLA monitoring with visual indicators</li>
            <li>Workflow orchestration management</li>
        </ul>
    </div>

    <div class="section">
        <h2>Request Lifecycle</h2>

        <div class="flow">
            <strong>Step 1: Action Request</strong><br>
            Agent or MCP server initiates action → Request hits API endpoint
        </div>

        <div class="flow">
            <strong>Step 2: Policy Evaluation</strong><br>
            enforcement_engine checks all policies → Returns ALLOW/DENY/REQUIRE_APPROVAL
        </div>

        <div class="flow">
            <strong>Step 3: Approval Workflow (if needed)</strong><br>
            Creates workflow instance → Routes to appropriate approver → Tracks SLA
        </div>

        <div class="flow">
            <strong>Step 4: Execution</strong><br>
            If approved/allowed → Execute action → Log execution results
        </div>

        <div class="flow">
            <strong>Step 5: Audit Trail</strong><br>
            Log to immutable audit → Create hash chain → Store in security_audit_trail
        </div>

        <div class="flow">
            <strong>Step 6: Smart Rules Analysis</strong><br>
            Analyze for patterns → Detect anomalies → Suggest policy updates
        </div>
    </div>

    <div class="section">
        <h2>Authentication & Authorization</h2>
        
        <h3>Supported Methods</h3>
        <ul>
            <li><strong>SSO:</strong> Okta, Azure AD, Google Workspace</li>
            <li><strong>JWT:</strong> Token-based API authentication</li>
            <li><strong>Cookies:</strong> Session-based web authentication</li>
        </ul>

        <h3>RBAC Roles</h3>
        <table>
            <tr><th>Role</th><th>Permissions</th></tr>
            <tr><td>admin</td><td>Full system access, policy management</td></tr>
            <tr><td>security_analyst</td><td>View logs, manage policies</td></tr>
            <tr><td>approver</td><td>Approve/deny workflow requests</td></tr>
            <tr><td>viewer</td><td>Read-only dashboard access</td></tr>
        </table>
    </div>

    <div class="section">
        <h2>Database Schema</h2>
        
        <h3>Key Tables</h3>
        <ul>
            <li><code>governance_policies</code> - All policies (unified)</li>
            <li><code>workflow_executions</code> - Approval workflow instances</li>
            <li><code>security_audit_trail</code> - Immutable audit logs</li>
            <li><code>smart_rules</code> - Pattern detection rules</li>
            <li><code>users</code> - User accounts and roles</li>
            <li><code>mcp_servers</code> - Registered MCP servers</li>
            <li><code>action_executions</code> - Execution history</li>
        </ul>
    </div>

    <div class="section">
        <h2>Deployment Architecture</h2>
        
        <h3>AWS Infrastructure</h3>
        <ul>
            <li><strong>ECS Fargate:</strong> Backend API containers</li>
            <li><strong>RDS PostgreSQL:</strong> Primary database</li>
            <li><strong>CloudFront:</strong> Frontend CDN</li>
            <li><strong>S3:</strong> Static asset hosting</li>
            <li><strong>Application Load Balancer:</strong> Traffic distribution</li>
        </ul>

        <h3>Endpoints</h3>
        <ul>
            <li><strong>Backend API:</strong> https://api.pilot.owkai.app</li>
            <li><strong>Frontend:</strong> https://pilot.owkai.app</li>
        </ul>
    </div>

    <div class="section">
        <h2>Compliance & Standards</h2>
        
        <table>
            <tr><th>Framework</th><th>Coverage</th><th>Controls</th></tr>
            <tr><td>NIST 800-53</td><td>85%</td><td>AC-3, AC-6, AU-2, SI-4</td></tr>
            <tr><td>SOC 2</td><td>90%</td><td>CC6.1, CC6.2, CC7.2</td></tr>
            <tr><td>ISO 27001</td><td>85%</td><td>A.9.2, A.9.4, A.12.4</td></tr>
        </table>
    </div>

    <p style="text-align: center; margin-top: 40px; color: #95a5a6;">
        OW-AI Platform | Enterprise AI Governance
    </p>
</body>
</html>
"""

with open('OW-AI_How_It_Works.html', 'w') as f:
    f.write(html)

print("✅ Generated: OW-AI_How_It_Works.html")
