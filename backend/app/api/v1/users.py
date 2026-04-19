from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    responses={
        403: {"description": "Admin only"},
    },
)
async def list_users(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserResponse]:
    users = await user_service.list_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        403: {"description": "Cannot access other user's data"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"description": "Admin only"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: int,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_service.delete_user(db, user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        403: {"description": "Cannot modify other user or change role without admin"},
        404: {"description": "User not found"},
    },
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    from app.models.user import UserRole
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if payload.role is not None and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change roles")
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated = await user_service.update_user(db, user, payload)
    return UserResponse.model_validate(updated)
