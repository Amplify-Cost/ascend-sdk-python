"""
Enterprise Policy Conflict Detection Engine

Detects and analyzes conflicts between authorization policies to prevent:
- Contradictory rules (deny vs allow on same resource)
- Priority conflicts (overlapping policies with different effects)
- Resource hierarchy conflicts (parent/child resource contradictions)
- Condition conflicts (incompatible conditions)

Author: OW-KAI Engineering Team
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, UTC
from models import EnterprisePolicy
from sqlalchemy.orm import Session
import json
import re
import logging

logger = logging.getLogger(__name__)


class ConflictType:
    """Conflict severity and type classifications"""
    CRITICAL = "critical"  # Deny vs Allow on same resource
    HIGH = "high"  # Priority conflicts
    MEDIUM = "medium"  # Condition conflicts
    LOW = "low"  # Minor overlaps


class PolicyConflict:
    """Represents a detected conflict between policies"""

    def __init__(
        self,
        conflict_type: str,
        severity: str,
        policy1_id: int,
        policy2_id: int,
        policy1_name: str,
        policy2_name: str,
        description: str,
        resolution_suggestions: List[str]
    ):
        self.conflict_type = conflict_type
        self.severity = severity
        self.policy1_id = policy1_id
        self.policy2_id = policy2_id
        self.policy1_name = policy1_name
        self.policy2_name = policy2_name
        self.description = description
        self.resolution_suggestions = resolution_suggestions
        self.detected_at = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "policy1": {
                "id": self.policy1_id,
                "name": self.policy1_name
            },
            "policy2": {
                "id": self.policy2_id,
                "name": self.policy2_name
            },
            "description": self.description,
            "resolution_suggestions": self.resolution_suggestions,
            "detected_at": self.detected_at.isoformat()
        }


class PolicyConflictDetector:
    """Enterprise-grade policy conflict detection engine"""

    def __init__(self, db: Session):
        self.db = db
        self.conflicts: List[PolicyConflict] = []

    def detect_conflicts(
        self,
        new_policy: Dict[str, Any],
        policy_id: Optional[int] = None
    ) -> List[PolicyConflict]:
        """
        Detect conflicts between a new/updated policy and existing policies

        Args:
            new_policy: Policy data to check for conflicts
            policy_id: If updating existing policy, its ID (to exclude from comparison)

        Returns:
            List of detected conflicts
        """
        self.conflicts = []

        # Get all active policies except the one being updated
        query = self.db.query(EnterprisePolicy).filter(
            EnterprisePolicy.status == "active"
        )
        if policy_id:
            query = query.filter(EnterprisePolicy.id != policy_id)

        existing_policies = query.all()

        for existing in existing_policies:
            # Convert existing policy to dict for comparison
            existing_dict = {
                "id": existing.id,
                "policy_name": existing.policy_name,
                "effect": existing.effect,
                "actions": existing.actions or [],
                "resources": existing.resources or [],
                "conditions": existing.conditions or {},
                "priority": existing.priority or 0
            }

            # Check for various conflict types
            self._check_effect_conflict(new_policy, existing_dict)
            self._check_priority_conflict(new_policy, existing_dict)
            self._check_resource_hierarchy_conflict(new_policy, existing_dict)
            self._check_condition_conflict(new_policy, existing_dict)

        return self.conflicts

    def _check_effect_conflict(
        self,
        policy1: Dict[str, Any],
        policy2: Dict[str, Any]
    ) -> None:
        """Detect deny vs allow conflicts on overlapping resources"""

        # Check if effects are contradictory
        if policy1.get("effect") == policy2.get("effect"):
            return  # Same effect, no conflict

        # Check if one denies and one allows
        effects = {policy1.get("effect"), policy2.get("effect")}
        if not ({"deny", "permit"}.issubset(effects) or {"deny", "allow"}.issubset(effects)):
            return  # Not a deny/allow conflict

        # Check for overlapping actions
        actions1 = set(policy1.get("actions", []))
        actions2 = set(policy2.get("actions", []))

        # Wildcard handling
        if "*" in actions1 or "*" in actions2:
            overlapping_actions = True
        else:
            overlapping_actions = bool(actions1 & actions2)

        if not overlapping_actions:
            return

        # Check for overlapping resources
        resources1 = policy1.get("resources", [])
        resources2 = policy2.get("resources", [])

        overlapping_resources = self._find_overlapping_resources(resources1, resources2)

        if not overlapping_resources:
            return

        # CONFLICT DETECTED: Deny vs Allow on same resource
        conflict = PolicyConflict(
            conflict_type="effect_contradiction",
            severity=ConflictType.CRITICAL,
            policy1_id=policy1.get("id", 0),
            policy2_id=policy2.get("id"),
            policy1_name=policy1.get("policy_name", "New Policy"),
            policy2_name=policy2.get("policy_name"),
            description=f"Policy effects conflict: '{policy1.get('effect')}' vs '{policy2.get('effect')}' "
                       f"on overlapping resources: {', '.join(overlapping_resources[:3])}",
            resolution_suggestions=[
                "Refine resource patterns to avoid overlap",
                "Use priority to explicitly define precedence",
                "Change one policy effect to match the other",
                f"Deny policies take precedence - {policy2.get('policy_name')} will override"
            ]
        )
        self.conflicts.append(conflict)

    def _check_priority_conflict(
        self,
        policy1: Dict[str, Any],
        policy2: Dict[str, Any]
    ) -> None:
        """Detect policies with same priority on overlapping resources"""

        priority1 = policy1.get("priority", 0)
        priority2 = policy2.get("priority", 0)

        # Only flag if priorities are the same
        if priority1 != priority2:
            return

        # Check for overlapping resources
        resources1 = policy1.get("resources", [])
        resources2 = policy2.get("resources", [])

        overlapping = self._find_overlapping_resources(resources1, resources2)

        if overlapping:
            conflict = PolicyConflict(
                conflict_type="priority_conflict",
                severity=ConflictType.HIGH,
                policy1_id=policy1.get("id", 0),
                policy2_id=policy2.get("id"),
                policy1_name=policy1.get("policy_name", "New Policy"),
                policy2_name=policy2.get("policy_name"),
                description=f"Policies have same priority ({priority1}) on overlapping resources. "
                           f"Evaluation order is non-deterministic.",
                resolution_suggestions=[
                    "Assign different priorities to ensure deterministic evaluation",
                    "Higher priority = evaluated first",
                    "Deny policies automatically take precedence regardless of priority"
                ]
            )
            self.conflicts.append(conflict)

    def _check_resource_hierarchy_conflict(
        self,
        policy1: Dict[str, Any],
        policy2: Dict[str, Any]
    ) -> None:
        """Detect parent/child resource conflicts"""

        resources1 = policy1.get("resources", [])
        resources2 = policy2.get("resources", [])

        for r1 in resources1:
            for r2 in resources2:
                # Check if one resource is parent of the other
                if self._is_parent_resource(r1, r2) or self._is_parent_resource(r2, r1):
                    # Only flag if effects differ
                    if policy1.get("effect") != policy2.get("effect"):
                        conflict = PolicyConflict(
                            conflict_type="resource_hierarchy",
                            severity=ConflictType.MEDIUM,
                            policy1_id=policy1.get("id", 0),
                            policy2_id=policy2.get("id"),
                            policy1_name=policy1.get("policy_name", "New Policy"),
                            policy2_name=policy2.get("policy_name"),
                            description=f"Parent/child resource conflict: '{r1}' vs '{r2}' "
                                       f"with different effects",
                            resolution_suggestions=[
                                "Ensure child resource policies are more specific",
                                "Use priority to define parent/child precedence",
                                "Document hierarchical policy intent"
                            ]
                        )
                        self.conflicts.append(conflict)
                        break

    def _check_condition_conflict(
        self,
        policy1: Dict[str, Any],
        policy2: Dict[str, Any]
    ) -> None:
        """Detect incompatible conditions on overlapping policies"""

        conditions1 = policy1.get("conditions", {})
        conditions2 = policy2.get("conditions", {})

        # Check if policies target same resources
        resources1 = policy1.get("resources", [])
        resources2 = policy2.get("resources", [])

        if not self._find_overlapping_resources(resources1, resources2):
            return

        # Check for contradictory conditions
        for key in set(conditions1.keys()) & set(conditions2.keys()):
            val1 = conditions1[key]
            val2 = conditions2[key]

            # If same key has different values, flag as potential conflict
            if val1 != val2:
                conflict = PolicyConflict(
                    conflict_type="condition_mismatch",
                    severity=ConflictType.MEDIUM,
                    policy1_id=policy1.get("id", 0),
                    policy2_id=policy2.get("id"),
                    policy1_name=policy1.get("policy_name", "New Policy"),
                    policy2_name=policy2.get("policy_name"),
                    description=f"Conflicting conditions on key '{key}': {val1} vs {val2}",
                    resolution_suggestions=[
                        "Review condition logic for consistency",
                        "Use condition operators (any_of, all_of) for flexibility",
                        "Consider merging policies with similar intent"
                    ]
                )
                self.conflicts.append(conflict)

    def _find_overlapping_resources(
        self,
        resources1: List[str],
        resources2: List[str]
    ) -> List[str]:
        """Find resources that overlap between two lists"""
        overlapping = []

        for r1 in resources1:
            for r2 in resources2:
                if self._resources_overlap(r1, r2):
                    overlapping.append(f"{r1} ↔ {r2}")

        return overlapping

    def _resources_overlap(self, resource1: str, resource2: str) -> bool:
        """Check if two resource patterns overlap"""

        # Wildcard handling
        if resource1 == "*" or resource2 == "*":
            return True

        # Exact match
        if resource1 == resource2:
            return True

        # Pattern matching (e.g., database:* matches database:production:*)
        if "*" in resource1:
            pattern = resource1.replace("*", ".*")
            if re.match(pattern, resource2):
                return True

        if "*" in resource2:
            pattern = resource2.replace("*", ".*")
            if re.match(pattern, resource1):
                return True

        # Hierarchy check (database:prod:users overlaps with database:prod:*)
        parts1 = resource1.split(":")
        parts2 = resource2.split(":")

        # Check if one is a prefix of the other
        min_len = min(len(parts1), len(parts2))
        if parts1[:min_len] == parts2[:min_len]:
            return True

        return False

    def _is_parent_resource(self, parent: str, child: str) -> bool:
        """Check if parent resource is an ancestor of child resource"""

        # Remove wildcards for hierarchy check
        parent_clean = parent.replace("*", "")
        child_clean = child.replace("*", "")

        # Parent must be shorter and match beginning
        return len(parent_clean) < len(child_clean) and child_clean.startswith(parent_clean)

    def analyze_all_policies(self) -> Dict[str, Any]:
        """
        Analyze all active policies for conflicts (system-wide scan)

        Returns:
            Comprehensive conflict report
        """
        all_conflicts = []
        policies = self.db.query(EnterprisePolicy).filter(
            EnterprisePolicy.status == "active"
        ).all()

        # Compare each policy with every other policy
        for i, policy1 in enumerate(policies):
            for policy2 in policies[i+1:]:
                detector = PolicyConflictDetector(self.db)

                policy1_dict = {
                    "id": policy1.id,
                    "policy_name": policy1.policy_name,
                    "effect": policy1.effect,
                    "actions": policy1.actions or [],
                    "resources": policy1.resources or [],
                    "conditions": policy1.conditions or {},
                    "priority": policy1.priority or 0
                }

                policy2_dict = {
                    "id": policy2.id,
                    "policy_name": policy2.policy_name,
                    "effect": policy2.effect,
                    "actions": policy2.actions or [],
                    "resources": policy2.resources or [],
                    "conditions": policy2.conditions or {},
                    "priority": policy2.priority or 0
                }

                # Run all conflict checks
                detector._check_effect_conflict(policy1_dict, policy2_dict)
                detector._check_priority_conflict(policy1_dict, policy2_dict)
                detector._check_resource_hierarchy_conflict(policy1_dict, policy2_dict)
                detector._check_condition_conflict(policy1_dict, policy2_dict)

                all_conflicts.extend(detector.conflicts)

        # Categorize by severity
        critical = [c for c in all_conflicts if c.severity == ConflictType.CRITICAL]
        high = [c for c in all_conflicts if c.severity == ConflictType.HIGH]
        medium = [c for c in all_conflicts if c.severity == ConflictType.MEDIUM]
        low = [c for c in all_conflicts if c.severity == ConflictType.LOW]

        return {
            "total_conflicts": len(all_conflicts),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
            "conflicts": [c.to_dict() for c in all_conflicts],
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "policies_analyzed": len(policies)
        }


# Global instance factory
def create_conflict_detector(db: Session) -> PolicyConflictDetector:
    """Factory function to create conflict detector instance"""
    return PolicyConflictDetector(db)
