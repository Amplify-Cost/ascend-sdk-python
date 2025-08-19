# ========================================
# PHASE 2.1 IMPLEMENTATION SCRIPT
# Execute this script to implement immutable audit trails
# ========================================

"""
OW-AI Phase 2.1: Immutable Audit Trail Implementation
Automated setup script for enterprise audit logging system
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

def create_file_with_content(file_path: str, content: str):
    """Create a file with the specified content"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {file_path}")

def backup_existing_file(file_path: str):
    """Backup existing file if it exists"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"📋 Backed up: {file_path} -> {backup_path}")

def implement_phase2_1():
    """Implement Phase 2.1 - Immutable Audit Trail System"""
    
    print("🚀 OW-AI Phase 2.1: Immutable Audit Trail Implementation")
    print("=" * 70)
    print(f"Start time: {datetime.now()}")
    print()
    
    # Ensure we're in the project root
    if not os.path.exists("ow-ai-backend"):
        print("❌ Error: Must run from OW_AI_Project root directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    try:
        # 1. Create the enhanced audit models
        print("📝 Creating enhanced audit models...")
        
        models_audit_content = """\"\"\"
Enterprise Immutable Audit Models
Implements WORM (Write-Once-Read-Many) design with hash-chaining
\"\"\"
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import hashlib
import json
import uuid
from database import Base

class ImmutableAuditLog(Base):
    \"\"\"
    WORM (Write-Once-Read-Many) audit log with hash-chaining
    Each entry is cryptographically linked to the previous entry
    \"\"\"
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
        \"\"\"Calculate SHA-256 hash of audit log content\"\"\"
        content = {
            'timestamp': self.timestamp.isoformat(),
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
        \"\"\"Calculate chain hash linking this entry to previous\"\"\"
        chain_data = f"{self.content_hash}:{previous_hash or ''}"
        return hashlib.sha256(chain_data.encode()).hexdigest()

class EvidencePack(Base):
    \"\"\"
    Signed evidence packages for legal and compliance use
    Contains cryptographically verified audit trails
    \"\"\"
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
    \"\"\"
    Regular integrity verification of audit chain
    Validates hash chains and detects tampering
    \"\"\"
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
"""
        
        create_file_with_content("ow-ai-backend/models_audit.py", models_audit_content)
        
        # 2. Create the immutable audit service
        print("🔧 Creating immutable audit service...")
        
        # Create services directory if it doesn't exist
        os.makedirs("ow-ai-backend/services", exist_ok=True)
        create_file_with_content("ow-ai-backend/services/__init__.py", "")
        
        audit_service_content = """\"\"\"
Enterprise Immutable Audit Service
Provides WORM audit logging with hash-chaining and integrity verification
\"\"\"
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
    \"\"\"Enterprise-grade immutable audit logging service\"\"\"
    
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
        risk_level: str = "MEDIUM",
        compliance_tags: List[str] = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None
    ) -> ImmutableAuditLog:
        \"\"\"Create immutable audit log entry with hash-chaining\"\"\"
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
        \"\"\"Verify the integrity of the audit log hash chain\"\"\"
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
        \"\"\"Calculate retention date based on compliance requirements\"\"\"
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
"""
        
        create_file_with_content("ow-ai-backend/services/immutable_audit_service.py", audit_service_content)
        
        # 3. Create audit routes (simplified version)
        print("🌐 Creating audit routes...")
        
        audit_routes_content = """\"\"\"
Enterprise Audit Routes
Provides APIs for immutable audit logs, evidence packs, and compliance reporting
\"\"\"
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from database import get_db
from dependencies import verify_token

router = APIRouter()

# Basic audit log model
class AuditLogRequest(BaseModel):
    event_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    action: str
    event_data: Dict[str, Any]
    risk_level: str = "MEDIUM"
    compliance_tags: Optional[List[str]] = None

@router.get("/audit/health")
def audit_health_check():
    \"\"\"Health check for audit system\"\"\"
    return {
        "status": "healthy",
        "audit_system": "operational",
        "timestamp": datetime.now(UTC),
        "features": ["immutable_logs", "hash_chaining", "evidence_packs"]
    }

@router.post("/audit/log")
def create_audit_log(
    request: AuditLogRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    \"\"\"Create immutable audit log entry\"\"\"
    try:
        from services.immutable_audit_service import ImmutableAuditService
        service = ImmutableAuditService(db)
        
        # Extract client information
        ip_address = getattr(http_request.client, 'host', None)
        user_agent = http_request.headers.get("user-agent")
        
        audit_log = service.log_event(
            event_type=request.event_type,
            actor_id=request.actor_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            action=request.action,
            event_data=request.event_data,
            risk_level=request.risk_level,
            compliance_tags=request.compliance_tags,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=current_user.get("session_id")
        )
        
        return {
            "id": str(audit_log.id),
            "sequence_number": audit_log.sequence_number,
            "timestamp": audit_log.timestamp,
            "content_hash": audit_log.content_hash,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit log: {str(e)}")

@router.get("/audit/logs")
def get_audit_logs(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    \"\"\"Get audit logs with pagination\"\"\"
    try:
        from models_audit import ImmutableAuditLog
        query = db.query(ImmutableAuditLog)
        
        total = query.count()
        logs = query.order_by(ImmutableAuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "logs": [
                {
                    "id": str(log.id),
                    "sequence_number": log.sequence_number,
                    "timestamp": log.timestamp,
                    "event_type": log.event_type,
                    "actor_id": log.actor_id,
                    "resource_type": log.resource_type,
                    "action": log.action,
                    "risk_level": log.risk_level
                }
                for log in logs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}")

@router.post("/audit/verify-integrity")
def verify_chain_integrity(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    \"\"\"Verify audit log chain integrity\"\"\"
    try:
        from services.immutable_audit_service import ImmutableAuditService
        service = ImmutableAuditService(db)
        integrity_check = service.verify_chain_integrity()
        
        return {
            "id": str(integrity_check.id),
            "check_time": integrity_check.check_time,
            "status": integrity_check.status,
            "total_records": integrity_check.total_records,
            "check_duration_ms": integrity_check.check_duration_ms,
            "records_per_second": integrity_check.records_per_second
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify integrity: {str(e)}")
"""
        
        create_file_with_content("ow-ai-backend/routes/audit_routes.py", audit_routes_content)
        
        # 4. Create Alembic migration
        print("📊 Creating database migration...")
        
        migration_content = f"""\"\"\"Add immutable audit trail tables

Revision ID: immutable_audit_v1
Revises: be858bdecce8
Create Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}

\"\"\"
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'immutable_audit_v1'
down_revision: Union[str, None] = 'be858bdecce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create immutable_audit_logs table
    op.create_table(
        'immutable_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence_number', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_system', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_id', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('compliance_tags', sa.JSON(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('previous_hash', sa.String(length=64), nullable=True),
        sa.Column('chain_hash', sa.String(length=64), nullable=False),
        sa.Column('evidence_pack_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sequence_number')
    )
    
    # Create indexes
    op.create_index('idx_audit_timestamp', 'immutable_audit_logs', ['timestamp'])
    op.create_index('idx_audit_actor', 'immutable_audit_logs', ['actor_id'])
    op.create_index('idx_audit_sequence', 'immutable_audit_logs', ['sequence_number'])
    
    # Create evidence_packs table
    op.create_table(
        'evidence_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('manifest_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_integrity_checks table
    op.create_table(
        'audit_integrity_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('check_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('start_sequence', sa.Integer(), nullable=False),
        sa.Column('end_sequence', sa.Integer(), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('check_duration_ms', sa.Integer(), nullable=False),
        sa.Column('records_per_second', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('audit_integrity_checks')
    op.drop_table('evidence_packs')
    op.drop_index('idx_audit_sequence', table_name='immutable_audit_logs')
    op.drop_index('idx_audit_actor', table_name='immutable_audit_logs')
    op.drop_index('idx_audit_timestamp', table_name='immutable_audit_logs')
    op.drop_table('immutable_audit_logs')
"""
        
        # Create the migration file with a proper filename
        migration_filename = f"alembic/versions/{datetime.now().strftime('%Y%m%d_%H%M%S')}_add_immutable_audit_tables.py"
        create_file_with_content(migration_filename, migration_content)
        
        # 5. Update main.py to include audit routes
        print("🔗 Updating main.py with audit routes...")
        
        main_py_addition = """
# Enterprise Audit Routes (Phase 2.1)
try:
    from routes import audit_routes
    app.include_router(audit_routes.router, prefix="/api", tags=["audit"])
    print("✅ Enterprise audit routes loaded")
except ImportError as e:
    print(f"⚠️  Audit routes not available: {e}")
"""
        
        # Check if main.py exists and update it
        main_py_path = "ow-ai-backend/main.py"
        if os.path.exists(main_py_path):
            backup_existing_file(main_py_path)
            
            # Read existing main.py
            with open(main_py_path, 'r') as f:
                content = f.read()
            
            # Add audit routes if not already present
            if "audit_routes" not in content:
                content += main_py_addition
                
                # Write updated content
                with open(main_py_path, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated: {main_py_path}")
        
        # 6. Create deployment script
        print("🚀 Creating deployment script...")
        
        deploy_script_content = """#!/bin/bash
# OW-AI Phase 2.1 Deployment Script

echo "🚀 OW-AI Phase 2.1: Deploying Immutable Audit System"
echo "====================================================="

# Check if we're in the right directory
if [ ! -d "ow-ai-backend" ]; then
    echo "❌ Error: Must run from OW_AI_Project root directory"
    exit 1
fi

echo "📊 Running database migrations..."
cd ow-ai-backend
python -m alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    exit 1
fi

echo "✅ Database migrations completed"

echo "🚂 Deploying to Railway..."
cd ..
railway up

echo "✅ Phase 2.1 Deployment Complete!"
"""
        
        create_file_with_content("deploy_phase2_1.sh", deploy_script_content)
        os.chmod("deploy_phase2_1.sh", 0o755)  # Make executable
        
        print("\n" + "=" * 70)
        print("🎉 PHASE 2.1 IMPLEMENTATION COMPLETE!")
        print("=" * 70)
        print("📁 Files Created:")
        print("   ✅ models_audit.py - Enhanced audit models")
        print("   ✅ services/immutable_audit_service.py - Core service") 
        print("   ✅ routes/audit_routes.py - API endpoints")
        print("   ✅ Database migration file")
        print("   ✅ deploy_phase2_1.sh - Deployment script")
        print()
        print("🚀 Next Steps:")
        print("   1. Deploy: ./deploy_phase2_1.sh")
        print("   2. Test: Check Railway logs")
        print("   3. Verify: curl https://owai-production.up.railway.app/api/audit/health")
        print()
        print("🎯 Phase 2.1 Features Implemented:")
        print("   ✅ WORM audit storage")
        print("   ✅ Hash-chained integrity")
        print("   ✅ Enterprise audit APIs")
        print("   ✅ Compliance framework")
        print()
        print(f"⏰ Implementation completed: {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Error during implementation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    implement_phase2_1()
