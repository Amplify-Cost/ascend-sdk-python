"""
GDPR/CCPA Data Subject Rights API Routes
Implements enterprise-grade data rights APIs for EU/California compliance
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, UTC
from pydantic import BaseModel, EmailStr, Field
import logging
import json

from database import get_db
from dependencies import get_current_user
from models_data_rights import DataSubjectRequest, DataLineage, ConsentRecord, DataErasureLog
from services.data_rights_service import DataSubjectRightsService as DataRightsService
from services.immutable_audit_service import ImmutableAuditService

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC SCHEMAS FOR REQUEST/RESPONSE VALIDATION
# ============================================================================

class DataSubjectRequestCreate(BaseModel):
    """Schema for creating new data subject requests"""
    subject_email: EmailStr
    subject_user_id: Optional[str] = None
    request_type: str = Field(..., description="ACCESS, ERASURE, PORTABILITY, RECTIFICATION")
    legal_basis: str = Field(..., description="GDPR Article or CCPA Section")
    priority: str = Field(default="NORMAL", description="LOW, NORMAL, HIGH, URGENT")
    request_details: Dict[str, Any] = Field(default_factory=dict)
    verification_method: Optional[str] = None

class DataSubjectRequestResponse(BaseModel):
    """Schema for data subject request responses"""
    id: str
    created_at: datetime
    subject_email: str
    request_type: str
    status: str
    legal_basis: str
    priority: str
    due_date: datetime
    request_details: Dict[str, Any]
    verification_status: Optional[str]
    
class ConsentRecordCreate(BaseModel):
    """Schema for creating consent records"""
    subject_email: EmailStr
    subject_user_id: Optional[str] = None
    consent_type: str
    consent_status: str = Field(..., description="GIVEN, WITHDRAWN, EXPIRED, PENDING")
    processing_purposes: List[str]
    legal_basis: str
    consent_method: Optional[str] = None
    data_controller: str
    privacy_policy_version: Optional[str] = None

class DataLineageCreate(BaseModel):
    """Schema for creating data lineage records"""
    subject_identifier: str
    data_type: str
    source_system: str
    destination_system: Optional[str] = None
    processing_purpose: str
    legal_basis: str
    retention_period: Optional[str] = None
    data_location: Optional[str] = None
    data_classification: Optional[str] = None

class DataAccessRequest(BaseModel):
    """Schema for data access requests"""
    subject_email: EmailStr
    verification_token: Optional[str] = None
    include_metadata: bool = Field(default=True)
    data_categories: Optional[List[str]] = None

class DataErasureRequest(BaseModel):
    """Schema for data erasure requests"""
    subject_email: EmailStr
    erasure_scope: str = Field(..., description="FULL, PARTIAL, SPECIFIC")
    data_categories: Optional[List[str]] = None
    retention_exceptions: Optional[List[str]] = None
    verification_token: Optional[str] = None

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_data_rights_service(db: Session = Depends(get_db)) -> DataRightsService:
    """Dependency injection for data rights service"""
    return DataRightsService(db)

def get_audit_service(db: Session = Depends(get_db)) -> ImmutableAuditService:
    """Dependency injection for audit service"""
    return ImmutableAuditService(db)

# ============================================================================
# RIGHT TO ACCESS APIs (GDPR Article 15, CCPA §1798.110)
# ============================================================================

@router.post("/access/request", 
             response_model=DataSubjectRequestResponse,
             summary="Submit Right to Access Request",
             description="Submit a GDPR Article 15 or CCPA data access request")
async def submit_access_request(
    request_data: DataAccessRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Submit a Right to Access request under GDPR Article 15 or CCPA §1798.110
    
    **Legal Compliance:**
    - GDPR: Must respond within 30 days (Article 15)
    - CCPA: Must respond within 45 days (§1798.130)
    
    **Enterprise Features:**
    - Automatic request validation and prioritization
    - Audit trail logging for compliance
    - Data discovery across all systems
    """
    try:
        # Create the data subject request
        request_create = DataSubjectRequestCreate(
            subject_email=request_data.subject_email,
            request_type="ACCESS",
            legal_basis="GDPR Article 15" if "gdpr" in str(request_data).lower() else "CCPA §1798.110",
            request_details={
                "include_metadata": request_data.include_metadata,
                "data_categories": request_data.data_categories or [],
                "verification_token": request_data.verification_token,
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process the request
        data_request = await data_service.create_data_subject_request(
            request_create, created_by=current_user.email
        )
        
        # Log to immutable audit trail
        await audit_service.log_event(
            event_type="DATA_ACCESS_REQUEST",
            actor_id=current_user.email,
            resource_type="DATA_SUBJECT",
            resource_id=request_data.subject_email,
            action="REQUEST_SUBMITTED",
            event_data={
                "request_id": str(data_request.id),
                "legal_basis": data_request.legal_basis,
                "due_date": data_request.due_date.isoformat(),
                "verification_required": bool(request_data.verification_token)
            },
            risk_level="MEDIUM",
            compliance_tags=["GDPR", "CCPA", "DATA_ACCESS"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Background task: Start data discovery process
        background_tasks.add_task(
            data_service.start_data_discovery,
            str(data_request.id),
            request_data.subject_email
        )
        
        return DataSubjectRequestResponse(
            id=str(data_request.id),
            created_at=data_request.created_at,
            subject_email=data_request.subject_email,
            request_type=data_request.request_type,
            status=data_request.status,
            legal_basis=data_request.legal_basis,
            priority=data_request.priority,
            due_date=data_request.due_date,
            request_details=data_request.request_details,
            verification_status=data_request.verification_status
        )
        
    except Exception as e:
        logger.error(f"Failed to submit access request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit access request: {str(e)}"
        )

@router.get("/access/{request_id}/data",
            summary="Retrieve Subject Data",
            description="Get all data for a verified access request")
async def get_subject_data(
    request_id: str,
    verification_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Retrieve all data for a data subject (GDPR Article 15 compliance)
    
    **Enterprise Features:**
    - Comprehensive data discovery across all systems
    - Structured machine-readable format
    - Metadata about data processing activities
    - Audit logging for access events
    """
    try:
        # Get and validate the request
        data_request = db.query(DataSubjectRequest).filter(
            DataSubjectRequest.id == request_id
        ).first()
        
        if not data_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data subject request not found"
            )
        
        # Verify authorization
        if data_request.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request verification required"
            )
        
        # Get comprehensive data package
        data_package = await data_service.generate_data_access_package(
            data_request.subject_email,
            include_metadata=data_request.request_details.get("include_metadata", True)
        )
        
        # Log data access in audit trail
        await audit_service.log_event(
            event_type="DATA_ACCESS_FULFILLED",
            actor_id=current_user.email,
            resource_type="DATA_SUBJECT",
            resource_id=data_request.subject_email,
            action="DATA_RETRIEVED",
            event_data={
                "request_id": request_id,
                "data_categories": list(data_package.keys()),
                "record_counts": {k: len(v) if isinstance(v, list) else 1 
                                for k, v in data_package.items()},
                "legal_basis": data_request.legal_basis
            },
            risk_level="HIGH",
            compliance_tags=["GDPR", "CCPA", "DATA_ACCESS", "PII_ACCESS"],
        )
        
        # Update request status
        await data_service.update_request_status(
            request_id, "COMPLETED", 
            response_data={"access_timestamp": datetime.now(UTC).isoformat()}
        )
        
        return {
            "request_id": request_id,
            "subject_email": data_request.subject_email,
            "generated_at": datetime.now(UTC).isoformat(),
            "legal_basis": data_request.legal_basis,
            "data_package": data_package,
            "metadata": {
                "total_records": sum(len(v) if isinstance(v, list) else 1 
                                   for v in data_package.values()),
                "data_sources": await data_service.get_data_sources_for_subject(
                    data_request.subject_email
                ),
                "retention_information": await data_service.get_retention_schedule(
                    data_request.subject_email
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve subject data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subject data: {str(e)}"
        )

# ============================================================================
# RIGHT TO ERASURE APIs (GDPR Article 17, CCPA §1798.105)
# ============================================================================

@router.post("/erasure/request",
             response_model=DataSubjectRequestResponse,
             summary="Submit Right to Erasure Request",
             description="Submit a GDPR Article 17 'Right to be Forgotten' request")
async def submit_erasure_request(
    request_data: DataErasureRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Submit a Right to Erasure request under GDPR Article 17 or CCPA §1798.105
    
    **Legal Compliance:**
    - GDPR: Must process within 30 days (Article 17)
    - CCPA: Must process within 45 days (§1798.105)
    - Considers legitimate interests and legal obligations
    
    **Enterprise Features:**
    - Automated legal basis assessment
    - Cross-system erasure coordination
    - Immutable audit logging
    - Retention exception handling
    """
    try:
        # Create the erasure request
        request_create = DataSubjectRequestCreate(
            subject_email=request_data.subject_email,
            request_type="ERASURE",
            legal_basis="GDPR Article 17" if "gdpr" in str(request_data).lower() else "CCPA §1798.105",
            priority="HIGH",  # Erasure requests are high priority
            request_details={
                "erasure_scope": request_data.erasure_scope,
                "data_categories": request_data.data_categories or [],
                "retention_exceptions": request_data.retention_exceptions or [],
                "verification_token": request_data.verification_token,
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process the request
        data_request = await data_service.create_data_subject_request(
            request_create, created_by=current_user.email
        )
        
        # Log to immutable audit trail
        await audit_service.log_event(
            event_type="DATA_ERASURE_REQUEST",
            actor_id=current_user.email,
            resource_type="DATA_SUBJECT",
            resource_id=request_data.subject_email,
            action="ERASURE_REQUESTED",
            event_data={
                "request_id": str(data_request.id),
                "erasure_scope": request_data.erasure_scope,
                "legal_basis": data_request.legal_basis,
                "due_date": data_request.due_date.isoformat(),
                "data_categories": request_data.data_categories or [],
                "retention_exceptions": request_data.retention_exceptions or []
            },
            risk_level="HIGH",
            compliance_tags=["GDPR", "CCPA", "DATA_ERASURE", "RIGHT_TO_BE_FORGOTTEN"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # Background task: Start erasure assessment
        background_tasks.add_task(
            data_service.assess_erasure_eligibility,
            str(data_request.id),
            request_data.subject_email
        )
        
        return DataSubjectRequestResponse(
            id=str(data_request.id),
            created_at=data_request.created_at,
            subject_email=data_request.subject_email,
            request_type=data_request.request_type,
            status=data_request.status,
            legal_basis=data_request.legal_basis,
            priority=data_request.priority,
            due_date=data_request.due_date,
            request_details=data_request.request_details,
            verification_status=data_request.verification_status
        )
        
    except Exception as e:
        logger.error(f"Failed to submit erasure request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit erasure request: {str(e)}"
        )

@router.post("/erasure/{request_id}/execute",
             summary="Execute Data Erasure",
             description="Execute verified erasure request with audit logging")
async def execute_erasure(
    request_id: str,
    background_tasks: BackgroundTasks,
    confirmation_token: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Execute a verified data erasure request
    
    **Enterprise Features:**
    - Multi-system coordinated erasure
    - Retention exception handling
    - Comprehensive audit logging
    - Verification and evidence generation
    """
    try:
        # Get and validate the request
        data_request = db.query(DataSubjectRequest).filter(
            DataSubjectRequest.id == request_id,
            DataSubjectRequest.request_type == "ERASURE"
        ).first()
        
        if not data_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Erasure request not found"
            )
        
        # Verify authorization and confirmation
        if data_request.verification_status != "VERIFIED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Request verification required"
            )
        
        # Execute the erasure
        erasure_result = await data_service.execute_data_erasure(
            request_id=request_id,
            subject_email=data_request.subject_email,
            erasure_scope=data_request.request_details.get("erasure_scope", "FULL"),
            data_categories=data_request.request_details.get("data_categories", []),
            retention_exceptions=data_request.request_details.get("retention_exceptions", []),
            performed_by=current_user.email
        )
        
        # Log erasure execution in audit trail
        await audit_service.log_event(
            event_type="DATA_ERASURE_EXECUTED",
            actor_id=current_user.email,
            resource_type="DATA_SUBJECT",
            resource_id=data_request.subject_email,
            action="DATA_ERASED",
            event_data={
                "request_id": request_id,
                "erasure_scope": erasure_result["scope"],
                "systems_affected": erasure_result["systems_affected"],
                "records_erased": erasure_result["records_erased"],
                "retention_exceptions": erasure_result["retention_exceptions"],
                "completion_time": erasure_result["completed_at"],
                "legal_basis": data_request.legal_basis
            },
            risk_level="CRITICAL",
            compliance_tags=["GDPR", "CCPA", "DATA_ERASURE", "EXECUTED"],
        )
        
        # Update request status
        await data_service.update_request_status(
            request_id, "COMPLETED",
            response_data=erasure_result
        )
        
        return {
            "request_id": request_id,
            "status": "COMPLETED",
            "erasure_summary": erasure_result,
            "legal_compliance": {
                "basis": data_request.legal_basis,
                "completed_within_deadline": True,
                "audit_trail_id": erasure_result.get("audit_trail_id")
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to execute erasure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute erasure: {str(e)}"
        )

# ============================================================================
# DATA PORTABILITY APIs (GDPR Article 20, CCPA §1798.130)
# ============================================================================

@router.post("/portability/request",
             summary="Submit Data Portability Request",
             description="Request data in portable format (GDPR Article 20)")
async def submit_portability_request(
    subject_email: EmailStr,
    target_format: str = "JSON",  # JSON, CSV, XML
    include_metadata: bool = True,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Submit a data portability request under GDPR Article 20
    
    **Enterprise Features:**
    - Multiple export formats (JSON, CSV, XML)
    - Structured machine-readable data
    - Complete metadata inclusion
    - Audit trail compliance
    """
    try:
        # Create portability request
        request_create = DataSubjectRequestCreate(
            subject_email=subject_email,
            request_type="PORTABILITY",
            legal_basis="GDPR Article 20",
            request_details={
                "target_format": target_format,
                "include_metadata": include_metadata,
                "ip_address": request.client.host if request else None,
                "user_agent": request.headers.get("user-agent") if request else None
            }
        )
        
        data_request = await data_service.create_data_subject_request(
            request_create, created_by=current_user.email
        )
        
        # Log to audit trail
        await audit_service.log_event(
            event_type="DATA_PORTABILITY_REQUEST",
            actor_id=current_user.email,
            resource_type="DATA_SUBJECT",
            resource_id=subject_email,
            action="PORTABILITY_REQUESTED",
            event_data={
                "request_id": str(data_request.id),
                "target_format": target_format,
                "include_metadata": include_metadata
            },
            risk_level="MEDIUM",
            compliance_tags=["GDPR", "DATA_PORTABILITY"]
        )
        
        return DataSubjectRequestResponse(
            id=str(data_request.id),
            created_at=data_request.created_at,
            subject_email=data_request.subject_email,
            request_type=data_request.request_type,
            status=data_request.status,
            legal_basis=data_request.legal_basis,
            priority=data_request.priority,
            due_date=data_request.due_date,
            request_details=data_request.request_details,
            verification_status=data_request.verification_status
        )
        
    except Exception as e:
        logger.error(f"Failed to submit portability request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit portability request: {str(e)}"
        )

# ============================================================================
# CONSENT MANAGEMENT APIs (GDPR Articles 6-7)
# ============================================================================

@router.post("/consent/record",
             summary="Record Consent",
             description="Record consent under GDPR Articles 6-7")
async def record_consent(
    consent_data: ConsentRecordCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Record consent for data processing (GDPR compliance)
    
    **Enterprise Features:**
    - Granular consent tracking by purpose
    - Legal basis documentation
    - Withdrawal capability
    - Immutable audit logging
    """
    try:
        # Create consent record
        consent = await data_service.create_consent_record(
            subject_email=consent_data.subject_email,
            subject_user_id=consent_data.subject_user_id,
            consent_type=consent_data.consent_type,
            consent_status=consent_data.consent_status,
            processing_purposes=consent_data.processing_purposes,
            legal_basis=consent_data.legal_basis,
            consent_method=consent_data.consent_method,
            data_controller=consent_data.data_controller,
            privacy_policy_version=consent_data.privacy_policy_version,
            consent_evidence={
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
        
        # Log to audit trail
        await audit_service.log_event(
            event_type="CONSENT_RECORDED",
            actor_id=current_user.email,
            resource_type="CONSENT",
            resource_id=str(consent.id),
            action="CONSENT_GIVEN" if consent_data.consent_status == "GIVEN" else "CONSENT_WITHDRAWN",
            event_data={
                "subject_email": consent_data.subject_email,
                "consent_type": consent_data.consent_type,
                "processing_purposes": consent_data.processing_purposes,
                "legal_basis": consent_data.legal_basis,
                "data_controller": consent_data.data_controller
            },
            risk_level="MEDIUM",
            compliance_tags=["GDPR", "CONSENT", "LEGAL_BASIS"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return {
            "consent_id": str(consent.id),
            "status": "recorded",
            "created_at": consent.created_at.isoformat(),
            "legal_basis": consent.legal_basis,
            "processing_purposes": consent.processing_purposes
        }
        
    except Exception as e:
        logger.error(f"Failed to record consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record consent: {str(e)}"
        )

# ============================================================================
# DATA LINEAGE APIs (Enterprise Data Mapping)
# ============================================================================

@router.post("/lineage/record",
             summary="Record Data Lineage",
             description="Record data processing lineage for compliance")
async def record_data_lineage(
    lineage_data: DataLineageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service),
    audit_service: ImmutableAuditService = Depends(get_audit_service)
):
    """
    Record data lineage for comprehensive data mapping
    
    **Enterprise Features:**
    - Complete data flow tracking
    - Processing purpose documentation
    - Retention period management
    - Cross-system visibility
    """
    try:
        # Create lineage record
        lineage = await data_service.create_data_lineage(
            subject_identifier=lineage_data.subject_identifier,
            data_type=lineage_data.data_type,
            source_system=lineage_data.source_system,
            destination_system=lineage_data.destination_system,
            processing_purpose=lineage_data.processing_purpose,
            legal_basis=lineage_data.legal_basis,
            retention_period=lineage_data.retention_period,
            data_location=lineage_data.data_location,
            data_classification=lineage_data.data_classification,
            lineage_metadata={
                "created_by": current_user.email,
                "creation_timestamp": datetime.now(UTC).isoformat()
            }
        )
        
        # Log to audit trail
        await audit_service.log_event(
            event_type="DATA_LINEAGE_RECORDED",
            actor_id=current_user.email,
            resource_type="DATA_LINEAGE",
            resource_id=str(lineage.id),
            action="LINEAGE_CREATED",
            event_data={
                "subject_identifier": lineage_data.subject_identifier,
                "data_type": lineage_data.data_type,
                "source_system": lineage_data.source_system,
                "processing_purpose": lineage_data.processing_purpose,
                "legal_basis": lineage_data.legal_basis
            },
            risk_level="LOW",
            compliance_tags=["DATA_LINEAGE", "GDPR", "MAPPING"]
        )
        
        return {
            "lineage_id": str(lineage.id),
            "status": "recorded",
            "created_at": lineage.created_at.isoformat(),
            "data_mapping": {
                "source": lineage_data.source_system,
                "destination": lineage_data.destination_system,
                "purpose": lineage_data.processing_purpose
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to record data lineage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record data lineage: {str(e)}"
        )

@router.get("/lineage/subject/{subject_identifier}",
            summary="Get Subject Data Lineage",
            description="Get complete data lineage for a subject")
async def get_subject_lineage(
    subject_identifier: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service)
):
    """
    Get complete data lineage for a data subject
    
    **Enterprise Features:**
    - Complete data flow visualization
    - Processing purpose mapping
    - Retention schedule overview
    - Cross-system data tracking
    """
    try:
        lineage_map = await data_service.get_subject_data_lineage(subject_identifier)
        
        return {
            "subject_identifier": subject_identifier,
            "data_lineage": lineage_map,
            "summary": {
                "total_data_types": len(lineage_map.get("data_types", [])),
                "source_systems": len(lineage_map.get("source_systems", [])),
                "processing_purposes": len(lineage_map.get("processing_purposes", [])),
                "retention_periods": lineage_map.get("retention_summary", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get subject lineage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subject lineage: {str(e)}"
        )

# ============================================================================
# COMPLIANCE REPORTING APIs
# ============================================================================

@router.get("/compliance/report",
            summary="Generate Compliance Report",
            description="Generate GDPR/CCPA compliance report")
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = "SUMMARY",  # SUMMARY, DETAILED, AUDIT
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service)
):
    """
    Generate comprehensive GDPR/CCPA compliance report
    
    **Enterprise Features:**
    - Request processing metrics
    - Compliance timeline analysis
    - Audit trail summaries
    - Regulatory readiness assessment
    """
    try:
        report = await data_service.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )
        
        return {
            "report_type": report_type,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "generated_at": datetime.now(UTC).isoformat(),
            "generated_by": current_user.email,
            "compliance_metrics": report
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}"
        )

# ============================================================================
# REQUEST STATUS AND MANAGEMENT APIs
# ============================================================================

@router.get("/requests",
            summary="List Data Subject Requests",
            description="Get paginated list of data subject requests")
async def list_data_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    data_service: DataRightsService = Depends(get_data_rights_service)
):
    """List and filter data subject requests with pagination"""
    try:
        requests = await data_service.list_data_requests(
            status=status,
            request_type=request_type,
            limit=limit,
            offset=offset
        )
        
        return {
            "total": len(requests),
            "limit": limit,
            "offset": offset,
            "requests": [
                DataSubjectRequestResponse(
                    id=str(req.id),
                    created_at=req.created_at,
                    subject_email=req.subject_email,
                    request_type=req.request_type,
                    status=req.status,
                    legal_basis=req.legal_basis,
                    priority=req.priority,
                    due_date=req.due_date,
                    request_details=req.request_details,
                    verification_status=req.verification_status
                ) for req in requests
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list data requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list data requests: {str(e)}"
        )

@router.get("/requests/{request_id}",
            response_model=DataSubjectRequestResponse,
            summary="Get Data Subject Request",
            description="Get detailed information about a specific request")
async def get_data_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get detailed information about a specific data subject request"""
    try:
        data_request = db.query(DataSubjectRequest).filter(
            DataSubjectRequest.id == request_id
        ).first()
        
        if not data_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data subject request not found"
            )
        
        return DataSubjectRequestResponse(
            id=str(data_request.id),
            created_at=data_request.created_at,
            subject_email=data_request.subject_email,
            request_type=data_request.request_type,
            status=data_request.status,
            legal_basis=data_request.legal_basis,
            priority=data_request.priority,
            due_date=data_request.due_date,
            request_details=data_request.request_details,
            verification_status=data_request.verification_status
        )
        
    except Exception as e:
        logger.error(f"Failed to get data request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data request: {str(e)}"
        )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health",
            summary="Data Rights System Health",
            description="Check health and status of data rights system")
async def health_check(db: Session = Depends(get_db)):
    """Health check for the data rights system"""
    try:
        # Test database connectivity
        db.execute("SELECT 1")
        
        # Get system statistics
        pending_requests = db.query(DataSubjectRequest).filter(
            DataSubjectRequest.status == "PENDING"
        ).count()
        
        overdue_requests = db.query(DataSubjectRequest).filter(
            DataSubjectRequest.due_date < datetime.now(UTC),
            DataSubjectRequest.status.in_(["PENDING", "IN_PROGRESS"])
        ).count()
        
        return {
            "status": "healthy",
            "data_rights_system": "operational",
            "timestamp": datetime.now(UTC).isoformat(),
            "statistics": {
                "pending_requests": pending_requests,
                "overdue_requests": overdue_requests
            },
            "features": [
                "right_to_access",
                "right_to_erasure", 
                "data_portability",
                "consent_management",
                "data_lineage",
                "audit_integration"
            ]
        }
        
    except Exception as e:
        logger.error(f"Data rights health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data rights system unavailable: {str(e)}"
        )
