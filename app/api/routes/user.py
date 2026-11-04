from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import get_current_user, get_user_service
from app.schemas.user import (
    PaginatedUsersResponse,
    UserDeleteResponse,
    UserFilterParams,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get(
    "/",
    response_model=PaginatedUsersResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (Admin only)",
)
async def list_users(
    filters: Annotated[UserFilterParams, Query()],
    service: Annotated[UserService, Depends(get_user_service)],
    current_user=Security(get_current_user, scopes=["user:read"]),
):
    """
    Retrieve paginated users list. Supports filtering by role and active status.
    Restricted to Admin.
    """
    return await service.get_users(filters=filters, current_user=current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user profile by ID",
)
async def get_user_by_id(
    user_id: int,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user=Security(get_current_user, scopes=["user:read_own"]),
):
    """
    Get user profile details.
    Users can view their own profile; Admin can view any user's profile.
    """
    return await service.get_user_by_id(user_id=user_id, current_user=current_user)


@router.delete(
    "/{user_id}",
    response_model=UserDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete a user and deactivate their active listings (Admin only)",
)
async def soft_delete_user(
    user_id: int,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user=Security(get_current_user, scopes=["user:delete"]),
):
    """
    Soft delete user (sets is_active=False).
    Cascades deactivation to all active vehicle listings owned by the user.
    Restricted to Admin.
    """
    return await service.soft_delete_user(
        user_id=user_id, current_user=current_user
    )

