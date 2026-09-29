from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.integrations.redis import get_redis
from app.schemas.auth import RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserRead
from app.services.auth import (
    AuthService,
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: AsyncSession = Depends(get_redis),
) -> UserRead:
    service = AuthService(db, redis)
    try:
        user = await service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return UserRead.model_validate(user)

@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login and receive access and refresh tokens",
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    redis: AsyncSession = Depends(get_redis),
) -> TokenPair:
    service = AuthService(db, redis)
    try:
        user = await service.authenticate(
            email=form.username,
            password=form.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )

    access, refresh = await service.issue_token_pair(user)
    return TokenPair(access_token=access, refresh_token=refresh)

@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Rotate refresh token and issue a new pair",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenPair:
    service = AuthService(db, redis)
    try:
        access, refresh = await service.refresh_tokens(payload.refresh_token)
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )
    return TokenPair(access_token=access, refresh_token=refresh)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token",
)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> None:
    service = AuthService(db, redis)
    await service.logout(payload.refresh_token)