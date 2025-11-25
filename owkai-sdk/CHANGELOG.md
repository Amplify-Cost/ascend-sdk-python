# Changelog

All notable changes to the OW-AI SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-25

### Added

- Initial release of OW-AI Enterprise SDK
- `OWKAIClient` for synchronous API interactions
- `AsyncOWKAIClient` for asynchronous operations
- Agent action submission with `execute_action()`
- Approval workflow polling with `wait_for_approval()`
- boto3 auto-patching for AWS governance
- Comprehensive exception hierarchy
- Enterprise-grade logging with audit support
- Retry logic with exponential backoff
- API key authentication with validation
- Full test suite with pytest

### Security

- API keys validated on initialization
- Sensitive data masked in logs and exceptions
- TLS 1.2+ required for all API communication
- Constant-time comparison for key validation

### Documentation

- Complete README with examples
- API reference documentation
- Security and compliance guidelines
- Development setup instructions

## [Unreleased]

### Planned

- WebSocket support for real-time approval notifications
- Batch action submission
- Local policy caching for offline evaluation
- Plugin architecture for custom integrations
