# Changelog

All notable changes to the ASCEND Node.js SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-03

### Added
- **Fail Mode Configuration**: `FailMode.CLOSED` and `FailMode.OPEN` for resilience control
- **Circuit Breaker Pattern**: `CircuitBreaker` class with configurable failure threshold and recovery
- **MCP Governance Wrapper**: `mcpGovernance()` higher-order function for tool authorization
- **High-Risk Action Wrapper**: `highRiskAction()` for actions requiring human approval
- **MCPGovernanceMiddleware**: Class for managing governance across multiple tools
- **MCPGovernanceConfig**: TypeScript interface for approval handling configuration
- **Structured JSON Logging**: `AscendLogger` class with API key masking
- **HMAC-SHA256 Request Signing**: Optional request integrity verification
- **Correlation IDs**: Automatic request tracing
- **Agent Registration**: `register()` method for agent lifecycle management
- **Action Completion Logging**: `logActionCompleted()` and `logActionFailed()` methods
- **Approval Polling**: `checkApproval()` method with configurable timeout
- **Webhook Configuration**: `configureWebhook()` method for event subscriptions
- **Metrics Collection**: `MetricsCollector` class for SDK telemetry
- **Request Interceptors**: `InterceptorManager` for request/response hooks
- **Batch Operations**: `evaluateBatch()` for multiple action evaluation

### Changed
- **AscendClient**: Complete TypeScript rewrite with full type safety
- **Decision Enum**: New enum with `ALLOWED`, `DENIED`, `PENDING` values
- **Package Name**: Changed from `@owkai/sdk` to `@ascend/sdk`
- **Error Classes**: Enhanced with typed error codes and details

### Fixed
- WARN-004: Rate limit retry now capped at 300 seconds (5 minutes) to prevent DoS

### Security
- API keys masked in all log output
- Rate limit retry cap prevents infinite waits
- Circuit breaker prevents cascade failures
- TypeScript strict mode for type safety

### Compliance
- SOC 2 CC6.1: Access control and authorization
- HIPAA 164.312(e): Transmission security
- PCI-DSS 8.2: Authentication management
- NIST AI RMF: Risk management framework alignment

## [1.1.0] - 2025-12-01

### Added
- Batch action evaluation
- Metrics collection
- Request interceptors

## [1.0.0] - 2025-11-15

### Added
- Initial SDK release with basic authorization
- `evaluateAction()` method for policy evaluation
- Basic error handling and retry logic
