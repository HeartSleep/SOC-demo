from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.api.models.task import TaskType, TaskStatus, TaskPriority


class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL


class TaskCreate(TaskBase):
    target_assets: List[str] = []
    target_domains: List[str] = []
    target_ips: List[str] = []
    target_urls: List[str] = []
    config: Dict[str, Any] = {}
    scan_profile: Optional[str] = None
    engine: Optional[str] = None
    schedule_type: str = "immediate"
    scheduled_at: Optional[datetime] = None
    recurring_pattern: Optional[str] = None
    max_execution_time: int = 3600
    tags: List[str] = []


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TaskResponse(TaskBase):
    id: str
    status: TaskStatus
    target_assets: List[str]
    target_domains: List[str]
    target_ips: List[str]
    target_urls: List[str]
    config: Dict[str, Any]
    scan_profile: Optional[str]
    engine: Optional[str]
    schedule_type: str
    scheduled_at: Optional[datetime]
    recurring_pattern: Optional[str]
    max_execution_time: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_time: Optional[float]
    worker_id: Optional[str]
    celery_task_id: Optional[str]
    total_targets: int
    processed_targets: int
    success_count: int
    error_count: int
    results: List[Dict[str, Any]]
    error_messages: List[str]
    log_messages: List[Dict[str, Any]]
    output_files: List[str]
    report_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str]
    retry_count: int
    max_retries: int
    retry_delay: int
    parent_task_id: Optional[str]
    child_tasks: List[str]
    tags: List[str]
    metadata: Dict[str, Any]

    class Config:
        from_attributes = True


class TaskSearch(BaseModel):
    task_type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    created_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    tags: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100


class TaskStats(BaseModel):
    total_tasks: int
    tasks_by_type: Dict[TaskType, int]
    tasks_by_status: Dict[TaskStatus, int]
    tasks_by_priority: Dict[TaskPriority, int]
    recent_tasks: int
    running_tasks: int
    failed_tasks: int
    average_execution_time: Optional[float]