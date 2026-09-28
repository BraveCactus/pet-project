from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models.user import User
from app.repositories.user import UserRepository

class EmailAlreadyExistsError(Exception):
    """Email уже зарегистрирован."""

class InvalidCredentialsError(Exception):
    """Неверный email или пароль."""


class InactiveUserError(Exception):
    """Пользователь заблокирован."""


class AuthService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._users = UserRepository(session)

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