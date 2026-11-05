from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.vehicle import Vehicle
from app.services.vehicle_document_service import VehicleDocumentService


@pytest.mark.asyncio
async def test_upload_document_invalid_type_bad_request(mock_session, mock_customer_user):
    service = VehicleDocumentService(
        session=mock_session,
        vehicle_repository=AsyncMock(),
        vehicle_document_repository=AsyncMock(),
    )
    mock_file = MagicMock()

    with pytest.raises(BadRequestException) as exc_info:
        await service.upload_document(
            vehicle_id=1,
            document_type="INVALID_TYPE",
            file=mock_file,
            user=mock_customer_user,
        )
    assert "invalid document type" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_upload_document_vehicle_not_found(mock_session, mock_customer_user):
    mock_vehicle_repo = AsyncMock()
    mock_vehicle_repo.get_vehicle_by_id.return_value = None

    service = VehicleDocumentService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_document_repository=AsyncMock(),
    )

    # Valid PDF mock
    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024

    with pytest.raises(NotFoundException):
        await service.upload_document(
            vehicle_id=999,
            document_type="RC",
            file=mock_file,
            user=mock_customer_user,
        )


@pytest.mark.asyncio
async def test_upload_document_unauthorized_user_forbidden(
    mock_session, mock_customer_user, mock_buyer_user
):
    mock_vehicle_repo = AsyncMock()
    # Vehicle owned by customer_user, buyer_user tries to upload
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id, status="submitted"
    )

    service = VehicleDocumentService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_document_repository=AsyncMock(),
    )

    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024

    with pytest.raises(ForbiddenException):
        await service.upload_document(
            vehicle_id=1,
            document_type="RC",
            file=mock_file,
            user=mock_buyer_user,
        )


@pytest.mark.asyncio
async def test_get_vehicle_documents_other_customer_forbidden(
    mock_session, mock_customer_user, mock_buyer_user
):
    mock_vehicle_repo = AsyncMock()
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id
    )

    service = VehicleDocumentService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_document_repository=AsyncMock(),
    )

    with pytest.raises(ForbiddenException):
        await service.get_vehicle_documents(vehicle_id=1, user=mock_buyer_user)


@pytest.mark.asyncio
async def test_delete_vehicle_document_not_submitted_bad_request(mock_session, mock_customer_user):
    mock_vehicle_repo = AsyncMock()
    mock_vehicle_repo.get_vehicle_by_id.return_value = Vehicle(
        id=1, seller_id=mock_customer_user.id, status="approved"
    )

    service = VehicleDocumentService(
        session=mock_session,
        vehicle_repository=mock_vehicle_repo,
        vehicle_document_repository=AsyncMock(),
    )

    with pytest.raises(BadRequestException) as exc_info:
        await service.delete_vehicle_document(
            vehicle_id=1,
            document_type="RC",
            user=mock_customer_user,
        )
    assert "submitted" in str(exc_info.value.detail).lower()
