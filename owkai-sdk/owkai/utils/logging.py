"""
OW-AI SDK Logging Utilities

Enterprise-grade logging with audit trail support.
Designed for compliance with SOX, PCI-DSS, HIPAA requirements.

Security:
- No sensitive data (API keys, tokens) in logs
- Structured logging for SIEM integration
- Configurable log levels
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from owkai.auth import mask_api_key


class SDKLogger:
    """
    Enterprise SDK logger with audit capabilities.

    Features:
    - Structured JSON logging support
    - Automatic sensitive data masking
    - Request/response correlation
    - SIEM-compatible format
    """

    def __init__(
        self,
        name: str = "owkai.sdk",
        level: int = logging.INFO,
        *,
        json_format: bool = False,
        include_timestamp: bool = True,
    ) -> None:
        """
        Initialize SDK logger.

        Args:
            name: Logger name
            level: Logging level
            json_format: Use JSON output format
            include_timestamp: Include ISO timestamp
        """
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._json_format = json_format
        self._include_timestamp = include_timestamp

        # Avoid duplicate handlers
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setLevel(level)

            if json_format:
                formatter = logging.Formatter("%(message)s")
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )

            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def _format_message(
        self,
        message: str,
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format log message, optionally as JSON."""
        if not self._json_format:
            if extra:
                extra_str = " ".join(f"{k}={v}" for k, v in extra.items())
                return f"{message} | {extra_str}"
            return message

        # JSON format
        import json

        log_data = {
            "message": message,
            "sdk": "owkai",
            "sdk_version": "0.1.0",
        }

        if self._include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()

        if extra:
            log_data.update(extra)

        return json.dumps(log_data)

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove or mask sensitive data from log payload.

        Masks:
        - API keys
        - Authorization headers
        - Passwords
        - Tokens
        """
        sanitized = {}
        sensitive_keys = {
            "api_key",
            "apikey",
            "authorization",
            "password",
            "token",
            "secret",
            "credential",
        }

        for key, value in data.items():
            key_lower = key.lower()

            # Check if key is sensitive
            if any(s in key_lower for s in sensitive_keys):
                if isinstance(value, str) and value.startswith("owkai_"):
                    sanitized[key] = mask_api_key(value)
                else:
                    sanitized[key] = "****"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value

        return sanitized

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message."""
        sanitized = self._sanitize_data(extra) if extra else None
        self._logger.debug(self._format_message(message, extra=sanitized))

    def info(self, message: str, **extra: Any) -> None:
        """Log info message."""
        sanitized = self._sanitize_data(extra) if extra else None
        self._logger.info(self._format_message(message, extra=sanitized))

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message."""
        sanitized = self._sanitize_data(extra) if extra else None
        self._logger.warning(self._format_message(message, extra=sanitized))

    def error(self, message: str, **extra: Any) -> None:
        """Log error message."""
        sanitized = self._sanitize_data(extra) if extra else None
        self._logger.error(self._format_message(message, extra=sanitized))

    def audit(
        self,
        action: str,
        *,
        action_id: Optional[int] = None,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        risk_score: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """
        Log audit event for compliance.

        Creates structured audit log entry suitable for
        SOX, PCI-DSS, HIPAA compliance requirements.
        """
        audit_data = {
            "audit_event": True,
            "action": action,
        }

        if action_id is not None:
            audit_data["action_id"] = action_id
        if agent_id is not None:
            audit_data["agent_id"] = agent_id
        if status is not None:
            audit_data["status"] = status
        if risk_score is not None:
            audit_data["risk_score"] = risk_score

        audit_data.update(extra)
        sanitized = self._sanitize_data(audit_data)

        self._logger.info(self._format_message(f"AUDIT: {action}", extra=sanitized))


# Global logger instance
_default_logger: Optional[SDKLogger] = None


def get_logger(
    name: str = "owkai.sdk",
    level: int = logging.INFO,
    *,
    json_format: bool = False,
) -> SDKLogger:
    """
    Get or create SDK logger.

    Args:
        name: Logger name
        level: Logging level
        json_format: Use JSON output format

    Returns:
        SDKLogger instance
    """
    global _default_logger

    if _default_logger is None or _default_logger._logger.name != name:
        _default_logger = SDKLogger(name=name, level=level, json_format=json_format)

    return _default_logger


def configure_logging(
    level: int = logging.INFO,
    json_format: bool = False,
) -> SDKLogger:
    """
    Configure global SDK logging.

    Args:
        level: Logging level (default: INFO)
        json_format: Use JSON output format (default: False)

    Returns:
        Configured SDKLogger instance
    """
    global _default_logger
    _default_logger = SDKLogger(level=level, json_format=json_format)
    return _default_logger
