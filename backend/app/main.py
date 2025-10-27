from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database import init_database, close_database
from app.core.cache import init_cache, close_cache, get_cache_stats
from app.core.response import ORJSONResponse
from app.core.performance import PerformanceMiddleware, get_performance_summary
from app.core.rate_limit import limiter, rate_limit_exceeded_handler, get_rate_limit_headers
from app.core.csrf import CSRFProtectMiddleware, csrf_cookie_setter
from app.core.websocket import manager
from slowapi.errors import RateLimitExceeded
from app.api.endpoints import (
    auth,
    assets,
    tasks,
    vulnerabilities,
    reports,
    users,
    settings as settings_endpoints,
    system,
    api_security,
)

logger = get_logger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting SOC Security Platform v2.0...")

    # Initialize WebSocket manager Redis connection
    try:
        await manager.connect_redis()
        logger.info("WebSocket Redis connection initialized")
    except Exception as e:
        logger.warning(f"WebSocket Redis initialization failed: {e}")

    # Initialize database - don't fail startup if database is unavailable
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.info("Continuing in demo mode without database")

    # Initialize cache
    try:
        await init_cache()
        logger.info("Response cache initialized successfully")
    except Exception as e:
        logger.warning(f"Cache initialization failed: {e}")
        logger.info("Continuing without response caching")

    logger.info("All security features initialized:")
    logger.info(f"  - Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"  - CSRF Protection: Enabled")
    logger.info(f"  - MFA Support: {'Enabled' if settings.MFA_ENABLED else 'Disabled'}")
    logger.info(f"  - WebSocket Real-time: Enabled")
    logger.info(f"  - Connection Pooling: Enabled (size={settings.DB_POOL_SIZE})")

    yield

    # Cleanup
    try:
        await manager.disconnect_redis()
        logger.info("WebSocket Redis connections closed")
    except Exception as e:
        logger.warning(f"WebSocket cleanup failed: {e}")

    try:
        await close_cache()
        logger.info("Response cache closed")
    except Exception as e:
        logger.warning(f"Cache cleanup failed: {e}")

    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Database cleanup failed: {e}")

    logger.info("SOC Security Platform stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Security Testing Platform with Enhanced Security",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # Use orjson for 2-3x faster serialization
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# GZip Compression Middleware (apply first for best compression)
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-CSRF-Token"],
)

# CSRF Protection Middleware
if not settings.DEBUG:
    app.add_middleware(CSRFProtectMiddleware)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localdomain", "*"] if settings.DEBUG else ["localhost", "127.0.0.1"],
)


# Middleware to add rate limit headers and performance tracking
@app.middleware("http")
async def add_headers_and_performance(request: Request, call_next):
    # Track performance
    response = await PerformanceMiddleware()(request, call_next)

    # Add rate limit headers
    if settings.RATE_LIMIT_ENABLED:
        rate_headers = get_rate_limit_headers(request)
        for key, value in rate_headers.items():
            response.headers[key] = value

    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint with system status.

    Returns:
        dict: Health status and system information
    """
    cache_stats = await get_cache_stats()

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
            "mfa": settings.MFA_ENABLED,
            "websocket": True,
            "database": "postgresql",
            "caching": cache_stats.get("status", "disabled"),
        },
        "websocket": {
            "active_connections": manager.get_connection_count(),
            "active_users": len(manager.get_active_users()),
        },
        "cache": cache_stats
    }


# CSRF token endpoint
@app.get("/csrf-token")
async def get_csrf_token():
    """
    Get CSRF token for form submissions.

    Returns:
        JSONResponse: Response with CSRF token
    """
    response = JSONResponse(content={"message": "CSRF token generated"})
    return csrf_cookie_setter(response)


# Performance metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """
    Get performance metrics and system information.

    Returns:
        dict: Performance metrics including request timings and system resources
    """
    return await get_performance_summary()


# API Routes
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

app.include_router(
    assets.router,
    prefix=f"{settings.API_V1_STR}/assets",
    tags=["assets"]
)

app.include_router(
    tasks.router,
    prefix=f"{settings.API_V1_STR}/tasks",
    tags=["tasks"]
)

app.include_router(
    vulnerabilities.router,
    prefix=f"{settings.API_V1_STR}/vulnerabilities",
    tags=["vulnerabilities"]
)

app.include_router(
    reports.router,
    prefix=f"{settings.API_V1_STR}/reports",
    tags=["reports"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)

app.include_router(
    settings_endpoints.router,
    prefix=f"{settings.API_V1_STR}/settings",
    tags=["settings"]
)

app.include_router(
    system.router,
    prefix=f"{settings.API_V1_STR}/system",
    tags=["system"]
)

app.include_router(
    api_security.router,
    prefix=f"{settings.API_V1_STR}/api-security",
    tags=["api-security"]
)

# WebSocket routes
try:
    from app.api.endpoints import websocket_endpoint
    app.include_router(
        websocket_endpoint.router,
        prefix=f"{settings.API_V1_STR}",
        tags=["websocket"]
    )
except ImportError:
    logger.warning("WebSocket endpoint not available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )