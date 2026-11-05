from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    VehicleDecisionRequest,
    VehicleSubmission,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService


@pytest.mark.asyncio
async def test_submit_vehicle_duplicate_registration_conflict(mock_session, mock_customer_user):
    mock_vehicle_repo = AsyncMock()
    mock_vehicle_repo.get_vehicle_by_registration_number.return_value = Vehicle(
        id=1, registration_number="TN01AB1234"
    )

    service = VehicleService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    submission = VehicleSubmission(
        brand="Maruti",
        model="Swift",
        registration_number="TN01AB1234",
        manufacturing_year=2021,
        fuel_type="PETROL",
        transmission="MANUAL",
        kilometers_driven=25000,
        expected_price=Decimal("550000.00"),
        seating_capacity=5,
    )

    with pytest.raises(ConflictException) as exc_info:
        await service.submit_vehicle_details(submission, seller_id=mock_customer_user.id)
    assert "already found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_vehicle_by_id_not_found(mock_session, mock_customer_user):
    mock_vehicle_repo = AsyncMock()
    mock_vehicle_repo.get_vehicle_by_id.return_value = None

    service = VehicleService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    with pytest.raises(NotFoundException):
        await service.get_vehicle_by_id(vehicle_id=999, user=mock_customer_user)


@pytest.mark.asyncio
async def test_get_vehicle_by_id_other_customer_forbidden(
    mock_session, mock_customer_user, mock_buyer_user
):
    mock_vehicle_repo = AsyncMock()
    # Vehicle owned by customer_user (id=2), buyer_user (id=3) tries to get it
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id, status="submitted"
    )

    service = VehicleService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    with pytest.raises(ForbiddenException):
        await service.get_vehicle_by_id(vehicle_id=1, user=mock_buyer_user)


@pytest.mark.asyncio
async def test_update_vehicle_not_owner_forbidden(
    mock_session, mock_customer_user, mock_buyer_user
):
    mock_vehicle_repo = AsyncMock()
    # Vehicle owned by customer_user (id=2), buyer_user (id=3) tries to update
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id, status="submitted"
    )

    service = VehicleService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    with pytest.raises(ForbiddenException):
        await service.update_vehicle_details(
            vehicle_id=1,
            update_data=VehicleUpdate(expected_price=Decimal("600000.00")),
            user=mock_buyer_user,
        )


@pytest.mark.asyncio
async def test_update_vehicle_not_submitted_bad_request(mock_session, mock_customer_user):
    mock_vehicle_repo = AsyncMock()
    # Vehicle status is approved, not submitted
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id, status="approved"
    )

    service = VehicleService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    with pytest.raises(BadRequestException) as exc_info:
        await service.update_vehicle_details(
            vehicle_id=1,
            update_data=VehicleUpdate(expected_price=Decimal("600000.00")),
            user=mock_customer_user,
        )
    assert "submitted" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_admin_decision_non_admin_forbidden(mock_session, mock_customer_user):
    service = VehicleService(
        session=mock_session,
        vehicle_repository=AsyncMock(),
        vehicle_inspection_repository=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
    )

    with pytest.raises(ForbiddenException):
        await service.admin_vehicle_decision(
            vehicle_id=1,
            decision=VehicleDecisionRequest(action="APPROVED"),
            admin_user=mock_customer_user,
        )
