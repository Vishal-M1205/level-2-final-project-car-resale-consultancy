from typing import Annotated
from fastapi import APIRouter, Depends, File, Form, Query, Security, UploadFile, status

from app.api.dependencies.dependencies import (
    get_current_user,
    get_vehicle_document_service,
    get_vehicle_service,
)
from app.schemas.vehicle import (
    VehicleDecisionRequest,
    VehicleDecisionResponse,
    VehicleDeleteResponse,
    VehicleFilterParams,
    VehicleListResponse,
    VehicleResponse,
    VehicleSubmission,
    VehicleUpdate,
)
from app.schemas.vehicle_document import (
    VehicleDocumentDeleteResponse,
    VehicleDocumentResponse,
)
from app.services.vehicle_document_service import VehicleDocumentService
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit vehicle details for resale",
)
async def submit_vehicle(
    vehicle_details: VehicleSubmission,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:create"]),
):
    """
    Submit a new vehicle for resale.
    The authenticated user becomes the seller.
    Automatically creates a pending inspection record in the same transaction.
    """
    return await service.submit_vehicle_details(
        vehicle_details=vehicle_details,
        seller_id=current_user.id,
    )


@router.get(
    "/",
    response_model=VehicleListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicles with filters and pagination",
)
async def get_all_vehicles(
    filters: Annotated[VehicleFilterParams, Query()],
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read_own"]),
):
    """
    Retrieve a paginated list of vehicles with optional filters.
    - Customers automatically view only their own submitted vehicles.
    - Consultants and Admins view all vehicles across the system.
    """
    return await service.get_all_vehicles(filters=filters, user=current_user)


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicle details by ID",
)
async def get_vehicle_by_id(
    vehicle_id: int,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read_own"]),
):
    """
    Retrieve details of a vehicle by its ID.
    Sellers can view their own vehicle; Consultants and Admins can view any.
    """
    return await service.get_vehicle_by_id(vehicle_id=vehicle_id, user=current_user)


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vehicle details",
)
async def update_vehicle_details(
    vehicle_id: int,
    update_data: VehicleUpdate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:update_own"]),
):
    """
    Update vehicle specifications, pricing, registration number, or description.
    Sellers can edit their own vehicles while status is 'submitted'.
    Admins can edit at any status (except sold/deactivated).
    """
    return await service.update_vehicle_details(
        vehicle_id=vehicle_id,
        update_data=update_data,
        user=current_user,
    )


@router.post(
    "/{vehicle_id}/documents",
    response_model=VehicleDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload or update a document for a vehicle",
)
async def upload_vehicle_document(
    vehicle_id: int,
    file: Annotated[
        UploadFile, File(description="Vehicle document in PDF format (max 5MB)")
    ],
    document_type: Annotated[
        str, Form(description="Document type: RC, INSURANCE, or PUC")
    ],
    service: Annotated[VehicleDocumentService, Depends(get_vehicle_document_service)],
    current_user=Security(get_current_user, scopes=["vehicle:update_own"]),
):
    """
    Upload document RC, INSURANCE, PUC for a submitted vehicle.
    If a document of the same type was previously uploaded, it replaces the old file.
    """
    return await service.upload_document(
        vehicle_id=vehicle_id,
        document_type=document_type,
        file=file,
        user=current_user,
    )


@router.get(
    "/{vehicle_id}/documents",
    response_model=list[VehicleDocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all uploaded documents for a vehicle",
)
async def get_vehicle_documents(
    vehicle_id: int,
    service: Annotated[VehicleDocumentService, Depends(get_vehicle_document_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read_own"]),
):
    """
    Retrieve all uploaded documents for a specific vehicle.
    Sellers can view documents of their own vehicles; Admins can view all.
    """
    return await service.get_vehicle_documents(
        vehicle_id=vehicle_id,
        user=current_user,
    )


@router.delete(
    "/{vehicle_id}/documents/{document_type}",
    response_model=VehicleDocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a vehicle document (only when vehicle is in submitted status)",
)
async def delete_vehicle_document(
    vehicle_id: int,
    document_type: str,
    service: Annotated[VehicleDocumentService, Depends(get_vehicle_document_service)],
    current_user=Security(get_current_user, scopes=["vehicle:update_own"]),
):
    """
    Hard delete a document uploaded for a vehicle.
    Permitted only when the vehicle is in 'submitted' status.
    """
    return await service.delete_vehicle_document(
        vehicle_id=vehicle_id,
        document_type=document_type,
        user=current_user,
    )


@router.patch(
    "/{vehicle_id}/decision",
    response_model=VehicleDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin lifecycle decision (APPROVED, REJECTED, or RESUBMIT)",
)
async def admin_vehicle_decision(
    vehicle_id: int,
    decision: VehicleDecisionRequest,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:update"]),
):
    """
    Admin decides lifecycle status for a submitted vehicle:
    - 'APPROVED': verifies mandatory documents and auto-creates active resale listing.
    - 'REJECTED': rejects vehicle submission and deactivates any listing.
    - 'RESUBMIT': reopens a rejected vehicle back to 'submitted' and resets inspection to 'PENDING'.
    """
    return await service.admin_vehicle_decision(
        vehicle_id=vehicle_id,
        decision=decision,
        admin_user=current_user,
    )


@router.delete(
    "/{vehicle_id}",
    response_model=VehicleDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete a vehicle",
)
async def delete_vehicle(
    vehicle_id: int,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:delete_own"]),
):
    """
    Soft delete a vehicle by marking its status as 'deactivated'.
    Sellers can delete their own vehicles only when status is 'submitted' or 'rejected'.
    Admins can deactivate a vehicle at any status except 'sold'.
    Any active listing associated with the vehicle is automatically deactivated.
    """
    return await service.delete_vehicle(
        vehicle_id=vehicle_id,
        user=current_user,
    )
