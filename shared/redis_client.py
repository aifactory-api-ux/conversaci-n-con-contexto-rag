import asyncio
import json
from typing import Any, Optional, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and error handling."""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Establish connection to Redis server."""
        if self._is_connected:
            return
        
        try:
            # Build Redis URL from settings
            redis_url = settings.REDIS_URL
            if not redis_url:
                redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
                if settings.REDIS_PASSWORD:
                    redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                str(redis_url),
                max_connections=20,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Create Redis client
            self._redis = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._redis.ping()
            self._is_connected = True
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._is_connected = False
            raise
        except RedisError as e:
            logger.error(f"Redis error during connection: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection and pool."""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        self._is_connected = False
        logger.info("Disconnected from Redis")
    
    async def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        if not self._redis or not self._is_connected:
            return False
        
        try:
            await self._redis.ping()
            return True
        except RedisError:
            self._is_connected = False
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            return value.decode('utf-8') if value else None
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Union[str, bytes, dict, list], expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            # Convert complex types to JSON string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif isinstance(value, bytes):
                value = value.decode('utf-8')
            
            if expire:
                result = await self._redis.setex(key, expire, value)
            else:
                result = await self._redis.set(key, value)
            
            return bool(result)
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.exists(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching pattern."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            keys = await self._redis.keys(pattern)
            return [key.decode('utf-8') for key in keys]
        except RedisError as e:
            logger.error(f"Redis keys error for pattern {pattern}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """Flush all data from current database."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            await self._redis.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Redis flushdb error: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Union[dict, list]]:
        """Get and parse JSON value from Redis."""
        value = await self.get(key)
        if not value:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Redis key {key}: {e}")
            return None
    
    async def set_json(self, key: str, value: Union[dict, list], expire: Optional[int] = None) -> bool:
        """Set JSON value in Redis."""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, expire)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize JSON for Redis key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment integer value in Redis."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            return await self._redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for key."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            result = await self._redis.expire(key, seconds)
            return bool(result)
        except RedisError as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> Optional[int]:
        """Get time to live for key."""
        if not await self.is_connected():
            await self.connect()
        
        try:
            return await self._redis.ttl(key)
        except RedisError as e:
            logger.error(f"Redis ttl error for key {key}: {e}")
            return None


# Global Redis client instance
redis_client = RedisClient()


@asynccontextmanager
async def get_redis():
    """Async context manager for Redis operations."""
    try:
        await redis_client.connect()
        yield redis_client
    finally:
        await redis_client.disconnect()


async def health_check_redis() -> dict[str, Any]:
    """Health check for Redis connection."""
    try:
        is_healthy = await redis_client.is_connected()
        if not is_healthy:
            await redis_client.connect()
            is_healthy = await redis_client.is_connected()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "redis",
            "connected": is_healthy,
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "redis",
            "connected": False,
            "error": str(e),
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
        }
