# Changelog

All notable changes to the Ascend AI SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.1] - 2026-04-29

### Fixed (SDK-261)

- **Governance violations now return a decision, not an exception.**
  Unregistered MCP server, unregistered model, and other governance
  violations the platform surfaces as HTTP 403 are now returned as
  `AuthorizationDecision(decision=DENIED)`. Callers branch on
  `result.decision` rather than wrapping every call in `try/except`
  for an *expected* denial outcome. Real auth failures (bad API key,
  off-tenant) continue to raise `AuthorizationError`.
- **`AuthorizationError` message is now a readable sentence**, not a
  Python `dict` repr — when the platform returns a nested `detail`
  object, the SDK extracts the human-readable string before
  constructing the exception message.
- **`result.status` returns backend-vocabulary strings** matching
  the CWG test plan: `PENDING → 'pending_approval'`,
  `ALLOWED → 'approved'`, `DENIED → 'denied'`. The 2.6.0 vocabulary
  (`'pending'` / `'allowed'` / `'denied'`) is still available as
  `result.decision.value` for callers that want the typed enum value.

### Added

- **`result.raw_status`** — exposes the wire status string the
  platform actually sent, before SDK normalisation. Surfaces values
  the v2.0 `Decision` enum collapses, e.g. `'auto_approved'`,
  `'executed'`, `'escalated'`, `'timeout'`,
  `'requires_modification'`. Falls back to `result.status` when the
  platform omitted the `status` field.
- Governance-violation responses now populate
  `metadata["governance_violation"] = True`,
  `metadata["correlation_id"]`, plus the SDK-251 routing fields
  (`mcp_server_name`, `model_id`) when present, so callers can
  inspect rich denial context without parsing the original error.

### Zero breaking changes (callers)

- Code using `try/except AuthorizationError` for governance
  violations continues to compile and run — governance violations
  no longer raise, so the existing `except` block becomes inert
  rather than broken.
- `result.decision` is unchanged; `result.status == 'denied'` still
  works for denied outcomes.
- The `metadata` dict still carries every key the platform returns,
  matching the SDK-250 ZERO BREAKING CHANGE contract.

### Internal contract update (no PyPI 2.6.0 release was published)

- Six 2.6.0 contract assertions in `tests/test_sdk260_cwg_compat.py`
  (locked vocabulary `'pending'` / `'allowed'`) have been updated to
  the 2.6.1 vocabulary (`'pending_approval'` / `'approved'`). 2.6.0
  was tag-pushed but never published to PyPI, so no installed
  release ever exposed the 2.6.0 `.status` value vocabulary.

## [2.6.0] - 2026-04-28

### Added — CWG compatibility (SDK-260)

- **`evaluate_action()`** now accepts three convenience kwargs that route
  into the underlying `AgentAction` payload without the caller having to
  assemble dicts manually:
  - `tool_name: Optional[str]` — merged into `action_details["tool_name"]`
  - `description: Optional[str]` — merged into `action_details["description"]`
  - `business_justification: Optional[str]` — merged into `ActionContext`
    so it lands on the wire payload and in the audit trail
  Caller-supplied keys in `parameters=` win on collision (`setdefault`),
  so `parameters={"tool_name": "..."}` continues to work unchanged.
- **`AuthorizationDecision.status`** — read-only property returning the
  raw string form of `decision.value` (`'allowed'`, `'denied'`,
  `'pending'`). Use `result.status` for string comparisons and legacy
  code; use `result.decision` for the typed `Decision` enum.
- **`test_connection()`** result now carries `latency` and `latency_ms`
  (float, milliseconds, two decimal places) measuring the round-trip
  to the health endpoint. On failure both are `None`.

### Fixed
- CWG test plan compatibility: scenarios that pass `tool_name`,
  `description`, or `business_justification` no longer raise
  `TypeError`. Scenarios that compare `result.status` against strings
  no longer raise `AttributeError`.

### Zero Breaking Changes
- All existing callers continue to work. The three new kwargs are
  optional with `None` defaults. The `.status` property is additive —
  `result.decision` is unchanged. The new `latency`/`latency_ms`
  fields on `test_connection()` are additive.

## [2.5.2] - 2026-04-28

### Fixed — `risk_score` typed as `Optional[float]` (SDK-252)

`AuthorizationDecision.risk_score`, `ActionDetails.risk_score`,
`PolicyEvaluationResult.risk_score`, `AuthorizationError.risk_score`, and
`AscendClient.evaluate_policy(risk_score=...)` are now typed as
`Optional[float]` to match the backend, which has always returned float
values (e.g. `51.0`, `91.0`). The previous `Optional[int]` annotation
caused contract-test noise on every governed action and forced callers
to coerce. No behavioral change — values flow through unchanged.

## [2.5.1] - 2026-04-27

### Added — Governance routing fields on `evaluate_action` (SDK-251)

Two new optional kwargs and matching `AgentAction` fields surface the
backend governance enforcement that has been live since the G-P0-01 /
G-P0-02 work — the SDK now exposes them at the public API:

- **`mcp_server_name: Optional[str]`** — when set, the backend looks up
  `MCPServerConfig` by name at submit time and runs Layer 13 enforcement
  (G-P0-01). Unregistered, deactivated, or blocked-tool servers respond
  HTTP 403 and the response surfaces an `mcp_governance` block with the
  enforcement detail. Compliance: SOC 2 CC7.2, NIST AC-3.

- **`model_id: Optional[str]`** — when set, the backend looks up
  `DeployedModel` by registered identifier and gates the action on
  `compliance_status ∈ {approved, partially_approved}` (G-P0-02).
  Non-compliant or unregistered models respond HTTP 403 and the response
  surfaces a `model_governance` block with `registry_checked: True` and
  the compliance state. Compliance: SR-11-7, EU AI Act Art. 9.

Both fields are emitted at the **top level** of the submit body —
`data["mcp_server_name"]` and `data["model_id"]` — never nested inside
`action_details` or `context`. The backend reads only the top level.

### Validation

- `evaluate_action(...)` raises `ValidationError` immediately if either
  field is provided as a non-string or empty/whitespace string. Same
  check is mirrored inside `AgentAction.to_dict()` so the constraint
  cannot be bypassed by constructing the dataclass directly.
- Server-side validation continues to enforce the same constraints —
  the client check just saves a round-trip and yields a clearer error
  type than the backend's HTTP 422.

### Zero breaking changes

- Both kwargs default to `None`. Existing callers that don't pass them
  see identical behaviour: the backend follows its existing
  agent-link fallback paths (`registered_agent.model_id`, no MCP gating).
- Wire payload for callers that don't pass either field is byte-for-byte
  unchanged from 2.5.0.

## [2.5.0] - 2026-04-27

### Added — Enterprise Management Surface (G-P1-01..05, G-P2-01)

Pairs with backend ticket BACKEND-AUTH-001 (dual-auth retrofits) so that
all new methods below are reachable with the standard SDK API key.

**MCP server lifecycle (G-P1-01)** — wraps `/api/registry/mcp-servers/*`:
- `register_mcp_server(server_name, ...)` — POST register, returns 201
- `list_mcp_servers()` — GET list for org
- `get_mcp_server(server_name)` — GET full detail (tools, overrides, audit)
- `activate_mcp_server(server_name)` — POST, admin role required
- `deactivate_mcp_server(server_name, reason=None)` — POST, admin required;
  fail-secure: subsequent submits naming this server are denied via G-P0-01
- `delete_mcp_server(server_name)` — DELETE, admin role required
- `scan_mcp_network()` — parameter-free network discovery
- `get_mcp_health()` — health-monitor report across all org MCP servers

**Kill-switch trigger / release (G-P1-02)** — wraps
`/api/billing/kill-switch/{organization_id}/(trigger|release)`:
- `trigger_kill_switch(organization_id, reason)` — reason ≥10 chars enforced
  client-side (matches backend `KillSwitchRequest.min_length=10`)
- `release_kill_switch(organization_id, reason)` — same reason guard

**Orchestration management (G-P1-03)** — wraps `/api/v1/orchestration/*`:
- `register_topology(orchestrator_agent_id, worker_agent_ids)` —
  client-side validation: 1..20 workers, no duplicates
- `register_mcp_topology(orchestrator_agent_id, mcp_server_ids)` —
  same length/dedupe rules, integers only
- `cascade_kill(orchestrator_id, reason, dry_run=True)` — **SAFETY:**
  defaults to dry_run=True; caller must explicitly pass `dry_run=False`
  to execute. Backend retains JWT-admin-only auth on this endpoint.
- `get_orchestration_session(session_id)` — full audit trail
- `get_orchestration_session_risk(session_id)` — cumulative risk score
- `get_orchestration_stats()` — org-level summary stats

**Output filter (G-P1-04)** — wraps `/api/v1/output-filter/*`:
- `get_output_filter_config()` — read-only config
- `get_output_findings(limit, offset, category, severity)` — paginated;
  client-side cap mirrors backend `1..100`
- `get_output_findings_for_action(action_id)` — per-action findings
- `scan_output(content, agent_id, action_id=None)` — rate-limited 60/min
  server-side; fail-secure (BLOCKED on server exception)

**Supply chain visibility (G-P1-05)** — wraps `/api/v1/supply-chain/*`:
- `list_supply_chain_components(component_type, risk_level, ...)` —
  paginated component inventory
- `get_supply_chain_stats()` — CVE counts + risk distribution
- `get_supply_chain_impact(component_id)` — blast-radius lookup
- `get_cve_sync_status()` — NVD/OSV sync state
- `get_supply_chain_alerts(limit, acknowledged)` — polls `/api/alerts`
  with `type=supply_chain_cve`. Note: backend has no SSE/webhook for
  supply-chain alerts yet — polling is the only option.

**AuthorizationDecision typed-field promotion (G-P2-01)**

22 fields the platform has been returning all along (CVSS, MITRE, NIST,
code/prompt/MCP/model governance, processing time, alerts, workflow,
output scan, thresholds) are now first-class attributes:
- `correlation_id`, `cvss_score`, `cvss_severity`, `cvss_vector`
- `mitre_tactic`, `mitre_technique`, `nist_control`, `nist_description`
- `code_analysis`, `prompt_security`
- `mcp_governance`, `model_governance` (shipped 2026-04-26 with G-P0-01/02)
- `processing_time_ms`, `alert_triggered`, `alert_id`, `workflow_id`
- `policy_decision`, `matched_policies`, `matched_smart_rules`
- `output_scan_result`, `output_findings_count`, `thresholds`

### Zero Breaking Changes

`AuthorizationDecision.metadata` is unchanged: pre-2.5.0 callers reading
`decision.metadata["cvss_score"]` continue to work. The new typed fields
are populated *in addition to*, not instead of, the metadata entries.
If a caller-supplied metadata key conflicts with a top-level promoted
key, the caller's value is preserved unchanged (the typed field reflects
the top-level payload value).

### Notes

- All new methods raise `ValidationError` on bad input *before* any
  network call, so misuse fails fast.
- `cascade_kill` deliberately keeps a JWT-admin-only backend gate;
  the SDK wrapper surfaces 401/403 cleanly with the standard auth
  exception. Use `trigger_kill_switch()` for single-org isolated kills
  via the SDK API key.
- Supply-chain alert subscribe (webhook/SSE) is tracked separately as a
  backend follow-up — `get_supply_chain_alerts()` is a polling shim until
  that lands.

## [2.4.3] - 2026-04-23

### Security Fix
- **CRITICAL**: `submit_action` deprecation shim (Forms A and B) was silently
  dropping security-critical fields before forwarding to `evaluate_action`.
  Affected fields: `action_details` (read as wrong key `parameters`),
  `resource_id`, `risk_indicators`, `orchestration_session_id`,
  `parent_action_id`, `orchestration_depth`.

  **Impact**: `risk_indicators` not reaching the risk engine caused
  under-scoring of high-risk actions. `resource_id` absent from audit logs
  created SOC 2 / PCI-DSS compliance gaps.

  **Who is affected**: Any caller using `submit_action(action)` with an
  `AgentAction` instance (Form A) or dict (Form B) where any of the above
  fields were populated. Form C (kwargs) was not affected.

  **Action required**: Upgrade to 2.4.3. Long-term: migrate from deprecated
  `submit_action` to canonical `evaluate_action`.

### Migration Guide
The canonical method is `evaluate_action`. Replace:
```python
# Deprecated (submit_action — shim, scheduled for removal in 3.0.0)
result = client.submit_action(AgentAction(
    agent_id="bot-001",
    agent_name="My Bot",
    action_type="data_access",
    resource="customer_db",
    resource_id="CUST-123",
    action_details={"fields": ["name", "email"]},
    risk_indicators={"pii_involved": True}
))

# Canonical (evaluate_action)
result = client.evaluate_action(
    action_type="data_access",
    resource="customer_db",
    resource_id="CUST-123",
    parameters={"fields": ["name", "email"]},
    risk_indicators={"pii_involved": True}
)
```

## [2.4.2] - 2026-04-21

### Fixed
- **BUG-16-SHIM-KWARG**: submit_action shim now accepts kwarg-style
  calls. Previously raised TypeError "got multiple values for
  keyword argument 'action_type'". Positional calls continue to work
  with DeprecationWarning unchanged. Alan's Section 6.2 test path
  (kwarg syntax) is now unblocked.

### Changed
- README.md rewritten for accuracy against the verified 2.4.1 API
  surface. Removed unearned compliance claims and deprecated-API
  examples. Added Layer 13 MCP Governance, kill-switch integration,
  and platform capability sections (Agentless Discovery, Security
  Graph, Regulatory Evidence Package, BYOK).

## [2.4.1] - 2026-04-20

Patch release. Single-bug hotfix on top of 2.4.0. No API changes, no
deprecations, no behavior changes beyond the broken call path.

### Fixed

- **BUG-44** — `AscendClient.get_action_status()` hit a legacy endpoint
  (`/api/agent-action/status/{action_id}`) that does not accept
  `X-API-Key` authentication, causing every
  `evaluate_action(wait_for_decision=True)` call in 2.4.0 to raise
  `AuthenticationError` despite valid credentials. Status lookups now
  use `API_ENDPOINTS["action_status"]` → `/api/v1/actions/{action_id}/status`,
  matching the submit path and the authenticated `X-API-Key` surface.
  `wait_for_decision()` inherits the fix transparently (no signature
  change).

### Added

- Regression test `tests/test_client_endpoints.py` locking in the v1
  endpoint contract so the legacy path cannot be reintroduced.

## [2.4.0] - 2026-04-19

BUG-16 cohort remediation. First SDK release validated end-to-end by
the SEC-REL-001 doc/SDK contract gate. Before-state: 54 violations on
live-fire; after-state: 0 violations. No breaking changes: every
renamed symbol is preserved as a deprecated shim emitting
`DeprecationWarning` exactly once per process per name. Shims are
removed in 3.0.0.

### Added

- **`ascend.wrappers` subpackage** — governed alternatives for
  dangerous Python operations. Ships three modules:
  - `ascend.wrappers.subprocess` — drop-in replacement for stdlib
    `subprocess` with command-risk classification, shell-injection
    protection (`shell=True` blocked by default), and fail-closed
    governance. Compliance: CWE-78, CWE-77, MITRE T1059.004, NIST SI-10.
  - `ascend.wrappers.dynamic_code` — `safe_eval`, `safe_exec`, and
    `SafeEvaluator` with four-layer defense (AST analysis →
    governance check → restricted builtins → timeout). Fail-closed.
  - `ascend.wrappers.ast_analyzer` — standalone AST-based code
    safety analysis (`ASTAnalyzer`, `analyze_code`, `is_code_safe`).
- **`AscendClient.start_heartbeat(interval_seconds=60)`** and
  **`stop_heartbeat()`** — background daemon-thread heartbeat sender.
  Fail-secure: heartbeat failures never raise; scheduler keeps
  running. Integrated into `close()` for clean lifecycle.
- First-class exception types previously referenced in docs but
  absent from the SDK surface — `ServerError` (5xx), `NotFoundError`
  (404), `ConflictError` (409). All subclass `OWKAIError`.

### Deprecated (compat shims emit `DeprecationWarning` once per process)

- **Methods on `AscendClient`** (removal 3.0.0):
  - `submit_action(...)` → `evaluate_action(...)` *(BUG-16)*
  - `send_heartbeat(...)` → `heartbeat(...)` *(DOC-DRIFT-HEARTBEAT)*
  - `register_agent(...)` → `register(...)` *(DOC-DRIFT-REGISTER;
    fail-secure: refuses cross-identity registration)*
  - `wait_for_approval(...)` → `wait_for_decision(...)`
    *(DOC-DRIFT-APPROVAL)*
  - `get_agent(...)` → `get_agent_status()` *(DOC-DRIFT-AGENT;
    fail-secure: refuses cross-identity query)*
- **Exception aliases** (forward via `ascend` and
  `ascend.exceptions` module `__getattr__`):
  - `NetworkError` → `ConnectionError`
  - `AscendConnectionError` → `ConnectionError`
  - `AscendError` → `OWKAIError`
  - `AuthorizationDeniedError` → `AuthorizationError`
  - `AscendAuthenticationError` → `AuthenticationError`
  - `AscendRateLimitError` → `RateLimitError`
- **`ascend.constants.ActionType`** — canonical import path is
  `from ascend import ActionType` (`ascend.models` is the home).
  The `constants` re-export is preserved through 3.0.0.
- **`MCPGovernanceMiddleware.wrap(action_type, resource, func, ...)`**
  → use `.govern(action_type, resource, ...)` as a decorator. The
  `wrap` shim also accepts an inline `func` and returns the governed
  callable directly.

### Docs

- Rewrote `governance/audit-logging.md`, `governance/analytics.md`,
  `governance/compliance.md` to use existing SDK methods + REST
  `curl` examples. The higher-level `client.audit.*` /
  `client.analytics.*` / `client.compliance.*` namespace accessors
  are tracked as **SDK-NAMESPACE-FEATURE** for v2.5.
- Removed SDK code example for `create_smart_rule(...)` in
  `api/governance.md` (the method was never shipped); replaced with
  a concrete `POST /api/smart-rules` curl example.
- All 54 violations referenced in SEC-REL-001's live-fire report
  are now either (a) working against a deprecated shim, (b) using
  canonical names directly, or (c) shown as REST API examples.

### Fixed

- `ascend.wrappers.subprocess.classify_command_risk` — two latent
  classification-pattern false positives found during the port and
  fixed in canonical (and back-ported to the source location):
  - `chmod\s+777\s+/` now requires literal root at end-of-string;
    `chmod 777 /var/www` correctly classifies as `high` not `critical`.
  - `at\s+` prefixed with word-boundary so `cat`, `chat`,
    `dispatch`, etc. stop false-positiving into the `at`
    scheduled-task classifier.

### Security & Compliance

- All new code preserves the SDK's `FailMode.CLOSED` contract: no
  new network paths introduced by Class A shims (all delegate to
  canonical methods that already honor fail-secure); Class B
  wrappers default to `fail_mode="closed"`; the heartbeat scheduler
  is fire-and-forget and never propagates transport failures.
- Evidence: `tests/test_bug16_classB_failmode_closed.py` (11 Python
  tests) and `ow-ai-backend/sdk/nodejs/tests/heartbeat-failmode.test.ts`
  (5 Node tests).

### Contract gate (SEC-REL-001)

- **First release validated end-to-end by SEC-REL-001.**
- Live-fire before: 54 contract violations across 480/534 blocks.
- Live-fire after:  0 contract violations across 528/528 blocks.
  Audit ledger trigger: `sdk-2.4.0-validation-v1`, sdk_sha
  `ceb4ac72a0446856`, docs_sha `23bcfa7cffe7f4e6`.
- `surface_node.py` regex widened to accept TypeScript generic
  method signatures (`method<T extends ...>(...)`); the old
  narrower pattern falsely flagged generic methods as missing.

## [2.3.0] - 2026-04-17

### Added

- `AscendClient.evaluate_action(...)` now accepts three optional
  orchestration parameters for multi-agent workflows (FEAT-007):
  `orchestration_session_id`, `parent_action_id`, `orchestration_depth`.
  The server enforces cross-tenant scoping on `parent_action_id`,
  session-graft protection when both session and parent are provided,
  and caps depth at 0..5 (HTTP 422 outside that range). Fail-secure:
  any DB error during validation returns HTTP 403, never silently drops.
- `AgentAction` dataclass gained the three orchestration fields; they
  serialize through `to_dict()` only when set.
- `AscendClient.link_model_to_agent(agent_id, model_id)` — FEAT-001B:
  links a registered `DeployedModel` to an agent via
  `PUT /api/registry/agents/{agent_id}`. Server validates model
  tenant + compliance status (approved / partially_approved).
- `AscendClient.register_supply_chain_component(...)` — FEAT-005:
  posts to `POST /api/v1/supply-chain/components`. Supports the
  full `ComponentCreateRequest` schema; dual-auth (API key admin or
  JWT admin) on the server side as of this release.
- `AscendClient.get_pending_commands(agent_id=None)` — SEC-103: HTTP
  fallback for SQS kill-switch polling. Returns pending + delivered
  commands for this agent plus org-broadcast commands.
- `AscendClient.ack_command(command_id, agent_id=None)` — SEC-103:
  receipt-only acknowledge. Server rejects off-tenant / mismatched
  agent acks with HTTP 403 and writes immutable audit events
  (`AGENT_COMMAND_ACK_REJECTED`, `AGENT_COMMAND_ACKNOWLEDGED`).

### Changed

- `SDK_VERSION` in `ascend/constants.py` and `__version__` in
  `ascend/__init__.py` are now both `2.3.0` (previous drift between
  `2.1.1` and `2.2.0` resolved).

### Security

- Client-side guardrail on `orchestration_depth` mirrors the server
  cap so out-of-range values are rejected before any network call.
- `link_model_to_agent` and `register_supply_chain_component` both
  validate required parameters before submission.
- `get_pending_commands` / `ack_command` require an `agent_id` (either
  via arg or the client's bound id) — fail closed when missing.

### Compatibility

- No breaking changes. All new parameters default to `None` /
  sensible defaults. Existing callers of `evaluate_action` and
  `AgentAction` are unaffected.

## [2.2.0] - 2026-04-10

### Added

- `AscendClient.evaluate_mcp_action(...)` — FEAT-008 dedicated MCP
  governance pipeline endpoint (`POST /api/v1/mcp/actions/submit`).
- `MCPKillSwitchConsumer` — in-process consumer of MCP kill-switch
  SNS/SQS messages.

## [1.0.0] - 2025-12-04

### Added
- Initial release of Ascend AI SDK for Python
- `AscendClient` class for API interaction
- `AuthorizedAgent` wrapper for simplified authorization
- `AgentAction` model for action submission
- `ActionResult` model for authorization responses
- Comprehensive exception hierarchy for error handling
- Automatic retry with exponential backoff
- Dual authentication headers (Bearer + X-API-Key)
- TLS certificate validation
- Request correlation IDs for tracing
- API key masking in logs for security
- Full type hints for Python 3.8+
- Context manager support for automatic cleanup
- Connection testing with latency measurement
- Action listing with pagination
- Decision waiting with configurable timeout
- Input validation for all API calls
- Enterprise-grade security features:
  - SOC 2 Type II compliance
  - HIPAA compliance
  - PCI-DSS compliance
  - GDPR compliance
- Comprehensive documentation and examples
- Basic test suite

### Security
- API keys never logged in plaintext (masked to first/last 4 chars)
- All requests use HTTPS with certificate validation
- Dual authentication headers for compatibility
- Input validation to prevent injection attacks
- Rate limit handling with automatic retry

### Documentation
- Complete README with quick start guide
- Usage examples for common scenarios
- Error handling guide
- Best practices section
- API reference documentation
- Compliance information

### Testing
- Unit tests for core functionality
- Mock-based tests for API calls
- Validation tests for input checking
- Type checking with mypy

[1.0.0]: https://github.com/ascend-ai/ascend-sdk-python/releases/tag/v1.0.0
