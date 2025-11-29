"""
OW-kai Enterprise Integration Phase 4: Compliance Export Models

Enterprise-grade compliance export system supporting:
- SOX (Sarbanes-Oxley) audit reports
- PCI-DSS transaction logs
- HIPAA access logs
- GDPR data subject requests
- SOC 2 Type II evidence collection
- NIST Cybersecurity Framework alignment
- ISO 27001 control mapping

Security Features:
- Signed exports with SHA-256 hashes
- Export audit trails
- Data masking for PII
- Retention policy enforcement
- Access control per compliance framework
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base


# ============================================
# Compliance Framework Enums
# ============================================

class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    SOX = "sox"                    # Sarbanes-Oxley
    PCI_DSS = "pci_dss"           # Payment Card Industry
    HIPAA = "hipaa"               # Health Insurance Portability
    GDPR = "gdpr"                 # General Data Protection Regulation
    SOC2 = "soc2"                 # Service Organization Control 2
    NIST_CSF = "nist_csf"         # NIST Cybersecurity Framework
    ISO_27001 = "iso_27001"       # Information Security Management
    CCPA = "ccpa"                 # California Consumer Privacy Act
    FEDRAMP = "fedramp"           # Federal Risk Authorization
    CUSTOM = "custom"             # Custom compliance framework


class ExportFormat(str, Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XML = "xml"
    XLSX = "xlsx"


class ExportStatus(str, Enum):
    """Export job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DataClassification(str, Enum):
    """Data sensitivity classification"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ReportType(str, Enum):
    """Types of compliance reports"""
    AUDIT_TRAIL = "audit_trail"
    ACCESS_LOG = "access_log"
    POLICY_VIOLATIONS = "policy_violations"
    RISK_ASSESSMENT = "risk_assessment"
    INCIDENT_REPORT = "incident_report"
    USER_ACTIVITY = "user_activity"
    DATA_ACCESS = "data_access"
    SYSTEM_CHANGES = "system_changes"
    APPROVAL_HISTORY = "approval_history"
    AGENT_ACTIONS = "agent_actions"
    SECURITY_EVENTS = "security_events"
    COMPLIANCE_SUMMARY = "compliance_summary"


# ============================================
# SQLAlchemy Models
# ============================================

class ComplianceExportJob(Base):
    """Tracks compliance export requests and their status"""
    __tablename__ = "compliance_export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Export Configuration
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), default=ExportFormat.JSON)

    # Date Range
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Status
    status = Column(SQLEnum(ExportStatus), default=ExportStatus.PENDING)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Output
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    record_count = Column(Integer, nullable=True)

    # Security
    file_hash = Column(String(64), nullable=True)  # SHA-256
    data_classification = Column(SQLEnum(DataClassification), default=DataClassification.CONFIDENTIAL)
    include_pii = Column(Boolean, default=False)

    # Metadata
    filters = Column(JSON, nullable=True)  # Additional query filters
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="compliance_exports")
    download_logs = relationship("ComplianceExportDownload", back_populates="export_job")


class ComplianceExportDownload(Base):
    """Audit trail for export downloads"""
    __tablename__ = "compliance_export_downloads"

    id = Column(Integer, primary_key=True, index=True)
    export_job_id = Column(Integer, ForeignKey("compliance_export_jobs.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Download Info
    downloaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    downloaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Verification
    verified_hash = Column(Boolean, default=False)

    # Relationships
    export_job = relationship("ComplianceExportJob", back_populates="download_logs")


class ComplianceSchedule(Base):
    """Scheduled compliance reports"""
    __tablename__ = "compliance_schedules"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # Schedule Config
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    framework = Column(SQLEnum(ComplianceFramework), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), default=ExportFormat.PDF)

    # Schedule
    cron_expression = Column(String(100), nullable=False)  # e.g., "0 0 1 * *" for monthly
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)

    # Recipients
    email_recipients = Column(JSON, nullable=True)  # List of email addresses
    webhook_url = Column(String(500), nullable=True)

    # Retention
    retention_days = Column(Integer, default=90)

    # Metadata
    filters = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)


# ============================================
# Pydantic Schemas - Request Models
# ============================================

class ComplianceExportRequest(BaseModel):
    """Request to create a compliance export"""
    framework: ComplianceFramework
    report_type: ReportType
    export_format: ExportFormat = ExportFormat.JSON
    start_date: datetime
    end_date: datetime
    include_pii: bool = False
    data_classification: DataClassification = DataClassification.CONFIDENTIAL
    filters: Optional[Dict[str, Any]] = None

    @field_validator('end_date')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def not_future(cls, v):
        if v > datetime.now(timezone.utc):
            raise ValueError('Date cannot be in the future')
        return v


class ComplianceScheduleCreate(BaseModel):
    """Create a scheduled compliance report"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    framework: ComplianceFramework
    report_type: ReportType
    export_format: ExportFormat = ExportFormat.PDF
    cron_expression: str = Field(..., pattern=r'^[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+\s+[\d\*\/\-\,]+$')
    timezone: str = "UTC"
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    retention_days: int = Field(default=90, ge=7, le=365)
    filters: Optional[Dict[str, Any]] = None


class ComplianceScheduleUpdate(BaseModel):
    """Update a scheduled compliance report"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    email_recipients: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    retention_days: Optional[int] = Field(None, ge=7, le=365)
    filters: Optional[Dict[str, Any]] = None


# ============================================
# Pydantic Schemas - Response Models
# ============================================

class ComplianceExportResponse(BaseModel):
    """Response for export job"""
    id: int
    framework: ComplianceFramework
    report_type: ReportType
    export_format: ExportFormat
    start_date: datetime
    end_date: datetime
    status: ExportStatus
    progress_percent: int
    error_message: Optional[str]
    file_size_bytes: Optional[int]
    record_count: Optional[int]
    data_classification: DataClassification
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class ComplianceScheduleResponse(BaseModel):
    """Response for scheduled report"""
    id: int
    name: str
    description: Optional[str]
    framework: ComplianceFramework
    report_type: ReportType
    export_format: ExportFormat
    cron_expression: str
    timezone: str
    is_active: bool
    email_recipients: Optional[List[str]]
    webhook_url: Optional[str]
    retention_days: int
    created_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    class Config:
        from_attributes = True


class ComplianceDownloadResponse(BaseModel):
    """Response for download audit log"""
    id: int
    export_job_id: int
    downloaded_by: int
    downloaded_at: datetime
    ip_address: Optional[str]
    verified_hash: bool

    class Config:
        from_attributes = True


# ============================================
# Framework-Specific Report Schemas
# ============================================

class SOXAuditRecord(BaseModel):
    """SOX audit trail record"""
    timestamp: datetime
    event_type: str
    user_id: int
    user_email: str
    action: str
    resource_type: str
    resource_id: str
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    approval_chain: Optional[List[Dict[str, Any]]]
    control_id: Optional[str]
    risk_level: Optional[str]


class PCIDSSRecord(BaseModel):
    """PCI-DSS transaction log record"""
    timestamp: datetime
    transaction_id: str
    user_id: int
    action_type: str
    data_accessed: List[str]
    masked_card_data: Optional[str]
    system_component: str
    access_method: str
    ip_address: Optional[str]
    success: bool
    pci_requirement: str  # e.g., "Req 10.2.1"


class HIPAAAccessRecord(BaseModel):
    """HIPAA access log record"""
    timestamp: datetime
    user_id: int
    user_role: str
    patient_id_hash: Optional[str]  # Hashed PHI reference
    access_type: str  # read, write, delete
    data_category: str  # e.g., "medical_record", "billing"
    purpose: str
    ip_address: Optional[str]
    minimum_necessary: bool  # Did access follow minimum necessary standard
    audit_control: str


class GDPRRecord(BaseModel):
    """GDPR data subject access record"""
    timestamp: datetime
    request_type: str  # access, rectification, erasure, portability
    data_subject_id: str
    data_categories: List[str]
    processing_purpose: str
    legal_basis: str
    third_party_recipients: Optional[List[str]]
    retention_period: Optional[str]
    automated_decision: bool
    controller_response_date: Optional[datetime]


class SOC2ControlEvidence(BaseModel):
    """SOC 2 control evidence record"""
    timestamp: datetime
    trust_principle: str  # Security, Availability, Processing Integrity, Confidentiality, Privacy
    control_id: str
    control_description: str
    evidence_type: str
    evidence_details: Dict[str, Any]
    test_result: str  # pass, fail, exception
    tested_by: Optional[str]
    remediation_required: bool


# ============================================
# Framework Mapping Configuration
# ============================================

FRAMEWORK_REPORT_MAPPINGS = {
    ComplianceFramework.SOX: {
        "supported_reports": [
            ReportType.AUDIT_TRAIL,
            ReportType.APPROVAL_HISTORY,
            ReportType.SYSTEM_CHANGES,
            ReportType.USER_ACTIVITY,
        ],
        "default_retention_days": 2555,  # 7 years
        "required_fields": ["user_id", "action", "timestamp", "approval_chain"],
        "data_classification": DataClassification.CONFIDENTIAL,
    },
    ComplianceFramework.PCI_DSS: {
        "supported_reports": [
            ReportType.ACCESS_LOG,
            ReportType.DATA_ACCESS,
            ReportType.SECURITY_EVENTS,
            ReportType.SYSTEM_CHANGES,
        ],
        "default_retention_days": 365,  # 1 year minimum
        "required_fields": ["user_id", "action", "timestamp", "ip_address"],
        "data_classification": DataClassification.RESTRICTED,
    },
    ComplianceFramework.HIPAA: {
        "supported_reports": [
            ReportType.ACCESS_LOG,
            ReportType.DATA_ACCESS,
            ReportType.AUDIT_TRAIL,
            ReportType.SECURITY_EVENTS,
        ],
        "default_retention_days": 2190,  # 6 years
        "required_fields": ["user_id", "access_type", "timestamp", "purpose"],
        "data_classification": DataClassification.RESTRICTED,
    },
    ComplianceFramework.GDPR: {
        "supported_reports": [
            ReportType.DATA_ACCESS,
            ReportType.USER_ACTIVITY,
            ReportType.COMPLIANCE_SUMMARY,
        ],
        "default_retention_days": 1095,  # 3 years
        "required_fields": ["data_subject_id", "processing_purpose", "legal_basis"],
        "data_classification": DataClassification.CONFIDENTIAL,
    },
    ComplianceFramework.SOC2: {
        "supported_reports": [
            ReportType.AUDIT_TRAIL,
            ReportType.SECURITY_EVENTS,
            ReportType.SYSTEM_CHANGES,
            ReportType.INCIDENT_REPORT,
            ReportType.COMPLIANCE_SUMMARY,
        ],
        "default_retention_days": 365,
        "required_fields": ["control_id", "evidence_type", "test_result"],
        "data_classification": DataClassification.CONFIDENTIAL,
    },
    ComplianceFramework.NIST_CSF: {
        "supported_reports": [
            ReportType.RISK_ASSESSMENT,
            ReportType.SECURITY_EVENTS,
            ReportType.INCIDENT_REPORT,
            ReportType.COMPLIANCE_SUMMARY,
        ],
        "default_retention_days": 365,
        "required_fields": ["function", "category", "subcategory"],
        "data_classification": DataClassification.CONFIDENTIAL,
    },
    ComplianceFramework.ISO_27001: {
        "supported_reports": [
            ReportType.AUDIT_TRAIL,
            ReportType.RISK_ASSESSMENT,
            ReportType.SYSTEM_CHANGES,
            ReportType.COMPLIANCE_SUMMARY,
        ],
        "default_retention_days": 1095,  # 3 years
        "required_fields": ["control_objective", "control_id"],
        "data_classification": DataClassification.CONFIDENTIAL,
    },
}


def get_framework_config(framework: ComplianceFramework) -> Dict[str, Any]:
    """Get configuration for a compliance framework"""
    return FRAMEWORK_REPORT_MAPPINGS.get(framework, {
        "supported_reports": list(ReportType),
        "default_retention_days": 365,
        "required_fields": [],
        "data_classification": DataClassification.INTERNAL,
    })


def get_supported_frameworks() -> List[Dict[str, Any]]:
    """Get list of all supported frameworks with their configurations"""
    return [
        {
            "framework": framework.value,
            "display_name": framework.name.replace("_", " ").title(),
            "supported_reports": [r.value for r in config["supported_reports"]],
            "default_retention_days": config["default_retention_days"],
            "data_classification": config["data_classification"].value,
        }
        for framework, config in FRAMEWORK_REPORT_MAPPINGS.items()
    ]
