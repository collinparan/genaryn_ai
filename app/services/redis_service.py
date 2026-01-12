"""
Redis service for caching and session management
"""

import json
from typing import Any, Optional, Union

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class RedisService:
    """Redis service for caching and session management."""

    def __init__(self):
        """Initialize Redis service."""
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=30,
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def ping(self) -> bool:
        """Ping Redis to check connection."""
        try:
            return await self.redis_client.ping()
        except Exception as e:
            logger.error("Redis ping failed", error=str(e))
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Redis get failed", key=key, error=str(e))
            return None

    async def set(
        self, key: str, value: Any, expire: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            Success status
        """
        try:
            serialized = json.dumps(value)
            return await self.redis_client.set(key, serialized, ex=expire)
        except Exception as e:
            logger.error("Redis set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.

        Args:
            key: Cache key

        Returns:
            Success status
        """
        try:
            return bool(await self.redis_client.delete(key))
        except Exception as e:
            logger.error("Redis delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.

        Args:
            key: Cache key

        Returns:
            Existence status
        """
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.error("Redis exists check failed", key=key, error=str(e))
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter in Redis.

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            New counter value
        """
        try:
            return await self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error("Redis increment failed", key=key, error=str(e))
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key.

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            Success status
        """
        try:
            return await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error("Redis expire failed", key=key, error=str(e))
            return False

    async def get_ttl(self, key: str) -> int:
        """
        Get time-to-live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -2 if key doesn't exist, -1 if no expiration
        """
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error("Redis TTL check failed", key=key, error=str(e))
            return -2


# Singleton instance
redis_service_instance: Optional[RedisService] = None


async def get_redis() -> RedisService:
    """
    Get Redis service instance.

    Returns:
        RedisService instance
    """
    global redis_service_instance
    if redis_service_instance is None:
        redis_service_instance = RedisService()
        await redis_service_instance.connect()
    return redis_service_instance