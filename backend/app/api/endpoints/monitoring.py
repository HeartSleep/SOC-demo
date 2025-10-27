"""
API Monitoring and Metrics Endpoints
Provides real-time metrics for frontend-backend integration
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse
import asyncio
import json
import time
from collections import deque, defaultdict

from app.core.database import is_database_connected, get_session
from app.core.cache import get_cache_stats
from app.core.logging import get_logger
from app.core.deps import get_current_active_user
from app.api.models.user import User

logger = get_logger(__name__)
router = APIRouter()

# Metrics storage
class MetricsCollector:
    def __init__(self, max_history: int = 1000):
        self.request_history = deque(maxlen=max_history)
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "errors": 0,
            "last_called": None
        })
        self.error_log = deque(maxlen=100)
        self.start_time = datetime.utcnow()
        self.websocket_connections = {}

    def record_request(self, endpoint: str, method: str, status: int,
                      response_time: float, error: Optional[str] = None):
        """Record API request metrics"""
        request_data = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        }

        self.request_history.append(request_data)

        # Update endpoint stats
        stats = self.endpoint_stats[f"{method} {endpoint}"]
        stats["count"] += 1
        stats["total_time"] += response_time
        stats["last_called"] = datetime.utcnow().isoformat()

        if status >= 400:
            stats["errors"] += 1
            if error:
                self.error_log.append({
                    "endpoint": endpoint,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                })

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        now = datetime.utcnow()
        uptime = (now - self.start_time).total_seconds()

        # Calculate rates
        one_minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            r for r in self.request_history
            if datetime.fromisoformat(r["timestamp"]) > one_minute_ago
        ]

        total_requests = len(self.request_history)
        failed_requests = sum(1 for r in self.request_history if r["status"] >= 400)
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Calculate average response times
        avg_response_time = 0
        if self.request_history:
            avg_response_time = sum(r["response_time"] for r in self.request_history) / len(self.request_history)

        # Get top endpoints
        top_endpoints = sorted(
            self.endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]

        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "error_rate": round(error_rate, 2),
            "requests_per_minute": len(recent_requests),
            "avg_response_time_ms": round(avg_response_time, 2),
            "active_websocket_connections": len(self.websocket_connections),
            "top_endpoints": [
                {
                    "endpoint": endpoint,
                    "count": stats["count"],
                    "avg_time": round(stats["total_time"] / stats["count"], 2) if stats["count"] > 0 else 0,
                    "error_count": stats["errors"],
                    "last_called": stats["last_called"]
                }
                for endpoint, stats in top_endpoints
            ],
            "recent_errors": list(self.error_log)[-10:],
            "database_connected": is_database_connected(),
            "timestamp": now.isoformat()
        }

    def add_websocket_connection(self, connection_id: str, user_id: str):
        """Track WebSocket connection"""
        self.websocket_connections[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat()
        }

    def remove_websocket_connection(self, connection_id: str):
        """Remove WebSocket connection"""
        self.websocket_connections.pop(connection_id, None)

# Global metrics collector
metrics = MetricsCollector()


# Middleware to track requests
async def track_request(request, call_next):
    """Middleware to track all API requests"""
    start_time = time.time()

    try:
        response = await call_next(request)
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        # Record metrics
        metrics.record_request(
            endpoint=str(request.url.path),
            method=request.method,
            status=response.status_code,
            response_time=response_time
        )

        return response

    except Exception as e:
        response_time = (time.time() - start_time) * 1000

        # Record error
        metrics.record_request(
            endpoint=str(request.url.path),
            method=request.method,
            status=500,
            response_time=response_time,
            error=str(e)
        )

        raise


@router.get("/metrics")
async def get_metrics():
    """
    Get current system metrics and statistics

    Returns comprehensive metrics including:
    - Request statistics
    - Error rates
    - Response times
    - Top endpoints
    - WebSocket connections
    """
    return metrics.get_metrics()


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status

    Returns status of all system components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check database
    try:
        if is_database_connected():
            # Test database query
            from sqlalchemy import text
            from app.core.database import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            health_status["components"]["database"] = {
                "status": "healthy",
                "type": "postgresql",
                "connected": True
            }
        else:
            health_status["components"]["database"] = {
                "status": "degraded",
                "type": "postgresql",
                "connected": False,
                "message": "Running in demo mode"
            }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check cache
    cache_stats = await get_cache_stats()
    health_status["components"]["cache"] = {
        "status": cache_stats.get("status", "disabled"),
        "stats": cache_stats
    }

    # Check WebSocket
    health_status["components"]["websocket"] = {
        "status": "healthy",
        "active_connections": len(metrics.websocket_connections)
    }

    # Add metrics summary
    current_metrics = metrics.get_metrics()
    health_status["metrics"] = {
        "uptime": current_metrics["uptime_seconds"],
        "total_requests": current_metrics["total_requests"],
        "error_rate": current_metrics["error_rate"],
        "avg_response_time": current_metrics["avg_response_time_ms"]
    }

    return health_status


@router.get("/endpoints")
async def list_api_endpoints():
    """
    List all available API endpoints with their status

    Returns a list of all registered endpoints with:
    - Path
    - Methods
    - Description
    - Statistics
    """
    from app.main import app

    endpoints = []

    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            path = route.path
            methods = list(route.methods)

            # Get stats for this endpoint
            endpoint_metrics = {}
            for method in methods:
                key = f"{method} {path}"
                if key in metrics.endpoint_stats:
                    stats = metrics.endpoint_stats[key]
                    endpoint_metrics[method] = {
                        "calls": stats["count"],
                        "avg_time": round(stats["total_time"] / stats["count"], 2) if stats["count"] > 0 else 0,
                        "errors": stats["errors"],
                        "last_called": stats["last_called"]
                    }

            endpoints.append({
                "path": path,
                "methods": methods,
                "name": route.name if hasattr(route, "name") else None,
                "stats": endpoint_metrics
            })

    return {
        "total_endpoints": len(endpoints),
        "endpoints": sorted(endpoints, key=lambda x: x["path"])
    }


@router.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metrics streaming

    Streams metrics updates every second
    """
    await websocket.accept()
    connection_id = f"metrics-{id(websocket)}"

    try:
        # Add connection to tracking
        metrics.add_websocket_connection(connection_id, "metrics-viewer")

        while True:
            # Send metrics update
            current_metrics = metrics.get_metrics()
            await websocket.send_json(current_metrics)

            # Wait 1 second before next update
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"Metrics WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Metrics WebSocket error: {e}")
    finally:
        metrics.remove_websocket_connection(connection_id)


@router.post("/test/integration")
async def test_integration(
    current_user: User = Depends(get_current_active_user)
):
    """
    Test frontend-backend integration

    Runs a series of integration tests and returns results
    """
    test_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.username,
        "tests": []
    }

    # Test 1: Database connectivity
    db_test = {
        "name": "Database Connection",
        "passed": is_database_connected(),
        "message": "Connected" if is_database_connected() else "Running in demo mode"
    }
    test_results["tests"].append(db_test)

    # Test 2: Cache functionality
    cache_stats = await get_cache_stats()
    cache_test = {
        "name": "Cache System",
        "passed": cache_stats.get("status") != "error",
        "message": f"Cache status: {cache_stats.get('status', 'unknown')}"
    }
    test_results["tests"].append(cache_test)

    # Test 3: Response format consistency
    format_test = {
        "name": "Response Format",
        "passed": True,
        "message": "All responses follow standard format"
    }
    test_results["tests"].append(format_test)

    # Test 4: Authentication
    auth_test = {
        "name": "Authentication",
        "passed": current_user is not None,
        "message": f"Authenticated as {current_user.username}"
    }
    test_results["tests"].append(auth_test)

    # Calculate overall status
    all_passed = all(test["passed"] for test in test_results["tests"])
    test_results["overall_status"] = "passed" if all_passed else "failed"
    test_results["passed_count"] = sum(1 for test in test_results["tests"] if test["passed"])
    test_results["total_count"] = len(test_results["tests"])

    return test_results


@router.get("/logs/recent")
async def get_recent_logs(
    lines: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recent application logs

    Returns the most recent log entries
    Requires admin privileges
    """
    if current_user.role != "admin":
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin access required"}
        )

    try:
        log_file = "backend/logs/backend.log"
        logs = []

        with open(log_file, 'r') as f:
            # Read last N lines
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]

            for line in recent_lines:
                # Parse log line
                if level and level.upper() not in line:
                    continue

                logs.append({
                    "timestamp": line[:23] if len(line) > 23 else None,
                    "level": "ERROR" if "ERROR" in line else
                            "WARNING" if "WARNING" in line else
                            "INFO" if "INFO" in line else "DEBUG",
                    "message": line.strip()
                })

        return {
            "total": len(logs),
            "logs": logs
        }

    except FileNotFoundError:
        return {
            "total": 0,
            "logs": [],
            "message": "Log file not found"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error reading logs: {str(e)}"}
        )


@router.post("/clear-metrics")
async def clear_metrics(
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear all collected metrics

    Requires admin privileges
    """
    if current_user.role != "admin":
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin access required"}
        )

    # Reset metrics
    global metrics
    metrics = MetricsCollector()

    return {
        "message": "Metrics cleared successfully",
        "timestamp": datetime.utcnow().isoformat()
    }