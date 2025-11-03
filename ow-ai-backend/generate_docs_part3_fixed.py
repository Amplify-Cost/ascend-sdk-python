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

### Administrator Checklist

#### Daily
- [ ] Review critical alerts
- [ ] Check system health dashboard
- [ ] Monitor approval queue depth
- [ ] Review any workflow timeouts

#### Weekly
- [ ] Review rule performance metrics
- [ ] Analyze false positive trends
- [ ] Check integration health
- [ ] Review user access logs
- [ ] Update documentation

#### Monthly
- [ ] Generate compliance reports
- [ ] Review and optimize rules
- [ ] Audit user permissions
- [ ] Performance tuning review
- [ ] Backup restoration test
- [ ] Team training session

#### Quarterly
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
SECURITY LAYERS

Layer 7: Physical Security
└─ AWS data centers (SOC 1/2/3 certified)

Layer 6: Network Security
├─ VPC isolation
├─ Security groups
├─ Network ACLs
└─ TLS 1.3 encryption

Layer 5: Infrastructure Security
├─ ECS task isolation
├─ IAM least privilege
├─ Secrets Manager
└─ CloudTrail logging

Layer 4: Application Security
├─ Input validation (Pydantic)
├─ SQL injection prevention (SQLAlchemy ORM)
├─ XSS protection
└─ CSRF protection

Layer 3: Authentication & Authorization
├─ JWT with RS256
├─ MFA support
├─ SSO integration
└─ Role-Based Access Control

Layer 2: Data Security
├─ Encryption at rest (AES-256)
├─ Encryption in transit (TLS 1.3)
├─ Database encryption
└─ PII tokenization

Layer 1: Monitoring & Response
├─ Real-time threat detection
├─ Anomaly detection
├─ Automated incident response
└─ Security audit logs
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

**CC6.6 - System Operations**
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

**CC7.2 - Risk Assessment**
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

**Key Principles:**

1. **Lawfulness, Fairness, Transparency**
   - All processing has legal basis
   - Purposes clearly communicated
   - Privacy notices provided

2. **Purpose Limitation**
   - Data collected for specific purposes
   - Not used for incompatible purposes
   - Purpose documented in processing records

3. **Data Minimization**
   - Only necessary data collected
   - Automatic checks enforce minimization
   - Regular data audits

4. **Accuracy**
   - Data accuracy verified
   - Correction mechanisms available
   - Outdated data removed

5. **Storage Limitation**
   - Retention periods defined
   - Automatic deletion after retention
   - Legal holds respected

6. **Integrity and Confidentiality**
   - Encryption at rest and in transit
   - Access controls enforced
   - Security monitoring active

7. **Accountability**
   - Complete audit trails
   - Processing records maintained
   - DPO oversight

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

#### Administrative Safeguards (Section 164.308)
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

#### Technical Safeguards (Section 164.312)
```
Access Control:
├─ Unique User Identification ✅
│  └─ Every user has unique ID
├─ Emergency Access Procedure ✅
│  └─ Break-glass access with logging
├─ Automatic Logoff ✅
│  └─ 15-minute inactivity timeout
└─ Encryption and Decryption ✅
   └─ AES-256 for all PHI

Audit Controls:
├─ Record all PHI access ✅
├─ Immutable audit logs ✅
├─ 6-year retention ✅
└─ Regular review ✅

Integrity:
├─ Checksums verify data integrity ✅
├─ Unauthorized change detection ✅
└─ Security team alerts ✅

Transmission Security:
├─ TLS 1.3 for all transmissions ✅
├─ HMAC signatures ✅
└─ Transmission logging ✅
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

# HTML template
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
