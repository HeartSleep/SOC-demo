from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
import threading
import random
import time

from app.core.database_simple import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def simulate_task_execution(task_id: str):
    """在后台模拟任务执行过程"""
    def execution_worker():
        try:
            db = get_database()

            # 模拟扫描过程，逐步更新进度
            progress_steps = [10, 25, 45, 60, 75, 90, 100]

            for step in progress_steps:
                time.sleep(random.uniform(2, 5))  # 随机等待2-5秒

                # 更新任务进度
                tasks = db.data.get('tasks', [])
                for i, task in enumerate(tasks):
                    if task['id'] == task_id and task.get('status') == 'running':
                        db.data['tasks'][i]['progress'] = step
                        db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()

                        # 如果是100%，标记任务完成
                        if step == 100:
                            db.data['tasks'][i]['status'] = 'completed'
                            db.data['tasks'][i]['completed_at'] = datetime.now().isoformat()

                            # 生成扫描结果（模拟发现的漏洞）
                            scan_results = generate_scan_results(task)
                            db.data['tasks'][i]['results'] = scan_results

                            logger.info(f"Task {task_id} completed successfully")

                        db._mark_dirty()
                        break
                else:
                    # 任务已被取消或删除，停止执行
                    logger.info(f"Task {task_id} was cancelled or deleted, stopping execution")
                    break

        except Exception as e:
            logger.error(f"Error in task execution for {task_id}: {e}")
            # 标记任务失败
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

    # 在后台线程中运行任务
    thread = threading.Thread(target=execution_worker, daemon=True)
    thread.start()


def generate_scan_results(task):
    """生成模拟扫描结果"""
    task_type = task.get('type', 'port_scan')
    target_count = len(task.get('target_assets', [])) + len(task.get('manual_targets', '').split('\n') if task.get('manual_targets') else [])

    results = {
        'summary': {
            'targets_scanned': max(1, target_count),
            'scan_duration': random.uniform(30, 300),  # 30秒到5分钟
            'findings_count': 0
        },
        'findings': []
    }

    # 根据扫描类型生成不同的结果
    if task_type == 'port_scan':
        # 生成端口扫描结果
        open_ports = random.sample(range(21, 9999), random.randint(2, 8))
        for port in open_ports:
            service = random.choice(['http', 'https', 'ssh', 'ftp', 'smtp', 'dns', 'mysql', 'postgresql'])
            results['findings'].append({
                'type': 'open_port',
                'port': port,
                'service': service,
                'severity': 'info',
                'description': f'Port {port} is open running {service}'
            })

    elif task_type == 'vulnerability_scan':
        # 生成漏洞扫描结果
        vuln_types = [
            {'name': 'SQL Injection', 'severity': 'high'},
            {'name': 'XSS (Cross-Site Scripting)', 'severity': 'medium'},
            {'name': 'Weak Password Policy', 'severity': 'low'},
            {'name': 'Outdated Software Version', 'severity': 'medium'},
            {'name': 'Missing Security Headers', 'severity': 'low'},
            {'name': 'Directory Traversal', 'severity': 'high'},
        ]

        found_vulns = random.sample(vuln_types, random.randint(1, 4))
        for vuln in found_vulns:
            results['findings'].append({
                'type': 'vulnerability',
                'name': vuln['name'],
                'severity': vuln['severity'],
                'description': f'Detected {vuln["name"]} vulnerability',
                'risk_score': random.uniform(3.0, 9.5)
            })

    elif task_type == 'web_discovery':
        # 生成Web发现结果
        web_techs = ['Apache', 'Nginx', 'PHP', 'MySQL', 'WordPress', 'jQuery', 'Bootstrap']
        found_techs = random.sample(web_techs, random.randint(2, 5))
        for tech in found_techs:
            results['findings'].append({
                'type': 'technology',
                'name': tech,
                'version': f'{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}',
                'description': f'Detected {tech} technology'
            })

    results['summary']['findings_count'] = len(results['findings'])
    return results


@router.get("/")
async def list_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    status: str = Query(""),
    type: str = Query("")
):
    """获取任务列表"""
    
    db = get_database()
    current_time = datetime.now()
    
    # 确保任务数据存在
    if not db.data.get('tasks'):
        demo_tasks = [
            {
                "id": "1",
                "name": "Web服务器漏洞扫描",
                "description": "对所有Web服务器进行全面的漏洞扫描",
                "type": "vulnerability_scan",
                "status": "running",
                "priority": "high",
                "target": "192.168.1.100-110",
                "assigned_to": "1",
                "progress": 65,
                "started_at": (current_time - timedelta(hours=2)).isoformat(),
                "estimated_completion": (current_time + timedelta(hours=1)).isoformat(),
                "created_at": (current_time - timedelta(hours=3)).isoformat(),
                "updated_at": current_time.isoformat(),
                "created_by": "1",
                "tags": ["vulnerability", "web", "automated"]
            },
            {
                "id": "2",
                "name": "资产发现扫描",
                "description": "扫描网络中的新设备和服务",
                "type": "asset_discovery",
                "status": "completed",
                "priority": "medium",
                "target": "192.168.1.0/24",
                "assigned_to": "2",
                "progress": 100,
                "started_at": (current_time - timedelta(days=1)).isoformat(),
                "completed_at": (current_time - timedelta(hours=12)).isoformat(),
                "estimated_completion": (current_time - timedelta(hours=12)).isoformat(),
                "created_at": (current_time - timedelta(days=1, hours=2)).isoformat(),
                "updated_at": (current_time - timedelta(hours=12)).isoformat(),
                "created_by": "1",
                "tags": ["discovery", "network", "completed"]
            },
            {
                "id": "3",
                "name": "安全配置检查",
                "description": "检查服务器安全配置合规性",
                "type": "compliance_check",
                "status": "pending",
                "priority": "low",
                "target": "database servers",
                "assigned_to": "2",
                "progress": 0,
                "scheduled_at": (current_time + timedelta(hours=4)).isoformat(),
                "estimated_completion": (current_time + timedelta(hours=8)).isoformat(),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "created_by": "1",
                "tags": ["compliance", "config", "security"]
            }
        ]
        
        db.data['tasks'] = demo_tasks
        db._mark_dirty()
    
    tasks = db.data['tasks']
    
    # 应用过滤器
    if search:
        tasks = [t for t in tasks if 
                 search.lower() in t.get('name', '').lower() or 
                 search.lower() in t.get('description', '').lower()]
    
    if status:
        tasks = [t for t in tasks if t.get('status') == status]
        
    if type:
        tasks = [t for t in tasks if t.get('type') == type]
    
    # 分页
    total = len(tasks)
    start = (page - 1) * limit
    end = start + limit
    paginated_tasks = tasks[start:end]
    
    return {
        "data": paginated_tasks,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_task_stats():
    """获取任务统计信息"""
    
    db = get_database()
    tasks = db.data.get('tasks', [])
    
    # 计算统计信息
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
    """获取单个任务详情"""
    
    db = get_database()
    tasks = db.data.get('tasks', [])
    
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.post("/")
async def create_task(task_data: dict):
    """创建新任务"""
    
    db = get_database()
    
    # 生成新ID
    max_id = 0
    for task in db.data.get('tasks', []):
        try:
            max_id = max(max_id, int(task['id']))
        except:
            pass
    
    new_task = {
        "id": str(max_id + 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "pending",
        "priority": "medium",
        "progress": 0,
        **task_data
    }
    
    if 'tasks' not in db.data:
        db.data['tasks'] = []
    
    db.data['tasks'].append(new_task)
    db._mark_dirty()
    
    return new_task


@router.put("/{task_id}")
async def update_task(task_id: str, update_data: dict):
    """更新任务"""
    
    db = get_database()
    tasks = db.data.get('tasks', [])
    
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            db.data['tasks'][i].update(update_data)
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return db.data['tasks'][i]
    
    raise HTTPException(status_code=404, detail="任务不存在")


@router.get("/{task_id}/results")
async def get_task_results(task_id: str):
    """获取任务结果"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    if not task:
        # Return empty results instead of 404
        return {"summary": None, "vulnerabilities": []}

    if task.get('status') != 'completed':
        # Return empty results for uncompleted tasks instead of 400
        return {"summary": None, "vulnerabilities": []}

    return task.get('results', {"summary": None, "vulnerabilities": []})


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    
    db = get_database()
    tasks = db.data.get('tasks', [])
    
    db.data['tasks'] = [t for t in tasks if t['id'] != task_id]
    db._mark_dirty()
    
    return {"message": "任务已删除"}


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """启动任务"""

    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            # 检查任务是否已经在运行
            if task.get('status') == 'running':
                return {"message": "任务已在运行", "task": task}

            # 更新任务状态
            db.data['tasks'][i]['status'] = 'running'
            db.data['tasks'][i]['started_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['progress'] = 0
            db._mark_dirty()

            # 启动后台任务执行
            simulate_task_execution(task_id)

            logger.info(f"Started task {task_id}: {task.get('name')}")
            return {"message": "任务已启动", "task": db.data['tasks'][i]}

    raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务"""
    
    db = get_database()
    tasks = db.data.get('tasks', [])
    
    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            db.data['tasks'][i]['status'] = 'cancelled'
            db.data['tasks'][i]['stopped_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return {"message": "任务已停止", "task": db.data['tasks'][i]}

    raise HTTPException(status_code=404, detail="任务不存在")

@router.get("/{task_id}/logs")
async def get_task_logs(task_id: str):
    """获取任务日志（演示版本）"""
    db = get_database()
    tasks = db.data.get('tasks', [])

    task = next((t for t in tasks if t['id'] == task_id), None)

    # Always return an array, even if task doesn't exist
    if not task:
        return []

    # 返回模拟日志数据
    logs = []
    if task['status'] in ['running', 'completed', 'failed']:
        logs = [
            f"[{datetime.now().isoformat()}] Task {task_id} started",
            f"[{datetime.now().isoformat()}] Initializing scan engine...",
            f"[{datetime.now().isoformat()}] Target: {task.get('target', 'N/A')}",
            f"[{datetime.now().isoformat()}] Scan type: {task.get('type', 'N/A')}",
        ]

        if task['status'] == 'completed':
            logs.extend([
                f"[{datetime.now().isoformat()}] Scan completed successfully",
                f"[{datetime.now().isoformat()}] Results saved to database"
            ])
        elif task['status'] == 'failed':
            logs.append(f"[{datetime.now().isoformat()}] Task failed: Error during execution")
        elif task['status'] == 'running':
            logs.append(f"[{datetime.now().isoformat()}] Scan in progress...")

    return logs

@router.post("/{task_id}/restart")
async def restart_task(task_id: str):
    """重启任务（演示版本）"""
    db = get_database()
    tasks = db.data.get('tasks', [])

    for i, task in enumerate(tasks):
        if task['id'] == task_id:
            # 更新任务状态为运行中
            db.data['tasks'][i]['status'] = 'running'
            db.data['tasks'][i]['progress'] = 0
            db.data['tasks'][i]['started_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['updated_at'] = datetime.now().isoformat()
            db.data['tasks'][i]['stopped_at'] = None
            db.data['tasks'][i]['completed_at'] = None
            db._mark_dirty()

            # 返回重启成功消息
            return {"message": "任务已重启", "task": db.data['tasks'][i]}

    # Return a soft error response instead of raising exception
    return {"message": "任务不存在", "task": None}
