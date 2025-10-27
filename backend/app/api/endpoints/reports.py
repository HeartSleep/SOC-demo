from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
import os

from app.core.deps import get_current_active_user, require_permission
from app.core.database import is_database_connected
from app.api.models.user import User
from app.api.models.report import Report, ReportType, ReportFormat, ReportStatus
from app.api.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportSearch,
    ReportStats, ReportSchedule
)
from app.core.celery.tasks.report_tasks import generate_report_task, scheduled_report_task
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    current_user: User = Depends(require_permission("report:read"))
):
    """List reports with optional filtering"""

    filters = {}

    if report_type:
        filters["report_type"] = report_type
    if status:
        filters["status"] = status

    # Apply visibility filters
    access_filter = {
        "$or": [
            {"created_by": current_user.username},
            {"visibility": "public"},
            {"shared_with": current_user.username}
        ]
    }

    if filters:
        filters = {"$and": [filters, access_filter]}
    else:
        filters = access_filter

    query = Report.find(filters)
    reports = await query.skip(skip).limit(limit).to_list()

    return [ReportResponse(**report.dict()) for report in reports]


@router.post("/search", response_model=List[ReportResponse])
async def search_reports(
    search_params: ReportSearch,
    current_user: User = Depends(require_permission("report:read"))
):
    """Advanced report search"""

    filters = {}

    if search_params.report_type:
        filters["report_type"] = search_params.report_type
    if search_params.status:
        filters["status"] = search_params.status
    if search_params.created_by:
        filters["created_by"] = search_params.created_by
    if search_params.tags:
        filters["tags"] = {"$in": search_params.tags}

    # Date filters
    if search_params.created_after or search_params.created_before:
        date_filter = {}
        if search_params.created_after:
            date_filter["$gte"] = search_params.created_after
        if search_params.created_before:
            date_filter["$lte"] = search_params.created_before
        filters["created_at"] = date_filter

    # Apply visibility filters
    access_filter = {
        "$or": [
            {"created_by": current_user.username},
            {"visibility": "public"},
            {"shared_with": current_user.username}
        ]
    }

    if filters:
        filters = {"$and": [filters, access_filter]}
    else:
        filters = access_filter

    query = Report.find(filters)
    reports = await query.skip(search_params.skip).limit(search_params.limit).to_list()

    return [ReportResponse(**report.dict()) for report in reports]


@router.get("/stats", response_model=ReportStats)
async def get_report_statistics(
    current_user: User = Depends(require_permission("report:read"))
):
    """Get report statistics"""

    try:
        # Apply user filter if not admin
        user_filter = {}
        if not any(perm in current_user.permissions for perm in ["report:read_all", "system:admin"]):
            user_filter = {
                "$or": [
                    {"created_by": current_user.username},
                    {"visibility": "public"},
                    {"shared_with": current_user.username}
                ]
            }

        # Count total reports
        total_reports = await Report.find(user_filter).count()

        # Count by type
        reports_by_type = {}
        for report_type in ReportType:
            count = await Report.find({**user_filter, "report_type": report_type}).count()
            reports_by_type[report_type] = count

        # Count by status
        reports_by_status = {}
        for report_status in ReportStatus:
            count = await Report.find({**user_filter, "status": report_status}).count()
            reports_by_status[report_status] = count

        # Count by format
        reports_by_format = {}
        for report_format in ReportFormat:
            count = await Report.find({**user_filter, "format": report_format}).count()
            reports_by_format[report_format] = count

        # Count recent reports (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_reports = await Report.find({**user_filter, "created_at": {"$gte": week_ago}}).count()

        # Count scheduled reports
        scheduled_reports = await Report.find({**user_filter, "is_scheduled": True}).count()

        # Calculate average generation time
        completed_reports = await Report.find({
            **user_filter,
            "status": ReportStatus.COMPLETED,
            "generation_time": {"$ne": None}
        }).to_list()

        average_generation_time = None
        if completed_reports:
            total_time = sum(r.generation_time for r in completed_reports if r.generation_time)
            average_generation_time = total_time / len(completed_reports)

        return ReportStats(
            total_reports=total_reports,
            reports_by_type=reports_by_type,
            reports_by_status=reports_by_status,
            reports_by_format=reports_by_format,
            recent_reports=recent_reports,
            scheduled_reports=scheduled_reports,
            average_generation_time=average_generation_time
        )

    except Exception as e:
        logger.error(f"Failed to get report statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report statistics"
        )


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(require_permission("report:create"))
):
    """Create and generate a new report"""

    try:
        # Create report record
        report = Report(
            **report_data.dict(),
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await report.insert()

        # Start report generation task
        task = generate_report_task.delay(
            str(report.id),
            {
                "type": report.report_type,
                "format": report.format,
                "filters": {
                    "asset_filters": report.asset_filters,
                    "vulnerability_filters": report.vulnerability_filters,
                    "date_range": report.date_range,
                    "severity_filter": report.severity_filter
                },
                "config": report.config,
                "include_assets": "assets" in report.include_sections or not report.include_sections,
                "include_vulnerabilities": "vulnerabilities" in report.include_sections or not report.include_sections,
                "include_scan_tasks": "scan_tasks" in report.include_sections,
                "auto_email": report.auto_email,
                "email_recipients": report.email_recipients,
                "email_subject": report.email_subject,
                "email_body": report.email_body
            }
        )

        logger.info(f"Report creation started: {report.title} by {current_user.username}")

        return ReportResponse(**report.dict())

    except Exception as e:
        logger.error(f"Failed to create report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report"
        )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(require_permission("report:read"))
):
    """Get report by ID"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check access permissions
    if not report.is_accessible_by(current_user.username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report"
        )

    return ReportResponse(**report.dict())


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_update: ReportUpdate,
    current_user: User = Depends(require_permission("report:update"))
):
    """Update report metadata"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check if user can update this report
    if (report.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["report:update_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this report"
        )

    try:
        # Update fields
        update_data = report_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(report, field, value)

        report.updated_by = current_user.username
        report.updated_at = datetime.utcnow()

        await report.save()

        logger.info(f"Report updated: {report.title} by {current_user.username}")

        return ReportResponse(**report.dict())

    except Exception as e:
        logger.error(f"Failed to update report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update report"
        )


@router.post("/{report_id}/regenerate")
async def regenerate_report(
    report_id: str,
    current_user: User = Depends(require_permission("report:generate"))
):
    """Regenerate an existing report"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check if user can regenerate this report
    if (report.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["report:generate_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to regenerate this report"
        )

    try:
        # Reset report status and metadata
        report.status = ReportStatus.GENERATING
        report.generated_at = None
        report.generation_time = None
        report.file_path = None
        report.file_size = None
        report.error_message = None
        report.warnings = []
        report.updated_by = current_user.username
        report.updated_at = datetime.utcnow()

        await report.save()

        # Start report generation task
        task = generate_report_task.delay(
            report_id,
            {
                "type": report.report_type,
                "format": report.format,
                "filters": {
                    "asset_filters": report.asset_filters,
                    "vulnerability_filters": report.vulnerability_filters,
                    "date_range": report.date_range,
                    "severity_filter": report.severity_filter
                },
                "config": report.config
            }
        )

        logger.info(f"Report regeneration started: {report.title} by {current_user.username}")

        return {"message": "Report regeneration started", "task_id": task.id}

    except Exception as e:
        logger.error(f"Failed to regenerate report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate report"
        )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(require_permission("report:read"))
):
    """Download report file"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check access permissions
    if not report.is_accessible_by(current_user.username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this report"
        )

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )

    # Generate filename based on report title and format
    filename = f"{report.title.replace(' ', '_')}_{report.created_at.strftime('%Y%m%d')}.{report.format.value}"

    return FileResponse(
        report.file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/{report_id}/schedule")
async def schedule_report(
    report_id: str,
    schedule_data: ReportSchedule,
    current_user: User = Depends(require_permission("report:create"))
):
    """Schedule report for recurring generation"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check if user can schedule this report
    if (report.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["report:schedule_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to schedule this report"
        )

    try:
        # Update report with scheduling information
        report.is_scheduled = True
        report.schedule_pattern = schedule_data.schedule_pattern
        report.auto_email = schedule_data.auto_email
        report.email_recipients = schedule_data.email_recipients
        report.email_subject = schedule_data.email_subject
        report.email_body = schedule_data.email_body
        report.updated_by = current_user.username
        report.updated_at = datetime.utcnow()

        # Calculate next run time based on cron pattern
        # This is a simplified implementation - you'd use a proper cron parser
        report.next_run = datetime.utcnow() + timedelta(hours=24)  # Daily by default

        await report.save()

        logger.info(f"Report scheduled: {report.title} by {current_user.username}")

        return {"message": "Report scheduled successfully", "next_run": report.next_run}

    except Exception as e:
        logger.error(f"Failed to schedule report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule report"
        )


@router.delete("/{report_id}/schedule")
async def unschedule_report(
    report_id: str,
    current_user: User = Depends(require_permission("report:update"))
):
    """Remove report scheduling"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check if user can unschedule this report
    if (report.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["report:schedule_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to unschedule this report"
        )

    try:
        report.is_scheduled = False
        report.schedule_pattern = None
        report.next_run = None
        report.updated_by = current_user.username
        report.updated_at = datetime.utcnow()

        await report.save()

        logger.info(f"Report unscheduled: {report.title} by {current_user.username}")

        return {"message": "Report scheduling removed"}

    except Exception as e:
        logger.error(f"Failed to unschedule report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unschedule report"
        )


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(require_permission("report:delete"))
):
    """Delete report"""

    report = await Report.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Check if user can delete this report
    if (report.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["report:delete_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this report"
        )

    try:
        # Delete report file if it exists
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError:
                logger.warning(f"Failed to delete report file: {report.file_path}")

        await report.delete()

        logger.info(f"Report deleted: {report.title} by {current_user.username}")

        return {"message": "Report deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete report {report_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete report"
        )