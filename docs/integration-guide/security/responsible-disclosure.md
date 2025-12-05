# Responsible Disclosure Policy

At Ascend, security is our top priority. We value the security research community and encourage responsible disclosure of any vulnerabilities discovered in our platform.

## Reporting a Vulnerability

### Contact

**Email**: [security@ascendowkai.com](mailto:security@ascendowkai.com)

**PGP Key**: Available at [ascendowkai.com/.well-known/security.txt](https://ascendowkai.com/.well-known/security.txt)

### What to Include

When reporting a vulnerability, please provide:

1. **Description** - Clear explanation of the vulnerability
2. **Impact** - Potential security impact if exploited
3. **Reproduction Steps** - Detailed steps to reproduce the issue
4. **Proof of Concept** - Code, screenshots, or video demonstrating the vulnerability
5. **Affected Components** - URLs, API endpoints, or features affected
6. **Suggested Fix** - If you have recommendations for remediation

### Example Report

```
Subject: [Security Report] Multi-tenant isolation bypass in agent actions

Description:
A query parameter injection vulnerability allows bypassing organization_id
filtering in the /api/v1/actions endpoint under specific conditions.

Impact:
An authenticated user from Organization A could potentially view agent
actions from Organization B, violating SEC-007 multi-tenant isolation.

Reproduction Steps:
1. Authenticate as user from Organization 1
2. Send GET request to /api/v1/actions with crafted org_id parameter
3. Observe responses containing data from other organizations

Affected URL:
https://pilot.owkai.app/api/v1/actions?org_id=<injection>

Suggested Fix:
Enforce organization_id from JWT token (get_organization_filter dependency)
rather than accepting it as a query parameter.

Reference: dependencies.py (SEC-007 implementation)
```

## Our Commitment

### Response Timeline

| Phase | Timeline |
|-------|----------|
| Acknowledgment | Within 24 hours |
| Initial Assessment | Within 72 hours |
| Status Update | Within 7 days |
| Resolution Target | Within 90 days |

### What We Promise

- **Acknowledgment**: We will acknowledge your report promptly
- **Communication**: We will keep you informed of our progress
- **Credit**: We will credit you (if desired) in our security acknowledgments
- **No Legal Action**: We will not pursue legal action against researchers acting in good faith

## Scope

### In Scope

- **Web Applications**: pilot.owkai.app (Dashboard), pilot.owkai.app/api (REST API)
- **APIs**: REST API endpoints, WebSocket connections
- **Authentication**: Cookie-based JWT, API key authentication, AWS Cognito integration
- **Authorization**: Multi-tenant isolation, policy enforcement, RBAC
- **Data Handling**: Database queries, encryption, audit logging

### Backend Services

Security researchers are encouraged to focus on:

| Service | File Reference | Security Focus |
|---------|---------------|----------------|
| Multi-Tenant Isolation | `dependencies.py` | Organization ID filtering (SEC-007) |
| API Key Authentication | `api_key_routes.py` | Key hashing, validation (SEC-018) |
| Policy Enforcement | `cedar_enforcement_service.py` | Policy bypass, privilege escalation |
| Data Rights APIs | `data_rights_routes.py` | GDPR compliance, data access control |
| Anomaly Detection | `anomaly_detection_service.py` | Detection bypass, false negatives (SEC-077) |
| Circuit Breaker | `circuit_breaker_service.py` | State manipulation (SEC-077) |

### Vulnerability Types

We're interested in vulnerabilities including:

- **Authentication bypass** - Bypassing JWT or API key validation
- **Authorization flaws** - Bypassing multi-tenant isolation (SEC-007)
- **SQL injection** - Database query injection
- **Cross-site scripting (XSS)** - Stored or reflected XSS in Dashboard
- **Cross-site request forgery (CSRF)** - CSRF token bypass
- **Sensitive data exposure** - Organization data leakage, API key exposure
- **Insecure direct object references** - Access to other organizations' resources
- **Policy bypass** - Circumventing policy enforcement
- **Session fixation** - JWT or cookie manipulation
- **Rate limiting bypass** - API rate limit circumvention

### Out of Scope

- Social engineering attacks against employees
- Physical attacks on facilities
- Denial of service (DoS/DDoS) attacks
- Spam or phishing campaigns
- Third-party services and dependencies
- Issues already reported and acknowledged
- Vulnerabilities in outdated/unsupported versions
- Issues requiring physical access
- Theoretical vulnerabilities without proof of concept

## Safe Harbor

We consider security research conducted consistent with this policy to be:

- **Authorized** - We will not initiate legal action
- **Lawful** - We waive any relevant anti-hacking laws
- **Helpful** - An effort to improve our security

This safe harbor applies when:

1. You report vulnerabilities directly to us via [security@ascendowkai.com](mailto:security@ascendowkai.com)
2. You do not access data beyond what's necessary to demonstrate the vulnerability
3. You do not disclose vulnerabilities publicly before we've had reasonable time to remediate
4. You do not exploit vulnerabilities beyond proof of concept
5. You do not perform destructive testing (data deletion, service disruption)
6. You respect our multi-tenant architecture and do not access other organizations' data

## Recognition

### Hall of Fame

Security researchers who report valid vulnerabilities may be recognized in our Security Hall of Fame (with their permission).

### Bug Bounty

We offer monetary rewards for qualifying vulnerabilities:

| Severity | Criteria | Reward Range |
|----------|----------|--------------|
| Critical | Multi-tenant isolation bypass, authentication bypass, RCE | $1,000 - $5,000 |
| High | Authorization bypass, SQL injection, CSRF, sensitive data exposure | $500 - $1,000 |
| Medium | XSS, policy bypass, session issues | $100 - $500 |
| Low | Information disclosure, minor configuration issues | $50 - $100 |

Rewards are determined based on:
- Severity and impact (especially multi-tenant isolation - SEC-007)
- Quality and clarity of the report
- Complexity of exploitation
- Presence of proof of concept code

### Priority Vulnerabilities

Vulnerabilities affecting these areas receive expedited review and higher rewards:

- **Multi-tenant isolation** (SEC-007): Cross-organization data access
- **API key security** (SEC-018): Key leakage or brute force
- **GDPR compliance**: Data rights API bypass
- **Policy enforcement**: Cedar engine bypass
- **Anomaly detection**: Detection evasion techniques

## Examples of Valid Reports

### High Severity: Organization ID Bypass

```
Title: SQL injection in organization filter allows cross-tenant data access
Severity: Critical
Impact: Violates SEC-007 multi-tenant isolation

POC:
GET /api/alerts?org_id=1 OR 1=1--
Returns alerts from all organizations despite authentication as org_id=4
```

### Medium Severity: Policy Bypass

```
Title: Policy evaluation can be bypassed via action_type manipulation
Severity: High
Impact: Allows executing high-risk actions without policy approval

POC:
POST /api/unified/action
{"action_type": "database.query\x00admin", ...}
Null byte injection bypasses policy matching in cedar_enforcement_service.py
```

### Low Severity: Information Disclosure

```
Title: API error messages expose internal file paths
Severity: Low
Impact: Information disclosure aids in fingerprinting

POC:
POST /api/invalid-endpoint
Response includes: "/opt/app/ow-ai-backend/routes/auth_routes.py line 42"
```

## Contact

**Security Team**: [security@ascendowkai.com](mailto:security@ascendowkai.com)

**General Support**: [support@ascendowkai.com](mailto:support@ascendowkai.com)

**Status Page**: [status.ascendowkai.com](https://status.ascendowkai.com)

---

Thank you for helping keep Ascend and our customers secure.

## Additional Resources

- [Security Overview](/security/overview) - Complete security architecture
- [Compliance](/security/compliance) - Regulatory frameworks
- [Data Encryption](/security/data-encryption) - Encryption implementations
