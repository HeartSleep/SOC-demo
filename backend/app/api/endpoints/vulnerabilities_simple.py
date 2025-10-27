from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import json

from app.core.database_simple import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_vulnerabilities(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    severity: str = Query(""),
    status: str = Query("")
):
    """获取漏洞列表"""
    
    db = get_database()
    current_time = datetime.now()
    
    # 确保漏洞数据存在
    if not db.data.get('vulnerabilities'):
        demo_vulnerabilities = [
            {
                "id": "1",
                "title": "SQL注入漏洞",
                "description": "登录表单存在SQL注入漏洞，可能导致数据泄露",
                "vulnerability_type": "sql_injection",
                "severity": "high",
                "status": "open",
                "target_url": "https://example.com/login",
                "target_ip": "192.168.1.100",
                "cvss_score": 8.1,
                "scanner": "自动扫描",
                "discovery_date": current_time.isoformat(),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "verified": False,
                "assigned_to": None,
                "tags": ["injection", "authentication"]
            },
            {
                "id": "2",
                "title": "跨站脚本攻击(XSS)",
                "description": "搜索功能存在反射型XSS漏洞",
                "vulnerability_type": "xss",
                "severity": "medium",
                "status": "in_progress",
                "target_url": "https://example.com/search",
                "target_ip": "192.168.1.101",
                "cvss_score": 5.4,
                "scanner": "手工测试",
                "discovery_date": (current_time - timedelta(days=1)).isoformat(),
                "created_at": (current_time - timedelta(days=1)).isoformat(),
                "updated_at": current_time.isoformat(),
                "verified": True,
                "assigned_to": "1",
                "tags": ["xss", "input_validation"]
            },
            {
                "id": "3",
                "title": "弱密码策略",
                "description": "系统未强制执行强密码策略",
                "vulnerability_type": "weak_authentication",
                "severity": "low",
                "status": "fixed",
                "target_url": "https://example.com/register",
                "target_ip": "192.168.1.102",
                "cvss_score": 3.1,
                "scanner": "安全审计",
                "discovery_date": (current_time - timedelta(days=7)).isoformat(),
                "created_at": (current_time - timedelta(days=7)).isoformat(),
                "updated_at": (current_time - timedelta(days=2)).isoformat(),
                "verified": True,
                "assigned_to": "1",
                "tags": ["authentication", "policy"]
            }
        ]
        
        db.data['vulnerabilities'] = demo_vulnerabilities
        db._mark_dirty()
    
    vulnerabilities = db.data['vulnerabilities']
    
    # 应用过滤器
    if search:
        vulnerabilities = [v for v in vulnerabilities if 
                          search.lower() in v.get('title', '').lower() or 
                          search.lower() in v.get('description', '').lower()]
    
    if severity:
        vulnerabilities = [v for v in vulnerabilities if v.get('severity') == severity]
        
    if status:
        vulnerabilities = [v for v in vulnerabilities if v.get('status') == status]
    
    # 分页
    total = len(vulnerabilities)
    start = (page - 1) * limit
    end = start + limit
    paginated_vulnerabilities = vulnerabilities[start:end]
    
    return {
        "data": paginated_vulnerabilities,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_vulnerability_stats():
    """获取漏洞统计信息"""
    
    db = get_database()
    vulnerabilities = db.data.get('vulnerabilities', [])
    
    # 计算统计信息
    total = len(vulnerabilities)
    
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    status_counts = {"open": 0, "in_progress": 0, "fixed": 0, "closed": 0, "false_positive": 0}
    
    for vuln in vulnerabilities:
        severity = vuln.get('severity', 'low')
        status = vuln.get('status', 'open')
        
        if severity in severity_counts:
            severity_counts[severity] += 1
        if status in status_counts:
            status_counts[status] += 1
    
    verified_count = len([v for v in vulnerabilities if v.get('verified', False)])
    
    return {
        "total_vulnerabilities": total,
        "vulnerabilities_by_severity": severity_counts,
        "vulnerabilities_by_status": status_counts,
        "verified_vulnerabilities": verified_count,
        "overdue_vulnerabilities": 0,
        "recent_vulnerabilities": total,
        "average_cvss_score": 5.5
    }


@router.get("/{vulnerability_id}")
async def get_vulnerability(vulnerability_id: str):
    """获取单个漏洞详情"""
    
    db = get_database()
    vulnerabilities = db.data.get('vulnerabilities', [])
    
    vulnerability = next((v for v in vulnerabilities if v['id'] == vulnerability_id), None)
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="漏洞不存在")
    
    return vulnerability


@router.post("/")
async def create_vulnerability(vulnerability_data: dict):
    """创建新漏洞"""
    
    db = get_database()
    
    # 生成新ID
    max_id = 0
    for vuln in db.data.get('vulnerabilities', []):
        try:
            max_id = max(max_id, int(vuln['id']))
        except:
            pass
    
    new_vulnerability = {
        "id": str(max_id + 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        **vulnerability_data
    }
    
    if 'vulnerabilities' not in db.data:
        db.data['vulnerabilities'] = []
    
    db.data['vulnerabilities'].append(new_vulnerability)
    db._mark_dirty()
    
    return new_vulnerability


@router.put("/{vulnerability_id}")
async def update_vulnerability(vulnerability_id: str, update_data: dict):
    """更新漏洞"""
    
    db = get_database()
    vulnerabilities = db.data.get('vulnerabilities', [])
    
    for i, vuln in enumerate(vulnerabilities):
        if vuln['id'] == vulnerability_id:
            db.data['vulnerabilities'][i].update(update_data)
            db.data['vulnerabilities'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return db.data['vulnerabilities'][i]
    
    raise HTTPException(status_code=404, detail="漏洞不存在")


@router.delete("/{vulnerability_id}")
async def delete_vulnerability(vulnerability_id: str):
    """删除漏洞"""
    
    db = get_database()
    vulnerabilities = db.data.get('vulnerabilities', [])
    
    db.data['vulnerabilities'] = [v for v in vulnerabilities if v['id'] != vulnerability_id]
    db._mark_dirty()
    
    return {"message": "漏洞已删除"}
