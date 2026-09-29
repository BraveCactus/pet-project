from collections.abc import AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

_redis_pool: Redis = redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
)

def get_redis() -> Redis:
    """FastAPI-зависимость: возвращает общий клиент Redis."""
    return _redis_pool

async def close_redis() -> None:
    """Вызывается на shutdown приложения."""
    await _redis_pool.aclose()