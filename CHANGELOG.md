# Changelog

All notable changes to the Ascend AI SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
