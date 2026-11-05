from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.user import User
from app.schemas.auth import Login, RegisterUser
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_user_success(mock_session):
    mock_user_repo = AsyncMock()
    mock_email_service = AsyncMock()

    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_phone.return_value = None

    expected_user = User(
        id=10,
        name="Alice Doe",
        email="alice@example.com",
        phone="9876543210",
        role="CUSTOMER",
        is_active=True,
    )
    mock_user_repo.register_user.return_value = expected_user

    service = AuthService(
        session=mock_session,
        user_repository=mock_user_repo,
        email_service=mock_email_service,
    )

    user_data = RegisterUser(
        name="Alice Doe",
        email="alice@example.com",
        password="Password@123",
        phone="9876543210",
        age=26,
        gender="FEMALE",
        address_line_1="123 Street",
        district="Chennai",
        state="Tamil Nadu",
        pincode="600001",
    )

    result = await service.register_user(user_data)
    assert result.id == 10
    assert result.email == "alice@example.com"
    mock_user_repo.register_user.assert_called_once()
    mock_email_service.send_mail.assert_called_once()


@pytest.mark.asyncio
async def test_register_user_duplicate_email(mock_session):
    mock_user_repo = AsyncMock()
    mock_email_service = AsyncMock()

    mock_user_repo.get_user_by_email.return_value = User(id=1, email="dup@example.com")

    service = AuthService(
        session=mock_session,
        user_repository=mock_user_repo,
        email_service=mock_email_service,
    )

    user_data = RegisterUser(
        name="Duplicate User",
        email="dup@example.com",
        password="Password@123",
        phone="9876543211",
        age=28,
        gender="MALE",
        address_line_1="Street",
        district="Chennai",
        state="Tamil Nadu",
        pincode="600001",
    )

    with pytest.raises(ConflictException) as exc_info:
        await service.register_user(user_data)
    assert "email" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_register_user_duplicate_phone(mock_session):
    mock_user_repo = AsyncMock()
    mock_email_service = AsyncMock()

    mock_user_repo.get_user_by_email.return_value = None
    mock_user_repo.get_user_by_phone.return_value = User(id=2, phone="9876543212")

    service = AuthService(
        session=mock_session,
        user_repository=mock_user_repo,
        email_service=mock_email_service,
    )

    user_data = RegisterUser(
        name="Phone Dup User",
        email="unique@example.com",
        password="Password@123",
        phone="9876543212",
        age=28,
        gender="MALE",
        address_line_1="Street",
        district="Chennai",
        state="Tamil Nadu",
        pincode="600001",
    )

    with pytest.raises(ConflictException) as exc_info:
        await service.register_user(user_data)
    assert "phone" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_login_user_not_found(mock_session):
    mock_user_repo = AsyncMock()
    mock_email_service = AsyncMock()
    mock_user_repo.get_user_by_email.return_value = None

    service = AuthService(
        session=mock_session,
        user_repository=mock_user_repo,
        email_service=mock_email_service,
    )

    login_data = Login(email="ghost@example.com", password="Password@123")
    with pytest.raises(NotFoundException) as exc_info:
        await service.login(login_data)
    assert "no user found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_login_deactivated_account(mock_session):
    mock_user_repo = AsyncMock()
    mock_email_service = AsyncMock()
    mock_user_repo.get_user_by_email.return_value = User(
        id=5,
        email="inactive@example.com",
        is_active=False,
    )

    service = AuthService(
        session=mock_session,
        user_repository=mock_user_repo,
        email_service=mock_email_service,
    )

    login_data = Login(email="inactive@example.com", password="Password@123")
    with pytest.raises(ForbiddenException) as exc_info:
        await service.login(login_data)
    assert "deactivated" in str(exc_info.value.detail).lower()
