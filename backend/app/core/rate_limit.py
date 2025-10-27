"""
Rate Limiting Configuration
Provides rate limiting functionality using SlowAPI and Redis
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import get_logger
import redis

logger = get_logger(__name__)

# Initialize Redis connection for rate limiting
try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info("Redis connected for rate limiting")
except Exception as e:
    logger.warning(f"Redis connection failed for rate limiting: {e}")
    redis_client = None


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses user ID if authenticated, otherwise uses IP address.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    storage_uri=settings.REDIS_URL if redis_client else None,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    enabled=settings.RATE_LIMIT_ENABLED,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns 429 Too Many Requests with retry-after header.
    """
    logger.warning(
        f"Rate limit exceeded for {get_identifier(request)} - "
        f"Path: {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail)
        },
        headers={
            "Retry-After": str(exc.detail.split()[-1]),
            "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(exc.detail.split()[-1])
        }
    )


def get_rate_limit_headers(request: Request) -> dict:
    """
    Get current rate limit status headers.
    """
    try:
        if redis_client and settings.RATE_LIMIT_ENABLED:
            identifier = get_identifier(request)
            # Get current usage from Redis
            key = f"slowapi:{identifier}"
            current = redis_client.get(key)
            remaining = max(0, settings.RATE_LIMIT_PER_MINUTE - int(current or 0))

            return {
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                "X-RateLimit-Remaining": str(remaining),
            }
    except Exception as e:
        logger.debug(f"Failed to get rate limit headers: {e}")

    return {}


# Decorator for custom rate limits on specific endpoints
def custom_rate_limit(limit: str):
    """
    Decorator for applying custom rate limits to specific endpoints.

    Usage:
        @router.post("/login")
        @custom_rate_limit("5/minute")
        async def login(...)
    """
    return limiter.limit(limit)