"""
Response Caching Layer
Provides Redis-backed caching for expensive operations
"""
import pickle
import hashlib
import json
from typing import Optional, Any, Callable
from functools import wraps
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis client for caching
cache_redis: Optional[aioredis.Redis] = None


async def init_cache():
    """Initialize Redis cache connection"""
    global cache_redis
    try:
        cache_redis = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,  # We'll use pickle
            socket_connect_timeout=5
        )
        await cache_redis.ping()
        logger.info("Cache Redis connected")
        return cache_redis
    except Exception as e:
        logger.warning(f"Cache Redis connection failed: {e}")
        cache_redis = None
        return None


async def close_cache():
    """Close Redis cache connection"""
    global cache_redis
    if cache_redis:
        await cache_redis.close()
        logger.info("Cache Redis closed")


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments.

    Args:
        prefix: Cache key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        str: Cache key
    """
    # Create a deterministic key from arguments
    key_parts = [prefix]

    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # Hash complex objects
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

    # Add keyword args
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        for k, v in sorted_kwargs:
            key_parts.append(f"{k}={v}")

    return ":".join(key_parts)


async def get_cached(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None
    """
    if not cache_redis:
        return None

    try:
        cached = await cache_redis.get(key)
        if cached:
            logger.debug(f"Cache HIT: {key}")
            return pickle.loads(cached)
        logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 5 minutes)

    Returns:
        bool: Success status
    """
    if not cache_redis:
        return False

    try:
        serialized = pickle.dumps(value)
        await cache_redis.setex(key, ttl, serialized)
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key

    Returns:
        bool: Success status
    """
    if not cache_redis:
        return False

    try:
        await cache_redis.delete(key)
        logger.debug(f"Cache DELETE: {key}")
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {e}")
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """
    Clear all cache keys matching a pattern.

    Args:
        pattern: Pattern to match (e.g., "user:*")

    Returns:
        int: Number of keys deleted
    """
    if not cache_redis:
        return 0

    try:
        keys = []
        async for key in cache_redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            deleted = await cache_redis.delete(*keys)
            logger.info(f"Cache CLEAR: {pattern} ({deleted} keys)")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return 0


def cached(ttl: int = 300, key_prefix: str = None):
    """
    Decorator to cache function results.

    Usage:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: str):
            return await db.get(user_id)

    Args:
        ttl: Time to live in seconds
        key_prefix: Cache key prefix (defaults to function name)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = await get_cached(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await set_cached(cache_key, result, ttl)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: clear_cache_pattern(f"{key_prefix or func.__name__}:*")
        wrapper.cache_key_prefix = key_prefix or func.__name__

        return wrapper
    return decorator


async def get_cache_stats() -> dict:
    """
    Get cache statistics.

    Returns:
        dict: Cache statistics
    """
    if not cache_redis:
        return {"status": "disabled"}

    try:
        info = await cache_redis.info("stats")
        return {
            "status": "enabled",
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1) * 100,
            "keys": await cache_redis.dbsize(),
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}


# Convenience decorators for common TTLs
def cached_short(func: Callable):
    """Cache for 1 minute"""
    return cached(ttl=60)(func)


def cached_medium(func: Callable):
    """Cache for 5 minutes"""
    return cached(ttl=300)(func)


def cached_long(func: Callable):
    """Cache for 1 hour"""
    return cached(ttl=3600)(func)


def cached_very_long(func: Callable):
    """Cache for 24 hours"""
    return cached(ttl=86400)(func)