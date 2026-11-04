from typing import Annotated
from fastapi import APIRouter, Depends, Query, Security, status

from app.api.dependencies.dependencies import (
    get_current_user,
    get_vehicle_listing_service,
)
from app.schemas.vehicle_listing import (
    ListingFilterParams,
    ListingPatchRequest,
    ListingResponse,
    PaginatedListingsResponse,
)
from app.services.vehicle_listing_service import VehicleListingService

router = APIRouter(prefix="/api/listings", tags=["Vehicle Listings"])


@router.get(
    "/",
    response_model=PaginatedListingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Browse vehicle listings (active, sold, price filters)",
)
async def get_listings(
    filters: Annotated[ListingFilterParams, Query()],
    service: Annotated[VehicleListingService, Depends(get_vehicle_listing_service)],
    current_user=Security(get_current_user, scopes=["listing:read"]),
):
    """
    Retrieve paginated vehicle listings.
    Supports filtering by status (ACTIVE, SOLD, INACTIVE), price range, and vehicle brand.
    """
    return await service.get_listings(filters)


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed view of a vehicle listing",
)
async def get_listing(
    listing_id: int,
    service: Annotated[VehicleListingService, Depends(get_vehicle_listing_service)],
    current_user=Security(get_current_user, scopes=["listing:read"]),
):
    """
    Get detailed information about a vehicle listing, including vehicle specifications.
    """
    return await service.get_listing_by_id(listing_id)


@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update listing status or price (Admin only)",
)
async def patch_listing(
    listing_id: int,
    patch_data: ListingPatchRequest,
    service: Annotated[VehicleListingService, Depends(get_vehicle_listing_service)],
    current_user=Security(get_current_user, scopes=["listing:update"]),
):
    """
    Update a listing's status (e.g. mark SOLD) or adjust listed price.
    Restricted to Admin. Marking listing SOLD auto-syncs vehicle status to 'sold'.
    """
    return await service.patch_listing(
        listing_id=listing_id,
        patch_data=patch_data,
        user=current_user,
    )

