from abc import ABC, abstractmethod
from decimal import Decimal

from app.models.vehicle_listing import VehicleListing
from app.schemas.vehicle_listing import ListingFilterParams


class VehicleListingInterface(ABC):
    @abstractmethod
    async def create_listing(
        self,
        vehicle_id: int,
        listed_price: Decimal,
        listing_description: str | None,
        status: str = "ACTIVE",
    ) -> VehicleListing:
        pass

    @abstractmethod
    async def get_listing_by_id(self, listing_id: int) -> VehicleListing | None:
        pass

    @abstractmethod
    async def get_listing_by_vehicle_id(self, vehicle_id: int) -> VehicleListing | None:
        pass

    @abstractmethod
    async def get_listings(self, filters: ListingFilterParams) -> dict:
        pass

    @abstractmethod
    async def update_listing(
        self,
        listing_id: int,
        status: str | None = None,
        listed_price: Decimal | None = None,
        description: str | None = None,
    ) -> VehicleListing | None:
        pass

    @abstractmethod
    async def deactivate_listings_by_seller_id(self, seller_id: int) -> list[int]:
        pass

    @abstractmethod
    async def update_listing_description(
        self, vehicle_id: int, description: str | None
    ) -> VehicleListing | None:
        pass

    @abstractmethod
    async def update_listing_price(
        self, vehicle_id: int, listed_price: Decimal
    ) -> VehicleListing | None:
        pass

    @abstractmethod
    async def deactivate_listing(self, vehicle_id: int) -> VehicleListing | None:
        pass

    @abstractmethod
    async def reactivate_listing(
        self,
        vehicle_id: int,
        listed_price: Decimal,
        listing_description: str | None,
    ) -> VehicleListing | None:
        pass
