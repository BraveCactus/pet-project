from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.user import User
from app.repositories.user import UserRepository

class EmailAlreadyExistsError(Exception):
    """Email уже зарегистрирован."""

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