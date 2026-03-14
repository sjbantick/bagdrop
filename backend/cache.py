"""Thin Redis cache layer. Degrades gracefully when Redis is unavailable."""
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_cache() -> None:
    global _redis
    try:
        client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await client.ping()
        _redis = client
        logger.info("[cache] Redis connected: %s", settings.redis_url)
    except Exception as exc:
        logger.warning("[cache] Redis unavailable, caching disabled: %s", exc)
        _redis = None


async def close_cache() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def cache_get(key: str) -> Optional[Any]:
    if not _redis:
        return None
    try:
        raw = await _redis.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        logger.debug("[cache] get error on %s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    if not _redis:
        return
    try:
        await _redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("[cache] set error on %s: %s", key, exc)


async def cache_delete(*keys: str) -> None:
    if not _redis or not keys:
        return
    try:
        await _redis.delete(*keys)
    except Exception as exc:
        logger.debug("[cache] delete error: %s", exc)
