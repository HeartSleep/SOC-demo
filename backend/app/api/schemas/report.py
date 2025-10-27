from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.api.models.report import ReportType, ReportFormat, ReportStatus


class ReportBase(BaseModel):
    title: str
    description: Optional[str] = None
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF


class ReportCreate(ReportBase):
    asset_filters: Dict[str, Any] = {}
    vulnerability_filters: Dict[str, Any] = {}
    date_range: Dict[str, datetime] = {}
    severity_filter: List[str] = []
    include_sections: List[str] = []
    template: Optional[str] = None
    custom_logo: Optional[str] = None
    custom_branding: Dict[str, Any] = {}
    config: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
    auto_email: bool = False
    email_recipients: List[str] = []
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    tags: List[str] = []


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    shared_with: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ReportResponse(ReportBase):
    id: str
    status: ReportStatus
    asset_filters: Dict[str, Any]
    vulnerability_filters: Dict[str, Any]
    date_range: Dict[str, datetime]
    severity_filter: List[str]
    include_sections: List[str]
    template: Optional[str]
    custom_logo: Optional[str]
    custom_branding: Dict[str, Any]
    total_assets: int
    total_vulnerabilities: int
    vulnerability_by_severity: Dict[str, int]
    assets_by_type: Dict[str, int]
    generated_at: Optional[datetime]
    generation_time: Optional[float]
    file_path: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str]
    visibility: str
    shared_with: List[str]
    access_permissions: Dict[str, List[str]]
    is_scheduled: bool
    schedule_pattern: Optional[str]
    next_run: Optional[datetime]
    version: int
    parent_report_id: Optional[str]
    revision_notes: Optional[str]
    auto_email: bool
    email_recipients: List[str]
    email_subject: Optional[str]
    email_body: Optional[str]
    config: Dict[str, Any]
    parameters: Dict[str, Any]
    tags: List[str]
    metadata: Dict[str, Any]
    error_message: Optional[str]
    warnings: List[str]

    class Config:
        from_attributes = True


class ReportSearch(BaseModel):
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    created_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    tags: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100


class ReportStats(BaseModel):
    total_reports: int
    reports_by_type: Dict[ReportType, int]
    reports_by_status: Dict[ReportStatus, int]
    reports_by_format: Dict[ReportFormat, int]
    recent_reports: int
    scheduled_reports: int
    average_generation_time: Optional[float]


class ReportSchedule(BaseModel):
    schedule_pattern: str  # cron expression
    auto_email: bool = False
    email_recipients: List[str] = []
    email_subject: Optional[str] = None
    email_body: Optional[str] = None