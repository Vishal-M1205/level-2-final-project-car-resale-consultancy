from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import (
    get_current_user,
    get_vehicle_inspection_service,
)
from app.schemas.vehicle_inspection import (
    AdminInspectionDetailResponse,
    InspectionCancelResponse,
    InspectionFilterParams,
    InspectionUnclaimResponse,
    PaginatedInspectionsResponse,
    VehicleInspectionClaim,
    VehicleInspectionDetailResponse,
    VehicleInspectionDetailSubmission,
)
from app.services.vehicle_inspection_service import VehicleInspectionService

router = APIRouter(prefix="/api/vehicle-inspections", tags=["Vehicle Inspections"])


@router.get(
    "/",
    response_model=PaginatedInspectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="View vehicle inspections with filters",
)
async def get_all_inspections(
    filters: Annotated[InspectionFilterParams, Query()],
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:read"]),
):
    """
    Retrieve a paginated list of vehicle inspections with optional filters:
    - status: 'PENDING', 'COMPLETED', 'CANCELLED'
    - is_claimed: false (unassigned pool), true (claimed queue)
    - mine: true (claimed by current consultant)
    - inspection_date, vehicle_status, page, limit
    """
    return await service.get_all_inspections(filters=filters, current_user=current_user)


@router.get(
    "/{inspection_id}",
    response_model=AdminInspectionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full inspection details by ID",
)
async def get_inspection_by_id(
    inspection_id: int,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:read"]),
):
    """
    Retrieve complete details of a vehicle inspection including vehicle, consultant, and uploaded documents.
    """
    return await service.get_inspection_with_details(
        inspection_id=inspection_id,
        current_user=current_user,
    )


@router.post(
    "/{inspection_id}/claim",
    response_model=VehicleInspectionClaim,
    status_code=status.HTTP_200_OK,
    summary="Claim a pending vehicle inspection",
)
async def claim_vehicle_inspection(
    inspection_id: int,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:claim"]),
):
    """Consultant claims an unassigned pending vehicle inspection."""
    return await service.claim_vehicle_inspection(
        inspection_id=inspection_id,
        consultant=current_user,
    )


@router.post(
    "/{inspection_id}/unclaim",
    response_model=InspectionUnclaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Unclaim a vehicle inspection",
)
async def unclaim_vehicle_inspection(
    inspection_id: int,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:claim"]),
):
    """
    Unclaim a pending vehicle inspection and return it to the unassigned pool.
    Consultants can only unclaim their own claimed inspections; Admins can unclaim any.
    """
    return await service.unclaim_vehicle_inspection(
        inspection_id=inspection_id,
        user=current_user,
    )


@router.patch(
    "/{inspection_id}/cancel",
    response_model=InspectionCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a vehicle inspection",
)
async def cancel_vehicle_inspection(
    inspection_id: int,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:update"]),
):
    """
    Cancel an inspection (Admin only).
    Marks inspection as CANCELLED and moves the vehicle to 'rejected'.
    """
    return await service.cancel_vehicle_inspection(
        inspection_id=inspection_id,
        user=current_user,
    )


@router.put(
    "/{inspection_id}",
    response_model=VehicleInspectionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit or update vehicle inspection report",
)
async def submit_or_update_inspection(
    inspection_id: int,
    report_data: VehicleInspectionDetailSubmission,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:update"]),
):
    """
    Submit initial completed inspection report OR update existing report details:
    - If PENDING: consultant submits report -> moves status to 'COMPLETED'.
    - If COMPLETED & vehicle 'submitted': consultant or Admin can update details.
    - If COMPLETED & vehicle 'approved' / 'rejected': Admin ONLY can update details.
    - Auto-syncs listed_price if vehicle is approved.
    """
    return await service.replace_vehicle_inspection(
        inspection_id=inspection_id,
        report_data=report_data,
        user=current_user,
    )
