from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    BadRequestException,
    ForbiddenException,
)
from app.models.vehicle import Vehicle
from app.models.vehicle_listing import VehicleListing
from app.schemas.resale_transaction import (
    CreateResaleTransactionRequest,
    ResaleTransactionPatchRequest,
)
from app.services.resale_transaction_service import ResaleTransactionService


@pytest.mark.asyncio
async def test_log_transaction_non_admin_forbidden(mock_session, mock_customer_user):
    service = ResaleTransactionService(
        session=mock_session,
        resale_transaction_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )
    req = CreateResaleTransactionRequest(
        listing_id=1,
        buyer_id=2,
        final_price=Decimal("500000.00"),
    )
    with pytest.raises(ForbiddenException):
        await service.log_resale_transaction(request=req, user=mock_customer_user)


@pytest.mark.asyncio
async def test_log_transaction_listing_not_active_bad_request(mock_session, mock_admin_user):
    mock_listing_repo = AsyncMock()
    mock_listing_repo.get_listing_by_id.return_value = VehicleListing(id=1, status="INACTIVE")

    service = ResaleTransactionService(
        session=mock_session,
        resale_transaction_repository=AsyncMock(),
        vehicle_listing_repository=mock_listing_repo,
        vehicle_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )
    req = CreateResaleTransactionRequest(
        listing_id=1,
        buyer_id=2,
        final_price=Decimal("500000.00"),
    )
    with pytest.raises(BadRequestException) as exc_info:
        await service.log_resale_transaction(request=req, user=mock_admin_user)
    assert "only active listings can be sold" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_log_transaction_buyer_is_seller_bad_request(
    mock_session, mock_admin_user, mock_customer_user
):
    mock_listing_repo = AsyncMock()
    mock_listing_repo.get_listing_by_id.return_value = VehicleListing(
        id=1, vehicle_id=10, status="ACTIVE"
    )

    mock_vehicle_repo = AsyncMock()
    # Seller is mock_customer_user (id=2)
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=10, seller_id=mock_customer_user.id, status="approved"
    )

    mock_user_repo = AsyncMock()
    mock_user_repo.get_user_by_id.return_value = mock_customer_user

    service = ResaleTransactionService(
        session=mock_session,
        resale_transaction_repository=AsyncMock(),
        vehicle_listing_repository=mock_listing_repo,
        vehicle_repository=mock_vehicle_repo,
        user_repository=mock_user_repo,
        email_service=AsyncMock(),
    )

    # Buyer ID is set to same as seller ID (id=2)
    req = CreateResaleTransactionRequest(
        listing_id=1,
        buyer_id=mock_customer_user.id,
        final_price=Decimal("500000.00"),
    )
    with pytest.raises(BadRequestException) as exc_info:
        await service.log_resale_transaction(request=req, user=mock_admin_user)
    assert "seller cannot be the buyer" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_patch_transaction_empty_fields_bad_request(mock_session, mock_admin_user):
    service = ResaleTransactionService(
        session=mock_session,
        resale_transaction_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )
    empty_patch = ResaleTransactionPatchRequest()

    with pytest.raises(BadRequestException) as exc_info:
        await service.patch_transaction(
            transaction_id=1,
            patch_data=empty_patch,
            user=mock_admin_user,
        )
    assert "no fields provided" in str(exc_info.value.detail).lower()
