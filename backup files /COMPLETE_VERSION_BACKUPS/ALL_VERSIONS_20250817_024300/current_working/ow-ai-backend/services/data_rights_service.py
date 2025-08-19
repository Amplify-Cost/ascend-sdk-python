# 2. Data Subject Rights Service
# File: ow-ai-backend/services/data_rights_service.py
"""
GDPR/CCPA Data Subject Rights Processing Service
Implements automated compliance workflows
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import json
import uuid
from models_data_rights import DataSubjectRequest, DataLineage, ConsentRecord, DataErasureLog
from models import User, AgentAction  # Existing models
from services.immutable_audit_service import ImmutableAuditService

logger = logging.getLogger(__name__)

class DataSubjectRightsService:
    """Enterprise GDPR/CCPA compliance service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = ImmutableAuditService(db)
    
    def create_access_request(
        self,
        subject_email: str,
        legal_basis: str = "GDPR_ART_15",
        request_details: Dict[str, Any] = None,
        requester_ip: str = None
    ) -> DataSubjectRequest:
        """Create Right to Access request (GDPR Article 15)"""
        
        # Generate unique request ID
        request_id = f"DSR-{datetime.now(UTC).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create request
        request = DataSubjectRequest(
            request_id=request_id,
            subject_email=subject_email.lower().strip(),
            request_type="ACCESS",
            legal_basis=legal_basis,
            compliance_framework="GDPR" if legal_basis.startswith("GDPR") else "CCPA",
            request_details=request_details or {},
            due_date=datetime.now(UTC) + timedelta(days=30)
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Create audit log
        self.audit_service.log_event(
            event_type="DATA_SUBJECT_REQUEST",
            actor_id=subject_email,
            resource_type="DATA",
            resource_id=request_id,
            action="CREATE_ACCESS_REQUEST",
            event_data={
                "request_id": request_id,
                "legal_basis": legal_basis,
                "subject_email": subject_email,
                "due_date": request.due_date.isoformat()
            },
            risk_level="MEDIUM",
            compliance_tags=["GDPR", "PRIVACY"],
            ip_address=requester_ip
        )
        
        logger.info(f"Data access request created: {request_id} for {subject_email}")
        return request
    
    def process_access_request(self, request_id: str) -> Dict[str, Any]:
        """Process Right to Access request and gather all subject data"""
        
        request = self.db.query(DataSubjectRequest).filter(
            DataSubjectRequest.request_id == request_id
        ).first()
        
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.request_type != "ACCESS":
            raise ValueError(f"Request {request_id} is not an access request")
        
        # Update status
        request.status = "PROCESSING"
        self.db.commit()
        
        try:
            # Gather all data for the subject
            subject_data = self._gather_subject_data(request.subject_email)
            
            # Create structured export
            export_data = {
                "request_details": {
                    "request_id": request_id,
                    "subject_email": request.subject_email,
                    "generated_at": datetime.now(UTC).isoformat(),
                    "legal_basis": request.legal_basis
                },
                "personal_data": subject_data,
                "data_sources": self._get_data_sources(request.subject_email),
                "processing_activities": self._get_processing_activities(request.subject_email),
                "retention_periods": self._get_retention_info(request.subject_email)
            }
            
            # Store result
            request.result_data = export_data
            request.status = "COMPLETED"
            request.completed_at = datetime.now(UTC)
            request.delivery_status = "READY"
            
            self.db.commit()
            
            # Audit the completion
            self.audit_service.log_event(
                event_type="DATA_SUBJECT_REQUEST",
                actor_id="system",
                resource_type="DATA",
                resource_id=request_id,
                action="COMPLETE_ACCESS_REQUEST",
                event_data={
                    "request_id": request_id,
                    "records_found": len(subject_data),
                    "data_categories": list(subject_data.keys())
                },
                risk_level="LOW",
                compliance_tags=["GDPR", "PRIVACY"]
            )
            
            logger.info(f"Access request {request_id} processed successfully")
            return export_data
            
        except Exception as e:
            request.status = "FAILED"
            request.processing_notes = str(e)
            self.db.commit()
            logger.error(f"Failed to process access request {request_id}: {e}")
            raise
    
    def create_erasure_request(
        self,
        subject_email: str,
        erasure_scope: List[str] = None,
        legal_basis: str = "GDPR_ART_17",
        requester_ip: str = None
    ) -> DataSubjectRequest:
        """Create Right to Erasure request (GDPR Article 17)"""
        
        request_id = f"DSR-{datetime.now(UTC).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        request = DataSubjectRequest(
            request_id=request_id,
            subject_email=subject_email.lower().strip(),
            request_type="ERASURE",
            legal_basis=legal_basis,
            compliance_framework="GDPR" if legal_basis.startswith("GDPR") else "CCPA",
            request_details={
                "erasure_scope": erasure_scope or ["ALL"],
                "retention_exceptions": []
            },
            due_date=datetime.now(UTC) + timedelta(days=30)
        )
        
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        
        # Audit the request
        self.audit_service.log_event(
            event_type="DATA_SUBJECT_REQUEST",
            actor_id=subject_email,
            resource_type="DATA",
            resource_id=request_id,
            action="CREATE_ERASURE_REQUEST",
            event_data={
                "request_id": request_id,
                "legal_basis": legal_basis,
                "erasure_scope": erasure_scope or ["ALL"]
            },
            risk_level="HIGH",
            compliance_tags=["GDPR", "PRIVACY", "ERASURE"],
            ip_address=requester_ip
        )
        
        logger.info(f"Data erasure request created: {request_id} for {subject_email}")
        return request
    
    def _gather_subject_data(self, subject_email: str) -> Dict[str, Any]:
        """Gather all data associated with a data subject"""
        
        subject_data = {}
        
        # 1. User profile data
        user = self.db.query(User).filter(User.email == subject_email).first()
        if user:
            subject_data["profile"] = {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            }
        
        # 2. Agent interaction data
        if user:
            agent_actions = self.db.query(AgentAction).filter(
                AgentAction.user_id == user.id
            ).all()
            
            subject_data["agent_interactions"] = [
                {
                    "id": action.id,
                    "agent_id": action.agent_id,
                    "tool": action.tool,
                    "timestamp": action.timestamp,
                    "risk_level": action.risk_level,
                    "summary": getattr(action, 'summary', None)
                }
                for action in agent_actions
            ]
        
        # 3. Audit logs (from immutable audit system)
        try:
            from models_audit import ImmutableAuditLog
            audit_logs = self.db.query(ImmutableAuditLog).filter(
                or_(
                    ImmutableAuditLog.actor_id == subject_email,
                    ImmutableAuditLog.actor_id == str(user.id) if user else None
                )
            ).all()
            
            subject_data["audit_trail"] = [
                {
                    "id": str(log.id),
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "risk_level": log.risk_level
                }
                for log in audit_logs
            ]
        except Exception as e:
            logger.warning(f"Could not retrieve audit logs for {subject_email}: {e}")
            subject_data["audit_trail"] = []
        
        # 4. Consent records
        consent_records = self.db.query(ConsentRecord).filter(
            ConsentRecord.subject_email == subject_email
        ).all()
        
        subject_data["consent_history"] = [
            {
                "consent_type": record.consent_type,
                "purpose": record.purpose,
                "granted": record.granted,
                "granted_at": record.granted_at.isoformat() if record.granted_at else None,
                "withdrawn_at": record.withdrawn_at.isoformat() if record.withdrawn_at else None
            }
            for record in consent_records
        ]
        
        return subject_data
    
    def _get_data_sources(self, subject_email: str) -> List[Dict[str, str]]:
        """Get list of data sources containing subject data"""
        return [
            {"source": "users", "category": "Profile Data", "retention": "Account lifetime"},
            {"source": "agent_actions", "category": "Interaction Data", "retention": "7 years"},
            {"source": "immutable_audit_logs", "category": "Audit Data", "retention": "7 years"},
            {"source": "consent_records", "category": "Consent Data", "retention": "3 years after withdrawal"}
        ]
    
    def _get_processing_activities(self, subject_email: str) -> List[Dict[str, str]]:
        """Get processing activities for the subject"""
        return [
            {
                "activity": "User Authentication",
                "purpose": "Platform access control",
                "legal_basis": "Contract performance"
            },
            {
                "activity": "Agent Interaction Logging", 
                "purpose": "Service delivery and audit",
                "legal_basis": "Legitimate interest"
            },
            {
                "activity": "Security Monitoring",
                "purpose": "Platform security and compliance",
                "legal_basis": "Legitimate interest"
            }
        ]
    
    def _get_retention_info(self, subject_email: str) -> Dict[str, str]:
        """Get data retention information"""
        return {
            "profile_data": "Retained while account is active",
            "interaction_data": "7 years for compliance purposes", 
            "audit_data": "7 years as required by regulations",
            "consent_data": "3 years after consent withdrawal"
        }
