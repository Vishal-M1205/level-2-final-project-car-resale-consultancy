from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.schemas.user import UserFilterParams, UserPatchRequest
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_get_users_non_admin_forbidden(mock_session, mock_customer_user):
    service = UserService(
        session=mock_session,
        user_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
    )
    with pytest.raises(ForbiddenException):
        await service.get_users(UserFilterParams(), current_user=mock_customer_user)


@pytest.mark.asyncio
async def test_get_user_by_id_other_user_forbidden(mock_session, mock_customer_user):
    service = UserService(
        session=mock_session,
        user_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
    )
    # mock_customer_user has id=2, tries to view user 99
    with pytest.raises(ForbiddenException):
        await service.get_user_by_id(user_id=99, current_user=mock_customer_user)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(mock_session, mock_admin_user):
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_id.return_value = None

    service = UserService(
        session=mock_session,
        user_repository=mock_user_repo,
        vehicle_listing_repository=AsyncMock(),
    )
    with pytest.raises(NotFoundException):
        await service.get_user_by_id(user_id=99, current_user=mock_admin_user)


@pytest.mark.asyncio
async def test_soft_delete_admin_self_deactivation_rejected(mock_session, mock_admin_user):
    service = UserService(
        session=mock_session,
        user_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
    )
    # Admin tries to deactivate own id (id=1)
    with pytest.raises(BadRequestException) as exc_info:
        await service.soft_delete_user(user_id=mock_admin_user.id, current_user=mock_admin_user)
    assert "cannot deactivate their own account" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_patch_user_duplicate_phone_conflict(mock_session, mock_customer_user):
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_id.return_value = mock_customer_user
    # Another user owns the new phone number
    mock_user_repo.get_user_by_phone.return_value = User(id=99, phone="9988776655")

    service = UserService(
        session=mock_session,
        user_repository=mock_user_repo,
        vehicle_listing_repository=AsyncMock(),
    )

    patch_data = UserPatchRequest(phone="9988776655")
    with pytest.raises(ConflictException) as exc_info:
        await service.patch_user(
            user_id=mock_customer_user.id,
            patch_data=patch_data,
            current_user=mock_customer_user,
        )
    assert "already registered" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_my_profile_success(mock_session, mock_customer_user):
    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_id.return_value = mock_customer_user

    service = UserService(
        session=mock_session,
        user_repository=mock_user_repo,
        vehicle_listing_repository=AsyncMock(),
    )
    user = await service.get_my_profile(current_user=mock_customer_user)
    assert user.id == mock_customer_user.id
    assert user.email == mock_customer_user.email
