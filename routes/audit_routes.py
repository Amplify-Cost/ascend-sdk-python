"""
Enterprise Audit Routes
Provides APIs for immutable audit logs, evidence packs, and compliance reporting
"""
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
    """Health check for audit system"""
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
    """Create immutable audit log entry"""
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
    """Get audit logs with pagination"""
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
    """Verify audit log chain integrity"""
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

@router.get("/audit/export/csv")
def export_audit_logs_csv(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Export audit logs to CSV format with compliance metadata"""
    try:
        import csv
        import io
        from fastapi.responses import StreamingResponse
        from models_audit import ImmutableAuditLog

        # Build query with filters
        query = db.query(ImmutableAuditLog)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(ImmutableAuditLog.timestamp >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(ImmutableAuditLog.timestamp <= end_dt)

        if event_type:
            query = query.filter(ImmutableAuditLog.event_type == event_type)

        if actor_id:
            query = query.filter(ImmutableAuditLog.actor_id == actor_id)

        if resource_type:
            query = query.filter(ImmutableAuditLog.resource_type == resource_type)

        # Get logs ordered by sequence
        logs = query.order_by(ImmutableAuditLog.sequence_number.asc()).all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Sequence Number', 'Timestamp', 'Event Type', 'Actor ID',
            'Resource Type', 'Resource ID', 'Action', 'Risk Level',
            'Compliance Tags', 'Content Hash', 'Chain Hash',
            'Retention Until', 'Legal Hold', 'IP Address'
        ])

        # Write data rows
        for log in logs:
            import json
            compliance_tags = json.loads(log.compliance_tags) if log.compliance_tags else []
            writer.writerow([
                log.sequence_number,
                log.timestamp.isoformat(),
                log.event_type,
                log.actor_id,
                log.resource_type,
                log.resource_id,
                log.action,
                log.risk_level,
                ','.join(compliance_tags),
                log.content_hash,
                log.chain_hash,
                log.retention_until.isoformat() if log.retention_until else '',
                'Yes' if log.legal_hold else 'No',
                log.ip_address or ''
            ])

        # Prepare response
        output.seek(0)
        filename = f"audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")

@router.get("/audit/export/pdf")
def export_audit_logs_pdf(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """Export audit logs to PDF format with professional formatting and compliance badges"""
    try:
        import io
        import json
        from fastapi.responses import StreamingResponse
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.platypus import Image as RLImage
        from models_audit import ImmutableAuditLog

        # Build query with filters
        query = db.query(ImmutableAuditLog)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(ImmutableAuditLog.timestamp >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(ImmutableAuditLog.timestamp <= end_dt)

        if event_type:
            query = query.filter(ImmutableAuditLog.event_type == event_type)

        if actor_id:
            query = query.filter(ImmutableAuditLog.actor_id == actor_id)

        if resource_type:
            query = query.filter(ImmutableAuditLog.resource_type == resource_type)

        # Get logs ordered by sequence
        logs = query.order_by(ImmutableAuditLog.sequence_number.asc()).all()

        # Verify hash chain integrity for this export
        from services.immutable_audit_service import ImmutableAuditService
        service = ImmutableAuditService(db)
        integrity_status = "VERIFIED" if logs else "N/A"

        if logs:
            # Quick integrity check on exported logs
            previous_chain_hash = None
            for log in logs:
                if log.sequence_number > 1 and log.previous_hash != previous_chain_hash:
                    integrity_status = "BROKEN_CHAIN"
                    break
                previous_chain_hash = log.chain_hash

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1*inch, bottomMargin=0.75*inch)

        # Build PDF content
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("OW AI Enterprise Audit Trail Report", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Report metadata
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4b5563')
        )

        report_date = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')
        story.append(Paragraph(f"<b>Generated:</b> {report_date}", metadata_style))
        story.append(Paragraph(f"<b>Generated By:</b> {current_user.get('email', 'Unknown')}", metadata_style))
        story.append(Paragraph(f"<b>Total Records:</b> {len(logs)}", metadata_style))
        story.append(Paragraph(f"<b>Hash Chain Status:</b> {integrity_status}", metadata_style))

        if start_date:
            story.append(Paragraph(f"<b>Start Date:</b> {start_date}", metadata_style))
        if end_date:
            story.append(Paragraph(f"<b>End Date:</b> {end_date}", metadata_style))

        story.append(Spacer(1, 0.3*inch))

        # Compliance badges
        compliance_frameworks = set()
        for log in logs:
            tags = json.loads(log.compliance_tags) if log.compliance_tags else []
            compliance_frameworks.update(tags)

        if compliance_frameworks:
            badge_text = f"<b>Compliance Frameworks:</b> {', '.join(sorted(compliance_frameworks))}"
            story.append(Paragraph(badge_text, metadata_style))
            story.append(Spacer(1, 0.2*inch))

        # Data table
        if logs:
            # Table header
            table_data = [[
                'Seq#', 'Timestamp', 'Event Type', 'Actor',
                'Resource', 'Action', 'Risk', 'Compliance'
            ]]

            # Table rows
            for log in logs:
                compliance_tags = json.loads(log.compliance_tags) if log.compliance_tags else []
                table_data.append([
                    str(log.sequence_number),
                    log.timestamp.strftime('%Y-%m-%d\n%H:%M:%S'),
                    log.event_type,
                    log.actor_id[:15] + '...' if len(log.actor_id) > 15 else log.actor_id,
                    f"{log.resource_type}\n{log.resource_id[:15]}{'...' if len(log.resource_id) > 15 else ''}",
                    log.action[:20] + '...' if len(log.action) > 20 else log.action,
                    log.risk_level,
                    '\n'.join(compliance_tags[:3])  # Show first 3 tags
                ])

            # Create table with styling
            table = Table(table_data, colWidths=[
                0.5*inch, 1*inch, 0.8*inch, 1*inch,
                1.2*inch, 1.2*inch, 0.6*inch, 0.8*inch
            ])

            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                # Data rows styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(table)
            story.append(Spacer(1, 0.3*inch))
        else:
            story.append(Paragraph("<i>No audit logs found matching the specified criteria.</i>", metadata_style))

        # Footer with digital signature notice
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            alignment=1
        )
        story.append(Paragraph("This report is cryptographically secured through hash-chaining.", footer_style))
        story.append(Paragraph(f"Hash Chain Integrity: {integrity_status}", footer_style))
        story.append(Paragraph(f"Generated by OW AI Enterprise Audit System - {report_date}", footer_style))

        # Build PDF
        doc.build(story)

        # Prepare response
        buffer.seek(0)
        filename = f"audit_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export PDF: {str(e)}")
