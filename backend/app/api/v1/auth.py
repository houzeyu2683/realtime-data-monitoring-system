from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services import log_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Username or email already taken"},
    },
)
async def register(
    payload: UserCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    if await user_service.get_user_by_username(db, payload.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if await user_service.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = await user_service.create_user(db, payload)
    await log_service.create_log(
        db, action="register", resource="user", user_id=user.id,
        detail=f"New user: {user.username}", ip_address=request.client.host,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"description": "Invalid credentials"},
        403: {"description": "Account disabled"},
    },
)
async def login(
    payload: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await user_service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(str(user.id))
    await log_service.create_log(
        db, action="login", resource="user", user_id=user.id,
        detail=f"Login: {user.username}", ip_address=request.client.host,
    )
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"description": "Invalid or expired token"},
    },
)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
