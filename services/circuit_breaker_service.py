"""
SEC-077: Enterprise Circuit Breaker Service
============================================

Banking-level circuit breaker implementation for MCP server resilience.
Prevents cascade failures and enables automatic recovery.

Pattern: CLOSED -> OPEN -> HALF_OPEN -> CLOSED

Industry Alignment:
- Netflix Hystrix circuit breaker pattern
- AWS Application Load Balancer health checks
- Datadog synthetic monitoring patterns

Compliance: SOC 2 CC7.1, NIST SI-4, PCI-DSS 6.5.5

Created: 2025-12-04
"""

from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
import logging
import hashlib

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states following industry-standard pattern."""
    CLOSED = "CLOSED"       # Normal operation, requests pass through
    OPEN = "OPEN"           # Circuit tripped, requests blocked
    HALF_OPEN = "HALF_OPEN" # Testing recovery, limited requests


class CircuitBreakerService:
    """
    Enterprise Circuit Breaker for MCP Server Governance

    Implements the circuit breaker pattern to:
    1. Detect failing MCP servers automatically
    2. Prevent cascade failures across the system
    3. Enable automatic recovery with gradual traffic restoration
    4. Provide audit trail for compliance (SOC 2 CC7.1)

    State Machine:
    ┌─────────┐  failure_threshold  ┌─────────┐  timeout  ┌───────────┐
    │ CLOSED  │ ─────────────────→  │  OPEN   │ ────────→ │ HALF_OPEN │
    │(healthy)│                     │(blocked)│           │ (testing) │
    └────┬────┘ ←───────────────────└─────────┘ ←──────── └─────┬─────┘
         │         recovery                       failure        │
         └───────────────────────────────────────────────────────┘
                             success
    """

    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id

    def record_success(self, server_id: str) -> Dict[str, Any]:
        """
        Record successful request to MCP server.
        May trigger state transition: HALF_OPEN -> CLOSED

        Args:
            server_id: MCP server identifier

        Returns:
            dict: Current circuit state and metrics
        """
        from models_mcp_governance import MCPServer

        server = self._get_server(server_id)
        if not server:
            return {"error": "Server not found", "server_id": server_id}

        previous_state = server.circuit_state
        now = datetime.now(UTC)

        if server.circuit_state == CircuitState.HALF_OPEN.value:
            # Increment success counter in half-open state
            server.circuit_half_open_success_count += 1

            if server.circuit_half_open_success_count >= server.circuit_required_successes:
                # Recovery successful - close circuit
                self._transition_state(server, CircuitState.CLOSED, "successful_recovery")
                logger.info(
                    f"SEC-077: Circuit CLOSED for {server_id} - recovery successful "
                    f"({server.circuit_half_open_success_count} probes passed)"
                )

        elif server.circuit_state == CircuitState.CLOSED.value:
            # Normal operation - reset failure count on success
            server.circuit_failure_count = 0

        self.db.commit()

        return {
            "server_id": server_id,
            "previous_state": previous_state,
            "current_state": server.circuit_state,
            "failure_count": server.circuit_failure_count,
            "half_open_successes": server.circuit_half_open_success_count,
        }

    def record_failure(self, server_id: str, error_details: Optional[str] = None) -> Dict[str, Any]:
        """
        Record failed request to MCP server.
        May trigger state transition: CLOSED -> OPEN or HALF_OPEN -> OPEN

        Args:
            server_id: MCP server identifier
            error_details: Optional error message for audit

        Returns:
            dict: Current circuit state and whether circuit tripped
        """
        from models_mcp_governance import MCPServer

        server = self._get_server(server_id)
        if not server:
            return {"error": "Server not found", "server_id": server_id}

        previous_state = server.circuit_state
        now = datetime.now(UTC)
        tripped = False

        server.circuit_failure_count += 1
        server.circuit_last_failure_at = now

        if server.circuit_state == CircuitState.CLOSED.value:
            if server.circuit_failure_count >= server.circuit_failure_threshold:
                # Trip circuit open
                self._transition_state(server, CircuitState.OPEN, "failure_threshold_exceeded")
                tripped = True
                logger.warning(
                    f"SEC-077: Circuit OPEN for {server_id} - "
                    f"{server.circuit_failure_count} consecutive failures"
                )

        elif server.circuit_state == CircuitState.HALF_OPEN.value:
            # Probe failed - back to open
            self._transition_state(server, CircuitState.OPEN, "probe_failed")
            tripped = True
            logger.warning(
                f"SEC-077: Circuit reopened for {server_id} - probe failed during recovery"
            )

        # Log event for audit trail
        self._log_event(
            server_id=server_id,
            previous_state=previous_state,
            new_state=server.circuit_state,
            trigger_reason="failure" if not tripped else "circuit_tripped",
            failure_count=server.circuit_failure_count,
            error_details=error_details
        )

        self.db.commit()

        return {
            "server_id": server_id,
            "previous_state": previous_state,
            "current_state": server.circuit_state,
            "circuit_tripped": tripped,
            "failure_count": server.circuit_failure_count,
            "threshold": server.circuit_failure_threshold,
        }

    def check_circuit(self, server_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if requests are allowed through the circuit.
        May trigger state transition: OPEN -> HALF_OPEN (timeout elapsed)

        Args:
            server_id: MCP server identifier

        Returns:
            tuple: (is_allowed: bool, circuit_info: dict)
        """
        server = self._get_server(server_id)
        if not server:
            return False, {"error": "Server not found", "server_id": server_id}

        now = datetime.now(UTC)

        if server.circuit_state == CircuitState.CLOSED.value:
            return True, {
                "allowed": True,
                "state": CircuitState.CLOSED.value,
                "server_id": server_id,
            }

        if server.circuit_state == CircuitState.OPEN.value:
            # Check if recovery timeout has elapsed
            if server.circuit_opened_at:
                timeout = timedelta(seconds=server.circuit_recovery_timeout_seconds)
                if now >= server.circuit_opened_at + timeout:
                    # Transition to half-open for recovery testing
                    self._transition_state(server, CircuitState.HALF_OPEN, "recovery_timeout_elapsed")
                    self.db.commit()
                    logger.info(
                        f"SEC-077: Circuit HALF_OPEN for {server_id} - attempting recovery"
                    )
                    return True, {
                        "allowed": True,
                        "state": CircuitState.HALF_OPEN.value,
                        "server_id": server_id,
                        "note": "Recovery probe - monitoring for success/failure",
                    }

            # Circuit still open
            time_remaining = None
            if server.circuit_opened_at:
                timeout = timedelta(seconds=server.circuit_recovery_timeout_seconds)
                remaining = (server.circuit_opened_at + timeout) - now
                time_remaining = max(0, int(remaining.total_seconds()))

            return False, {
                "allowed": False,
                "state": CircuitState.OPEN.value,
                "server_id": server_id,
                "recovery_in_seconds": time_remaining,
                "failure_count": server.circuit_failure_count,
            }

        if server.circuit_state == CircuitState.HALF_OPEN.value:
            # Allow probe request through
            return True, {
                "allowed": True,
                "state": CircuitState.HALF_OPEN.value,
                "server_id": server_id,
                "probe_number": server.circuit_half_open_success_count + 1,
                "required_successes": server.circuit_required_successes,
            }

        return False, {"error": "Unknown circuit state", "state": server.circuit_state}

    def force_open(self, server_id: str, reason: str = "manual_override") -> Dict[str, Any]:
        """
        Force circuit open (emergency shutdown).
        Requires audit trail for compliance.

        Args:
            server_id: MCP server identifier
            reason: Reason for manual override

        Returns:
            dict: Result of operation
        """
        server = self._get_server(server_id)
        if not server:
            return {"error": "Server not found", "server_id": server_id}

        previous_state = server.circuit_state
        self._transition_state(server, CircuitState.OPEN, f"manual_force_open: {reason}")
        self.db.commit()

        logger.warning(f"SEC-077: Circuit FORCE OPENED for {server_id} - reason: {reason}")

        return {
            "server_id": server_id,
            "previous_state": previous_state,
            "current_state": CircuitState.OPEN.value,
            "reason": reason,
            "action": "force_open",
        }

    def force_close(self, server_id: str, reason: str = "manual_reset") -> Dict[str, Any]:
        """
        Force circuit closed (manual recovery).
        Requires audit trail for compliance.

        Args:
            server_id: MCP server identifier
            reason: Reason for manual reset

        Returns:
            dict: Result of operation
        """
        server = self._get_server(server_id)
        if not server:
            return {"error": "Server not found", "server_id": server_id}

        previous_state = server.circuit_state
        self._transition_state(server, CircuitState.CLOSED, f"manual_force_close: {reason}")
        server.circuit_failure_count = 0
        server.circuit_half_open_success_count = 0
        self.db.commit()

        logger.info(f"SEC-077: Circuit FORCE CLOSED for {server_id} - reason: {reason}")

        return {
            "server_id": server_id,
            "previous_state": previous_state,
            "current_state": CircuitState.CLOSED.value,
            "reason": reason,
            "action": "force_close",
        }

    def get_circuit_status(self, server_id: str) -> Dict[str, Any]:
        """
        Get current circuit breaker status for a server.

        Returns:
            dict: Complete circuit state information
        """
        server = self._get_server(server_id)
        if not server:
            return {"error": "Server not found", "server_id": server_id}

        return {
            "server_id": server_id,
            "server_name": server.server_name,
            "state": server.circuit_state,
            "failure_count": server.circuit_failure_count,
            "failure_threshold": server.circuit_failure_threshold,
            "last_failure_at": server.circuit_last_failure_at.isoformat() if server.circuit_last_failure_at else None,
            "opened_at": server.circuit_opened_at.isoformat() if server.circuit_opened_at else None,
            "last_state_change": server.circuit_last_state_change.isoformat() if server.circuit_last_state_change else None,
            "recovery_timeout_seconds": server.circuit_recovery_timeout_seconds,
            "half_open_successes": server.circuit_half_open_success_count,
            "required_successes": server.circuit_required_successes,
            "total_trips": server.circuit_total_trips,
            "is_healthy": server.circuit_state == CircuitState.CLOSED.value,
        }

    def get_all_circuits(self) -> Dict[str, Any]:
        """
        Get circuit status for all MCP servers in the organization.

        Returns:
            dict: Summary of all circuit states
        """
        from models_mcp_governance import MCPServer

        servers = self.db.query(MCPServer).filter(
            MCPServer.organization_id == self.organization_id,
            MCPServer.is_active == True
        ).all()

        circuits = []
        summary = {"closed": 0, "open": 0, "half_open": 0}

        for server in servers:
            state = server.circuit_state
            if state == CircuitState.CLOSED.value:
                summary["closed"] += 1
            elif state == CircuitState.OPEN.value:
                summary["open"] += 1
            elif state == CircuitState.HALF_OPEN.value:
                summary["half_open"] += 1

            circuits.append({
                "server_id": server.server_id,
                "server_name": server.server_name,
                "state": state,
                "failure_count": server.circuit_failure_count,
                "total_trips": server.circuit_total_trips,
            })

        return {
            "organization_id": self.organization_id,
            "total_servers": len(servers),
            "summary": summary,
            "circuits": circuits,
            "health_score": (summary["closed"] / len(servers) * 100) if servers else 100,
        }

    def _get_server(self, server_id: str):
        """Get MCP server with organization isolation."""
        from models_mcp_governance import MCPServer

        return self.db.query(MCPServer).filter(
            MCPServer.server_id == server_id,
            MCPServer.organization_id == self.organization_id
        ).first()

    def _transition_state(self, server, new_state: CircuitState, reason: str):
        """
        Transition circuit to new state with audit logging.
        """
        previous_state = server.circuit_state
        now = datetime.now(UTC)

        # Log the transition
        self._log_event(
            server_id=server.server_id,
            previous_state=previous_state,
            new_state=new_state.value,
            trigger_reason=reason,
            failure_count=server.circuit_failure_count,
        )

        # Update server state
        server.circuit_state = new_state.value
        server.circuit_last_state_change = now

        if new_state == CircuitState.OPEN:
            server.circuit_opened_at = now
            server.circuit_total_trips += 1
            server.circuit_half_open_success_count = 0
        elif new_state == CircuitState.CLOSED:
            server.circuit_opened_at = None
            server.circuit_failure_count = 0
            server.circuit_half_open_success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            server.circuit_half_open_success_count = 0

    def _log_event(
        self,
        server_id: str,
        previous_state: str,
        new_state: str,
        trigger_reason: str,
        failure_count: int,
        error_details: Optional[str] = None
    ):
        """
        Log circuit breaker event to immutable audit table.
        Compliance: SOC 2 AU-6, PCI-DSS 10.2
        """
        from sqlalchemy import text

        correlation_id = hashlib.sha256(
            f"{server_id}:{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:64]

        self.db.execute(
            text("""
                INSERT INTO circuit_breaker_events
                (organization_id, server_id, event_time, previous_state, new_state,
                 trigger_reason, failure_count, error_details, correlation_id)
                VALUES (:org_id, :server_id, :event_time, :prev, :new,
                        :reason, :count, :error, :corr_id)
            """),
            {
                "org_id": self.organization_id,
                "server_id": server_id,
                "event_time": datetime.now(UTC),
                "prev": previous_state,
                "new": new_state,
                "reason": trigger_reason,
                "count": failure_count,
                "error": error_details,
                "corr_id": correlation_id,
            }
        )


# Convenience function for route handlers
def get_circuit_breaker(db: Session, organization_id: int) -> CircuitBreakerService:
    """Factory function for dependency injection."""
    return CircuitBreakerService(db, organization_id)
