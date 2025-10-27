"""
Performance Monitoring Utilities
Provides tools for tracking and measuring application performance
"""
import time
import asyncio
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import asynccontextmanager
from datetime import datetime
import psutil

from app.core.logging import get_logger

logger = get_logger(__name__)


class PerformanceTimer:
    """
    Context manager for timing code execution.

    Usage:
        with PerformanceTimer("database_query"):
            result = await db.execute(query)
        # Logs: "database_query completed in 0.123s"

        # Or async:
        async with PerformanceTimer("api_call"):
            response = await client.get(url)
    """

    def __init__(self, name: str, log_level: str = "debug", threshold_ms: Optional[float] = None):
        """
        Args:
            name: Name of the operation being timed
            log_level: Log level for the timing message (debug, info, warning)
            threshold_ms: Only log if duration exceeds this threshold (in milliseconds)
        """
        self.name = name
        self.log_level = log_level
        self.threshold_ms = threshold_ms
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        self._log_duration()
        return False

    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        self._log_duration()
        return False

    def _log_duration(self):
        """Log the duration if it meets the threshold"""
        duration_ms = self.duration * 1000

        # Skip logging if below threshold
        if self.threshold_ms and duration_ms < self.threshold_ms:
            return

        message = f"{self.name} completed in {duration_ms:.2f}ms ({self.duration:.4f}s)"

        if self.log_level == "info":
            logger.info(message)
        elif self.log_level == "warning":
            logger.warning(message)
        else:
            logger.debug(message)

    def get_duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return self.duration * 1000 if self.duration else 0


def timeit(name: Optional[str] = None, log_level: str = "debug", threshold_ms: Optional[float] = None):
    """
    Decorator to measure function execution time.

    Usage:
        @timeit(name="expensive_operation", threshold_ms=100)
        async def expensive_function():
            await asyncio.sleep(0.5)

    Args:
        name: Operation name (defaults to function name)
        log_level: Log level for timing message
        threshold_ms: Only log if duration exceeds this threshold
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with PerformanceTimer(operation_name, log_level, threshold_ms):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with PerformanceTimer(operation_name, log_level, threshold_ms):
                    return func(*args, **kwargs)
            return sync_wrapper

    return decorator


class PerformanceMetrics:
    """
    Collect and aggregate performance metrics.

    Usage:
        metrics = PerformanceMetrics()
        metrics.record("api_call", 123.45)
        metrics.record("api_call", 98.76)
        stats = metrics.get_stats("api_call")
        # {"count": 2, "total": 222.21, "avg": 111.105, "min": 98.76, "max": 123.45}
    """

    def __init__(self):
        self._metrics: Dict[str, list] = {}

    def record(self, name: str, duration_ms: float):
        """Record a performance metric"""
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(duration_ms)

    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a metric"""
        if name not in self._metrics or not self._metrics[name]:
            return None

        values = self._metrics[name]
        return {
            "count": len(values),
            "total": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p50": self._percentile(values, 0.50),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all metrics"""
        return {name: self.get_stats(name) for name in self._metrics}

    def clear(self, name: Optional[str] = None):
        """Clear metrics (specific or all)"""
        if name:
            self._metrics.pop(name, None)
        else:
            self._metrics.clear()

    @staticmethod
    def _percentile(values: list, percentile: float) -> float:
        """Calculate percentile value"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]


# Global metrics instance
performance_metrics = PerformanceMetrics()


async def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system resource metrics.

    Returns:
        dict: CPU, memory, disk, and network metrics
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024 ** 3),
                "memory_available_gb": memory.available / (1024 ** 3),
                "memory_percent": memory.percent,
                "disk_total_gb": disk.total / (1024 ** 3),
                "disk_used_gb": disk.used / (1024 ** 3),
                "disk_percent": disk.percent,
            },
            "process": {
                "memory_rss_mb": process_memory.rss / (1024 ** 2),
                "memory_vms_mb": process_memory.vms / (1024 ** 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {"error": str(e)}


async def get_performance_summary() -> Dict[str, Any]:
    """
    Get comprehensive performance summary including system metrics and application metrics.

    Returns:
        dict: Complete performance summary
    """
    system_metrics = await get_system_metrics()
    app_metrics = performance_metrics.get_all_stats()

    return {
        "system": system_metrics,
        "metrics": app_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@asynccontextmanager
async def measure_performance(operation_name: str):
    """
    Async context manager that measures and records performance.

    Usage:
        async with measure_performance("database_query"):
            result = await db.execute(query)
    """
    timer = PerformanceTimer(operation_name)
    async with timer:
        yield timer
    performance_metrics.record(operation_name, timer.get_duration_ms())


# Convenience function for middleware
class PerformanceMiddleware:
    """
    Middleware to track request performance.

    Usage:
        from app.core.performance import PerformanceMiddleware

        @app.middleware("http")
        async def add_performance_tracking(request: Request, call_next):
            return await PerformanceMiddleware()(request, call_next)
    """

    async def __call__(self, request, call_next):
        """Track request performance"""
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time
        duration_ms = duration * 1000

        # Add performance header
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        # Record metric
        endpoint = f"{request.method} {request.url.path}"
        performance_metrics.record(endpoint, duration_ms)

        # Log slow requests
        if duration_ms > 1000:  # Over 1 second
            logger.warning(f"Slow request: {endpoint} took {duration_ms:.2f}ms")
        elif duration_ms > 500:  # Over 500ms
            logger.info(f"Request {endpoint} took {duration_ms:.2f}ms")

        return response