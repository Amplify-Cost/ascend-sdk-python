"""
OW-kai Enterprise Integration Phase 4: Compliance Export Routes

Enterprise-grade REST API for compliance exports:
- Multi-framework support (SOX, PCI-DSS, HIPAA, GDPR, SOC2, NIST, ISO)
- Async export job processing
- Signed downloads with audit trails
- Scheduled report management
- Export status monitoring

Security:
- Role-based access control
- Organization isolation
- Audit logging for all exports
- SHA-256 file verification
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from database import get_db
from dependencies import get_current_user, get_organization_filter
from models_compliance_export import (
    ComplianceFramework,
    ExportFormat,
    ExportStatus,
    ReportType,
    ComplianceExportRequest,
    ComplianceExportResponse,
    ComplianceScheduleCreate,
    ComplianceScheduleUpdate,
    ComplianceScheduleResponse,
    ComplianceDownloadResponse,
    get_framework_config,
    get_supported_frameworks,
    FRAMEWORK_REPORT_MAPPINGS,
)
from services.compliance_export_service import ComplianceExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance-export", tags=["Compliance Export"])


# ============================================
# Framework Information (Public Reference)
# ============================================

@router.get("/frameworks")
async def get_frameworks():
    """
    Get all supported compliance frameworks with their configurations.

    Returns framework details including:
    - Supported report types
    - Default retention periods
    - Data classification requirements
    """
    return {
        "frameworks": get_supported_frameworks(),
        "export_formats": [f.value for f in ExportFormat],
        "report_types": [r.value for r in ReportType],
    }


@router.get("/frameworks/{framework}")
async def get_framework_details(framework: ComplianceFramework):
    """
    Get detailed configuration for a specific compliance framework.
    """
    config = get_framework_config(framework)
    return {
        "framework": framework.value,
        "display_name": framework.name.replace("_", " ").title(),
        "supported_reports": [r.value for r in config["supported_reports"]],
        "default_retention_days": config["default_retention_days"],
        "required_fields": config["required_fields"],
        "data_classification": config["data_classification"].value,
    }


# ============================================
# Export Job Management
# ============================================

@router.post("/exports", response_model=ComplianceExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    request: ComplianceExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new compliance export job.

    The export will be processed asynchronously. Poll the status endpoint
    to check progress and retrieve the download URL when complete.

    Required role: admin or compliance_officer
    """
    # Check permissions - compliance exports require elevated access
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compliance exports require admin, compliance_officer, or auditor role"
        )

    service = ComplianceExportService(db)

    try:
        job = service.create_export_job(
            request=request,
            organization_id=current_user["organization_id"],
            user_id=current_user["user_id"],
        )

        # Queue background processing
        background_tasks.add_task(
            _process_export_background,
            job.id,
            current_user["organization_id"],
        )

        logger.info(
            f"Created compliance export {job.id}: {request.framework.value}/{request.report_type.value} "
            f"by user {current_user['user_id']}"
        )

        return ComplianceExportResponse(
            id=job.id,
            framework=job.framework,
            report_type=job.report_type,
            export_format=job.export_format,
            start_date=job.start_date,
            end_date=job.end_date,
            status=job.status,
            progress_percent=job.progress_percent,
            error_message=job.error_message,
            file_size_bytes=job.file_size_bytes,
            record_count=job.record_count,
            data_classification=job.data_classification,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            expires_at=job.expires_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/exports", response_model=List[ComplianceExportResponse])
async def list_exports(
    framework: Optional[ComplianceFramework] = None,
    status_filter: Optional[ExportStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List compliance export jobs for the organization.

    Supports filtering by framework and status.
    """
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view compliance exports"
        )

    service = ComplianceExportService(db)
    jobs, total = service.list_export_jobs(
        organization_id=current_user["organization_id"],
        framework=framework,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [
        ComplianceExportResponse(
            id=job.id,
            framework=job.framework,
            report_type=job.report_type,
            export_format=job.export_format,
            start_date=job.start_date,
            end_date=job.end_date,
            status=job.status,
            progress_percent=job.progress_percent,
            error_message=job.error_message,
            file_size_bytes=job.file_size_bytes,
            record_count=job.record_count,
            data_classification=job.data_classification,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            expires_at=job.expires_at,
            download_url=f"/api/compliance-export/exports/{job.id}/download" if job.status == ExportStatus.COMPLETED else None,
        )
        for job in jobs
    ]


@router.get("/exports/{job_id}", response_model=ComplianceExportResponse)
async def get_export(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get status and details of a specific export job.
    """
    service = ComplianceExportService(db)
    job = service.get_export_job(job_id, current_user["organization_id"])

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job {job_id} not found"
        )

    return ComplianceExportResponse(
        id=job.id,
        framework=job.framework,
        report_type=job.report_type,
        export_format=job.export_format,
        start_date=job.start_date,
        end_date=job.end_date,
        status=job.status,
        progress_percent=job.progress_percent,
        error_message=job.error_message,
        file_size_bytes=job.file_size_bytes,
        record_count=job.record_count,
        data_classification=job.data_classification,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        expires_at=job.expires_at,
        download_url=f"/api/compliance-export/exports/{job.id}/download" if job.status == ExportStatus.COMPLETED else None,
    )


@router.get("/exports/{job_id}/download")
async def download_export(
    job_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download a completed export file.

    Returns the export file with appropriate content type.
    All downloads are logged for audit purposes.
    """
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to download compliance exports"
        )

    service = ComplianceExportService(db)
    job = service.get_export_job(job_id, current_user["organization_id"])

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job {job_id} not found"
        )

    if job.status != ExportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready for download. Status: {job.status.value}"
        )

    if job.expires_at and job.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export has expired and is no longer available"
        )

    # Log the download
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    service.log_download(
        job_id=job_id,
        organization_id=current_user["organization_id"],
        user_id=current_user["user_id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )

    logger.info(f"Export {job_id} downloaded by user {current_user['user_id']}")

    # Generate content (in production, would read from file storage)
    # For now, regenerate the content
    content = _generate_sample_content(job)

    # Determine content type
    content_types = {
        ExportFormat.JSON: "application/json",
        ExportFormat.CSV: "text/csv",
        ExportFormat.XML: "application/xml",
        ExportFormat.PDF: "application/pdf",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    content_type = content_types.get(job.export_format, "application/octet-stream")
    filename = f"{job.framework.value}_{job.report_type.value}_{job.id}.{job.export_format.value}"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Hash": job.file_hash or "",
            "X-Record-Count": str(job.record_count or 0),
        }
    )


@router.get("/exports/{job_id}/downloads", response_model=List[ComplianceDownloadResponse])
async def get_export_downloads(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get download audit trail for an export.

    Returns list of all downloads with user info, timestamps, and IP addresses.
    """
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view download history"
        )

    service = ComplianceExportService(db)
    downloads = service.get_download_history(job_id, current_user["organization_id"])

    return [
        ComplianceDownloadResponse(
            id=d.id,
            export_job_id=d.export_job_id,
            downloaded_by=d.downloaded_by,
            downloaded_at=d.downloaded_at,
            ip_address=d.ip_address,
            verified_hash=d.verified_hash,
        )
        for d in downloads
    ]


@router.post("/exports/{job_id}/verify")
async def verify_export_hash(
    job_id: int,
    hash_value: str = Query(..., description="SHA-256 hash to verify"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Verify the integrity of a downloaded export using its SHA-256 hash.
    """
    service = ComplianceExportService(db)
    is_valid = service.verify_export_hash(job_id, hash_value)

    return {
        "job_id": job_id,
        "provided_hash": hash_value,
        "is_valid": is_valid,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================
# Scheduled Reports
# ============================================

@router.post("/schedules", response_model=ComplianceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ComplianceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a scheduled compliance report.

    Reports will be automatically generated according to the cron schedule.
    Results can be emailed to recipients or sent to a webhook.

    Required role: admin or compliance_officer
    """
    if current_user.get("role") not in ["admin", "compliance_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and compliance officers can create scheduled reports"
        )

    service = ComplianceExportService(db)

    try:
        created = service.create_schedule(
            schedule_data=schedule.model_dump(),
            organization_id=current_user["organization_id"],
            user_id=current_user["user_id"],
        )

        logger.info(f"Created compliance schedule {created.id} by user {current_user['user_id']}")

        return ComplianceScheduleResponse(
            id=created.id,
            name=created.name,
            description=created.description,
            framework=created.framework,
            report_type=created.report_type,
            export_format=created.export_format,
            cron_expression=created.cron_expression,
            timezone=created.timezone,
            is_active=created.is_active,
            email_recipients=created.email_recipients,
            webhook_url=created.webhook_url,
            retention_days=created.retention_days,
            created_at=created.created_at,
            last_run_at=created.last_run_at,
            next_run_at=created.next_run_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/schedules", response_model=List[ComplianceScheduleResponse])
async def list_schedules(
    active_only: bool = Query(True, description="Only return active schedules"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List scheduled compliance reports for the organization.
    """
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view schedules"
        )

    service = ComplianceExportService(db)
    schedules = service.list_schedules(
        organization_id=current_user["organization_id"],
        active_only=active_only,
    )

    return [
        ComplianceScheduleResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            framework=s.framework,
            report_type=s.report_type,
            export_format=s.export_format,
            cron_expression=s.cron_expression,
            timezone=s.timezone,
            is_active=s.is_active,
            email_recipients=s.email_recipients,
            webhook_url=s.webhook_url,
            retention_days=s.retention_days,
            created_at=s.created_at,
            last_run_at=s.last_run_at,
            next_run_at=s.next_run_at,
        )
        for s in schedules
    ]


@router.get("/schedules/{schedule_id}", response_model=ComplianceScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific scheduled report.
    """
    service = ComplianceExportService(db)
    schedules = service.list_schedules(
        organization_id=current_user["organization_id"],
        active_only=False,
    )

    schedule = next((s for s in schedules if s.id == schedule_id), None)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    return ComplianceScheduleResponse(
        id=schedule.id,
        name=schedule.name,
        description=schedule.description,
        framework=schedule.framework,
        report_type=schedule.report_type,
        export_format=schedule.export_format,
        cron_expression=schedule.cron_expression,
        timezone=schedule.timezone,
        is_active=schedule.is_active,
        email_recipients=schedule.email_recipients,
        webhook_url=schedule.webhook_url,
        retention_days=schedule.retention_days,
        created_at=schedule.created_at,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
    )


@router.put("/schedules/{schedule_id}", response_model=ComplianceScheduleResponse)
async def update_schedule(
    schedule_id: int,
    updates: ComplianceScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a scheduled compliance report.

    Required role: admin or compliance_officer
    """
    if current_user.get("role") not in ["admin", "compliance_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and compliance officers can update schedules"
        )

    service = ComplianceExportService(db)
    updated = service.update_schedule(
        schedule_id=schedule_id,
        organization_id=current_user["organization_id"],
        updates=updates.model_dump(exclude_unset=True),
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    logger.info(f"Updated compliance schedule {schedule_id} by user {current_user['user_id']}")

    return ComplianceScheduleResponse(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        framework=updated.framework,
        report_type=updated.report_type,
        export_format=updated.export_format,
        cron_expression=updated.cron_expression,
        timezone=updated.timezone,
        is_active=updated.is_active,
        email_recipients=updated.email_recipients,
        webhook_url=updated.webhook_url,
        retention_days=updated.retention_days,
        created_at=updated.created_at,
        last_run_at=updated.last_run_at,
        next_run_at=updated.next_run_at,
    )


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a scheduled compliance report.

    Required role: admin or compliance_officer
    """
    if current_user.get("role") not in ["admin", "compliance_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and compliance officers can delete schedules"
        )

    service = ComplianceExportService(db)
    deleted = service.delete_schedule(schedule_id, current_user["organization_id"])

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )

    logger.info(f"Deleted compliance schedule {schedule_id} by user {current_user['user_id']}")


# ============================================
# Quick Export Endpoints
# ============================================

@router.post("/quick-export/{framework}/{report_type}")
async def quick_export(
    framework: ComplianceFramework,
    report_type: ReportType,
    background_tasks: BackgroundTasks,
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    export_format: ExportFormat = Query(ExportFormat.JSON),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Quick export with sensible defaults.

    Creates an export for the last N days with default settings.
    """
    if current_user.get("role") not in ["admin", "compliance_officer", "auditor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for compliance exports"
        )

    from datetime import timedelta

    request = ComplianceExportRequest(
        framework=framework,
        report_type=report_type,
        export_format=export_format,
        start_date=datetime.now(timezone.utc) - timedelta(days=days),
        end_date=datetime.now(timezone.utc),
        include_pii=False,
    )

    service = ComplianceExportService(db)

    try:
        job = service.create_export_job(
            request=request,
            organization_id=current_user["organization_id"],
            user_id=current_user["user_id"],
        )

        background_tasks.add_task(
            _process_export_background,
            job.id,
            current_user["organization_id"],
        )

        return {
            "job_id": job.id,
            "status": job.status.value,
            "framework": framework.value,
            "report_type": report_type.value,
            "period_days": days,
            "status_url": f"/api/compliance-export/exports/{job.id}",
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================
# Metrics and Statistics
# ============================================

@router.get("/metrics")
async def get_export_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get compliance export metrics and statistics.
    """
    service = ComplianceExportService(db)

    # Get all jobs for metrics
    jobs, total = service.list_export_jobs(
        organization_id=current_user["organization_id"],
        limit=1000,
    )

    # Calculate statistics
    by_framework = {}
    by_status = {}
    total_records = 0
    total_size = 0

    for job in jobs:
        framework = job.framework.value
        status_val = job.status.value

        by_framework[framework] = by_framework.get(framework, 0) + 1
        by_status[status_val] = by_status.get(status_val, 0) + 1

        if job.record_count:
            total_records += job.record_count
        if job.file_size_bytes:
            total_size += job.file_size_bytes

    return {
        "total_exports": total,
        "by_framework": by_framework,
        "by_status": by_status,
        "total_records_exported": total_records,
        "total_export_size_bytes": total_size,
        "supported_frameworks": [f.value for f in ComplianceFramework],
        "supported_formats": [f.value for f in ExportFormat],
    }


# ============================================
# Helper Functions
# ============================================

async def _process_export_background(job_id: int, organization_id: int):
    """Background task to process export job"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        service = ComplianceExportService(db)
        await service.process_export_job(job_id)
    except Exception as e:
        logger.error(f"Background export processing failed for job {job_id}: {e}")
        service.update_job_status(job_id, ExportStatus.FAILED, error=str(e))
    finally:
        db.close()


def _generate_sample_content(job) -> bytes:
    """Generate sample content for export (placeholder)"""
    import json

    content = {
        "export_info": {
            "job_id": job.id,
            "framework": job.framework.value,
            "report_type": job.report_type.value,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "record_count": job.record_count or 0,
        },
        "records": [],
    }

    if job.export_format == ExportFormat.JSON:
        return json.dumps(content, indent=2).encode('utf-8')
    elif job.export_format == ExportFormat.CSV:
        return b"id,timestamp,event_type,details\n"
    elif job.export_format == ExportFormat.XML:
        return b'<?xml version="1.0" encoding="UTF-8"?><export></export>'
    else:
        return json.dumps(content).encode('utf-8')
