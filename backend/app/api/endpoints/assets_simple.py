from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import json

from app.core.database_simple import get_database
from app.core.logging import get_logger
from app.models.response import create_paginated_response, create_success_response, create_error_response

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=10000),
    search: str = Query(""),
    asset_type: str = Query(""),
    status: str = Query("")
):
    """获取资产列表"""

    db = get_database()
    assets = db.data.get('assets', [])

    # 应用过滤器
    if search:
        assets = [a for a in assets if
                  search.lower() in a.get('name', '').lower() or
                  search.lower() in a.get('value', '').lower() or
                  search.lower() in a.get('description', '').lower()]

    if asset_type:
        assets = [a for a in assets if a.get('type') == asset_type]

    if status:
        assets = [a for a in assets if a.get('status') == status]

    # 分页
    total = len(assets)
    start = skip
    end = start + limit
    paginated_assets = assets[start:end]

    # 确保返回的数据结构与前端期望一致
    for asset in paginated_assets:
        if 'asset_type' not in asset and 'type' in asset:
            asset['asset_type'] = asset['type']
        if 'open_ports' not in asset:
            asset['open_ports'] = []
        if 'vulnerability_count' not in asset:
            asset['vulnerability_count'] = 0
        if 'last_scan' not in asset:
            asset['last_scan'] = asset.get('created_at')

    return {
        "items": paginated_assets,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
async def get_asset_stats():
    """获取资产统计信息"""
    
    db = get_database()
    assets = db.data.get('assets', [])
    
    # 计算统计信息
    total = len(assets)
    
    type_counts = {}
    status_counts = {"active": 0, "inactive": 0, "maintenance": 0}
    risk_counts = {"high": 0, "medium": 0, "low": 0}
    
    for asset in assets:
        asset_type = asset.get('type', 'unknown')
        status = asset.get('status', 'unknown')
        risk = asset.get('risk_level', 'low')
        
        type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
        if status in status_counts:
            status_counts[status] += 1
        if risk in risk_counts:
            risk_counts[risk] += 1
    
    return {
        "total_assets": total,
        "assets_by_type": type_counts,
        "assets_by_status": status_counts,
        "assets_by_risk": risk_counts,
        "recent_scans": total
    }


@router.get("/{asset_id}")
async def get_asset(asset_id: str):
    """获取单个资产详情"""
    
    db = get_database()
    assets = db.data.get('assets', [])
    
    asset = next((a for a in assets if a['id'] == asset_id), None)
    
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    return asset


@router.post("/")
async def create_asset(asset_data: dict):
    """创建新资产"""

    db = get_database()
    current_time = datetime.now()

    # 生成新ID
    max_id = 0
    for asset in db.data.get('assets', []):
        try:
            max_id = max(max_id, int(asset['id']))
        except:
            pass

    new_asset = {
        "id": str(max_id + 1),
        "created_at": current_time.isoformat(),
        "updated_at": current_time.isoformat(),
        "status": "active",
        "risk_level": "medium",
        "asset_type": asset_data.get('type', 'domain'),
        "open_ports": [],
        "vulnerability_count": 0,
        "last_scan": None,
        **asset_data
    }

    if 'assets' not in db.data:
        db.data['assets'] = []

    db.data['assets'].append(new_asset)
    db._mark_dirty()

    logger.info(f"Created new asset: {new_asset['name']} (ID: {new_asset['id']})")

    return new_asset


@router.put("/{asset_id}")
async def update_asset(asset_id: str, update_data: dict):
    """更新资产"""
    
    db = get_database()
    assets = db.data.get('assets', [])
    
    for i, asset in enumerate(assets):
        if asset['id'] == asset_id:
            db.data['assets'][i].update(update_data)
            db.data['assets'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            return db.data['assets'][i]
    
    raise HTTPException(status_code=404, detail="资产不存在")


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    """删除资产"""

    db = get_database()
    assets = db.data.get('assets', [])

    original_count = len(assets)
    db.data['assets'] = [a for a in assets if a['id'] != asset_id]

    if len(db.data['assets']) < original_count:
        db.save_data()
        logger.info(f"Deleted asset with ID: {asset_id}")
        return {"message": "资产已删除"}
    else:
        raise HTTPException(status_code=404, detail="资产不存在")


@router.post("/bulk")
async def bulk_create_assets(data: dict):
    """批量创建资产"""

    db = get_database()
    assets_data = data.get('assets', [])

    if not assets_data:
        raise HTTPException(status_code=400, detail="没有提供资产数据")

    created_assets = []
    current_time = datetime.now()

    # 获取当前最大ID
    max_id = 0
    for asset in db.data.get('assets', []):
        try:
            max_id = max(max_id, int(asset['id']))
        except:
            pass

    for asset_data in assets_data:
        max_id += 1
        new_asset = {
            "id": str(max_id),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "status": "active",
            "risk_level": "medium",
            "asset_type": asset_data.get('type', 'domain'),
            "open_ports": [],
            "vulnerability_count": 0,
            "last_scan": None,
            **asset_data
        }
        created_assets.append(new_asset)

    if 'assets' not in db.data:
        db.data['assets'] = []

    db.data['assets'].extend(created_assets)
    db.save_data()

    logger.info(f"Bulk created {len(created_assets)} assets")

    return {"data": created_assets, "count": len(created_assets)}


@router.delete("/bulk")
async def bulk_delete_assets(data: dict):
    """批量删除资产"""

    db = get_database()
    ids = data.get('ids', [])

    if not ids:
        raise HTTPException(status_code=400, detail="没有提供要删除的资产ID")

    original_count = len(db.data.get('assets', []))
    db.data['assets'] = [a for a in db.data.get('assets', []) if a['id'] not in ids]
    deleted_count = original_count - len(db.data['assets'])

    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="没有找到要删除的资产")

    db.save_data()
    logger.info(f"Bulk deleted {deleted_count} assets")

    return {"message": f"已删除 {deleted_count} 个资产"}


@router.post("/{asset_id}/scan")
async def scan_asset(asset_id: str):
    """扫描单个资产"""

    db = get_database()
    assets = db.data.get('assets', [])

    asset = next((a for a in assets if a['id'] == asset_id), None)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")

    # 更新最后扫描时间
    current_time = datetime.now()
    for i, a in enumerate(assets):
        if a['id'] == asset_id:
            db.data['assets'][i]['last_scan'] = current_time.isoformat()
            db.data['assets'][i]['updated_at'] = current_time.isoformat()
            break

    # 创建扫描任务
    if 'tasks' not in db.data:
        db.data['tasks'] = []

    # 生成新任务ID
    max_id = 0
    for task in db.data.get('tasks', []):
        try:
            max_id = max(max_id, int(task['id']))
        except:
            pass

    # 获取资产值用于目标
    asset_target = asset.get('value') or asset.get('domain') or asset.get('ip_address') or asset.get('url') or asset.get('name', 'Unknown')

    new_task = {
        "id": str(max_id + 1),
        "name": f"{asset['name']} - 资产扫描",
        "description": f"对资产 {asset['name']} 进行安全扫描",
        "type": "asset_scan",
        "status": "running",
        "priority": "medium",
        "target": asset_target,
        "target_assets": [asset_id],
        "progress": 0,
        "started_at": current_time.isoformat(),
        "estimated_completion": (current_time + timedelta(minutes=30)).isoformat(),
        "created_at": current_time.isoformat(),
        "updated_at": current_time.isoformat(),
        "created_by": "1",
        "assigned_to": "1",
        "tags": ["asset", "scan", "automated"]
    }

    db.data['tasks'].append(new_task)
    db.save_data()

    logger.info(f"Created scan task for asset: {asset['name']} (ID: {asset_id}, Task ID: {new_task['id']})")

    return {"message": "扫描任务已启动", "asset_id": asset_id, "task_id": new_task['id']}


@router.post("/bulk-scan")
async def bulk_scan_assets(data: dict):
    """批量扫描资产"""

    db = get_database()
    ids = data.get('ids', [])

    if not ids:
        raise HTTPException(status_code=400, detail="没有提供要扫描的资产ID")

    assets = db.data.get('assets', [])
    current_time = datetime.now()
    updated_count = 0

    # 确保任务数据存在
    if 'tasks' not in db.data:
        db.data['tasks'] = []

    # 获取当前最大任务ID
    max_id = 0
    for task in db.data.get('tasks', []):
        try:
            max_id = max(max_id, int(task['id']))
        except:
            pass

    # 收集要扫描的资产信息
    scan_assets = []
    for i, asset in enumerate(assets):
        if asset['id'] in ids:
            db.data['assets'][i]['last_scan'] = current_time.isoformat()
            db.data['assets'][i]['updated_at'] = current_time.isoformat()
            scan_assets.append(asset)
            updated_count += 1

    # 创建批量扫描任务
    if scan_assets:
        max_id += 1
        asset_names = [asset['name'] for asset in scan_assets]
        asset_targets = []
        for asset in scan_assets:
            target = asset.get('value') or asset.get('domain') or asset.get('ip_address') or asset.get('url') or asset.get('name', 'Unknown')
            asset_targets.append(target)

        new_task = {
            "id": str(max_id),
            "name": f"批量扫描 - {len(scan_assets)}个资产",
            "description": f"批量扫描资产: {', '.join(asset_names[:3])}" + (f" 等{len(asset_names)}个资产" if len(asset_names) > 3 else ""),
            "type": "bulk_asset_scan",
            "status": "running",
            "priority": "medium",
            "target": ', '.join(asset_targets),
            "target_assets": ids,
            "progress": 0,
            "started_at": current_time.isoformat(),
            "estimated_completion": (current_time + timedelta(minutes=60)).isoformat(),
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "created_by": "1",
            "assigned_to": "1",
            "tags": ["bulk", "asset", "scan", "automated"]
        }

        db.data['tasks'].append(new_task)

    db.save_data()
    logger.info(f"Created bulk scan task for {updated_count} assets")

    return {"message": f"已启动 {updated_count} 个资产的扫描任务", "task_id": str(max_id) if scan_assets else None}
