"""
Enterprise Retention Policy Service
Implements automated retention enforcement for immutable audit logs

Compliance Frameworks:
- SOX: 7 years for financial records
- HIPAA: 6 years for health records
- PCI-DSS: 1 year for cardholder data
- GDPR: Right to erasure with legal hold support
- CCPA: 12 months minimum
- FERPA: 5 years for education records

Features:
- Configurable retention periods per compliance framework
- Legal hold support (prevents deletion)
- Automated cleanup of expired records
- Audit trail of retention actions
- Hash chain integrity preservation
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, UTC
from typing import List, Dict, Optional, Tuple
import logging
from models_audit import ImmutableAuditLog
from services.immutable_audit_service import ImmutableAuditService

logger = logging.getLogger(__name__)

class RetentionPolicy:
    """Retention policy configuration"""

    # Standard compliance retention periods (in days)
    COMPLIANCE_RETENTION = {
        'SOX': 2555,      # 7 years
        'HIPAA': 2190,    # 6 years
        'PCI-DSS': 365,   # 1 year
        'GDPR': 365,      # 1 year (minimum, subject to erasure requests)
        'CCPA': 365,      # 1 year
        'FERPA': 1825,    # 5 years
        'DEFAULT': 2555,  # 7 years (SOX standard)
    }

    # Risk-based retention overrides
    RISK_RETENTION_OVERRIDE = {
        'CRITICAL': 2555,  # 7 years for critical events
        'HIGH': 1825,      # 5 years for high-risk events
        'MEDIUM': 1095,    # 3 years for medium-risk events
        'LOW': 730,        # 2 years for low-risk events
    }

    @classmethod
    def calculate_retention_date(
        cls,
        compliance_tags: List[str],
        risk_level: str,
        created_at: datetime
    ) -> datetime:
        """
        Calculate retention date based on compliance requirements and risk level

        Logic:
        1. Find maximum retention period from compliance tags
        2. Apply risk-based override if longer
        3. Return the longest retention period
        """
        max_retention_days = cls.COMPLIANCE_RETENTION['DEFAULT']

        # Check compliance tags for maximum retention requirement
        if compliance_tags:
            for tag in compliance_tags:
                tag_upper = tag.upper()
                if tag_upper in cls.COMPLIANCE_RETENTION:
                    tag_retention = cls.COMPLIANCE_RETENTION[tag_upper]
                    max_retention_days = max(max_retention_days, tag_retention)

        # Check risk-based override
        risk_upper = risk_level.upper()
        if risk_upper in cls.RISK_RETENTION_OVERRIDE:
            risk_retention = cls.RISK_RETENTION_OVERRIDE[risk_upper]
            max_retention_days = max(max_retention_days, risk_retention)

        # Calculate retention date
        retention_date = created_at + timedelta(days=max_retention_days)
        return retention_date

class RetentionPolicyService:
    """Service for managing audit log retention and cleanup"""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ImmutableAuditService(db)

    def apply_retention_policy(
        self,
        log: ImmutableAuditLog
    ) -> ImmutableAuditLog:
        """
        Apply retention policy to a new audit log entry

        Args:
            log: ImmutableAuditLog instance (before commit)

        Returns:
            Updated log with retention_until set
        """
        # Parse compliance tags
        compliance_tags = log.compliance_tags if isinstance(log.compliance_tags, list) else []

        # Calculate retention date
        retention_date = RetentionPolicy.calculate_retention_date(
            compliance_tags=compliance_tags,
            risk_level=log.risk_level,
            created_at=log.timestamp
        )

        log.retention_until = retention_date

        logger.info(
            f"Applied retention policy to log {log.id}: "
            f"retention_until={retention_date.isoformat()}, "
            f"compliance_tags={compliance_tags}, risk_level={log.risk_level}"
        )

        return log

    def backfill_retention_dates(
        self,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Backfill retention dates for existing logs without them

        Args:
            batch_size: Number of logs to process per batch

        Returns:
            Statistics dict with counts
        """
        logger.info("Starting retention date backfill...")

        # Find logs without retention dates
        logs_without_retention = self.db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.retention_until == None
        ).limit(batch_size).all()

        updated_count = 0
        for log in logs_without_retention:
            # Parse compliance tags
            compliance_tags = log.compliance_tags if isinstance(log.compliance_tags, list) else []

            # Calculate retention date
            retention_date = RetentionPolicy.calculate_retention_date(
                compliance_tags=compliance_tags,
                risk_level=log.risk_level,
                created_at=log.timestamp
            )

            log.retention_until = retention_date
            updated_count += 1

        # Commit changes
        self.db.commit()

        logger.info(f"Backfilled retention dates for {updated_count} logs")

        return {
            'updated': updated_count,
            'batch_size': batch_size,
            'has_more': len(logs_without_retention) == batch_size
        }

    def find_expired_logs(
        self,
        exclude_legal_hold: bool = True
    ) -> List[ImmutableAuditLog]:
        """
        Find audit logs that have passed their retention period

        Args:
            exclude_legal_hold: If True, exclude logs with legal_hold=True

        Returns:
            List of expired logs eligible for deletion
        """
        now = datetime.now(UTC)

        query = self.db.query(ImmutableAuditLog).filter(
            and_(
                ImmutableAuditLog.retention_until != None,
                ImmutableAuditLog.retention_until < now
            )
        )

        if exclude_legal_hold:
            query = query.filter(
                or_(
                    ImmutableAuditLog.legal_hold == False,
                    ImmutableAuditLog.legal_hold == None
                )
            )

        expired_logs = query.all()

        logger.info(
            f"Found {len(expired_logs)} expired logs "
            f"(legal_hold_excluded={exclude_legal_hold})"
        )

        return expired_logs

    def cleanup_expired_logs(
        self,
        dry_run: bool = True,
        max_delete: int = 1000
    ) -> Dict[str, any]:
        """
        Delete expired audit logs that are past their retention period

        IMPORTANT: This breaks the hash chain for deleted logs
        Use with caution and only after exporting to evidence packs

        Args:
            dry_run: If True, only report what would be deleted
            max_delete: Maximum number of logs to delete in one run

        Returns:
            Statistics dict with counts and details
        """
        expired_logs = self.find_expired_logs(exclude_legal_hold=True)

        # Limit deletion
        logs_to_delete = expired_logs[:max_delete]

        if dry_run:
            logger.info(
                f"DRY RUN: Would delete {len(logs_to_delete)} expired logs "
                f"(total expired: {len(expired_logs)})"
            )
            return {
                'dry_run': True,
                'would_delete': len(logs_to_delete),
                'total_expired': len(expired_logs),
                'oldest_retention_date': min(
                    [log.retention_until for log in logs_to_delete]
                ) if logs_to_delete else None,
                'newest_retention_date': max(
                    [log.retention_until for log in logs_to_delete]
                ) if logs_to_delete else None,
            }

        # ACTUAL DELETION (breaks hash chain)
        deleted_ids = []
        for log in logs_to_delete:
            deleted_ids.append(str(log.id))
            self.db.delete(log)

        self.db.commit()

        logger.warning(
            f"DELETED {len(deleted_ids)} expired audit logs. "
            f"Hash chain may be broken."
        )

        return {
            'dry_run': False,
            'deleted': len(deleted_ids),
            'deleted_ids': deleted_ids,
            'remaining_expired': len(expired_logs) - len(logs_to_delete),
        }

    def apply_legal_hold(
        self,
        log_ids: List[str],
        reason: str,
        applied_by: str
    ) -> Dict[str, any]:
        """
        Apply legal hold to specific audit logs to prevent deletion

        Args:
            log_ids: List of audit log IDs to apply hold to
            reason: Legal reason for the hold
            applied_by: User who applied the hold

        Returns:
            Statistics dict with counts
        """
        logs = self.db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.id.in_(log_ids)
        ).all()

        updated_count = 0
        for log in logs:
            log.legal_hold = True
            updated_count += 1

            # Log the legal hold action
            self.audit_service.log_event(
                event_type="LEGAL_HOLD_APPLIED",
                actor_id=applied_by,
                resource_type="AUDIT_LOG",
                resource_id=str(log.id),
                action="LEGAL_HOLD",
                event_data={
                    'reason': reason,
                    'applied_at': datetime.now(UTC).isoformat(),
                    'original_retention': log.retention_until.isoformat() if log.retention_until else None
                },
                risk_level="HIGH",
                compliance_tags=['LEGAL']
            )

        self.db.commit()

        logger.info(
            f"Applied legal hold to {updated_count} logs. "
            f"Reason: {reason}, Applied by: {applied_by}"
        )

        return {
            'applied': updated_count,
            'requested': len(log_ids),
            'reason': reason,
            'applied_by': applied_by
        }

    def release_legal_hold(
        self,
        log_ids: List[str],
        released_by: str
    ) -> Dict[str, any]:
        """
        Release legal hold from audit logs, making them eligible for deletion

        Args:
            log_ids: List of audit log IDs to release hold from
            released_by: User who released the hold

        Returns:
            Statistics dict with counts
        """
        logs = self.db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.id.in_(log_ids)
        ).all()

        released_count = 0
        for log in logs:
            if log.legal_hold:
                log.legal_hold = False
                released_count += 1

                # Log the hold release action
                self.audit_service.log_event(
                    event_type="LEGAL_HOLD_RELEASED",
                    actor_id=released_by,
                    resource_type="AUDIT_LOG",
                    resource_id=str(log.id),
                    action="LEGAL_HOLD_RELEASE",
                    event_data={
                        'released_at': datetime.now(UTC).isoformat(),
                        'retention_until': log.retention_until.isoformat() if log.retention_until else None
                    },
                    risk_level="MEDIUM",
                    compliance_tags=['LEGAL']
                )

        self.db.commit()

        logger.info(
            f"Released legal hold from {released_count} logs. "
            f"Released by: {released_by}"
        )

        return {
            'released': released_count,
            'requested': len(log_ids),
            'released_by': released_by
        }

    def get_retention_statistics(self) -> Dict[str, any]:
        """
        Get statistics about retention status of audit logs

        Returns:
            Dict with various retention statistics
        """
        now = datetime.now(UTC)

        # Total logs
        total_logs = self.db.query(ImmutableAuditLog).count()

        # Logs with retention dates
        logs_with_retention = self.db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.retention_until != None
        ).count()

        # Expired logs
        expired_logs = self.db.query(ImmutableAuditLog).filter(
            and_(
                ImmutableAuditLog.retention_until != None,
                ImmutableAuditLog.retention_until < now
            )
        ).count()

        # Logs on legal hold
        legal_hold_logs = self.db.query(ImmutableAuditLog).filter(
            ImmutableAuditLog.legal_hold == True
        ).count()

        # Expired logs on legal hold (can't be deleted)
        expired_legal_hold = self.db.query(ImmutableAuditLog).filter(
            and_(
                ImmutableAuditLog.retention_until != None,
                ImmutableAuditLog.retention_until < now,
                ImmutableAuditLog.legal_hold == True
            )
        ).count()

        # Eligible for deletion (expired, not on legal hold)
        eligible_for_deletion = expired_logs - expired_legal_hold

        return {
            'total_logs': total_logs,
            'logs_with_retention': logs_with_retention,
            'logs_without_retention': total_logs - logs_with_retention,
            'expired_logs': expired_logs,
            'legal_hold_logs': legal_hold_logs,
            'expired_legal_hold': expired_legal_hold,
            'eligible_for_deletion': eligible_for_deletion,
            'retention_compliance_rate': (logs_with_retention / total_logs * 100) if total_logs > 0 else 0,
            'timestamp': datetime.now(UTC).isoformat()
        }
