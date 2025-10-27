from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel

from app.core.deps import get_current_active_user, require_permission
from app.core.database import is_database_connected
from app.api.models.user import User
from app.api.models.task import ScanTask, TaskType, TaskStatus, TaskPriority
from app.api.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskSearch, TaskStats
)
from app.core.celery.tasks.scan_tasks import port_scan_task, subdomain_enumeration_task
from app.core.celery.tasks.vulnerability_tasks import vulnerability_scan_task
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class BulkTaskRequest(BaseModel):
    ids: List[str]


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_type: Optional[TaskType] = None,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    current_user: User = Depends(require_permission("task:read"))
):
    """List tasks with optional filtering"""

    # Demo mode - return mock tasks
    if not is_database_connected():
        current_time = datetime.utcnow()
        demo_tasks = [
            {
                "id": "demo_task_1",
                "name": "Network Port Scan",
                "description": "Scan for open ports on target network",
                "task_type": "port_scan",
                "priority": "high",
                "status": "completed",
                "target_assets": ["demo_asset_1"],
                "target_domains": ["example.com"],
                "target_ips": ["192.168.1.100"],
                "target_urls": [],
                "config": {"port_range": "1-1000", "scan_type": "tcp", "timeout": 10},
                "scan_profile": "fast",
                "engine": "nmap",
                "schedule_type": "immediate",
                "scheduled_at": None,
                "recurring_pattern": None,
                "max_execution_time": 3600,
                "started_at": current_time - timedelta(minutes=30),
                "completed_at": current_time - timedelta(minutes=25),
                "execution_time": 300.0,
                "worker_id": "worker-1",
                "celery_task_id": "celery-task-1",
                "total_targets": 1,
                "processed_targets": 1,
                "success_count": 1,
                "error_count": 0,
                "results": [
                    {
                        "target": "192.168.1.100",
                        "open_ports": [22, 80, 443],
                        "services": {
                            "22": "ssh",
                            "80": "http",
                            "443": "https"
                        }
                    }
                ],
                "error_messages": [],
                "log_messages": [
                    {"level": "info", "message": "Scan started", "timestamp": (current_time - timedelta(minutes=30)).isoformat()},
                    {"level": "info", "message": "Scan completed", "timestamp": (current_time - timedelta(minutes=25)).isoformat()}
                ],
                "output_files": [],
                "report_path": None,
                "created_at": current_time - timedelta(minutes=35),
                "updated_at": current_time - timedelta(minutes=25),
                "created_by": current_user.username,
                "updated_by": current_user.username,
                "retry_count": 0,
                "max_retries": 3,
                "retry_delay": 60,
                "parent_task_id": None,
                "child_tasks": [],
                "tags": ["security", "network"],
                "metadata": {"source": "demo_data", "version": "1.0"}
            },
            {
                "id": "demo_task_2",
                "name": "Subdomain Discovery",
                "description": "Enumerate subdomains for target domain",
                "task_type": "subdomain_enum",
                "priority": "normal",
                "status": "running",
                "target_assets": ["demo_asset_2"],
                "target_domains": ["example.com"],
                "target_ips": [],
                "target_urls": [],
                "config": {"wordlist": "common.txt", "dns_resolvers": ["8.8.8.8", "1.1.1.1"]},
                "scan_profile": "comprehensive",
                "engine": "subfinder",
                "schedule_type": "immediate",
                "scheduled_at": None,
                "recurring_pattern": None,
                "max_execution_time": 7200,
                "started_at": current_time - timedelta(minutes=10),
                "completed_at": None,
                "execution_time": None,
                "worker_id": "worker-2",
                "celery_task_id": "celery-task-2",
                "total_targets": 1,
                "processed_targets": 0,
                "success_count": 0,
                "error_count": 0,
                "results": [],
                "error_messages": [],
                "log_messages": [
                    {"level": "info", "message": "Subdomain enumeration started", "timestamp": (current_time - timedelta(minutes=10)).isoformat()},
                    {"level": "info", "message": "Found 15 subdomains so far", "timestamp": (current_time - timedelta(minutes=5)).isoformat()}
                ],
                "output_files": [],
                "report_path": None,
                "created_at": current_time - timedelta(minutes=15),
                "updated_at": current_time - timedelta(minutes=5),
                "created_by": current_user.username,
                "updated_by": current_user.username,
                "retry_count": 0,
                "max_retries": 3,
                "retry_delay": 60,
                "parent_task_id": None,
                "child_tasks": [],
                "tags": ["subdomain", "reconnaissance"],
                "metadata": {"source": "demo_data", "version": "1.0"}
            },
            {
                "id": "demo_task_3",
                "name": "Vulnerability Assessment",
                "description": "Automated vulnerability scan on web application",
                "task_type": "vulnerability_scan",
                "priority": "critical",
                "status": "pending",
                "target_assets": ["demo_asset_1"],
                "target_domains": [],
                "target_ips": [],
                "target_urls": ["https://web-server-01.example.com"],
                "config": {"scan_depth": "deep", "check_ssl": True, "include_exploits": False},
                "scan_profile": "web_application",
                "engine": "nuclei",
                "schedule_type": "scheduled",
                "scheduled_at": current_time + timedelta(hours=2),
                "recurring_pattern": "daily",
                "max_execution_time": 10800,
                "started_at": None,
                "completed_at": None,
                "execution_time": None,
                "worker_id": None,
                "celery_task_id": None,
                "total_targets": 1,
                "processed_targets": 0,
                "success_count": 0,
                "error_count": 0,
                "results": [],
                "error_messages": [],
                "log_messages": [],
                "output_files": [],
                "report_path": None,
                "created_at": current_time - timedelta(hours=1),
                "updated_at": current_time - timedelta(hours=1),
                "created_by": "admin",
                "updated_by": None,
                "retry_count": 0,
                "max_retries": 2,
                "retry_delay": 120,
                "parent_task_id": None,
                "child_tasks": [],
                "tags": ["vulnerability", "web", "automated"],
                "metadata": {"source": "demo_data", "version": "1.0", "priority_escalation": True}
            }
        ]

        # Apply basic filtering
        filtered_tasks = demo_tasks
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t["task_type"] == task_type]
        if status:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]

        # Apply user filtering unless admin
        if not any(perm in current_user.permissions for perm in ["task:read_all", "admin:*"]):
            filtered_tasks = [t for t in filtered_tasks if t["created_by"] == current_user.username]

        # Apply pagination
        start = skip
        end = skip + limit
        paginated_tasks = filtered_tasks[start:end]

        logger.info(f"Demo mode: returning {len(paginated_tasks)} mock tasks")
        return {
            "items": [TaskResponse(**task) for task in paginated_tasks],
            "total": len(filtered_tasks),
            "page": skip // limit + 1,
            "size": limit,
            "pages": (len(filtered_tasks) + limit - 1) // limit
        }

    filters = {}

    if task_type:
        filters["task_type"] = task_type
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority

    # Users can only see their own tasks unless they have admin privileges
    if not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"]):
        filters["created_by"] = current_user.username

    query = ScanTask.find(filters)
    tasks = await query.skip(skip).limit(limit).to_list()
    total = await ScanTask.find(filters).count()

    return {
        "items": [TaskResponse(**task.dict()) for task in tasks],
        "total": total,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/search", response_model=List[TaskResponse])
async def search_tasks(
    search_params: TaskSearch,
    current_user: User = Depends(require_permission("task:read"))
):
    """Advanced task search"""

    filters = {}

    if search_params.task_type:
        filters["task_type"] = search_params.task_type
    if search_params.status:
        filters["status"] = search_params.status
    if search_params.priority:
        filters["priority"] = search_params.priority
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

    # Apply user restrictions
    if not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"]):
        filters["created_by"] = current_user.username

    query = ScanTask.find(filters)
    tasks = await query.skip(search_params.skip).limit(search_params.limit).to_list()

    return [TaskResponse(**task.dict()) for task in tasks]


@router.get("/stats", response_model=TaskStats)
async def get_task_statistics(
    current_user: User = Depends(require_permission("task:read"))
):
    """Get task statistics"""

    # Demo mode - return mock stats
    if not is_database_connected():
        demo_stats = {
            "total_tasks": 3,
            "tasks_by_type": {
                "port_scan": 1,
                "subdomain_enum": 1,
                "vulnerability_scan": 1,
                "content_discovery": 0,
                "service_enumeration": 0,
                "web_screenshot": 0,
                "certificate_transparency": 0,
                "dns_enumeration": 0,
                "technology_detection": 0,
                "ssl_tls_scan": 0,
                "email_enumeration": 0,
                "osint_gathering": 0,
                "custom": 0
            },
            "tasks_by_status": {
                "pending": 1,
                "running": 1,
                "completed": 1,
                "failed": 0,
                "cancelled": 0
            },
            "tasks_by_priority": {
                "low": 0,
                "normal": 1,
                "high": 1,
                "urgent": 1
            },
            "recent_tasks": 3,
            "running_tasks": 1,
            "failed_tasks": 0,
            "average_execution_time": 300.0
        }

        logger.info("Demo mode: returning mock task statistics")
        return TaskStats(**demo_stats)

    try:
        # Apply user filter if not admin
        user_filter = {}
        if not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"]):
            user_filter = {"created_by": current_user.username}

        # Count total tasks
        total_tasks = await ScanTask.find(user_filter).count()

        # Count by type
        tasks_by_type = {}
        for task_type in TaskType:
            count = await ScanTask.find({**user_filter, "task_type": task_type}).count()
            tasks_by_type[task_type] = count

        # Count by status
        tasks_by_status = {}
        for task_status in TaskStatus:
            count = await ScanTask.find({**user_filter, "status": task_status}).count()
            tasks_by_status[task_status] = count

        # Count by priority
        tasks_by_priority = {}
        for task_priority in TaskPriority:
            count = await ScanTask.find({**user_filter, "priority": task_priority}).count()
            tasks_by_priority[task_priority] = count

        # Count recent tasks (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_tasks = await ScanTask.find({**user_filter, "created_at": {"$gte": week_ago}}).count()

        # Count running and failed tasks
        running_tasks = await ScanTask.find({**user_filter, "status": TaskStatus.RUNNING}).count()
        failed_tasks = await ScanTask.find({**user_filter, "status": TaskStatus.FAILED}).count()

        # Calculate average execution time
        completed_tasks = await ScanTask.find({
            **user_filter,
            "status": TaskStatus.COMPLETED,
            "execution_time": {"$ne": None}
        }).to_list()

        average_execution_time = None
        if completed_tasks:
            total_time = sum(task.execution_time for task in completed_tasks if task.execution_time)
            average_execution_time = total_time / len(completed_tasks) if completed_tasks else None

        return TaskStats(
            total_tasks=total_tasks,
            tasks_by_type=tasks_by_type,
            tasks_by_status=tasks_by_status,
            tasks_by_priority=tasks_by_priority,
            recent_tasks=recent_tasks,
            running_tasks=running_tasks,
            failed_tasks=failed_tasks,
            average_execution_time=average_execution_time
        )

    except Exception as e:
        logger.error(f"Failed to get task statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task statistics"
        )


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(require_permission("task:create"))
):
    """Create and optionally execute a new task"""

    try:
        # Create task record
        task = ScanTask(
            **task_data.dict(),
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await task.insert()

        # Execute task immediately if not scheduled
        if task.schedule_type == "immediate":
            await execute_task(task)

        logger.info(f"Task created: {task.name} by {current_user.username}")

        return TaskResponse(**task.dict())

    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:read"))
):
    """Get task by ID"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can access this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )

    return TaskResponse(**task.dict())


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: User = Depends(require_permission("task:update"))
):
    """Update task"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can update this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:update_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    try:
        # Update fields
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(task, field, value)

        task.updated_by = current_user.username
        task.updated_at = datetime.utcnow()

        await task.save()

        logger.info(f"Task updated: {task.name} by {current_user.username}")

        return TaskResponse(**task.dict())

    except Exception as e:
        logger.error(f"Failed to update task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update task"
        )


@router.post("/{task_id}/execute")
async def execute_task_endpoint(
    task_id: str,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Execute a task"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can execute this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:execute_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to execute this task"
        )

    # Check if task is already running
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already running"
        )

    try:
        await execute_task(task)

        logger.info(f"Task execution started: {task.name} by {current_user.username}")

        return {"message": "Task execution started", "task_id": task_id}

    except Exception as e:
        logger.error(f"Failed to execute task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute task"
        )


@router.post("/{task_id}/start")
async def start_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Start a task (alias for execute)"""
    return await execute_task_endpoint(task_id, current_user)


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Stop a task (alias for cancel)"""
    return await cancel_task(task_id, current_user)


@router.post("/{task_id}/restart")
async def restart_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Restart a failed or stopped task"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can restart this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:execute_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to restart this task"
        )

    # Check if task can be restarted
    if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task can only be restarted if it's failed or cancelled"
        )

    try:
        # Reset task status and clear previous results
        task.status = TaskStatus.PENDING
        task.started_at = None
        task.completed_at = None
        task.execution_time = None
        task.celery_task_id = None
        task.processed_targets = 0
        task.success_count = 0
        task.error_count = 0
        task.results = []
        task.error_messages = []
        task.updated_by = current_user.username
        task.updated_at = datetime.utcnow()

        await task.save()

        # Execute the task
        await execute_task(task)

        logger.info(f"Task restarted: {task.name} by {current_user.username}")

        return {"message": "Task restarted successfully", "task_id": task_id}

    except Exception as e:
        logger.error(f"Failed to restart task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart task"
        )


@router.post("/bulk-stop")
async def bulk_stop_tasks(
    request_data: BulkTaskRequest,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Bulk stop multiple tasks"""

    stopped_tasks = []
    failed_tasks = []

    for task_id in request_data.ids:
        try:
            task = await ScanTask.get(task_id)
            if not task:
                failed_tasks.append({"task_id": task_id, "error": "Task not found"})
                continue

            # Check permissions
            if (task.created_by != current_user.username and
                not any(perm in current_user.permissions for perm in ["task:execute_all", "system:admin"])):
                failed_tasks.append({"task_id": task_id, "error": "Not authorized"})
                continue

            # Check if task is running
            if task.status != TaskStatus.RUNNING:
                failed_tasks.append({"task_id": task_id, "error": "Task is not running"})
                continue

            # Cancel Celery task
            if task.celery_task_id:
                from app.core.celery import celery_app
                celery_app.control.revoke(task.celery_task_id, terminate=True)

            # Update task status
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            task.updated_by = current_user.username
            task.updated_at = datetime.utcnow()

            await task.save()
            stopped_tasks.append(task_id)

        except Exception as e:
            failed_tasks.append({"task_id": task_id, "error": str(e)})

    logger.info(f"Bulk stop completed by {current_user.username}: {len(stopped_tasks)} stopped, {len(failed_tasks)} failed")

    return {
        "message": f"Stopped {len(stopped_tasks)} tasks",
        "stopped_tasks": stopped_tasks,
        "failed_tasks": failed_tasks
    }


@router.delete("/bulk")
async def bulk_delete_tasks(
    request_data: BulkTaskRequest,
    current_user: User = Depends(require_permission("task:delete"))
):
    """Bulk delete multiple tasks"""

    deleted_tasks = []
    failed_tasks = []

    for task_id in request_data.ids:
        try:
            task = await ScanTask.get(task_id)
            if not task:
                failed_tasks.append({"task_id": task_id, "error": "Task not found"})
                continue

            # Check permissions
            if (task.created_by != current_user.username and
                not any(perm in current_user.permissions for perm in ["task:delete_all", "system:admin"])):
                failed_tasks.append({"task_id": task_id, "error": "Not authorized"})
                continue

            # Don't allow deleting running tasks
            if task.status == TaskStatus.RUNNING:
                failed_tasks.append({"task_id": task_id, "error": "Cannot delete running task"})
                continue

            await task.delete()
            deleted_tasks.append(task_id)

        except Exception as e:
            failed_tasks.append({"task_id": task_id, "error": str(e)})

    logger.info(f"Bulk delete completed by {current_user.username}: {len(deleted_tasks)} deleted, {len(failed_tasks)} failed")

    return {
        "message": f"Deleted {len(deleted_tasks)} tasks",
        "deleted_tasks": deleted_tasks,
        "failed_tasks": failed_tasks
    }


@router.post("/{task_id}/clone")
async def clone_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:create"))
):
    """Clone an existing task"""

    original_task = await ScanTask.get(task_id)
    if not original_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can access the original task
    if (original_task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to clone this task"
        )

    try:
        # Create new task with copied data
        cloned_task = ScanTask(
            name=f"{original_task.name} (Copy)",
            description=original_task.description,
            task_type=original_task.task_type,
            priority=original_task.priority,
            target_assets=original_task.target_assets,
            target_domains=original_task.target_domains,
            target_ips=original_task.target_ips,
            target_urls=original_task.target_urls,
            config=original_task.config,
            scan_profile=original_task.scan_profile,
            engine=original_task.engine,
            schedule_type="immediate",
            scheduled_at=None,
            recurring_pattern=None,
            max_execution_time=original_task.max_execution_time,
            tags=original_task.tags.copy() if original_task.tags else [],
            metadata=original_task.metadata.copy() if original_task.metadata else {},
            created_by=current_user.username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await cloned_task.insert()

        logger.info(f"Task cloned: {original_task.name} -> {cloned_task.name} by {current_user.username}")

        return TaskResponse(**cloned_task.dict())

    except Exception as e:
        logger.error(f"Failed to clone task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone task"
        )


@router.get("/{task_id}/export")
async def export_task_results(
    task_id: str,
    current_user: User = Depends(require_permission("task:read"))
):
    """Export task results"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can access this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export this task"
        )

    return {
        "task_info": {
            "id": str(task.id),
            "name": task.name,
            "type": task.task_type,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at
        },
        "results": task.results,
        "statistics": {
            "total_targets": task.total_targets,
            "processed_targets": task.processed_targets,
            "success_count": task.success_count,
            "error_count": task.error_count,
            "execution_time": task.execution_time
        },
        "errors": task.error_messages
    }


@router.get("/{task_id}/results")
async def get_task_results(
    task_id: str,
    current_user: User = Depends(require_permission("task:read"))
):
    """Get detailed task results"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can access this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )

    return {
        "results": task.results,
        "total_results": len(task.results) if task.results else 0,
        "status": task.status,
        "progress": {
            "total_targets": task.total_targets,
            "processed_targets": task.processed_targets,
            "success_count": task.success_count,
            "error_count": task.error_count
        }
    }


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:execute"))
):
    """Cancel a running task"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can cancel this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:execute_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this task"
        )

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not running"
        )

    try:
        # Cancel Celery task if exists
        if task.celery_task_id:
            from app.core.celery import celery_app
            celery_app.control.revoke(task.celery_task_id, terminate=True)

        # Update task status
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        task.updated_by = current_user.username
        task.updated_at = datetime.utcnow()

        await task.save()

        logger.info(f"Task cancelled: {task.name} by {current_user.username}")

        return {"message": "Task cancelled successfully"}

    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel task"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(require_permission("task:delete"))
):
    """Delete task"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can delete this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:delete_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )

    # Don't allow deleting running tasks
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running task. Cancel it first."
        )

    try:
        await task.delete()

        logger.info(f"Task deleted: {task.name} by {current_user.username}")

        return {"message": "Task deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )


@router.get("/{task_id}/logs", response_model=List[Dict[str, Any]])
async def get_task_logs(
    task_id: str,
    current_user: User = Depends(require_permission("task:read"))
):
    """Get task execution logs"""

    task = await ScanTask.get(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check if user can access this task
    if (task.created_by != current_user.username and
        not any(perm in current_user.permissions for perm in ["task:read_all", "system:admin"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this task"
        )

    return task.log_messages


async def execute_task(task: ScanTask):
    """Execute a task based on its type"""

    # Update task status
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    await task.save()

    try:
        # Prepare targets
        all_targets = []
        all_targets.extend(task.target_domains)
        all_targets.extend(task.target_ips)
        all_targets.extend(task.target_urls)

        # Add asset names if target_assets is provided
        if task.target_assets:
            from app.api.models.asset import Asset
            assets = await Asset.find({"_id": {"$in": task.target_assets}}).to_list()
            for asset in assets:
                all_targets.append(asset.name)

        # Execute based on task type
        if task.task_type == TaskType.PORT_SCAN:
            celery_task = port_scan_task.delay(str(task.id), all_targets, task.config)
        elif task.task_type == TaskType.SUBDOMAIN_ENUM:
            celery_task = subdomain_enumeration_task.delay(str(task.id), all_targets, task.config)
        elif task.task_type == TaskType.VULNERABILITY_SCAN:
            celery_task = vulnerability_scan_task.delay(str(task.id), all_targets, task.config)
        else:
            raise ValueError(f"Unsupported task type: {task.task_type}")

        # Store Celery task ID
        task.celery_task_id = celery_task.id
        task.total_targets = len(all_targets)
        await task.save()

    except Exception as e:
        # Update task status to failed
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.error_messages.append(str(e))
        await task.save()
        raise