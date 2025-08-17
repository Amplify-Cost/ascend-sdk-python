# ========================================
# PHASE 2.2: GDPR/CCPA DATA SUBJECT RIGHTS
# Enterprise Data Privacy Compliance System
# ========================================

# 1. Enhanced Data Rights Models
# File: ow-ai-backend/models_data_rights.py
"""
GDPR/CCPA Data Subject Rights Models
Implements Article 15 (Access), Article 17 (Erasure), Article 20 (Portability)
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC, timedelta
import uuid
from database import Base

class DataSubjectRequest(Base):
    """
    GDPR/CCPA Data Subject Rights Requests
    Tracks all data subject requests with audit trails
    """
    __tablename__ = "data_subject_requests"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(50), unique=True, nullable=False)  # DSR-2025-001
    
    # Request details
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True)  # Internal user ID if known
    request_type = Column(String(50), nullable=False)  # ACCESS, ERASURE, PORTABILITY, OBJECTION
    legal_basis = Column(String(50), nullable=False)  # GDPR_ART_15, CCPA_1798_110, etc.
    
    # Status tracking
    status = Column(String(50), nullable=False, default='RECEIVED')  # RECEIVED, PROCESSING, COMPLETED, REJECTED
    priority = Column(String(20), nullable=False, default='NORMAL')  # HIGH, NORMAL, LOW
    
    # Timestamps (GDPR requires 30-day response)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    due_date = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Request content
    request_details = Column(JSON, nullable=False)  # Original request details
    identity_verification = Column(JSON, nullable=True)  # Identity verification data
    
    # Processing details
    assigned_to = Column(String(100), nullable=True)  # Data Protection Officer
    processing_notes = Column(Text, nullable=True)
    
    # Results and delivery
    result_data = Column(JSON, nullable=True)  # Processed data for delivery
    delivery_method = Column(String(50), nullable=True)  # EMAIL, SECURE_DOWNLOAD, API
    delivery_status = Column(String(50), nullable=True)  # PENDING, DELIVERED, FAILED
    
    # Compliance tracking
    compliance_framework = Column(String(20), nullable=False)  # GDPR, CCPA, BOTH
    retention_period = Column(Integer, nullable=False, default=2555)  # Days to retain request
    
    def calculate_due_date(self):
        """Calculate due date based on legal framework"""
        if self.legal_basis.startswith('GDPR'):
            return self.created_at + timedelta(days=30)  # GDPR Article 12(3)
        elif self.legal_basis.startswith('CCPA'):
            return self.created_at + timedelta(days=45)  # CCPA §1798.130(a)(2)
        else:
            return self.created_at + timedelta(days=30)  # Default

class DataLineage(Base):
    """
    Data Lineage Tracking for GDPR/CCPA Compliance
    Maps data flow across all platform components
    """
    __tablename__ = "data_lineage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Data subject identification
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)
    
    # Data location and type
    data_category = Column(String(100), nullable=False)  # PROFILE, AUDIT_LOG, AGENT_INTERACTION
    data_source = Column(String(100), nullable=False)   # users, agent_actions, analytics
    table_name = Column(String(100), nullable=False)
    column_name = Column(String(100), nullable=False)
    record_id = Column(String(100), nullable=False)
    
    # Data classification
    sensitivity_level = Column(String(20), nullable=False)  # HIGH, MEDIUM, LOW
    legal_basis_processing = Column(String(100), nullable=False)  # CONSENT, CONTRACT, LEGITIMATE_INTEREST
    retention_period = Column(Integer, nullable=False)  # Days
    
    # Tracking metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    scheduled_deletion = Column(DateTime(timezone=True), nullable=True)
    
    # Cross-references
    related_requests = Column(JSON, nullable=True)  # DSR IDs that affected this data

class ConsentRecord(Base):
    """
    GDPR/CCPA Consent Management
    Tracks consent for all data processing activities
    """
    __tablename__ = "consent_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Subject identification
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)
    
    # Consent details
    consent_type = Column(String(100), nullable=False)  # ANALYTICS, MARKETING, ESSENTIAL
    purpose = Column(Text, nullable=False)  # Clear description of processing purpose
    legal_basis = Column(String(50), nullable=False)   # CONSENT, LEGITIMATE_INTEREST, CONTRACT
    
    # Consent status
    granted = Column(Boolean, nullable=False, default=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    consent_method = Column(String(50), nullable=False)  # WEB_FORM, API, EMAIL
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    last_updated = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class DataErasureLog(Base):
    """
    Audit Log for Data Erasure Activities
    Maintains compliance record of all erasure actions
    """
    __tablename__ = "data_erasure_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Erasure request reference
    request_id = Column(String(50), nullable=False, index=True)
    subject_email = Column(String(255), nullable=False, index=True)
    
    # Erasure details
    erasure_type = Column(String(50), nullable=False)  # FULL_ERASURE, ANONYMIZATION, PSEUDONYMIZATION
    data_category = Column(String(100), nullable=False)
    source_table = Column(String(100), nullable=False)
    records_affected = Column(Integer, nullable=False, default=0)
    
    # Execution details
    executed_by = Column(String(100), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    execution_method = Column(String(50), nullable=False)  # AUTOMATED, MANUAL
    
    # Compliance
    legal_basis = Column(String(100), nullable=False)
    retention_exception = Column(Boolean, nullable=False, default=False)  # Legal hold override
    exception_reason = Column(Text, nullable=True)
    
    # Verification
    verification_hash = Column(String(64), nullable=False)  # Hash of erasure proof
    backup_status = Column(String(50), nullable=False)  # PURGED, RETAINED_LEGAL, ANONYMIZED

