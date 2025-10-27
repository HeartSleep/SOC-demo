"""
Real Task Execution API with Scanner Engine Integration
This module provides task management with actual security scanning capabilities
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import json
import asyncio
import threading
import uuid
from pathlib import Path

from app.core.database_simple import get_database
from app.core.logging import get_logger
from app.services.scanner_engine import scanner_engine

logger = get_logger(__name__)
router = APIRouter()


async def execute_real_scan(task_id: str, task_data: dict):
    """Execute real security scan using scanner engine"""
    try:
        db = get_database()

        # Extract scan parameters
        target = task_data.get('target', '')
        scan_type = task_data.get('type', 'vulnerability_scan')

        # Map frontend scan types to scanner engine methods
        scan_config = {
            'subdomain_scan': True,
            'port_scan': True,
            'vulnerability_scan': True,
            'tech_detection': True,
            'crawl': False
        }

        # Adjust config based on scan type
        if scan_type == 'port_scan':
            scan_config = {
                'subdomain_scan': False,
                'port_scan': True,
                'vulnerability_scan': False,
                'tech_detection': False,
                'crawl': False
            }
        elif scan_type == 'web_discovery':
            scan_config = {
                'subdomain_scan': True,
                'port_scan': False,
                'vulnerability_scan': False,
                'tech_detection': True,
                'crawl': True
            }
        elif scan_type == 'asset_discovery':
            scan_config = {
                'subdomain_scan': True,
                'port_scan': True,
                'vulnerability_scan': False,
                'tech_detection': True,
                'crawl': False
            }

        # Update task status to running
        tasks = db.data.get('tasks', [])
        for i, task in enumerate(tasks):
            if task['id'] == task_id:
                db.data['tasks'][i]['status'] = 'running'
                db.data['tasks'][i]['progress'] = 10
                db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
                db._mark_dirty()
                break

        # Execute comprehensive scan
        results = await scanner_engine.comprehensive_scan(target, scan_config)

        # Update task with results
        for i, task in enumerate(tasks):
            if task['id'] == task_id:
                db.data['tasks'][i]['status'] = 'completed'
                db.data['tasks'][i]['progress'] = 100
                db.data['tasks'][i]['completed_at'] = datetime.now().isoformat()
                db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
                db.data['tasks'][i]['results'] = results
                db._mark_dirty()

                logger.info(f"Task {task_id} completed with real scan results")
                break

    except Exception as e:
        logger.error(f"Error executing real scan for task {task_id}: {e}")

        # Mark task as failed
        try:
            db = get_database()
            tasks = db.data.get('tasks', [])
            for i, task in enumerate(tasks):
                if task['id'] == task_id:
                    db.data['tasks'][i]['status'] = 'failed'
                    db.data['tasks'][i]['error'] = str(e)
                    db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
                    db._mark_dirty()
                    break
        except:
            pass


def start_real_task_execution(task_id: str, task_data: dict):
    """Start task execution in background thread"""
    def execution_worker():
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(execute_real_scan(task_id, task_data))
        finally:
            loop.close()

    # Start execution in background thread
    thread = threading.Thread(target=execution_worker, daemon=True)
    thread.start()


@router.get("/")
async def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    status: str = Query(""),
    type: str = Query("")
):
    """Get task list"""

    db = get_database()
    current_time = datetime.now()

    # Ensure tasks data exists
    if not db.data.get('tasks'):
        db.data['tasks'] = []
        db._mark_dirty()

    tasks = db.data['tasks']

    # Apply filters
    if search:
        tasks = [t for t in tasks if
                 search.lower() in t.get('name', '').lower() or
                 search.lower() in t.get('description', '').lower()]

    if status:
        tasks = [t for t in tasks if t.get('status') == status]

    if type:
        tasks = [t for t in tasks if t.get('type') == type]

    # Pagination
    total = len(tasks)
    start = (page - 1) * limit
    end = start + limit
    paginated_tasks = tasks[start:end]

    return {
        "data": paginated_tasks,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0
    }


@router.get("/stats")
async def get_task_stats():
    """Get task statistics"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    # Calculate statistics
    total = len(tasks)

    status_counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}
    type_counts = {}
    priority_counts = {"high": 0, "medium": 0, "low": 0}

    for task in tasks:
        status = task.get('status', 'pending')
        task_type = task.get('type', 'unknown')
        priority = task.get('priority', 'medium')

        if status in status_counts:
            status_counts[status] += 1

        type_counts[task_type] = type_counts.get(task_type, 0) + 1

        if priority in priority_counts:
            priority_counts[priority] += 1

    return {
        "total_tasks": total,
        "tasks_by_status": status_counts,
        "tasks_by_type": type_counts,
        "tasks_by_priority": priority_counts,
        "running_tasks": status_counts["running"],
        "completed_today": status_counts["completed"]
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get single task details"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.post("/")
async def create_task(task_data: dict):
    """Create new task with real scanning capability"""

    db = get_database()

    # Generate new ID
    new_id = str(uuid.uuid4())[:8]

    new_task = {
        "id": new_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "pending",
        "priority": task_data.get("priority", "medium"),
        "progress": 0,
        **task_data
    }

    if 'tasks' not in db.data:
        db.data['tasks'] = []

    db.data['tasks'].append(new_task)
    db._mark_dirty()

    logger.info(f"Created new task {new_id}: {new_task.get('name')}")

    return new_task


@router.put("/{task_id}")
async def update_task(task_id: str, update_data: dict):
    """Update task"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            db.data['tasks'][i].update(update_data)
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return db.data['tasks'][i]

    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/{task_id}/results")
async def get_task_results(task_id: str):
    """Get task scan results"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        return {"summary": None, "scans": {}}

    if task.get('status') != 'completed':
        return {"summary": None, "scans": {}}

    # Return real scan results
    results = task.get('results', {})

    # Format results for frontend
    formatted_results = {
        "summary": results.get("statistics", {}),
        "scans": results.get("scans", {}),
        "target": results.get("target"),
        "scan_id": results.get("scan_id"),
        "timestamp": results.get("timestamp")
    }

    return formatted_results


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete task"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    db.data['tasks'] = [t for t in tasks if t['id'] != task_id]
    db._mark_dirty()

    return {"message": "Task deleted"}


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """Start task with real scanning"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            # Check if task is already running
            if task.get('status') == 'running':
                return {"message": "Task already running", "task": task}

            # Update task status
            db.data['tasks'][i]['status'] = 'running'
            db.data['tasks'][i]['started_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['progress'] = 0
            db._mark_dirty()

            # Start real task execution
            start_real_task_execution(task_id, task)

            logger.info(f"Started real scan task {task_id}: {task.get('name')}")
            return {"message": "Task started", "task": db.data['tasks'][i]}

    raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """Stop running task"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            db.data['tasks'][i]['status'] = 'cancelled'
            db.data['tasks'][i]['stopped_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()

            logger.info(f"Stopped task {task_id}")
            return {"message": "Task stopped", "task": db.data['tasks'][i]}

    raise HTTPException(status_code=404, detail="Task not found")


@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Get task execution logs"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        return []

    # Get real-time logs from scan results if available
    logs = []

    if task.get('status') in ['running', 'completed', 'failed']:
        logs.append(f"[{task.get('started_at', datetime.now().isoformat())}] Task {task_id} started")
        logs.append(f"[{datetime.now().isoformat()}] Target: {task.get('target', 'N/A')}")
        logs.append(f"[{datetime.now().isoformat()}] Scan type: {task.get('type', 'N/A')}")

        if task.get('results'):
            results = task['results']
            if results.get('scans'):
                for scan_name, scan_data in results['scans'].items():
                    if isinstance(scan_data, dict) and not scan_data.get('error'):
                        logs.append(f"[{datetime.now().isoformat()}] {scan_name} scan completed")

                        # Add specific findings
                        if scan_name == 'subdomains' and scan_data.get('total_found'):
                            logs.append(f"[{datetime.now().isoformat()}] Found {scan_data['total_found']} subdomains")
                        elif scan_name == 'ports' and scan_data.get('total_ports'):
                            logs.append(f"[{datetime.now().isoformat()}] Found {scan_data['total_ports']} open ports")
                        elif scan_name == 'vulnerabilities' and scan_data.get('total_vulnerabilities'):
                            logs.append(f"[{datetime.now().isoformat()}] Found {scan_data['total_vulnerabilities']} vulnerabilities")

        if task['status'] == 'completed':
            logs.append(f"[{task.get('completed_at', datetime.now().isoformat())}] Scan completed successfully")
        elif task['status'] == 'failed':
            logs.append(f"[{datetime.now().isoformat()}] Task failed: {task.get('error', 'Unknown error')}")
        elif task['status'] == 'running':
            logs.append(f"[{datetime.now().isoformat()}] Scan in progress...")

    return logs


@router.post("/{task_id}/restart")
async def restart_task(task_id: str):
    """Restart a task"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            # Reset task status
            db.data['tasks'][i]['status'] = 'running'
            db.data['tasks'][i]['progress'] = 0
            db.data['tasks'][i]['started_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['stopped_at'] = None
            db.data['tasks'][i]['completed_at'] = None
            db.data['tasks'][i]['error'] = None
            db.data['tasks'][i]['results'] = None
            db._mark_dirty()

            # Start real task execution
            start_real_task_execution(task_id, db.data['tasks'][i])

            logger.info(f"Restarted task {task_id}")
            return {"message": "Task restarted", "task": db.data['tasks'][i]}

    return {"message": "Task not found", "task": None}


@router.post("/{task_id}/clone")
async def clone_task(task_id: str):
    """Clone an existing task"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    # Find the task to clone
    task_to_clone = next((t for t in tasks if t['id'] == task_id), None)

    if not task_to_clone:
        raise HTTPException(status_code=404, detail="Task not found")

    # Create a new task with cloned data
    new_id = str(uuid.uuid4())[:8]
    cloned_task = {
        **task_to_clone,
        "id": new_id,
        "name": f"{task_to_clone.get('name', 'Task')} (Clone)",
        "status": "pending",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "stopped_at": None,
        "error": None,
        "results": None
    }

    db.data['tasks'].append(cloned_task)
    db._mark_dirty()

    logger.info(f"Cloned task {task_id} to new task {new_id}")
    return {"message": "Task cloned successfully", "task": cloned_task}


@router.get("/{task_id}/export")
async def export_task(task_id: str):
    """Export task data and results"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Prepare export data
    export_data = {
        "task": task,
        "exported_at": datetime.now().isoformat(),
        "format_version": "1.0",
        "platform": "SOC Security Platform"
    }

    # Include scan results if completed
    if task.get('status') == 'completed' and task.get('results'):
        export_data['scan_results'] = task['results']

    return export_data