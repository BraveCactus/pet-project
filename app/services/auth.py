from uuid import UUID

from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.db.models.user import User
from app.repositories.user import UserRepository
from app.services.token_store import RefreshTokenStore

class EmailAlreadyExistsError(Exception):
    """Email уже зарегистрирован."""

class InvalidCredentialsError(Exception):
    """Неверный email или пароль."""


class InactiveUserError(Exception):
    """Пользователь заблокирован."""

class InvalidRefreshTokenError(Exception):
    """Refresh-токен невалиден или отозван."""


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self._session = session
        self._users = UserRepository(session)
        self._tokens = RefreshTokenStore(redis)

    async def register(
            self,
            *,
            email: str,
            password: str,
            full_name: str | None = None,
        ) -> User:
        existing = await self._users.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError(email)

        user = await self._users.create_user(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )

        await self._session.commit()
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self._users.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError
        
        if not user.is_active:
            raise InactiveUserError

        return user

    async def issue_token_pair(self, user: User) -> tuple[str, str]:
        """Создаёт access+refresh и сохраняет jti refresh в Redis."""
        access = create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value},
        )
        refresh = create_refresh_token(subject=user.id)
        from app.core.security import decode_token, TokenType
        payload = decode_token(refresh, expected_type=TokenType.REFRESH)

        await self._tokens.save(user_id=user.id, jti=payload["jti"])

        return access, refresh

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """
        Меняет старый refresh на новую пару access+refresh.
        Старый refresh отзывается.
        """
        from app.core.security import decode_token, TokenType
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        if payload is None:
            raise InvalidRefreshTokenError

        user_id = payload["sub"]
        jti = payload["jti"]

        if not await self._tokens.exists(user_id=user_id, jti=jti):
            raise InvalidRefreshTokenError

        # Ищем пользователя
        user = await self._users.get_by_id(UUID(user_id))
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError

        # Старый удаляем, новый выдаём
        await self._tokens.revoke(user_id=user_id, jti=jti)
        return await self.issue_token_pair(user)

    async def logout(self, refresh_token: str) -> None:
        """Отзывает refresh-токен."""
        from app.core.security import decode_token, TokenType
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        if payload is None:
            return  # уже невалиден — нечего отзывать
        await self._tokens.revoke(user_id=payload["sub"], jti=payload["jti"])