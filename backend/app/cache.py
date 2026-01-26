"""
Cache configuration for the application.
Supports both in-memory and Redis backends.
"""
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from .config import get_settings

settings = get_settings()


async def init_cache():
    """
    Initialize cache backend.

    Uses in-memory cache by default.
    Set REDIS_URL in environment to use Redis.
    """
    redis_url = getattr(settings, 'redis_url', None)

    if redis_url:
        # Production: Use Redis
        print(f"Initializing Redis cache at {redis_url}")
        redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
        FastAPICache.init(RedisBackend(redis), prefix="word-registry:")
    else:
        # Development: Use in-memory cache
        print("Initializing in-memory cache")
        FastAPICache.init(InMemoryBackend())


# Cache TTL constants (in seconds)
CACHE_TTL_LEADERBOARD = 30  # 30 seconds
CACHE_TTL_STATS = 60  # 1 minute
CACHE_TTL_RANDOM_POOL = 300  # 5 minutes
