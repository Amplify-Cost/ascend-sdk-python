# models_ml_registry.py - Enterprise ML Model Registry
"""
Enterprise ML Model Registry Database Schema

Purpose: Track deployed AI/ML models for governance, compliance, and agent scanning
Architecture: SQLAlchemy ORM with PostgreSQL-optimized JSONB storage
Compliance: SOX, GDPR, HIPAA, PCI-DSS audit requirements
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, UTC
from database import Base
import enum


class ComplianceStatus(enum.Enum):
    """Enterprise compliance status levels"""
    COMPLIANT = "compliant"
    PENDING_REVIEW = "pending_review"
    NON_COMPLIANT = "non_compliant"
    AUDIT_REQUIRED = "audit_required"
    DEPRECATED = "deprecated"


class ModelRiskLevel(enum.Enum):
    """Enterprise risk classification"""
    CRITICAL = "critical"  # Customer-facing, financial impact
    HIGH = "high"          # Business-critical operations
    MEDIUM = "medium"      # Internal tools, limited scope
    LOW = "low"            # Dev/test, non-production


class DeployedModel(Base):
    """
    Enterprise ML Model Registry

    Tracks all deployed AI/ML models across environments for:
    - Compliance scanning (agents need to know what models exist)
    - Governance enforcement (GDPR, SOX, HIPAA approvals)
    - Risk assessment (model risk scoring)
    - Audit trails (who deployed what, when)
    """
    __tablename__ = "deployed_models"

    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(255), unique=True, nullable=False, index=True)
    model_name = Column(String(500), nullable=False)
    version = Column(String(100), nullable=False)

    # Deployment tracking
    environment = Column(String(50), nullable=False, index=True)  # production, staging, development
    deployed_at = Column(DateTime(timezone=True), nullable=False)
    deployed_by = Column(String(255), nullable=False)  # email or service account

    # Ownership and responsibility
    model_owner = Column(String(255), nullable=False)  # Team or individual owner
    business_unit = Column(String(255))  # Optional: Finance, Marketing, Operations, etc.

    # Compliance and governance
    compliance_status = Column(SQLEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.PENDING_REVIEW, index=True)
    last_audit = Column(DateTime(timezone=True))
    next_audit_due = Column(DateTime(timezone=True))

    # Regulatory approvals
    gdpr_approved = Column(Boolean, default=False, nullable=False)
    gdpr_approval_date = Column(DateTime(timezone=True))
    gdpr_approved_by = Column(String(255))

    sox_compliant = Column(Boolean, default=False, nullable=False)
    sox_approval_date = Column(DateTime(timezone=True))
    sox_approved_by = Column(String(255))

    pci_dss_compliant = Column(Boolean, default=False, nullable=False)
    pci_approval_date = Column(DateTime(timezone=True))
    pci_approved_by = Column(String(255))

    hipaa_compliant = Column(Boolean, default=False, nullable=False)
    hipaa_approval_date = Column(DateTime(timezone=True))
    hipaa_approved_by = Column(String(255))

    # Technical metadata
    model_type = Column(String(100))  # classification, regression, clustering, neural_network, etc.
    framework = Column(String(100))   # tensorflow, pytorch, scikit-learn, xgboost, etc.
    framework_version = Column(String(50))

    # Risk assessment
    risk_level = Column(SQLEnum(ModelRiskLevel), nullable=False, default=ModelRiskLevel.MEDIUM, index=True)
    risk_score = Column(Integer)  # 0-100 enterprise risk score
    risk_justification = Column(Text)  # Why this risk level

    # Model performance and monitoring
    accuracy_score = Column(Integer)  # Latest accuracy percentage
    performance_metrics = Column(JSONB)  # Flexible JSON storage for detailed metrics

    # Data governance
    data_sources = Column(JSONB)  # List of data sources used for training
    data_classification = Column(String(50))  # public, internal, confidential, restricted
    contains_pii = Column(Boolean, default=False, nullable=False)
    contains_phi = Column(Boolean, default=False, nullable=False)  # Protected Health Information
    contains_pci = Column(Boolean, default=False, nullable=False)  # Payment Card data

    # Model lifecycle
    status = Column(String(50), nullable=False, default="active", index=True)  # active, deprecated, decommissioned
    decommission_date = Column(DateTime(timezone=True))
    decommission_reason = Column(Text)

    # External registry integration
    external_registry_type = Column(String(100))  # mlflow, sagemaker, azureml, vertex_ai
    external_registry_id = Column(String(500))  # ID in external system
    external_registry_url = Column(String(1000))  # Direct link to model in registry

    # Audit trail metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255))

    # Additional enterprise metadata
    extra_data = Column(JSONB)  # Flexible storage for organization-specific fields

    # Model documentation
    description = Column(Text)
    use_cases = Column(JSONB)  # List of approved use cases
    limitations = Column(Text)  # Known limitations and edge cases
    bias_assessment = Column(JSONB)  # Bias analysis results

    # Integration with approval workflow
    requires_approval_for_changes = Column(Boolean, default=True, nullable=False)
    approval_workflow_id = Column(String(100))  # Link to workflow in unified governance

    def __repr__(self):
        return f"<DeployedModel(id={self.id}, model_id='{self.model_id}', version='{self.version}', environment='{self.environment}')>"

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "environment": self.environment,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deployed_by": self.deployed_by,
            "model_owner": self.model_owner,
            "business_unit": self.business_unit,
            "compliance_status": self.compliance_status.value if self.compliance_status else None,
            "last_audit": self.last_audit.isoformat() if self.last_audit else None,
            "next_audit_due": self.next_audit_due.isoformat() if self.next_audit_due else None,
            "gdpr_approved": self.gdpr_approved,
            "sox_compliant": self.sox_compliant,
            "pci_dss_compliant": self.pci_dss_compliant,
            "hipaa_compliant": self.hipaa_compliant,
            "model_type": self.model_type,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "risk_level": self.risk_level.value if self.risk_level else None,
            "risk_score": self.risk_score,
            "accuracy_score": self.accuracy_score,
            "data_classification": self.data_classification,
            "contains_pii": self.contains_pii,
            "contains_phi": self.contains_phi,
            "contains_pci": self.contains_pci,
            "status": self.status,
            "external_registry_type": self.external_registry_type,
            "external_registry_url": self.external_registry_url,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
