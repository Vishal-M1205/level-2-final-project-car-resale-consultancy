from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.user import User


def create_mock_session():
    """Helper to create an AsyncMock database session that handles 'async with session.begin():'"""
    session = AsyncMock()
    begin_cm = MagicMock()
    begin_cm.__aenter__ = AsyncMock(return_value=session)
    begin_cm.__aexit__ = AsyncMock(return_value=None)
    session.begin = MagicMock(return_value=begin_cm)
    return session


@pytest.fixture
def mock_session():
    return create_mock_session()


@pytest.fixture
def mock_admin_user():
    return User(
        id=1,
        name="Admin User",
        email="admin@example.com",
        phone="9999999999",
        role="ADMIN",
        is_active=True,
    )


@pytest.fixture
def mock_customer_user():
    return User(
        id=2,
        name="Customer Seller",
        email="seller@example.com",
        phone="9888888888",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def mock_buyer_user():
    return User(
        id=3,
        name="Customer Buyer",
        email="buyer@example.com",
        phone="9777777777",
        role="CUSTOMER",
        is_active=True,
    )


@pytest.fixture
def mock_consultant_user():
    return User(
        id=4,
        name="Consultant User",
        email="consultant@example.com",
        phone="9666666666",
        role="CONSULTANT",
        is_active=True,
    )
