# ASCEND AI SDK

Official Python SDK for [Ascend AI Governance Platform](https://ascendowkai.com/) — enterprise AI governance and enforcement for regulated industries.

Govern what your AI agents do — in real time. ASCEND intercepts every agent action, scores risk using CVSS v3.1/NIST 800-30/MITRE ATT&CK, enforces your policies, and maintains an immutable audit trail for compliance.

Built for financial services, healthcare, and government contractors.

---

## Install

```bash
pip install ascend-ai-sdk
```

---

## Quick Start

```python
from ascend import AscendClient, FailMode

client = AscendClient(
    api_key="your_api_key",
    api_url="https://pilot.owkai.app",
    agent_id="my-agent",
    agent_name="My Agent",
    fail_mode=FailMode.CLOSED
)

# Govern an action before it executes
result = client.evaluate_action(
    action_type="database_write",
    resource="customer_db",
    wait_for_decision=False
)

print(result.decision)      # APPROVED / PENDING / DENIED
print(result.risk_score)    # 0-100
print(result.cvss_score)    # CVSS v3.1 base score
print(result.mitre_tactic)  # MITRE ATT&CK tactic
```

### Enforcement Decision Attribution

Inspect *why* the platform reached its verdict. These fields ship in
`AuthorizationDecision` as of SDK 2.7.0:

```python
# Authoritative governance verdict
print(result.enforcement_decision)
# 'auto_approved' | 'pending_approval' | 'denied' | 'escalated'

# Which signal drove the verdict
print(result.enforcement_decision_source)
# 'threshold' | 'policy' | 'smart_rule' |
# 'code_analysis' | 'prompt_security'

# Which signal contributed the highest risk score
print(result.risk_score_source)
# 'cvss' | 'policy' | 'code_analysis' |
# 'prompt_security' | 'pipeline'

# Shadow scoring — what the system WOULD have decided under
# the org's shadow threshold config. None when no shadow
# config exists (opt-in feature, observational only).
print(result.shadow_enforcement_decision)
print(result.shadow_enforcement_decision_source)
```

---

## Model Governance (SR-11-7 / EU AI Act Art. 9)

Enforce your model registry at action submit time. Non-compliant or unregistered models are denied.

```python
result = client.evaluate_action(
    action_type="model_inference",
    resource="ml_pipeline",
    model_id="gpt-4-production",  # checked against registry
    wait_for_decision=False
)

print(result.model_governance["registry_checked"])
print(result.model_governance["compliance_status"])
```

---

## MCP Layer 13 Governance

Govern actions from MCP servers. Unregistered or deactivated servers are denied.

```python
result = client.evaluate_action(
    action_type="tool_call",
    resource="crm_system",
    mcp_server_name="salesforce-mcp",
    wait_for_decision=False
)

print(result.mcp_governance["server_registered"])
```

---

## Kill-Switch

Block all agent actions within one poll cycle (default 5 seconds). Kill-switch server handler p99=17.03ms (measured June 2, 2026).

```python
# Agent side — poll for kill-switch signals
client.start_kill_switch_polling(
    interval_seconds=5
)

# Fail-secure: agents fail-closed after 3 consecutive unreachable
# polls (~15 seconds worst-case). Recovers automatically when the
# endpoint becomes healthy.
if client.is_blocked():
    # Kill-switch active OR polling has failed 3+ times —
    # do not proceed with the agent action.
    pass
```

---

## Capabilities

| Capability | Description |
|---|---|
| Risk Scoring | CVSS v3.1, NIST 800-30, MITRE ATT&CK composite |
| MCP Governance | Layer 13 enforcement — unregistered servers denied |
| Model Governance | Registry-backed compliance check — SR-11-7, EU AI Act |
| Kill-Switch | Poll-based agent blocking, default 5s interval. Server handler p99=17.03ms measured |
| Prompt Injection | 22 detection patterns including encoding detection |
| Code Analysis | SQL injection, command injection, credential detection |
| Supply Chain | CVE detection via NVD/OSV, risk scoring |
| Audit Trail | Immutable hash-chain, cryptographic verification |
| Human Approval | Multi-stage workflows with SLA enforcement |

---

## Compliance

SOC 2 Type II · PCI-DSS · HIPAA · FedRAMP Compatible
NIST AI RMF · SR 11-7 · EU AI Act Art. 9/28

---

## Links

- Platform: https://pilot.owkai.app
- Documentation: https://docs.ascendowkai.com
- Status: https://ascend-status.instatus.com
- Support: info@ow-kai.com

---

## Requirements

Python 3.8+

---

*ASCEND is a product of OW-KAI Technologies, Inc.*
*9+ years spanning AI/ML governance and cybersecurity.*
