from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
import json

from app.core.database_simple import get_database
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query("")
):
    """获取用户列表"""
    
    db = get_database()
    current_time = datetime.now()
    
    # 确保用户数据存在
    if not db.data.get('users'):
        demo_users = [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "系统管理员",
                "role": "admin",
                "department": "信息安全部",
                "is_active": True,
                "is_superuser": True,
                "last_login": current_time.isoformat(),
                "created_at": (current_time - datetime.now().replace(day=1)).isoformat(),
                "updated_at": current_time.isoformat(),
                "permissions": ["admin:all", "user:read", "user:write", "vulnerability:all"]
            },
            {
                "id": "2", 
                "username": "security_analyst",
                "email": "analyst@example.com",
                "full_name": "安全分析师",
                "role": "analyst",
                "department": "信息安全部",
                "is_active": True,
                "is_superuser": False,
                "last_login": (current_time - datetime.now().replace(hour=2)).isoformat(),
                "created_at": (current_time - datetime.now().replace(day=15)).isoformat(),
                "updated_at": current_time.isoformat(),
                "permissions": ["vulnerability:read", "vulnerability:write", "asset:read"]
            },
            {
                "id": "3",
                "username": "auditor", 
                "email": "auditor@example.com",
                "full_name": "安全审计员",
                "role": "auditor",
                "department": "审计部",
                "is_active": True,
                "is_superuser": False,
                "last_login": (current_time - datetime.now().replace(day=1)).isoformat(),
                "created_at": (current_time - datetime.now().replace(month=1)).isoformat(),
                "updated_at": current_time.isoformat(),
                "permissions": ["vulnerability:read", "asset:read", "report:read"]
            }
        ]
        
        db.data['users'] = demo_users
        db._mark_dirty()
    
    users = db.data['users']
    
    # 应用搜索过滤器
    if search:
        users = [u for u in users if 
                 search.lower() in u.get('username', '').lower() or 
                 search.lower() in u.get('full_name', '').lower() or
                 search.lower() in u.get('email', '').lower()]
    
    # 分页
    total = len(users)
    start = (page - 1) * limit
    end = start + limit
    paginated_users = users[start:end]
    
    # 移除敏感信息
    safe_users = []
    for user in paginated_users:
        safe_user = {k: v for k, v in user.items() if k != 'password'}
        safe_users.append(safe_user)
    
    return {
        "data": safe_users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_user_stats():
    """获取用户统计信息"""
    
    db = get_database()
    users = db.data.get('users', [])
    
    total = len(users)
    active_users = len([u for u in users if u.get('is_active', False)])
    
    role_counts = {}
    for user in users:
        role = user.get('role', 'user')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    return {
        "total_users": total,
        "active_users": active_users,
        "users_by_role": role_counts,
        "recent_logins": active_users  # 简化统计
    }


@router.get("/{user_id}")
async def get_user(user_id: str):
    """获取单个用户详情"""
    
    db = get_database()
    users = db.data.get('users', [])
    
    user = next((u for u in users if u['id'] == user_id), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 移除密码等敏感信息
    safe_user = {k: v for k, v in user.items() if k != 'password'}
    return safe_user


@router.post("/")
async def create_user(user_data: dict):
    """创建新用户"""
    
    db = get_database()
    
    # 检查用户名是否已存在
    existing_users = db.data.get('users', [])
    if any(u['username'] == user_data.get('username') for u in existing_users):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 生成新ID
    max_id = 0
    for user in existing_users:
        try:
            max_id = max(max_id, int(user['id']))
        except:
            pass
    
    new_user = {
        "id": str(max_id + 1),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True,
        "is_superuser": False,
        "role": "user",
        **user_data
    }
    
    if 'users' not in db.data:
        db.data['users'] = []
    
    db.data['users'].append(new_user)
    db._mark_dirty()
    
    # 返回时移除密码
    safe_user = {k: v for k, v in new_user.items() if k != 'password'}
    return safe_user


@router.put("/{user_id}")
async def update_user(user_id: str, update_data: dict):
    """更新用户"""
    
    db = get_database()
    users = db.data.get('users', [])
    
    for i, user in enumerate(users):
        if user['id'] == user_id:
            db.data['users'][i].update(update_data)
            db.data['users'][i]['updated_at'] = datetime.now().isoformat()
            db._mark_dirty()
            
            # 返回时移除密码
            safe_user = {k: v for k, v in db.data['users'][i].items() if k != 'password'}
            return safe_user
    
    raise HTTPException(status_code=404, detail="用户不存在")


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """删除用户"""
    
    db = get_database()
    users = db.data.get('users', [])
    
    db.data['users'] = [u for u in users if u['id'] != user_id]
    db._mark_dirty()
    
    return {"message": "用户已删除"}
