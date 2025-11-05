"""
Enterprise Policy Import/Export Service

Supports:
- JSON, YAML, Cedar formats
- Validation before import
- Dry-run mode
- Conflict resolution strategies
- Backup creation

Author: OW-KAI Engineering Team
"""

import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models import EnterprisePolicy
import logging

logger = logging.getLogger(__name__)


class PolicyImportExportService:
    """Enterprise-grade policy import/export with validation"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # EXPORT METHODS
    # ========================================================================

    def export_policies(
        self,
        format: str = "json",
        filter_status: Optional[str] = None,
        policy_ids: Optional[List[int]] = None
    ) -> str:
        """
        Export policies to JSON/YAML format

        Args:
            format: "json" or "yaml"
            filter_status: Filter by status ("active", "inactive", "draft")
            policy_ids: Specific policy IDs to export (None = all)

        Returns:
            Formatted string (JSON or YAML)
        """
        # Build query
        query = self.db.query(EnterprisePolicy)

        if filter_status:
            query = query.filter(EnterprisePolicy.status == filter_status)

        if policy_ids:
            query = query.filter(EnterprisePolicy.id.in_(policy_ids))

        policies = query.all()

        # Convert to export format
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now(UTC).isoformat(),
            "total_policies": len(policies),
            "policies": [
                {
                    "id": p.id,
                    "policy_name": p.policy_name,
                    "description": p.description,
                    "effect": p.effect,
                    "actions": p.actions or [],
                    "resources": p.resources or [],
                    "conditions": p.conditions or {},
                    "priority": p.priority or 100,
                    "status": p.status,
                    "created_by": p.created_by,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                }
                for p in policies
            ]
        }

        # Format output
        if format == "yaml":
            return yaml.dump(export_data, default_flow_style=False, sort_keys=False)
        else:  # JSON (default)
            return json.dumps(export_data, indent=2)

    def export_to_cedar(self, policy_ids: Optional[List[int]] = None) -> str:
        """
        Export policies to Cedar policy language format

        Cedar format example:
        permit(
            principal == User::"alice",
            action in [Action::"read", Action::"write"],
            resource == Database::"production"
        );
        """
        query = self.db.query(EnterprisePolicy)
        if policy_ids:
            query = query.filter(EnterprisePolicy.id.in_(policy_ids))

        policies = query.all()

        cedar_policies = []
        for p in policies:
            # Convert to Cedar syntax
            effect = p.effect if p.effect in ["permit", "forbid"] else "forbid"
            actions = ', '.join([f'Action::"{a}"' for a in (p.actions or ["*"])])
            resources = ', '.join([f'Resource::"{r}"' for r in (p.resources or ["*"])])

            cedar = f"""// {p.policy_name}
// {p.description or ""}
{effect}(
    principal,
    action in [{actions}],
    resource in [{resources}]
);
"""
            cedar_policies.append(cedar)

        return "\n".join(cedar_policies)

    # ========================================================================
    # IMPORT METHODS
    # ========================================================================

    def import_policies(
        self,
        import_data: str,
        format: str = "json",
        dry_run: bool = False,
        conflict_resolution: str = "skip",  # "skip", "overwrite", "merge"
        created_by: str = "import"
    ) -> Dict[str, Any]:
        """
        Import policies from JSON/YAML format

        Args:
            import_data: JSON or YAML string
            format: "json" or "yaml"
            dry_run: If True, validate but don't commit
            conflict_resolution: How to handle existing policies
            created_by: Email of user performing import

        Returns:
            Import results with counts and errors
        """
        # Parse input
        try:
            if format == "yaml":
                data = yaml.safe_load(import_data)
            else:
                data = json.loads(import_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse {format.upper()}: {str(e)}"
            }

        # Validate format
        if "policies" not in data:
            return {
                "success": False,
                "error": "Invalid format: missing 'policies' key"
            }

        policies_to_import = data["policies"]

        # Process each policy
        imported = []
        skipped = []
        errors = []
        conflicts = []

        for policy_data in policies_to_import:
            try:
                # Validate required fields
                validation_errors = self._validate_policy_data(policy_data)
                if validation_errors:
                    errors.append({
                        "policy_name": policy_data.get("policy_name", "Unknown"),
                        "errors": validation_errors
                    })
                    continue

                # Check for existing policy with same name
                existing = self.db.query(EnterprisePolicy).filter(
                    EnterprisePolicy.policy_name == policy_data["policy_name"]
                ).first()

                if existing:
                    if conflict_resolution == "skip":
                        skipped.append(policy_data["policy_name"])
                        conflicts.append({
                            "policy_name": policy_data["policy_name"],
                            "reason": "Policy with same name exists",
                            "resolution": "skipped"
                        })
                        continue
                    elif conflict_resolution == "overwrite":
                        # Update existing policy
                        if not dry_run:
                            existing.description = policy_data.get("description", "")
                            existing.effect = policy_data["effect"]
                            existing.actions = policy_data.get("actions", [])
                            existing.resources = policy_data.get("resources", [])
                            existing.conditions = policy_data.get("conditions", {})
                            existing.priority = policy_data.get("priority", 100)
                            existing.updated_at = datetime.now(UTC)
                        imported.append(policy_data["policy_name"])
                        conflicts.append({
                            "policy_name": policy_data["policy_name"],
                            "reason": "Policy exists",
                            "resolution": "overwritten"
                        })
                        continue

                # Create new policy
                if not dry_run:
                    new_policy = EnterprisePolicy(
                        policy_name=policy_data["policy_name"],
                        description=policy_data.get("description", ""),
                        effect=policy_data["effect"],
                        actions=policy_data.get("actions", []),
                        resources=policy_data.get("resources", []),
                        conditions=policy_data.get("conditions", {}),
                        priority=policy_data.get("priority", 100),
                        status=policy_data.get("status", "active"),
                        created_by=created_by
                    )
                    self.db.add(new_policy)

                imported.append(policy_data["policy_name"])

            except Exception as e:
                errors.append({
                    "policy_name": policy_data.get("policy_name", "Unknown"),
                    "error": str(e)
                })

        # Commit if not dry run
        if not dry_run and len(imported) > 0:
            try:
                self.db.commit()
                logger.info(f"✅ Imported {len(imported)} policies")
            except Exception as e:
                self.db.rollback()
                return {
                    "success": False,
                    "error": f"Database commit failed: {str(e)}"
                }

        return {
            "success": True,
            "dry_run": dry_run,
            "total_processed": len(policies_to_import),
            "imported": len(imported),
            "skipped": len(skipped),
            "errors": len(errors),
            "imported_policies": imported,
            "skipped_policies": skipped,
            "conflicts": conflicts,
            "error_details": errors
        }

    def _validate_policy_data(self, policy_data: Dict[str, Any]) -> List[str]:
        """Validate policy data before import"""
        errors = []

        # Required fields
        if "policy_name" not in policy_data or not policy_data["policy_name"]:
            errors.append("policy_name is required")

        if "effect" not in policy_data or not policy_data["effect"]:
            errors.append("effect is required")

        if policy_data.get("effect") not in ["allow", "deny", "permit", "forbid", "require_approval"]:
            errors.append(f"Invalid effect: {policy_data.get('effect')}")

        # Validate actions (if present)
        if "actions" in policy_data and not isinstance(policy_data["actions"], list):
            errors.append("actions must be a list")

        # Validate resources (if present)
        if "resources" in policy_data and not isinstance(policy_data["resources"], list):
            errors.append("resources must be a list")

        # Validate conditions (if present)
        if "conditions" in policy_data and not isinstance(policy_data["conditions"], dict):
            errors.append("conditions must be a dictionary")

        # Validate priority (if present)
        if "priority" in policy_data:
            try:
                priority = int(policy_data["priority"])
                if priority < 0 or priority > 1000:
                    errors.append("priority must be between 0 and 1000")
            except (ValueError, TypeError):
                errors.append("priority must be an integer")

        return errors

    # ========================================================================
    # BACKUP METHODS
    # ========================================================================

    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a full backup of all policies

        Returns:
            Backup metadata and export data
        """
        if not backup_name:
            backup_name = f"policy_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        export_data = self.export_policies(format="json")

        return {
            "success": True,
            "backup_name": backup_name,
            "created_at": datetime.now(UTC).isoformat(),
            "total_policies": len(self.db.query(EnterprisePolicy).all()),
            "backup_data": export_data
        }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_import_template(self, format: str = "json") -> str:
        """
        Get a template for importing policies

        Returns:
            Template string in requested format
        """
        template = {
            "version": "1.0",
            "policies": [
                {
                    "policy_name": "Example Policy - Block Production Deletes",
                    "description": "Prevent deletion operations on production databases",
                    "effect": "deny",
                    "actions": ["delete", "drop"],
                    "resources": ["database:production:*"],
                    "conditions": {
                        "environment": "production"
                    },
                    "priority": 100,
                    "status": "active"
                },
                {
                    "policy_name": "Example Policy - Require Approval for Financial Data",
                    "description": "Financial data modifications require approval",
                    "effect": "require_approval",
                    "actions": ["write", "modify"],
                    "resources": ["financial:*"],
                    "conditions": {},
                    "priority": 90,
                    "status": "active"
                }
            ]
        }

        if format == "yaml":
            return yaml.dump(template, default_flow_style=False, sort_keys=False)
        else:
            return json.dumps(template, indent=2)


def create_import_export_service(db: Session) -> PolicyImportExportService:
    """Factory function to create import/export service"""
    return PolicyImportExportService(db)
