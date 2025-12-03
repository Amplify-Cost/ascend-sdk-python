# Changelog

All notable changes to the ASCEND Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-03

### Added
- **Fail Mode Configuration**: `FailMode.CLOSED` (block on unreachable) and `FailMode.OPEN` (allow on unreachable)
- **Circuit Breaker Pattern**: Automatic failure detection with configurable thresholds and recovery
- **MCP Governance Decorator**: `@mcp_governance()` for wrapping MCP server tools with authorization
- **High-Risk Action Decorator**: `@high_risk_action()` for actions requiring human approval
- **MCPGovernanceMiddleware**: Class-based approach for governing multiple tools
- **MCPGovernanceConfig**: Configurable approval handling, callbacks, and error behavior
- **Structured JSON Logging**: `AscendLogger` class with API key masking
- **HMAC-SHA256 Request Signing**: Optional request integrity verification
- **Correlation IDs**: Automatic request tracing with `asc_*` prefixed IDs
- **Agent Registration**: `register()` method for agent lifecycle management
- **Action Completion Logging**: `log_action_completed()` and `log_action_failed()` methods
- **Approval Polling**: `check_approval()` method with configurable timeout and polling
- **Webhook Configuration**: `configure_webhook()` method for event subscriptions

### Changed
- **AscendClient**: Complete rewrite with enterprise-grade features
- **Decision Enum**: New `Decision` enum with `ALLOWED`, `DENIED`, `PENDING` values
- **AuthorizationDecision Model**: Enhanced with approval workflow fields
- **Package Name**: Changed from `owkai-sdk` to `ascend-sdk`

### Fixed
- CRIT-001: MCP decorator now passes `risk_level` and `require_human_approval` in context dict
- CRIT-004: Approval polling now checks correct boolean keys (`approved`, `denied`)

### Security
- API keys masked in all log output using regex pattern
- Circuit breaker prevents cascade failures
- Fail mode configuration for security-first deployments

### Compliance
- SOC 2 CC6.1: Access control and authorization
- HIPAA 164.312(e): Transmission security
- PCI-DSS 8.2: Authentication management
- NIST AI RMF: Risk management framework alignment

## [1.0.0] - 2025-11-15

### Added
- Initial SDK release with basic authorization
- `evaluate_action()` method for policy evaluation
- Basic error handling and retry logic
