"""
Enterprise Immutable Audit Service
Provides WORM audit logging with hash-chaining and integrity verification
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import json
from models_audit import ImmutableAuditLog, EvidencePack, AuditIntegrityCheck

logger = logging.getLogger(__name__)

class ImmutableAuditService:
    """Enterprise-grade immutable audit logging service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_event(
        self,
        event_type: str,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        event_data: Dict[str, Any],
        outcome: str = "SUCCESS",
        risk_level: str = "MEDIUM",
        compliance_tags: List[str] = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ) -> ImmutableAuditLog:
        """Create immutable audit log entry with hash-chaining"""
        try:
            # Get the last audit log for hash chaining
            last_log = self.db.query(ImmutableAuditLog).order_by(
                desc(ImmutableAuditLog.sequence_number)
            ).first()
            
            # Create new audit log
            audit_log = ImmutableAuditLog(
                event_type=event_type,
                actor_id=actor_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                outcome=outcome,
                event_data=event_data,
                risk_level=risk_level,
                compliance_tags=compliance_tags or [],
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            # Calculate content hash
            audit_log.content_hash = audit_log.calculate_content_hash()
            
            # Set previous hash and calculate chain hash
            previous_hash = last_log.chain_hash if last_log else None
            audit_log.previous_hash = previous_hash
            audit_log.chain_hash = audit_log.calculate_chain_hash(previous_hash)
            
            # Set retention based on compliance tags
            audit_log.retention_until = self._calculate_retention_date(compliance_tags)
            
            # Save to database
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.info(f"Immutable audit log created: {audit_log.id}")
            return audit_log
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create audit log: {str(e)}")
            raise
    
    def verify_chain_integrity(
        self, 
        start_sequence: int = None, 
        end_sequence: int = None
    ) -> AuditIntegrityCheck:
        """Verify the integrity of the audit log hash chain"""
        start_time = datetime.now(UTC)
        
        # Get sequence range if not specified
        if start_sequence is None:
            start_sequence = self.db.query(func.min(ImmutableAuditLog.sequence_number)).scalar() or 1
        if end_sequence is None:
            end_sequence = self.db.query(func.max(ImmutableAuditLog.sequence_number)).scalar() or 1
        
        # Fetch audit logs in sequence order
        logs = self.db.query(ImmutableAuditLog).filter(
            and_(
                ImmutableAuditLog.sequence_number >= start_sequence,
                ImmutableAuditLog.sequence_number <= end_sequence
            )
        ).order_by(ImmutableAuditLog.sequence_number).all()
        
        broken_chains = []
        invalid_hashes = []
        previous_hash = None
        
        for log in logs:
            # Verify content hash
            expected_content_hash = log.calculate_content_hash()
            if log.content_hash != expected_content_hash:
                invalid_hashes.append({
                    'sequence': log.sequence_number,
                    'id': str(log.id),
                    'expected': expected_content_hash,
                    'actual': log.content_hash
                })
            
            # Verify chain hash
            expected_chain_hash = log.calculate_chain_hash(previous_hash)
            if log.chain_hash != expected_chain_hash:
                broken_chains.append({
                    'sequence': log.sequence_number,
                    'id': str(log.id),
                    'expected': expected_chain_hash,
                    'actual': log.chain_hash
                })
            
            previous_hash = log.chain_hash
        
        # Determine overall status
        if broken_chains or invalid_hashes:
            status = "TAMPERED" if invalid_hashes else "BROKEN"
        else:
            status = "VALID"
        
        # Calculate performance metrics
        end_time = datetime.now(UTC)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        records_per_second = int(len(logs) / max((end_time - start_time).total_seconds(), 0.001))
        
        # Create integrity check record
        integrity_check = AuditIntegrityCheck(
            start_sequence=start_sequence,
            end_sequence=end_sequence,
            total_records=len(logs),
            status=status,
            broken_chains=broken_chains if broken_chains else None,
            invalid_hashes=invalid_hashes if invalid_hashes else None,
            check_duration_ms=duration_ms,
            records_per_second=records_per_second,
            details={
                'check_range': f"{start_sequence}-{end_sequence}",
                'chain_breaks': len(broken_chains),
                'hash_failures': len(invalid_hashes)
            }
        )
        
        self.db.add(integrity_check)
        self.db.commit()
        
        logger.info(f"Chain integrity check completed: {status} ({len(logs)} records)")
        return integrity_check
    
    def _calculate_retention_date(self, compliance_tags: List[str]) -> datetime:
        """Calculate retention date based on compliance requirements"""
        if not compliance_tags:
            return datetime.now(UTC) + timedelta(days=2555)  # 7 years default
        
        # Compliance retention periods
        retention_periods = {
            'SOX': timedelta(days=2555),      # 7 years
            'HIPAA': timedelta(days=2190),    # 6 years
            'PCI': timedelta(days=365),       # 1 year
            'GDPR': timedelta(days=2190),     # 6 years (can be longer)
            'CCPA': timedelta(days=1095),     # 3 years
            'FERPA': timedelta(days=1825),    # 5 years
        }
        
        # Use the longest retention period from applicable frameworks
        max_retention = timedelta(days=2555)  # Default 7 years
        for tag in compliance_tags:
            if tag in retention_periods:
                max_retention = max(max_retention, retention_periods[tag])
        
        return datetime.now(UTC) + max_retention
