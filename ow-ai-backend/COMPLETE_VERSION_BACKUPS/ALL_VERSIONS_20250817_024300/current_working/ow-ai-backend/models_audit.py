"""
Enterprise Immutable Audit Models
Implements WORM (Write-Once-Read-Many) design with hash-chaining
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import hashlib
import json
import uuid
from database import Base

class ImmutableAuditLog(Base):
    """
    WORM (Write-Once-Read-Many) audit log with hash-chaining
    Each entry is cryptographically linked to the previous entry
    """
    __tablename__ = "immutable_audit_logs"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_number = Column(Integer, nullable=False, unique=True, autoincrement=True)
    
    # Timestamp and source
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    source_system = Column(String(100), nullable=False, default="ow-ai")
    
    # Event data
    event_type = Column(String(50), nullable=False)  # USER_ACTION, SYSTEM_EVENT, POLICY_VIOLATION
    actor_id = Column(String(100), nullable=False)    # User ID or system identifier
    resource_type = Column(String(50), nullable=False) # AGENT, TOOL, DATA, POLICY
    resource_id = Column(String(100), nullable=False)  # Specific resource identifier
    action = Column(String(100), nullable=False)       # CREATE, READ, UPDATE, DELETE, EXECUTE
    
    # Detailed event data
    event_data = Column(JSON, nullable=False)         # Full event context
    risk_level = Column(String(20), nullable=False)   # LOW, MEDIUM, HIGH, CRITICAL
    compliance_tags = Column(JSON, nullable=True)      # SOX, HIPAA, PCI, GDPR, etc.
    
    # Immutability and integrity
    content_hash = Column(String(64), nullable=False)  # SHA-256 of event content
    previous_hash = Column(String(64), nullable=True)  # Hash of previous log entry
    chain_hash = Column(String(64), nullable=False)    # Combined hash for chain validation
    
    # Evidence and retention
    evidence_pack_id = Column(UUID(as_uuid=True), nullable=True)  # Link to evidence package
    retention_until = Column(DateTime(timezone=True), nullable=True)  # Compliance retention
    legal_hold = Column(Boolean, default=False)        # Prevent deletion for legal reasons
    
    # Metadata
    ip_address = Column(String(45), nullable=True)     # IPv4/IPv6 address
    user_agent = Column(Text, nullable=True)           # Browser/client info
    session_id = Column(String(100), nullable=True)    # Session identifier
    
    # Indexes for performance and compliance queries
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_actor', 'actor_id'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_compliance', 'compliance_tags'),
        Index('idx_audit_retention', 'retention_until'),
        Index('idx_audit_sequence', 'sequence_number'),
    )
    
    def calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of audit log content"""
        from datetime import datetime, UTC
        # Handle case where timestamp is not set yet
        timestamp = self.timestamp if self.timestamp else datetime.now(UTC)
        content = {
            'timestamp': timestamp.isoformat(),
            'event_type': self.event_type,
            'actor_id': self.actor_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'event_data': self.event_data,
            'risk_level': self.risk_level
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def calculate_chain_hash(self, previous_hash: str = None) -> str:
        """Calculate chain hash linking this entry to previous"""
        chain_data = f"{self.content_hash}:{previous_hash or ''}"
        return hashlib.sha256(chain_data.encode()).hexdigest()

class EvidencePack(Base):
    """
    Signed evidence packages for legal and compliance use
    Contains cryptographically verified audit trails
    """
    __tablename__ = "evidence_packs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by = Column(String(100), nullable=False)
    
    # Evidence metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    case_number = Column(String(100), nullable=True)    # Legal case reference
    investigation_id = Column(String(100), nullable=True) # Internal investigation
    
    # Time range and scope
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    actor_ids = Column(JSON, nullable=True)             # Users included
    resource_types = Column(JSON, nullable=True)        # Resources included
    
    # Cryptographic integrity
    manifest_hash = Column(String(64), nullable=False)  # Hash of included logs
    signature = Column(LargeBinary, nullable=True)      # Digital signature
    certificate_info = Column(JSON, nullable=True)      # Signing certificate details
    
    # Status and access
    status = Column(String(20), nullable=False, default='ACTIVE')  # ACTIVE, SEALED, ARCHIVED
    access_count = Column(Integer, default=0)           # Number of times accessed
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Compliance and legal
    legal_hold = Column(Boolean, default=False)
    retention_policy = Column(String(50), nullable=True) # SOX_7YEAR, HIPAA_6YEAR, etc.
    compliance_frameworks = Column(JSON, nullable=True)  # Applicable frameworks

class AuditIntegrityCheck(Base):
    """
    Regular integrity verification of audit chain
    Validates hash chains and detects tampering
    """
    __tablename__ = "audit_integrity_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    
    # Check scope
    start_sequence = Column(Integer, nullable=False)
    end_sequence = Column(Integer, nullable=False)
    total_records = Column(Integer, nullable=False)
    
    # Results
    status = Column(String(20), nullable=False)          # VALID, BROKEN, TAMPERED
    broken_chains = Column(JSON, nullable=True)          # List of broken chain points
    invalid_hashes = Column(JSON, nullable=True)         # Records with invalid hashes
    
    # Performance metrics
    check_duration_ms = Column(Integer, nullable=False)
    records_per_second = Column(Integer, nullable=False)
    
    # Additional details
    details = Column(JSON, nullable=True)
    remediation_actions = Column(JSON, nullable=True)