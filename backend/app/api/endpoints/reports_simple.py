from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import json

from app.core.database_simple import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    type: str = Query(""),
    status: str = Query("")
):
    """获取报告列表"""
    
    db = get_database()
    current_time = datetime.now()
    
    # 确保报告数据存在
    if not db.data.get('reports'):
        demo_reports = [
            {
                "id": "1",
                "title": "月度安全报告 - 2024年9月",
                "description": "2024年9月份安全态势总结报告",
                "type": "security_summary",
                "status": "completed",
                "format": "pdf",
                "created_by": "1",
                "created_at": (current_time - timedelta(days=2)).isoformat(),
                "updated_at": (current_time - timedelta(days=1)).isoformat(),
                "generated_at": (current_time - timedelta(days=1)).isoformat(),
                "file_size": 2457600,  # 2.4MB
                "download_count": 15,
                "tags": ["monthly", "summary", "security"],
                "period_start": (current_time - timedelta(days=30)).isoformat(),
                "period_end": (current_time - timedelta(days=1)).isoformat()
            },
            {
                "id": "2", 
                "title": "漏洞扫描报告 - Web服务器",
                "description": "针对Web服务器的全面漏洞扫描报告",
                "type": "vulnerability_scan",
                "status": "completed", 
                "format": "html",
                "created_by": "2",
                "created_at": (current_time - timedelta(days=7)).isoformat(),
                "updated_at": (current_time - timedelta(days=7)).isoformat(),
                "generated_at": (current_time - timedelta(days=7)).isoformat(),
                "file_size": 1524000,  # 1.5MB
                "download_count": 8,
                "tags": ["vulnerability", "scan", "web"],
                "period_start": (current_time - timedelta(days=8)).isoformat(),
                "period_end": (current_time - timedelta(days=7)).isoformat()
            },
            {
                "id": "3",
                "title": "合规性检查报告",
                "description": "企业安全合规性检查详细报告",
                "type": "compliance_check",
                "status": "generating",
                "format": "docx",
                "created_by": "1",
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat(),
                "generated_at": None,
                "file_size": None,
                "download_count": 0,
                "tags": ["compliance", "audit", "policy"],
                "period_start": (current_time - timedelta(days=30)).isoformat(),
                "period_end": current_time.isoformat()
            }
        ]
        
        db.data['reports'] = demo_reports
        db._mark_dirty()
    
    reports = db.data['reports']
    
    # 应用过滤器
    if search:
        reports = [r for r in reports if 
                   search.lower() in r.get('title', '').lower() or 
                   search.lower() in r.get('description', '').lower()]
    
    if type:
        reports = [r for r in reports if r.get('type') == type]
        
    if status:
        reports = [r for r in reports if r.get('status') == status]
    
    # 分页
    total = len(reports)
    start = (page - 1) * limit
    end = start + limit
    paginated_reports = reports[start:end]
    
    return {
        "data": paginated_reports,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_report_stats():
    """获取报告统计信息"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    # 计算统计信息
    total = len(reports)
    
    type_counts = {}
    status_counts = {"completed": 0, "generating": 0, "failed": 0, "pending": 0}
    format_counts = {"pdf": 0, "html": 0, "docx": 0, "xlsx": 0}
    
    for report in reports:
        report_type = report.get('type', 'unknown')
        status = report.get('status', 'pending')
        format_type = report.get('format', 'pdf')
        
        type_counts[report_type] = type_counts.get(report_type, 0) + 1
        
        if status in status_counts:
            status_counts[status] += 1
            
        if format_type in format_counts:
            format_counts[format_type] += 1
    
    return {
        "total_reports": total,
        "reports_by_type": type_counts,
        "reports_by_status": status_counts,
        "reports_by_format": format_counts,
        "recent_reports": total
    }


@router.get("/{report_id}")
async def get_report(report_id: str):
    """获取单个报告详情"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return report


@router.post("/")
async def create_report(report_data: dict):
    """创建新报告"""
    
    db = get_database()
    
    # 生成新ID
    max_id = 0
    for report in db.data.get('reports', []):
        try:
            max_id = max(max_id, int(report['id']))
        except:
            pass
    
    new_report = {
        "id": str(max_id + 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "pending",
        "format": "pdf",
        "download_count": 0,
        **report_data
    }
    
    if 'reports' not in db.data:
        db.data['reports'] = []
    
    db.data['reports'].append(new_report)
    db._mark_dirty()
    
    return new_report


@router.put("/{report_id}")
async def update_report(report_id: str, update_data: dict):
    """更新报告"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    for i, report in enumerate(reports):
        if report['id'] == report_id:
            db.data['reports'][i].update(update_data)
            db.data['reports'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return db.data['reports'][i]
    
    raise HTTPException(status_code=404, detail="报告不存在")


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """删除报告"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    db.data['reports'] = [r for r in reports if r['id'] != report_id]
    db._mark_dirty()
    
    return {"message": "报告已删除"}


@router.post("/{report_id}/generate")
async def generate_report(report_id: str):
    """生成报告"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    for i, report in enumerate(reports):
        if report['id'] == report_id:
            db.data['reports'][i]['status'] = 'generating'
            db.data['reports'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return {"message": "报告生成中", "report": db.data['reports'][i]}
    
    raise HTTPException(status_code=404, detail="报告不存在")


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """下载报告"""
    
    db = get_database()
    reports = db.data.get('reports', [])
    
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
        
    if report.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="报告未生成完成")
    
    # 增加下载次数
    for i, r in enumerate(reports):
        if r['id'] == report_id:
            db.data['reports'][i]['download_count'] = r.get('download_count', 0) + 1
            db._mark_dirty()
            break
    
    return {
        "download_url": f"/files/reports/{report_id}.{report.get('format', 'pdf')}",
        "filename": f"{report.get('title', 'report')}.{report.get('format', 'pdf')}",
        "content_type": f"application/{report.get('format', 'pdf')}"
    }
