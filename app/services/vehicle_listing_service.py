from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle_listing import VehicleListing
from app.repositories.interfaces.vehicle_interface import VehicleInterface
from app.repositories.interfaces.vehicle_listing_interface import (
    VehicleListingInterface,
)
from app.schemas.vehicle_listing import ListingFilterParams, ListingPatchRequest


class VehicleListingService:
    def __init__(
        self,
        session: AsyncSession,
        vehicle_listing_repository: VehicleListingInterface,
        vehicle_repository: VehicleInterface,
    ):
        self.session = session
        self.vehicle_listing_repository = vehicle_listing_repository
        self.vehicle_repository = vehicle_repository

    async def get_listings(self, filters: ListingFilterParams) -> dict:
        async with self.session.begin():
            return await self.vehicle_listing_repository.get_listings(filters)

    async def get_listing_by_id(self, listing_id: int) -> VehicleListing:
        async with self.session.begin():
            listing = await self.vehicle_listing_repository.get_listing_by_id(listing_id)
            if not listing or (listing.vehicle and listing.vehicle.status == "deactivated"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Listing not found.",
                )
            return listing

    async def patch_listing(
        self, listing_id: int, patch_data: ListingPatchRequest, user: User
    ) -> VehicleListing:
        if user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update listings.",
            )

        async with self.session.begin():
            listing = await self.vehicle_listing_repository.get_listing_by_id(listing_id)
            if not listing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Listing not found.",
                )

            # If status changed to SOLD, sync vehicle.status to "sold"
            if patch_data.status == "SOLD":
                await self.vehicle_repository.update_vehicle_status(
                    vehicle_id=listing.vehicle_id,
                    status="sold",
                )

            updated = await self.vehicle_listing_repository.update_listing(
                listing_id=listing_id,
                status=patch_data.status,
                listed_price=patch_data.listed_price,
                description=patch_data.listing_description,
            )
            return updated

