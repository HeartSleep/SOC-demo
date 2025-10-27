from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Enum as SQLEnum, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base
import uuid
import enum


class ReportType(str, enum.Enum):
    VULNERABILITY_REPORT = "vulnerability_report"
    ASSET_INVENTORY = "asset_inventory"
    SCAN_SUMMARY = "scan_summary"
    COMPLIANCE_REPORT = "compliance_report"
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_DETAILS = "technical_details"
    REMEDIATION_PLAN = "remediation_plan"
    TREND_ANALYSIS = "trend_analysis"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(SQLEnum(ReportType), nullable=False, index=True)
    format = Column(SQLEnum(ReportFormat), default=ReportFormat.PDF, nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.GENERATING, nullable=False, index=True)

    # Scope and filters
    asset_filters = Column(JSON, server_default='{}', nullable=False)
    vulnerability_filters = Column(JSON, server_default='{}', nullable=False)
    date_range = Column(JSON, server_default='{}', nullable=False)
    severity_filter = Column(ARRAY(String), server_default='{}', nullable=False)

    # Content configuration
    include_sections = Column(ARRAY(String), server_default='{}', nullable=False)
    template = Column(String(255), nullable=True)
    custom_logo = Column(String(500), nullable=True)
    custom_branding = Column(JSON, server_default='{}', nullable=False)

    # Statistics
    total_assets = Column(Integer, default=0, nullable=False)
    total_vulnerabilities = Column(Integer, default=0, nullable=False)
    vulnerability_by_severity = Column(JSON, server_default='{}', nullable=False)
    assets_by_type = Column(JSON, server_default='{}', nullable=False)

    # Generation details
    generated_at = Column(DateTime, nullable=True, index=True)
    generation_time = Column(Float, nullable=True)  # seconds
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Access control
    visibility = Column(String(20), default="private", nullable=False)
    shared_with = Column(ARRAY(String), server_default='{}', nullable=False)
    access_permissions = Column(JSON, server_default='{}', nullable=False)

    # Scheduling
    is_scheduled = Column(Boolean, default=False, nullable=False, index=True)
    schedule_pattern = Column(String(255), nullable=True)  # cron expression
    next_run = Column(DateTime, nullable=True)

    # Version control
    version = Column(Integer, default=1, nullable=False)
    parent_report_id = Column(UUID(as_uuid=True), nullable=True)
    revision_notes = Column(Text, nullable=True)

    # Distribution
    auto_email = Column(Boolean, default=False, nullable=False)
    email_recipients = Column(ARRAY(String), server_default='{}', nullable=False)
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)

    # Configuration
    config = Column(JSON, server_default='{}', nullable=False)
    parameters = Column(JSON, server_default='{}', nullable=False)

    # Tags and metadata
    tags = Column(ARRAY(String), server_default='{}', nullable=False)
    custom_metadata = Column(JSON, server_default='{}', nullable=False)

    # Error handling
    error_message = Column(Text, nullable=True)
    warnings = Column(ARRAY(String), server_default='{}', nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_report_type', 'report_type'),
        Index('idx_report_status', 'status'),
        Index('idx_report_created_by', 'created_by'),
        Index('idx_report_created_at', 'created_at'),
        Index('idx_report_generated_at', 'generated_at'),
        Index('idx_report_is_scheduled', 'is_scheduled'),
    )

    def get_file_url(self) -> Optional[str]:
        if self.file_path:
            return f"/api/v1/reports/{self.id}/download"
        return None

    def get_size_mb(self) -> Optional[float]:
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return None

    def is_accessible_by(self, user_id: str) -> bool:
        if str(self.created_by) == user_id:
            return True
        if self.visibility == "public":
            return True
        return user_id in self.shared_with