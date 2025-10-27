from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_database
from app.core.deps import get_current_user
from app.api.models.user import User

router = APIRouter()
security = HTTPBearer()


class SettingsResponse(BaseModel):
    general: Dict[str, Any]
    security: Dict[str, Any]
    notifications: Dict[str, Any]
    scanning: Dict[str, Any]
    integrations: Dict[str, Any]
    system: Dict[str, Any]


class SettingsUpdate(BaseModel):
    category: str
    settings: Dict[str, Any]


# Default settings structure
DEFAULT_SETTINGS = {
    "general": {
        "platform_name": "SOC Platform",
        "platform_description": "Enterprise Security Operations Center",
        "default_language": "zh",
        "timezone": "Asia/Shanghai",
        "default_page_size": 20
    },
    "security": {
        "min_password_length": 8,
        "password_requirements": ["lowercase", "numbers"],
        "password_expiry_days": 90,
        "session_timeout": 120,
        "max_concurrent_sessions": 3,
        "enable_login_lockout": True,
        "login_failure_threshold": 5,
        "lockout_duration": 15,
        "enable_two_factor": False
    },
    "notifications": {
        "email_enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "sender_email": "",
        "sender_password": "",
        "smtp_tls": True,
        "new_vulnerability_notification": ["email"],
        "task_completed_notification": ["email"],
        "system_alert_notification": ["email", "slack"]
    },
    "scanning": {
        "max_concurrent_tasks": 3,
        "default_timeout": 300,
        "max_retries": 2,
        "nmap_path": "/usr/bin/nmap",
        "nuclei_path": "/usr/bin/nuclei",
        "xray_path": "/usr/bin/xray",
        "auto_cleanup": True,
        "cleanup_days": 30,
        "enable_proxy": False,
        "proxy_url": ""
    },
    "integrations": {
        "fofa_enabled": False,
        "fofa_api_key": "",
        "fofa_email": "",
        "slack_enabled": False,
        "slack_webhook_url": "",
        "slack_channel": "#security",
        "webhook_enabled": False,
        "webhook_url": "",
        "webhook_token": ""
    },
    "system": {
        "db_pool_size": 10,
        "db_query_timeout": 30,
        "cache_enabled": True,
        "cache_ttl": 300,
        "log_level": "INFO",
        "log_retention_days": 90,
        "worker_processes": 4,
        "rate_limit_rpm": 600
    }
}


@router.get("/", response_model=SettingsResponse)
async def get_settings(current_user: User = Depends(get_current_user)):
    """Get all system settings"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view settings"
        )

    # In a real implementation, you would load settings from database
    # For now, return default settings
    return SettingsResponse(
        general=DEFAULT_SETTINGS["general"],
        security=DEFAULT_SETTINGS["security"],
        notifications=DEFAULT_SETTINGS["notifications"],
        scanning=DEFAULT_SETTINGS["scanning"],
        integrations=DEFAULT_SETTINGS["integrations"],
        system=DEFAULT_SETTINGS["system"]
    )


@router.get("/{category}")
async def get_settings_category(
    category: str,
    current_user: User = Depends(get_current_user)
):
    """Get settings for a specific category"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view settings"
        )

    if category not in DEFAULT_SETTINGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings category '{category}' not found"
        )

    return {"category": category, "settings": DEFAULT_SETTINGS[category]}


@router.put("/{category}")
async def update_settings_category(
    category: str,
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update settings for a specific category"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can modify settings"
        )

    if category not in DEFAULT_SETTINGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings category '{category}' not found"
        )

    # In a real implementation, you would validate and save to database
    # For now, just return success
    return {
        "message": f"Settings for category '{category}' updated successfully",
        "category": category,
        "updated_settings": settings_data
    }


@router.post("/test-notification")
async def test_notification(
    current_user: User = Depends(get_current_user)
):
    """Test notification configuration"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test notifications"
        )

    # In a real implementation, you would send a test notification
    return {"message": "Test notification sent successfully"}


@router.post("/test-integrations")
async def test_integrations(
    current_user: User = Depends(get_current_user)
):
    """Test integration configurations"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can test integrations"
        )

    # In a real implementation, you would test each enabled integration
    results = {
        "fofa": {"status": "success", "message": "Connection successful"},
        "slack": {"status": "success", "message": "Webhook test successful"},
        "webhook": {"status": "success", "message": "Webhook endpoint reachable"}
    }

    return {"message": "Integration tests completed", "results": results}


@router.post("/restart-services")
async def restart_services(
    current_user: User = Depends(get_current_user)
):
    """Restart system services"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can restart services"
        )

    # In a real implementation, you would restart the relevant services
    # This is a dangerous operation and should be handled carefully
    return {"message": "Service restart initiated"}


@router.get("/backup/list")
async def list_backups(
    current_user: User = Depends(get_current_user)
):
    """List available backups"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage backups"
        )

    # Mock backup list
    backups = [
        {
            "id": "backup-20231201",
            "name": "backup-2023-12-01.zip",
            "size": "156 MB",
            "created_at": "2023-12-01T02:00:00Z",
            "type": "automatic"
        },
        {
            "id": "backup-20231130",
            "name": "backup-2023-11-30.zip",
            "size": "152 MB",
            "created_at": "2023-11-30T02:00:00Z",
            "type": "automatic"
        }
    ]

    return {"backups": backups}


@router.post("/backup/create")
async def create_backup(
    current_user: User = Depends(get_current_user)
):
    """Create a new backup"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create backups"
        )

    # In a real implementation, you would trigger the backup process
    from datetime import datetime
    backup_id = f"backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return {
        "message": "Backup creation initiated",
        "backup_id": backup_id,
        "status": "in_progress"
    }


@router.get("/backup/{backup_id}/download")
async def download_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download a backup file"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can download backups"
        )

    # In a real implementation, you would return the actual file
    return {"download_url": f"/api/v1/backups/{backup_id}/file"}


@router.post("/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user)
):
    """Restore from a backup"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can restore backups"
        )

    # This is a dangerous operation - in real implementation,
    # you would have additional safeguards and confirmations
    return {
        "message": f"Restore from backup {backup_id} initiated",
        "backup_id": backup_id,
        "status": "in_progress"
    }


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a backup"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete backups"
        )

    return {"message": f"Backup {backup_id} deleted successfully"}


@router.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get system logs with filtering"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view logs"
        )

    # Mock log entries
    logs = [
        {
            "id": "log-001",
            "timestamp": "2023-12-01T10:30:15Z",
            "level": "INFO",
            "message": "User logged in successfully",
            "source": "auth",
            "user_id": str(current_user.id)
        },
        {
            "id": "log-002",
            "timestamp": "2023-12-01T10:25:33Z",
            "level": "WARNING",
            "message": "Scan task timeout",
            "source": "scanner",
            "task_id": "task-123"
        },
        {
            "id": "log-003",
            "timestamp": "2023-12-01T10:20:42Z",
            "level": "ERROR",
            "message": "Database connection failed",
            "source": "database",
            "error_code": "DB_CONN_001"
        }
    ]

    # Apply filters (mock implementation)
    if level:
        logs = [log for log in logs if log["level"] == level.upper()]

    total = len(logs)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_logs = logs[start_idx:end_idx]

    return {
        "logs": paginated_logs,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.delete("/logs")
async def clear_logs(
    current_user: User = Depends(get_current_user)
):
    """Clear all system logs"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can clear logs"
        )

    # In a real implementation, you would clear the log database
    return {"message": "System logs cleared successfully"}


@router.get("/logs/export")
async def export_logs(
    format: str = "json",
    level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Export system logs"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to export logs"
        )

    supported_formats = ["json", "csv", "txt"]
    if format not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format. Supported formats: {', '.join(supported_formats)}"
        )

    # In a real implementation, you would generate and return the file
    return {
        "message": f"Log export initiated in {format} format",
        "download_url": f"/api/v1/logs/download/{format}"
    }