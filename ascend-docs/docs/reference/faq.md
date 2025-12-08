---
sidebar_position: 4
title: FAQ
description: Frequently asked questions
---

# Frequently Asked Questions

Common questions about Ascend AI Governance Platform.

---

## Getting Started

### What is Ascend?

Ascend is an enterprise AI governance platform that provides real-time monitoring, risk assessment, and approval workflows for AI agent actions. It helps organizations maintain control over autonomous AI systems while ensuring compliance with security and regulatory requirements.

### How do I get started with Ascend?

1. Contact sales@owkai.app to set up your organization
2. Receive your API credentials and dashboard access
3. Install an SDK (Python, TypeScript, or Go)
4. Register your first agent
5. Start submitting actions for governance

### What programming languages are supported?

Ascend provides official SDKs for:
- **Python** 3.8+
- **TypeScript/Node.js** 18+
- **Go** 1.20+

All SDKs provide identical functionality. You can also use the REST API directly.

---

## Integration

### How do I integrate my AI agent with Ascend?

```python
from ascend_sdk import AscendClient

client = AscendClient(api_key="your_api_key")

# Submit action for governance
result = client.submit_action(
    agent_id="my-agent",
    action_type="database_write",
    description="Update customer record",
    tool_name="postgresql"
)

if result.status == "approved":
    # Execute the action
    pass
elif result.status == "pending_approval":
    # Wait for human approval
    pass
elif result.status == "denied":
    # Handle denial
    pass
```

### Can I use Ascend with MCP servers?

Yes, Ascend provides full governance support for Model Context Protocol (MCP) servers. Register your MCP server as an agent and all tool calls will be routed through the governance pipeline.

### How does Ascend handle high latency requirements?

Ascend is designed for low-latency operation:
- Average API response time: < 150ms
- P95 response time: < 300ms
- Auto-approve decisions: < 50ms

For time-sensitive operations, configure appropriate auto-approve thresholds.

---

## Risk & Compliance

### How is risk score calculated?

Risk scores combine CVSS 3.1 base metrics with contextual modifiers:

```
Risk Score = (CVSS Base × 10) + Context Modifiers

Context Modifiers include:
- Time of day (+10 for after hours)
- Data sensitivity (+15 for PII/PHI)
- Target system (+10 for production)
- Volume (+15 for bulk operations)
```

### What compliance frameworks does Ascend support?

Ascend supports:
- **SOC 2 Type II** - Full trust service criteria
- **HIPAA** - PHI safeguards and audit trails
- **PCI-DSS** - Payment card data protection
- **NIST 800-53** - Federal security controls
- **GDPR** - Data protection requirements
- **SOX** - Financial controls
- **MITRE ATT&CK** - Threat framework mapping

### Can I customize risk thresholds?

Yes, you can configure thresholds at multiple levels:

1. **Organization level**: Default thresholds for all agents
2. **Agent level**: Override defaults for specific agents
3. **Action type level**: Custom thresholds per action type

### How do I handle false positives in smart rules?

1. Review the rule's false positive metrics in the dashboard
2. Use the A/B testing feature to test rule modifications
3. Optimize rules using the `/optimize/{rule_id}` endpoint
4. Provide feedback through the rule feedback API

---

## Security

### How is data encrypted?

- **At rest**: AES-256-GCM using AWS KMS
- **In transit**: TLS 1.3
- **API keys**: SHA-256 hashed with salt

### How does multi-tenant isolation work?

Every database query is filtered by `organization_id`, ensuring complete data isolation between tenants. This is enforced at the application layer with dependency injection.

### What authentication methods are supported?

- **API Key**: For SDK and programmatic access
- **JWT with MFA**: For dashboard access via Cognito
- **Service accounts**: For system-to-system integration

### How long are audit logs retained?

Audit logs are retained for 7 years by default. Retention periods can be customized per compliance requirement.

---

## Operations

### What is the SLA for Ascend?

- **Uptime**: 99.9% monthly
- **RTO**: 4 hours
- **RPO**: 1 hour
- **Response time**: P95 < 300ms

### How do I monitor system health?

1. Check the `/health` endpoint for basic health
2. Use the Analytics API for detailed metrics
3. Enable CloudWatch integration for AWS monitoring
4. Set up webhook notifications for alerts

### Can I export my data?

Yes, data can be exported via:
- Compliance export API (SOC 2, HIPAA, NIST)
- Audit log export
- Analytics data export
- Agent activity reports

### How do I handle an agent that's misbehaving?

1. **Immediate**: Use emergency suspend via the API or dashboard
2. **Review**: Check the agent's action history
3. **Configure**: Adjust risk thresholds or add policies
4. **Resume**: Reactivate with stricter controls

```bash
# Emergency suspend
curl -X POST "https://pilot.owkai.app/api/registry/agents/agent-id/emergency-suspend" \
  -H "Cookie: access_token=your_token" \
  -d '{"reason": "Unusual behavior detected"}'
```

---

## Pricing & Support

### How is Ascend priced?

Contact sales@owkai.app for pricing information. Pricing is based on:
- Number of registered agents
- Action volume
- Feature tier (Standard, Enterprise)

### What support is available?

| Tier | Response Time | Channels |
|------|---------------|----------|
| Standard | 24 hours | Email |
| Enterprise | 4 hours | Email, Slack, Phone |
| Premium | 1 hour | Dedicated support |

### Is there a free trial?

Contact sales@owkai.app to request a trial environment.

---

## Troubleshooting

### Why is my action being denied?

Common reasons:
1. **Policy violation**: Check active policies
2. **Risk threshold exceeded**: Review risk configuration
3. **Agent suspended**: Verify agent status
4. **Rate limit**: Check agent rate limits

Debug using the correlation ID in the response.

### Why am I getting 401 Unauthorized?

1. Verify API key is correct
2. Check key hasn't been revoked
3. Ensure key has appropriate permissions
4. For dashboard, verify session hasn't expired

### How do I debug a slow request?

1. Check the `processing_time_ms` in the response
2. Review CloudWatch metrics
3. Check for network latency issues
4. Contact support with the correlation ID

### My agent isn't receiving updates for pending actions

For pending actions, implement polling:

```python
def wait_for_decision(action_id, max_wait=300):
    start = time.time()
    while time.time() - start < max_wait:
        status = client.get_action_status(action_id)
        if status.decision_ready:
            return status.status
        time.sleep(5)
    return "timeout"
```

Or use webhooks for real-time notifications.

---

## Best Practices

### What are best practices for agent registration?

1. Use descriptive, unique agent IDs
2. Configure appropriate risk thresholds
3. Define allowed action types explicitly
4. Set up alert recipients
5. Test in staging before production

### How should I handle high-volume agents?

1. Configure appropriate rate limits
2. Use batch operations where possible
3. Implement exponential backoff for retries
4. Monitor usage metrics regularly

### What's the recommended approval workflow?

1. Auto-approve low-risk actions (< 30)
2. Review medium-risk actions (30-70)
3. Require approval for high-risk actions (> 70)
4. Block critical actions (> 90) for security review

---

## Feature Requests

### How do I request a new feature?

Contact support@owkai.app with:
1. Feature description
2. Use case and business value
3. Desired timeline

### Is there a public roadmap?

Contact your account manager for roadmap information.

---

*For additional questions, contact support@owkai.app*
