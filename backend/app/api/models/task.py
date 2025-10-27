from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Enum as SQLEnum, JSON, Index, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base
import uuid
import enum


class TaskType(str, enum.Enum):
    PORT_SCAN = "port_scan"
    SUBDOMAIN_ENUM = "subdomain_enum"
    WEB_DISCOVERY = "web_discovery"
    VULNERABILITY_SCAN = "vulnerability_scan"
    SSL_CHECK = "ssl_check"
    DNS_ENUM = "dns_enum"
    FOFA_SEARCH = "fofa_search"
    CUSTOM = "custom"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ScanTask(Base):
    __tablename__ = "scan_tasks"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic info
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(SQLEnum(TaskType), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.NORMAL, nullable=False, index=True)

    # Target information
    target_assets = Column(ARRAY(String), server_default='{}', nullable=False)  # Asset IDs
    target_domains = Column(ARRAY(String), server_default='{}', nullable=False)
    target_ips = Column(ARRAY(String), server_default='{}', nullable=False)
    target_urls = Column(ARRAY(String), server_default='{}', nullable=False)

    # Task configuration
    config = Column(JSON, server_default='{}', nullable=False)
    scan_profile = Column(String(100), nullable=True)
    engine = Column(String(100), nullable=True)  # nmap, nuclei, xray, etc.

    # Scheduling
    schedule_type = Column(String(50), default="immediate", nullable=False)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    recurring_pattern = Column(String(255), nullable=True)  # cron expression
    max_execution_time = Column(Integer, default=3600, nullable=False)  # seconds

    # Execution details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # seconds
    worker_id = Column(String(255), nullable=True)
    celery_task_id = Column(String(255), nullable=True)

    # Results
    total_targets = Column(Integer, default=0, nullable=False)
    processed_targets = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)

    # Output
    results = Column(JSON, server_default='[]', nullable=False)
    error_messages = Column(ARRAY(String), server_default='{}', nullable=False)
    log_messages = Column(JSON, server_default='[]', nullable=False)

    # Files
    output_files = Column(ARRAY(String), server_default='{}', nullable=False)
    report_path = Column(String(500), nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    # Notifications
    notify_on_completion = Column(Boolean, default=True, nullable=False)
    notification_emails = Column(ARRAY(String), server_default='{}', nullable=False)

    # Retry logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=300, nullable=False)  # seconds

    # Parent/Child relationships
    parent_task_id = Column(UUID(as_uuid=True), nullable=True)
    child_tasks = Column(ARRAY(String), server_default='{}', nullable=False)

    # Tags and metadata
    tags = Column(ARRAY(String), server_default='{}', nullable=False)
    custom_metadata = Column(JSON, server_default='{}', nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_task_type', 'task_type'),
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        Index('idx_task_created_by', 'created_by'),
        Index('idx_task_created_at', 'created_at'),
        Index('idx_task_scheduled_at', 'scheduled_at'),
    )

    def get_duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_running(self) -> bool:
        return self.status == TaskStatus.RUNNING

    def is_completed(self) -> bool:
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]