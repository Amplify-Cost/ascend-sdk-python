# ========================================
# PHASE 2.2: GDPR/CCPA DATA SUBJECT RIGHTS
# Enterprise Data Privacy Compliance System
# ========================================
# ONBOARD-019: Added organization_id to all models for tenant isolation

# 1. Enhanced Data Rights Models
# File: ow-ai-backend/models_data_rights.py
"""
GDPR/CCPA Data Subject Rights Models
Implements Article 15 (Access), Article 17 (Erasure), Article 20 (Portability)

ONBOARD-019: Enterprise Tenant Isolation
- All models include organization_id (NOT NULL, indexed)
- Foreign key to organizations table
- Supports multi-tenant GDPR/CCPA compliance

Compliance: GDPR, CCPA, SOC 2 CC6.1, HIPAA 164.312(a)(1), PCI-DSS 7.1
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

    ONBOARD-019: Enterprise tenant isolation via organization_id
    """
    __tablename__ = "data_subject_requests"

    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(50), unique=True, nullable=False)  # DSR-2025-001

    # ONBOARD-019: Enterprise tenant isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

    # Request details
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True)  # Internal user ID if known
    subject_name = Column(String(255), nullable=True)  # ONBOARD-019: Subject name for display
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
    request_details = Column(JSON, nullable=False, default=dict)  # Original request details
    identity_verification = Column(JSON, nullable=True)  # Identity verification data
    verification_status = Column(String(50), nullable=True)  # PENDING, VERIFIED, FAILED

    # Processing details
    assigned_to = Column(String(100), nullable=True)  # Data Protection Officer
    processing_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ONBOARD-019: Actor tracking

    # Results and delivery
    result_data = Column(JSON, nullable=True)  # Processed data for delivery
    delivery_method = Column(String(50), nullable=True)  # EMAIL, SECURE_DOWNLOAD, API
    delivery_status = Column(String(50), nullable=True)  # PENDING, DELIVERED, FAILED
    export_format = Column(String(50), nullable=True)  # JSON, CSV, PDF for portability

    # Compliance tracking
    compliance_framework = Column(String(20), nullable=False, default='GDPR')  # GDPR, CCPA, BOTH
    retention_period = Column(Integer, nullable=False, default=2555)  # Days to retain request
    reason = Column(Text, nullable=True)  # ONBOARD-019: Reason for request (erasure)

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

    ONBOARD-019: Enterprise tenant isolation via organization_id
    """
    __tablename__ = "data_lineage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ONBOARD-019: Enterprise tenant isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

    # Data subject identification
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)

    # Data location and type
    data_category = Column(String(100), nullable=False)  # PROFILE, AUDIT_LOG, AGENT_INTERACTION
    data_source = Column(String(100), nullable=False)   # users, agent_actions, analytics
    source = Column(String(255), nullable=True)  # ONBOARD-019: Source system
    table_name = Column(String(100), nullable=True)
    column_name = Column(String(100), nullable=True)
    record_id = Column(String(100), nullable=True)

    # Data classification
    sensitivity_level = Column(String(20), nullable=False, default='MEDIUM')  # HIGH, MEDIUM, LOW
    legal_basis_processing = Column(String(100), nullable=True)  # CONSENT, CONTRACT, LEGITIMATE_INTEREST
    processing_purpose = Column(Text, nullable=True)  # ONBOARD-019: Purpose description
    retention_period = Column(String(100), nullable=True)  # ONBOARD-019: Changed to string for flexibility

    # Tracking metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    recorded_at = Column(DateTime(timezone=True), nullable=True)  # ONBOARD-019: When recorded
    recorded_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ONBOARD-019: Actor tracking
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    scheduled_deletion = Column(DateTime(timezone=True), nullable=True)

    # Cross-references
    related_requests = Column(JSON, nullable=True)  # DSR IDs that affected this data


class ConsentRecord(Base):
    """
    GDPR/CCPA Consent Management
    Tracks consent for all data processing activities

    ONBOARD-019: Enterprise tenant isolation via organization_id
    """
    __tablename__ = "consent_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ONBOARD-019: Enterprise tenant isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

    # Subject identification
    subject_email = Column(String(255), nullable=False, index=True)
    subject_id = Column(String(100), nullable=True, index=True)

    # Consent details
    consent_type = Column(String(100), nullable=False)  # ANALYTICS, MARKETING, ESSENTIAL
    purpose = Column(Text, nullable=False)  # Clear description of processing purpose
    legal_basis = Column(String(50), nullable=False)   # CONSENT, LEGITIMATE_INTEREST, CONTRACT
    consent_given = Column(Boolean, nullable=False, default=False)  # ONBOARD-019: Renamed for clarity

    # Consent status
    granted = Column(Boolean, nullable=False, default=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    consent_method = Column(String(50), nullable=False, default='API')  # WEB_FORM, API, EMAIL
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Tracking
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    recorded_at = Column(DateTime(timezone=True), nullable=True)  # ONBOARD-019: When recorded
    recorded_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ONBOARD-019: Actor tracking
    last_updated = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class DataErasureLog(Base):
    """
    Audit Log for Data Erasure Activities
    Maintains compliance record of all erasure actions

    ONBOARD-019: Enterprise tenant isolation via organization_id
    """
    __tablename__ = "data_erasure_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ONBOARD-019: Enterprise tenant isolation
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False, index=True)

    # Erasure request reference
    request_id = Column(String(50), nullable=False, index=True)
    subject_email = Column(String(255), nullable=False, index=True)

    # Erasure details
    erasure_type = Column(String(50), nullable=False, default='FULL_ERASURE')  # FULL_ERASURE, ANONYMIZATION, PSEUDONYMIZATION
    data_category = Column(String(100), nullable=True)
    source_table = Column(String(100), nullable=True)
    tables_affected = Column(JSON, nullable=True)  # ONBOARD-019: List of affected tables
    records_affected = Column(Integer, nullable=False, default=0)
    records_deleted = Column(Integer, nullable=False, default=0)  # ONBOARD-019: Alias for clarity

    # Execution details
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # ONBOARD-019: FK to users
    executed_by_email = Column(String(255), nullable=True)  # ONBOARD-019: Email for audit
    executed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    execution_method = Column(String(50), nullable=False, default='AUTOMATED')  # AUTOMATED, MANUAL

    # Compliance
    legal_basis = Column(String(100), nullable=True)
    retention_exception = Column(Boolean, nullable=False, default=False)  # Legal hold override
    exception_reason = Column(Text, nullable=True)

    # Verification
    verification_hash = Column(String(64), nullable=True)  # Hash of erasure proof
    backup_status = Column(String(50), nullable=True)  # PURGED, RETAINED_LEGAL, ANONYMIZED
