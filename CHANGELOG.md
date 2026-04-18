# Changelog

All notable changes to the Ascend AI SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
