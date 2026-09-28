from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import TokenPair
from app.services.auth import AuthService, EmailAlreadyExistsError, InactiveUserError, InvalidCredentialsError

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
) -> UserRead:
    service = AuthService(db)
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
    db: AsyncSession = Depends(get_db)
) -> TokenPair:
    service = AuthService(db)
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

    return TokenPair(
        access_token=create_access_token(
            subject=user.id,
            extra_claims={"role": user.role.value},
        ),
        refresh_token=create_refresh_token(subject=user.id),
    )