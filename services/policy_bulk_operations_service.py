"""
Enterprise Policy Bulk Operations Service

Supports:
- Bulk enable/disable
- Bulk delete (with backup)
- Bulk priority updates
- Bulk tag operations

Author: OW-KAI Engineering Team
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models import EnterprisePolicy, AuditLog
import logging
import json

logger = logging.getLogger(__name__)


class PolicyBulkOperationsService:
    """Enterprise bulk policy operations with safety features"""

    def __init__(self, db: Session):
        self.db = db

    def bulk_update_status(
        self,
        policy_ids: List[int],
        new_status: str,
        reason: str,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Bulk enable/disable policies

        Args:
            policy_ids: List of policy IDs to update
            new_status: "active" or "inactive"
            reason: Reason for status change
            user_email: Email of user performing operation

        Returns:
            Operation results
        """
        updated = []
        errors = []

        for policy_id in policy_ids:
            try:
                policy = self.db.query(EnterprisePolicy).filter(
                    EnterprisePolicy.id == policy_id
                ).first()

                if not policy:
                    errors.append({
                        "policy_id": policy_id,
                        "error": "Policy not found"
                    })
                    continue

                old_status = policy.status
                policy.status = new_status
                policy.updated_at = datetime.now(UTC)

                updated.append({
                    "policy_id": policy_id,
                    "policy_name": policy.policy_name,
                    "old_status": old_status,
                    "new_status": new_status
                })

                # Create audit log
                self._create_audit_log(
                    user_email=user_email,
                    action="bulk_status_update",
                    policy_id=policy_id,
                    details={
                        "old_status": old_status,
                        "new_status": new_status,
                        "reason": reason
                    }
                )

            except Exception as e:
                errors.append({
                    "policy_id": policy_id,
                    "error": str(e)
                })

        try:
            self.db.commit()
            logger.info(f"✅ Bulk status update: {len(updated)} policies updated to {new_status}")
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"Database commit failed: {str(e)}"
            }

        return {
            "success": True,
            "updated_count": len(updated),
            "error_count": len(errors),
            "updated_policies": updated,
            "errors": errors
        }

    def bulk_delete(
        self,
        policy_ids: List[int],
        confirmation: str,
        create_backup: bool,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Bulk delete policies (soft delete)

        Args:
            policy_ids: List of policy IDs to delete
            confirmation: Must be "DELETE" to proceed
            create_backup: Whether to create backup before deletion
            user_email: Email of user performing operation

        Returns:
            Deletion results with backup info
        """
        # Safety check: require explicit confirmation
        if confirmation != "DELETE":
            return {
                "success": False,
                "error": "Confirmation failed. Must provide 'DELETE' to proceed"
            }

        # Create backup if requested
        backup_data = None
        if create_backup:
            try:
                from services.policy_import_export_service import create_import_export_service
                export_service = create_import_export_service(self.db)

                # Export only the policies being deleted
                policies_to_backup = self.db.query(EnterprisePolicy).filter(
                    EnterprisePolicy.id.in_(policy_ids)
                ).all()

                if policies_to_backup:
                    backup_name = f"bulk_delete_backup_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
                    backup_data = {
                        "backup_name": backup_name,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "policies": [
                            {
                                "id": p.id,
                                "policy_name": p.policy_name,
                                "description": p.description,
                                "effect": p.effect,
                                "actions": p.actions,
                                "resources": p.resources,
                                "conditions": p.conditions,
                                "priority": p.priority
                            }
                            for p in policies_to_backup
                        ]
                    }
                    logger.info(f"✅ Created backup: {backup_name}")
            except Exception as e:
                logger.error(f"Backup creation failed: {e}")
                return {
                    "success": False,
                    "error": f"Backup creation failed: {str(e)}"
                }

        # Perform soft delete
        deleted = []
        errors = []

        for policy_id in policy_ids:
            try:
                policy = self.db.query(EnterprisePolicy).filter(
                    EnterprisePolicy.id == policy_id
                ).first()

                if not policy:
                    errors.append({
                        "policy_id": policy_id,
                        "error": "Policy not found"
                    })
                    continue

                # Soft delete: set status to 'deleted'
                policy.status = "deleted"
                policy.updated_at = datetime.now(UTC)

                deleted.append({
                    "policy_id": policy_id,
                    "policy_name": policy.policy_name
                })

                # Create audit log
                self._create_audit_log(
                    user_email=user_email,
                    action="bulk_delete",
                    policy_id=policy_id,
                    details={
                        "policy_name": policy.policy_name,
                        "backup_created": create_backup
                    }
                )

            except Exception as e:
                errors.append({
                    "policy_id": policy_id,
                    "error": str(e)
                })

        try:
            self.db.commit()
            logger.info(f"✅ Bulk delete: {len(deleted)} policies deleted")
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"Database commit failed: {str(e)}"
            }

        return {
            "success": True,
            "deleted_count": len(deleted),
            "error_count": len(errors),
            "deleted_policies": deleted,
            "errors": errors,
            "backup": backup_data
        }

    def bulk_update_priority(
        self,
        updates: List[Dict[str, int]],
        user_email: str
    ) -> Dict[str, Any]:
        """
        Bulk update policy priorities

        Args:
            updates: List of {"policy_id": int, "priority": int}
            user_email: Email of user performing operation

        Returns:
            Update results
        """
        updated = []
        errors = []

        for update in updates:
            policy_id = update.get("policy_id")
            new_priority = update.get("priority")

            if policy_id is None or new_priority is None:
                errors.append({
                    "update": update,
                    "error": "Missing policy_id or priority"
                })
                continue

            try:
                policy = self.db.query(EnterprisePolicy).filter(
                    EnterprisePolicy.id == policy_id
                ).first()

                if not policy:
                    errors.append({
                        "policy_id": policy_id,
                        "error": "Policy not found"
                    })
                    continue

                old_priority = policy.priority
                policy.priority = new_priority
                policy.updated_at = datetime.now(UTC)

                updated.append({
                    "policy_id": policy_id,
                    "policy_name": policy.policy_name,
                    "old_priority": old_priority,
                    "new_priority": new_priority
                })

                # Create audit log
                self._create_audit_log(
                    user_email=user_email,
                    action="bulk_priority_update",
                    policy_id=policy_id,
                    details={
                        "old_priority": old_priority,
                        "new_priority": new_priority
                    }
                )

            except Exception as e:
                errors.append({
                    "policy_id": policy_id,
                    "error": str(e)
                })

        try:
            self.db.commit()
            logger.info(f"✅ Bulk priority update: {len(updated)} policies updated")
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"Database commit failed: {str(e)}"
            }

        return {
            "success": True,
            "updated_count": len(updated),
            "error_count": len(errors),
            "updated_policies": updated,
            "errors": errors
        }

    def _create_audit_log(
        self,
        user_email: str,
        action: str,
        policy_id: int,
        details: Dict[str, Any]
    ):
        """Create audit log entry for bulk operation"""
        try:
            audit_entry = AuditLog(
                user_id=0,  # Bulk operations use system user
                action=action,
                resource_type="policy",
                resource_id=str(policy_id),
                details=json.dumps(details),
                ip_address="127.0.0.1",
                user_agent=f"BulkOperations-{user_email}"
            )
            self.db.add(audit_entry)
        except Exception as e:
            logger.warning(f"Failed to create audit log: {e}")


def create_bulk_operations_service(db: Session) -> PolicyBulkOperationsService:
    """Factory function"""
    return PolicyBulkOperationsService(db)
