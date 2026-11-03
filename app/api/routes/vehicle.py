from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import get_current_user, get_vehicle_service
from app.schemas.vehicle import (
    MyVehicleListResponse,
    VehicleFilterParams,
    VehicleListResponse,
    VehicleResponse,
    VehicleSubmission,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a vehicle for resale",
)
async def submit_vehicle_details(
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
    summary="Get all vehicles with filters and pagination",
)
async def get_all_vehicles(
    filters: Annotated[VehicleFilterParams, Query()],
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read"]),
):
    """
    Retrieve a paginated list of all vehicles with optional filters.
    Requires vehicle:read permission (Consultant / Admin).
    """
    return await service.get_all_vehicles(filters=filters)


# NOTE: /my-vehicles MUST be declared BEFORE /{vehicle_id}
# Otherwise, FastAPI matches 'my-vehicles' against '{vehicle_id: int}' and throws a 422 error.
@router.get(
    "/my-vehicles",
    response_model=MyVehicleListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicles submitted by the current user",
)
async def get_user_vehicles(
    filters: Annotated[VehicleFilterParams, Query()],
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read_own"]),
):
    """
    Retrieve a paginated list of vehicles submitted by the logged-in user with optional filters.
    """
    return await service.get_user_vehicles(
        user=current_user,
        filters=filters,
    )


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vehicle details by ID",
)
async def get_vehicle_by_id(
    vehicle_id: int,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
    current_user=Security(get_current_user, scopes=["vehicle:read"]),
):
    """
    Retrieve details of a vehicle by its ID.
    Requires vehicle:read permission (Consultant / Admin).
    """
    return await service.get_vehicle_by_id(vehicle_id)
