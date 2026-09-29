from datetime import timedelta
from uuid import UUID

from redis.asyncio import Redis

from app.core.config import settings

class RefreshTokenStore:
    """
    Хранит jti refresh-токенов в Redis.

    Ключ: refresh:{user_id}:{jti}
    Значение: "1" (факт наличия)
    TTL: 7 дней (совпадает с exp refresh-токена)

    Если jti нет в Redis — токен отозван (logout, смена пароля и т.п.).
    """

    _PREFIX = "refresh"

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    def _key(self, user_id: UUID | str, jti: str) -> str:
        return f"{self._PREFIX}:{user_id}:{jti}"

    async def save(self, *, user_id: UUID | str, jti: str) -> None:
        ttl = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self._redis.set(
            self._key(user_id, jti),
            "1",
            ex=int(ttl.total_seconds()),
        )

    async def exists(self, *, user_id: UUID | str, jti: str) -> bool:
        return bool(await self._redis.exists(self._key(user_id, jti)))

    async def revoke(self, *, user_id: UUID | str, jti: str) -> None:
        await self._redis.delete(self._key(user_id, jti))