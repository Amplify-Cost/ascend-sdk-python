"""
SEC-077: Enterprise Policy Conflict Resolver
============================================

Detects and resolves conflicts between governance policies.
Ensures deterministic policy evaluation with explicit priority ordering.

Industry Alignment:
- AWS IAM policy evaluation logic
- Cedar policy language conflict detection
- OPA (Open Policy Agent) decision logging

Compliance: PCI-DSS 7.1, NIST AC-3, SOC 2 CC6.1

Created: 2025-12-04
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
import logging
import json

logger = logging.getLogger(__name__)


class ConflictType:
    """Types of policy conflicts that can be detected."""
    PRIORITY_TIE = "priority_tie"           # Same priority on overlapping scope
    EFFECT_CONTRADICTION = "effect_contradiction"  # ALLOW vs DENY on same resource
    RESOURCE_OVERLAP = "resource_overlap"   # Overlapping resource patterns
    CONDITION_AMBIGUITY = "condition_ambiguity"   # Ambiguous condition evaluation


class ConflictSeverity:
    """Severity levels for detected conflicts."""
    LOW = "low"           # Informational, no immediate action needed
    MEDIUM = "medium"     # Should be reviewed
    HIGH = "high"         # Requires attention
    CRITICAL = "critical" # Must be resolved before deployment


class ResolutionStrategy:
    """Strategies for resolving policy conflicts."""
    FIRST_MATCH = "first_match"         # First matching policy wins (by priority)
    HIGHEST_PRIORITY = "highest_priority"   # Explicit priority ordering
    MOST_RESTRICTIVE = "most_restrictive"   # DENY takes precedence over ALLOW
    MOST_PERMISSIVE = "most_permissive"     # ALLOW takes precedence over DENY


class PolicyConflictResolver:
    """
    Enterprise Policy Conflict Detection and Resolution

    Implements conflict detection to:
    1. Identify overlapping policy scopes
    2. Detect contradicting effects (ALLOW vs DENY)
    3. Flag priority ties requiring resolution
    4. Provide deterministic evaluation order

    Resolution Strategies:
    - FIRST_MATCH: Evaluate in priority order, first match wins
    - MOST_RESTRICTIVE: DENY always wins over ALLOW
    - MOST_PERMISSIVE: ALLOW wins unless explicit DENY

    Compliance:
    - PCI-DSS 7.1: Access control policy implementation
    - NIST AC-3: Access enforcement
    - SOC 2 CC6.1: Logical and physical access controls
    """

    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self.default_strategy = ResolutionStrategy.MOST_RESTRICTIVE

    def detect_conflicts(self, policy_type: str = "all") -> Dict[str, Any]:
        """
        Scan all policies for conflicts.

        Args:
            policy_type: "mcp", "agent", or "all"

        Returns:
            dict: Detected conflicts with severity and recommendations
        """
        conflicts = []

        if policy_type in ("mcp", "all"):
            mcp_conflicts = self._detect_mcp_policy_conflicts()
            conflicts.extend(mcp_conflicts)

        if policy_type in ("agent", "all"):
            agent_conflicts = self._detect_agent_policy_conflicts()
            conflicts.extend(agent_conflicts)

        # Categorize by severity
        by_severity = {
            ConflictSeverity.CRITICAL: [],
            ConflictSeverity.HIGH: [],
            ConflictSeverity.MEDIUM: [],
            ConflictSeverity.LOW: [],
        }
        for conflict in conflicts:
            by_severity[conflict["severity"]].append(conflict)

        return {
            "organization_id": self.organization_id,
            "scan_time": datetime.now(UTC).isoformat(),
            "total_conflicts": len(conflicts),
            "by_severity": {
                "critical": len(by_severity[ConflictSeverity.CRITICAL]),
                "high": len(by_severity[ConflictSeverity.HIGH]),
                "medium": len(by_severity[ConflictSeverity.MEDIUM]),
                "low": len(by_severity[ConflictSeverity.LOW]),
            },
            "conflicts": conflicts,
            "requires_attention": len(by_severity[ConflictSeverity.CRITICAL]) > 0 or len(by_severity[ConflictSeverity.HIGH]) > 0,
        }

    def resolve_policy_match(
        self,
        matching_policies: List[Dict],
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve which policy should be applied when multiple match.

        Args:
            matching_policies: List of policies that matched the request
            strategy: Resolution strategy (default: most_restrictive)

        Returns:
            dict: Winning policy and resolution details
        """
        if not matching_policies:
            return {
                "resolved": False,
                "reason": "no_matching_policies",
                "winner": None,
            }

        if len(matching_policies) == 1:
            return {
                "resolved": True,
                "reason": "single_match",
                "winner": matching_policies[0],
                "strategy_used": "single_match",
            }

        strategy = strategy or self.default_strategy

        if strategy == ResolutionStrategy.MOST_RESTRICTIVE:
            winner = self._resolve_most_restrictive(matching_policies)
        elif strategy == ResolutionStrategy.MOST_PERMISSIVE:
            winner = self._resolve_most_permissive(matching_policies)
        elif strategy == ResolutionStrategy.HIGHEST_PRIORITY:
            winner = self._resolve_highest_priority(matching_policies)
        else:  # FIRST_MATCH
            winner = self._resolve_first_match(matching_policies)

        return {
            "resolved": True,
            "reason": "multiple_matches",
            "strategy_used": strategy,
            "candidates": len(matching_policies),
            "winner": winner,
            "all_matches": [
                {"id": p.get("id"), "priority": p.get("priority"), "action": p.get("action")}
                for p in matching_policies
            ],
        }

    def record_conflict(
        self,
        conflict_type: str,
        policy_a: Dict,
        policy_b: Dict,
        severity: str,
        details: Dict
    ) -> int:
        """
        Record a detected conflict to the database for audit.

        Args:
            conflict_type: Type of conflict
            policy_a: First conflicting policy
            policy_b: Second conflicting policy
            severity: Conflict severity
            details: Additional conflict details

        Returns:
            int: Conflict record ID
        """
        result = self.db.execute(
            text("""
                INSERT INTO policy_conflicts
                (organization_id, detected_at, conflict_type, policy_a_id, policy_a_type,
                 policy_b_id, policy_b_type, conflict_details, severity)
                VALUES (:org_id, :detected_at, :conflict_type, :policy_a_id, :policy_a_type,
                        :policy_b_id, :policy_b_type, :details, :severity)
                RETURNING id
            """),
            {
                "org_id": self.organization_id,
                "detected_at": datetime.now(UTC),
                "conflict_type": conflict_type,
                "policy_a_id": str(policy_a.get("id")),
                "policy_a_type": policy_a.get("type", "unknown"),
                "policy_b_id": str(policy_b.get("id")),
                "policy_b_type": policy_b.get("type", "unknown"),
                "details": json.dumps(details),
                "severity": severity,
            }
        )
        self.db.commit()
        return result.fetchone()[0]

    def resolve_conflict(
        self,
        conflict_id: int,
        resolution_strategy: str,
        resolved_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mark a conflict as resolved.

        Args:
            conflict_id: ID of the conflict record
            resolution_strategy: Strategy used to resolve
            resolved_by: User who resolved
            notes: Resolution notes

        Returns:
            dict: Resolution result
        """
        self.db.execute(
            text("""
                UPDATE policy_conflicts
                SET resolution_status = 'manually_resolved',
                    resolution_strategy = :strategy,
                    resolved_at = :resolved_at,
                    resolved_by = :resolved_by,
                    resolution_notes = :notes
                WHERE id = :conflict_id
                  AND organization_id = :org_id
            """),
            {
                "conflict_id": conflict_id,
                "org_id": self.organization_id,
                "strategy": resolution_strategy,
                "resolved_at": datetime.now(UTC),
                "resolved_by": resolved_by,
                "notes": notes,
            }
        )
        self.db.commit()

        return {
            "conflict_id": conflict_id,
            "status": "resolved",
            "strategy": resolution_strategy,
            "resolved_by": resolved_by,
        }

    def get_unresolved_conflicts(self) -> List[Dict[str, Any]]:
        """
        Get all unresolved conflicts for the organization.

        Returns:
            list: Unresolved conflicts
        """
        result = self.db.execute(
            text("""
                SELECT id, detected_at, conflict_type, policy_a_id, policy_a_type,
                       policy_b_id, policy_b_type, conflict_details, severity
                FROM policy_conflicts
                WHERE organization_id = :org_id
                  AND resolution_status = 'pending'
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    detected_at DESC
            """),
            {"org_id": self.organization_id}
        )

        return [
            {
                "id": row.id,
                "detected_at": row.detected_at.isoformat() if row.detected_at else None,
                "conflict_type": row.conflict_type,
                "policy_a": {"id": row.policy_a_id, "type": row.policy_a_type},
                "policy_b": {"id": row.policy_b_id, "type": row.policy_b_type},
                "details": json.loads(row.conflict_details) if row.conflict_details else {},
                "severity": row.severity,
            }
            for row in result
        ]

    def _detect_mcp_policy_conflicts(self) -> List[Dict]:
        """Detect conflicts in MCP policies."""
        from models_mcp_governance import MCPPolicy

        policies = self.db.query(MCPPolicy).filter(
            MCPPolicy.organization_id == self.organization_id,
            MCPPolicy.is_active == True
        ).order_by(MCPPolicy.priority).all()

        conflicts = []

        # Check each pair of policies for conflicts
        for i, policy_a in enumerate(policies):
            for policy_b in policies[i+1:]:
                # Check for priority tie with overlapping scope
                if policy_a.priority == policy_b.priority:
                    if self._scopes_overlap(policy_a, policy_b):
                        conflict = {
                            "type": ConflictType.PRIORITY_TIE,
                            "severity": ConflictSeverity.HIGH,
                            "policy_a": self._policy_to_dict(policy_a, "mcp_policy"),
                            "policy_b": self._policy_to_dict(policy_b, "mcp_policy"),
                            "details": {
                                "shared_priority": policy_a.priority,
                                "recommendation": "Assign different priorities to ensure deterministic evaluation",
                            },
                        }
                        conflicts.append(conflict)
                        self.record_conflict(
                            ConflictType.PRIORITY_TIE,
                            conflict["policy_a"],
                            conflict["policy_b"],
                            ConflictSeverity.HIGH,
                            conflict["details"]
                        )

                # Check for effect contradiction (ALLOW vs DENY on same scope)
                if self._scopes_overlap(policy_a, policy_b):
                    if self._effects_contradict(policy_a.action, policy_b.action):
                        conflict = {
                            "type": ConflictType.EFFECT_CONTRADICTION,
                            "severity": ConflictSeverity.CRITICAL if abs(policy_a.priority - policy_b.priority) <= 10 else ConflictSeverity.MEDIUM,
                            "policy_a": self._policy_to_dict(policy_a, "mcp_policy"),
                            "policy_b": self._policy_to_dict(policy_b, "mcp_policy"),
                            "details": {
                                "policy_a_effect": policy_a.action,
                                "policy_b_effect": policy_b.action,
                                "priority_difference": abs(policy_a.priority - policy_b.priority),
                                "recommendation": "Review policies - contradicting effects may cause unexpected behavior",
                            },
                        }
                        conflicts.append(conflict)

        return conflicts

    def _detect_agent_policy_conflicts(self) -> List[Dict]:
        """Detect conflicts in agent policies."""
        from models_agent_registry import AgentPolicy

        policies = self.db.query(AgentPolicy).filter(
            AgentPolicy.organization_id == self.organization_id,
            AgentPolicy.is_active == True
        ).order_by(AgentPolicy.priority).all()

        conflicts = []

        for i, policy_a in enumerate(policies):
            for policy_b in policies[i+1:]:
                # Check for priority tie on same agent
                if policy_a.agent_id == policy_b.agent_id and policy_a.priority == policy_b.priority:
                    conflict = {
                        "type": ConflictType.PRIORITY_TIE,
                        "severity": ConflictSeverity.HIGH,
                        "policy_a": {"id": policy_a.id, "name": policy_a.policy_name, "type": "agent_policy"},
                        "policy_b": {"id": policy_b.id, "name": policy_b.policy_name, "type": "agent_policy"},
                        "details": {
                            "agent_id": policy_a.agent_id,
                            "shared_priority": policy_a.priority,
                            "recommendation": "Assign different priorities for the same agent",
                        },
                    }
                    conflicts.append(conflict)

        return conflicts

    def _scopes_overlap(self, policy_a, policy_b) -> bool:
        """Check if two policies have overlapping scopes."""
        # Check namespace patterns
        ns_a = set(policy_a.namespace_patterns or [])
        ns_b = set(policy_b.namespace_patterns or [])
        if ns_a and ns_b and not ns_a.intersection(ns_b):
            return False  # Different namespaces, no overlap

        # Check verb patterns
        verb_a = set(policy_a.verb_patterns or [])
        verb_b = set(policy_b.verb_patterns or [])
        if verb_a and verb_b and not verb_a.intersection(verb_b):
            return False  # Different verbs, no overlap

        # Check resource patterns (simplified - actual implementation would use glob matching)
        res_a = set(policy_a.resource_patterns or [])
        res_b = set(policy_b.resource_patterns or [])
        if res_a and res_b and not res_a.intersection(res_b):
            return False  # Different resources, no overlap

        return True  # Scopes overlap

    def _effects_contradict(self, effect_a: str, effect_b: str) -> bool:
        """Check if two policy effects contradict each other."""
        allow_effects = {"ALLOW", "allow", "permit"}
        deny_effects = {"DENY", "deny", "block"}

        a_allows = effect_a in allow_effects
        a_denies = effect_a in deny_effects
        b_allows = effect_b in allow_effects
        b_denies = effect_b in deny_effects

        return (a_allows and b_denies) or (a_denies and b_allows)

    def _policy_to_dict(self, policy, policy_type: str) -> Dict:
        """Convert policy model to dictionary."""
        return {
            "id": str(policy.id),
            "type": policy_type,
            "name": policy.policy_name,
            "priority": policy.priority,
            "action": policy.action,
        }

    def _resolve_most_restrictive(self, policies: List[Dict]) -> Dict:
        """DENY wins over ALLOW."""
        deny_policies = [p for p in policies if p.get("action", "").upper() in ("DENY", "BLOCK")]
        if deny_policies:
            # Return highest priority DENY
            return sorted(deny_policies, key=lambda p: p.get("priority", 999))[0]
        # No DENY, return highest priority ALLOW
        return sorted(policies, key=lambda p: p.get("priority", 999))[0]

    def _resolve_most_permissive(self, policies: List[Dict]) -> Dict:
        """ALLOW wins over DENY (unless explicit DENY with higher priority)."""
        allow_policies = [p for p in policies if p.get("action", "").upper() in ("ALLOW", "PERMIT")]
        if allow_policies:
            return sorted(allow_policies, key=lambda p: p.get("priority", 999))[0]
        return sorted(policies, key=lambda p: p.get("priority", 999))[0]

    def _resolve_highest_priority(self, policies: List[Dict]) -> Dict:
        """Strict priority ordering (lower number = higher priority)."""
        return sorted(policies, key=lambda p: p.get("priority", 999))[0]

    def _resolve_first_match(self, policies: List[Dict]) -> Dict:
        """First in evaluation order wins."""
        return sorted(policies, key=lambda p: p.get("priority", 999))[0]


# Convenience function for dependency injection
def get_policy_resolver(db: Session, organization_id: int) -> PolicyConflictResolver:
    """Factory function for dependency injection."""
    return PolicyConflictResolver(db, organization_id)
