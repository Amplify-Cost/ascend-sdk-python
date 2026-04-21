# Ascend AI SDK for Python

**The AI Agent and MCP Control Plane for regulated industries.** Every agent action and MCP tool invocation is risk-scored against CVSS v3.1, NIST 800-30, and MITRE ATT&CK — then policy-enforced, human-reviewed when needed, and logged to an immutable audit trail. Sub-second kill-switch, fail-closed enforcement, 33-pattern threat detection, agentless discovery, and 28 regulator-ready compliance reports. Built for financial services, healthcare, and government.

[![PyPI Version](https://img.shields.io/pypi/v/ascend-ai-sdk)](https://pypi.org/project/ascend-ai-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/ascend-ai-sdk)](https://pypi.org/project/ascend-ai-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-ascendowkai.com-blue)](https://docs.ascendowkai.com)

```bash
pip install ascend-ai-sdk
```

---

## What you get

- **Real-time authorization** for every agent action and MCP tool invocation
- **Industry-standard risk scoring** — CVSS v3.1 + NIST 800-30 + MITRE ATT&CK (0–100 composite score)
- **Fail-closed enforcement** — if ASCEND is unreachable, actions are blocked by default
- **Sub-second kill-switch** — halt any agent globally via SNS/SQS in under 1 second
- **Immutable audit trail** — hash-chained logs ready for regulators and forensics
- **Layer 13 MCP Governance** — native risk scoring and enforcement on Model Context Protocol tool calls
- **Multi-stage approval workflows** — configurable thresholds, SLA tracking, human-in-the-loop
- **Circuit breaker and retries** — production-ready resilience built into the SDK

---

## Requirements

- Python 3.8 or higher
- `requests` (installed automatically)
- `python-dotenv` (installed automatically)

---

## Installation

```bash
pip install ascend-ai-sdk
```

Upgrade an existing installation:

```bash
pip install --upgrade ascend-ai-sdk
```

---

## Quick Start

### 1. Get an API key

Sign up for the free 14-day sandbox at **[ascendowkai.com](https://ascendowkai.com)** — 3 agents, 10,000 governed actions, 2 MCP servers, no credit card required. After signup, your API key is available at **Settings → API Keys** inside the pilot app.

### 2. Configure your environment

```bash
export ASCEND_API_KEY='ask_sbx_your_key_here'
export ASCEND_API_URL='https://pilot.owkai.app'
```

Or use a `.env` file:

```
ASCEND_API_KEY=ask_sbx_your_key_here
ASCEND_API_URL=https://pilot.owkai.app
```

### 3. Govern your first action

```python
from ascend import AscendClient

client = AscendClient(
    agent_id="customer-lookup-bot",
    agent_name="Customer Lookup Bot",
    fail_mode="closed",  # Block the action if ASCEND is unreachable
)

decision = client.evaluate_action(
    action_type="database.read",
    resource="customer_profiles",
    resource_id="CUST-12345",
    risk_indicators={"pii_involved": True},
)

if decision.execution_allowed:
    print(f"Approved — risk score {decision.risk_score} ({decision.risk_level})")
    # Run your action here
else:
    print(f"Blocked — {decision.reason}")
```

`evaluate_action` returns an `AuthorizationDecision` with `execution_allowed`, `risk_score`, `risk_level`, `reason`, `approved_by`, `approved_at`, and `expires_at`. Default behavior waits for a decision (up to 60 seconds) and raises `TimeoutError` if no human approver responds in time — which, in `fail_mode="closed"`, means the action is blocked.

---

## Recommended pattern: `AuthorizedAgent`

For most applications, `AuthorizedAgent` is the cleaner integration. It wraps authorization and execution in a single call — the function only runs if ASCEND approves.

```python
from ascend import AuthorizedAgent

agent = AuthorizedAgent(
    agent_id="payment-processor",
    agent_name="Payment Processing Agent",
)

def process_payment():
    # Your actual business logic
    return {"status": "completed", "transaction_id": "TXN-98765"}

# Action runs only if authorized
result = agent.execute_if_authorized(
    action_type="transaction",
    resource="payment_gateway",
    resource_id="TXN-98765",
    execute_fn=process_payment,
    risk_indicators={
        "amount_threshold": "exceeded",
        "external_transfer": True,
    },
    # Optional: graceful fallback when ASCEND denies the action
    on_denied=lambda decision: {
        "status": "blocked",
        "reason": decision.reason,
    },
)
```

You can also check authorization without executing anything:

```python
if agent.check_permission("database.write", "customer_profiles"):
    # Permission confirmed — proceed
    pass
```

---

## Fail-mode configuration

Fail-mode controls what happens when ASCEND itself is unreachable — network outage, API timeout, circuit breaker open. The default is `closed` (fail-secure).

| Mode | Behavior on ASCEND unreachable | Use case |
|---|---|---|
| `closed` | Action is blocked. `ConnectionError` raised. | **Default.** Production workloads, regulated environments, any action you would not run without governance. |
| `open` | Action proceeds without governance. Logged on next successful call. | Non-critical workloads where availability outweighs control. Use deliberately. |

```python
from ascend import AscendClient

# Fail-closed (recommended)
client = AscendClient(agent_id="...", agent_name="...", fail_mode="closed")

# Fail-open (use deliberately)
client = AscendClient(agent_id="...", agent_name="...", fail_mode="open")
```

The SDK also includes a circuit breaker that opens after 5 consecutive failures (configurable via `circuit_breaker_threshold`) and auto-resets after 30 seconds.

---

## MCP Governance (Layer 13)

ASCEND is the first platform to provide native governance for Model Context Protocol tool calls at the action layer. The MCP governance middleware intercepts every tool invocation, risk-scores it, and enforces the organization's policy before the tool executes.

```python
from ascend import AscendClient, MCPGovernanceConfig, MCPGovernanceMiddleware

client = AscendClient(
    agent_id="claude-desktop",
    agent_name="Claude with Filesystem MCP",
    fail_mode="closed",
)

config = MCPGovernanceConfig(
    wait_for_approval=True,
    approval_timeout_seconds=300,
    raise_on_denial=True,
    on_denied=lambda decision: print(f"MCP call blocked: {decision.reason}"),
)

middleware = MCPGovernanceMiddleware(client=client, config=config)

# Wrap any MCP tool function — governance runs before the tool executes
@middleware.wrap(tool_name="write_file")
def write_file(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)
    return {"status": "written", "path": path}

# This call is risk-scored and enforced by ASCEND before the file is touched.
# If denied, ASCEND raises AuthorizationError (per raise_on_denial=True above).
write_file(path="/etc/config.yaml", content="...")
```

Tool calls map to action types with baseline risk (e.g. `list_directory` = 15, `write_file` = 50, `delete_file` = 75). Contextual risk adjustments fire for sensitive paths (`/etc`, `.env`, `.ssh`), recursive operations, and bulk mutations.

---

## Kill-switch integration

The kill-switch infrastructure lets operators halt any agent globally in under one second. The SDK polls an SQS queue for control commands and terminates gracefully when a halt is issued.

```python
from ascend import AscendClient

client = AscendClient(
    agent_id="autonomous-trader",
    agent_name="Autonomous Trading Agent",
    fail_mode="closed",
)

# Start polling for kill-switch commands in a background thread
client.start_kill_switch_polling(interval_seconds=5)

try:
    while True:
        if client.is_blocked():
            # Operator has halted this agent — exit gracefully
            break

        decision = client.evaluate_action(
            action_type="transaction",
            resource="trading_api",
        )
        if decision.execution_allowed:
            # Execute trade
            pass
finally:
    client.stop_kill_switch_polling()
```

Kill-switch events are published via AWS SNS, delivered per-tenant via SQS, and acknowledged back to the audit trail — every halt is logged with trigger identity, timestamp, and affected agent scope.

---

## Exception handling

The SDK uses specific exception types for each failure mode. All inherit from `OWKAIError`.

```python
from ascend import (
    AscendClient,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConnectionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)

client = AscendClient(agent_id="...", agent_name="...")

try:
    decision = client.evaluate_action(
        action_type="database.read",
        resource="customer_profiles",
    )
except AuthenticationError as e:
    # 401 — API key invalid, expired, or revoked
    print(f"Check ASCEND_API_KEY: {e}")
except ValidationError as e:
    # 422 — request schema invalid
    print(f"Request invalid: {e}")
except RateLimitError as e:
    # 429 — tenant quota exceeded; retry later
    print(f"Rate limited: {e}")
except TimeoutError as e:
    # No decision received within timeout (default 60s)
    # In fail_mode="closed", the action is blocked.
    print(f"Decision timeout: {e}")
except ConnectionError as e:
    # Network unreachable; fail_mode determines behavior
    print(f"Network error: {e}")
except ServerError as e:
    # 5xx from ASCEND; automatically retried with exponential backoff
    print(f"Server error: {e}")
```

Full exception hierarchy: `AuthenticationError`, `AuthorizationError`, `ConfigurationError`, `ConflictError`, `ConnectionError`, `KillSwitchError`, `NotFoundError`, `RateLimitError`, `ServerError`, `TimeoutError`, `ValidationError`.

---

## Action types

Standard action types ship with the SDK. You can also pass arbitrary strings.

```python
from ascend import ActionType

ActionType.DATA_ACCESS          # Reading data
ActionType.DATA_MODIFICATION    # Writing or deleting data
ActionType.QUERY                # Database queries
ActionType.TRANSACTION          # Financial transactions
ActionType.RECOMMENDATION       # AI-generated recommendations
ActionType.COMMUNICATION        # External communications (email, SMS, chat)
ActionType.SYSTEM_OPERATION     # System-level changes
ActionType.API_CALL             # External API invocations
ActionType.ANALYSIS             # Data analysis
ActionType.REPORT_GENERATION    # Compliance or business reports
```

---

## Configuration reference

### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ASCEND_API_KEY` | Yes | — | Your ASCEND API key |
| `ASCEND_API_URL` | No | `https://pilot.owkai.app` | API endpoint |
| `ASCEND_DEBUG` | No | `false` | Enable debug logging |

### Programmatic configuration

```python
from ascend import AscendClient

client = AscendClient(
    api_key="ask_...",              # Or set ASCEND_API_KEY env var
    agent_id="my-agent",
    agent_name="My Production Agent",
    api_url="https://pilot.owkai.app",
    environment="production",
    fail_mode="closed",              # "closed" (recommended) or "open"
    timeout=5,                       # Per-request timeout in seconds
    max_retries=3,                   # Retry attempts on transient failure
    enable_circuit_breaker=True,
    circuit_breaker_threshold=5,     # Failures before breaker opens
    circuit_breaker_timeout=30,      # Seconds before breaker half-opens
    debug=False,
)
```

---

## Platform capabilities beyond the SDK

This SDK is one of several integration paths into the ASCEND platform. Additional enterprise capabilities — administered through the ASCEND console and REST API:

- **13-layer security architecture** — defense-in-depth from input validation to MCP governance; every layer defaults to deny on error
- **Agentless Discovery** — connect a read-only AWS IAM role, scan CloudWatch, Lambda, ECS, and API Gateway, surface every AI agent in your environment within 15 minutes — no SDK deployment required
- **Security Graph (F2)** — D3 force-directed visualization of your AI estate with 33 MITRE ATT&CK patterns running concurrently across all 14 tactics, real-time WebSocket updates, and detection of data aggregation, exfiltration, lateral movement, privilege escalation, policy drift, and approval bypass attempts
- **Regulatory Evidence Package (F3)** — 28 pre-built compliance report types including SEC AI Disclosure, SR 11-7 Model Risk, NYDFS Part 500, FINRA Rule 3110/4370, SOC 2, HIPAA, PCI-DSS, PDF with watermarks, classification markings, and cryptographic attestation
- **BYOK/CMK encryption** — customer-managed AWS KMS keys with AES-256 envelope encryption and 15-minute key health monitoring
- **Multi-tenant RLS isolation** — PostgreSQL row-level security with per-tenant Cognito user pools
- **Agent Registry** — supervised and autonomous agent modes with per-agent risk thresholds
- **Smart Rules Engine** — self-learning rules that auto-allow or auto-block based on action patterns
- **Multi-agent orchestration governance** — topology visualization, cascade kill-switch with dry-run preview, parent-child delegation tracking

Full platform documentation: **[docs.ascendowkai.com](https://docs.ascendowkai.com)**

---

## Compliance posture

ASCEND is designed and built to align with the control requirements of:

- SOC 2 Type II
- PCI-DSS
- HIPAA
- SOX
- GDPR
- NIST 800-53
- NIST AI RMF
- NYDFS 500 (including 2023 AI amendments)
- FINRA Rule 3110 and 4370
- Federal Reserve SR 11-7
- SEC 2026 AI examination priorities
- FFIEC CAT

External audits are in progress.

---

## Support

- **Documentation** — [docs.ascendowkai.com](https://docs.ascendowkai.com)
- **Product (pilot)** — [pilot.owkai.app](https://pilot.owkai.app/login)
- **Marketing and sandbox signup** — [ascendowkai.com](https://ascendowkai.com)
- **Security and SDK contact** — [security@ow-kai.com](mailto:security@ow-kai.com)
- **GitHub Issues** — [github.com/Amplify-Cost/ascend-sdk-python/issues](https://github.com/Amplify-Cost/ascend-sdk-python/issues)

---

## Changelog

See [CHANGELOG.md](https://github.com/Amplify-Cost/ascend-sdk-python/blob/main/CHANGELOG.md) on GitHub.

---

## License

MIT — see [LICENSE](https://github.com/Amplify-Cost/ascend-sdk-python/blob/main/LICENSE).

© OW-KAI Technologies, Inc.
