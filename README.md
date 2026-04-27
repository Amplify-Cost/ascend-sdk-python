# ASCEND AI SDK

**Enterprise AI governance and enforcement for regulated industries.**

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

Block all agent actions in under 500ms.

```python
# Agent side — poll for kill-switch signals
client.start_kill_switch_polling(
    interval_seconds=5
)
```

---

## Capabilities

| Capability | Description |
|---|---|
| Risk Scoring | CVSS v3.1, NIST 800-30, MITRE ATT&CK composite |
| MCP Governance | Layer 13 enforcement — unregistered servers denied |
| Model Governance | Registry-backed compliance check — SR-11-7, EU AI Act |
| Kill-Switch | Sub-500ms agent blocking via SNS/SQS |
| Prompt Injection | 21 detection patterns including encoding detection |
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
- Support: Donald.king@ow-kai.com

---

## Requirements

Python 3.8+

---

*ASCEND is a product of OW-KAI Technologies, Inc.*
*9+ years spanning AI/ML governance and cybersecurity.*
