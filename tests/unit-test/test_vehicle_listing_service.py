from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.vehicle import Vehicle
from app.models.vehicle_listing import VehicleListing
from app.schemas.vehicle_listing import ListingPatchRequest
from app.services.vehicle_listing_service import VehicleListingService


@pytest.mark.asyncio
async def test_get_listing_by_id_not_found(mock_session):
    mock_listing_repo = AsyncMock()
    mock_listing_repo.get_listing_by_id.return_value = None

    service = VehicleListingService(
        session=mock_session,
        vehicle_listing_repository=mock_listing_repo,
        vehicle_repository=AsyncMock(),
    )
    with pytest.raises(NotFoundException):
        await service.get_listing_by_id(listing_id=999)


@pytest.mark.asyncio
async def test_get_listing_by_id_deactivated_vehicle_not_found(mock_session):
    mock_listing_repo = AsyncMock()
    # Vehicle linked to listing is deactivated
    deactivated_v = Vehicle(id=1, status="deactivated")
    mock_listing_repo.get_listing_by_id.return_value = VehicleListing(
        id=1, vehicle_id=1, vehicle=deactivated_v
    )

    service = VehicleListingService(
        session=mock_session,
        vehicle_listing_repository=mock_listing_repo,
        vehicle_repository=AsyncMock(),
    )
    with pytest.raises(NotFoundException):
        await service.get_listing_by_id(listing_id=1)


@pytest.mark.asyncio
async def test_patch_listing_non_admin_forbidden(mock_session, mock_customer_user):
    service = VehicleListingService(
        session=mock_session,
        vehicle_listing_repository=AsyncMock(),
        vehicle_repository=AsyncMock(),
    )
    patch_req = ListingPatchRequest(listed_price=Decimal("600000.00"))

    with pytest.raises(ForbiddenException) as exc_info:
        await service.patch_listing(listing_id=1, patch_data=patch_req, user=mock_customer_user)
    assert "only administrators" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_patch_listing_already_sold_bad_request(mock_session, mock_admin_user):
    mock_listing_repo = AsyncMock()
    mock_listing_repo.get_listing_by_id.return_value = VehicleListing(id=1, status="SOLD")

    service = VehicleListingService(
        session=mock_session,
        vehicle_listing_repository=mock_listing_repo,
        vehicle_repository=AsyncMock(),
    )
    patch_req = ListingPatchRequest(listed_price=Decimal("600000.00"))

    with pytest.raises(BadRequestException) as exc_info:
        await service.patch_listing(listing_id=1, patch_data=patch_req, user=mock_admin_user)
    assert "already been sold" in str(exc_info.value.detail).lower()
