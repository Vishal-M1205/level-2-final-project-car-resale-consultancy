from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
)
from app.models.vehicle_inspection import VehicleInspection
from app.schemas.vehicle_inspection import (
    InspectionFilterParams,
    VehicleInspectionDetailSubmission,
)
from app.services.vehicle_inspection_service import VehicleInspectionService


def create_inspection_service(mock_session, mock_inspection_repo=None, mock_vehicle_repo=None):
    return VehicleInspectionService(
        session=mock_session,
        vehicle_inspection_repository=mock_inspection_repo or AsyncMock(),
        vehicle_repository=mock_vehicle_repo or AsyncMock(),
        user_repository=AsyncMock(),
        email_service=AsyncMock(),
        vehicle_listing_repository=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_get_all_inspections_customer_forbidden(mock_session, mock_customer_user):
    service = create_inspection_service(mock_session)
    with pytest.raises(ForbiddenException):
        await service.get_all_inspections(
            filters=InspectionFilterParams(), current_user=mock_customer_user
        )


@pytest.mark.asyncio
async def test_claim_inspection_already_claimed_conflict(mock_session, mock_consultant_user):
    mock_inspection_repo = AsyncMock()
    # Already claimed by another consultant (consultant_id=99)
    mock_inspection_repo.get_inspection_by_id.return_value = VehicleInspection(
        id=1, status="PENDING", consultant_id=99
    )

    service = create_inspection_service(mock_session, mock_inspection_repo=mock_inspection_repo)

    with pytest.raises(ConflictException) as exc_info:
        await service.claim_vehicle_inspection(inspection_id=1, consultant=mock_consultant_user)
    assert "already claimed" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_unclaim_inspection_not_claimed_bad_request(mock_session, mock_consultant_user):
    mock_inspection_repo = AsyncMock()
    # Not claimed (consultant_id is None)
    mock_inspection_repo.get_inspection_by_id.return_value = VehicleInspection(
        id=1, status="PENDING", consultant_id=None
    )

    service = create_inspection_service(mock_session, mock_inspection_repo=mock_inspection_repo)

    with pytest.raises(BadRequestException) as exc_info:
        await service.unclaim_vehicle_inspection(inspection_id=1, user=mock_consultant_user)
    assert "not currently claimed" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_cancel_inspection_non_admin_forbidden(mock_session, mock_consultant_user):
    service = create_inspection_service(mock_session)
    with pytest.raises(ForbiddenException) as exc_info:
        await service.cancel_vehicle_inspection(inspection_id=1, user=mock_consultant_user)
    assert "only admins" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_replace_inspection_cancelled_bad_request(mock_session, mock_consultant_user):
    mock_inspection_repo = AsyncMock()
    mock_inspection_repo.get_inspection_by_id.return_value = VehicleInspection(
        id=1, status="CANCELLED"
    )

    service = create_inspection_service(mock_session, mock_inspection_repo=mock_inspection_repo)

    report = VehicleInspectionDetailSubmission(
        condition="good",
        engine_condition="good",
        exterior_condition="good",
        interior_condition="good",
        accident_history=False,
        estimated_market_value=Decimal("500000.00"),
    )

    with pytest.raises(BadRequestException) as exc_info:
        await service.replace_vehicle_inspection(
            inspection_id=1, report_data=report, user=mock_consultant_user
        )
    assert "cancelled" in str(exc_info.value.detail).lower()
