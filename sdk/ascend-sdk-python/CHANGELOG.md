# Changelog

All notable changes to the Ascend AI SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
