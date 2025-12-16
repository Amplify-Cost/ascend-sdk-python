"""
ASCEND Lambda Authorizer - CloudWatch Integration
==================================================

GW-006: Structured logging and metrics for CloudWatch.

Features:
    - JSON structured logging for CloudWatch Logs Insights
    - Custom metrics for authorization decisions
    - Latency tracking
    - Error rate monitoring
    - Cache hit/miss tracking

Metrics Published:
    - AscendAuthorizer/Decisions (with dimensions: Status, AgentId)
    - AscendAuthorizer/Latency (milliseconds)
    - AscendAuthorizer/Errors (with dimension: ErrorType)
    - AscendAuthorizer/CacheHits
    - AscendAuthorizer/CacheMisses

Log Format:
    JSON with fields: timestamp, level, message, correlation_id, agent_id,
    action_type, status, risk_score, latency_ms, error

Compliance: SOC 2 AU-6, NIST AU-2/AU-3
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import json
import logging
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class AuthorizationMetrics:
    """
    Metrics for a single authorization request.

    Collected during request processing and published to CloudWatch
    at the end of the request.
    """
    # Request identification
    correlation_id: str = ""
    agent_id: str = ""
    action_type: str = ""

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # Decision
    status: str = ""  # approved, pending_approval, denied, error
    risk_score: float = 0.0
    risk_level: str = ""

    # Cache
    cache_hit: bool = False

    # Error tracking
    error: Optional[str] = None
    error_type: Optional[str] = None

    # ASCEND response
    ascend_action_id: Optional[int] = None
    ascend_latency_ms: Optional[float] = None

    @property
    def total_latency_ms(self) -> float:
        """Total request latency in milliseconds."""
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    def finalize(self) -> None:
        """Mark metrics as complete."""
        self.end_time = time.time()

    def to_log_entry(self) -> Dict[str, Any]:
        """Convert to structured log entry."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "correlation_id": self.correlation_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "status": self.status,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "cache_hit": self.cache_hit,
            "latency_ms": round(self.total_latency_ms, 2),
            "ascend_latency_ms": self.ascend_latency_ms,
            "ascend_action_id": self.ascend_action_id,
            "error": self.error,
            "error_type": self.error_type
        }


class StructuredLogger:
    """
    JSON structured logger for CloudWatch Logs Insights.

    Outputs logs in JSON format for easy querying and analysis
    in CloudWatch Logs Insights.
    """

    def __init__(self, name: str = "ascend-authorizer"):
        """
        Initialize structured logger.

        Args:
            name: Logger name
        """
        self.name = name
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for JSON output."""
        # Get root logger
        root_logger = logging.getLogger()

        # Set level from environment or default to INFO
        import os
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Check if handler already exists
        if not root_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JsonFormatter())
            root_logger.addHandler(handler)

    def log_authorization(self, metrics: AuthorizationMetrics) -> None:
        """
        Log authorization decision with full metrics.

        Args:
            metrics: Collected metrics for the request
        """
        metrics.finalize()
        entry = metrics.to_log_entry()
        entry["event_type"] = "authorization_decision"
        entry["logger"] = self.name

        # Determine log level based on outcome
        if metrics.error:
            level = logging.ERROR
        elif metrics.status == "denied":
            level = logging.WARNING
        else:
            level = logging.INFO

        logger.log(level, json.dumps(entry))

    def log_cache_event(
        self,
        event_type: str,
        cache_key: str,
        hit: bool,
        ttl_remaining: Optional[float] = None
    ) -> None:
        """Log cache hit/miss event."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": f"cache_{event_type}",
            "logger": self.name,
            "cache_key": cache_key,
            "cache_hit": hit,
            "ttl_remaining_seconds": ttl_remaining
        }
        logger.debug(json.dumps(entry))

    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None
    ) -> None:
        """Log error with context."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": "error",
            "logger": self.name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        logger.error(json.dumps(entry))


class JsonFormatter(logging.Formatter):
    """JSON log formatter for CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Check if message is already JSON
        try:
            if record.msg.startswith("{"):
                return record.msg
        except (AttributeError, TypeError):
            pass

        # Create JSON log entry
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }

        # Add exception info if present
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry)


class MetricsPublisher:
    """
    Publishes custom metrics to CloudWatch.

    Uses embedded metric format (EMF) for efficient metric publishing
    without separate API calls.
    """

    NAMESPACE = "AscendAuthorizer"

    def __init__(self, enabled: bool = True):
        """
        Initialize metrics publisher.

        Args:
            enabled: Whether to publish metrics
        """
        self.enabled = enabled
        logger.info(f"GW-006: Metrics publisher initialized - enabled={enabled}")

    def publish_authorization_metrics(
        self,
        metrics: AuthorizationMetrics
    ) -> None:
        """
        Publish authorization metrics using CloudWatch EMF.

        Args:
            metrics: Authorization metrics to publish
        """
        if not self.enabled:
            return

        # Create EMF log entry
        emf_entry = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.NAMESPACE,
                        "Dimensions": [["Status"], ["AgentId"]],
                        "Metrics": [
                            {"Name": "Decisions", "Unit": "Count"},
                            {"Name": "Latency", "Unit": "Milliseconds"},
                            {"Name": "RiskScore", "Unit": "None"}
                        ]
                    }
                ]
            },
            # Dimension values
            "Status": metrics.status or "unknown",
            "AgentId": metrics.agent_id or "unknown",
            # Metric values
            "Decisions": 1,
            "Latency": metrics.total_latency_ms,
            "RiskScore": metrics.risk_score
        }

        # Log in EMF format
        print(json.dumps(emf_entry))

        # Publish cache metrics
        if metrics.cache_hit:
            self._publish_cache_hit()
        else:
            self._publish_cache_miss()

        # Publish error metrics
        if metrics.error:
            self._publish_error(metrics.error_type or "Unknown")

    def _publish_cache_hit(self) -> None:
        """Publish cache hit metric."""
        emf_entry = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.NAMESPACE,
                        "Dimensions": [[]],
                        "Metrics": [
                            {"Name": "CacheHits", "Unit": "Count"}
                        ]
                    }
                ]
            },
            "CacheHits": 1
        }
        print(json.dumps(emf_entry))

    def _publish_cache_miss(self) -> None:
        """Publish cache miss metric."""
        emf_entry = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.NAMESPACE,
                        "Dimensions": [[]],
                        "Metrics": [
                            {"Name": "CacheMisses", "Unit": "Count"}
                        ]
                    }
                ]
            },
            "CacheMisses": 1
        }
        print(json.dumps(emf_entry))

    def _publish_error(self, error_type: str) -> None:
        """Publish error metric."""
        emf_entry = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.NAMESPACE,
                        "Dimensions": [["ErrorType"]],
                        "Metrics": [
                            {"Name": "Errors", "Unit": "Count"}
                        ]
                    }
                ]
            },
            "ErrorType": error_type,
            "Errors": 1
        }
        print(json.dumps(emf_entry))


@contextmanager
def track_authorization(correlation_id: str = None):
    """
    Context manager for tracking authorization metrics.

    Usage:
        with track_authorization("req-123") as metrics:
            metrics.agent_id = "my-agent"
            # ... process request ...
            metrics.status = "approved"

    Args:
        correlation_id: Request correlation ID

    Yields:
        AuthorizationMetrics: Metrics object to populate
    """
    import uuid

    metrics = AuthorizationMetrics(
        correlation_id=correlation_id or str(uuid.uuid4())[:8]
    )

    try:
        yield metrics
    except Exception as e:
        metrics.error = str(e)
        metrics.error_type = type(e).__name__
        metrics.status = "error"
        raise
    finally:
        metrics.finalize()
        get_structured_logger().log_authorization(metrics)
        get_metrics_publisher().publish_authorization_metrics(metrics)


# Singleton instances
_logger_instance: Optional[StructuredLogger] = None
_metrics_instance: Optional[MetricsPublisher] = None


def get_structured_logger() -> StructuredLogger:
    """Get or create structured logger instance."""
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = StructuredLogger()

    return _logger_instance


def get_metrics_publisher(enabled: bool = True) -> MetricsPublisher:
    """Get or create metrics publisher instance."""
    global _metrics_instance

    if _metrics_instance is None:
        _metrics_instance = MetricsPublisher(enabled=enabled)

    return _metrics_instance
