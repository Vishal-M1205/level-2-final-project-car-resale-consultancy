from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import (
    get_current_user,
    get_vehicle_inspection_service,
)
from app.schemas.vehicle_inspection import (
    ConsultantInspectionFilterParams,
    MyInspectionListResponse,
    PaginatedPendingInspectionsResponse,
    VehicleInspectionClaim,
    VehicleInspectionDetailResponse,
    VehicleInspectionDetailSubmission,
)
from app.services.vehicle_inspection_service import VehicleInspectionService

router = APIRouter(prefix="/api/vehicle-inspections", tags=["Vehicle Inspections"])


@router.get(
    "/pending",
    response_model=PaginatedPendingInspectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="View unassigned pending inspections",
)
async def get_pending_inspections(
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    current_user=Security(get_current_user, scopes=["inspection:read"]),
):
    """Retrieve all pending vehicle inspections that are not claimed by any consultant"""
    return await service.get_pending_inspections(page=page, limit=limit)


@router.get(
    "/my-inspections",
    response_model=MyInspectionListResponse,
    status_code=status.HTTP_200_OK,
    summary="View inspections claimed by the logged-in consultant",
)
async def get_my_inspections(
    filters: Annotated[ConsultantInspectionFilterParams, Query()],
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:read"]),
):
    """
    Retrieve a  list of vehicle inspections claimed by the consultant
    supports filtering by status (PENDING,COMPLETED) and  inspection date (yyyy-mm-dd)
    """
    return await service.get_my_inspections(
        consultant=current_user,
        filters=filters,
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
    """Consultant will claim unassigned pending vehicle inspection"""
    return await service.claim_vehicle_inspection(
        inspection_id=inspection_id,
        consultant=current_user,
    )


@router.patch(
    "/{inspection_id}/complete",
    response_model=VehicleInspectionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit completed vehicle inspection report",
)
async def complete_inspection(
    inspection_id: int,
    report_data: VehicleInspectionDetailSubmission,
    service: Annotated[
        VehicleInspectionService, Depends(get_vehicle_inspection_service)
    ],
    current_user=Security(get_current_user, scopes=["inspection:update"]),
):
    """Submit completed vehicle inspection report."""
    return await service.submit_inspection_report(
        inspection_id=inspection_id,
        consultant=current_user,
        report_data=report_data,
    )
