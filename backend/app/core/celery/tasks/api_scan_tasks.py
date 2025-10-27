import asyncio
from datetime import datetime
from typing import Dict, Any

from app.core.celery.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
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
from app.api.services.api_security_scanner import APISecurityScanner

logger = get_logger(__name__)


@celery_app.task(bind=True, name="api_scan.run_security_scan")
def run_api_security_scan(self, scan_task_id: str, target_url: str, scan_config: Dict[str, Any]):
    """执行API安全扫描（Celery任务）

    Args:
        scan_task_id: 扫描任务ID
        target_url: 目标URL
        scan_config: 扫描配置
    """
    db = SessionLocal()

    try:
        logger.info(f"Starting API security scan for task {scan_task_id}")

        # 获取扫描任务
        task = db.query(APIScanTask).filter(APIScanTask.id == scan_task_id).first()
        if not task:
            logger.error(f"Scan task {scan_task_id} not found")
            return

        # 更新任务状态
        task.status = APIScanStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.current_phase = "初始化"
        db.commit()

        # 创建扫描器
        scanner = APISecurityScanner(config=scan_config)

        # 执行扫描（异步转同步）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            scanner.scan(target_url, scan_config)
        )
        loop.close()

        logger.info(f"Scan completed for task {scan_task_id}")

        # 保存结果到数据库
        _save_scan_results(db, scan_task_id, result)

        # 更新任务状态
        task.status = APIScanStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.duration_seconds = int((task.completed_at - task.started_at).total_seconds())
        task.current_phase = "完成"
        task.progress = 100.0

        # 更新统计
        task.total_js_files = len(result.get('js_resources', []))
        task.total_apis = len(result.get('apis', []))
        task.total_services = len(result.get('microservices', []))
        task.total_issues = len(result.get('security_issues', []))

        # 统计问题严重程度
        issues = result.get('security_issues', [])
        task.critical_issues = sum(1 for i in issues if i.get('severity') == 'critical')
        task.high_issues = sum(1 for i in issues if i.get('severity') == 'high')
        task.medium_issues = sum(1 for i in issues if i.get('severity') == 'medium')
        task.low_issues = sum(1 for i in issues if i.get('severity') == 'low')

        db.commit()

        logger.info(f"API security scan completed for task {scan_task_id}")

    except Exception as e:
        logger.error(f"API security scan failed for task {scan_task_id}: {str(e)}")

        # 更新任务状态为失败
        try:
            task = db.query(APIScanTask).filter(APIScanTask.id == scan_task_id).first()
            if task:
                task.status = APIScanStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e2:
            logger.error(f"Failed to update task status: {str(e2)}")

        raise

    finally:
        db.close()


def _save_scan_results(db: SessionLocal, scan_task_id: str, result: Dict[str, Any]):
    """保存扫描结果到数据库

    Args:
        db: 数据库会话
        scan_task_id: 扫描任务ID
        result: 扫描结果
    """
    try:
        logger.info(f"Saving scan results for task {scan_task_id}")

        # 1. 保存JS资源
        js_resources = result.get('js_resources', [])
        for js in js_resources:
            js_resource = JSResource(
                scan_task_id=scan_task_id,
                url=js.get('url', ''),
                base_url=js.get('base_url'),
                file_name=js.get('file_name'),
                file_size=js.get('file_size'),
                content_hash=js.get('content_hash'),
                extraction_method=js.get('extraction_method'),
                has_apis=False,  # 将在后续分析中更新
                has_base_api_path=False,
                has_sensitive_info=False,
                extracted_apis=[],
                extracted_base_paths=[]
            )
            db.add(js_resource)

        db.commit()
        logger.info(f"Saved {len(js_resources)} JS resources")

        # 2. 保存API接口
        apis = result.get('apis', [])
        for api in apis:
            api_endpoint = APIEndpoint(
                scan_task_id=scan_task_id,
                base_url=api.get('base_url', ''),
                base_api_path=api.get('base_api_path'),
                service_path=api.get('service_path'),
                api_path=api.get('api_path', ''),
                full_url=api.get('full_url', ''),
                http_method=api.get('http_method', 'GET'),
                discovery_method=api.get('discovery_method'),
                status_code=api.get('status_code'),
                response_time=api.get('response_time'),
                is_404=api.get('status_code') == 404,
                is_public_api=api.get('is_public_api'),
                requires_auth=api.get('requires_auth')
            )
            db.add(api_endpoint)

        db.commit()
        logger.info(f"Saved {len(apis)} API endpoints")

        # 3. 保存微服务信息
        microservices = result.get('microservices', [])
        for service in microservices:
            microservice = MicroserviceInfo(
                scan_task_id=scan_task_id,
                base_url=service.get('base_url', ''),
                service_name=service.get('service_name', ''),
                service_full_path=service.get('service_full_path', ''),
                total_endpoints=service.get('total_endpoints', 0),
                unique_paths=service.get('unique_paths', []),
                detected_technologies=service.get('detected_technologies', []),
                has_vulnerabilities=service.get('has_vulnerabilities', False),
                vulnerability_details=service.get('vulnerability_details', [])
            )
            db.add(microservice)

        db.commit()
        logger.info(f"Saved {len(microservices)} microservices")

        # 4. 保存安全问题
        issues = result.get('security_issues', [])
        for issue in issues:
            # 映射问题类型
            issue_type_map = {
                'unauthorized_access': APISecurityIssueType.UNAUTHORIZED_ACCESS,
                'sensitive_data_leak': APISecurityIssueType.SENSITIVE_DATA_LEAK,
                'component_vulnerability': APISecurityIssueType.COMPONENT_VULNERABILITY,
                'weak_authentication': APISecurityIssueType.WEAK_AUTHENTICATION,
            }

            # 映射严重程度
            severity_map = {
                'critical': APIIssueSeverity.CRITICAL,
                'high': APIIssueSeverity.HIGH,
                'medium': APIIssueSeverity.MEDIUM,
                'low': APIIssueSeverity.LOW,
                'info': APIIssueSeverity.INFO,
            }

            issue_type = issue_type_map.get(
                issue.get('type', 'other'),
                APISecurityIssueType.OTHER
            )
            severity = severity_map.get(
                issue.get('severity', 'info'),
                APIIssueSeverity.INFO
            )

            security_issue = APISecurityIssue(
                scan_task_id=scan_task_id,
                title=issue.get('title', 'Unknown Issue'),
                description=issue.get('description', ''),
                issue_type=issue_type,
                severity=severity,
                target_url=issue.get('target_url', ''),
                target_api=issue.get('target_api'),
                evidence=issue.get('evidence', {}),
                remediation=issue.get('remediation'),
                ai_verified=False
            )
            db.add(security_issue)

        db.commit()
        logger.info(f"Saved {len(issues)} security issues")

        logger.info(f"Successfully saved all scan results for task {scan_task_id}")

    except Exception as e:
        logger.error(f"Failed to save scan results: {str(e)}")
        db.rollback()
        raise
