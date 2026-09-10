from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.user import UserResponse, UserStatusUpdate
from app.repositories.user_repository import UserRepository
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])
user_repo = UserRepository()


@router.get(
    "/",
    response_model=StandardResponse[PaginatedData[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all users with search and pagination",
)
def list_users(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    users_data = user_repo.get_users(db, pagination, search=search, is_active=is_active)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Users retrieved successfully",
        "data": users_data,
    }


@router.get(
    "/{user_id}",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get user details by ID",
)
def get_user(
    user_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "User details retrieved successfully",
        "data": user,
    }


@router.patch(
    "/{user_id}/status",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Activate or suspend user account",
)
def update_user_status(
    user_id: int,
    body: UserStatusUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise NotFoundException(f"User with id {user_id} not found")

    updated = user_repo.update(db, user, {"is_active": body.is_active})
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": f"User status updated to {'active' if body.is_active else 'suspended'}",
        "data": updated,
    }
