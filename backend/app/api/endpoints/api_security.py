from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import get_logger
from app.core.url_validator import url_validator, URLValidationError
from app.core.rate_limit import custom_rate_limit
from app.api.models.user import User
from app.api.models.api_security import (
    APIScanTask,
    JSResource,
    APIEndpoint,
    MicroserviceInfo,
    APISecurityIssue,
    APIScanStatus,
    APISecurityIssueType,
    APIIssueSeverity
)
from app.api.schemas.api_security import (
    APIScanTaskCreate,
    APIScanTaskUpdate,
    APIScanTaskResponse,
    APIScanTaskSearch,
    JSResourceResponse,
    APIEndpointResponse,
    MicroserviceInfoResponse,
    APISecurityIssueResponse,
    APISecurityIssueUpdate,
    APISecurityIssueSearch,
    APIScanStatistics
)

logger = get_logger(__name__)
router = APIRouter()


# ============ API扫描任务 ============

@router.post("/scans", response_model=APIScanTaskResponse)
@custom_rate_limit("5/minute")  # ✅ 安全修复：每分钟最多5个扫描任务
async def create_scan_task(
    task_data: APIScanTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建API安全扫描任务"""
    try:
        # ✅ 安全修复：验证目标URL，防止SSRF攻击
        try:
            url_validator.validate(task_data.target_url)
        except URLValidationError as e:
            logger.warning(f"Invalid target URL from user {current_user.id}: {task_data.target_url}, reason: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target URL: {str(e)}"
            )

        # 创建扫描任务
        scan_task = APIScanTask(
            name=task_data.name,
            target_url=task_data.target_url,
            scan_config=task_data.scan_config.dict() if task_data.scan_config else {},
            status=APIScanStatus.PENDING,
            created_by=current_user.id
        )

        db.add(scan_task)
        db.commit()
        db.refresh(scan_task)

        # ✅ Bug修复：直接调用Celery任务，不需要 background_tasks.add_task
        from app.core.celery.tasks.api_scan_tasks import run_api_security_scan
        run_api_security_scan.delay(
            str(scan_task.id),
            task_data.target_url,
            scan_task.scan_config
        )

        logger.info(f"Created API scan task {scan_task.id} for {task_data.target_url}")

        return scan_task

    except HTTPException:
        # 直接抛出HTTP异常（如400错误）
        raise
    except Exception as e:
        logger.error(f"Failed to create scan task: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scans", response_model=List[APIScanTaskResponse])
async def list_scan_tasks(
    status: Optional[APIScanStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取扫描任务列表"""
    query = db.query(APIScanTask)

    if status:
        query = query.filter(APIScanTask.status == status)

    # 非管理员只能看自己的任务
    if current_user.role != 'admin':
        query = query.filter(APIScanTask.created_by == current_user.id)

    total = query.count()
    tasks = query.order_by(desc(APIScanTask.created_at)).offset(skip).limit(limit).all()

    return tasks


@router.get("/scans/{scan_id}", response_model=APIScanTaskResponse)
async def get_scan_task(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取扫描任务详情"""
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    return task


@router.patch("/scans/{scan_id}", response_model=APIScanTaskResponse)
async def update_scan_task(
    scan_id: str,
    task_update: APIScanTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新扫描任务"""
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 更新字段
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.delete("/scans/{scan_id}")
async def delete_scan_task(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除扫描任务"""
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    # 删除关联数据
    db.query(JSResource).filter(JSResource.scan_task_id == scan_id).delete()
    db.query(APIEndpoint).filter(APIEndpoint.scan_task_id == scan_id).delete()
    db.query(MicroserviceInfo).filter(MicroserviceInfo.scan_task_id == scan_id).delete()
    db.query(APISecurityIssue).filter(APISecurityIssue.scan_task_id == scan_id).delete()

    db.delete(task)
    db.commit()

    return {"message": "Scan task deleted successfully"}


# ============ JS资源 ============

@router.get("/scans/{scan_id}/js-resources", response_model=List[JSResourceResponse])
async def get_js_resources(
    scan_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取JS资源列表"""
    # 检查任务是否存在
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    resources = db.query(JSResource)\
        .filter(JSResource.scan_task_id == scan_id)\
        .offset(skip).limit(limit).all()

    return resources


# ============ API接口 ============

@router.get("/scans/{scan_id}/apis", response_model=List[APIEndpointResponse])
async def get_api_endpoints(
    scan_id: str,
    service_path: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取API接口列表"""
    # 检查任务是否存在
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    query = db.query(APIEndpoint).filter(APIEndpoint.scan_task_id == scan_id)

    if service_path:
        query = query.filter(APIEndpoint.service_path == service_path)

    apis = query.offset(skip).limit(limit).all()

    return apis


# ============ 微服务 ============

@router.get("/scans/{scan_id}/microservices", response_model=List[MicroserviceInfoResponse])
async def get_microservices(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取微服务列表"""
    # 检查任务是否存在
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    microservices = db.query(MicroserviceInfo)\
        .filter(MicroserviceInfo.scan_task_id == scan_id)\
        .all()

    return microservices


# ============ 安全问题 ============

@router.get("/scans/{scan_id}/issues", response_model=List[APISecurityIssueResponse])
async def get_security_issues(
    scan_id: str,
    issue_type: Optional[APISecurityIssueType] = None,
    severity: Optional[APIIssueSeverity] = None,
    is_verified: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取安全问题列表"""
    # 检查任务是否存在
    task = db.query(APIScanTask).filter(APIScanTask.id == scan_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Scan task not found")

    # 权限检查
    if current_user.role != 'admin' and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    query = db.query(APISecurityIssue).filter(APISecurityIssue.scan_task_id == scan_id)

    if issue_type:
        query = query.filter(APISecurityIssue.issue_type == issue_type)

    if severity:
        query = query.filter(APISecurityIssue.severity == severity)

    if is_verified is not None:
        query = query.filter(APISecurityIssue.is_verified == is_verified)

    issues = query.order_by(desc(APISecurityIssue.created_at))\
        .offset(skip).limit(limit).all()

    return issues


@router.patch("/issues/{issue_id}", response_model=APISecurityIssueResponse)
async def update_security_issue(
    issue_id: str,
    issue_update: APISecurityIssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新安全问题"""
    issue = db.query(APISecurityIssue).filter(APISecurityIssue.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Security issue not found")

    # 更新字段
    update_data = issue_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    # 更新验证信息
    if issue_update.is_verified is not None:
        issue.verified_by = current_user.id
        from datetime import datetime
        issue.verified_at = datetime.utcnow()

    db.commit()
    db.refresh(issue)

    return issue


# ============ 统计 ============

@router.get("/statistics", response_model=APIScanStatistics)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取统计信息"""
    query = db.query(APIScanTask)

    # 非管理员只看自己的数据
    if current_user.role != 'admin':
        query = query.filter(APIScanTask.created_by == current_user.id)

    total_scans = query.count()
    completed_scans = query.filter(APIScanTask.status == APIScanStatus.COMPLETED).count()
    running_scans = query.filter(APIScanTask.status == APIScanStatus.RUNNING).count()
    failed_scans = query.filter(APIScanTask.status == APIScanStatus.FAILED).count()

    # 获取所有已完成任务的统计
    completed_tasks = query.filter(APIScanTask.status == APIScanStatus.COMPLETED).all()

    total_apis = sum(task.total_apis for task in completed_tasks)
    total_js_files = sum(task.total_js_files for task in completed_tasks)
    total_microservices = sum(task.total_services for task in completed_tasks)
    total_issues = sum(task.total_issues for task in completed_tasks)
    critical_issues = sum(task.critical_issues for task in completed_tasks)
    high_issues = sum(task.high_issues for task in completed_tasks)
    medium_issues = sum(task.medium_issues for task in completed_tasks)
    low_issues = sum(task.low_issues for task in completed_tasks)

    # 按类型统计问题
    issues_query = db.query(APISecurityIssue)
    if current_user.role != 'admin':
        # 只查询用户自己任务的问题
        user_task_ids = [str(task.id) for task in query.all()]
        issues_query = issues_query.filter(APISecurityIssue.scan_task_id.in_(user_task_ids))

    issues_by_type = {}
    for issue_type in APISecurityIssueType:
        count = issues_query.filter(APISecurityIssue.issue_type == issue_type).count()
        if count > 0:
            issues_by_type[issue_type.value] = count

    return APIScanStatistics(
        total_scans=total_scans,
        completed_scans=completed_scans,
        running_scans=running_scans,
        failed_scans=failed_scans,
        total_apis_discovered=total_apis,
        total_js_files=total_js_files,
        total_microservices=total_microservices,
        total_issues=total_issues,
        critical_issues=critical_issues,
        high_issues=high_issues,
        medium_issues=medium_issues,
        low_issues=low_issues,
        issues_by_type=issues_by_type
    )
