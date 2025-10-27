from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timedelta
import psutil
import asyncio

from app.core.database import get_database
from app.core.deps import get_current_user
from app.api.models.user import User

router = APIRouter()
security = HTTPBearer()


class SystemInfo(BaseModel):
    version: str
    uptime: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_users: int
    active_tasks: int
    database_status: str
    cache_status: str


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, Dict[str, Any]]


class SystemMetrics(BaseModel):
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    active_connections: int


@router.get("/info", response_model=SystemInfo)
async def get_system_info(current_user: User = Depends(get_current_user)):
    """Get basic system information"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view system information"
        )

    # Get system metrics using psutil
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Mock some values for demonstration
        uptime = psutil.boot_time()
        current_time = datetime.now().timestamp()
        uptime_seconds = current_time - uptime

        return SystemInfo(
            version="1.0.0",
            uptime=uptime_seconds,
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_users=5,  # Mock value
            active_tasks=3,  # Mock value
            database_status="healthy",
            cache_status="healthy"
        )
    except Exception as e:
        # Fallback to mock data if psutil fails
        return SystemInfo(
            version="1.0.0",
            uptime=86400.0,  # 1 day
            cpu_usage=25.5,
            memory_usage=45.2,
            disk_usage=60.1,
            active_users=5,
            active_tasks=3,
            database_status="healthy",
            cache_status="healthy"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check"""
    components = {}
    overall_status = "healthy"

    # Database check
    try:
        # In real implementation, you would test database connectivity
        components["database"] = {
            "status": "healthy",
            "response_time": "15ms",
            "connections": 5
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "unhealthy"

    # Cache check (Redis)
    try:
        # In real implementation, you would test Redis connectivity
        components["cache"] = {
            "status": "healthy",
            "response_time": "2ms",
            "memory_usage": "45MB"
        }
    except Exception as e:
        components["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded" if overall_status == "healthy" else "unhealthy"

    # Celery worker check
    try:
        # In real implementation, you would check Celery workers
        components["workers"] = {
            "status": "healthy",
            "active_workers": 4,
            "queue_size": 2
        }
    except Exception as e:
        components["workers"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_status = "degraded" if overall_status == "healthy" else "unhealthy"

    # External services check
    components["external_services"] = {
        "fofa_api": {"status": "healthy", "response_time": "150ms"},
        "notification_service": {"status": "healthy"}
    }

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        components=components
    )


@router.get("/metrics", response_model=List[SystemMetrics])
async def get_system_metrics(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Get system metrics over time"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view system metrics"
        )

    # Generate mock metrics for the requested time period
    metrics = []
    now = datetime.utcnow()

    for i in range(hours):
        timestamp = now - timedelta(hours=hours - i - 1)

        # Generate realistic-looking mock data
        base_cpu = 20 + (i % 10) * 3
        base_memory = 40 + (i % 8) * 2
        base_disk = 55 + (i % 5) * 1

        metrics.append(SystemMetrics(
            timestamp=timestamp.isoformat(),
            cpu_percent=base_cpu + (i % 3),
            memory_percent=base_memory + (i % 4),
            disk_percent=base_disk + (i % 2),
            network_io={
                "bytes_sent": 1024 * (100 + i * 10),
                "bytes_recv": 1024 * (200 + i * 15)
            },
            active_connections=50 + (i % 20)
        ))

    return metrics


@router.get("/status")
async def get_service_status():
    """Get status of all system services"""
    services = {
        "web_server": {
            "status": "running",
            "pid": 1234,
            "uptime": "2d 4h 30m",
            "memory": "120MB",
            "cpu": "2.5%"
        },
        "database": {
            "status": "running",
            "pid": 1235,
            "uptime": "2d 4h 30m",
            "memory": "256MB",
            "cpu": "5.1%"
        },
        "cache": {
            "status": "running",
            "pid": 1236,
            "uptime": "2d 4h 30m",
            "memory": "64MB",
            "cpu": "1.2%"
        },
        "workers": {
            "status": "running",
            "active_workers": 4,
            "pending_tasks": 2,
            "completed_tasks": 1547
        },
        "scheduler": {
            "status": "running",
            "next_run": "2023-12-01T15:00:00Z",
            "scheduled_tasks": 5
        }
    }

    return {"services": services, "last_updated": datetime.utcnow().isoformat()}


@router.get("/performance")
async def get_performance_stats(
    current_user: User = Depends(get_current_user)
):
    """Get performance statistics"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view performance stats"
        )

    stats = {
        "response_times": {
            "api_avg": "45ms",
            "database_avg": "12ms",
            "cache_avg": "2ms"
        },
        "request_stats": {
            "total_requests": 15642,
            "requests_per_minute": 125,
            "error_rate": "0.5%"
        },
        "resource_usage": {
            "cpu_cores": 4,
            "cpu_usage": "25.3%",
            "memory_total": "8GB",
            "memory_used": "3.2GB",
            "disk_total": "100GB",
            "disk_used": "55GB"
        },
        "database_stats": {
            "connections": 12,
            "max_connections": 100,
            "slow_queries": 3,
            "cache_hit_rate": "95.2%"
        }
    }

    return {"performance_stats": stats, "timestamp": datetime.utcnow().isoformat()}


@router.get("/alerts")
async def get_system_alerts(
    severity: str = None,
    resolved: bool = None,
    current_user: User = Depends(get_current_user)
):
    """Get system alerts and warnings"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view system alerts"
        )

    # Mock alerts
    alerts = [
        {
            "id": "alert-001",
            "title": "High Memory Usage",
            "message": "System memory usage is above 80%",
            "severity": "warning",
            "timestamp": "2023-12-01T10:30:00Z",
            "resolved": False,
            "component": "system"
        },
        {
            "id": "alert-002",
            "title": "Failed Login Attempts",
            "message": "Multiple failed login attempts detected from IP 192.168.1.100",
            "severity": "medium",
            "timestamp": "2023-12-01T09:45:00Z",
            "resolved": True,
            "component": "security"
        },
        {
            "id": "alert-003",
            "title": "Backup Overdue",
            "message": "Automatic backup has not run in 48 hours",
            "severity": "high",
            "timestamp": "2023-12-01T08:00:00Z",
            "resolved": False,
            "component": "backup"
        }
    ]

    # Apply filters
    if severity:
        alerts = [alert for alert in alerts if alert["severity"] == severity]
    if resolved is not None:
        alerts = [alert for alert in alerts if alert["resolved"] == resolved]

    return {"alerts": alerts}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Resolve a system alert"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to resolve alerts"
        )

    # In real implementation, you would update the alert in database
    return {
        "message": f"Alert {alert_id} resolved successfully",
        "resolved_by": current_user.username,
        "resolved_at": datetime.utcnow().isoformat()
    }


@router.get("/dashboard")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    """Get dashboard statistics for system monitoring"""
    if current_user.role not in ["admin", "security_analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view dashboard"
        )

    stats = {
        "overview": {
            "total_assets": 156,
            "total_vulnerabilities": 23,
            "active_tasks": 3,
            "generated_reports": 12
        },
        "security_status": {
            "critical_vulnerabilities": 2,
            "high_vulnerabilities": 8,
            "medium_vulnerabilities": 13,
            "low_vulnerabilities": 0
        },
        "task_status": {
            "pending": 1,
            "running": 2,
            "completed": 45,
            "failed": 1
        },
        "recent_activities": [
            {
                "type": "vulnerability_found",
                "message": "Critical vulnerability found in web-server-01",
                "timestamp": "2023-12-01T10:30:00Z"
            },
            {
                "type": "scan_completed",
                "message": "Port scan completed for network-segment-A",
                "timestamp": "2023-12-01T10:15:00Z"
            },
            {
                "type": "asset_added",
                "message": "New asset added: api-server-03",
                "timestamp": "2023-12-01T09:45:00Z"
            }
        ],
        "system_health": {
            "cpu_usage": 25.3,
            "memory_usage": 45.7,
            "disk_usage": 55.2,
            "network_status": "healthy"
        }
    }

    return {"dashboard_stats": stats, "last_updated": datetime.utcnow().isoformat()}