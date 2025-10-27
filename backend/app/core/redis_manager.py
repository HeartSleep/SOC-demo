"""
Redis Configuration for Production
High-performance caching and message queue setup
"""
import redis
import asyncio
import json
import pickle
from typing import Any, Optional, List, Dict
from datetime import datetime, timedelta
import hashlib
from redis.asyncio import Redis, ConnectionPool, Sentinel
from redis.asyncio.lock import Lock
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Production-ready Redis manager with high availability"""

    def __init__(self, config: Dict):
        self.config = config
        self.redis_client: Optional[Redis] = None
        self.pubsub_client: Optional[Redis] = None
        self.sentinel_client: Optional[Sentinel] = None
        self.connection_pool: Optional[ConnectionPool] = None

    async def initialize(self):
        """Initialize Redis connections with proper configuration"""
        try:
            # Use Sentinel for high availability if configured
            if self.config.get('use_sentinel'):
                await self._init_sentinel()
            else:
                await self._init_standalone()

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")

            # Initialize pub/sub client
            self.pubsub_client = self.redis_client.client()

            # Set up connection monitoring
            asyncio.create_task(self._monitor_connection())

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def _init_standalone(self):
        """Initialize standalone Redis connection"""
        # Create connection pool with retry strategy
        retry = Retry(ExponentialBackoff(), 3)

        self.connection_pool = ConnectionPool(
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 6379),
            password=self.config.get('password'),
            db=self.config.get('db', 0),
            max_connections=self.config.get('max_connections', 100),
            socket_keepalive=True,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5   # TCP_KEEPCNT
            },
            socket_connect_timeout=5,
            retry=retry,
            retry_on_error=[ConnectionError, TimeoutError],
            decode_responses=False  # Handle both string and binary data
        )

        self.redis_client = Redis(connection_pool=self.connection_pool)

    async def _init_sentinel(self):
        """Initialize Redis Sentinel for high availability"""
        sentinels = self.config.get('sentinels', [('localhost', 26379)])
        master_name = self.config.get('master_name', 'mymaster')

        self.sentinel_client = Sentinel(
            sentinels,
            password=self.config.get('password'),
            sentinel_kwargs={'password': self.config.get('sentinel_password')}
        )

        # Discover master and slaves
        self.redis_client = self.sentinel_client.master_for(
            master_name,
            redis_class=Redis,
            max_connections=self.config.get('max_connections', 100)
        )

    async def _monitor_connection(self):
        """Monitor Redis connection health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self.redis_client.ping()
            except Exception as e:
                logger.error(f"Redis connection lost: {e}")
                # Attempt reconnection
                try:
                    await self.initialize()
                except Exception:
                    logger.error("Failed to reconnect to Redis")

    async def close(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.pubsub_client:
            await self.pubsub_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()

    # Cache Operations
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis_client.get(key)
            if value:
                # Try to deserialize JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(value)
                    except:
                        return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                serialized = str(value)
            else:
                serialized = pickle.dumps(value)

            return await self.redis_client.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return await self.redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for a key"""
        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False

    # Batch Operations
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Get multiple values at once"""
        try:
            values = await self.redis_client.mget(keys)
            results = []
            for value in values:
                if value:
                    try:
                        results.append(json.loads(value))
                    except:
                        results.append(value.decode('utf-8') if isinstance(value, bytes) else value)
                else:
                    results.append(None)
            return results
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return [None] * len(keys)

    async def mset(self, mapping: Dict[str, Any]) -> bool:
        """Set multiple values at once"""
        try:
            serialized = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized[key] = json.dumps(value)
                else:
                    serialized[key] = str(value)
            return await self.redis_client.mset(serialized)
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False

    # List Operations
    async def lpush(self, key: str, *values) -> int:
        """Push values to the left of a list"""
        try:
            serialized = [json.dumps(v) if isinstance(v, (dict, list)) else str(v) for v in values]
            return await self.redis_client.lpush(key, *serialized)
        except Exception as e:
            logger.error(f"Redis lpush error for key {key}: {e}")
            return 0

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from the right of a list"""
        try:
            value = await self.redis_client.rpop(key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Redis rpop error for key {key}: {e}")
            return None

    async def lrange(self, key: str, start: int, stop: int) -> List[Any]:
        """Get range of values from a list"""
        try:
            values = await self.redis_client.lrange(key, start, stop)
            results = []
            for value in values:
                try:
                    results.append(json.loads(value))
                except:
                    results.append(value.decode('utf-8') if isinstance(value, bytes) else value)
            return results
        except Exception as e:
            logger.error(f"Redis lrange error for key {key}: {e}")
            return []

    # Set Operations
    async def sadd(self, key: str, *values) -> int:
        """Add members to a set"""
        try:
            serialized = [json.dumps(v) if isinstance(v, (dict, list)) else str(v) for v in values]
            return await self.redis_client.sadd(key, *serialized)
        except Exception as e:
            logger.error(f"Redis sadd error for key {key}: {e}")
            return 0

    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        try:
            members = await self.redis_client.smembers(key)
            results = set()
            for member in members:
                try:
                    results.add(json.loads(member))
                except:
                    results.add(member.decode('utf-8') if isinstance(member, bytes) else member)
            return results
        except Exception as e:
            logger.error(f"Redis smembers error for key {key}: {e}")
            return set()

    # Hash Operations
    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set hash field"""
        try:
            serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            return await self.redis_client.hset(key, field, serialized)
        except Exception as e:
            logger.error(f"Redis hset error for key {key}, field {field}: {e}")
            return 0

    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        try:
            value = await self.redis_client.hget(key, field)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value.decode('utf-8') if isinstance(value, bytes) else value
        except Exception as e:
            logger.error(f"Redis hget error for key {key}, field {field}: {e}")
            return None

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields and values"""
        try:
            data = await self.redis_client.hgetall(key)
            result = {}
            for field, value in data.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                try:
                    result[field_str] = json.loads(value)
                except:
                    result[field_str] = value.decode('utf-8') if isinstance(value, bytes) else value
            return result
        except Exception as e:
            logger.error(f"Redis hgetall error for key {key}: {e}")
            return {}

    # Atomic Operations
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        try:
            return await self.redis_client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis decr error for key {key}: {e}")
            return 0

    # Distributed Locking
    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> Optional[Lock]:
        """Acquire distributed lock"""
        try:
            lock = self.redis_client.lock(lock_name, timeout=timeout)
            if await lock.acquire(blocking=True, blocking_timeout=5):
                return lock
            return None
        except Exception as e:
            logger.error(f"Failed to acquire lock {lock_name}: {e}")
            return None

    async def release_lock(self, lock: Lock) -> bool:
        """Release distributed lock"""
        try:
            await lock.release()
            return True
        except Exception as e:
            logger.error(f"Failed to release lock: {e}")
            return False

    # Pub/Sub Operations
    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to channel"""
        try:
            serialized = json.dumps(message) if isinstance(message, (dict, list)) else str(message)
            return await self.redis_client.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Redis publish error for channel {channel}: {e}")
            return 0

    async def subscribe(self, *channels):
        """Subscribe to channels"""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(*channels)
            return pubsub
        except Exception as e:
            logger.error(f"Redis subscribe error: {e}")
            return None

    # Rate Limiting
    async def is_rate_limited(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        try:
            pipe = self.redis_client.pipeline()
            now = datetime.now()
            window_start = now - timedelta(seconds=window)

            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start.timestamp())
            # Add current request
            pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
            # Count requests in window
            pipe.zcard(key)
            # Set expiry
            pipe.expire(key, window)

            results = await pipe.execute()
            request_count = results[2]

            return request_count > limit
        except Exception as e:
            logger.error(f"Rate limiting error for key {key}: {e}")
            return False

    # Cache Invalidation
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            count = 0
            async for key in self.redis_client.scan_iter(match=pattern):
                await self.redis_client.delete(key)
                count += 1
            return count
        except Exception as e:
            logger.error(f"Pattern invalidation error for {pattern}: {e}")
            return 0

    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis"""
        try:
            # Ping test
            start = datetime.now()
            await self.redis_client.ping()
            latency = (datetime.now() - start).total_seconds() * 1000

            # Get info
            info = await self.redis_client.info()

            return {
                "status": "healthy",
                "latency_ms": latency,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0"),
                "used_memory_peak": info.get("used_memory_peak_human", "0"),
                "uptime_days": info.get("uptime_in_days", 0),
                "version": info.get("redis_version", "unknown")
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class CacheDecorator:
    """Decorator for caching function results"""

    def __init__(self, redis_manager: RedisManager, ttl: int = 300, prefix: str = "cache"):
        self.redis = redis_manager
        self.ttl = ttl
        self.prefix = prefix

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached = await self.redis.get(cache_key)
            if cached is not None:
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await self.redis.set(cache_key, result, ttl=self.ttl)

            return result

        return wrapper

    def _generate_key(self, func_name: str, args, kwargs) -> str:
        """Generate cache key from function name and arguments"""
        key_parts = [self.prefix, func_name]

        # Add args to key
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

        # Add kwargs to key
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}={v}")
            else:
                key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")

        return ":".join(key_parts)


# Export configured Redis manager
redis_config = {
    'host': 'localhost',
    'port': 6379,
    'password': None,  # Will be loaded from environment
    'db': 0,
    'max_connections': 100,
    'use_sentinel': False,  # Enable for HA setup
    'sentinels': [('localhost', 26379)],
    'master_name': 'mymaster'
}

redis_manager = RedisManager(redis_config)